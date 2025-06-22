from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import time

UDEMY_EMAIL = 'suhailece@gmail.com'
UDEMY_PASSWORD = 'hoqpyq-zutrep-2dUjwu'
COURSE_URL = 'https://www.udemy.com/course/advanced-langchain-techniques-mastering-rag-applications/learn/'

driver = webdriver.Chrome()
driver.maximize_window()
driver.get('https://www.udemy.com/join/login-popup/')

wait = WebDriverWait(driver, 30)

# Handle cookie banner if it appears
try:
    cookie_button = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Accept All Cookies')]"))
    )
    cookie_button.click()
    print("Clicked cookie consent")
except:
    print("No cookie popup appeared")

# Wait for email and password fields
#email_input = wait.until(EC.presence_of_element_located((By.NAME, "email")))
#password_input = wait.until(EC.presence_of_element_located((By.NAME, "password")))
#
#email_input.send_keys(UDEMY_EMAIL)
#password_input.send_keys(UDEMY_PASSWORD)
#password_input.send_keys(Keys.RETURN)

# Wait for login to complete (you may want to increase the time for slow connections)
wait.until(EC.url_contains("/courses"))
print("Logged in!")

driver.get(COURSE_URL)
time.sleep(8)  # Wait for course page to load

# Expand all sections
expand_buttons = driver.find_elements(By.CSS_SELECTOR, '[data-purpose="section-toggle"]')
for btn in expand_buttons:
    driver.execute_script("arguments[0].click();", btn)
    time.sleep(0.5)

time.sleep(2)  # Wait for all sections to load

# Extract section and lesson names
sections = driver.find_elements(By.CSS_SELECTOR, '.section--section--BukKG')

for section in sections:
    section_title = section.find_element(By.CSS_SELECTOR, '.section--section-title--8blTh').text
    print(f'\n## {section_title}')
    lessons = section.find_elements(By.CSS_SELECTOR, '.curriculum-item-link--content--2VQ9P')
    for lesson in lessons:
        lesson_title = lesson.text
        print(f'- {lesson_title}')

driver.quit()
