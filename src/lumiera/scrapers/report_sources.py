# src/pythonkitchen/report_broken_sources.property

import os
import sys
import html
import pandas as pd
import browser_cookie3

from selenium import webdriver
from selenium.webdriver.chrome.options  import Options
from selenium.webdriver.chrome.service  import Service
from webdriver_manager.chrome          import ChromeDriverManager
from selenium.common.exceptions       import InvalidSessionIdException
from bs4                                import BeautifulSoup

# — CONFIG — 
EXCEL_PATH = os.path.expanduser('~/Desktop/course_template.xlsx')
SHEET_NAME = 'lessons'
OUTPUT_CSV = os.path.expanduser('~/Desktop/broken_sources_report.csv')

# — HELPERS — 
def make_chrome_driver():
    opts = Options()
    opts.add_argument("--headless")
    # attach to your already‐running Chrome on port 9222
    opts.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    svc  = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=svc, options=opts)

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

def main():
    # 1) Load the sheet
    df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME, engine="openpyxl")
    if not {"chapter_index","name","link"}.issubset(df.columns):
        print("🚨 Missing one of required columns (chapter_index,name,link).", file=sys.stderr)
        sys.exit(1)

    driver = make_chrome_driver()
    broken = []

    # 2) Iterate every lesson
    for i, row in df.iterrows():
        lesson_url = row["link"]
        chapter    = row["chapter_index"]
        title      = row["name"]

        # load page, restarting Chrome if needed
        try:
            driver.get(lesson_url)
        except InvalidSessionIdException:
            print(f"🔄 Session died at row {i+2}, restarting Chrome…")
            driver.quit()
            driver = make_chrome_driver()
            driver.get(lesson_url)

        driver.implicitly_wait(3)
        html_body = driver.page_source

        # check for SOURCE
        src = find_source_url(html_body)
        if not src:
            broken.append({
                "row"          : i+2,             # +2 because pandas index 0 + header row
                "chapter_index": chapter,
                "name"         : title,
                "link"         : lesson_url,
            })
            print(f"❌ Row {i+2}: No SOURCE → {lesson_url}")

    driver.quit()

    # 3) Write out CSV
    if broken:
        out_df = pd.DataFrame(broken)
        out_df.to_csv(OUTPUT_CSV, index=False)
        print(f"\n✅ Found {len(broken)} broken SOURCE entries.")
        print(f"→ Report saved to {OUTPUT_CSV}")
    else:
        print("\n🎉 All lessons have a SOURCE option!")

if __name__ == "__main__":
    main()
