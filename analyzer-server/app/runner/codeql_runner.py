import hashlib
import subprocess
import json
import os
from pathlib import Path
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

DB_CACHE_DIR = Path(os.getenv("CODEQL_DB_DIR", "/tmp/codeql_dbs"))
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
    subprocess.run([
        "codeql", "database", "create", str(db_path),
        "--language", language,
        "--source-root", str(source_dir)
    ], check=True)

    return db_path

def run_codeql(source_dir: Path, language: str) -> List[Dict]:
    # Skip java for now
    # TODO: Add Java build command support for CodeQL
    if language == "java":
        return[]
    
    db_path = get_or_create_codeql_db(source_dir, language)
    sarif_output = source_dir / f"codeql_result_{language}.sarif"

    subprocess.run([
        "codeql", "database", "analyze", str(db_path),
        "--format=sarifv2.1.0",
        "--output", str(sarif_output),
        "--rerun"
    ], check=True)

    with open(sarif_output, "r") as f:
        sarif_data = json.load(f)

    findings = []
    for run in sarif_data.get("runs", []):
        for result in run.get("results", []):
            message = result.get("message", {}).get("text", "")
            location = result.get("locations", [{}])[0]
            region = location.get("physicalLocation", {}).get("region", {})
            line = region.get("startLine", 0)
            findings.append({
                "message": message,
                "line": line
            })

    return findings
