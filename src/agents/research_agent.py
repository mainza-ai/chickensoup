import os
import re
import logging
from typing import Dict, Any, List, Optional
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END

from src.knowledge_graph.connection import neo4j_conn
from src.knowledge_graph.queries import search_entities, get_entity_neighborhood
from src.discovery import get_discovered, get_active_provider
from src.llm_client import llm_client
from src.config import settings
from src.cache import cache_decorator
import json
import yaml

WIKI_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "wiki")
WIKI_SUBDIRS = ["entities", "concepts", "projects"]


def _slugify(name: str) -> str:
    return name.lower().replace(" ", "-").replace("_", "-")


def _read_wiki_file(entity_name: str) -> Optional[Dict[str, Any]]:
    """Read a wiki markdown file by entity name, return parsed frontmatter + body."""
    slug = _slugify(entity_name)
    for subdir in WIKI_SUBDIRS:
        path = os.path.join(WIKI_DIR, subdir, f"{slug}.md")
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            meta = {}
            body = content
            yaml_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
            if yaml_match:
                try:
                    meta = yaml.safe_load(yaml_match.group(1)) or {}
                except Exception:
                    pass
                body = content[yaml_match.end():]
            return {
                "name": entity_name,
                "file": path,
                "frontmatter": meta,
                "body": body[:2000],
                "content_preview": body[:300],
                "tags": meta.get("tags", []),
                "sources": meta.get("sources", []),
                "related": meta.get("related", []),
            }
    return None


def _wiki_file_fallback(entities: List[str], query: str) -> List[Dict[str, Any]]:
    """
    Fallback when Neo4j is empty/unavailable: read wiki markdown files directly.
    Returns a list of graph_context-like dicts.
    """
    context = []
    candidates = list(entities)
    if query:
        candidates.append(query)

    seen = set()
    for entity in candidates:
        if entity.lower() in seen:
            continue
        seen.add(entity.lower())
        page = _read_wiki_file(entity)
        if page:
            context.append({
                "entity": {
                    "name": page["name"],
                    "labels": ["Entity"] + [t.capitalize() for t in page["tags"] if t in ("person", "place", "event", "concept", "project")],
                    "properties": {
                        "content_preview": page["content_preview"],
                        "sources": page["sources"],
                        "tags": page["tags"],
                    }
                },
                "connections": [],
                "_wiki_file": page["file"],
                "_body_snippet": page["body"][:500],
            })
    return context

logger = logging.getLogger("chickensoup.agents.research_agent")

class ResearchState(TypedDict):
    # Inputs
    query: str
    entities: List[str]
    structured_filters: Dict[str, Any]
    history: List[Dict[str, str]]
    
    # Internal & Outputs
    found_nodes: List[Dict[str, Any]]
    graph_context: List[Dict[str, Any]]
    credibility_scores: Dict[str, float]
    assembled_context: str
    human_approval_required: bool
    human_approved: bool
    force_human_approval: bool
    summary: str

def extraction_node(state: ResearchState) -> Dict[str, Any]:
    """Node: Extracts entities if they are missing, leveraging state or lightweight LLM parsing."""
    logger.info("Running ResearchAgent Extraction Node...")
    entities = state.get("entities", [])
    query = state.get("query", "")
    
    if not entities and query:
        # Perform simple keyword extraction
        words = query.split()
        capitalized = [w.strip("?,.!") for w in words if w and w[0].isupper()]
        entities = capitalized if capitalized else [query]
        
    return {"entities": entities}

