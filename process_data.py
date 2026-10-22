import pandas as pd
import json
from collections import defaultdict
from datetime import datetime
from ticker_extraction import extract_tickers

def process_data(file_path, valid_tickers):
    """
    Process the data.csv file to count ticker occurrences weekly.

    Args:
        file_path (str): Path to the data.csv file.
        valid_tickers (set): Set of valid NASDAQ tickers.

    Returns:
        dict: Weekly ticker counts.
    """
    # Initialize a dictionary to store weekly counts
    weekly_counts = defaultdict(lambda: defaultdict(int))

    # Read the CSV file in chunks
    chunks = pd.read_csv(file_path, chunksize=10000)

    for chunk in chunks:
        # Ensure the chunk has the necessary columns
        if 'datetime' not in chunk.columns or 'text' not in chunk.columns:
            raise ValueError("The CSV file must contain 'datetime' and 'text' columns.")

        # Convert datetime column to datetime
        chunk['datetime'] = pd.to_datetime(chunk['datetime'])

        # Group messages by week
        chunk['week'] = chunk['datetime'].dt.to_period('W').astype(str)

        # Process each week
        for week, group in chunk.groupby('week'):
            # Ensure text column has no missing or non-string values
            group['text'] = group['text'].fillna('').astype(str)

            messages = group['text'].tolist()
            ticker_counts = extract_tickers(messages, valid_tickers)

            # Update weekly counts
            for ticker, count in ticker_counts.items():
                weekly_counts[week][ticker] += count

    return weekly_counts

if __name__ == "__main__":
    # Load NASDAQ tickers
    with open("nasdaq_tickers.json", "r") as f:
        nasdaq_tickers = set(json.load(f))

    # Path to the data.csv file
    file_path = "data.csv"

    # Process the data
    try:
        weekly_ticker_counts = process_data(file_path, nasdaq_tickers)

        # Print results
        for week, counts in weekly_ticker_counts.items():
            print(f"Week: {week}")
            for ticker, count in counts.items():
                print(f"  {ticker}: {count}")
        
        # Save results to a JSON file
        with open("weekly_ticker_counts.json", "w") as outfile:
            json.dump(weekly_ticker_counts, outfile, indent=4)
    except Exception as e:
        print("Error processing data:", e)
