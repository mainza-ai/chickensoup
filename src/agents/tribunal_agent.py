import json
import logging
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from typing_extensions import TypedDict

from src.llm_client import llm_client
from src.discovery import get_discovered, get_active_provider
from src.models import ClaimEvidence
from src.config import settings
from src.observability import tribunal_runs_total

logger = logging.getLogger("chickensoup.agents.tribunal_agent")


class TribunalState(TypedDict):
    claim_text: str
    evidence: List[Dict[str, Any]]
    wavefunction: Dict[str, Any]
    skeptic_position: str
    empiricist_position: str
    believer_position: str
    skeptic_citations: List[str]
    empiricist_citations: List[str]
    believer_citations: List[str]
    referee_synthesis: str
    disagreements: List[Dict[str, str]]
    final_state_label: str


SKEPTIC_SYSTEM = """You are the SKEPTIC in a three-agent tribunal evaluating claims about UAP, time travel, and anomalous phenomena.
Your role:
- Weigh absence of corroboration heavily. If only one platform reports a claim, say so.
- Weigh contradiction signals and debunking evidence.
- Demand reproducibility and extraordinary evidence for extraordinary claims.
- Point out where evidence is weak, anecdotal, or from unverified sources.
- Cite specific evidence items by cluster_id and URL.
Be concise, rigorous, and adversarial to hype."""

EMPIRICIST_SYSTEM = """You are the EMPIRICIST in a three-agent tribunal evaluating claims about UAP, time travel, and anomalous phenomena.
Your role:
- Weigh source diversity, market odds (Polymarket), and reproducibility heavily.
- Be agnostic to narrative plausibility — follow the data.
- Count independent platforms and clusters as strong signals.
- Note market-implied probabilities as meaningful priors when available.
- Cite specific evidence items by cluster_id and URL.
Be data-driven, quantitative where possible, and neutral."""

BELIEVER_SYSTEM = """You are the BELIEVER/NARRATIVIST in a three-agent tribunal evaluating claims about UAP, time travel, and anomalous phenomena.
Your role:
- Weigh internal consistency with established lore, witness testimony, and cross-referenced entities.
- Consider the broader mythology — how this claim fits with existing canon (Bob Lazar, Roswell, Element 115, etc.).
- Take witness testimony seriously while acknowledging uncertainty.
- Note when claims are consistent with other corroborated claims.
- Cite specific evidence items by cluster_id and URL and link to existing wiki entities where relevant.
Be narrative-aware, respectful of testimony, but not credulous."""


REFEREE_SYSTEM = """You are the REFEREE in a three-agent tribunal. You have received three positions (Skeptic, Empiricist, Believer) on the same claim, based on the same evidence pool plus a wavefunction confidence score.
Your job:
- Synthesize a final assessment without erasing disagreement.
- Explicitly note where the three disagreed and why.
- Include the wavefunction's epistemic_confidence, social_traction, state_label, and collapsed status.
- Produce a balanced final judgment: what is likely true, what remains contested, what is unverified.
- Preserve all three positions' citations — do not drop them.
- State your final state_label (corroborated | contested | unverified).

Return ONLY JSON:
{
  "final_state_label": "corroborated|contested|unverified",
  "synthesis": "2-4 paragraph synthesis",
  "disagreements": [{"topic": "...", "skeptic": "...", "empiricist": "...", "believer": "...", "resolution": "..."}],
  "confidence_adjustment": "up|down|same with reason"
}
"""


