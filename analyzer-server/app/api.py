from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pathlib import Path
import tempfile

from app.utils.unzipper import unzip_to_temp_dir, cleanup_temp_dir
from app.runner.semgrep_runner import run_semgrep
from app.runner.codeql_runner import run_codeql
from app.runner.gpt_assistant import get_gpt_recommendation

router = APIRouter()

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
            semgrep_results = run_semgrep(source_dir)
            for item in semgrep_results:
                item["tool"] = "semgrep"
                message = item.get("message", "")
                file_path = source_dir / item.get("filePath", "")
                line = item.get("line", 0)

                try:
                    full_code = file_path.read_text()
                except Exception:
                    full_code = ""

                item["recommendation"] = get_gpt_recommendation(message, full_code, line, openai_api_key)
            results["semgrep"] = semgrep_results

        if do_run_codeql:
            codeql_results = run_codeql(source_dir, "javascript")
            for item in codeql_results:
                item["tool"] = "codeql"
                message = item.get("message", "")
                file_path = source_dir / item.get("filePath", "")
                line = item.get("line", 0)

                try:
                    full_code = file_path.read_text()
                except Exception:
                    full_code = ""

                item["recommendation"] = get_gpt_recommendation(message, full_code, line, openai_api_key)
            results["codeql"] = codeql_results

        return JSONResponse(content={
            "message": "Analysis complete.",
            "results": results
        })

    finally:
        if temp_zip_path.exists():
            temp_zip_path.unlink()
        cleanup_temp_dir(source_dir)

@router.post("/fix")
async def fix_selected_code(
    message: str = Form(...),
    code: str = Form(...),
    openai_api_key: str = Form("")
):
    print("[analyzer-server] fix_selected_code called")
    result = get_gpt_fix(message, code, openai_api_key)
    return JSONResponse(content={"fixedCode": result.get("fixedCode", "")})