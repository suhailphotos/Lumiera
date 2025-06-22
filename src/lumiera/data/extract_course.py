import os
import re
import json
import openai
from pathlib import Path
from typing import List, Dict

from PIL import Image
import pytesseract
from dotenv import load_dotenv

# —————————————————————————————
# HELPER: Determine package name dynamically
# —————————————————————————————
def get_package_name() -> str:
    if __package__:
        return __package__.split('.')[0]
    return Path(__file__).resolve().parent.name

PACKAGE_NAME = get_package_name()

# —————————————————————————————
# CONFIGURE ENV-FILE LOADING
# —————————————————————————————
GLOBAL_ENV_FILE = globals().get("GLOBAL_ENV_FILE", [])
_loaded = False

# 1) Check any explicitly listed .env paths
for env_path in GLOBAL_ENV_FILE:
    p = Path(env_path)
    if p.is_file():
        load_dotenv(dotenv_path=p)
        _loaded = True
        break

# 2) Fallback to ~/.<package_name>/.env
if not _loaded:
    p = Path.home() / f".{PACKAGE_NAME}" / ".env"
    if p.is_file():
        load_dotenv(dotenv_path=p)
        _loaded = True

# 3) Final fallback: default lookup (cwd & parent dirs)
if not _loaded:
    load_dotenv()

# 4) Read the API key
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise RuntimeError("OPENAI_API_KEY not found in environment or .env file")

# —————————————————————————————————————————————————————
# 1) OCR + PARSING (no OpenAI here)
# —————————————————————————————————————————————————————

def ocr_images(image_paths: List[Path]) -> str:
    texts = []
    for img_path in image_paths:
        img = Image.open(img_path)
        text = pytesseract.image_to_string(img)
        texts.append(text)
    return "\n".join(texts)

def split_course_and_weeks(raw: str) -> (str, List[Dict]):
    raw = raw.replace("\r\n", "\n")
    m = re.search(r"(?m)^WEEK\s*1\b", raw)
    if not m:
        raise ValueError("Could not find 'WEEK 1' in OCR text")
    course_desc = raw[: m.start()].strip()
    weeks_block = raw[m.start():].strip()

    parts = re.split(r"(?m)^(WEEK\s*\d+)\b", weeks_block)
    chapters = []
    for i in range(1, len(parts), 2):
        header = parts[i].strip()         # e.g. "WEEK 1"
        body   = parts[i + 1].strip()     # text under that week
        name = header.title().replace("  ", " ")
        chapters.append({
            "name": name,
            "full_description": re.sub(r"\s+", " ", body).strip(),
            "short_description": ""
        })
    # sort chapters by their numeric index (e.g., "Week 1", "Chapter 2")
    chapters.sort(key=lambda ch: int(re.search(r'\d+', ch['name']).group()))
    return course_desc, chapters

# —————————————————————————————————————————————————————
# 2) DESCRIPTION FORMATTER (uses OpenAI)
# —————————————————————————————————————————————————————

def format_description(
    name: str,
    text: str,
    is_course: bool = False,
    max_sentences: int = 1
) -> str:
    system = {
        "role": "system",
        "content": (
            "You are a documentation assistant. "
            "Produce exactly the sentence(s) specified, "
            "no extra commentary or numbering."
        )
    }

    if is_course:
        instruction = (
            f"Write up to {max_sentences} sentences that start with 'This course covers' "
            "and then list the main topics, separated by commas. "
            "Do not begin with phrases like 'The text lists' or 'This text consists'."
        )
    else:
        instruction = (
            f"Write 1 sentence that starts with '{name} covers' and then list the key topics, "
            "separated by commas. Do not begin with phrases like 'The text lists' or 'This text consists'."
        )

    user = {
        "role": "user",
        "content": f"{instruction}\n\nContent:\n{text}"
    }

    resp = openai.chat.completions.create(
        model="gpt-4o",
        messages=[system, user],
        max_completion_tokens=max_sentences * 40,
    )

    return resp.choices[0].message.content.strip()

# —————————————————————————————————————————————————————
# 3) MAIN: DRY-RUN MODE + JSON BUILD
# —————————————————————————————————————————————————————

def build_course_json(image_files: List[str], output_path: str, dry_run: bool):
    raw_text = ocr_images([Path(f) for f in image_files])
    print("\n\n===== RAW OCR TEXT =====\n")
    print(raw_text)
    print("\n\n===== END RAW OCR =====\n")

    course_full, chapters = split_course_and_weeks(raw_text)

    course_data = {
        "name": "Machine Learning in VFX",
        "full_description": re.sub(r"\s+", " ", course_full),
        "short_description": "",
        "chapters": chapters
    }

    if not dry_run:
        # course-level summary
        course_data["short_description"] = format_description(
            name="",
            text=course_data["full_description"],
            is_course=True,
            max_sentences=2
        )
        # chapter-level summaries
        for chap in course_data["chapters"]:
            chap["short_description"] = format_description(
                name=chap["name"],
                text=chap["full_description"],
                is_course=False,
                max_sentences=1
            )
   

    print("\n\n===== GENERATED JSON =====\n")
    print(json.dumps(course_data, indent=2, ensure_ascii=False))
    print("\n\n===== END JSON =====\n")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(course_data, f, indent=2, ensure_ascii=False)

# —————————————————————————————————————————————————————
# 4) ENTRYPOINT
# —————————————————————————————————————————————————————

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(
        description="OCR → JSON skeleton (dry-run skips OpenAI)"
    )
    p.add_argument("images", nargs="+", help="Paths to your screenshot images")
    p.add_argument(
        "-o", "--output", default="course_data.json",
        help="Where to write the resulting JSON"
    )
    p.add_argument(
        "--dry-run", action="store_true",
        help="Skip any API calls, just print OCR & JSON skeleton"
    )
    args = p.parse_args()

    build_course_json(args.images, args.output, dry_run=args.dry_run)
    print(f"Written {args.output}")
