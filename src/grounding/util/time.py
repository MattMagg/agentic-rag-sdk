"""
Time utilities for timestamps and run IDs.

Provides ISO format timestamps and run ID generation for manifests.
"""

from __future__ import annotations

from datetime import datetime, timezone


def now_iso() -> str:
    """
    Get current UTC time in ISO 8601 format.
    
    Returns:
        ISO formatted timestamp, e.g. "2024-01-15T10:30:45.123456Z"
    """
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def now_run_id() -> str:
    """
    Get current time as a run ID in YYYYMMDD-HHMMSS format.
    
    Used for naming ingestion run files in manifests/ingestion_runs/.
    
    Returns:
        Run ID string, e.g. "20240115-103045"
    """
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
