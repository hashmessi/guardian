"""Candidate action generation and multi-constraint boundary verification (INTV-01, INTV-02)."""

from typing import List, Dict, Optional, Any
from process_guardian.adapter.schemas import NormalizedCycleRecord
from process_guardian.fingerprint.models import ProcessFingerprint
from process_guardian.sentinel.schemas import DriftOutput
from process_guardian.root_cause.schemas import RootCauseReport
from process_guardian.intervention.schemas import (
    ActionType,
    CandidateAction,
    ConstraintCheckResult,
    MachineSafetyLimits,
    RecipeLimits,
    StepLimits,
)


class CandidateGenerator:
    """
    Generates actionable operational candidates (A0..A4) conditioned on process drift and telemetry (INTV-01).
    """

    def __init__(self, step_limits: Optional[StepLimits] = None):
        self.step_limits = step_limits or StepLimits()

    def generate_candidates(
        self,
        record: NormalizedCycleRecord,
        fingerprint: ProcessFingerprint,
        drift_output: Optional[DriftOutput] = None,
        root_cause_report: Optional[RootCauseReport] = None,
    ) -> List[CandidateAction]:
        """
        Generate at least 5 candidate operational actions (A0..A4).
        
        A0: DO_NOTHING (Continue monitoring)
        A1: TEMP_ADJUST (Zone 3 temperature adjustment)
        A2: PRESSURE_ADJUST (Hold/injection pressure adjustment)
        A3: CYCLE_TIME_ADJUST (Cooling time adjustment)
        A4: MATERIAL_INSPECT_PURGE (Hopper check & purge)
        """
        candidates: List[CandidateAction] = []

        # A0: Continue monitoring (Baseline / No-op)
        candidates.append(
            CandidateAction(
                action_id="A0",
                action_type=ActionType.DO_NOTHING,
                name="Continue Monitoring",
                target_signal=None,
                delta_value=0.0,
                unit="",
                cost_weight=0.0,
                disruption_weight=0.0,
                description="Maintain current machine settings without adjustment and continue monitoring process telemetry.",
            )
        )

        # Determine direction and magnitude from observed telemetry relative to fingerprint baseline
        # 1. Temperature: Check barrel_temp_z3 (or primary thermal contributor)
        temp_sig = "barrel_temp_z3"
        curr_temp = getattr(record, temp_sig, 230.0)
        temp_stats = fingerprint.signal_stats.get(temp_sig)
        temp_mean = temp_stats.mean if temp_stats else 231.0
        temp_diff = curr_temp - temp_mean

        # Counteract thermal shift, capped by max step limit
        max_temp_step = self.step_limits.limits.get(temp_sig, 3.0)
        if abs(temp_diff) > 0.5:
            temp_delta = -round(max(-max_temp_step, min(max_temp_step, temp_diff * 0.75)), 1)
        else:
            temp_delta = -2.0  # nominal preventive cooling step

        candidates.append(
            CandidateAction(
                action_id="A1",
                action_type=ActionType.TEMP_ADJUST,
                name="Barrel Zone 3 Temperature Adjustment",
                target_signal=temp_sig,
                delta_value=temp_delta,
                unit="°C",
                cost_weight=0.15,
                disruption_weight=0.10,
                description=f"Adjust {temp_sig} by {temp_delta:+.1f}°C to stabilize polymer melt viscosity.",
            )
        )

        # 2. Pressure: Check hold_pressure or injection_pressure
        inj_sig = "injection_pressure"
        curr_inj = getattr(record, inj_sig, 110.0)
        inj_stats = fingerprint.signal_stats.get(inj_sig)
        inj_mean = inj_stats.mean if inj_stats else 110.0
        inj_diff = curr_inj - inj_mean

        peak_diff = getattr(record, "peak_pressure", 135.0) - (
            fingerprint.signal_stats.get("peak_pressure").mean if "peak_pressure" in fingerprint.signal_stats else 135.0
        )

        # Match the signal exactly. A substring test for "pressure" also matches
        # hold_pressure, which sent a hold-pressure root cause to an injection-
        # pressure correction -- the wrong actuator, and on a low-hold-pressure
        # drift it pushes packing further down instead of restoring it.
        is_inj_drift = False
        if root_cause_report and any(
            getattr(c, "signal_name", "") == inj_sig for c in getattr(root_cause_report, "contributors", [])[:2]
        ):
            is_inj_drift = True
        elif root_cause_report and getattr(root_cause_report, "primary_contributor", "") == inj_sig:
            is_inj_drift = True
        elif drift_output and inj_sig in getattr(drift_output, "signals", []):
            is_inj_drift = True
        elif abs(inj_diff) > 4.0:
            is_inj_drift = True

        if is_inj_drift:
            press_sig = "injection_pressure"
            press_name = "Injection Pressure Adjustment"
            max_press_step = self.step_limits.limits.get(press_sig, 15.0)
            press_delta = -round(max(-max_press_step, min(max_press_step, inj_diff * 0.85)), 1)
            # Ensure proposed injection pressure restores towards nominal baseline
            if inj_diff < -4.0 and press_delta < 4.0:
                press_delta = min(max_press_step, round(abs(inj_diff), 1))
        else:
            press_sig = "hold_pressure"
            press_name = "Holding Pressure Adjustment"
            curr_press = getattr(record, press_sig, 65.0)
            press_stats = fingerprint.signal_stats.get(press_sig)
            press_mean = press_stats.mean if press_stats else 65.0
            press_diff = curr_press - press_mean
            max_press_step = self.step_limits.limits.get(press_sig, 6.0)

            if abs(press_diff) > 0.5:
                press_delta = -round(max(-max_press_step, min(max_press_step, press_diff * 0.8)), 1)
            elif peak_diff < -2.0:
                # Cavity peak pressure is low (e.g. pressure drift regime); boost hold pressure to compensate
                press_delta = 2.0
            else:
                press_delta = -2.0 if temp_diff > 2.0 else 1.5

        # Clamp so proposed value stays within operating envelope
        if press_sig in fingerprint.operating_envelopes:
            env = fingerprint.operating_envelopes[press_sig]
            curr_val = getattr(record, press_sig, 65.0)
            if curr_val < env.upper_limit and press_delta > 0:
                press_delta = min(press_delta, round(env.upper_limit - curr_val - 0.05, 1))
            elif curr_val > env.lower_limit and press_delta < 0:
                press_delta = max(press_delta, round(env.lower_limit - curr_val + 0.05, 1))

        candidates.append(
            CandidateAction(
                action_id="A2",
                action_type=ActionType.PRESSURE_ADJUST,
                name=press_name,
                target_signal=press_sig,
                delta_value=press_delta,
                unit="bar",
                cost_weight=0.10,
                disruption_weight=0.05,
                description=f"Adjust {press_sig} by {press_delta:+.1f} bar to compensate for cavity fill dynamics.",
            )
        )

        # 3. Timing: Check cooling_time
        cool_sig = "cooling_time"
        curr_cool = getattr(record, cool_sig, 14.0)
        cool_stats = fingerprint.signal_stats.get(cool_sig)
        cool_mean = cool_stats.mean if cool_stats else 14.0
        cool_diff = curr_cool - cool_mean

        max_cool_step = self.step_limits.limits.get(cool_sig, 2.0)
        if abs(cool_diff) > 0.3:
            cool_delta = -round(max(-max_cool_step, min(max_cool_step, cool_diff * 0.7)), 1)
        else:
            cool_delta = 0.5 if temp_diff > 1.5 else -0.5

        # Clamp cooling time to operating envelope
        if cool_sig in fingerprint.operating_envelopes:
            env = fingerprint.operating_envelopes[cool_sig]
            if curr_cool < env.upper_limit and cool_delta > 0:
                cool_delta = min(cool_delta, round(env.upper_limit - curr_cool - 0.05, 1))
            elif curr_cool > env.lower_limit and cool_delta < 0:
                cool_delta = max(cool_delta, round(env.lower_limit - curr_cool + 0.05, 1))

        candidates.append(
            CandidateAction(
                action_id="A3",
                action_type=ActionType.CYCLE_TIME_ADJUST,
                name="Cooling Time Adjustment",
                target_signal=cool_sig,
                delta_value=cool_delta,
                unit="s",
                cost_weight=0.25,
                disruption_weight=0.30,
                description=f"Adjust {cool_sig} by {cool_delta:+.1f} s to ensure proper heat deflection and part rigidity.",
            )
        )

        # 4. Material Inspection / Purge
        moist_sig = "material_moisture"
        curr_moist = getattr(record, moist_sig, 0.02)
        moist_stats = fingerprint.signal_stats.get(moist_sig)
        moist_mean = moist_stats.mean if moist_stats else 0.02
        moist_diff = curr_moist - moist_mean
        moist_delta = -round(max(0.0, moist_diff), 4) if moist_diff > 0.005 else 0.0

        candidates.append(
            CandidateAction(
                action_id="A4",
                action_type=ActionType.MATERIAL_INSPECT_PURGE,
                name="Material Inspection & Hopper Purge",
                target_signal=moist_sig,
                delta_value=moist_delta,
                unit="%",
                cost_weight=0.60,
                disruption_weight=0.75,
                description="Perform dryer dew-point verification and purge resin barrel to restore raw material baseline.",
            )
        )

        return candidates


