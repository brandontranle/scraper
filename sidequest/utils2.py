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
import random

def fetch_all_games():
    all_games = []
    limit = 10000 # all games available
    max_retries = 5
    base_delay = 1.0
    max_delay = 30.0

    api_url = "https://api.sidequestvr.com/v2/apps"
    params = {
        "limit": limit,
        "sortOn": "hot_sort_rating",
        "descending": "true"
    }

    retries = 0
    while retries < max_retries:
        try:
            response = requests.get(api_url, params=params)
            if response.status_code == 200:
                games = response.json()
                all_games.extend(games)
                return all_games
            elif response.status_code == 429:  # Too Many Requests
                print("Rate limited. Retrying after delay.")
                delay = min(base_delay * (2 ** retries), max_delay)
                time.sleep(delay)
                retries += 1
            else:
                print(f"Failed to fetch games. Status Code: {response.status_code}")
                return all_games
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}. Retrying...")
            delay = min(base_delay * (2 ** retries), max_delay)
            time.sleep(delay)
            retries += 1




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
    limit = 5000  # maximum payload size
    skip = 0
    max_retries = 5  # Maximum number of retries for a failed request
    base_delay = 1.0  # Base delay in seconds for retries
    max_delay = 30.0  # Maximum delay in seconds

    print(f"Fetching reviews for {app_name}.")

    while True:
        api_url = f"https://api.sidequestvr.com/v2/apps/{app_id}/posts"
        params = {
            "skip": skip,
            "limit": limit,
            "descending": "true,true,true,true",
            "sortOn": "is_verified_review",
        }

        retries = 0
        while retries < max_retries:
            try:
                response = requests.get(api_url, params=params)
                if response.status_code == 200:
                    reviews = response.json()
                    print(f"Received {len(reviews)} reviews for {app_name}.")
                    if len(reviews) == 0:  # If no more reviews are returned, break out of the loop
                        return app_name, all_reviews
                    all_reviews.extend(reviews)

                    # Random delay to avoid rate limiting
                    delay = random.uniform(1, 3)
                    time.sleep(delay)
                    break  # Exit retry loop on success
                elif response.status_code == 429:  # Too Many Requests
                    print(f"Rate limited for {app_name}. Retrying after delay.")
                    delay = min(base_delay * (2 ** retries), max_delay)
                    time.sleep(delay)
                    retries += 1
                else:
                    print(f"Failed to fetch reviews for app ID {app_id}. Status Code: {response.status_code}")
                    return app_name, all_reviews
            except requests.exceptions.RequestException as e:
                print(f"Request failed: {e}. Retrying...")
                delay = min(base_delay * (2 ** retries), max_delay)
                time.sleep(delay)
                retries += 1

        if retries == max_retries:
            print(f"Max retries reached for {app_name}. Stopping fetching for this app.")
            return app_name, all_reviews
        
        return app_name, all_reviews

def scrape_sidequest():
    start_time = time.time()

    print("Fetching all games using the API.")
    all_games = fetch_all_games()  # Fetch all game data from the API

    if not all_games:
        print("No games fetched. Exiting.")
        return

    all_reviews = []
    apps_to_scrape = []

    for game in all_games:
        try:
            app_id = game.get('apps_id', None)  # Get app ID from API response
            app_name = game.get('name', 'Unknown App')  # Get app name
            if app_id:
                apps_to_scrape.append((app_id, app_name))  # Collect app ID and app name
                print(f"Added {app_name} with ID {app_id} for scraping.")
            else:
                print(f"Skipping invalid app: {app_name}")
        except Exception as e:
            print(f"Error processing game data: {e}")
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
    time.sleep(5)  # Wait for 5 seconds before exiting
    print("Exiting.")

