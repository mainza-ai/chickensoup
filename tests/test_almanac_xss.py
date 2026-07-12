import pytest
from src.almanac.almanac_generator import _render_html

def test_render_html_escapes_xss_payloads():
    # Inject XSS payload into various fields
    xss_payload = "<script>alert('XSS')</script>"
    
    tier_results = [
        {
            "entity_name": f"Bob Lazar {xss_payload}",
            "pulse_status": f"success {xss_payload}",
            "evidence_count": 1,
            "confidences": [
                {
                    "state_label": "corroborated",
                    "epistemic_confidence": 0.85,
                    "social_traction": 0.4,
                    "collapsed": True,
                    "claim_text": f"Bob Lazar worked at S-4 {xss_payload}",
                }
            ],
            "divergence": {
                "divergence_risk": 0.45,
                "driving_claims": [
                    {
                        "claim_text": f"Diverging claim {xss_payload}",
                        "platform": "reddit",
                    }
                ]
            },
            "tribunal": {
                "triggered": True,
                "final_state_label": f"contested {xss_payload}",
                "referee_synthesis": f"Synthesis {xss_payload}",
                "disagreements": [
                    {
                        "topic": f"Topic {xss_payload}",
                        "skeptic": f"Skeptic {xss_payload}",
                        "empiricist": f"Empiricist {xss_payload}",
                        "believer": f"Believer {xss_payload}",
                    }
                ]
            }
        }
    ]
    
    entanglements = [
        {
            "entity_a": f"Entity A {xss_payload}",
            "entity_b": f"Entity B {xss_payload}",
            "entanglement_score": 0.95,
            "co_occurrence_count": 5,
        }
    ]
    
    meta = {
        "date_str": "2026-07-12",
        "total": 1,
        "moved": 0,
        "collapsed": 1,
        "contested": 0,
    }
    
    html_output = _render_html(tier_results, meta)
    
    # Verify that raw script tags do NOT exist in the output HTML
    assert "<script>" not in html_output
    assert "</script>" not in html_output
    assert "alert('XSS')" not in html_output
    
    # Verify that the escaped form exists
    assert "&lt;script&gt;alert(&#x27;XSS&#x27;)&lt;/script&gt;" in html_output or "&lt;script&gt;alert(&apos;XSS&apos;)&lt;/script&gt;" in html_output
