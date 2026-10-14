"""SQLite database manager and DDL migration layer for Process Guardian."""

import sqlite3
import json
import logging
import threading
from contextlib import contextmanager
from typing import Generator, Optional, Union
from pathlib import Path

logger = logging.getLogger(__name__)

# Complete DDL creating all 17 tables (STOR-01)
SCHEMA_SQL = """
-- 1. Machines
CREATE TABLE IF NOT EXISTS machines (
    id TEXT PRIMARY KEY,
    machine_name TEXT NOT NULL,
    model TEXT NOT NULL,
    tonnage REAL NOT NULL,
    plant_location TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'ACTIVE',
    created_at TEXT NOT NULL
);

-- 2. Molds
CREATE TABLE IF NOT EXISTS molds (
    id TEXT PRIMARY KEY,
    mold_code TEXT NOT NULL,
    cavities INTEGER NOT NULL DEFAULT 1,
    material_compatibility TEXT NOT NULL,
    clamp_tonnage_required REAL NOT NULL,
    created_at TEXT NOT NULL
);

-- 3. Parts
CREATE TABLE IF NOT EXISTS parts (
    id TEXT PRIMARY KEY,
    part_number TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    target_weight_g REAL NOT NULL,
    created_at TEXT NOT NULL
);

-- 4. Recipes
CREATE TABLE IF NOT EXISTS recipes (
    id TEXT PRIMARY KEY,
    recipe_code TEXT NOT NULL,
    part_id TEXT NOT NULL,
    mold_id TEXT NOT NULL,
    machine_id TEXT NOT NULL,
    target_temperature REAL NOT NULL,
    target_pressure REAL NOT NULL,
    target_cycle_time REAL NOT NULL,
    parameters_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    FOREIGN KEY (part_id) REFERENCES parts(id),
    FOREIGN KEY (mold_id) REFERENCES molds(id),
    FOREIGN KEY (machine_id) REFERENCES machines(id)
);

-- 5. Materials
CREATE TABLE IF NOT EXISTS materials (
    id TEXT PRIMARY KEY,
    material_code TEXT NOT NULL,
    name TEXT NOT NULL,
    polymer_type TEXT NOT NULL,
    target_moisture_pct REAL NOT NULL,
    max_moisture_pct REAL NOT NULL,
    density_g_cm3 REAL NOT NULL,
    created_at TEXT NOT NULL
);

-- 6. Cycles
CREATE TABLE IF NOT EXISTS cycles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cycle_index INTEGER NOT NULL,
    machine_id TEXT NOT NULL,
    mold_id TEXT NOT NULL,
    part_id TEXT NOT NULL,
    recipe_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    barrel_temp_z1 REAL NOT NULL,
    barrel_temp_z2 REAL NOT NULL,
    barrel_temp_z3 REAL NOT NULL,
    barrel_temp_z4 REAL NOT NULL,
    nozzle_temp REAL NOT NULL,
    mold_temp REAL NOT NULL,
    injection_pressure REAL NOT NULL,
    holding_pressure REAL NOT NULL,
    back_pressure REAL NOT NULL,
    injection_speed REAL NOT NULL,
    screw_rpm REAL NOT NULL,
    cushion_position REAL NOT NULL,
    dosing_time REAL NOT NULL,
    injection_time REAL NOT NULL,
    cooling_time REAL NOT NULL,
    cycle_time REAL NOT NULL,
    ambient_temp REAL NOT NULL,
    ambient_humidity REAL NOT NULL,
    material_moisture_pct REAL NOT NULL,
    part_weight_g REAL NOT NULL,
    defect_flag INTEGER NOT NULL DEFAULT 0,
    defect_type TEXT,
    raw_json TEXT NOT NULL DEFAULT '{}',
    FOREIGN KEY (machine_id) REFERENCES machines(id),
    FOREIGN KEY (mold_id) REFERENCES molds(id),
    FOREIGN KEY (part_id) REFERENCES parts(id),
    FOREIGN KEY (recipe_id) REFERENCES recipes(id)
);

CREATE INDEX IF NOT EXISTS idx_cycles_machine_cycle ON cycles(machine_id, cycle_index);
CREATE INDEX IF NOT EXISTS idx_cycles_timestamp ON cycles(timestamp);

-- 7. Process Fingerprints
CREATE TABLE IF NOT EXISTS process_fingerprints (
    id TEXT PRIMARY KEY,
    context_key TEXT NOT NULL,
    machine_id TEXT NOT NULL,
    mold_id TEXT NOT NULL,
    part_id TEXT NOT NULL,
    recipe_id TEXT NOT NULL,
    baseline_version TEXT NOT NULL,
    sample_count INTEGER NOT NULL,
    stats_json TEXT NOT NULL,
    envelope_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (machine_id) REFERENCES machines(id),
    FOREIGN KEY (mold_id) REFERENCES molds(id),
    FOREIGN KEY (part_id) REFERENCES parts(id),
    FOREIGN KEY (recipe_id) REFERENCES recipes(id)
);

-- 8. Quality Contracts
CREATE TABLE IF NOT EXISTS quality_contracts (
    id TEXT PRIMARY KEY,
    contract_code TEXT NOT NULL,
    part_id TEXT NOT NULL,
    recipe_id TEXT NOT NULL,
    target_weight_g REAL NOT NULL,
    weight_tolerance_g REAL NOT NULL,
    max_sink_mark_mm REAL NOT NULL,
    allow_flash INTEGER NOT NULL DEFAULT 0,
    target_cycle_time_s REAL NOT NULL,
    cycle_time_tolerance_s REAL NOT NULL,
    specs_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    FOREIGN KEY (part_id) REFERENCES parts(id),
    FOREIGN KEY (recipe_id) REFERENCES recipes(id)
);

-- 9. Drift Events
CREATE TABLE IF NOT EXISTS drift_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT UNIQUE NOT NULL,
    cycle_index INTEGER NOT NULL,
    machine_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    drift INTEGER NOT NULL,
    severity REAL NOT NULL,
    lead_cycles INTEGER NOT NULL,
    signals_json TEXT NOT NULL DEFAULT '[]',
    details_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    FOREIGN KEY (machine_id) REFERENCES machines(id)
);

CREATE INDEX IF NOT EXISTS idx_drift_events_cycle ON drift_events(cycle_index);

-- 10. Quality Predictions
CREATE TABLE IF NOT EXISTS quality_predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT NOT NULL,
    cycle_index INTEGER NOT NULL,
    machine_id TEXT NOT NULL,
    risk_probability REAL NOT NULL,
    confidence REAL NOT NULL,
    risk_state TEXT NOT NULL,
    operator_mode TEXT NOT NULL,
    root_cause_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    FOREIGN KEY (machine_id) REFERENCES machines(id)
);

CREATE INDEX IF NOT EXISTS idx_predictions_cycle ON quality_predictions(cycle_index);

-- 11. Intervention Candidates
CREATE TABLE IF NOT EXISTS intervention_candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recommendation_id TEXT NOT NULL,
    action_id TEXT NOT NULL,
    name TEXT NOT NULL,
    target_signal TEXT,
    delta_value REAL NOT NULL DEFAULT 0.0,
    unit TEXT NOT NULL DEFAULT '',
    cost REAL NOT NULL DEFAULT 0.0,
    disruption REAL NOT NULL DEFAULT 0.0,
    estimated_risk REAL NOT NULL DEFAULT 0.0,
    boundary_checked INTEGER NOT NULL DEFAULT 1,
    is_selected INTEGER NOT NULL DEFAULT 0,
    metadata_json TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_candidates_rec ON intervention_candidates(recommendation_id);

-- 12. Intervention Recommendations
CREATE TABLE IF NOT EXISTS intervention_recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recommendation_id TEXT UNIQUE NOT NULL,
    event_id TEXT NOT NULL,
    cycle_index INTEGER NOT NULL,
    machine_id TEXT NOT NULL,
    action_id TEXT NOT NULL,
    action_text TEXT NOT NULL,
    why_text TEXT NOT NULL,
    evidence_json TEXT NOT NULL DEFAULT '{}',
    expected_effect TEXT NOT NULL,
    confidence REAL NOT NULL,
    operating_limit TEXT NOT NULL,
    recovery_check TEXT NOT NULL,
    is_abstain INTEGER NOT NULL DEFAULT 0,
    abstain_reason TEXT,
    operator_mode TEXT NOT NULL DEFAULT 'DIRECT_RECOMMENDATION',
    created_at TEXT NOT NULL,
    FOREIGN KEY (machine_id) REFERENCES machines(id)
);

CREATE INDEX IF NOT EXISTS idx_recommendations_cycle ON intervention_recommendations(cycle_index);

-- 13. Intervention Applications
CREATE TABLE IF NOT EXISTS intervention_applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cycle_index INTEGER NOT NULL,
    machine_id TEXT NOT NULL,
    action_id TEXT NOT NULL,
    applied_by TEXT NOT NULL DEFAULT 'DEMO_OPERATOR',
    timestamp TEXT NOT NULL,
    pre_intervention_risk REAL NOT NULL,
    target_delta REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'APPLIED',
    details_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    FOREIGN KEY (machine_id) REFERENCES machines(id)
);

-- 14. Recovery Events
CREATE TABLE IF NOT EXISTS recovery_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cycle_index INTEGER NOT NULL,
    machine_id TEXT NOT NULL,
    intervention_id TEXT,
    recovery_status TEXT NOT NULL,
    release_decision TEXT NOT NULL,
    risk_before REAL NOT NULL,
    risk_after REAL NOT NULL,
    stability_before REAL NOT NULL,
    stability_after REAL NOT NULL,
    consecutive_stable_cycles INTEGER NOT NULL DEFAULT 0,
    summary_message TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (machine_id) REFERENCES machines(id)
);

-- 15. Containment Windows
CREATE TABLE IF NOT EXISTS containment_windows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    machine_id TEXT NOT NULL,
    last_known_good_cycle INTEGER,
    suspect_start_cycle INTEGER,
    suspect_end_cycle INTEGER,
    suspect_cycle_count INTEGER NOT NULL DEFAULT 0,
    intervention_cycle INTEGER,
    recovery_cycle INTEGER,
    release_cycle INTEGER,
    quarantine_cycles_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    FOREIGN KEY (machine_id) REFERENCES machines(id)
);

-- 16. Checkpoints
CREATE TABLE IF NOT EXISTS checkpoints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    checkpoint_name TEXT NOT NULL,
    cycle_index INTEGER NOT NULL,
    machine_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    state TEXT NOT NULL,
    data_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    FOREIGN KEY (machine_id) REFERENCES machines(id)
);

-- 17. Audit Log
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT NOT NULL,
    cycle_index INTEGER NOT NULL,
    machine_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    event_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    description TEXT NOT NULL,
    details_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    FOREIGN KEY (machine_id) REFERENCES machines(id)
);

CREATE INDEX IF NOT EXISTS idx_audit_log_cycle ON audit_log(cycle_index);
CREATE INDEX IF NOT EXISTS idx_audit_log_type ON audit_log(event_type);
"""


