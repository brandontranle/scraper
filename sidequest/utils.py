from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import requests
from config import CHROME_DRIVER_PATH
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.service import Service
from config import MAX_APPS, FILENAME, MAX_THREADS, URL, DIRECTORY
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
import os


def init_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    service = Service(CHROME_DRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def dismiss_cookie_banner(driver):
    try:
        WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.CLASS_NAME, 'cky-btn-accept')))
        accept_button = driver.find_element(By.CLASS_NAME, 'cky-btn-accept')
        accept_button.click()
        print("Cookie banner dismissed.")
    except Exception as e:
        print(f"Error dismissing cookie banner: {e}")


# lazy loading fix
def page_down_to_load_apps(driver, max_apps=MAX_APPS):
    app_divs = []
    unique_apps = set()  
    scroll_pause_time = 2 
    body = driver.find_element(By.TAG_NAME, 'body')

    dismiss_cookie_banner(driver)

    div = driver.find_element(By.CLASS_NAME, 'virtual-scroller')
    div.click()
   
    while len(app_divs) < max_apps:
        body.send_keys(Keys.PAGE_DOWN)
        time.sleep(scroll_pause_time)

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        new_app_divs = soup.find_all('div', class_='virtual-scroller__card-wrapper')

        for app in new_app_divs:
            app_id = app.find('a')['href']  # href as id
            if app_id not in unique_apps:
                app_divs.append(app)
                unique_apps.add(app_id)

                if len(app_divs) >= max_apps:
                    print(f"Loaded the maximum of {max_apps} apps. Stopping.")
                    return app_divs

        print(f"Loaded {len(app_divs)} unique apps so far.")

        if len(new_app_divs) == 0:
            print(f"No more apps found after scrolling. Stopping.")
            break

    return app_divs

def write_reviews_to_csv(all_reviews):
    os.makedirs(DIRECTORY, exist_ok=True)
    full_txt_filename = os.path.join(DIRECTORY, FILENAME)

    with open(full_txt_filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['App Name', 'Reviewer', 'Date', 'Rating', 'Review Text', 'Upvotes', 'Comments', 'Review URL'])  # CSV header
        for review in all_reviews:
            writer.writerow(review)


def fetch_all_reviews_from_api(app_id, app_name):
    all_reviews = []
    limit = 200  # maximum payload size
    skip = 0

    print(f"Fetching reviews for {app_name}.")

    while True:
        api_url = f"https://api.sidequestvr.com/v2/apps/{app_id}/posts"
        params = {
            "skip": skip,
            "limit": limit,
            "descending": "true,true,true,true",
            "sortOn": "is_verified_review",
        }

        try:
            response = requests.get(api_url, params=params)
            if response.status_code == 200:
                reviews = response.json()
                if len(reviews) == 0:  # If no more reviews are returned, break out of the loop
                    break
                all_reviews.extend(reviews)
                skip += limit  # Move to the next set of reviews
            else:
                print(f"Failed to fetch reviews for app ID {app_id}. Status Code: {response.status_code}")
                break
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            break

    return app_name, all_reviews

def scrape_sidequest():
    start_time = time.time()

    driver = init_driver()
    driver.get(URL)

    app_divs = page_down_to_load_apps(driver, max_apps=MAX_APPS)
    driver.quit()

    all_reviews = []
    apps_to_scrape = []

    for app in app_divs:
        app_name = app.find('span', class_='w-full overflow-ellipsis grey-text').text.strip()
        app_link = app.find('a')['href']
        
        try:
            app_id = app_link.split('/')[-2]
            if not app_id.isdigit():
                print(f"Skipping invalid ID for {app_name}. Extracted ID: {app_id}")
                continue
            apps_to_scrape.append((app_id, app_name))  # Collect app ID and app name
            print(f"Added {app_name} with ID {app_id} for scraping.")
        except IndexError:
            print(f"Error extracting app ID from {app_link} for app {app_name}")
            continue

    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        futures = []
        for app_id, app_name in apps_to_scrape:
            futures.append(executor.submit(fetch_all_reviews_from_api, app_id, app_name))

        for future in as_completed(futures):
            try:
                app_name, reviews = future.result()  # Get both app_name and reviews from the future result

                print(f"Processing reviews for {app_name}.")
                for review in reviews:
                    review_text = review.get('body', 'No review text') or 'No review text'
                    review_entry = [
                        app_name,  # Correct app name is used here
                        review.get('user_name', 'Anonymous'),  # Reviewer name
                        review.get('created_at', 'Unknown Date'),  # Review date
                        review.get('app_rating', 'No Rating'),  # Rating
                        review_text.replace('\n', ' ').replace('\r', ''),  # Cleaned review text
                        review.get('upvotes', 0),  # Upvotes
                        review.get('comments', 0),  # Number of comments
                        review.get('url', 'No URL')  # Link to video review, if any
                    ]
                    if review_entry not in all_reviews:
                        all_reviews.append(review_entry)

            except Exception as exc:
                print(f"Error during scraping: {exc}")

    
    write_reviews_to_csv(all_reviews)

    end_time = time.time()
    execution_time = end_time - start_time
    print(f"Scraping sidequest took {execution_time:.2f} seconds.")

