import json
import pandas as pd
from datetime import datetime, timedelta
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import re
import sys

# Ticker extraction function (adapted from src/ticker_extraction.py)
def extract_tickers_from_text(text, valid_tickers):
    """Extract and validate tickers from a single text message"""
    if not text or pd.isna(text):
        return []
    
    # Regex to match potential tickers (all caps, 1-4 characters)
    ticker_pattern = re.compile(r'\b[A-Z]{1,4}\b')
    potential_tickers = ticker_pattern.findall(str(text))
    
    # Validate tickers against NASDAQ list
    validated_tickers = [ticker for ticker in potential_tickers if ticker in valid_tickers]
    
    return validated_tickers

# Load NASDAQ tickers for validation
with open("nasdaq_tickers.json", "r") as file:
    nasdaq_tickers = set(json.load(file))

# Load Reddit-specific sentiment words
with open("reddit_sentiment_words.json", "r") as file:
    reddit_words = json.load(file)

# Initialize the sentiment analyzer
analyzer = SentimentIntensityAnalyzer()

def get_week_range(date_str):
    """Convert date to week range string (Monday to Sunday)"""
    date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    # Find Monday of that week
    monday = date - timedelta(days=date.weekday())
    sunday = monday + timedelta(days=6)
    return f"{monday.strftime('%Y-%m-%d')}/{sunday.strftime('%Y-%m-%d')}"

def calculate_message_sentiment(message, karma):
    """Calculate sentiment score for a message, including Reddit-specific words"""
    if pd.isna(message) or message == "":
        return 0
    
    # VADER sentiment analysis
    sentiment = analyzer.polarity_scores(str(message))
    vader_score = sentiment['compound']
    
    # Reddit-specific sentiment adjustment
    reddit_score = 0
    words = str(message).lower().split()
    for word in words:
        if word in reddit_words['positive']:
            reddit_score += 0.1
        elif word in reddit_words['negative']:
            reddit_score -= 0.1
    
    # Weight by karma (use log to prevent extreme values)
    karma_weight = max(1, abs(karma)) if not pd.isna(karma) else 1
    weighted_sentiment = (vader_score + reddit_score) * karma_weight
    
    return {
        'vader_sentiment': vader_score,
        'reddit_sentiment': reddit_score,
        'karma': karma_weight,
        'overall_sentiment': weighted_sentiment
    }

def process_csv_data():
    """Process the CSV data in chunks to handle large file"""
    print("Processing CSV data...")
    
    # Read CSV in chunks
    chunk_size = 10000
    weekly_data = {}
    
    for chunk in pd.read_csv("data.csv", chunksize=chunk_size):
        for _, row in chunk.iterrows():
            try:
                # Extract relevant fields
                datetime_str = row['datetime']
                text = row['text'] if not pd.isna(row['text']) else ""
                title = row['title'] if not pd.isna(row['title']) else ""
                karma = row['score'] if not pd.isna(row['score']) else 1
                
                # Combine title and text for analysis
                full_text = f"{title} {text}".strip()
                
                if not full_text:
                    continue
                
                # Get week range
                week_range = get_week_range(datetime_str)
                
                # Extract tickers from the text
                tickers = extract_tickers_from_text(full_text, nasdaq_tickers)
                
                if not tickers:
                    continue
                
                # Calculate sentiment
                sentiment_data = calculate_message_sentiment(full_text, karma)
                
                # Initialize week data if needed
                if week_range not in weekly_data:
                    weekly_data[week_range] = {}
                
                # Store data for each ticker mentioned
                for ticker in tickers:
                    if ticker not in weekly_data[week_range]:
                        weekly_data[week_range][ticker] = {
                            'count': 0,
                            'vader_scores': [],
                            'reddit_scores': [],
                            'karma_values': [],
                            'overall_scores': []
                        }
                    
                    weekly_data[week_range][ticker]['count'] += 1
                    weekly_data[week_range][ticker]['vader_scores'].append(sentiment_data['vader_sentiment'])
                    weekly_data[week_range][ticker]['reddit_scores'].append(sentiment_data['reddit_sentiment'])
                    weekly_data[week_range][ticker]['karma_values'].append(sentiment_data['karma'])
                    weekly_data[week_range][ticker]['overall_scores'].append(sentiment_data['overall_sentiment'])
                    
            except Exception as e:
                # Skip problematic rows
                continue
    
    return weekly_data

def calculate_final_metrics(weekly_data):
    """Calculate final aggregated metrics for each ticker per week"""
    final_results = {}
    
    for week_range, tickers in weekly_data.items():
        final_results[week_range] = {}
        
        for ticker, data in tickers.items():
            if data['count'] == 0:
                continue
                
            # Calculate averages
            avg_vader = sum(data['vader_scores']) / len(data['vader_scores'])
            avg_reddit = sum(data['reddit_scores']) / len(data['reddit_scores'])
            avg_karma = sum(data['karma_values']) / len(data['karma_values'])
            avg_overall = sum(data['overall_scores']) / len(data['overall_scores'])
            
            final_results[week_range][ticker] = {
                'ticker_count': data['count'],
                'avg_vader_sentiment': round(avg_vader, 4),
                'avg_reddit_sentiment': round(avg_reddit, 4),
                'avg_karma': round(avg_karma, 2),
                'overall_sentiment_score': round(avg_overall, 4),
                'total_mentions': data['count']
            }
    
    return final_results

# Main execution
if __name__ == "__main__":
    print("Starting comprehensive sentiment analysis...")
    
    # Process the CSV data
    weekly_data = process_csv_data()
    
    # Calculate final metrics
    final_results = calculate_final_metrics(weekly_data)
    
    # Save the comprehensive sentiment data
    with open("weekly_sentiment.json", "w") as file:
        json.dump(final_results, file, indent=4)
    
    print(f"Comprehensive sentiment analysis completed!")
    print(f"Processed {len(final_results)} weeks of data")
    
    # Print summary statistics
    total_tickers = sum(len(week_data) for week_data in final_results.values())
    print(f"Total ticker-week combinations: {total_tickers}")
    
    if final_results:
        sample_week = list(final_results.keys())[0]
        sample_ticker = list(final_results[sample_week].keys())[0] if final_results[sample_week] else None
        if sample_ticker:
            print(f"Sample data structure for {sample_ticker} in {sample_week}:")
            print(json.dumps(final_results[sample_week][sample_ticker], indent=2))
    
    print("Results saved to weekly_sentiment.json")
