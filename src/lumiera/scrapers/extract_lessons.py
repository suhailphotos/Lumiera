import re
from urllib.parse import urlparse
import pandas as pd

def extract_lesson_name(url: str) -> str:
    """
    Given a Rebelway URL like
      https://rebelway.academy/topic/00_intro-60/
      https://rebelway.academy/topic/04_functions-5/
    returns
      'Intro'
      'Functions'
    """
    # 1) parse out the path, drop trailing slash, get last piece
    path = urlparse(url).path.rstrip('/')
    last = path.split('/')[-1]

    # 2) remove any leading digits + optional underscore/hyphen
    no_prefix = re.sub(r'^\d+[_-]?', '', last)

    # 3) remove any trailing hyphen/underscore + digits (e.g. "-60", "_5")
    no_suffix = re.sub(r'[-_]\d+$', '', no_prefix)

    # 4) turn remaining underscores/hyphens into spaces
    spaced = re.sub(r'[-_]+', ' ', no_suffix).strip()

    # 5) title-case each word
    return spaced.title()

def build_lessons_csv(excel_path: str, output_csv: str):
    # 1) load the lessons sheet
    df = pd.read_excel(excel_path, sheet_name="lessons")
    
    # 2) assume the column containing URLs is named 'link'; adjust if needed
    df['name'] = df['link'].apply(extract_lesson_name)
    
    # 3) keep only name + link, and write out
    df[['name', 'link']].to_csv(output_csv, index=False)
    print(f"Wrote {len(df)} lessons to {output_csv}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python extract_lessons.py <input.xlsx> <output.csv>")
        sys.exit(1)
    build_lessons_csv(sys.argv[1], sys.argv[2])
