import json
import pytest
from src.last30days_adapter import Last30daysAdapter
from src.models import ClaimEvidence

def test_adapter_parses_real_ranked_candidates():
    # A mock matching the real last30days schema output
    real_schema_json = json.dumps({
        "topic": "Bob Lazar",
        "ranked_candidates": [
            {
                "candidate_id": "cand-1",
                "title": "Bob Lazar S-4 Flying Saucer claims",
                "explanation": "Bob Lazar claimed he worked on reverse engineering alien spacecraft at S-4",
                "source": "reddit",
                "url": "https://reddit.com/r/ufos/comments/123",
                "engagement": 1200,
                "cluster_id": "cluster-1",
                "metadata": {
                    "polymarket_odds": 0.35
                }
            },
            {
                "candidate_id": "cand-2",
                "title": "Database Engineer - Element 115",
                "explanation": " h-iring: Database Engineer - Element 115 careers at element115.ai",
                "source": "jobs-web",
                "url": "https://www.element115.ai/career/database-engineer",
                "engagement": 0,
                "cluster_id": "cluster-2"
            }
        ]
    })
    
    adapter = Last30daysAdapter()
    evidence = adapter.parse_output(real_schema_json, "Bob Lazar")
    
    # We parsed two candidates, but let's check parse results
    # Since skip URLs is implemented, and explanation is present:
    assert len(evidence) == 2
    assert evidence[0].claim_text == "Bob Lazar claimed he worked on reverse engineering alien spacecraft at S-4"
    assert evidence[0].source_platform == "reddit"
    assert evidence[0].engagement_count == 1200
    assert evidence[0].polymarket_odds == 0.35
    
    # Check jobs-web candidate
    assert evidence[1].source_platform == "jobs-web"

def test_pulse_agent_filters_hiring_for_non_org():
    from src.agents.pulse_agent import PulseAgent
    from src.models import PulseResult
    from unittest.mock import MagicMock, patch
    
    agent = PulseAgent()
    
    raw_output = json.dumps({
        "ranked_candidates": [
            {
                "candidate_id": "cand-1",
                "title": "Bob Lazar S-4 Flying Saucer claims",
                "explanation": "Bob Lazar claimed he worked on reverse engineering alien spacecraft at S-4",
                "source": "reddit",
                "url": "https://reddit.com/r/ufos/comments/123",
                "engagement": 1200
            },
            {
                "candidate_id": "cand-2",
                "title": "Database Engineer - Element 115",
                "explanation": "Database Engineer - Element 115 careers at element115.ai",
                "source": "jobs-web",
                "url": "https://www.element115.ai/career/database-engineer",
                "engagement": 0
            }
        ]
    })
    
    # Mock subprocess.run to return raw_output
    with patch("subprocess.run") as mock_run, \
         patch("src.agents.pulse_agent.ResourceLedger") as mock_ledger, \
         patch("src.wiki.writer.read_page") as mock_read:
         
         # Mock non-organization page frontmatter (tags has no "organization")
         mock_read.return_value = {
             "frontmatter": {
                 "tags": ["person", "ufo-witness"],
                 "last30days_handles": {"reddit": "r/ufos"}
             }
         }
         
         mock_status = MagicMock()
         mock_status.paid_remaining = 19.5
         mock_ledger.get_status.return_value = mock_status
         mock_ledger.check_budget.return_value = (True, 19.5, "ok")
         mock_run.return_value = MagicMock(returncode=0, stdout=raw_output, stderr="")
         
         result = agent.run_pulse("Bob Lazar")
         
         assert result.status == "success"
         # Database Engineer - Element 115 should be filtered out because Bob Lazar is NOT an organization!
         assert len(result.evidence) == 1
         assert result.evidence[0].source_platform == "reddit"


def test_adapter_parses_nested_engagement():
    # A candidate where engagement count is missing or 0 at the top level,
    # but nested inside source_items lists.
    nested_json = json.dumps({
        "topic": "Aldo Rebelo",
        "ranked_candidates": [
            {
                "candidate_id": "cand-1",
                "title": "IronTalks ao vivo com Super Xandao",
                "explanation": "Aldo Rebelo was interviewed on IronTalks podcast",
                "source": "youtube",
                "url": "https://www.youtube.com/watch?v=VxDQzBCQ-Es",
                "cluster_id": "cluster-3",
                "source_items": [
                    {
                        "author": "Dr. Felipe Sestaro",
                        "body": "IronTalks podcast interview with Aldo Rebelo",
                        "engagement": {
                            "comments": 234,
                            "likes": 5420
                        },
                        "source": "youtube"
                    }
                ]
            }
        ]
    })
    
    adapter = Last30daysAdapter()
    evidence = adapter.parse_output(nested_json, "Aldo Rebelo")
    evidence = adapter.normalize_engagement(evidence)
    
    assert len(evidence) == 1
    assert evidence[0].engagement_count == 5654
    assert evidence[0].engagement_decayed is not None
