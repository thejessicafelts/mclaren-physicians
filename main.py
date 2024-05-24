from playwright.sync_api import sync_playwright
import time
import csv

with open("physicians.csv", "r") as f:
    reader = csv.reader(f)
    physicians = [physician[0] for physician in reader]

url_error = "Error"

with sync_playwright() as p:
    
    # Launch Chromium
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    # Go to McLaren Physician Directory
    directory_url = "https://www.mclaren.org/main/physician-directory/"
    page.goto(directory_url)

    time.sleep(1)

    # Physician ID

    results = []

    for physician in physicians:
        page.goto(directory_url + str(physician))
        time.sleep(1)
        if url_error in page.url:
            pass
        else:
            print(f"SUCCESS: " + str(physician))
            results.append(str(physician))

    # Close the browser
    browser.close()
    print(results)