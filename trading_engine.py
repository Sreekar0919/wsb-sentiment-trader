import json
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
from collections import defaultdict
import yfinance as yf

class TradingEngine:
    def __init__(self, initial_capital=10000, data_file="weekly_sentiment_momentum.json"):
        """Initialize trading engine with starting capital and data"""
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.cash = initial_capital
        self.positions = {}  # {ticker: {'shares': int, 'avg_price': float, 'value': float}}
        self.portfolio_history = []
        self.trade_history = []
        
        # Load sentiment and momentum data
        with open(data_file, 'r') as f:
            self.data = json.load(f)
        
        # Trading parameters
        self.max_position_size = 0.05  # Max 5% of portfolio per position
        self.min_trade_amount = 100    # Minimum trade amount
        self.transaction_cost = 0.00
        
        # Strategy parameters
        self.sentiment_threshold = 10.0    # Minimum sentiment score for buy
        self.momentum_threshold = 0.02     # Minimum 2% momentum for buy
        self.combined_score_threshold = 15.0  # Minimum combined score
        self.max_positions = 20            # Maximum number of positions
        
        print(f"Trading Engine initialized with ${initial_capital:,.2f}")
    
    def get_sorted_weeks(self):
        """Get weeks sorted chronologically"""
        return sorted(self.data.keys(), key=lambda x: datetime.strptime(x.split('/')[0], '%Y-%m-%d'))
    
    def get_current_portfolio_value(self, week_range):
        """Calculate current portfolio value including positions"""
        total_value = self.cash
        
        for ticker, position in self.positions.items():
            # Get current price for the ticker in this week
            current_price = self.get_ticker_price(ticker, week_range)
            if current_price:
                position_value = position['shares'] * current_price
                total_value += position_value
                # Update position value
                self.positions[ticker]['value'] = position_value
        
        return total_value
    
    def get_ticker_price(self, ticker, week_range):
        """Get ticker price for a specific week"""
        if week_range in self.data and ticker in self.data[week_range]:
            ticker_data = self.data[week_range][ticker]
            # Use start_price if available, otherwise try to fetch current price
            if ticker_data.get('start_price'):
                return ticker_data['start_price']
        
        # Fallback: try to get price from yfinance
        try:
            start_date = datetime.strptime(week_range.split('/')[0], '%Y-%m-%d')
            stock = yf.Ticker(ticker)
            hist = stock.history(start=start_date, end=start_date + timedelta(days=7))
            if not hist.empty:
                return hist['Close'].iloc[0]
        except:
            pass
        
        return None
    
    def calculate_position_size(self, ticker, price, score):
        """Calculate position size based on score and risk management"""
        portfolio_value = self.get_current_portfolio_value(self.current_week)
        
        # Base position size (percentage of portfolio)
        base_size = min(self.max_position_size, score / 1000.0)  # Scale score to percentage
        base_size = max(0.01, base_size)  # Minimum 1%
        
        # Calculate dollar amount
        dollar_amount = portfolio_value * base_size
        
        # Ensure minimum trade amount
        dollar_amount = max(dollar_amount, self.min_trade_amount)
        
        # Don't exceed available cash
        dollar_amount = min(dollar_amount, self.cash * 0.9)  # Keep 10% cash buffer
        
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
        
        # Buy criteria
        buy_conditions = [
            sentiment_score > self.sentiment_threshold,
            momentum is not None and momentum > self.momentum_threshold,
            combined_score > self.combined_score_threshold,
            mentions >= 5,  # At least 5 mentions
            ticker_data.get('start_price') is not None  # Must have price data
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
    
    def execute_buy(self, ticker, price, shares, week_range):
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
            'purchase_date': week_range
        }
        
        # Record trade
        self.trade_history.append({
            'date': week_range,
            'ticker': ticker,
            'action': 'BUY',
            'shares': shares,
            'price': price,
            'total_cost': total_cost,
            'fees': transaction_cost,
            'cash_after': self.cash
        })
        
        print(f"BUY: {shares} shares of {ticker} at ${price:.2f} (Total: ${total_cost:.2f})")
        return True
    
    def execute_sell(self, ticker, price, week_range):
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
            'date': week_range,
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
        
        print(f"SELL: {shares} shares of {ticker} at ${price:.2f} (P&L: ${pnl:.2f}, {pnl_percent:.1%})")
        return True
    
    def process_week(self, week_range):
        """Process trading decisions for a single week"""
        self.current_week = week_range
        week_data = self.data[week_range]
        
        print(f"\n=== Processing Week: {week_range} ===")
        
        # First, check for sells
        tickers_to_sell = []
        for ticker in self.positions.keys():
            if ticker in week_data:
                ticker_data = week_data[ticker]
                current_price = self.get_ticker_price(ticker, week_range)
                
                if current_price and self.should_sell(ticker, ticker_data, current_price):
                    tickers_to_sell.append((ticker, current_price))
        
        # Execute sells
        for ticker, price in tickers_to_sell:
            self.execute_sell(ticker, price, week_range)
        
        # Then, look for buys
        # Sort tickers by combined score (best opportunities first)
        buy_candidates = []
        for ticker, ticker_data in week_data.items():
            if self.should_buy(ticker, ticker_data):
                price = self.get_ticker_price(ticker, week_range)
                if price:
                    combined_score = ticker_data.get('combined_score', 0)
                    buy_candidates.append((ticker, ticker_data, price, combined_score))
        
        # Sort by combined score (descending)
        buy_candidates.sort(key=lambda x: x[3], reverse=True)
        
        # Execute buys (up to available cash and position limits)
        for ticker, ticker_data, price, score in buy_candidates:
            if len(self.positions) >= self.max_positions:
                break
            
            shares, dollar_amount = self.calculate_position_size(ticker, price, score)
            if shares > 0 and dollar_amount <= self.cash:
                self.execute_buy(ticker, price, shares, week_range)
        
        # Record portfolio state
        portfolio_value = self.get_current_portfolio_value(week_range)
        self.portfolio_history.append({
            'date': week_range,
            'cash': self.cash,
            'positions_value': portfolio_value - self.cash,
            'total_value': portfolio_value,
            'num_positions': len(self.positions),
            'return': (portfolio_value - self.initial_capital) / self.initial_capital
        })
        
        print(f"Portfolio Value: ${portfolio_value:,.2f} | Cash: ${self.cash:,.2f} | Positions: {len(self.positions)}")
    
    def run_backtest(self):
        """Run the complete backtesting simulation"""
        print("Starting backtesting simulation...")
        
        weeks = self.get_sorted_weeks()
        print(f"Processing {len(weeks)} weeks from {weeks[0]} to {weeks[-1]}")
        
        for i, week in enumerate(weeks):
            self.process_week(week)
            
            # Print progress every 10 weeks
            if (i + 1) % 10 == 0:
                current_value = self.portfolio_history[-1]['total_value']
                current_return = self.portfolio_history[-1]['return']
                print(f"Progress: {i+1}/{len(weeks)} weeks | Return: {current_return:.1%}")
        
        print("\nBacktesting completed!")
        self.print_final_results()
    
    def print_final_results(self):
        """Print final backtesting results"""
        if not self.portfolio_history:
            print("No trading history available")
            return
        
        final_value = self.portfolio_history[-1]['total_value']
        total_return = (final_value - self.initial_capital) / self.initial_capital
        
        print(f"\n{'='*50}")
        print(f"FINAL BACKTESTING RESULTS")
        print(f"{'='*50}")
        print(f"Initial Capital: ${self.initial_capital:,.2f}")
        print(f"Final Value: ${final_value:,.2f}")
        print(f"Total Return: {total_return:.2%}")
        print(f"Total Trades: {len(self.trade_history)}")
        
        # Calculate additional metrics
        returns = [h['return'] for h in self.portfolio_history]
        if len(returns) > 1:
            weekly_returns = np.diff(returns)
            sharpe_ratio = np.mean(weekly_returns) / np.std(weekly_returns) * np.sqrt(52) if np.std(weekly_returns) > 0 else 0
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
    
    def save_results(self, filename="backtest_results.json"):
        """Save backtesting results to file"""
        results = {
            'initial_capital': self.initial_capital,
            'final_value': self.portfolio_history[-1]['total_value'] if self.portfolio_history else self.initial_capital,
            'total_return': self.portfolio_history[-1]['return'] if self.portfolio_history else 0,
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
    print("Initializing Trading Engine...")
    
    # Create trading engine
    engine = TradingEngine(initial_capital=10000)
    
    # Run backtest
    engine.run_backtest()
    
    # Save results
    engine.save_results()
    
    return engine

if __name__ == "__main__":
    engine = main()