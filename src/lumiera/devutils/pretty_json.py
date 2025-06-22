#!/usr/bin/env python3
import json
import argparse
import sys
from pathlib import Path

def pretty_print_json(input_path: Path, output_path: Path | None = None, indent: int = 2):
    """
    Load a JSON file from input_path, then write it back with standard indentation.
    If output_path is None, writes to stdout; otherwise, overwrites (or creates) output_path.
    """
    # Read the original JSON
    with input_path.open('r', encoding='utf-8') as f:
        data = json.load(f)
    # Serialize with indentation, preserving Unicode characters
    pretty = json.dumps(data, indent=indent, ensure_ascii=False)
    if output_path:
        with output_path.open('w', encoding='utf-8') as f_out:
            f_out.write(pretty)
            f_out.write("\n")
    else:
        print(pretty)

def main():
    parser = argparse.ArgumentParser(
        description="Load a JSON file and rewrite it with pretty (standard) indentation."
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Path to the original JSON file."
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=None,
        help="If provided, write the pretty JSON here; otherwise, print to stdout."
    )
    parser.add_argument(
        "-i", "--indent",
        type=int,
        default=2,
        help="Number of spaces to use for indentation (default: 2)."
    )
    args = parser.parse_args()

    if not args.input.is_file():
        print(f"Error: '{args.input}' does not exist or is not a file.", file=sys.stderr)
        sys.exit(1)

    pretty_print_json(args.input, args.output, args.indent)

if __name__ == "__main__":
    main()
