# analyzer-server/app/utils/unzipper.py
import tempfile
import shutil
import zipfile
from pathlib import Path

def unzip_to_temp_dir(zip_path: Path) -> Path:
    temp_dir = Path(tempfile.mkdtemp())
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)
    return temp_dir

def cleanup_temp_dir(directory: Path):
    try:
        if directory.exists():
            shutil.rmtree(directory)
    except Exception as e:
        print(f"[unzipper] Failed to remove temp dir {directory}: {e}")
