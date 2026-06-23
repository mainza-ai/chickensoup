import logging
from typing import Dict, Any, List, Union
from dataclasses import dataclass

from pydantic_graph import BaseNode, End, GraphBuilder, GraphRunContext, StepContext

from src.agents.query_agent import QueryAgent, ParsedQuery
from src.agents.research_agent import ResearchAgent
from src.agents.navigation_agent import NavigationAgent

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
        filters = ctx.state.parsed_query.structured_filters if ctx.state.parsed_query else {}
        
        # Pull parameters out of parsed query filters or use defaults
        origin = filters.get("origin", "Earth-2026")
        destination = filters.get("destination", "Earth-1947")
        target_year = int(filters.get("year", filters.get("target_year", 1947)))
        energy_level = float(filters.get("energy_level", 1.0))
        
        nav_res = ctx.deps.navigation_agent.navigate(
            origin=origin,
            destination=destination,
            target_year=target_year,
            energy_level=energy_level
        )
        
        ctx.state.navigation_results = nav_res
        ctx.state.final_output = {
            "status": "completed",
            "success": nav_res["success"],
            "path": nav_res["path"],
            "warp_factor": nav_res["warp_factor"],
            "divergence_risk": nav_res["divergence_risk"],
            "geometry_tensor": nav_res["geometry_tensor"],
            "field_manipulation": nav_res["field_manipulation"]
        }
        
        return End(ctx.state)

@dataclass
class StatusNode(BaseNode[OrchestratorState, OrchestratorDeps]):
    async def run(self, ctx: GraphRunContext[OrchestratorState, OrchestratorDeps]) -> End[OrchestratorState]:
        logger.info("Orchestrator Graph -> Status/Health check...")
        
        from src.main import get_status
        status_res = await get_status()
        
        ctx.state.final_output = {
            "status": "completed",
            "system_status": status_res.model_dump()
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
        result_state = await orchestrator_graph.run(state=state, deps=self.deps)
        return result_state.final_output