def neo4j_lookup_node(state: ResearchState) -> Dict[str, Any]:
    """Node: Query the Neo4j database to find matching entities and their neighborhood context.
    Falls back to reading wiki markdown files directly when Neo4j returns nothing."""
    logger.info("Running ResearchAgent Neo4j Lookup Node...")
    driver = None
    entities = state.get("entities", [])
    
    found_nodes = []
    graph_context = []
    
    try:
        driver = neo4j_conn.get_driver()
    except Exception as e:
        logger.warning(f"Neo4j driver unavailable: {e}")

    if driver:
        for entity in entities:
            matches = search_entities(driver, entity)
            for match in matches:
                found_nodes.append(match)
                neighborhood = get_entity_neighborhood(driver, match["name"])
                if neighborhood and neighborhood.get("entity"):
                    graph_context.append(neighborhood)
                    
        if not found_nodes and state.get("query"):
            matches = search_entities(driver, state["query"])
            for match in matches:
                found_nodes.append(match)
                neighborhood = get_entity_neighborhood(driver, match["name"])
                if neighborhood and neighborhood.get("entity"):
                    graph_context.append(neighborhood)

    # Fallback to wiki files when Neo4j returned nothing
    if not graph_context:
        logger.info("No Neo4j results — trying wiki file fallback...")
        file_context = _wiki_file_fallback(entities, state.get("query", ""))
        if file_context:
            graph_context = file_context
            for ctx in file_context:
                ent = ctx.get("entity", {})
                found_nodes.append({
                    "name": ent.get("name", ""),
                    "labels": ent.get("labels", []),
                    "confidence": 0.8,
                    "preview": ent.get("properties", {}).get("content_preview", ""),
                    "source": "wiki_file_fallback",
                })

    return {
        "found_nodes": found_nodes,
        "graph_context": graph_context
    }

