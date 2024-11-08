import praw
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from prawcore.exceptions import TooManyRequests
import pandas as pd
import csv
import re
import os
from config import CLIENT_INFO, KEY_WORDS, MAX_POSTS, MAX_RETRIES, TXT_DIR, CSV_DIR, FILE_TYPE, TOPICS_WITH_FILENAMES, SUBREDDITS, MULTI_REDDIT_USER, MULTI_REDDIT_NAME
from praw.models import MoreComments
import strip_markdown
import time
from tqdm import tqdm


def get_reddit_instance():
    return praw.Reddit(**CLIENT_INFO)

def clean_text(text):
    clean_text = strip_markdown.strip_markdown(text) 
    clean_text = clean_text.strip().replace('\r', '') 
    clean_text = re.sub(' +', ' ', clean_text)  #  multiple spaces to a single space
    clean_text = clean_text.replace('\n\n', '\n')  # paragraph breaks
    if FILE_TYPE == 'csv':
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    clean_text = '\n'.join(line.lstrip() for line in clean_text.splitlines())  # leading spaces per line
    return clean_text

def process_comment(comment, level=0):
    if isinstance(comment, MoreComments):
        return ''
    
    author = comment.author.name if comment.author else 'N/A'
    score = comment.score
    created_utc = comment.created_utc
    body = clean_text(comment.body)
    
    if FILE_TYPE != "csv":
        indentation = '    ' * level
        result = f"{indentation}[Author: {author}, Score: {score}, Posted: {created_utc}] {body}\n"
    else:
        result = f"[Author: {author}, Score: {score}, Posted: {created_utc}] {body}"
    
    # Process replies recursively
    replies = []
    if comment.replies:
        for reply in comment.replies:
            replies.append(process_comment(reply, level + 1))
    
    if FILE_TYPE == "csv":
        return result + ' ' + ' '.join(replies)
    else:
        return result + ''.join(replies)


def scrape_comments(submission, retries=MAX_RETRIES):
    try:
        if retries == MAX_RETRIES:
            submission.comments.replace_more(limit=None)  # only laod more ONCE 

        comments = []
        comment_ids_seen = set()

        for comment in submission.comments:
            if comment.id not in comment_ids_seen:
                comments.append(process_comment(comment))  # branch branch branch
                comment_ids_seen.add(comment.id)
            
        return " ".join(comments) if FILE_TYPE == "csv" else "\n".join(comments)
    
    except TooManyRequests as e:
        if retries > 0:
            wait_time = int(e.response.headers.get("retry-after", 60))
            print(f"Rate-limited while scraping comments. Retrying after {wait_time} seconds...")
            time.sleep(wait_time)
            return scrape_comments(submission, retries=retries - 1)
        else:
            print("Maximum retries reached. Skipping comments...")
            return ""

def scrape_reddit(reddit, query, limit=MAX_POSTS, retries=MAX_RETRIES, delay=2):
    posts = []
    subreddit = reddit.subreddit("all") 
    print(f"Scraping posts for topic: {query}")
    
    try:
        for submission in subreddit.search(query, limit=limit):
            time.sleep(delay)
            
            if any(keyword in submission.title.lower() or keyword in submission.selftext.lower() for keyword in KEY_WORDS):
                comments = scrape_comments(submission)
                
                post = {
                    'title': submission.title,
                    'author': submission.author.name if submission.author else 'N/A',
                    'subreddit': submission.subreddit.display_name,
                    'score': submission.score,
                    'created_utc': submission.created_utc,
                    'num_comments': submission.num_comments,
                    'url': f"https://www.reddit.com{submission.permalink}",
                    'selftext': clean_text(submission.selftext),
                    'comments': comments
                }
                
                posts.append(post)
    except TooManyRequests as e:
        if retries > 0:
            wait_time = int(e.response.headers.get("retry-after", 60))
            print(f"Rate-limited while scraping posts. Retrying after {wait_time} seconds...")
            time.sleep(wait_time)
            return scrape_reddit(reddit, query, limit, retries=retries - 1, delay=delay)
        else:
            print("Maximum retries reached for this query. Skipping...")
    return posts