class DatabaseManager:
    """Manages SQLite database connections, schema creation, and transaction lifecycles."""

    def __init__(self, db_path: Union[str, Path] = ":memory:"):
        self.db_path = str(db_path)
        self._is_memory = (self.db_path == ":memory:")
        self._persistent_conn: Optional[sqlite3.Connection] = None
        self._lock = threading.RLock()
        
        # If in-memory, retain a persistent connection so tables aren't lost between closes
        if self._is_memory:
            self._persistent_conn = sqlite3.connect(
                ":memory:",
                check_same_thread=False,
                detect_types=sqlite3.PARSE_DECLTYPES,
            )
            self._persistent_conn.row_factory = sqlite3.Row
            self._persistent_conn.execute("PRAGMA foreign_keys = ON;")
            self._initialize_schema(self._persistent_conn)
        else:
            # Ensure parent directories exist
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            with self.get_connection() as conn:
                self._initialize_schema(conn)

    def _initialize_schema(self, conn: sqlite3.Connection) -> None:
        """Execute DDL script to create all 17 tables."""
        conn.executescript(SCHEMA_SQL)
        conn.commit()
        logger.debug(f"Process Guardian schema initialized on {self.db_path}")

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Provide a contextual database connection."""
        if self._is_memory and self._persistent_conn:
            with self._lock:
                yield self._persistent_conn
        else:
            conn = sqlite3.connect(
                self.db_path,
                timeout=10.0,
                check_same_thread=False,
                detect_types=sqlite3.PARSE_DECLTYPES,
            )
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.execute("PRAGMA busy_timeout = 5000;")
            try:
                yield conn
            finally:
                conn.close()

    @contextmanager
    def transaction(self) -> Generator[sqlite3.Connection, None, None]:
        """Provide a transactional boundary with automatic commit and rollback."""
        with self.get_connection() as conn:
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise

    def reset_database(self) -> None:
        """Drop and recreate all 17 tables for deterministic testing or demo replay."""
        with self.get_connection() as conn:
            # Disable foreign keys temporarily during drop
            conn.execute("PRAGMA foreign_keys = OFF;")
            tables = [
                "machines", "molds", "parts", "recipes", "materials",
                "cycles", "process_fingerprints", "quality_contracts",
                "drift_events", "quality_predictions", "intervention_candidates",
                "intervention_recommendations", "intervention_applications",
                "recovery_events", "containment_windows", "checkpoints", "audit_log"
            ]
            for tbl in tables:
                conn.execute(f"DROP TABLE IF EXISTS {tbl};")
            conn.execute("PRAGMA foreign_keys = ON;")
            self._initialize_schema(conn)

    def get_table_names(self) -> list[str]:
        """Retrieve list of existing table names."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            return [row["name"] for row in cursor.fetchall()]
