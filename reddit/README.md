
# Reddit Scraper

A Python-based Reddit scraper that collects and analyzes data from Reddit using the Reddit API (PRAW or another method). This tool is designed to extract posts, comments, and metadata from specified subreddits or user profiles to assist with data analysis, security research, and more.

**Note**: To see notes I took during my development process, please view `notes.txt`

## Prerequisites
- **Python 3.7 or higher**: Ensure your environment supports Python 3.7 or newer.
- **PRAW (Python Reddit API Wrapper)**: Install PRAW for accessing the Reddit API.
- **pandas**: Used for handling and saving scraped data as `.csv` files.
- **concurrent.futures**: For parallel processing to speed up scraping tasks.
- **strip_markdown**: For removing markdown from bodies of text.

To install the necessary dependencies, run:

```bash
pip install praw pandas strip_markdown
```

## How does it work?
This Reddit scraper works by connecting to Reddit via the PRAW API. It searches for posts and collects their metadata (title, author, score, etc.) along with their comments. The scraper allows users to save the data as either .txt (for better readability) or .csv files. 

The scraper is designed to handle rate limiting and API restrictions by retrying API requests when necessary. It can scrape multiple topics in parallel using the concurrent.futures library for increased efficiency.

## Key Features
* Scrapes posts, including comments with replies, and metadata, from either specific or all subreddits (default).
* Cleans and formats the data to remove * Markdown formatting for easier analysis.
* Saves the output in either .txt or .csv format.
* Handles rate limits and retries when necessary.
* Supports parallel scraping for multiple topics, improving performance


## Getting Started

**API Setup**

To access the Reddit API, you will need to create a Reddit app and generate API credentials. Follow these steps:

* Go to Reddit's App Preferences.
* Click "Create App" or "Create Another App."
* Choose the "Script" option and fill out the form with your app's details.
* Copy the client_id, client_secret, and user_agent for use in your code.


Update your `config.py` file with your credentials as follows:

```
CLIENT_INFO = {
    'client_id': 'your_client_id',
    'client_secret': 'your_client_secret',
    'user_agent': 'your_user_agent'
}
```

## Execution
You can scrape posts and comments from specific topics (subreddits) by defining the topics and filenames in the `config.py` file:
```
TOPICS_WITH_FILENAMES = [
    ('computersecurity OR cybersecurity', 'digitalsecurity.{FILE_TYPE}'),
    ('learnprogramming', 'learnprogramming_posts.{FILE_TYPE}')
]
```

Adjust file extension if necessary (supports txt or csv)
```
FILE_TYPE = 'txt' #no '.' necessary
```

After setting up the options you can run the scraper:
```
python scrape.py
```

## Challenges
**Rate Limiting**

Initialy, I had issues with Reddit's rate limits on API usage which had crashed previous iterations of my scraper. However, the scraper automatically handles these limits by detecting the rate limit responses and waiting for the required time before retrying (60 seconds by default). A limitation though is that when scraping large amounts of data, the process can be slowed by these rate limits.

**Formatting Replies**

PRAW is able to easily fetch comments instaneously; however, the format is severely off in comparison to the actual conversation. This is because when the comments are returned, they are returned in a flat-list rather than a hierachy or tree structure to represent the nested replies. To work around this, the scraper uses `process_comment` which is a recursive function that traverses each comment and its replies and increases the level by 1 (i.e. a top-level comment starts at 0)

**Large Data Volume == Slow Performance**

Initially, it took around 66 minutes to scrape 220 posts and over 89,000 comments or replies. To optimize this scraper, I implemented a multithreading feature that assigns a thread to every topic that has posts to be scraped. Doing this shortened runtime by 50%. 

**Markdown Formatting**

Reddit comments and posts often include Markdown formatting, which may not be suitable for analysis. Initially, there was a bug that corrupted the format of a CSV file output which caused the content of a markdown post to spread into other indices. To resolve this, the scraper includes a function to clean and remove this formatting for easier processing of the data thanks to `strip_markdown`.
