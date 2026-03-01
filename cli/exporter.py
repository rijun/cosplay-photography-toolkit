from pathlib import Path

from cli.api_client import get_selections


def export_selections(slug: str, output_dir: Path = Path("")) -> Path:
    filenames = get_selections(slug)
    output_path = output_dir / f"{slug}-selections.txt"
    output_path.write_text("\n".join(filenames) + "\n" if filenames else "")
    return output_path
