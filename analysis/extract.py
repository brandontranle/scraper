import pandas as pd

def extract_terms(input_csv, output_txt):
    # Load the CSV file
    data = pd.read_csv(input_csv)

    # Check if 'Term' column exists
    if 'Term' not in data.columns:
        print("The CSV file does not contain a 'Term' column.")
        return

    # Extract the 'Term' column and save it to a .txt file
    terms = data['Term']
    terms.to_csv(output_txt, index=False, header=False)
    print(f"Terms successfully saved to {output_txt}")

# Usage
extract_terms('niccs--cybersecurity-vocabulary--2024Nov08.csv', 'cybersecurity_terms.txt')
