import os
import argparse

def tree(path, prefix="", max_files=2, _is_root=True, show_hidden=False, max_depth=None, current_depth=1):
    if _is_root:
        print(path)

    try:
        entries = os.listdir(path)
    except PermissionError:
        print(prefix + "[Permission Denied]")
        return

    if not show_hidden:
        entries = [e for e in entries if not e.startswith('.')]
    entries = sorted(entries, key=lambda x: (not os.path.isdir(os.path.join(path, x)), x.lower()))

    folders = [e for e in entries if os.path.isdir(os.path.join(path, e))]
    files = [e for e in entries if not os.path.isdir(os.path.join(path, e))]

    # Print all folders (always)
    for idx, folder in enumerate(folders):
        is_last = (idx == len(folders) - 1) and (len(files[:max_files]) == 0)
        connector = "└── " if is_last else "├── "
        print(prefix + connector + folder)
        extension = "    " if is_last else "│   "
        if max_depth is None or current_depth < max_depth:
            tree(
                os.path.join(path, folder),
                prefix + extension,
                max_files=max_files,
                _is_root=False,
                show_hidden=show_hidden,
                max_depth=max_depth,
                current_depth=current_depth + 1
            )

    # Print first N files
    for idx, file in enumerate(files[:max_files]):
        is_last = (idx == len(files[:max_files]) - 1)
        connector = "└── " if is_last else "├── "
        print(prefix + connector + file)

    extra = len(files) - max_files
    if extra > 0:
        print(prefix + f"┊ ... ({extra} more files)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Custom tree utility with depth and file count limit per directory."
    )
    parser.add_argument('path', nargs='?', default='.', help='Root directory to list')
    parser.add_argument('-a', '--all', action='store_true', help='All files are listed')
    parser.add_argument('-L', '--max-depth', type=int, help='Max display depth of the directory tree')
    parser.add_argument('-n', '--num-files', type=int, default=2, help='Max files per directory to display (default: 2)')
    args = parser.parse_args()

    tree(
        args.path,
        max_files=args.num_files,
        show_hidden=args.all,
        max_depth=args.max_depth
    )
