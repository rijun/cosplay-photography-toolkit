import click

from cli.config import set_dev
from cli.commands.configure import configure
from cli.commands.gallery import gallery
from cli.commands.upload import upload
from cli.commands.export import export
from cli.commands.reregister import reregister


@click.group()
@click.option("--dev", is_flag=True, default=False, help="Use dev environment overrides")
def cli(dev: bool):
    """Photo gallery CLI for managing galleries and uploading photos."""
    if dev:
        set_dev(True)
        click.echo("Using dev environment.")


cli.add_command(configure)
cli.add_command(gallery)
cli.add_command(upload)
cli.add_command(export)
cli.add_command(reregister)
