import re
import json
from collections import Counter

def extract_tickers(messages, valid_tickers):
    """
    Extract potential tickers from messages and validate them.

    Args:
        messages (list of str): List of messages to process.
        valid_tickers (set): Set of valid NASDAQ tickers.

    Returns:
        dict: Validated tickers with their occurrence counts.
    """
    # Regex to match potential tickers (all caps, 1-4 characters)
    ticker_pattern = re.compile(r'\b[A-Z]{1,4}\b')

    # Extract potential tickers
    potential_tickers = []
    for message in messages:
        potential_tickers.extend(ticker_pattern.findall(message))

    # Validate tickers
    validated_tickers = [ticker for ticker in potential_tickers if ticker in valid_tickers]

    # Count occurrences
    ticker_counts = Counter(validated_tickers)

    return dict(ticker_counts)

if __name__ == "__main__":
    # Load NASDAQ tickers
    with open("../nasdaq_tickers.json", "r") as f:
        nasdaq_tickers = set(json.load(f))

    # Example messages (replace with actual data loading logic)
    messages = [
        "AAPL is doing great!",
        "TSLA to the moon!",
        "I think MSFT is a good buy.",
        "Random text without tickers."
    ]

    # Extract and validate tickers
    ticker_counts = extract_tickers(messages, nasdaq_tickers)

    # Print results
    print("Validated Tickers:", ticker_counts)
