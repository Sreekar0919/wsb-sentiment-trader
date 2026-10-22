import json
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

class MomentumTracker:
    def __init__(self, sentiment_file="weekly_sentiment.json"):
        """Initialize momentum tracker with sentiment data"""
        with open(sentiment_file, 'r') as f:
            self.sentiment_data = json.load(f)
        
        self.price_data = {}
        self.momentum_data = {}
        
    def get_unique_tickers(self):
        """Extract all unique tickers from sentiment data"""
        tickers = set()
        for week_data in self.sentiment_data.values():
            tickers.update(week_data.keys())
        return sorted(list(tickers))
    
    def get_date_range(self):
        """Get the overall date range from sentiment data"""
        weeks = sorted(self.sentiment_data.keys())
        start_date = datetime.strptime(weeks[0].split('/')[0], '%Y-%m-%d')
        end_date = datetime.strptime(weeks[-1].split('/')[1], '%Y-%m-%d')
        
        # Add buffer for momentum calculation
        start_date = start_date - timedelta(days=10)
        end_date = end_date + timedelta(days=10)
        
        return start_date, end_date
    
    def fetch_ticker_data(self, ticker, start_date, end_date, max_retries=3):
        """Fetch price data for a single ticker with retry logic"""
        for attempt in range(max_retries):
            try:
                stock = yf.Ticker(ticker)
                data = stock.history(start=start_date, end=end_date)
                
                if data.empty:
                    print(f"No data found for {ticker}")
                    return ticker, None
                
                # Keep only essential columns
                price_data = data[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
                price_data.index = price_data.index.date  # Convert to date only
                
                return ticker, price_data
                
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"Attempt {attempt + 1} failed for {ticker}: {e}. Retrying...")
                    time.sleep(1)  # Brief pause before retry
                else:
                    print(f"Failed to fetch data for {ticker} after {max_retries} attempts: {e}")
                    return ticker, None
    
    def fetch_all_price_data(self, max_workers=10):
        """Fetch price data for all tickers using parallel processing"""
        tickers = self.get_unique_tickers()
        start_date, end_date = self.get_date_range()
        
        print(f"Fetching price data for {len(tickers)} tickers from {start_date.date()} to {end_date.date()}")
        
        # Use ThreadPoolExecutor for parallel API calls
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_ticker = {
                executor.submit(self.fetch_ticker_data, ticker, start_date, end_date): ticker 
                for ticker in tickers
            }
            
            # Collect results
            completed = 0
            for future in as_completed(future_to_ticker):
                ticker, data = future.result()
                if data is not None:
                    self.price_data[ticker] = data
                
                completed += 1
                if completed % 50 == 0:
                    print(f"Completed {completed}/{len(tickers)} tickers")
        
        print(f"Successfully fetched data for {len(self.price_data)} out of {len(tickers)} tickers")
    
    def calculate_3day_momentum(self, prices):
        """Calculate 3-day price momentum"""
        if len(prices) < 4:  # Need at least 4 days for 3-day momentum
            return pd.Series(index=prices.index, dtype=float)
        
        # 3-day momentum = (current_price - price_3_days_ago) / price_3_days_ago
        momentum = (prices - prices.shift(3)) / prices.shift(3)
        return momentum
    
    def calculate_all_momentum(self):
        """Calculate momentum for all tickers"""
        print("Calculating 3-day momentum for all tickers...")
        
        for ticker, price_data in self.price_data.items():
            # Calculate momentum using closing prices
            momentum = self.calculate_3day_momentum(price_data['Close'])
            
            # Store momentum data with additional metrics
            self.momentum_data[ticker] = {
                'momentum': momentum,
                'prices': price_data['Close'],
                'volume': price_data['Volume'],
                'volatility': price_data['Close'].pct_change().rolling(window=5).std()
            }
    
    def get_momentum_for_week(self, week_range, ticker):
        """Get momentum data for a specific week and ticker"""
        if ticker not in self.momentum_data:
            return None
        
        # Parse week range
        start_date = datetime.strptime(week_range.split('/')[0], '%Y-%m-%d').date()
        end_date = datetime.strptime(week_range.split('/')[1], '%Y-%m-%d').date()
        
        # Get momentum data for the week
        momentum_series = self.momentum_data[ticker]['momentum']
        week_momentum = momentum_series[
            (momentum_series.index >= start_date) & 
            (momentum_series.index <= end_date)
        ]
        
        if week_momentum.empty:
            return None
        
        # Return average momentum for the week
        return {
            'avg_momentum': week_momentum.mean(),
            'momentum_values': week_momentum.tolist(),
            'momentum_dates': [str(date) for date in week_momentum.index],
            'start_price': self.momentum_data[ticker]['prices'].get(start_date),
            'end_price': self.momentum_data[ticker]['prices'].get(end_date),
            'avg_volume': self.momentum_data[ticker]['volume'][
                (self.momentum_data[ticker]['volume'].index >= start_date) & 
                (self.momentum_data[ticker]['volume'].index <= end_date)
            ].mean() if ticker in self.momentum_data else None
        }
    
    def create_combined_data(self):
        """Combine sentiment and momentum data"""
        print("Combining sentiment and momentum data...")
        
        combined_data = {}
        
        for week_range, week_sentiment in self.sentiment_data.items():
            combined_data[week_range] = {}
            
            for ticker, sentiment_info in week_sentiment.items():
                momentum_info = self.get_momentum_for_week(week_range, ticker)
                
                # Combine sentiment and momentum data
                combined_data[week_range][ticker] = {
                    # Sentiment data
                    'ticker_count': sentiment_info['ticker_count'],
                    'avg_vader_sentiment': sentiment_info['avg_vader_sentiment'],
                    'avg_reddit_sentiment': sentiment_info['avg_reddit_sentiment'],
                    'avg_karma': sentiment_info['avg_karma'],
                    'overall_sentiment_score': sentiment_info['overall_sentiment_score'],
                    'total_mentions': sentiment_info['total_mentions'],
                    
                    # Momentum data
                    'avg_3day_momentum': momentum_info['avg_momentum'] if momentum_info else None,
                    'momentum_values': momentum_info['momentum_values'] if momentum_info else [],
                    'start_price': momentum_info['start_price'] if momentum_info else None,
                    'end_price': momentum_info['end_price'] if momentum_info else None,
                    'avg_volume': momentum_info['avg_volume'] if momentum_info else None,
                    
                    # Combined score (you can adjust this formula)
                    'combined_score': self.calculate_combined_score(sentiment_info, momentum_info)
                }
        
        return combined_data
    
    def calculate_combined_score(self, sentiment_info, momentum_info):
        """Calculate a combined sentiment-momentum score"""
        if momentum_info is None or pd.isna(momentum_info['avg_momentum']):
            return sentiment_info['overall_sentiment_score']
        
        # Simple combination: sentiment score + momentum weight
        sentiment_score = sentiment_info['overall_sentiment_score']
        momentum_score = momentum_info['avg_momentum'] * 1000  # Scale momentum
        
        # Weight them (you can adjust these weights)
        combined = 0.7 * sentiment_score + 0.3 * momentum_score
        return round(combined, 4)
    
    def save_data(self, filename="weekly_sentiment_momentum.json"):
        """Save combined data to JSON file"""
        combined_data = self.create_combined_data()
        
        with open(filename, 'w') as f:
            json.dump(combined_data, f, indent=4, default=str)
        
        print(f"Combined sentiment and momentum data saved to {filename}")
        return combined_data
    
    def get_summary_stats(self):
        """Get summary statistics"""
        tickers_with_price_data = len(self.price_data)
        total_tickers = len(self.get_unique_tickers())
        
        print(f"\n=== MOMENTUM TRACKING SUMMARY ===")
        print(f"Total unique tickers: {total_tickers}")
        print(f"Tickers with price data: {tickers_with_price_data}")
        print(f"Success rate: {tickers_with_price_data/total_tickers*100:.1f}%")
        
        if self.momentum_data:
            # Sample momentum statistics
            sample_ticker = list(self.momentum_data.keys())[0]
            sample_momentum = self.momentum_data[sample_ticker]['momentum'].dropna()
            
            print(f"\nSample momentum stats for {sample_ticker}:")
            print(f"  Mean 3-day momentum: {sample_momentum.mean():.4f}")
            print(f"  Std 3-day momentum: {sample_momentum.std():.4f}")
            print(f"  Data points: {len(sample_momentum)}")

def main():
    """Main execution function"""
    print("Starting momentum tracking analysis...")
    
    # Initialize tracker
    tracker = MomentumTracker()
    
    # Fetch price data
    tracker.fetch_all_price_data()
    
    # Calculate momentum
    tracker.calculate_all_momentum()
    
    # Save combined data
    combined_data = tracker.save_data()
    
    # Print summary
    tracker.get_summary_stats()
    
    return tracker, combined_data

if __name__ == "__main__":
    tracker, combined_data = main()