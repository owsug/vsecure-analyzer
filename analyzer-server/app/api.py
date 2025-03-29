from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pathlib import Path
import tempfile

from app.utils.unzipper import unzip_to_temp_dir
from app.runner.semgrep_runner import run_semgrep
from app.runner.codeql_runner import run_codeql
from app.runner.gpt_assistant import get_gpt_recommendation

def extract_code_snippet(file_path: Path, line: int, context: int = 2) -> str:
    lines = file_path.read_text().splitlines()
    start = max(0, line - context - 1)
    end = min(len(lines), line + context)
    return "\n".join(lines[start:end])


router = APIRouter()

@router.get("/ping")
def ping():
    return JSONResponse(content={"message": "vsecure-analyzer server is running."})

@router.post("/analyze")
async def analyze_code(
    code_zip: UploadFile = File(...),
    run_semgrep_flag: bool = Form(False),
    run_codeql_flag: bool = Form(False),
    openai_api_key: str = Form("")
):

    temp_zip_path = Path(tempfile.mkstemp(suffix=".zip")[1])
    with open(temp_zip_path, "wb") as f:
        f.write(await code_zip.read())

    source_dir = unzip_to_temp_dir(temp_zip_path)

    results = {}

    if run_semgrep_flag:
        semgrep_result = run_semgrep(source_dir)
        for item in semgrep_result:
            file_path = source_dir / item.get("path", "")
            line = item.get("start", {}).get("line", 0)
            code = ""
            if file_path.exists():
                code = extract_code_snippet(file_path, line)

            recommendation = get_gpt_recommendation(item["extra"]["message"], code, openai_api_key)
            item["recommendation"] = recommendation
        results["semgrep"] = semgrep_result

    if run_codeql_flag:
        codeql_result = run_codeql(source_dir, "javascript")
        for item in codeql_result:
            # TODO: add file_path if available for better context
            message = item.get("message", "")
            line = item.get("line", 0)
            recommendation = get_gpt_recommendation(message, "", openai_api_key)
            item["recommendation"] = recommendation
        results["codeql"] = codeql_result

    temp_zip_path.unlink()

    return JSONResponse(content={
        "message": "Analysis complete.",
        "results": results
    })