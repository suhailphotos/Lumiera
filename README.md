# Lumiera

> **Swiss-army CLI toolbox for automating data, code, and developer tasks.**
>
> **Lumiera** (successor to pythonKitchen) centralizes all your one-off Python scripts into a clean, discoverable, and extensible CLI – so you never lose a handy script again.

---

## Features

* **Organized namespaces:** All scripts grouped by purpose (backup, devutils, scrapers, etc.)
* **Unified CLI:** Instantly invoke *any* tool using `lumiera <category> <command>`
* **Easy to extend:** Drop new scripts or sub-packages in – Lumiera auto-discovers them!
* **Test scripts included:** Ship or keep local ad-hoc REST probes and test helpers.
* **Click-powered CLI:** Rich help, flags, and auto-completion for every command
* **PyPI-ready structure:** All scripts and sub-packages organized for clean builds, wheel, and `pipx` usage

---

## Installation

```bash
# (Recommended: install in a virtualenv or use pipx)
cd /path/to/Lumiera
poetry install

# or after publishing
pip install lumiera
```

---

## Usage

Get help and a list of all available commands:

```bash
lumiera --help
lumiera devutils --help
lumiera backup run --help
```

**Examples:**

* Run a custom directory tree visualizer:

  ```bash
  lumiera devutils tree ~/projects -n 5 -L 3
  ```
* Create a backup job (configured in your Dropbox backup\_config.json):

  ```bash
  lumiera backup --job my_important_files
  ```
* Pretty-print JSON:

  ```bash
  lumiera devutils pretty-json myfile.json -o out.json
  ```

---

## Project Layout

```
lumiera/                    # src/lumiera
├── __init__.py             # version & high‑level helpers
├── cli.py                  # root Click group, auto‑registers sub‑CLIs
│
├── backup/                 # backup & restore utilities
│   ├── __init__.py
│   └── jobs.py
│
├── devutils/               # small one‑off developer utilities
│   ├── __init__.py
│   ├── custom_tree.py
│   ├── seq_renamer.py
│   ├── resize_pdf.py
│   └── pretty_json.py
│
├── export/                 # project/code exporters
│   ├── __init__.py
│   └── project.py
│
├── pypi/                   # helpers around PyPI publishing / locking
│   ├── __init__.py
│   ├── availability.py
│   └── yank.py
│
├── data/                   # payload munging + JSON helpers
│   ├── __init__.py
│   ├── create_subset.py
│   ├── split_payload.py
│   ├── extract_course.py
│   ├── generate_desc.py
│   └── ml_vfx.json         # data asset
│
├── scrapers/               # web‑scraping / Selenium driven tools
│   ├── __init__.py
│   ├── rebelway_dl.py
│   ├── report_sources.py
│   ├── extract_lessons.py
│   └── udemy_curriculum.py
│
├── tests/                  # ad‑hoc REST‑API probes (not shipped)
│   ├── __init__.py
│   ├── test_imgseg.py
│   └── test_predict.py
└── utils.py                # misc helpers shared across sub‑packages
```

*Every folder has an `__init__.py` and can expose CLI sub-commands via a `cli` group.*

---

## Command Structure

* **All CLI entry-points are grouped:**
  Run any script as a subcommand:
  `lumiera <namespace> <command>`

* **Examples:**

  * `lumiera backup run --job ...`
  * `lumiera devutils tree [options]`
  * `lumiera pypi availability --names foo,bar`
  * `lumiera scrapers rebelway-dl ...`

* **Auto-discovery:** New scripts with `cli` groups are automatically added to the main CLI.

---

## Migration from pythonKitchen

1. **All scripts are now discoverable** under a logical sub-package.
2. **Imports and hardcoded paths** are updated: use `lumiera.*` imports and paths referencing `Lumiera` instead of `pythonKitchen`.
3. **CLI entry-point:** Use `lumiera` instead of `pythonkitchen`.
4. **Legacy:** You may release a final pythonKitchen version that prints a migration message and points to Lumiera.

---

## Contributing

* **Extend:** Drop any new script into an appropriate sub-package and expose a `@cli.command()` or group in its `cli.py`.
* **Test:** Add test helpers or probes in `/tests` – these are never shipped to PyPI.
* **Docs:** Keep this README and docstrings up-to-date for new commands.

---

## License

MIT. © Suhail 2024+