def scrape_reddit_subs(reddit, subreddit_name, limit=MAX_POSTS, retries=MAX_RETRIES, delay=2):
    posts = []
    subreddit = reddit.subreddit(subreddit_name)
    print(f"Scraping posts for subreddit: {subreddit_name}")
    
    try:
        for submission in tqdm(subreddit.hot(limit=limit), desc=f"Scraping {subreddit_name}", unit="post"):
            time.sleep(delay)
            
            if any(keyword in submission.title.lower() or keyword in submission.selftext.lower() for keyword in KEY_WORDS):
                comments = scrape_comments(submission)
                
                post = {
                    'title': submission.title,
                    'author': submission.author.name if submission.author else 'N/A',
                    'subreddit': submission.subreddit.display_name,
                    'score': submission.score,
                    'created_utc': submission.created_utc,
                    'num_comments': submission.num_comments,
                    'url': f"https://www.reddit.com{submission.permalink}",
                    'selftext': clean_text(submission.selftext),
                    'comments': comments
                }
                
                posts.append(post)
    except TooManyRequests as e:
        if retries > 0:
            wait_time = int(e.response.headers.get("retry-after", 60))
            print(f"Rate-limited while scraping posts. Retrying after {wait_time} seconds...")
            time.sleep(wait_time)
            return scrape_reddit_subs(reddit, subreddit_name, limit, retries=retries - 1, delay=delay)
        else:
            print("Maximum retries reached for this query. Skipping...")
    return posts


def save_to_txt(posts, filename, directory=TXT_DIR):
    os.makedirs(directory, exist_ok=True)
    full_txt_filename = os.path.join(directory, filename)

    with open(full_txt_filename, 'w', encoding='utf-8') as f:
        for post in posts:
            f.write(
                f"POST TITLE: {post['title']}\n"
                f"AUTHOR: {post['author']}\n"
                f"SUBREDDIT: {post['subreddit']}\n"
                f"SCORE: {post['score']}\n"
                f"CREATED UTC: {post['created_utc']}\n"
                f"COMMENTS COUNT: {post['num_comments']}\n"
                f"URL: {post['url']}\n"
                f"POST BODY:\n{post['selftext']}\n"
                f"{'-' * 80}\n"
                f"COMMENTS:\n{post['comments']}\n"
                f"{'=' * 100}\n"
            )
    print(f"Data saved to {full_txt_filename}")

def save_to_csv(posts, filename, directory=CSV_DIR):
    os.makedirs(directory, exist_ok=True)
    full_csv_filename = os.path.join(directory, filename)

    df = pd.DataFrame(posts)
    df.to_csv(full_csv_filename, index=False, quoting=csv.QUOTE_ALL)
    print(f"Data saved to {full_csv_filename}")

def scrape_and_save_to_txt(reddit, topic, filename, limit=MAX_POSTS, delay=2):
    posts = []
    if SUBREDDITS:
        posts = scrape_reddit_subs(reddit, topic, limit, delay=delay)
    else:
        posts = scrape_reddit(reddit, topic, limit, delay=delay)
    save_to_txt(posts, filename)

def scrape_and_save_to_csv(reddit, topic, filename, limit=MAX_POSTS, delay=2):
    posts = []
    if SUBREDDITS:
        posts = scrape_reddit_subs(reddit, topic, limit, delay=delay)
    else:
        posts = scrape_reddit(reddit, topic, limit, delay=delay)
    save_to_csv(posts, filename)

