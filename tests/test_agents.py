import pytest
from unittest.mock import MagicMock, patch
from src.agents.query_agent import QueryAgent
from src.agents.navigation_agent import NavigationAgent
from src.agents.research_agent import ResearchAgent
from src.agents.orchestrator import Orchestrator

def test_query_agent_tql_parsing():
    agent = QueryAgent()
    # Test valid TQL
    parsed = agent.parse_tql("Roswell incident TYPE:Event YEAR:1947 CONFIDENCE:0.9")
    assert parsed is not None
    assert parsed.intent == "navigate" or parsed.intent == "query"
    assert parsed.structured_filters["type"] == "Event"
    assert parsed.structured_filters["year"] == 1947
    assert parsed.structured_filters["confidence"] == 0.9
    assert parsed.entities == ["Roswell incident"]

def test_query_agent_heuristic_fallback():
    agent = QueryAgent()
    parsed = agent.classify_and_parse("Who worked at Roswell in 1947?")
    assert parsed.intent in ["query", "navigate"]
    assert len(parsed.entities) > 0

@patch("src.agents.research_agent.neo4j_conn")
def test_research_agent_flow(mock_conn):
    # Mock Neo4j driver results
    mock_driver = MagicMock()
    mock_conn.get_driver.return_value = mock_driver
    
    agent = ResearchAgent()
    with patch("src.agents.research_agent.search_entities", return_value=[{"name": "Bob Lazar", "confidence": 0.85, "labels": ["Person"]}]), \
         patch("src.agents.research_agent.get_entity_neighborhood", return_value={"entity": {"name": "Bob Lazar", "labels": ["Person"], "properties": {"confidence": 0.85}}, "connections": []}):
        
        res = agent.run_research(query="Bob Lazar", entities=["Bob Lazar"], thread_id="test_thread")
        assert "Bob Lazar" in res["assembled_context"]
        assert res["credibility_scores"]["Bob Lazar"] >= 0.85
        assert res["human_approval_required"] is False

def test_navigation_agent_calculation():
    agent = NavigationAgent()
    res = agent.navigate(origin="Earth-2026", destination="Earth-1947", target_year=1947, energy_level=2.0)
    assert res["success"] is True
    assert len(res["path"]) > 0
    assert res["warp_factor"] > 1.0
    assert res["divergence_risk"] >= 0.0

@pytest.mark.anyio
async def test_orchestrator_execution():
    orchestrator = Orchestrator()
    # Mock endpoints and LLM behaviors
    with patch.object(orchestrator.query_agent, "classify_and_parse") as mock_classify, \
         patch.object(orchestrator.research_agent, "run_research") as mock_research:
         
        from src.agents.query_agent import ParsedQuery
        mock_classify.return_value = ParsedQuery(intent="query", entities=["Roswell"], structured_filters={}, confidence=0.9)
        mock_research.return_value = {
            "assembled_context": "Roswell context details",
            "credibility_scores": {"Roswell": 0.9},
            "human_approval_required": False,
            "summary": "Roswell incident summary."
        }
        
        output = await orchestrator.execute("Roswell query", thread_id="orch_test")
        assert output["status"] == "completed"
        assert output["answer"] == "Roswell incident summary."
        assert output["entities"] == ["Roswell"]
