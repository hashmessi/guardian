"""PS02 Shop-Floor Operational Checkpoints Engine (QCHK-02).

Evaluates 3 mandatory shop-floor operational gates required for injection molding release:
1. Recipe Verification Lock: Compares machine parameters with signed recipe tolerances (R-12).
2. Resin Moisture Batch Sign-Off: Material hopper moisture <= 0.15% (Fraunhofer/SKZ limit).
3. Mold-Release Spray Interval Tracking: Scheduled every 50 cycles; overdue if > 60 cycles.
"""

from typing import Dict, List, Optional, Any, Tuple
from pydantic import BaseModel, Field

from process_guardian.llm.human_channel import (
    CONFIDENCE_THRESHOLD,
    BoundedChoice,
    CheckpointQuestion,
    HumanChannelClient,
    HumanChannelSignal,
)


class RecipeParameterSpec(BaseModel):
    name: str
    nominal: float
    tolerance: float
    unit: str

    @property
    def min_val(self) -> float:
        return self.nominal - self.tolerance

    @property
    def max_val(self) -> float:
        return self.nominal + self.tolerance


# Automotive R-12 Signed Master Recipe
R12_RECIPE_SPECS: Dict[str, RecipeParameterSpec] = {
    "zone_1_temp": RecipeParameterSpec(name="Zone 1 Temp", nominal=235.0, tolerance=5.0, unit="°C"),
    "zone_2_temp": RecipeParameterSpec(name="Zone 2 Temp", nominal=240.0, tolerance=5.0, unit="°C"),
    "zone_3_temp": RecipeParameterSpec(name="Zone 3 Temp", nominal=245.0, tolerance=5.0, unit="°C"),
    "zone_4_temp": RecipeParameterSpec(name="Zone 4 Temp", nominal=250.0, tolerance=5.0, unit="°C"),
    "holding_pressure": RecipeParameterSpec(name="Holding Pressure", nominal=75.0, tolerance=8.0, unit="bar"),
    "injection_speed": RecipeParameterSpec(name="Injection Speed", nominal=45.0, tolerance=5.0, unit="mm/s"),
    "cooling_time": RecipeParameterSpec(name="Cooling Time", nominal=14.0, tolerance=2.0, unit="s"),
}


class RecipeCheckpointStatus(BaseModel):
    recipe_id: str = "R-12"
    status: str = "PASS"  # PASS or FAIL
    is_locked: bool = False
    parameter_deviations: List[str] = Field(default_factory=list)
    active_parameters: Dict[str, float] = Field(default_factory=dict)


class MoistureCheckpointStatus(BaseModel):
    batch_id: str = "BATCH-PA66-202610"
    moisture_pct: float
    max_threshold_pct: float = 0.15
    status: str = "PASS"  # PASS or FAIL
    status_label: str = "DRYING_SPEC_SATISFIED"
    inspector_id: str
    notes: Optional[str] = None


class MoldReleaseCheckpointStatus(BaseModel):
    last_spray_cycle: int
    current_cycle: int
    cycles_since_spray: int
    scheduled_interval_cycles: int = 50
    overdue_limit_cycles: int = 60
    status: str = "PASS"  # PASS, WARNING, or FAIL
    status_label: str = "SPRAY_SCHEDULE_NORMAL"
    last_operator_id: Optional[str] = None


class OperationalCheckpointsReport(BaseModel):
    """Unified evaluation of PS02 shop-floor operational checkpoints (QCHK-02)."""
    recipe_verification: RecipeCheckpointStatus
    resin_moisture: MoistureCheckpointStatus
    mold_release_spray: MoldReleaseCheckpointStatus
    overall_clearance: bool
    clearance_status: str  # CLEARED or GATED
    blocking_reasons: List[str] = Field(default_factory=list)


