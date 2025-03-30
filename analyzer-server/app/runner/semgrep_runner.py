import subprocess
import json
from pathlib import Path
from typing import List, Dict

def run_semgrep(target_dir: Path) -> List[Dict]:
    try:
        result = subprocess.run(
            # TODO: Add proper Java analysis support
            # Currently using --config auto which may not detect Java rules.
            # Consider explicitly loading https://semgrep.dev/p/java when needed.
            ["semgrep", "--config", "auto", "--json", str(target_dir)],
            capture_output=True,
            text=True,
            check=True
        )
        output = json.loads(result.stdout)

        findings = []
        for result in output.get("results", []):
            message = result.get("extra", {}).get("message", "")
            start_location = result.get("start", {})
            start_line = start_location.get("line", 0)
            start_column = start_location.get("col", 0)
            end_location = result.get("end", {})
            end_column = end_location.get("col", 0)
            full_path = result.get("path", 0)
            file_path = Path(full_path).name

            findings.append({
                "message": message,
                "line": start_line,
                "column": {
                    "start": start_column,
                    "end": end_column
                },
                "filePath": file_path
            })

        return findings

    except subprocess.CalledProcessError as e:
        print("[analyzer-server] Semgrep failed:", e.stderr)
        return []
