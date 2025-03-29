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
        return output.get("results", [])
    except subprocess.CalledProcessError as e:
        print("Semgrep failed:", e.stderr)
        return []
