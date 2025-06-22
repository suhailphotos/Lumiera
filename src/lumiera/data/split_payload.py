#!/usr/bin/env python3
import json
from pathlib import Path

# adjust as needed
IN_FILE  = Path.home() / ".incept" / "payload" / "intro_to_ml.json"
OUT_DIR  = IN_FILE.parent

# helper: shallow-copy all keys except the one in skip_keys
def copy_except(d: dict, skip_keys: set):
    return {k: v for k, v in d.items() if k not in skip_keys}

def make_payload(course: dict,
                 chapter_idxs: list[int],
                 lesson_slices: dict[int, tuple[int, int | None]] | None = None
) -> dict:
    """
    Build {"courses":[...]} with:
      - only the chapters at chapter_idxs
      - for each chapter i in lesson_slices, slice its lessons[i_start:i_end]
        (if i not in lesson_slices, take all lessons)
    """
    # copy everything but chapters
    new_course = copy_except(course, {"chapters"})
    new_chapters = []
    for ci in chapter_idxs:
        chap = course["chapters"][ci]
        chap_copy = copy_except(chap, {"lessons"})
        lessons = chap.get("lessons", [])
        if lesson_slices and ci in lesson_slices:
            start, end = lesson_slices[ci]
            chap_copy["lessons"] = lessons[start:end]
        else:
            chap_copy["lessons"] = lessons
        new_chapters.append(chap_copy)
    new_course["chapters"] = new_chapters
    return {"courses": [new_course]}

def main():
    data = json.loads(IN_FILE.read_text())
    course = data["courses"][0]

    jobs = [
        # payload file         chapter idxs     lesson_slices
        ("intro_to_ml_ch1-5.json",  [0,1,2,3,4],       None),
        ("intro_to_ml_ch6-7.json", [5,6],         None),
        ("intro_to_ml_ch8.json",   [7],           None),
        ("intro_to_ml_ch9.json",   [8],           None),
        # for chapter 8 (idx 7), lessons 1-3 (idx 0..2)
        ("intro_to_ml_ch10_l1-3.json",[9],          {9:(0,3)}),
        # for chapter 8, lessons 4..end (idx 3..None)
        ("intro_to_ml_ch10_l4-end.json",[9],         {9:(3,None)}),
    ]

    for fname, ch_idxs, ls_slices in jobs:
        out = OUT_DIR / fname
        subset = make_payload(course, ch_idxs, ls_slices)
        out.write_text(json.dumps(subset, indent=2))
        print(f"Wrote {out}")

if __name__ == "__main__":
    main()
