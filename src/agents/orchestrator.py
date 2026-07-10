import asyncio
import re
import logging
from typing import Dict, Any, List, Union
from dataclasses import dataclass

from pydantic_graph import BaseNode, End, GraphBuilder, GraphRunContext, StepContext

from src.agents.query_agent import QueryAgent, ParsedQuery
from src.agents.research_agent import ResearchAgent
from src.agents.navigation_agent import NavigationAgent
from src.config import settings

logger = logging.getLogger("chickensoup.agents.orchestrator")

@dataclass
class OrchestratorDeps:
    query_agent: QueryAgent
    research_agent: ResearchAgent
    navigation_agent: NavigationAgent

@dataclass
class OrchestratorState:
    query: str
    parsed_query: ParsedQuery | None = None
    research_results: Dict[str, Any] | None = None
    navigation_results: Dict[str, Any] | None = None
    final_output: Dict[str, Any] | None = None
    thread_id: str = "default_thread"
    human_approved: bool = False

# Define Nodes using pydantic-graph BaseNode
@dataclass
class ClassifyNode(BaseNode[OrchestratorState, OrchestratorDeps]):
    async def run(self, ctx: GraphRunContext[OrchestratorState, OrchestratorDeps]) -> Union["ResearchNode", "NavigateNode", "StatusNode"]:
        logger.info("Orchestrator Graph -> Classifying query...")
        parsed = ctx.deps.query_agent.classify_and_parse(ctx.state.query)
        ctx.state.parsed_query = parsed
        
        if parsed.confidence < 0.6:
            logger.info(
                f"Low classification confidence ({parsed.confidence:.2f}) for intent '{parsed.intent}' — "
                f"falling back to ResearchNode"
            )
            return ResearchNode()

        if parsed.intent == "navigate":
            return NavigateNode()
        elif parsed.intent == "status":
            return StatusNode()
        else:
            return ResearchNode()

@dataclass
class ResearchNode(BaseNode[OrchestratorState, OrchestratorDeps]):
    async def run(self, ctx: GraphRunContext[OrchestratorState, OrchestratorDeps]) -> End[OrchestratorState]:
        logger.info("Orchestrator Graph -> Triggering Research Agent...")
        parsed = ctx.state.parsed_query
        
        entities = parsed.entities if parsed else []
        filters = parsed.structured_filters if parsed else {}
        
        res = ctx.deps.research_agent.run_research(
            query=ctx.state.query,
            entities=entities,
            structured_filters=filters,
            thread_id=ctx.state.thread_id,
            human_approved=ctx.state.human_approved
        )
        
        ctx.state.research_results = res
        
        if res.get("human_approval_required", False):
            # We pause the orchestrator, returning the current state
            ctx.state.final_output = {
                "status": "paused_for_human_approval",
                "thread_id": ctx.state.thread_id,
                "credibility_scores": res.get("credibility_scores", {}),
                "summary": "Human approval required for credibility evaluation."
            }
        else:
            ctx.state.final_output = {
                "status": "completed",
                "answer": res.get("summary", ""),
                "entities": entities,
                "confidence": parsed.confidence if parsed else 0.5,
                "sources": ["Local Wiki Knowledge Graph"],
                "research_details": res
            }
            
        return End(ctx.state)

@dataclass
class NavigateNode(BaseNode[OrchestratorState, OrchestratorDeps]):
    async def run(self, ctx: GraphRunContext[OrchestratorState, OrchestratorDeps]) -> End[OrchestratorState]:
        logger.info("Orchestrator Graph -> Triggering Navigation Agent...")
        parsed = ctx.state.parsed_query
        filters = parsed.structured_filters if parsed else {}
        entities = parsed.entities if parsed else []
        
        # Infer navigation params from filters (highest priority), then entities, then defaults
        origin = filters.get("origin", "Earth-2026")

        # Try to extract a year from entities (4-digit number)
        inferred_year = None
        if entities:
            for ent in entities:
                year_match = re.findall(r"\b(1[8-9]\d\d|20[0-3]\d)\b", ent)
                for ym in year_match:
                    inferred_year = int(ym)
                    break

        destination = filters.get("destination")
        target_year = int(filters.get("year", filters.get("target_year", inferred_year or 1947)))
        energy_level = float(filters.get("energy_level", 1.0))

        # If no explicit destination, try first entity (skip if it's a year)
        if not destination and entities:
            first = entities[0]
            if not re.match(r"^\d{4}$", first):
                destination = first

        if not destination:
            destination = "Earth-1947"
        
        nav_res = ctx.deps.navigation_agent.navigate(
            origin=origin,
            destination=destination,
            target_year=target_year,
            energy_level=energy_level
        )
        
        ctx.state.navigation_results = nav_res

        path_str = " → ".join(nav_res["path"]) if nav_res["path"] else "N/A"
        answer = (
            f"Navigation from {origin} to {destination} (target year {target_year}): "
            f"{'Successful' if nav_res['success'] else 'Failed'} | "
            f"Warp factor {nav_res['warp_factor']:.2f}, "
            f"divergence risk {nav_res['divergence_risk']:.1%} | "
            f"Path: {path_str}"
        )

        ctx.state.final_output = {
            "status": "completed",
            "answer": answer,
            "success": nav_res["success"],
            "path": nav_res["path"],
            "warp_factor": nav_res["warp_factor"],
            "divergence_risk": nav_res["divergence_risk"],
            "geometry_tensor": nav_res["geometry_tensor"],
            "field_manipulation": nav_res["field_manipulation"],
            "confidence": 1.0 if nav_res["success"] else 0.5,
            "sources": ["Navigation Agent"]
        }
        
        return End(ctx.state)