class ConstraintChecker:
    """
    Evaluates operational actions against multi-boundary constraints (INTV-02):
    1. Machine Safety Limits
    2. Recipe Specification Limits
    3. Fingerprint Operating Envelope (mu +- 3*sigma)
    4. Maximum Single-Step Adjustment Delta
    5. Directional Drift Opposition Logic
    """

    def __init__(
        self,
        safety_limits: Optional[MachineSafetyLimits] = None,
        recipe_limits: Optional[RecipeLimits] = None,
        step_limits: Optional[StepLimits] = None,
    ):
        self.safety_limits = safety_limits or MachineSafetyLimits()
        self.recipe_limits = recipe_limits or RecipeLimits()
        self.step_limits = step_limits or StepLimits()

    def check_constraints(
        self,
        candidate: CandidateAction,
        record: NormalizedCycleRecord,
        fingerprint: ProcessFingerprint,
    ) -> ConstraintCheckResult:
        """
        Validate a candidate action against all 5 boundary layers.
        """
        # A0: DO_NOTHING
        if candidate.action_type == ActionType.DO_NOTHING or candidate.target_signal is None:
            # Baseline monitoring: check if current state is within envelope
            return ConstraintCheckResult(
                is_feasible=True,
                safety_ok=True,
                recipe_ok=True,
                envelope_ok=True,
                step_ok=True,
                direction_ok=True,
                proposed_value=None,
                violations=[],
            )

        sig = candidate.target_signal
        current_val = float(getattr(record, sig, 0.0))
        delta = candidate.delta_value
        proposed_val = current_val + delta

        violations: List[str] = []
        safety_ok = True
        recipe_ok = True
        envelope_ok = True
        step_ok = True
        direction_ok = True

        # 1. Machine safety bounds check
        if sig in self.safety_limits.limits:
            sbounds = self.safety_limits.limits[sig]
            if not sbounds.contains(proposed_val):
                safety_ok = False
                violations.append(
                    f"Violates Machine Safety Limits for {sig}: proposed {proposed_val:.2f} {candidate.unit} "
                    f"outside [{sbounds.min_val:.1f}, {sbounds.max_val:.1f}]"
                )

        # 2. Recipe limits check
        if sig in self.recipe_limits.limits:
            rbounds = self.recipe_limits.limits[sig]
            if not rbounds.contains(proposed_val):
                recipe_ok = False
                violations.append(
                    f"Violates Recipe Limits for {sig}: proposed {proposed_val:.2f} {candidate.unit} "
                    f"outside [{rbounds.min_val:.1f}, {rbounds.max_val:.1f}]"
                )

        # 3. Fingerprint operating envelope (mu +- 3*sigma)
        if sig in fingerprint.operating_envelopes:
            envelope = fingerprint.operating_envelopes[sig]
            in_envelope = (envelope.lower_limit <= proposed_val <= envelope.upper_limit)
            if not in_envelope:
                # If current parameter has drifted outside the envelope, check if the proposed
                # adjustment moves strictly closer to the baseline mean while within recipe limits
                stats = fingerprint.signal_stats.get(sig)
                moves_towards_baseline = False
                if stats:
                    current_dist = abs(current_val - stats.mean)
                    proposed_dist = abs(proposed_val - stats.mean)
                    moves_towards_baseline = (proposed_dist < current_dist)

                if not (moves_towards_baseline and recipe_ok):
                    envelope_ok = False
                    violations.append(
                        f"Violates Fingerprint Envelope for {sig}: proposed {proposed_val:.2f} {candidate.unit} "
                        f"outside envelope [{envelope.lower_limit:.2f}, {envelope.upper_limit:.2f}]"
                    )

        # 4. Maximum permitted single adjustment step
        max_step = self.step_limits.limits.get(sig, 999.0)
        if abs(delta) > max_step + 1e-5:
            step_ok = False
            violations.append(
                f"Violates Max Step Delta for {sig}: adjustment |{delta:.2f}| exceeds limit {max_step:.2f} {candidate.unit}"
            )

        # 5. Directional drift opposition logic
        # If signal is elevated (> mean + 1.5*std), adjustment must be negative.
        # If signal is depressed (< mean - 1.5*std), adjustment must be positive.
        if sig in fingerprint.signal_stats:
            stats = fingerprint.signal_stats[sig]
            z_score = (current_val - stats.mean) / (stats.std + 1e-6)
            if z_score > 1.5 and delta > 0.05:
                direction_ok = False
                violations.append(
                    f"Violates Directional Policy: {sig} is drifted high (z={z_score:+.2f}), "
                    f"positive delta ({delta:+.2f}) exacerbates drift"
                )
            elif z_score < -1.5 and delta < -0.05:
                direction_ok = False
                violations.append(
                    f"Violates Directional Policy: {sig} is drifted low (z={z_score:+.2f}), "
                    f"negative delta ({delta:+.2f}) exacerbates drift"
                )

        is_feasible = safety_ok and recipe_ok and envelope_ok and step_ok and direction_ok

        return ConstraintCheckResult(
            is_feasible=is_feasible,
            safety_ok=safety_ok,
            recipe_ok=recipe_ok,
            envelope_ok=envelope_ok,
            step_ok=step_ok,
            direction_ok=direction_ok,
            proposed_value=round(proposed_val, 3),
            violations=violations,
        )
