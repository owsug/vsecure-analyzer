import subprocess
import json
from pathlib import Path
from typing import List, Dict

def run_semgrep(source_dir: Path) -> List[Dict]:
    try:
        result = subprocess.run(
            ["semgrep", "--config", "auto", "--json", str(source_dir)],
            capture_output=True,
            text=True,
            check=True
        )
        data = json.loads(result.stdout)
        findings = []
        for item in data.get("results", []):
            findings.append({
                "message": item.get("extra", {}).get("message", ""),
                "filePath": Path(item.get("path", "")).name,
                "line": item.get("start", {}).get("line", 0),
                "column": {
                    "start": item.get("start", {}).get("col", 0),
                    "end": item.get("end", {}).get("col", 0)
                }
            })
        return findings
    except subprocess.CalledProcessError as e:
        print("[semgrep_runner] Semgrep error:", e.stderr)
        return []