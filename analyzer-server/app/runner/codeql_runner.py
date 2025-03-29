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

QUERY_PACKS = {
    "javascript": "codeql/javascript-queries",
    "java": "codeql/java-queries",  # included for future support
}

def compute_file_content_hash(directory: Path) -> str:
    hash_obj = hashlib.sha256()

    for file in sorted(directory.rglob("*")):
        if file.is_file():
            rel_path = file.relative_to(directory)
            hash_obj.update(str(rel_path).encode())  # ensure consistent ordering
            with open(file, 'rb') as f:
                while chunk := f.read(8192):
                    hash_obj.update(chunk)

    return hash_obj.hexdigest()

def get_or_create_codeql_db(source_dir: Path, language: str) -> Path:
    key = compute_file_content_hash(source_dir)
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
        print(f"CodeQL DB creation failed: {e}")
        return None

    return db_path

def run_codeql(source_dir: Path, language: str) -> List[Dict]:
    if language == "java":
        print("Skipping Java (TODO: build support needed)")
        return []

    query_pack = QUERY_PACKS.get(language)
    if not query_pack:
        print(f"No query pack found for language: {language}")
        return []

    db_path = get_or_create_codeql_db(source_dir, language)
    if not db_path:
        return []

    sarif_output = source_dir / f"codeql_result_{language}.sarif"

    try:
        subprocess.run([
            "codeql", "database", "analyze", str(db_path),
            query_pack,
            "--format=sarifv2.1.0",
            "--output", str(sarif_output),
            "--rerun"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"CodeQL analysis failed: {e}")
        return []

    findings = []
    try:
        with open(sarif_output, "r") as f:
            sarif_data = json.load(f)

        for run in sarif_data.get("runs", []):
            for result in run.get("results", []):
                message = result.get("message", {}).get("text", "")
                location = result.get("locations", [{}])[0]
                physical = location.get("physicalLocation", {})
                region = physical.get("region", {})
                artifact = physical.get("artifactLocation", {})

                start_line = region.get("startLine", 0)
                file_path = artifact.get("uri", "")

                findings.append({
                    "message": message,
                    "line": start_line,
                    "filePath": file_path
                })

    except Exception as e:
        print(f"Failed to parse SARIF result: {e}")

    return findings
