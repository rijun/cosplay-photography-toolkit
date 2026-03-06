import click

from cli.commands.configure import configure
from cli.commands.gallery import gallery
from cli.commands.upload import upload
from cli.commands.export import export


@click.group()
def cli():
    """Photo gallery CLI for managing galleries and uploading photos."""
    pass


cli.add_command(configure)
cli.add_command(gallery)
cli.add_command(upload)
cli.add_command(export)
