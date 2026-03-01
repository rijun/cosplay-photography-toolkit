import shutil
import subprocess
from pathlib import Path


def strip_metadata(photo_path: Path) -> None:
    exiftool = shutil.which("exiftool")
    if not exiftool:
        raise SystemExit("exiftool not found. Install it with: brew install exiftool")

    subprocess.run(
        [exiftool, "-all=", "-overwrite_original", str(photo_path)],
        check=True,
        capture_output=True,
    )
