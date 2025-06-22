# src/pythonkitchen/download_rebelway.py

import os
import re
import sys
import html
import time
import pandas as pd
import requests
import browser_cookie3

from urllib.parse       import urlsplit
from selenium           import webdriver
from selenium.webdriver.chrome.options  import Options
from selenium.webdriver.chrome.service  import Service
from webdriver_manager.chrome          import ChromeDriverManager
from selenium.common.exceptions import InvalidSessionIdException
from requests.adapters   import HTTPAdapter
from urllib3.util.retry   import Retry
from bs4                 import BeautifulSoup

# — CONFIG — 
EXCEL_PATH   = os.path.expanduser('~/Desktop/course_template.xlsx')
SHEET_NAME   = 'lessons'
SKIP_FIRST   = 48     # skip rows 0–18, resume at row 19 (the 20th)
OUT_DIR      = os.path.expanduser('~/Downloads/RebelwaySource')
TIMEOUT_CONN = 10      # seconds for connect
TIMEOUT_READ = 300     # seconds for read
RETRY_TOTAL  = 5       # number of retries on failure

# — HELPERS — 
def slugify(text: str) -> str:
    # lowercase, drop non-alphanum/space, collapse spaces → _
    s = text.lower()
    s = re.sub(r'[^a-z0-9\s-]', '', s)
    s = re.sub(r'\s+', '_', s.strip())
    return s

def make_chrome_driver():
    opts = Options()
    opts.add_argument("--headless")
    # attach to your already‐running Chrome on port 9222
    opts.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    svc  = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=svc, options=opts)

def make_download_session():
    # piggy-back your Chrome cookies for auth
    cj   = browser_cookie3.chrome()
    sess = requests.Session()
    sess.cookies.update(cj)
    # retry on timeouts, 5xx, 429
    retry = Retry(
        total=RETRY_TOTAL,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    adapter = HTTPAdapter(max_retries=retry)
    sess.mount("https://", adapter)
    sess.mount("http://", adapter)
    return sess

def find_source_url(html_text: str) -> str | None:
    soup = BeautifulSoup(html_text, "html.parser")
    sel  = soup.select_one("select.video-download-selector")
    if not sel:
        return None
    for opt in sel.find_all("option"):
        if "source" in opt.get_text(strip=True).lower():
            # unescape &amp; → &
            return html.unescape(opt["value"])
    return None

def download_with_stream(sess: requests.Session, url: str, dest: str):
    # stream with generous read timeout
    with sess.get(url, stream=True, timeout=(TIMEOUT_CONN, TIMEOUT_READ)) as r:
        r.raise_for_status()
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "wb") as f:
            for chunk in r.iter_content(1024*1024):
                if chunk:
                    f.write(chunk)

def main():
    # load the full lessons sheet
    df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME, engine="openpyxl")
    if not {"chapter_index","name","link"}.issubset(df.columns):
        print("🚨 Missing one of required columns (chapter_index,name,link).", file=sys.stderr)
        sys.exit(1)

    driver  = make_chrome_driver()
    sess_dl = make_download_session()

    os.makedirs(OUT_DIR, exist_ok=True)

    # seed episode counters by counting the first SKIP_FIRST rows
    ep_counters = {}
    for pre in df.iloc[:SKIP_FIRST].itertuples():
        chap = int(pre.chapter_index)
        ep_counters[chap] = ep_counters.get(chap, 0) + 1

    for idx, row in df.iterrows():
        # skip the already-downloaded lessons
        if idx < SKIP_FIRST:
            continue


        chap   = int(row["chapter_index"])
        title  = str(row["name"])
        lesson = row["link"]

        # episode numbering: increment for every row, broken or not
        ep_counters.setdefault(chap, 0)
        ep_counters[chap] += 1
        season  = chap
        episode = ep_counters[chap]

        slug = slugify(title)

        print(f"\n➡️  [{idx+1}] Loading {lesson} (s{season:02d}e{episode:02d})")
        # Safely load the lesson page (restart Chrome if needed)
        try:
            driver.get(lesson)
        except InvalidSessionIdException:
            print("🔄 Chrome session died, restarting…")
            driver.quit()
            driver = make_chrome_driver()
            driver.get(lesson)
        driver.implicitly_wait(3)  # let JS inject the widget
        html_body = driver.page_source
        src_url   = find_source_url(html_body)
        if not src_url:
            print(f"No SOURCE option found for s{season:02d}e{episode:02d}.")
            continue

        ext = os.path.splitext(urlsplit(src_url).path)[1] or ".mp4"

        fname = f"s{season:02d}e{episode:02d}_{slug}{ext}"
        dest  = os.path.join(OUT_DIR, fname)
        # 1) Skip if we already have it
        if os.path.exists(dest):
            print(f"⏭ Skipping already downloaded: {fname}")
            continue

        # 2) Include Referer header for downloads (Vimeo progressive-redirect)
        sess_dl.headers["Referer"] = lesson

        print(f"↓ Downloading → {fname}")
        try:
            download_with_stream(sess_dl, src_url, dest)
            print(f"✔  Saved: {dest}")
        except Exception as e:
            print(f"Failed: {e}")

    driver.quit()
    print("\n🎉 All done.")

if __name__ == "__main__":
    main()
