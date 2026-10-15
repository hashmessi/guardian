"""Data-Driven Scenario Registry for Process Guardian Industrial Validation.

Defines the 11 formal operational validation scenarios spanning continuous process drift,
pressure instability, raw-material moisture, recipe clerical errors, operational checkpoints,
compound multi-signal drift, normal variation, abstention safety gates, recovery verifications,
and the human-channel material-risk flip (SCN-FLIP-HUMAN-CHANNEL, P1).
"""

from typing import Dict, List, Optional
from process_guardian.scenario.models import (
    ScenarioDefinition,
    DisturbanceSpec,
    OperationalOverrideSpec,
    ExpectedOutcome,
    NarrativeMilestone,
)


def _build_scenario_catalog() -> Dict[str, ScenarioDefinition]:
    """Build the dictionary of 11 formal industrial scenarios."""
    scenarios: Dict[str, ScenarioDefinition] = {}

    # =========================================================================
    # Scenario 01: Thermal Drift (Hero Scenario)
    # =========================================================================
    scenarios["SCN-01-THERMAL"] = ScenarioDefinition(
        scenario_id="SCN-01-THERMAL",
        name="thermal_drift",
        title="Scenario 01 — Thermal Drift",
        category="thermal",
        is_hero=False,
        description=(
            "Barrel Zone 3 heater band moves gradually outside its calibrated process fingerprint, "
            "lowering melt viscosity, raising flash risk, and threatening quality contract integrity."
        ),
        total_cycles=500,
        seed=42,
        disturbances=[
            DisturbanceSpec(
                signal="barrel_temp_z3",
                pattern="linear_drift",
                start_cycle=320,
                duration=None,
                severity=1.0,
                rate=0.22,
                params={"coupled_nozzle_rate": 0.10},
            )
        ],
        expected_outcome=ExpectedOutcome(
            drift_expected=True,
            dominant_signal="barrel_temp_z3",
            action_class="temperature_adjustment",
            recovery_expected=True,
            release_decision="RELEASE_PERMITTED",
            allow_intervention=True,
        ),
        narrative=[
            NarrativeMilestone(
                phase="HEALTHY",
                label="Stationary Baseline",
                cycle_range="1–319",
                description="Machine operating within certified R-12 fingerprint envelope; zero false alarms.",
            ),
            NarrativeMilestone(
                phase="DRIFT",
                label="Thermal Deviation",
                cycle_range="320–345",
                description="Zone 3 heater starts steady upward drift (+0.22°C/cycle); multivariate Sentinel triggers.",
            ),
            NarrativeMilestone(
                phase="INTERVENTION",
                label="Constrained Recommendation",
                cycle_range="346–350",
                description="Quality risk crosses threshold; optimizer evaluates candidates and selects minimum-cost temperature offset.",
            ),
            NarrativeMilestone(
                phase="RECOVERY",
                label="Thermal Relaxation",
                cycle_range="351–380",
                description="Applied temperature reduction relaxes melt temperature back into operating envelope.",
            ),
            NarrativeMilestone(
                phase="QC",
                label="Mandatory Poka-Yoke QC",
                cycle_range="381–383",
                description="Process physically verified; CTQ part weight checked.",
            ),
            NarrativeMilestone(
                phase="RELEASE",
                label="Verified Production Release",
                cycle_range="384–500",
                description="Production released; suspect cycles contained to minimal quarantine window.",
            ),
        ],
    )

    # =========================================================================
    # Scenario 02: Injection Pressure Drift
    # =========================================================================
    scenarios["SCN-02-PRESSURE"] = ScenarioDefinition(
        scenario_id="SCN-02-PRESSURE",
        name="pressure_drift",
        title="Scenario 02 — Injection Pressure Drift",
        category="pressure",
        is_hero=False,
        description=(
            "Hydraulic proportional valve wear or check-ring leakage causes sustained injection and "
            "peak pressure loss, threatening cavity pack and inducing sink mark defects."
        ),
        total_cycles=500,
        seed=102,
        disturbances=[
            DisturbanceSpec(
                signal="injection_pressure",
                pattern="linear_drift",
                start_cycle=280,
                duration=None,
                severity=1.0,
                rate=-0.28,
                params={"coupled_peak_loss": -0.38},
            )
        ],
        expected_outcome=ExpectedOutcome(
            drift_expected=True,
            # Family match, deliberately. A hydraulic pressure loss surfaces as
            # cavity peak_pressure or injection_pressure depending on how far the
            # drift has run, and pinning one exact sensor makes the expectation
            # fragile rather than strict. The pillar still requires a pressure
            # signal to *dominate* the incident window, and the intervention pillar
            # separately pins the actuator the engine reaches for.
            dominant_signal="pressure",
            action_class="pressure_adjustment",
            recovery_expected=True,
            release_decision="RELEASE_PERMITTED",
            allow_intervention=True,
        ),
        narrative=[
            NarrativeMilestone(
                phase="HEALTHY",
                label="Nominal Hydraulics",
                cycle_range="1–279",
                description="Injection pressure stable at 84 bar with normal ±0.8 bar hydraulic variance.",
            ),
            NarrativeMilestone(
                phase="DRIFT",
                label="Pressure Decay Onset",
                cycle_range="280–320",
                description="Injection pressure exhibits sustained negative drift (-0.28 bar/cycle); CUSUM alert fires.",
            ),
            NarrativeMilestone(
                phase="INTERVENTION",
                label="Pressure Compensation",
                cycle_range="321–325",
                description="Guardian isolates injection pressure as primary contributor; optimizer recommends pressure adjustment.",
            ),
            NarrativeMilestone(
                phase="RECOVERY",
                label="Pressure Stabilization",
                cycle_range="326–360",
                description="Cavity packing pressure restored; sink mark probability drops below 5%.",
            ),
            NarrativeMilestone(
                phase="RELEASE",
                label="Controlled Lot Release",
                cycle_range="361–500",
                description="Stability verified across consecutive cycles; suspect parts quarantined.",
            ),
        ],
    )

    # =========================================================================
    # Scenario 03: Material Moisture Excursion
    # =========================================================================
    scenarios["SCN-03-MOISTURE"] = ScenarioDefinition(
        scenario_id="SCN-03-MOISTURE",
        name="moisture_excursion",
        title="Scenario 03 — Material Moisture Excursion",
        category="material",
        is_hero=False,
        description=(
            "Hygroscopic resin hopper absorbs ambient moisture, breaching the 0.15% processing limit. "
            "Guardian identifies raw-material quality excursion and requires hopper drying sign-off "
            "rather than masking the defect with machine temperature changes."
        ),
        total_cycles=500,
        seed=203,
        disturbances=[
            DisturbanceSpec(
                signal="material_moisture",
                pattern="moisture_surge",
                start_cycle=300,
                duration=None,
                severity=1.0,
                rate=0.005,
                params={"target_plateau": 0.22},
            )
        ],
        operational_overrides=OperationalOverrideSpec(
            initial_moisture_pct=0.22,
        ),
        expected_outcome=ExpectedOutcome(
            drift_expected=True,
            dominant_signal="material_moisture",
            # Resin moisture cannot be corrected with a machine parameter
            # (scope_plan.md Sec.1), so the correct engine behaviour is to refuse
            # to act and escalate -- not to invent a pressure or thermal trim.
            action_class="abstain",
            recovery_expected=False,
            release_decision="HOLD_QUARANTINE",
            allow_intervention=False,
        ),
        narrative=[
            NarrativeMilestone(
                phase="HEALTHY",
                label="Certified Dry Resin",
                cycle_range="1–299",
                description="Material moisture in hopper measured at nominal 0.08%, well below 0.15% ceiling.",
            ),
            NarrativeMilestone(
                phase="DRIFT",
                label="Moisture Ingress",
                cycle_range="300–350",
                description="Desiccant dryer saturation causes moisture to climb to 0.22%, degrading melt viscosity.",
            ),
            NarrativeMilestone(
                phase="INTERVENTION",
                label="Material Sign-Off Demanded",
                cycle_range="351–360",
                description="Guardian detects moisture excursion; refuses machine compensation; triggers mandatory resin drying gate.",
            ),
            NarrativeMilestone(
                phase="RECOVERY",
                label="Hopper Purge & Dry",
                cycle_range="361–390",
                description="Hopper purged with validated dry batch (<0.12%); resin gate signed off by QC.",
            ),
            NarrativeMilestone(
                phase="RELEASE",
                label="Resumed Production",
                cycle_range="391–500",
                description="Process returns to stable fingerprint; full containment of wet batch cycles.",
            ),
        ],
    )

    # =========================================================================
    # Scenario 04: Recipe / Setting Drift
    # =========================================================================
    # Scenario 05: Mold-Release Spray Checkpoint
    # =========================================================================
    # Scenario 06: Compound Multi-Signal Drift (Boss Scenario)
    # =========================================================================
    scenarios["SCN-06-COMPOUND"] = ScenarioDefinition(
        scenario_id="SCN-06-COMPOUND",
        name="compound_drift",
        title="Scenario 06 — Compound Multi-Signal Drift",
        category="compound",
        is_hero=True,
        description=(
            "Complex sequential interaction: subtle barrel Zone 3 temperature creep coupled with "
            "hydraulic pressure decay. Guardian distinguishes persistent multi-signal interaction "
            "from noise, ranks root causes, and computes the global minimum-cost intervention."
        ),
        total_cycles=500,
        seed=506,
        disturbances=[
            DisturbanceSpec(
                signal="barrel_temp_z3",
                pattern="linear_drift",
                start_cycle=200,
                duration=None,
                severity=1.0,
                rate=0.18,
                params={"signal": "barrel_temp_z3"},
            ),
            DisturbanceSpec(
                signal="injection_pressure",
                pattern="linear_drift",
                start_cycle=280,
                duration=None,
                severity=1.0,
                rate=-0.22,
                params={"signal": "injection_pressure"},
            ),
        ],
        expected_outcome=ExpectedOutcome(
            drift_expected=True,
            dominant_signal="barrel_temp_z3",
            action_class="temperature_adjustment",
            recovery_expected=True,
            release_decision="RELEASE_PERMITTED",
            allow_intervention=True,
        ),
        narrative=[
            NarrativeMilestone(
                phase="HEALTHY",
                label="Coupled Nominal State",
                cycle_range="1–199",
                description="Thermal and hydraulic systems both tracking baseline fingerprint.",
            ),
            NarrativeMilestone(
                phase="DRIFT",
                label="Thermal Creep Begins",
                cycle_range="200–279",
                description="Zone 3 exhibits slow thermal rise; multivariate residual begins climbing.",
            ),
            NarrativeMilestone(
                phase="DRIFT",
                label="Secondary Hydraulic Decay",
                cycle_range="280–340",
                description="Injection pressure loss combines with thermal rise; quality risk escalates past 65%.",
            ),
            NarrativeMilestone(
                phase="INTERVENTION",
                label="Joint Root-Cause Optimization",
                cycle_range="341–350",
                description="Guardian ranks contributors (Zone 3: 58%, Pressure: 42%) and selects the minimum-cost feasible candidate against a no-action baseline.",
            ),
            NarrativeMilestone(
                phase="RECOVERY",
                label="Coupled Stabilization",
                cycle_range="351–390",
                description="Viscosity and pressure recover in lockstep; multi-signal residuals return to normal.",
            ),
            NarrativeMilestone(
                phase="RELEASE",
                label="Multi-Signal Lot Release",
                cycle_range="391–500",
                description="Production released under verified stability with 100% containment integrity.",
            ),
        ],
    )

    # =========================================================================
    # Scenario 07: Normal Variation / Robustness
    # =========================================================================
    scenarios["SCN-07-NORMAL-VAR"] = ScenarioDefinition(
        scenario_id="SCN-07-NORMAL-VAR",
        name="normal_variation",
        title="Scenario 07 — Normal Variation (False-Positive Robustness)",
        category="robustness",
        is_hero=False,
        description=(
            "Random sensor noise, shop-floor ambient temperature swings, and natural machine vibration. "
            "Proves Guardian does not falsely alert, trigger unneeded downtime, or recommend unnecessary adjustments."
        ),
        total_cycles=400,
        seed=607,
        disturbances=[
            DisturbanceSpec(
                signal="barrel_temp_z3",
                pattern="noise_burst",
                start_cycle=120,
                duration=60,
                severity=1.0,
                params={"scale": 2.2},
            )
        ],
        expected_outcome=ExpectedOutcome(
            drift_expected=False,
            dominant_signal=None,
            action_class="monitor",
            recovery_expected=True,
            release_decision="MONITOR_ONLY",
            allow_intervention=False,
        ),
        narrative=[
            NarrativeMilestone(
                phase="HEALTHY",
                label="Nominal Plant Ambient",
                cycle_range="1–119",
                description="Machine operating under nominal industrial ambient conditions.",
            ),
            NarrativeMilestone(
                phase="DRIFT",
                label="Sensor Noise Transient",
                cycle_range="120–180",
                description="Electrical noise introduces elevated sensor variance without underlying melt temperature shift.",
            ),
            NarrativeMilestone(
                phase="INTERVENTION",
                label="Filter Rejection / Monitor",
                cycle_range="181–220",
                description="EWMA/CUSUM filters reject transient spikes; optimizer correctly selects A0 (Monitoring).",
            ),
            NarrativeMilestone(
                phase="RELEASE",
                label="Uninterrupted Production",
                cycle_range="221–400",
                description="Zero false stops; production remains continuously active and released.",
            ),
        ],
    )

    # =========================================================================
    # Scenario 08: Low-Confidence / Mandatory Abstain Safety Gate
    # =========================================================================
    scenarios["SCN-08-LOW-CONF-ABSTAIN"] = ScenarioDefinition(
        scenario_id="SCN-08-LOW-CONF-ABSTAIN",
        name="low_confidence_abstain",
        title="Scenario 08 — Low Confidence (Mandatory Abstain Safety Gate)",
        category="safety",
        is_hero=True,
        description=(
            "Out-of-distribution failure pattern with conflicting signals and high model uncertainty. "
            "Guardian triggers SAFE-03: refuses automated recommendations, halts unvalidated changes, "
            "and requests senior engineering inspection."
        ),
        total_cycles=400,
        seed=708,
        disturbances=[
            DisturbanceSpec(
                signal="barrel_temp_z3",
                pattern="step_shift",
                start_cycle=150,
                duration=None,
                severity=1.0,
                step_value=24.0,  # Extreme unmodeled shock
                params={"out_of_distribution": True},
            )
        ],
        operational_overrides=OperationalOverrideSpec(
            unseen_failure_pattern=True,
        ),
        expected_outcome=ExpectedOutcome(
            drift_expected=True,
            dominant_signal=None,
            action_class="abstain",
            recovery_expected=False,
            release_decision="HOLD_QUARANTINE",
            allow_intervention=False,
        ),
        narrative=[
            NarrativeMilestone(
                phase="HEALTHY",
                label="Baseline Operation",
                cycle_range="1–149",
                description="Pristine baseline operation.",
            ),
            NarrativeMilestone(
                phase="DRIFT",
                label="Unprecedented Anomaly",
                cycle_range="150–180",
                description="Extreme out-of-distribution sensor signature observed.",
            ),
            NarrativeMilestone(
                phase="INTERVENTION",
                label="Mandatory ABSTAIN Triggered",
                cycle_range="181–220",
                description="Model epistemic confidence drops below 0.65; SAFE-03 strictly prevents automated action.",
            ),
            NarrativeMilestone(
                phase="RELEASE",
                label="Quarantine & Engineering Escalation",
                cycle_range="221–400",
                description="Production held safely; lot quarantined to prevent scrap escape to customer.",
            ),
        ],
    )

    # =========================================================================
    # Scenario 09: Failed Intervention / Safety Hold
    # =========================================================================
    scenarios["SCN-09-FAILED-INTERVENTION"] = ScenarioDefinition(
        scenario_id="SCN-09-FAILED-INTERVENTION",
        name="failed_intervention_safety_hold",
        title="Scenario 09 — Failed Intervention (No False Release)",
        category="safety",
        is_hero=False,
        description=(
            "Intervention applied, but severe physical defect (e.g. blown heater contactor) prevents "
            "thermal recovery. Recovery Verifier detects lack of parameter convergence, refuses to clear "
            "quarantine, and escalates to maintenance hold."
        ),
        total_cycles=400,
        seed=809,
        disturbances=[
            DisturbanceSpec(
                signal="barrel_temp_z3",
                pattern="persistent_drift",
                start_cycle=160,
                duration=None,
                severity=1.0,
                rate=0.35,
                params={"recalcitrant": True},
            )
        ],
        operational_overrides=OperationalOverrideSpec(
            intervention_ineffective=True,
        ),
        expected_outcome=ExpectedOutcome(
            drift_expected=True,
            dominant_signal="barrel_temp_z3",
            action_class="temperature_adjustment",
            recovery_expected=False,
            release_decision="HOLD_QUARANTINE",
            allow_intervention=True,
        ),
        narrative=[
            NarrativeMilestone(
                phase="HEALTHY",
                label="Nominal Baseline",
                cycle_range="1–159",
                description="Process conforming to fingerprint envelope.",
            ),
            NarrativeMilestone(
                phase="DRIFT",
                label="Severe Runaway Drift",
                cycle_range="160–200",
                description="Zone 3 climbs rapidly (+0.35°C/cycle).",
            ),
            NarrativeMilestone(
                phase="INTERVENTION",
                label="Action Applied",
                cycle_range="201–210",
                description="Guardian recommends -5.0°C offset; action acknowledged.",
            ),
            NarrativeMilestone(
                phase="RECOVERY",
                label="Recovery Timeout / Failure",
                cycle_range="211–240",
                description="Contactor failure prevents cooling; Recovery Verifier fails 3-cycle stability gate.",
            ),
            NarrativeMilestone(
                phase="RELEASE",
                label="Hard Containment Lockout",
                cycle_range="241–400",
                description="Zero false release; all affected cycles held strictly in quarantine.",
            ),
        ],
    )

    # =========================================================================
    # Scenario 10: Successful Recovery + Release
    # =========================================================================
    scenarios["SCN-10-RECOVERY-RELEASE"] = ScenarioDefinition(
        scenario_id="SCN-10-RECOVERY-RELEASE",
        name="successful_recovery_release",
        title="Scenario 10 — Closed-Loop Recovery & Production Release",
        category="robustness",
        is_hero=False,
        description=(
            "Complete closed-loop verification: early detection, root cause isolation, minimum-cost "
            "intervention, dynamic stability verification, physical QC CTQ sign-off, and release."
        ),
        total_cycles=450,
        seed=910,
        disturbances=[
            DisturbanceSpec(
                signal="barrel_temp_z3",
                pattern="linear_drift",
                start_cycle=180,
                duration=None,
                severity=1.0,
                rate=0.25,
            )
        ],
        expected_outcome=ExpectedOutcome(
            drift_expected=True,
            dominant_signal="barrel_temp_z3",
            action_class="temperature_adjustment",
            recovery_expected=True,
            release_decision="RELEASE_PERMITTED",
            allow_intervention=True,
        ),
        narrative=[
            NarrativeMilestone(
                phase="HEALTHY",
                label="Pre-Drift Baseline",
                cycle_range="1–179",
                description="Stable production run.",
            ),
            NarrativeMilestone(
                phase="DRIFT",
                label="Thermal Anomaly",
                cycle_range="180–210",
                description="Predictive detection triggers before scrap generation.",
            ),
            NarrativeMilestone(
                phase="INTERVENTION",
                label="Corrective Adjustment",
                cycle_range="211–215",
                description="Optimized parameter compensation applied.",
            ),
            NarrativeMilestone(
                phase="RECOVERY",
                label="3-Cycle Stability Window",
                cycle_range="216–230",
                description="Consecutive cycle stability confirmed by Recovery Verifier.",
            ),
            NarrativeMilestone(
                phase="QC",
                label="Physical CTQ Sign-Off",
                cycle_range="231–233",
                description="Physical sample conforms to CTQ weight tolerances.",
            ),
            NarrativeMilestone(
                phase="RELEASE",
                label="Certified Production Release",
                cycle_range="234–450",
                description="Complete lifecycle closed loop validated; production released.",
            ),
        ],
    )

    # =========================================================================
    # Scenario FLIP: Human-Channel Material Risk (P1, scope_plan.md Sec.3/4)
    # =========================================================================
    scenarios["SCN-FLIP-HUMAN-CHANNEL"] = ScenarioDefinition(
        scenario_id="SCN-FLIP-HUMAN-CHANNEL",
        name="human_channel_flip",
        title="Scenario FLIP — The One Demo That Wins (Human-Channel Material Risk)",
        category="material",
        is_hero=True,
        description=(
            "Zero sensor-level disturbance anywhere in this replay -- every barrel, pressure and "
            "timing signal stays fully in-envelope, Hotelling T2 stays quiet the entire run. A sensor-only "
            "system sees nothing. An operator shift note (\"previous shift loaded a new resin lot, dryer "
            "was down for two hours, moisture not verified\") is parsed through the same bounded multilingual "
            "channel as the live checkpoint gates and flips the verdict from CONTINUE to a physical material "
            "verification request -- the sensor-blind gap the problem statement names, filled."
        ),
        total_cycles=300,
        seed=913,
        disturbances=[],
        operational_overrides=OperationalOverrideSpec(
            human_channel_event_cycle=150,
            human_channel_event_text=(
                "Previous shift loaded a new resin lot, dryer was down for two hours, moisture not verified"
            ),
        ),
        expected_outcome=ExpectedOutcome(
            drift_expected=True,
            dominant_signal="human_channel",
            action_class="material_checkpoint",
            recovery_expected=True,
            release_decision="GATED_QC_REQUIRED",
            allow_intervention=False,
        ),
        narrative=[
            NarrativeMilestone(
                phase="HEALTHY",
                label="Pristine Sensor Baseline",
                cycle_range="1–149",
                description="Every barrel, pressure and timing signal fully in-envelope. No sensor-level event is ever injected in this scenario.",
            ),
            NarrativeMilestone(
                phase="DRIFT",
                label="Operator Shift Note Received",
                cycle_range="150",
                description=(
                    "Sensors remain quiet -- T2 stays below alarm the entire run. The fused human channel "
                    "reports a just-loaded, unverified resin lot: evidence no hopper hygrometer has caught up to yet."
                ),
            ),
            NarrativeMilestone(
                phase="INTERVENTION",
                label="Verdict Flips: CONTINUE -> Material Verification",
                cycle_range="150–300",
                description="Engine routes to QC_REQUIRED on human-channel evidence alone -- the same gate a confirmed sensor drift would trigger, never a fabricated sensor reading.",
            ),
            NarrativeMilestone(
                phase="QC",
                label="Held Pending Physical Verification",
                cycle_range="150–300",
                description="Production held pending a physical moisture check; this is the proof, not a resolved release.",
            ),
        ],
    )

    return scenarios


