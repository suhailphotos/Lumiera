#!/usr/bin/env python3
"""
yank_releases.py

Automate yanking or deleting old PyPI package releases via Selenium.
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import time

# -----------------------
# Configuration
# -----------------------
PYPI_USERNAME = os.getenv("PYPI_USERNAME")
PYPI_PASSWORD = os.getenv("PYPI_PASSWORD")
PROJECT_NAME = "incept"
# List of versions to yank (all except latest)
VERSIONS = [
    "0.1.112", "0.1.111", "0.1.110", "0.1.109", "0.1.108", "0.1.107", "0.1.106", "0.1.105",
    "0.1.104", "0.1.103", "0.1.102", "0.1.101", "0.1.100", "0.1.99",  "0.1.98",  "0.1.97",
    "0.1.96",  "0.1.95",  "0.1.94",  "0.1.93",  "0.1.92",  "0.1.91",  "0.1.90",  "0.1.89",
    "0.1.88",  "0.1.87",  "0.1.86",  "0.1.85",  "0.1.84",  "0.1.83",  "0.1.82",  "0.1.81",
    "0.1.80",  "0.1.79",  "0.1.78",  "0.1.77",  "0.1.76",  "0.1.75",  "0.1.74",  "0.1.73",
    "0.1.72",  "0.1.71",  "0.1.70",  "0.1.69",  "0.1.68",  "0.1.67",  "0.1.66",  "0.1.65",
    "0.1.64",  "0.1.63",  "0.1.62",  "0.1.61",  "0.1.60",  "0.1.59",  "0.1.58",  "0.1.57",
    "0.1.56",  "0.1.55",  "0.1.54",  "0.1.53",  "0.1.52",  "0.1.51",  "0.1.50",  "0.1.49",
    "0.1.48",  "0.1.46",  "0.1.45",  "0.1.44",  "0.1.43",  "0.1.42",  "0.1.41",  "0.1.40",
    "0.1.39",  "0.1.38",  "0.1.37",  "0.1.36",  "0.1.35",  "0.1.34",  "0.1.33",  "0.1.32",
    "0.1.31",  "0.1.30",  "0.1.29",  "0.1.28",  "0.1.27",  "0.1.26",  "0.1.25",  "0.1.24",
    "0.1.23",  "0.1.22",  "0.1.21",  "0.1.20",  "0.1.19",  "0.1.18"
]
ACTION = "Delete"  # or "Delete"

# -----------------------
# Helper: click and confirm
# -----------------------
def process_version(driver, version):
    wait = WebDriverWait(driver, 10)
    # Find the version link on the page
    version_link = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, version)))
    # Navigate up to the release row container
    release_row = version_link.find_element(By.XPATH, "./ancestor::tr")
    # Open the Options menu
    options_btn = release_row.find_element(By.XPATH, ".//button[contains(., 'Options')]")
    options_btn.click()
    # Click the Yank or Delete link
    action_link = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, ACTION)))
    action_link.click()
    # Wait for modal, type version, and confirm
    modal = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "modal-content")))
    inp = modal.find_element(By.XPATH, ".//input[@name='version']")
    inp.send_keys(version)
    confirm_btn = modal.find_element(By.XPATH, f".//button[contains(text(), '{ACTION}')]")
    confirm_btn.click()
    wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, "modal-content")))
    print(f"{ACTION}ed version {version}")

# -----------------------
# Main
# -----------------------
if __name__ == "__main__":
    # Launch Chrome (or adjust to Firefox)
    driver = webdriver.Chrome()
    driver.maximize_window()

    # 1) Log in
    # …
    driver.get("https://pypi.org/account/login/")
    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.NAME, "username"))).send_keys(PYPI_USERNAME)
    driver.find_element(By.NAME, "password").send_keys(PYPI_PASSWORD)
    
    # NEW: click the submit button by its type
    wait.until(EC.element_to_be_clickable((
        By.CSS_SELECTOR,
        "button[type='submit'], input[type='submit']"
    ))).click()
# …

    # 2) Go to releases page
    driver.get(f"https://pypi.org/manage/project/{PROJECT_NAME}/releases/")

    # 3) Loop through versions
    for ver in VERSIONS:
        try:
            process_version(driver, ver)
            time.sleep(1)
        except Exception as e:
            print(f"Failed to {ACTION.lower()} {ver}: {e}")

    driver.quit()
