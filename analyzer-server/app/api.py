from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()

@router.get("/ping")
def ping():
    return JSONResponse(content={"message": "vsecure-analyzer server is running."})

from fastapi import UploadFile, File, Form
from pathlib import Path
import tempfile

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

    return {
        "message": "Zip file received successfully.",
        "file_name": code_zip.filename,
        "run_semgrep": run_semgrep_flag,
        "run_codeql": run_codeql_flag
    }
