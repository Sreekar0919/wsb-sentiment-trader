"""
Daily Trading Engine
Modified version that trades every day instead of weekly
"""

import json
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
from collections import defaultdict
import yfinance as yf

class DailyTradingEngine:
    def __init__(self, initial_capital=10000, data_file="weekly_sentiment_momentum.json"):
        """Initialize daily trading engine with starting capital and data"""
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.cash = initial_capital
        self.positions = {}  # {ticker: {'shares': int, 'avg_price': float, 'value': float}}
        self.portfolio_history = []
        self.trade_history = []
        
        # Load sentiment and momentum data (weekly data, but we'll interpolate daily)
        with open(data_file, 'r') as f:
            self.weekly_data = json.load(f)
        
        # Convert weekly data to daily data
        self.daily_data = self._convert_to_daily()
        
        # Price cache to avoid repeated failed requests
        self.price_cache = {}  # {ticker: price}
        self.failed_tickers = set()  # Track tickers with no data
        
        # Trading parameters
        self.max_position_size = 0.05  # Max 5% of portfolio per position
        self.min_trade_amount = 100    # Minimum trade amount
        self.transaction_cost = 0.001  # 0.1% per trade
        
        # Strategy parameters
        self.sentiment_threshold = 10.0    # Minimum sentiment score for buy
        self.momentum_threshold = 0.02     # Minimum 2% momentum for buy
        self.combined_score_threshold = 15.0  # Minimum combined score
        self.max_positions = 20            # Maximum number of positions
        
        print(f"Daily Trading Engine initialized with ${initial_capital:,.2f}")
        print(f"Total trading days: {len(self.daily_data)}")
    
    def _convert_to_daily(self):
        """Convert weekly data to daily data by interpolating"""
        
        print("Converting weekly data to daily data...")
        
        daily_data = {}
        
        for week_range, tickers in self.weekly_data.items():
            # Parse week range
            start_date = datetime.strptime(week_range.split('/')[0], '%Y-%m-%d')
            end_date = datetime.strptime(week_range.split('/')[1], '%Y-%m-%d')
            
            # Generate all days in this week
            current_date = start_date
            while current_date <= end_date:
                date_str = current_date.strftime('%Y-%m-%d')
                
                # Use same data for all days in the week
                daily_data[date_str] = tickers
                
                current_date += timedelta(days=1)
        
        return daily_data
    
    def get_sorted_days(self):
        """Get all trading days sorted chronologically"""
        return sorted(self.daily_data.keys())
    
    def get_current_portfolio_value(self, date_str):
        """Calculate current portfolio value including positions"""
        total_value = self.cash
        
        for ticker, position in self.positions.items():
            # Get current price for the ticker on this date
            current_price = self.get_ticker_price(ticker, date_str)
            if current_price:
                position_value = position['shares'] * current_price
                total_value += position_value
                # Update position value
                self.positions[ticker]['value'] = position_value
        
        return total_value
    
    def get_ticker_price(self, ticker, date_str):
        """Get ticker price for a specific date with caching"""
        # Skip if ticker is known to have no data
        if ticker in self.failed_tickers:
            return None
        
        # Check cache first
        cache_key = f"{ticker}_{date_str}"
        if cache_key in self.price_cache:
            return self.price_cache[cache_key]
        
        price = None
        
        # Try to get price from daily data
        if date_str in self.daily_data and ticker in self.daily_data[date_str]:
            ticker_data = self.daily_data[date_str][ticker]
            if ticker_data.get('start_price') and ticker_data.get('start_price') > 0:
                price = ticker_data['start_price']
        
        # Fallback: try to get price from yfinance with extended date range
        if price is None:
            try:
                date = datetime.strptime(date_str, '%Y-%m-%d')
                stock = yf.Ticker(ticker)
                
                # Try to get data for the specific date
                hist = stock.history(start=date, end=date + timedelta(days=1))
                if not hist.empty:
                    price = hist['Close'].iloc[0]
                
                # If no data for that day, try nearby days (up to 5 days forward)
                if price is None:
                    for days_offset in range(1, 6):
                        future_date = date + timedelta(days=days_offset)
                        hist = stock.history(start=future_date, end=future_date + timedelta(days=1))
                        if not hist.empty:
                            price = hist['Close'].iloc[0]
                            break
                
                # If still no data, try looking backwards
                if price is None:
                    for days_offset in range(1, 6):
                        past_date = date - timedelta(days=days_offset)
                        hist = stock.history(start=past_date, end=past_date + timedelta(days=1))
                        if not hist.empty:
                            price = hist['Close'].iloc[0]
                            break
                            
            except Exception as e:
                # Mark ticker as failed to avoid repeated requests
                self.failed_tickers.add(ticker)
        
        # Cache the result
        if price is not None:
            self.price_cache[cache_key] = price
        else:
            # Mark as failed
            self.failed_tickers.add(ticker)
        
        return price
    
    def calculate_position_size(self, ticker, price, score):
        """Calculate position size based on score and risk management"""
        portfolio_value = self.get_current_portfolio_value(self.current_date)
        
        # Base position size (percentage of portfolio)
        base_size = min(self.max_position_size, score / 1000.0)
        base_size = max(0.01, base_size)
        
        # Calculate dollar amount
        dollar_amount = portfolio_value * base_size
        
        # Ensure minimum trade amount
        dollar_amount = max(dollar_amount, self.min_trade_amount)
        
        # Don't exceed available cash
        dollar_amount = min(dollar_amount, self.cash * 0.9)
        
        # Calculate shares
        shares = int(dollar_amount / price)
        
        return shares, dollar_amount
    
    def should_buy(self, ticker, ticker_data):
        """Determine if we should buy a ticker based on strategy"""
        # Check if we already have this position
        if ticker in self.positions:
            return False
        
        # Check if we've reached max positions
        if len(self.positions) >= self.max_positions:
            return False
        
        # Get metrics
        sentiment_score = ticker_data.get('overall_sentiment_score', 0)
        momentum = ticker_data.get('avg_3day_momentum')
        combined_score = ticker_data.get('combined_score', 0)
        mentions = ticker_data.get('ticker_count', 0)
        start_price = ticker_data.get('start_price')
        
        # Skip if no valid price data
        if start_price is None or start_price <= 0:
            return False
        
        # Buy criteria
        buy_conditions = [
            sentiment_score > self.sentiment_threshold,
            momentum is not None and momentum > self.momentum_threshold,
            combined_score > self.combined_score_threshold,
            mentions >= 5
        ]
        
        return all(buy_conditions)
    
    def should_sell(self, ticker, ticker_data, current_price):
        """Determine if we should sell a position"""
        if ticker not in self.positions:
            return False
        
        position = self.positions[ticker]
        current_return = (current_price - position['avg_price']) / position['avg_price']
        
        # Get current metrics
        sentiment_score = ticker_data.get('overall_sentiment_score', 0)
        momentum = ticker_data.get('avg_3day_momentum')
        combined_score = ticker_data.get('combined_score', 0)
        
        # Sell criteria
        sell_conditions = [
            current_return < -0.10,  # Stop loss at -10%
            current_return > 0.25,   # Take profit at +25%
            sentiment_score < -10,   # Very negative sentiment
            momentum is not None and momentum < -0.05,  # Strong negative momentum
            combined_score < -20     # Very negative combined score
        ]
        
        return any(sell_conditions)
    
    def execute_buy(self, ticker, price, shares, date_str):
        """Execute a buy order"""
        if shares <= 0:
            return False
        
        total_cost = shares * price
        transaction_cost = total_cost * self.transaction_cost
        total_with_fees = total_cost + transaction_cost
        
        if total_with_fees > self.cash:
            return False
        
        # Execute trade
        self.cash -= total_with_fees
        self.positions[ticker] = {
            'shares': shares,
            'avg_price': price,
            'value': total_cost,
            'purchase_date': date_str
        }
        
        # Record trade
        self.trade_history.append({
            'date': date_str,
            'ticker': ticker,
            'action': 'BUY',
            'shares': shares,
            'price': price,
            'total_cost': total_cost,
            'fees': transaction_cost,
            'cash_after': self.cash
        })
        
        return True
    
    def execute_sell(self, ticker, price, date_str):
        """Execute a sell order"""
        if ticker not in self.positions:
            return False
        
        position = self.positions[ticker]
        shares = position['shares']
        total_proceeds = shares * price
        transaction_cost = total_proceeds * self.transaction_cost
        net_proceeds = total_proceeds - transaction_cost
        
        # Calculate P&L
        purchase_cost = shares * position['avg_price']
        pnl = net_proceeds - purchase_cost
        pnl_percent = (price - position['avg_price']) / position['avg_price']
        
        # Execute trade
        self.cash += net_proceeds
        del self.positions[ticker]
        
        # Record trade
        self.trade_history.append({
            'date': date_str,
            'ticker': ticker,
            'action': 'SELL',
            'shares': shares,
            'price': price,
            'total_proceeds': total_proceeds,
            'fees': transaction_cost,
            'pnl': pnl,
            'pnl_percent': pnl_percent,
            'cash_after': self.cash
        })
        
        return True
    
    def process_day(self, date_str):
        """Process trading decisions for a single day"""
        self.current_date = date_str
        
        if date_str not in self.daily_data:
            return
        
        day_data = self.daily_data[date_str]
        
        # First, check for sells
        tickers_to_sell = []
        for ticker in list(self.positions.keys()):
            if ticker in day_data:
                ticker_data = day_data[ticker]
                current_price = self.get_ticker_price(ticker, date_str)
                
                if current_price and self.should_sell(ticker, ticker_data, current_price):
                    tickers_to_sell.append((ticker, current_price))
        
        # Execute sells
        for ticker, price in tickers_to_sell:
            self.execute_sell(ticker, price, date_str)
        
        # Then, look for buys
        buy_candidates = []
        for ticker, ticker_data in day_data.items():
            if self.should_buy(ticker, ticker_data):
                price = self.get_ticker_price(ticker, date_str)
                if price:
                    combined_score = ticker_data.get('combined_score', 0)
                    buy_candidates.append((ticker, ticker_data, price, combined_score))
        
        # Sort by combined score (best first)
        buy_candidates.sort(key=lambda x: x[3], reverse=True)
        
        # Execute buys
        for ticker, ticker_data, price, score in buy_candidates:
            if len(self.positions) >= self.max_positions:
                break
            
            shares, dollar_amount = self.calculate_position_size(ticker, price, score)
            if shares > 0 and dollar_amount <= self.cash:
                self.execute_buy(ticker, price, shares, date_str)
        
        # Record portfolio state
        portfolio_value = self.get_current_portfolio_value(date_str)
        self.portfolio_history.append({
            'date': date_str,
            'cash': self.cash,
            'positions_value': portfolio_value - self.cash,
            'total_value': portfolio_value,
            'num_positions': len(self.positions),
            'return': (portfolio_value - self.initial_capital) / self.initial_capital
        })
    
    def run_backtest(self):
        """Run the complete backtesting simulation"""
        print("Starting daily backtesting simulation...")
        
        days = self.get_sorted_days()
        print(f"Processing {len(days)} trading days from {days[0]} to {days[-1]}")
        
        for i, date_str in enumerate(days):
            self.process_day(date_str)
            
            # Print progress every 50 days
            if (i + 1) % 50 == 0:
                current_value = self.portfolio_history[-1]['total_value']
                current_return = self.portfolio_history[-1]['return']
                print(f"Progress: {i+1}/{len(days)} days | Return: {current_return:.1%}")
        
        print("\nDaily backtesting completed!")
        self.print_final_results()
    
    def print_final_results(self):
        """Print final backtesting results"""
        if not self.portfolio_history:
            print("No trading history available")
            return
        
        final_value = self.portfolio_history[-1]['total_value']
        total_return = (final_value - self.initial_capital) / self.initial_capital
        
        print(f"\n{'='*50}")
        print(f"DAILY TRADING BACKTEST RESULTS")
        print(f"{'='*50}")
        print(f"Initial Capital: ${self.initial_capital:,.2f}")
        print(f"Final Value: ${final_value:,.2f}")
        print(f"Total Return: {total_return:.2%}")
        print(f"Total Trades: {len(self.trade_history)}")
        
        # Calculate additional metrics
        returns = [h['return'] for h in self.portfolio_history]
        if len(returns) > 1:
            daily_returns = np.diff(returns)
            sharpe_ratio = np.mean(daily_returns) / np.std(daily_returns) * np.sqrt(252) if np.std(daily_returns) > 0 else 0
            max_drawdown = self.calculate_max_drawdown()
            
            print(f"Sharpe Ratio: {sharpe_ratio:.2f}")
            print(f"Max Drawdown: {max_drawdown:.2%}")
        
        # Trade statistics
        buy_trades = [t for t in self.trade_history if t['action'] == 'BUY']
        sell_trades = [t for t in self.trade_history if t['action'] == 'SELL']
        
        print(f"Buy Trades: {len(buy_trades)}")
        print(f"Sell Trades: {len(sell_trades)}")
        
        if sell_trades:
            winning_trades = [t for t in sell_trades if t['pnl'] > 0]
            losing_trades = [t for t in sell_trades if t['pnl'] <= 0]
            
            print(f"Winning Trades: {len(winning_trades)} ({len(winning_trades)/len(sell_trades):.1%})")
            print(f"Losing Trades: {len(losing_trades)} ({len(losing_trades)/len(sell_trades):.1%})")
            
            if winning_trades:
                avg_win = np.mean([t['pnl_percent'] for t in winning_trades])
                print(f"Average Win: {avg_win:.1%}")
            
            if losing_trades:
                avg_loss = np.mean([t['pnl_percent'] for t in losing_trades])
                print(f"Average Loss: {avg_loss:.1%}")
    
    def calculate_max_drawdown(self):
        """Calculate maximum drawdown"""
        values = [h['total_value'] for h in self.portfolio_history]
        peak = values[0]
        max_dd = 0
        
        for value in values:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak
            max_dd = max(max_dd, drawdown)
        
        return max_dd
    
    def save_results(self, filename="daily_backtest_results.json"):
        """Save backtesting results to file"""
        results = {
            'initial_capital': self.initial_capital,
            'final_value': self.portfolio_history[-1]['total_value'] if self.portfolio_history else self.initial_capital,
            'total_return': self.portfolio_history[-1]['return'] if self.portfolio_history else 0,
            'trading_frequency': 'daily',
            'portfolio_history': self.portfolio_history,
            'trade_history': self.trade_history,
            'strategy_parameters': {
                'sentiment_threshold': self.sentiment_threshold,
                'momentum_threshold': self.momentum_threshold,
                'combined_score_threshold': self.combined_score_threshold,
                'max_positions': self.max_positions,
                'max_position_size': self.max_position_size,
                'transaction_cost': self.transaction_cost
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=4, default=str)
        
        print(f"Results saved to {filename}")

def main():
    """Main execution function"""
    print("Initializing Daily Trading Engine...")
    
    # Create trading engine
    engine = DailyTradingEngine(initial_capital=10000)
    
    # Run backtest
    engine.run_backtest()
    
    # Save results
    engine.save_results()
    
    return engine

if __name__ == "__main__":
    engine = main()
