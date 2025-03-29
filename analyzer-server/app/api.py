from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pathlib import Path
import tempfile

from app.utils.unzipper import unzip_to_temp_dir

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

    return JSONResponse(content={
        "message": "Zip file extracted successfully.",
        "file_name": code_zip.filename,
        "extracted_to": str(source_dir),
        "run_semgrep": run_semgrep_flag,
        "run_codeql": run_codeql_flag
    })
