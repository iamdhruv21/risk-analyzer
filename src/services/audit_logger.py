import json
import logging
from datetime import datetime
from typing import Dict, Any
from src.models.signal import RiskAnalysisReport

class AuditLogger:
    """Layer 6: Audit Logging System"""
    
    def __init__(self):
        # Setup basic file logging as a fallback for DB
        logging.basicConfig(
            filename='audit_log.jsonl',
            level=logging.INFO,
            format='%(message)s'
        )
        self.logger = logging.getLogger("audit_logger")

    async def log_decision(self, report: RiskAnalysisReport):
        """
        Persists the final decision and all context for reproducibility.
        Logs to structured JSONL file for audit trail.
        """
        try:
            log_entry = report.model_dump()
            log_entry["timestamp"] = datetime.utcnow().isoformat()

            self.logger.info(json.dumps(log_entry))
            print(f"\n[AuditLog] Decision '{report.decision}' persisted to audit trail at {log_entry['timestamp']}")

        except Exception as e:
            print(f"[AuditLog] Error persisting decision: {e}")
            raise