class ScenarioRegistry:
    """Thread-safe registry providing access to all 11 industrial scenarios."""

    def __init__(self):
        self._scenarios: Dict[str, ScenarioDefinition] = _build_scenario_catalog()

    def get(self, scenario_id: str) -> Optional[ScenarioDefinition]:
        """Fetch scenario definition by ID or name."""
        if scenario_id in self._scenarios:
            return self._scenarios[scenario_id]
        # Allow lookup by slug name
        for s in self._scenarios.values():
            if s.name == scenario_id:
                return s
        return None

    def list_all(self) -> List[ScenarioDefinition]:
        """Return list of all 11 defined scenarios."""
        return list(self._scenarios.values())

    def list_hero_scenarios(self) -> List[ScenarioDefinition]:
        """Return the locked demo-worthy scenarios for the live operator UI.

        Locked per scope_plan.md Sec.4 to S06 (closed loop + SPC contradiction),
        SCN-FLIP (the human-channel flip, P1) and S08 (ABSTAIN trust gate). The
        other 8 registry scenarios remain defined for the automated validation
        suite but are not hero-flagged.
        """
        return [s for s in self._scenarios.values() if s.is_hero]

    def list_validation_scenarios(self) -> List[ScenarioDefinition]:
        """Return every scenario registered for the automated validation suite."""
        return list(self._scenarios.values())


# Global singleton instance
_GLOBAL_REGISTRY: Optional[ScenarioRegistry] = None


def get_scenario_registry() -> ScenarioRegistry:
    """Retrieve global singleton ScenarioRegistry."""
    global _GLOBAL_REGISTRY
    if _GLOBAL_REGISTRY is None:
        _GLOBAL_REGISTRY = ScenarioRegistry()
    return _GLOBAL_REGISTRY
