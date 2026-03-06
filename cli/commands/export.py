from pathlib import Path

import click

from cli.api_client import get_client


@click.group()
def export():
    """Export data from galleries."""
    pass


@export.command("selections")
@click.argument("slug")
@click.option("--output", "-o", type=click.Path(path_type=Path), default=".", help="Output directory")
def export_selections(slug: str, output: Path):
    """Export selected photo filenames to a text file."""
    with get_client() as client:
        filenames = client.get_selections(slug)
    output_path = output / f"{slug}-selections.txt"
    output_path.write_text("\n".join(filenames) + "\n" if filenames else "")
    click.echo(f"Selections exported to {output_path}")
