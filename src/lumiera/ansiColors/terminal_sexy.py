import json
import sys

def json_to_ghostty(json_file):
    with open(json_file, "r") as f:
        data = json.load(f)

    # Colors 0–15
    for idx, color in enumerate(data["color"]):
        print(f"palette = {idx}={color}")

    # Foreground / background
    print(f"background = {data['background']}")
    print(f"foreground = {data['foreground']}")

    # Optional: some defaults
    # You can adjust these if you like
    print(f"cursor-color = {data['foreground']}")
    print(f"cursor-text = {data['background']}")
    print(f"selection-background = {data['color'][8]}")  # often bright-black
    print(f"selection-foreground = {data['foreground']}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python convert.py <theme.json>")
        sys.exit(1)

    json_to_ghostty(sys.argv[1])
