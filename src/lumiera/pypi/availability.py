import os
import requests
import subprocess
import tempfile
import shutil

PYPI_URL = "https://pypi.org/pypi/{}/json"

def check_pypi_availability(names):
    """Returns two lists: available, taken"""
    available, taken = [], []
    for name in names:
        resp = requests.get(PYPI_URL.format(name.strip()))
        if resp.status_code == 404:
            available.append(name)
        else:
            taken.append(name)
    return available, taken

def try_publish_dummy(name):
    """Attempts to publish a dummy package with the given name."""
    temp_dir = tempfile.mkdtemp()
    pkg_dir = os.path.join(temp_dir, name)
    os.mkdir(pkg_dir)
    with open(os.path.join(pkg_dir, "__init__.py"), "w") as f:
        f.write(f"# Dummy package for {name}\n")
    # setup.cfg for setuptools
    setup_cfg = f"""
[metadata]
name = {name}
version = 0.0.1
author = AutoPublisher
description = Dummy lock package for {name}

[options]
packages = find:
    """
    with open(os.path.join(temp_dir, "setup.cfg"), "w") as f:
        f.write(setup_cfg)
    with open(os.path.join(temp_dir, "pyproject.toml"), "w") as f:
        f.write("[build-system]\nrequires = [\"setuptools>=42\"]\nbuild-backend = \"setuptools.build_meta\"\n")
    prev_cwd = os.getcwd()
    os.chdir(temp_dir)
    try:
        subprocess.run(["python3", "-m", "build"], check=True)
        # Upload using twine (requires .pypirc config or env vars for PyPI credentials)
        res = subprocess.run(
            ["twine", "upload", "--non-interactive", "--skip-existing", "dist/*"],
            capture_output=True, text=True)
        # print(res.stdout)
        return "View at:" in res.stdout
    except Exception as e:
        print("Error publishing:", e)
        return False
    finally:
        os.chdir(prev_cwd)
        shutil.rmtree(temp_dir)

def try_publish_first_available(names):
    """Tries to publish each available name, stops at first success."""
    for name in names:
        print(f"Attempting to publish dummy package: {name}")
        if try_publish_dummy(name):
            print(f"Package: {name} locked and published.")
            return name
        else:
            print(f"Failed to publish: {name}")
    print("Could not lock any of the names.")
    return None