class TribunalAgent:
    def __init__(self):
        self.provider, self.base_url, self.models = get_discovered(depth="cached")

    def _query_llm(self, system_prompt: str, user_prompt: str, role_label: str) -> tuple[str, List[str]]:
        if get_active_provider() == "simulated":
            return f"{role_label} position (simulated): Analysed claim with {len(user_prompt)} chars of context.", []

        content = llm_client.query_sync(
            prompt=user_prompt,
            system=system_prompt,
            priority="high",
            temperature=0.4,
        )
        if content:
            urls = re.findall(r"https?://[^\s\)\]]+", content)
            return content, urls

        return f"{role_label} position fallback: insufficient evidence evaluated.", []

    def _build_evidence_context(self, claim_text: str, evidence: List[ClaimEvidence], wavefunction: Dict[str, Any]) -> str:
        lines = []
        lines.append(f"CLAIM: {claim_text}\n")
        lines.append(f"WAVEFUNCTION: epistemic={wavefunction.get('epistemic_confidence', 0.5):.3f}, "
                     f"traction={wavefunction.get('social_traction', 0.0):.3f}, "
                     f"state={wavefunction.get('state_label', 'unverified')}, "
                     f"collapsed={wavefunction.get('collapsed', False)}, "
                     f"evidence_count={wavefunction.get('evidence_count', 0)}\n")
        if wavefunction.get("scoring_inputs"):
            si = wavefunction["scoring_inputs"]
            lines.append(f"SCORING INPUTS: diversity={si.get('source_diversity', 0):.2f}, "
                         f"engagement_mag={si.get('engagement_magnitude', 0):.2f}, "
                         f"market_prior={si.get('polymarket_prior', 'None')}, "
                         f"contradiction={si.get('contradiction_signal', 0):.2f}, "
                         f"platforms={si.get('evidence_platforms', [])}\n")

        lines.append("EVIDENCE:\n")
        for idx, ev in enumerate(evidence, 1):
            odds_str = f", market={ev.polymarket_odds:.2%}" if ev.polymarket_odds is not None else ""
            lines.append(
                f"  {idx}. [{ev.cluster_id}] ({ev.source_platform}, eng={ev.engagement_count}{odds_str}) "
                f"{ev.claim_text[:300]} | {ev.url}\n"
            )

        return "\n".join(lines)

    def should_trigger_tribunal(
        self,
        state_label: str,
        divergence_risk: float = 0.0,
        divergence_threshold: float = None,
    ) -> bool:
        if divergence_threshold is None:
            divergence_threshold = settings.DIVERGENCE_SPIKE_THRESHOLD

        if state_label == "contested":
            try:
                tribunal_runs_total.add(1, {"trigger": "contested"})
            except Exception:
                pass
            return True
        if divergence_risk >= divergence_threshold:
            try:
                tribunal_runs_total.add(1, {"trigger": "divergence"})
            except Exception:
                pass
            return True
        return False

    def run_tribunal(
        self,
        claim_text: str,
        evidence: List[ClaimEvidence],
        wavefunction: Dict[str, Any],
        divergence_risk: float = 0.0,
    ) -> Dict[str, Any]:
        state_label = wavefunction.get("state_label", "unverified")

        if not self.should_trigger_tribunal(state_label, divergence_risk):
            logger.info(f"Tribunal NOT triggered for claim '{claim_text[:50]}' — state={state_label}, divergence={divergence_risk:.2f}")
            return {
                "triggered": False,
                "reason": f"state_label={state_label}, divergence_risk={divergence_risk:.3f} below threshold — uncontested claims never trigger tribunal",
                "claim_text": claim_text,
                "wavefunction": wavefunction,
            }

        logger.info(f"Tribunal triggered for claim '{claim_text[:60]}' — state={state_label}, divergence={divergence_risk:.3f}")

        from src.idle_sentinel import IdleSentinel
        IdleSentinel.update_activity("tribunal", "start")
        try:
            evidence_context = self._build_evidence_context(claim_text, evidence, wavefunction)

            # Three adversarial positions — same evidence, different priors
            skeptic_prompt = f"{evidence_context}\n\nProvide your skeptical position on this claim with citations."
            empiricist_prompt = f"{evidence_context}\n\nProvide your empiricist position with quantitative assessment and citations."
            believer_prompt = f"{evidence_context}\n\nProvide your narrativist/believer position with lore-consistency analysis and citations."

            skeptic_pos, skeptic_cites = self._query_llm(SKEPTIC_SYSTEM, skeptic_prompt, "Skeptic")
            empiricist_pos, empiricist_cites = self._query_llm(EMPIRICIST_SYSTEM, empiricist_prompt, "Empiricist")
            believer_pos, believer_cites = self._query_llm(BELIEVER_SYSTEM, believer_prompt, "Believer")

            # Referee synthesis
            referee_input = (
                f"CLAIM: {claim_text}\n\n"
                f"WAVEFUNCTION: {json.dumps(wavefunction, indent=2)}\n\n"
                f"SKEPTIC POSITION:\n{skeptic_pos}\n\n"
                f"EMPIRICIST POSITION:\n{empiricist_pos}\n\n"
                f"BELIEVER POSITION:\n{believer_pos}\n\n"
                f"All three positions must have their citations preserved. Do not collapse disagreement away."
            )

            referee_raw, _ = self._query_llm(REFEREE_SYSTEM, referee_input, "Referee")

            # Parse final state and disagreements
            synthesis = referee_raw
            final_label = state_label
            if "FINAL STATE:" in referee_raw:
                try:
                    parts = referee_raw.split("FINAL STATE:")
                    lbl = parts[-1].strip().split()[0].strip().lower().replace(".", "").replace('"', '').replace("'", "")
                    if lbl in ("corroborated", "contested", "unverified"):
                        final_label = lbl
                except Exception:
                    pass

            # Extract structured disagreements
            disagreements = []
            try:
                # Basic parser for [DISAGREEMENT] blocks
                blocks = referee_raw.split("[DISAGREEMENT]")
                for b in blocks[1:]:
                    lines = b.strip().split("\n")
                    topic = lines[0].strip() if lines else "disagreement"
                    disagreements.append({
                        "topic": topic,
                        "skeptic": skeptic_pos[:500],
                        "empiricist": empiricist_pos[:500],
                        "believer": believer_pos[:500],
                        "resolution": b.strip()[:1000]
                    })
            except Exception:
                pass

            if not disagreements:
                disagreements = [
                    {
                        "topic": "Overall assessment",
                        "skeptic": skeptic_pos[:500],
                        "empiricist": empiricist_pos[:500],
                        "believer": believer_pos[:500],
                        "resolution": f"Unparsed referee output — see synthesis field. Original label {state_label} retained as {final_label}.",
                    }
                ]

            return {
                "triggered": True,
                "claim_text": claim_text,
                "wavefunction": wavefunction,
                "divergence_risk": divergence_risk,
                "skeptic_position": skeptic_pos,
                "empiricist_position": empiricist_pos,
                "believer_position": believer_pos,
                "skeptic_citations": skeptic_cites,
                "empiricist_citations": empiricist_cites,
                "believer_citations": believer_cites,
                "referee_synthesis": synthesis,
                "final_state_label": final_label,
                "disagreements": disagreements,
                "all_citations": list(set(skeptic_cites + empiricist_cites + believer_cites)),
            }
        finally:
            IdleSentinel.update_activity("tribunal", "end")
