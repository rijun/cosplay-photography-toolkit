import click

from cli.config import load_config, save_config


@click.command()
@click.option("--dev", is_flag=True, default=False, help="Configure dev environment overrides")
def configure(dev: bool):
    """Set up CLI configuration."""
    config = load_config()

    if dev:
        dev_config = config.get("dev", {})
        click.echo("Configuring dev environment overrides (leave blank to use prod value):")
        dev_config["api_url"] = click.prompt("Dev API URL", default=dev_config.get("api_url", "http://localhost:8000"))
        dev_config["api_key"] = click.prompt("Dev API key", default=dev_config.get("api_key", ""))
        config["dev"] = dev_config
        save_config(config)
        click.echo("Dev configuration saved.")
        return

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
    config["nextcloud_webdav_url"] = click.prompt(
        "Nextcloud WebDAV URL", default=config.get("nextcloud_webdav_url", "")
    )
    config["nextcloud_username"] = click.prompt(
        "Nextcloud username", default=config.get("nextcloud_username", "")
    )
    config["nextcloud_app_password"] = click.prompt(
        "Nextcloud app password", default=config.get("nextcloud_app_password", "")
    )
    config["nextcloud_base_path"] = click.prompt(
        "Nextcloud base path", default=config.get("nextcloud_base_path", "")
    )
    save_config(config)
    click.echo("Configuration saved.")
