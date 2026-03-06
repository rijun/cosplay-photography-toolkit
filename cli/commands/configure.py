import click

from cli.config import load_config, save_config


@click.command()
def configure():
    """Set up CLI configuration."""
    config = load_config()
    config["api_url"] = click.prompt("App API URL", default=config.get("api_url", ""))
    config["api_key"] = click.prompt("API key", default=config.get("api_key", ""))
    config["object_storage_endpoint_url"] = click.prompt(
        "Object storage endpoint URL", default=config.get("object_storage_endpoint_url", "")
    )
    config["object_storage_access_key_id"] = click.prompt(
        "Object storage access key ID", default=config.get("object_storage_access_key_id", "")
    )
    config["object_storage_secret_access_key"] = click.prompt(
        "Object storage secret access key", default=config.get("object_storage_secret_access_key", "")
    )
    config["object_storage_bucket_name"] = click.prompt(
        "Object storage bucket name", default=config.get("object_storage_bucket_name", "")
    )
    save_config(config)
    click.echo("Configuration saved.")
