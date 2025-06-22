#!/usr/bin/env python3
import json
from pathlib import Path

def make_subset(data, num_courses=1, num_chapters=2, num_lessons=1):
    subset = {'courses': []}
    for course in data.get('courses', [])[:num_courses]:
        # shallow‐copy the course, then replace its 'chapters' list
        new_course = dict(course)
        new_course['chapters'] = []

        for chap in course.get('chapters', [])[:num_chapters]:
            # shallow‐copy the chapter, then replace its lessons
            new_chap = dict(chap)
            # adjust this key if yours is actually 'lesssons'
            lesson_key = 'lessons' if 'lessons' in chap else 'lesssons'
            new_chap[lesson_key] = chap.get(lesson_key, [])[:num_lessons]
            new_course['chapters'].append(new_chap)

        subset['courses'].append(new_course)
    return subset

def main():
    home = Path.home()
    infile  = home / '.incept' / 'payload' / 'cine_light.json'
    outfile = home / '.incept' / 'payload' / 'cine_light_subset.json'

    # load full payload
    data = json.loads(infile.read_text())

    # build small subset
    small = make_subset(data, num_courses=1, num_chapters=2, num_lessons=1)

    # write it out
    outfile.write_text(json.dumps(small, indent=2))
    print(f"Wrote subset payload to {outfile}")

if __name__ == '__main__':
    main()
