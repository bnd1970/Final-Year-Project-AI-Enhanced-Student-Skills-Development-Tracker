import json
from datetime import datetime
from pathlib import Path
from config import config

class ProgressManager:
    def __init__(self):
        self.data_dir = config.DATA_DIR
        self._init_storage()

    def _init_storage(self):
        try:
            self.data_dir.mkdir(exist_ok=True)
        except PermissionError:
            raise RuntimeError(f"Permission denied: {self.data_dir}")

    def save_analysis(self, source_file: str, content: str, analysis: dict):
        if "scores" not in analysis:
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.data_dir / f"analysis_{timestamp}.json"

        record = {
            "source_file": source_file,
            "timestamp": datetime.now().isoformat(),
            "content": content,
            "feedback": analysis.get("feedback", ""),
            "scores": analysis["scores"],
            "schema_version": config.SCHEMA_VERSION
        }

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(record, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Save failed: {str(e)}")