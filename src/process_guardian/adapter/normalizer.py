"""Telemetry normalization for physical units, timestamps, and sequence ordering."""

from datetime import datetime, timezone, timedelta
from typing import Optional, Union


class TelemetryNormalizer:
    """Normalizes raw physical engineering units and timestamps into standardized SI units."""

    def normalize_pressure(self, value: Optional[float], unit: str = "bar") -> Optional[float]:
        """Convert pressure to bar (from psi, MPa, or bar)."""
        if value is None:
            return None
        unit_clean = unit.lower().strip()
        if unit_clean == "psi":
            return round(value / 14.50377, 2)
        elif unit_clean == "mpa":
            return round(value * 10.0, 2)
        return round(float(value), 2)

    def normalize_temperature(self, value: Optional[float], unit: str = "c") -> Optional[float]:
        """Convert temperature to Celsius (°C) (from Fahrenheit or Celsius)."""
        if value is None:
            return None
        unit_clean = unit.lower().strip()
        if unit_clean == "f":
            return round((value - 32.0) * 5.0 / 9.0, 2)
        return round(float(value), 2)

    def generate_timestamp(
        self,
        raw_timestamp: Optional[Union[datetime, str, float]],
        cycle_index: int,
        base_time: Optional[datetime] = None,
    ) -> str:
        """
        Format timestamp into strict ISO 8601 UTC string (YYYY-MM-DDTHH:MM:SS.fffZ).
        
        If raw_timestamp is None, synthesize monotonic timestamp from base_time + cycle offset.
        """
        if isinstance(raw_timestamp, datetime):
            dt = raw_timestamp if raw_timestamp.tzinfo else raw_timestamp.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        elif isinstance(raw_timestamp, str):
            try:
                # Try parsing standard formats
                dt = datetime.fromisoformat(raw_timestamp.replace("Z", "+00:00"))
                return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
            except Exception:
                pass

        # Synthesize fallback monotonic time
        anchor = base_time or datetime(2026, 9, 24, 8, 0, 0, tzinfo=timezone.utc)
        cycle_dt = anchor + timedelta(seconds=(cycle_index - 1) * 28.5)
        return cycle_dt.isoformat().replace("+00:00", "Z")


class SequenceTracker:
    """Monitors and enforces strictly monotonic cycle indices."""

    def __init__(self, start_index: int = 1):
        self.last_cycle = start_index - 1

    def track(self, proposed_cycle: Optional[int]) -> int:
        """Return guaranteed monotonic cycle index."""
        if proposed_cycle is not None and proposed_cycle > self.last_cycle:
            self.last_cycle = proposed_cycle
        else:
            self.last_cycle += 1
        return self.last_cycle
