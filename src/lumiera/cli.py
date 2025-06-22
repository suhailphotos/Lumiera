# src/pythonkitchen/cli.py

import os
import sys
import click
from pathlib import Path
from pythonkitchen.backup_jobs import backup_job, restore_job


def get_dropbox_dir() -> Path:
    """
    Determine the Dropbox directory:
    - Use $DROPBOX if set
    - On macOS: ~/Library/CloudStorage/Dropbox
    - On Windows: C:/Users/<User>/Dropbox
    - Otherwise: ~/Dropbox
    """
    env = os.getenv('DROPBOX')
    if env:
        return Path(env).expanduser()

    if sys.platform == 'darwin':  # macOS
        return Path.home() / 'Library' / 'CloudStorage' / 'Dropbox'
    elif sys.platform.startswith('win'):  # Windows
        return Path.home() / 'Dropbox'
    else:
        return Path.home() / 'Dropbox'


# Path to your backup configuration JSON
CONFIG_PATH = get_dropbox_dir() / 'matrix' / 'backups' / 'backup_config.json'

@click.group()
def main():
    """
    PythonKitchen CLI: backup and restore tasks defined in config.
    """
    pass

@main.command()
@click.option('--job', 'job_name', required=True, help='Name of the job defined in config.')
def backup(job_name):
    """Create a new versioned backup for the given job."""
    backup_job(CONFIG_PATH, job_name)

@main.command()
@click.option('--job', 'job_name', required=True, help='Name of the job defined in config.')
@click.option('--version', type=int, default=None, help='Version number to restore (default: latest).')
def restore(job_name, version):
    """Restore files for a given job and version."""
    restore_job(CONFIG_PATH, job_name, version)

@main.command("export-project")
@click.option(
    "--root", "root", required=True, type=click.Path(exists=True, file_okay=False),
    help="Root folder to export (recursively)."
)
@click.option(
    "--output", "output_path", required=False, type=click.Path(file_okay=True, dir_okay=False, writable=True),
    help="Optional output file path. If not given, print to stdout."
)
@click.option(
    "--include", "include_list", default="",
    help="Comma-separated list of filenames or extensions to always include, e.g. 'README.md,.env'."
)
@click.option(
    "--include-env", is_flag=True, default=False,
    help="Include .env files in export."
)
def export_project_cli(root, output_path, include_env, include_list):
    """
    Exports the folder structure and all relevant project files for context.
    """
    from pythonkitchen.project_export import export_project
    # build a set of overrides (strip whitespace, ignore empty)
    overrides = {name.strip() for name in include_list.split(",") if name.strip()}
    export_project(
        root,
        output_path=output_path,
        include_env=include_env,
        include_list=overrides
    )

@main.command("pypi-availability")
@click.option("--names", required=True, help="Comma-separated list of candidate names.")
@click.option("--build", is_flag=True, help="Attempt to actually publish dummy package for each available name.")
def pypi_availability(names, build):
    """
    Checks PyPI for name availability, optionally attempts to publish a dummy package to 'lock' the first available name.
    """
    from pythonkitchen.pypiAvailablity import check_pypi_availability, try_publish_first_available

    # Parse names
    candidates = [n.strip() for n in names.split(",") if n.strip()]
    available, taken = check_pypi_availability(candidates)

    print("==== Results ====")
    print("Taken:", ", ".join(taken) if taken else "None")
    print("Available:", ", ".join(available) if available else "None")

    if build and available:
        print("Trying to lock the first available name...")
        locked = try_publish_first_available(available)
        if locked:
            print(f"Locked and published: {locked}")
        else:
            print("Could not publish any available name.")

if __name__ == '__main__':
    main()

