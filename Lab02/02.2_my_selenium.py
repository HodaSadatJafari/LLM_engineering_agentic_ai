from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

options = Options()
# options.add_argument("--headless=new")  # headless mode (new headless for chrome)

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()), options=options
)

try:
    driver.get("https://www.geeksforgeeks.org/courses")
    time.sleep(2)  # wait for JS
    courses = driver.find_elements(
        By.CLASS_NAME,
        "courseListingPage_cardLayout__multW",
    )
    results = []
    for course in courses:
        try:
            cards = course.find_elements(By.TAG_NAME, "a")
            for card in cards:
                all_h4 = course.find_elements(By.TAG_NAME, "h4")
                for h4 in all_h4:
                    title = h4.text
                    url = h4.get_attribute("href")
        except Exception as e:
            print(e)

        results.append({"title": title, "url": url})
    print(results)
finally:
    driver.quit()
