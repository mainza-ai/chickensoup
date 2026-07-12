import pytest
import json
from unittest.mock import MagicMock, patch
from src.agents.query_agent import resolve_pronominal_references, QueryAgent
from src.agents.orchestrator import Orchestrator
from src.agents.pulse_agent import PulseAgent

def test_resolve_pronominal_references():
    history = [
        {"role": "user", "content": "Tell me about Bob Lazar"},
        {"role": "assistant", "content": "Bob Lazar claimed he worked on reverse engineering alien spacecraft at S-4."}
    ]
    
    with patch("src.agents.query_agent._wiki_entity_lookup", return_value=["Bob Lazar"]):
        # Proronominal reference to Bob Lazar
        query1 = "when did he testify?"
        resolved1 = resolve_pronominal_references(query1, history)
        assert "Bob Lazar" in resolved1
        
        query2 = "what was its engine?"
        # Here the last matched entity in history is still Bob Lazar
        resolved2 = resolve_pronominal_references(query2, history)
        assert "Bob Lazar" in resolved2

def test_pulse_agent_semantic_disambiguation():
    agent = PulseAgent()
    
    # We query for "Bob Lazar"
    raw_output = json.dumps({
        "ranked_candidates": [
            {
                "candidate_id": "cand-1",
                "title": "Bob Lazar S-4 claims",
                "explanation": "Bob Lazar's testimonies on reverse engineering",
                "source": "reddit",
                "url": "https://reddit.com/r/ufos/comments/123",
                "engagement": 1200
            },
            {
                "candidate_id": "cand-2",
                "title": "UFO Roswell sighting in 1947",
                "explanation": "A weather balloon or alien spacecraft crashed in New Mexico",
                "source": "news",
                "url": "https://roswell-news.com/crash",
                "engagement": 500
            }
        ]
    })
    
    with patch("subprocess.run") as mock_run, \
         patch("src.agents.pulse_agent.ResourceLedger") as mock_ledger, \
         patch("src.wiki.writer.read_page") as mock_read:
         
         # Mock organization page
         mock_read.return_value = {
             "frontmatter": {
                 "tags": ["organization"],
                 "last30days_handles": {}
             }
         }
         
         mock_status = MagicMock()
         mock_status.paid_remaining = 19.5
         mock_ledger.get_status.return_value = mock_status
         mock_ledger.check_budget.return_value = (True, 19.5, "ok")
         mock_run.return_value = MagicMock(returncode=0, stdout=raw_output, stderr="")
         
         result = agent.run_pulse("Bob Lazar")
         
         # "UFO Roswell sighting in 1947" should be filtered out by semantic disambiguation 
         # since it doesn't mention "Bob" or "Lazar" anywhere in the candidate
         assert result.status == "success"
         assert len(result.evidence) == 1
         assert result.evidence[0].claim_text == "Bob Lazar's testimonies on reverse engineering"