''' 
def scrape(reddit, topics_with_files=TOPICS_WITH_FILENAMES, limit=MAX_POSTS, delay=2, file_type=FILE_TYPE):
    start_time = time.time()  

    with ThreadPoolExecutor() as executor:
        futures = []
        for topic, filename in topics_with_files:
            if file_type == 'txt':
                futures.append(executor.submit(scrape_and_save_to_txt, reddit, topic, filename, limit, delay))
            elif file_type == 'csv':
                futures.append(executor.submit(scrape_and_save_to_csv, reddit, topic, filename, limit, delay))
        
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Error in parallel scraping: {e}")
    end_time = time.time() 
    elapsed_time = end_time - start_time  

    print(f"Scraping completed in {elapsed_time:.2f} seconds.")
'''

def scrape_reddit_multireddit(reddit, user, multireddit_name, limit=MAX_POSTS, retries=MAX_RETRIES, delay=2):
    posts = []
    multireddit = reddit.multireddit(user, multireddit_name)
    print(f"Scraping posts from multireddit: {user}/{multireddit_name}")

    try:
        for submission in tqdm(multireddit.hot(limit=limit), desc=f"Scraping {user}/{multireddit_name}", unit="post"):
            time.sleep(delay)

            comments = scrape_comments(submission)

            post = {
                'title': submission.title,
                'author': submission.author.name if submission.author else 'N/A',
                'subreddit': submission.subreddit.display_name,
                'score': submission.score,
                'created_utc': submission.created_utc,
                'num_comments': submission.num_comments,
                'url': f"https://www.reddit.com{submission.permalink}",
                'selftext': clean_text(submission.selftext),
                'comments': comments
            }

            posts.append(post)
    except TooManyRequests as e:
        if retries > 0:
            wait_time = int(e.response.headers.get("retry-after", 60))
            print(f"Rate-limited while scraping posts. Retrying after {wait_time} seconds...")
            time.sleep(wait_time)
            return scrape_reddit_multireddit(reddit, user, multireddit_name, limit, retries=retries - 1, delay=delay)
        else:
            print("Maximum retries reached for this multireddit. Skipping...")
    return posts


def scrape(reddit, topics_with_files=TOPICS_WITH_FILENAMES, subreddits=SUBREDDITS, limit=MAX_POSTS, delay=2, file_type=FILE_TYPE, multireddit_user=MULTI_REDDIT_USER, multireddit_name=MULTI_REDDIT_NAME):
    start_time = time.time()
    
    # Check if a multireddit is specified
    if multireddit_user and multireddit_name:
        print("Scraping based on multireddit.")
        posts = scrape_reddit_multireddit(reddit, multireddit_user, multireddit_name, limit, delay=delay)
        filename = f"{multireddit_name}.{file_type}"
        if file_type == 'txt':
            save_to_txt(posts, filename)
        elif file_type == 'csv':
            save_to_csv(posts, filename)
    
    # Otherwise, proceed with topic or subreddit scraping
    elif topics_with_files:
        print("Scraping based on topics.")
        with ThreadPoolExecutor() as executor:
            futures = []
            for topic, filename in topics_with_files:
                if file_type == 'txt':
                    futures.append(executor.submit(scrape_and_save_to_txt, reddit, topic, filename, limit, delay))
                elif file_type == 'csv':
                    futures.append(executor.submit(scrape_and_save_to_csv, reddit, topic, filename, limit, delay))
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"Error in parallel scraping: {e}")
    else:
        print("Scraping based on subreddits only.")
        with ThreadPoolExecutor() as executor:
            futures = []
            for subreddit_name in subreddits:
                filename = f"{subreddit_name}.{file_type}"
                if file_type == 'txt':
                    futures.append(executor.submit(scrape_and_save_to_txt, reddit, subreddit_name, filename, limit, delay))
                elif file_type == 'csv':
                    futures.append(executor.submit(scrape_and_save_to_csv, reddit, subreddit_name, filename, limit, delay))
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"Error in parallel scraping: {e}")

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Scraping completed in {elapsed_time:.2f} seconds.")
