import re
from collections import Counter
from config import PATH, DIRECTORY, FILENAME
import os

with open(PATH, 'r', encoding='utf-8') as f:
    text_data = f.read()

# load keywords
with open('vr_security_privacy_terms.txt', 'r') as f:
    keywords = f.read().splitlines()

def preprocess_text(text):
    return text.lower()

def is_abbreviation(keyword):
    return keyword.isupper() or len(keyword) <= 4

# count keyword occurrences exactly like CTRL+F would
def count_keywords(text, keywords):
    keyword_counter = Counter()
    
    for keyword in keywords:
        
        keyword_lower = keyword.lower()
        
        if is_abbreviation(keyword):
            # word boundaries (\b) for abbreviations
            keyword_pattern = rf'\b{re.escape(keyword_lower)}\b'
        else:
            keyword_pattern = rf'{re.escape(keyword_lower)}'

        matches = re.findall(keyword_pattern, text)
        keyword_counter[keyword] = len(matches)  # number of matches
    
    return keyword_counter

processed_text = preprocess_text(text_data)

keyword_counter = count_keywords(processed_text, keywords)

sorted_keyword_counter = sorted(keyword_counter.items(), key=lambda x: x[1], reverse=True)

print("Keyword Frequencies:")
for i, (keyword, frequency) in enumerate(sorted_keyword_counter, 1):
    print(f"{i}. {keyword}: {frequency}")


os.makedirs(DIRECTORY, exist_ok=True)
full_txt_filename = os.path.join(DIRECTORY, FILENAME + '.txt',)

with open(full_txt_filename, 'w') as f:
    for i, (keyword, frequency) in enumerate(sorted_keyword_counter, 1):
        f.write(f"{i}. {keyword}: {frequency}\n")
