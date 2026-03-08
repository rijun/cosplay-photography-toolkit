from pathlib import Path

import click

from cli.api_client import get_client

FLAG_NAMES = {0: "final", 1: "rose", 2: "lavender", 3: "sage", 4: "sky", 5: "amber"}


@click.group()
def export():
    """Export data from galleries."""
    pass


@export.command("selections")
@click.argument("slug")
@click.option("--flag", "-f", type=click.IntRange(0, 5), default=0, help="Flag color to export (0=final, 1=rose, 2=lavender, 3=sage, 4=sky, 5=amber)")
@click.option("--output", "-o", type=click.Path(path_type=Path), default=".", help="Output directory")
def export_selections(slug: str, flag: int, output: Path):
    """Export flagged photo filenames to a text file."""
    with get_client() as client:
        filenames = client.get_selections(slug, flag=flag)
    suffix = FLAG_NAMES[flag]
    output_path = output / f"{slug}-{suffix}.txt"
    output_path.write_text("\n".join(filenames) + "\n" if filenames else "")
    click.echo(f"Selections ({suffix}) exported to {output_path}")