import subprocess
import json
import hashlib
import os
from pathlib import Path
from typing import List, Dict

DB_CACHE_DIR = Path("/tmp/codeql_dbs")
DB_CACHE_DIR.mkdir(parents=True, exist_ok=True)

def compute_directory_hash(directory: Path) -> str:
    hash_obj = hashlib.sha256()
    for root, _, files in sorted(os.walk(directory)):
        for file in sorted(files):
            file_path = Path(root) / file
            with open(file_path, 'rb') as f:
                while chunk := f.read(8192):
                    hash_obj.update(chunk)
    return hash_obj.hexdigest()

def get_or_create_codeql_db(source_dir: Path, language: str) -> Path:
    key = compute_directory_hash(source_dir)
    db_path = DB_CACHE_DIR / f"{key}_{language}"

    if db_path.exists():
        print(f"Reusing existing CodeQL DB: {db_path}")
        return db_path

    print(f"Creating new CodeQL DB: {db_path}")
    try:
        subprocess.run([
            "codeql", "database", "create", str(db_path),
            "--language", language,
            "--source-root", str(source_dir)
        ], check=True)
    except subprocess.CalledProcessError as e:
        print("[codeql_runner] CodeQL database creation failed:", e.stderr)
        return Path()

    return db_path

def run_codeql(source_dir: Path, language: str) -> List[Dict]:
    if language == "java":
        return []

    db_path = get_or_create_codeql_db(source_dir, language)
    if not db_path.exists():
        return []

    sarif_output = source_dir / f"codeql_result_{language}.sarif"

    try:
        subprocess.run([
            "codeql", "database", "analyze", str(db_path),
            "--format=sarifv2.1.0",
            "--output", str(sarif_output),
            "--rerun",
            "--search-path", "/opt/codeql-workspace",  # 쿼리 설치 경로
            "codeql/javascript-queries"                # 패키지 이름
        ], check=True)


    except subprocess.CalledProcessError as e:
        print("[codeql_runner] CodeQL analysis failed:", e.stderr)
        return []

    try:
        with open(sarif_output, "r") as f:
            sarif_data = json.load(f)
    except Exception as e:
        print("[codeql_runner] Failed to read SARIF output:", e)
        return []

    findings = []
    for run in sarif_data.get("runs", []):
        for result in run.get("results", []):
            message = result.get("message", {}).get("text", "")
            location = result.get("locations", [{}])[0]
            physical = location.get("physicalLocation", {})
            region = physical.get("region", {})
            artifact = physical.get("artifactLocation", {})

            findings.append({
                "message": message,
                "line": region.get("startLine", 0),
                "column": {
                    "start": region.get("startColumn", 0),
                    "end": region.get("endColumn", 0)
                },
                "filePath": Path(artifact.get("uri", "")).name
            })
    return findings
