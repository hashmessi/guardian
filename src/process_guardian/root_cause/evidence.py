"""Evidence generation with strict epistemic honesty enforcement (ROOT-02, ROOT-03)."""

from typing import Dict, List, Tuple
from process_guardian.fingerprint.models import ProcessFingerprint


class EvidenceGenerator:
    """
    Generates structured empirical evidence statements for process deviations.
    
    Enforces honest probabilistic language standards (ROOT-03):
    - Uses: 'likely contributor', 'observed evidence', 'modeled effect', 'confidence'
    - Forbids: 'guaranteed cause', 'proven cause', 'definite root cause'
    """

    BANNED_PHRASES = [
        "guaranteed cause",
        "proven cause",
        "proven root cause",
        "definite cause",
        "definitely caused by",
        "guaranteed defect",
        "100% certain",
        "proven causal effect",
        "incontestable proof",
    ]

    FRIENDLY_NAMES: Dict[str, Tuple[str, str]] = {
        "barrel_temp_z1": ("Barrel Temperature (Zone 1)", "Thermal"),
        "barrel_temp_z2": ("Barrel Temperature (Zone 2)", "Thermal"),
        "barrel_temp_z3": ("Barrel Temperature (Zone 3)", "Thermal"),
        "barrel_temp_z4": ("Barrel Temperature (Zone 4)", "Thermal"),
        "barrel_temp_z5": ("Barrel Temperature (Zone 5)", "Thermal"),
        "nozzle_temp": ("Nozzle Temperature", "Thermal"),
        "injection_pressure": ("Injection Fill Pressure", "Pressure"),
        "peak_pressure": ("Peak Cavity Pressure", "Pressure"),
        "hold_pressure": ("Packing & Holding Pressure", "Pressure"),
        "injection_time": ("Injection Fill Time", "Timing"),
        "hold_time": ("Hold Duration", "Timing"),
        "cooling_time": ("Cooling Duration", "Timing"),
        "cycle_time": ("Total Cycle Duration", "Timing"),
        "part_weight": ("Molded Part Weight", "Quality"),
        "material_moisture": ("Resin Moisture Content", "Material"),
        "human_channel": ("Operator Shift Note (Human Channel)", "Material"),
    }

    def generate_signal_evidence(
        self,
        signal_name: str,
        current_val: float,
        baseline_mean: float,
        baseline_std: float,
        z_score: float,
        slope_per_cycle: float,
    ) -> str:
        """
        Formulate an honest, empirical evidence statement for a specific signal.
        """
        disp_name, category = self.FRIENDLY_NAMES.get(signal_name, (signal_name, "Process"))
        delta = current_val - baseline_mean
        sign_str = "+" if delta >= 0 else ""

        if abs(z_score) < 1.0:
            evidence = (
                f"{disp_name} is operating nominally at {current_val:.2f} "
                f"(modeled delta: {sign_str}{delta:.2f}, z-score: {z_score:+.2f}σ)."
            )
        else:
            trend_desc = ""
            if abs(slope_per_cycle) >= 0.01:
                slope_sign = "+" if slope_per_cycle > 0 else ""
                trend_desc = f" with an estimated rate of {slope_sign}{slope_per_cycle:.3f} units/cycle"

            evidence = (
                f"Observed evidence indicates {disp_name} shifted {sign_str}{delta:.2f} "
                f"({z_score:+.2f}σ from baseline mean {baseline_mean:.2f}){trend_desc}, "
                f"representing a likely contributor to process drift."
            )

        # Ensure text is compliant with honesty rules
        assert self.verify_honest_language(evidence), f"Evidence text failed honesty check: {evidence}"
        return evidence

    def verify_honest_language(self, text: str) -> bool:
        """
        Verify that text does NOT contain forbidden certainty claims.
        """
        text_lower = text.lower()
        for banned in self.BANNED_PHRASES:
            if banned in text_lower:
                return False
        return True

    def generate_summary(
        self,
        primary_signal: str,
        primary_pct: float,
        primary_z: float,
        top_category: str,
    ) -> str:
        """
        Generate honest overall summary statement for the root cause report.
        """
        disp_name, _ = self.FRIENDLY_NAMES.get(primary_signal, (primary_signal, "Process"))
        summary = (
            f"Modeled evidence identifies {disp_name} as the primary likely contributor "
            f"({primary_pct:.1f}% attribution, {primary_z:+.2f}σ deviation), "
            f"with {top_category} dynamics dominating overall process state divergence."
        )
        assert self.verify_honest_language(summary), "Summary failed honesty check"
        return summary
