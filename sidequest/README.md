
# SideQuestVR Scraper

A Python-based scraper for collecting and analyzing reviews and data from `sidequestvr.com`. This tool automates the extraction of VR app reviews, including user feedback, ratings, and metadata, using both Selenium for dynamic web interaction and an API for fetching detailed app reviews.

**Note**: To see notes I took during my development process, please view `notes.txt`

## Prerequisites
- **Python 3.7 or higher**: Ensure your environment supports Python 3.7 or newer.
- **Selenium**: For interacting with dynamic web content and automating browser tasks.
- **requests**: Used for making API requests to fetch review data.
- **BeautifulSoup (bs4)**: For parsing HTML to collect app details from the webpage.
- **concurrent.futures**: Enables parallel processing to speed up scraping tasks.
- **Google ChromeDriver**: Required for Selenium to automate web browsing (ensure it is installed and matches your Chrome version).
- **CSV module**: To save collected data in .csv format.

To install the necessary dependencies, run:

```bash
pip install selenium requests beautifulsoup4
```

## How does it work?
This scraper works in two phases:
 - **Web scraping using Selenium & BS4**: It scrolls through the `sidequestvr.com` app listings, bypasses lazy loading by simulating user scrolling, and extracts app urls within an headless Chrome instance.
- **API requests**: For each app, it fetches all available reviews using SideQuest’s API, collecting details such as review text, reviewer name, rating, upvotes, and more.


The data is saved as a `.csv` file.

## Key Features
* **Dynamic Web Scraping**: This scraper Selenium to scroll through app listings and load app details dynamically.
* **API Integration**: Fetches up to 200 reviews per API call, ensuring comprehensive data collection.
* **CSV Export**: Saves the extracted reviews and metadata into a CSV file for easy analysis.
* **Cookie Banner Handling**: Automatically dismisses the cookie banner to prevent interruptions.
* **Multithreaded Scraping**: Utilizes the ThreadPoolExecutor for scraping multiple apps and reviews in parallel, improving performance.
Error Handling: Gracefully handles network issues and retries API calls when needed.


## Getting Started

**ChromeDriver Setup**

Download and install the appropriate version of ChromeDriver and update the CHROME_DRIVER_PATH in your config.py file.

```
CHROME_DRIVER_PATH = 'path/to/chromedriver'
```

**Configurations**
You can adjust the following settings in `config.py`:

- `MAX_APPS`: Controls maximum number of apps to scrape
- `MAX_THREADS`: Controls number of threads used for parellel processing
- `FILENAME`: Controls the filename for the CSV data
- `URL`: Controls the URL to scrape app listings from (by default it is the most popular page)


## Execution

Set up your `config.py` file with the required variables
```
CHROME_DRIVER_PATH = 'path/to/chromedriver.exe'

MAX_APPS = 100

MAX_THREADS = 5

URL = 'https://sidequestvr.com/category/all?sortOn=downloads' 

FILENAME = 'sidequestvr.csv'
```

Run the scraper
```
python scrape.py
```

## Challenges
**Lazy Loading**

During development, I had issues with scraping app links due to the lazy loading mechanism of the app listings page. To resolve this, the scraper uses Selenium to scroll through the page and load additional apps dynamically by simulating a user scrolling. With each scroll stroke, urls are being extracted from `<a>` tags of the `virtual-scroller__card-wrapper` class elements.

**Performance**

I initially was limited to no more than 10 reviews per app without the scraper taking over 30 minutes to scrape 1,000 reviews across 100 applications. However, I significantly improved runtime by identifying the following API 

```
https://api.sidequestvr.com/v2/apps/{app_id}/posts?skip={skip}&limit={limit}&descending=true,true,true,true&sortOn={sort_criteria}
```
I combined using this API with multiple threads with the `concurrent.futures` module, thus enabling the ability to scrape multiple apps concurenntly. This API allowed me to disable any boundaries or limitations to the amount of reviews I am able to scrape since it eliminated the need to load reviews one page at a time.

The following showcases the configurations and results of a benchmark that emphasize how performance improved by over 95%:
```
MAX_APPS = 200
MAX_THREADS = 5
TOTAL REVIEWS: 32639
Scraping sidequest took 160.81 seconds.
```