class OperationalCheckpointsEvaluator:
    """Evaluates and manages the 3 PS02 shop-floor operational checkpoints."""

    MAX_MOISTURE_PCT: float = 0.15
    SPRAY_INTERVAL: int = 50
    SPRAY_OVERDUE_LIMIT: int = 60

    def __init__(self):
        self.recipe_specs = R12_RECIPE_SPECS
        self.last_spray_cycle: int = 0
        self.last_spray_operator: Optional[str] = "OP-SYS"
        self.active_moisture_pct: float = 0.08
        self.active_moisture_inspector: str = "QC-101"
        self.active_batch_id: str = "BATCH-PA66-202610"
        self.human_channel = HumanChannelClient()

    def record_spray(self, cycle_index: int, operator_id: str = "OP-104") -> None:
        """Record mold release spray application at a specific cycle."""
        self.last_spray_cycle = cycle_index
        self.last_spray_operator = operator_id

    def update_moisture_signoff(
        self, moisture_pct: float, inspector_id: str, batch_id: Optional[str] = None
    ) -> None:
        """Record moisture check sign-off for resin hopper."""
        self.active_moisture_pct = moisture_pct
        self.active_moisture_inspector = inspector_id
        if batch_id:
            self.active_batch_id = batch_id

    def evaluate_recipe(self, active_params: Dict[str, float]) -> RecipeCheckpointStatus:
        """Evaluate active machine parameters against signed recipe R-12."""
        deviations: List[str] = []
        for key, spec in self.recipe_specs.items():
            if key in active_params:
                val = active_params[key]
                if val < spec.min_val or val > spec.max_val:
                    deviations.append(
                        f"{spec.name} {val:.1f}{spec.unit} out of tolerance "
                        f"[{spec.min_val:.1f} - {spec.max_val:.1f}{spec.unit}]"
                    )

        is_pass = len(deviations) == 0
        return RecipeCheckpointStatus(
            recipe_id="R-12",
            status="PASS" if is_pass else "FAIL",
            is_locked=not is_pass,
            parameter_deviations=deviations,
            active_parameters=active_params,
        )

    def evaluate_moisture(
        self,
        moisture_pct: Optional[float] = None,
        inspector_id: Optional[str] = None,
        batch_id: Optional[str] = None,
    ) -> MoistureCheckpointStatus:
        """Evaluate resin moisture against Fraunhofer/SKZ non-linear 0.15% threshold."""
        m_pct = moisture_pct if moisture_pct is not None else self.active_moisture_pct
        insp_id = inspector_id if inspector_id is not None else self.active_moisture_inspector
        b_id = batch_id if batch_id is not None else self.active_batch_id

        if m_pct > self.MAX_MOISTURE_PCT:
            status = "FAIL"
            status_label = "BLOCKED_DRYING_REQUIRED"
            notes = f"Moisture {m_pct:.2f}% exceeds 0.15% max spec. Hydrolysis & splay risk."
        else:
            status = "PASS"
            status_label = "DRYING_SPEC_SATISFIED"
            notes = f"Moisture {m_pct:.2f}% within automotive spec (<= 0.15%)."

        return MoistureCheckpointStatus(
            batch_id=b_id,
            moisture_pct=m_pct,
            max_threshold_pct=self.MAX_MOISTURE_PCT,
            status=status,
            status_label=status_label,
            inspector_id=insp_id,
            notes=notes,
        )

    def evaluate_mold_spray(self, current_cycle: int) -> MoldReleaseCheckpointStatus:
        """Track cycle interval since last mold-release spray application."""
        cycles_since = max(0, current_cycle - self.last_spray_cycle)
        
        if cycles_since <= self.SPRAY_INTERVAL:
            status = "PASS"
            status_label = "SPRAY_SCHEDULE_NORMAL"
        elif cycles_since <= self.SPRAY_OVERDUE_LIMIT:
            status = "WARNING"
            status_label = "SPRAY_DUE_SOON"
        else:
            status = "FAIL"
            status_label = "SPRAY_OVERDUE_APPLY_NOW"

        return MoldReleaseCheckpointStatus(
            last_spray_cycle=self.last_spray_cycle,
            current_cycle=current_cycle,
            cycles_since_spray=cycles_since,
            scheduled_interval_cycles=self.SPRAY_INTERVAL,
            overdue_limit_cycles=self.SPRAY_OVERDUE_LIMIT,
            status=status,
            status_label=status_label,
            last_operator_id=self.last_spray_operator,
        )

    def record_spray_from_text(
        self, text: str, cycle_index: int, operator_id: str = "HUMAN-CHANNEL"
    ) -> Tuple[MoldReleaseCheckpointStatus, HumanChannelSignal]:
        """Parse a bounded "spray done this interval?" confirmation (P0, scope_plan.md
        Sec.3) and, if confident, record it the same as the structured endpoint. A
        negative or low-confidence answer leaves the counter untouched: no state
        change on an unclear signal (SAFE-03)."""
        signal = self.human_channel.parse(text, CheckpointQuestion.SPRAY_DONE)
        if signal.choice == BoundedChoice.YES and signal.confidence >= CONFIDENCE_THRESHOLD:
            self.record_spray(cycle_index=cycle_index, operator_id=operator_id)
        return self.evaluate_mold_spray(current_cycle=cycle_index), signal

    def attest_moisture_signoff_from_text(self, text: str) -> HumanChannelSignal:
        """Parse a bounded "resin lot dried & signed?" confirmation. Corroborating
        evidence only -- it never substitutes a measured moisture %; the engine still
        decides off the sensor reading in evaluate_moisture() (scope_plan.md Sec.6
        rule 1)."""
        return self.human_channel.parse(text, CheckpointQuestion.MOISTURE_SIGNED)

    def attest_recipe_setpoint_from_text(self, text: str) -> HumanChannelSignal:
        """Parse a bounded "setpoint matches recipe R-12?" confirmation. Corroborating
        evidence only -- the numeric parameter comparison in evaluate_recipe() remains
        the authority."""
        return self.human_channel.parse(text, CheckpointQuestion.RECIPE_MATCHES)

    def evaluate_all(
        self,
        current_cycle: int,
        active_params: Dict[str, float],
        moisture_pct: Optional[float] = None,
        inspector_id: Optional[str] = None,
    ) -> OperationalCheckpointsReport:
        """Generate comprehensive operational checkpoints clearance report."""
        recipe_status = self.evaluate_recipe(active_params)
        moisture_status = self.evaluate_moisture(moisture_pct, inspector_id)
        spray_status = self.evaluate_mold_spray(current_cycle)

        blocking_reasons: List[str] = []
        if recipe_status.status == "FAIL":
            blocking_reasons.append(
                f"Recipe Lock R-12 violation: {len(recipe_status.parameter_deviations)} parameter(s) out of tolerance"
            )
        if moisture_status.status == "FAIL":
            blocking_reasons.append(
                f"Resin Moisture Gate: {moisture_status.moisture_pct:.2f}% exceeds {self.MAX_MOISTURE_PCT:.2f}% limit"
            )
        if spray_status.status == "FAIL":
            blocking_reasons.append(
                f"Mold Spray Gate: {spray_status.cycles_since_spray} cycles since last spray (limit: {self.SPRAY_OVERDUE_LIMIT})"
            )

        overall_clearance = len(blocking_reasons) == 0
        clearance_status = "CLEARED" if overall_clearance else "GATED"

        return OperationalCheckpointsReport(
            recipe_verification=recipe_status,
            resin_moisture=moisture_status,
            mold_release_spray=spray_status,
            overall_clearance=overall_clearance,
            clearance_status=clearance_status,
            blocking_reasons=blocking_reasons,
        )
