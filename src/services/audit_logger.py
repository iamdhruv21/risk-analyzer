import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from src.models.signal import RiskAnalysisReport

class AuditLogger:
    """Layer 6: Audit Logging System"""

    def __init__(self, source_filename: str = None):
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)
        self.source_filename = source_filename

    async def log_decision(self, report: RiskAnalysisReport):
        """
        Persists the final decision and all context for reproducibility.
        Logs to individual JSON file in output folder.
        """
        try:
            log_entry = report.model_dump()
            timestamp = datetime.utcnow()
            log_entry["timestamp"] = timestamp.isoformat()

            # Generate filename: original_filename_timestamp.json
            if self.source_filename:
                base_name = Path(self.source_filename).stem
                filename = f"{base_name}_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
            else:
                filename = f"analysis_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"

            output_path = self.output_dir / filename

            with open(output_path, 'w') as f:
                json.dump(log_entry, f, indent=2, default=str)

            print(f"\n[AuditLog] Decision '{report.decision}' saved to {output_path}")

        except Exception as e:
            print(f"[AuditLog] Error persisting decision: {e}")
            raise
