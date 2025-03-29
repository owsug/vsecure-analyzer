import zipfile
import tempfile
from pathlib import Path

def unzip_to_temp_dir(zip_file_path: Path) -> Path:
    temp_dir = Path(tempfile.mkdtemp(prefix="vsecure_"))
    with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
        zip_ref.extractall(temp_dir)
    return temp_dir
