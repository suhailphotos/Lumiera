# pythonkitchen/project_export.py
import os
from pathlib import Path

SKIP_EXTS = {'.env'}
SKIP_NAMES = {'.env'}
SKIP_TREE_FILES = {'__pycache__', 'dist', '.git'}

# files to hide in the *content* dump (dump_code_files), but still show in the tree
SKIP_CONTENT_NAMES = {'.env', 'README.md'}

INCLUDE_EXTS = {'.py', '.json', '.yml', '.yaml', '.toml', '.txt', '.md'}
INCLUDE_NAMES = {'Dockerfile', 'requirements.txt', 'pyproject.toml', '.env'}

def build_tree(root, overrides=None):
    overrides = overrides or set()
    lines = []
    dir_count = 0
    file_count = 0

    def walk(dir_path, prefix=""):
        nonlocal dir_count, file_count
        entries = sorted(os.listdir(dir_path))
        # skip names only if they're *not* in overrides
        # skip tree‐names unless overridden
        entries = [
            e for e in entries
            if not (e in SKIP_NAMES and (overrides is None or e not in overrides))
        ]
        for idx, entry in enumerate(entries):
            path = os.path.join(dir_path, entry)
            is_last = (idx == len(entries) - 1)
            connector = "└── " if is_last else "├── "
            sub_prefix = "    " if is_last else "│   "

            # if directory
            if os.path.isdir(path):
                # always show overridden dirs
                if entry in SKIP_TREE_FILES and entry not in overrides:
                    lines.append(f"{prefix}{connector}{entry}")
                    lines.append(f"{prefix}{sub_prefix}// * files hidden for brevity")
                    dir_count += 1
                    continue
                lines.append(f"{prefix}{connector}{entry}")
                dir_count += 1
                walk(path, prefix + sub_prefix)

            # if file
            else:
                ext = Path(entry).suffix.lower()
                # skip by name or extension unless overridden
                if (entry in SKIP_NAMES and entry not in overrides) or (ext in SKIP_EXTS and ext not in overrides):
                    continue
                lines.append(f"{prefix}{connector}{entry}")
                file_count += 1

    lines.append(str(root))
    walk(str(root))
    lines.append(f"\n{dir_count} directories, {file_count} files\n")
    return "\n".join(lines)

def dump_code_files(root, include_env=False, overrides=None):
    overrides = overrides or set()
    blocks = []

    for dirpath, dirnames, filenames in os.walk(root):
        # first, drop any files we want to hide in the *content* unless overridden
        filenames = [
            f for f in filenames
            if not (f in SKIP_CONTENT_NAMES and f not in overrides)
        ]
        # then, remove skipped folders from traversal
        dirnames[:] = [
            d for d in dirnames
            if not (d in SKIP_TREE_FILES and d not in overrides)
               and not (d.startswith('.') and d not in overrides)
        ]
        for fname in filenames:
            ext = Path(fname).suffix.lower()

            # always include overrides
            if fname in overrides or ext in overrides:
                include_this = True
            else:
                include_this = (
                    ext in INCLUDE_EXTS or
                    fname in INCLUDE_NAMES
                )

            # env special case
            if fname == ".env" and not include_env and ".env" not in overrides:
                include_this = False

            if not include_this:
                continue

            # skip hidden files unless overridden
            if fname.startswith('.') and fname not in overrides:
                continue

            # skip under .git/dist unless overridden
            rel_dir = Path(dirpath).relative_to(root)
            if any(part in SKIP_TREE_FILES for part in rel_dir.parts) and not any(part in overrides for part in rel_dir.parts):
                continue

            rel_path = Path(dirpath, fname).relative_to(root)
            try:
                with open(os.path.join(dirpath, fname), encoding="utf-8", errors="replace") as f:
                    content = f.read().strip()
            except Exception:
                continue
            if fname == '__init__.py' and not content:
                continue

            # language mapping
            lang_map = {
                ".py": "python", ".json": "json", ".yml": "yaml", ".yaml": "yaml",
                ".toml": "toml", ".md": "markdown", ".env": "", ".txt": "",
                "Dockerfile": "docker"
            }
            lang = lang_map.get(ext, "")
            if fname == "Dockerfile":
                lang = "docker"

            blocks.append(f"path: {rel_path}")
            if lang:
                blocks.append(f"```{lang}\n{content}\n```")
            else:
                blocks.append(f"```\n{content}\n```")

    return "\n\n".join(blocks)

def export_project(root_path: str, output_path: str = None, include_env: bool = False, include_list=None):
    root = Path(root_path).resolve()
    include_list = include_list or set()

    # wrap the tree in backticks
    tree_md = "```\n" + build_tree(root, overrides=include_list) + "\n```"

    code_md = dump_code_files(root, include_env=include_env, overrides=include_list)

    full = "\n\n".join([tree_md, code_md])

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(full)
        print(f"Exported to {output_path}")
    else:
        print(full)
