import pandas as pd
import re
from config import CSV_DIR
from nltk.corpus import stopwords
import nltk

# Ensure nltk stop words are downloaded
nltk.download('stopwords')

# Load stop words
stop_words = set(stopwords.words('english'))
my_words = ['subreddit','make', 'using', 'scammers', 'dont', 'scam',  'said','automoderator','youre','like','know', 'advice', 'think', 'got', 'need', 'im', 'lol', 'shit', 'thats', 'moderators' ]

# Set the file path using CSV_DIR
file_path = CSV_DIR + 'privacy.csv'
reddit_data = pd.read_csv(file_path)

# Drop any columns containing URLs, if applicable
if 'url' in reddit_data.columns:
    reddit_data.drop(columns=['url'], inplace=True)


automated_message_text = [
    "New users beware:",
    "I am a bot, and this action was performed automatically."
    ]

# Function to clean, filter patterns, and remove stop words from the comments field
def clean_comment_text(comment_text):
    # Convert non-string entries to an empty string
    if not isinstance(comment_text, str):
        comment_text = ''

    

    # Convert to lowercase
    comment_text = comment_text.lower()
    # Remove URLs within the text
    comment_text = re.sub(r'http\S+|www\S+', '', comment_text)
    # Remove formatting text like "Author:", "Score:", "Posted:"
    comment_text = re.sub(r'\b(author|score|posted):', '', comment_text, flags=re.IGNORECASE)
    # Remove numbers
    comment_text = re.sub(r'\d+', '', comment_text)
    # Remove symbols (keep only alphabets and spaces)
    comment_text = re.sub(r'[^a-z\s]', '', comment_text)
    # Remove stop words
    filtered_words = [word for word in comment_text.split() if word not in stop_words]
    # Remove custom words
    filtered_words = [word for word in filtered_words if word not in my_words]
    # Join the filtered words back into a cleaned comment text
    cleaned_text = ' '.join(filtered_words)
    for phrase in automated_message_text:
        if phrase.lower() in cleaned_text:
            return ''  # Return an empty string if the automated message is detected

    return cleaned_text
# Apply the function to the 'comments' column
reddit_data['comments'] = reddit_data['comments'].apply(clean_comment_text)

# Save the cleaned data to a new file
filtered_file_path = CSV_DIR + 'privacy_comments.csv'
reddit_data.to_csv(filtered_file_path, index=False)

print("Final filtered data saved to:", filtered_file_path)