@dataclass
class StatusNode(BaseNode[OrchestratorState, OrchestratorDeps]):
    async def run(self, ctx: GraphRunContext[OrchestratorState, OrchestratorDeps]) -> End[OrchestratorState]:
        logger.info("Orchestrator Graph -> Status/Health check...")
        
        from src.main import get_status
        status_res = await get_status()
        status_data = status_res.model_dump()
        
        ctx.state.final_output = {
            "status": "completed",
            "system_status": status_data,
            "answer": (
                f"System status: LLM provider={status_data.get('llm_provider', '?')} "
                f"(connected={status_data.get('llm_connected', False)}), "
                f"Neo4j={'connected' if status_data.get('neo4j_connected') else 'disconnected'}, "
                f"Redis={'connected' if status_data.get('redis_connected') else 'disconnected'}, "
                f"Quantum backend={status_data.get('quantum_backend', '?')}"
            ),
            "confidence": 1.0,
            "sources": ["System Status"]
        }
        
        return End(ctx.state)

# Construct GraphBuilder
g = GraphBuilder(deps_type=OrchestratorDeps, state_type=OrchestratorState, output_type=OrchestratorState)

@g.step
async def start_step(ctx: StepContext[OrchestratorState, OrchestratorDeps, None]) -> ClassifyNode:
    return ClassifyNode()

# Add Nodes and Edges
g.add(
    g.node(ClassifyNode),
    g.node(ResearchNode),
    g.node(NavigateNode),
    g.node(StatusNode),
    g.edge_from(g.start_node).to(start_step),
)

orchestrator_graph = g.build()

class Orchestrator:
    """
    Top-level Orchestrator managing Pydantic Graph state execution.
    """
    def __init__(self):
        self.query_agent = QueryAgent()
        self.research_agent = ResearchAgent()
        self.navigation_agent = NavigationAgent()
        self.deps = OrchestratorDeps(
            query_agent=self.query_agent,
            research_agent=self.research_agent,
            navigation_agent=self.navigation_agent
        )

    async def execute(self, query: str, thread_id: str = "default_thread", human_approved: bool = False) -> Dict[str, Any]:
        state = OrchestratorState(query=query, thread_id=thread_id, human_approved=human_approved)
        try:
            result_state = await asyncio.wait_for(
                orchestrator_graph.run(state=state, deps=self.deps),
                timeout=settings.ORCHESTRATOR_TIMEOUT_SECONDS
            )
        except asyncio.TimeoutError:
            logger.error(f"Orchestrator execution timed out for query: {query}")
            return {
                "status": "completed",
                "answer": "The query processing timed out. Try a more specific question or check that the LLM service is running.",
                "confidence": 0.3,
                "entities": [],
                "sources": ["Timeout Fallback"],
            }
        output = result_state.final_output or {}

        # Synthesize answer if missing or empty — every endpoint needs an "answer" key
        if not output.get("answer"):
            if output.get("status") == "paused_for_human_approval":
                output["answer"] = output.get("summary", "Query requires human approval to proceed.")
            elif output.get("navigation_results"):
                nav = output["navigation_results"]
                path_str = " → ".join(nav.get("path", [])) if nav.get("path") else "N/A"
                output["answer"] = (
                    f"Navigation complete: "
                    f"{'Successful' if nav.get('success') else 'Failed'} | "
                    f"Warp factor {nav.get('warp_factor', 0):.2f}, "
                    f"divergence risk {nav.get('divergence_risk', 0):.1%} | "
                    f"Path: {path_str}"
                )
            elif output.get("system_status"):
                sd = output["system_status"]
                output["answer"] = (
                    f"System status: LLM provider={sd.get('llm_provider', '?')} "
                    f"(connected={sd.get('llm_connected', False)}), "
                    f"Neo4j={'connected' if sd.get('neo4j_connected') else 'disconnected'}"
                )
            else:
                output["answer"] = "Processed your request, but no specific answer was generated."

        # Ensure consistent keys
        output.setdefault("confidence", 0.5)
        output.setdefault("entities", [])
        output.setdefault("sources", [])

        return output