def _compute_wavefunction_scores(
    entities: List[str],
    found_nodes: List[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    from src.wiki.pulse_writer import load_recent_pulse_evidence
    from src.quantum_credibility.wavefunction import ClaimWavefunction

    wavefunction = ClaimWavefunction()
    scored: Dict[str, Any] = {}
    any_pulse = False

    for node in found_nodes:
        name = node.get("name", "")
        if not name:
            continue
        try:
            evidence = load_recent_pulse_evidence(name, max_age_days=14)
            if not evidence:
                continue
            any_pulse = True
            claim_text = node.get("preview", "") or name
            
            from src.scheduler import _get_reinforcement_count
            from src.wiki.writer import slugify
            slug = slugify(name)
            rc = _get_reinforcement_count(slug)
            
            cc = wavefunction.score_claim(claim_text, evidence, reinforcement_count=rc)
            scored[name] = {
                "epistemic_confidence": cc.epistemic_confidence,
                "social_traction": cc.social_traction,
                "state_label": cc.state_label,
                "collapsed": cc.collapsed,
                "evidence_count": cc.evidence_count,
                "last_pulse_at": cc.last_pulse_at,
                "scoring_version": cc.scoring_version,
                "scoring_inputs": cc.scoring_inputs,
                "claim_text": cc.claim_text,
            }
        except Exception as e:
            logger.debug(f"Wavefunction scoring failed for '{name}': {e}")
            continue

    if not any_pulse:
        return None

    return scored


def credibility_scoring_node(state: ResearchState) -> Dict[str, Any]:
    logger.info("Running ResearchAgent Credibility Scoring Node...")
    found_nodes = state.get("found_nodes", [])
    entities = state.get("entities", [])

    # Try wavefunction scoring when recent pulse data exists
    wf_scores: Optional[Dict[str, Any]] = None
    try:
        wf_scores = _compute_wavefunction_scores(entities, found_nodes)
    except Exception as e:
        logger.warning(f"Wavefunction scoring path error, falling back to heuristic: {e}")
        wf_scores = None

    scores: Dict[str, float] = {}
    wf_details: Dict[str, Any] = {}

    if wf_scores:
        logger.info(f"Wavefunction scoring active — {len(wf_scores)} nodes with pulse evidence")
        for node in found_nodes:
            name = node.get("name", "")
            if name in wf_scores:
                detail = wf_scores[name]
                scores[name] = detail["epistemic_confidence"]
                wf_details[name] = detail
            else:
                # No pulse evidence for this node — heuristic fallback
                base_conf = node.get("confidence", 0.5)
                labels = node.get("labels", [])
                score = base_conf
                if "Person" in labels:
                    score += 0.1
                if "Project" in labels:
                    score += 0.15
                scores[name] = min(1.0, max(0.0, score))
    else:
        # Heuristic fallback — existing behaviour preserved
        for node in found_nodes:
            name = node.get("name", "")
            base_conf = node.get("confidence", 0.5)
            labels = node.get("labels", [])
            score = base_conf
            if "Person" in labels:
                score += 0.1
            if "Project" in labels:
                score += 0.15
            scores[name] = min(1.0, max(0.0, score))

    human_approval_required = state.get("force_human_approval", False)
    if not human_approval_required:
        for name, val in scores.items():
            if val < 0.4:
                human_approval_required = True
                break

    result: Dict[str, Any] = {
        "credibility_scores": scores,
        "human_approval_required": human_approval_required,
    }
    if wf_details:
        result["wavefunction_scores"] = wf_details

    return result

def context_assembly_node(state: ResearchState) -> Dict[str, Any]:
    """Node: Synthesizes all gathered information into an assembled context block."""
    logger.info("Running ResearchAgent Context Assembly Node...")
    graph_context = state.get("graph_context", [])
    scores = state.get("credibility_scores", {})
    
    lines = []
    lines.append("=== KNOWLEDGE GRAPH RESEARCH FINDINGS ===")
    
    for ctx in graph_context:
        ent = ctx.get("entity")
        if not ent:
            continue
        name = ent.get("name")
        labels = ent.get("labels", [])
        props = ent.get("properties", {})
        score = scores.get(name, 0.5)
        
        lines.append(f"\nEntity: {name} (Labels: {', '.join(labels)}, Credibility Score: {score:.2f})")
        if props.get("content_preview"):
            lines.append(f"  Description: {props['content_preview']}")
        if props.get("sources"):
            lines.append(f"  Sources: {', '.join(props['sources'])}")
            
        connections = ctx.get("connections", [])
        if connections:
            lines.append("  Connected Relationships:")
            for conn in connections:
                lines.append(
                    f"    - [{conn['relationship_type']}] -> {conn['neighbor_name']} ({', '.join(conn['neighbor_labels'])})"
                )
                
    if not graph_context:
        lines.append("No matching entities found in the local wiki knowledge graph.")
        
    assembled = "\n".join(lines)
    return {"assembled_context": assembled}

def check_human_approval(state: ResearchState) -> str:
    """Conditional routing edge."""
    if state.get("human_approval_required", False) and not state.get("human_approved", False):
        return "human_approval_gate"
    return "context_assembly"

def human_approval_gate(state: ResearchState) -> Dict[str, Any]:
    """Node representing a pause/wait for human approval."""
    logger.info("ResearchAgent paused at Human Approval Gate.")
    return {"human_approval_required": True}

# Build LangGraph workflow
workflow = StateGraph(ResearchState)

# Add Nodes
workflow.add_node("extraction", extraction_node)
workflow.add_node("neo4j_lookup", neo4j_lookup_node)
workflow.add_node("credibility_scoring", credibility_scoring_node)
workflow.add_node("human_approval_gate", human_approval_gate)
workflow.add_node("context_assembly", context_assembly_node)

# Set Entry
workflow.set_entry_point("extraction")

# Core flow
workflow.add_edge("extraction", "neo4j_lookup")
workflow.add_edge("neo4j_lookup", "credibility_scoring")

# Conditional path
workflow.add_conditional_edges(
    "credibility_scoring",
    check_human_approval,
    {
        "human_approval_gate": "human_approval_gate",
        "context_assembly": "context_assembly"
    }
)

# Resume path from gate
workflow.add_edge("human_approval_gate", "context_assembly")
workflow.add_edge("context_assembly", END)

# Checkpointer for persistent state saving & resuming.
# Uses RedisSaver when Redis is available; falls back to MemorySaver.
# interrupt_before human_approval_gate so the graph truly pauses
# when human approval is required, enabling resume via POST /research/{thread_id}/approve

def _create_checkpointer():
    try:
        from langgraph.checkpoint.redis import RedisSaver
        cp = RedisSaver(redis_url=settings.REDIS_URL)
        cp.setup()
        logger.info("Using RedisSaver for persistent checkpointing")
        return cp
    except Exception as e:
        logger.warning(f"Redis checkpointer unavailable, using MemorySaver: {e}")
        from langgraph.checkpoint.memory import MemorySaver
        return MemorySaver()

research_graph = workflow.compile(
    checkpointer=_create_checkpointer(),
    interrupt_before=["human_approval_gate"],
)

class ResearchAgent:
    """
    Orchestrates the LangGraph Research Graph workflow, supporting
    checkpointing and human-in-the-loop overrides.
    """
    
    def __init__(self):
        self.provider, self.base_url, self.models = get_discovered(depth="cached")
        self.graph = research_graph

    def run_research(
        self,
        query: str,
        entities: List[str] = None,
        structured_filters: Dict[str, Any] = None,
        thread_id: str = "default_thread",
        human_approved: bool = False,
        force_human_approval: bool = False,
        history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        
        initial_state = ResearchState(
            query=query,
            entities=entities or [],
            structured_filters=structured_filters or {},
            history=history or [],
            found_nodes=[],
            graph_context=[],
            credibility_scores={},
            assembled_context="",
            human_approval_required=False,
            human_approved=human_approved,
            force_human_approval=force_human_approval,
            summary=""
        )
        
        config = {"configurable": {"thread_id": thread_id}}
        
        # If it's a resume after human approval, update persisted state
        if human_approved:
            current_state = self.graph.get_state(config)
            if current_state and current_state.values:
                updated_values = dict(current_state.values)
                updated_values["human_approved"] = True
                self.graph.update_state(config, updated_values)

        # Run graph — may be interrupted at human_approval_gate
        final_state = self.graph.invoke(initial_state, config=config)
        # If interrupt_before paused the graph, final_state is partial.
        # Check if there are pending nodes to run.
        paused_check = self.graph.get_state(config)
        if paused_check and paused_check.next:
            # Graph is paused waiting for human approval
            return {
                "human_approval_required": True,
                "credibility_scores": final_state.get("credibility_scores", {}),
                "summary": "Human approval required for credibility evaluation.",
                "thread_id": thread_id,
                "inferred_events": [],
                "inferred_entities": [],
                "assembled_context": "",
            }
        
        # Generate summary using local LLM if possible
        summary = ""
        if final_state.get("assembled_context"):
            summary = self._generate_summary(query, final_state["assembled_context"], history=history)
            
        # Build inferred events/entities from wavefunction scores if available
        inferred_events: list = []
        inferred_entities: list = []
        try:
            wf_details = final_state.get("wavefunction_scores", {}) if isinstance(final_state, dict) else {}
            if wf_details:
                from src.models import ClaimConfidence
                for node_name, detail in wf_details.items():
                    # Inferred entities carry wavefunction metadata
                    inferred_entities.append({
                        "name": node_name,
                        "epistemic_confidence": detail.get("epistemic_confidence", 0.5),
                        "social_traction": detail.get("social_traction", 0.0),
                        "state_label": detail.get("state_label", "unverified"),
                        "collapsed": detail.get("collapsed", False),
                        "evidence_count": detail.get("evidence_count", 0),
                        "last_pulse_at": detail.get("last_pulse_at"),
                        "scoring_inputs": detail.get("scoring_inputs", {}),
                        "source_tier": "network_opt_in",
                    })
                # Any contested/collapsed claims become inferred events
                for node_name, detail in wf_details.items():
                    if detail.get("state_label") in ("corroborated", "contested") and detail.get("collapsed"):
                        inferred_events.append({
                            "entity": node_name,
                            "type": "claim_collapse",
                            "state_label": detail.get("state_label"),
                            "epistemic_confidence": detail.get("epistemic_confidence"),
                            "social_traction": detail.get("social_traction"),
                            "evidence_count": detail.get("evidence_count"),
                            "last_pulse_at": detail.get("last_pulse_at"),
                        })
        except Exception as inf_err:
            logger.debug(f"Failed to build inferred events/entities: {inf_err}")

        return {
            "assembled_context": final_state.get("assembled_context", ""),
            "credibility_scores": final_state.get("credibility_scores", {}),
            "wavefunction_scores": final_state.get("wavefunction_scores", {}),
            "human_approval_required": final_state.get("human_approval_required", False) and not final_state.get("human_approved", False),
            "summary": summary or "Summary generation fallback.",
            "thread_id": thread_id,
            "inferred_events": inferred_events,
            "inferred_entities": inferred_entities,
        }

    @cache_decorator(prefix="mcp", ttl=300)
    def _generate_summary(self, query: str, context: str, history: List[Dict[str, str]] = None) -> str:
        if get_active_provider() == "simulated":
            return f"Lore Summary: Detailed report matches query '{query}'."

        prompt = f"""
        Analyze the following research context and answer the user query: "{query}"

        Context:
        {context}

        Synthesize a clean summary including references to specific entities, credibility values, and connections.
        """

        messages = [
            {"role": "system", "content": "You are a helpful researcher summarizing UFO/anomalous lore."}
        ]
        if history:
            for turn in history:
                role = turn.get("role")
                content = turn.get("content")
                if role in ("user", "assistant") and content:
                    messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": prompt})

        result = llm_client.query_sync(
            prompt="",
            messages=messages,
            priority="high",
            temperature=0.3,
        )
        if result:
            return result
        return f"Lore Summary: Found relevant context matches. {query}"
