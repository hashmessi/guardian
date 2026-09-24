"""Quality Contract specifications and compliance tolerance evaluation."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from process_guardian.adapter.schemas import NormalizedCycleRecord


@dataclass
class ToleranceRange:
    """Engineering tolerance specification for a single parameter."""
    min_val: float
    max_val: float
    target_val: Optional[float] = None
    unit: str = ""

    def is_within(self, value: float) -> bool:
        """Check if value is within strictly compliant bounds."""
        return self.min_val <= value <= self.max_val

    def get_deviation(self, value: float) -> float:
        """Return distance outside tolerance bounds (0.0 if compliant)."""
        if value < self.min_val:
            return self.min_val - value
        elif value > self.max_val:
            return value - self.max_val
        return 0.0


@dataclass
class ContractEvaluationResult:
    """Result of evaluating a cycle against the active Quality Contract."""
    is_compliant: bool
    violations: List[str]
    deviations: Dict[str, float]
    defect_risk_indicator: float  # [0.0, 1.0] derived from worst tolerance breach


@dataclass
class QualityContract:
    """
    Automotive Tier-2/Tier-3 plastic injection molding Quality Contract.
    
    Defines strict tolerance limits for critical part dimensions, surface defects,
    and key physical process parameters (QRSK-03).
    """
    part_id: str = "PART-AUTO-HOUSING-A"
    revision: str = "1.0"
    
    # Part quality limits
    part_weight: ToleranceRange = field(
        default_factory=lambda: ToleranceRange(min_val=141.0, max_val=144.0, target_val=142.5, unit="g")
    )
    max_sink_mark_depth: float = 0.08  # mm max allowable sink mark
    allow_flash: bool = False  # Zero tolerance on parting line flash

    # Critical process window limits
    peak_pressure: ToleranceRange = field(
        default_factory=lambda: ToleranceRange(min_val=122.0, max_val=148.0, target_val=135.0, unit="bar")
    )
    cycle_time: ToleranceRange = field(
        default_factory=lambda: ToleranceRange(min_val=26.5, max_val=30.5, target_val=28.5, unit="s")
    )
    barrel_temp_z3: ToleranceRange = field(
        default_factory=lambda: ToleranceRange(min_val=225.0, max_val=235.0, target_val=230.0, unit="°C")
    )

    def evaluate(self, record: NormalizedCycleRecord) -> ContractEvaluationResult:
        """
        Evaluate a cycle record against the contract specifications.
        """
        violations: List[str] = []
        deviations: Dict[str, float] = {}

        # 1. Part weight check
        w_dev = self.part_weight.get_deviation(record.part_weight)
        if w_dev > 0:
            violations.append(
                f"Part weight ({record.part_weight:.2f}g) outside tolerance [{self.part_weight.min_val}, {self.part_weight.max_val}]g"
            )
            deviations["part_weight"] = w_dev

        # 2. Sink mark check
        if record.sink_mark_depth > self.max_sink_mark_depth:
            violations.append(
                f"Sink mark depth ({record.sink_mark_depth:.3f}mm) exceeds contract limit ({self.max_sink_mark_depth}mm)"
            )
            deviations["sink_mark_depth"] = record.sink_mark_depth - self.max_sink_mark_depth

        # 3. Flash check
        if record.flash_observed and not self.allow_flash:
            violations.append("Parting-line flash observed on molded component")
            deviations["flash_observed"] = 1.0

        # 4. Peak cavity pressure check
        p_dev = self.peak_pressure.get_deviation(record.peak_pressure)
        if p_dev > 0:
            violations.append(
                f"Peak pressure ({record.peak_pressure:.1f} bar) outside contract range [{self.peak_pressure.min_val}, {self.peak_pressure.max_val}]"
            )
            deviations["peak_pressure"] = p_dev

        # 5. Cycle time check
        c_dev = self.cycle_time.get_deviation(record.cycle_time)
        if c_dev > 0:
            violations.append(
                f"Cycle time ({record.cycle_time:.2f}s) outside tolerance [{self.cycle_time.min_val}, {self.cycle_time.max_val}]s"
            )
            deviations["cycle_time"] = c_dev

        # Composite risk indicator
        is_compliant = len(violations) == 0
        if is_compliant:
            defect_indicator = 0.0
        else:
            # Scale severity based on presence of direct part defects (flash/sink/weight) vs process deviations
            has_part_defect = ("flash_observed" in deviations) or ("sink_mark_depth" in deviations) or ("part_weight" in deviations)
            defect_indicator = 0.95 if has_part_defect else 0.65

        return ContractEvaluationResult(
            is_compliant=is_compliant,
            violations=violations,
            deviations=deviations,
            defect_risk_indicator=defect_indicator,
        )
