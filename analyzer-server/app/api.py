from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pathlib import Path
import tempfile

from app.utils.unzipper import unzip_to_temp_dir
from app.runner.semgrep_runner import run_semgrep
from app.runner.codeql_runner import run_codeql
from app.runner.gpt_assistant import get_gpt_recommendation, get_gpt_fix

router = APIRouter()

def extract_code_snippet(file_path: Path, line: int, start_col: int, end_col: int, context: int = 2) -> str:
    lines = file_path.read_text().splitlines()
    target_idx = line - 1
    start = max(0, target_idx - context)
    end = min(len(lines), target_idx + context + 1)
    snippet_lines = lines[start:end]

    if start <= target_idx < end:
        marker_line = (
            " " * (start_col - 1 if start_col > 0 else 0) +
            "^" * max(1, end_col - start_col)
        )
        snippet_lines.insert(target_idx - start + 1, marker_line)

    return "\n".join(snippet_lines)

def format_issue_prompt(tool: str, message: str, filepath: str, line: int) -> str:
    return (
        f"This code was flagged by {tool} for the following issue:\n"
        f"- File: {filepath}\n"
        f"- Line: {line}\n"
        f"- Message: {message}\n\n"
        "Please explain why this might be a security vulnerability and suggest a secure fix."
    )

def annotate_findings(findings: list, source_dir: Path, api_key: str):
    for item in findings:
        message = item.get("message", "")
        line = item.get("line", 0)
        start_col = item.get("column", {}).get("start", 0)
        end_col = item.get("column", {}).get("end", 0)
        tool = item.get("tool", "a static analysis tool")

        file_path = source_dir / item.get("filePath", "")
        full_code = file_path.read_text() if file_path.exists() else ""
        full_lines = full_code.splitlines()

        start_idx = max(0, line - 2)
        end_idx = min(len(full_lines), line + 1)

        marked_code = "\n".join(full_lines[start_idx:end_idx])

        prompt = format_issue_prompt(tool, message, str(file_path), line)
        recommendation = get_gpt_recommendation(prompt, marked_code, api_key)

        fixed_code = recommendation.get("fixedCode", "")
        line_count = fixed_code.count("\n") + 1 if fixed_code else 1

        recommendation["lineCount"] = line_count
        item["recommendation"] = recommendation
    return findings

@router.get("/ping")
def ping():
    return JSONResponse(content={"message": "vsecure-analyzer server is running."})

@router.post("/analyze")
async def analyze_code(
    code_zip: UploadFile = File(...),
    run_semgrep_flag: str = Form("false"),
    run_codeql_flag: str = Form("false"),
    openai_api_key: str = Form("")
):
    do_run_semgrep = run_semgrep_flag.lower() == "true"
    do_run_codeql = run_codeql_flag.lower() == "true"

    print("[analyzer-server] run_semgrep_flag:", do_run_semgrep)
    print("[analyzer-server] run_codeql_flag:", do_run_codeql)

    temp_zip_path = Path(tempfile.mkstemp(suffix=".zip")[1])
    try:
        with open(temp_zip_path, "wb") as f:
            f.write(await code_zip.read())

        source_dir = unzip_to_temp_dir(temp_zip_path)
        results = {}

        if do_run_semgrep:
            semgrep_result = run_semgrep(source_dir)
            for item in semgrep_result:
                item["tool"] = "Semgrep"
            results["semgrep"] = annotate_findings(semgrep_result, source_dir, openai_api_key)

        if do_run_codeql:
            codeql_result = run_codeql(source_dir, "javascript") or []
            for item in codeql_result:
                item["tool"] = "CodeQL"
            results["codeql"] = annotate_findings(codeql_result, source_dir, openai_api_key)

        return JSONResponse(content={
            "message": "Analysis complete.",
            "results": results
        })

    finally:
        if temp_zip_path.exists():
            try:
                temp_zip_path.unlink()
            except Exception as e:
                print("[analyzer-server] Failed to delete temp zip:", e)

@router.post("/fix")
async def fix_selected_code(
    message: str = Form(...),
    code: str = Form(...),
    openai_api_key: str = Form("")
):
    result = get_gpt_fix(message, code, openai_api_key)
    return JSONResponse(content={"fixedCode": result.get("fixedCode", "")})
