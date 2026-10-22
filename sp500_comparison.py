import json
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

class SP500Comparison:
    def __init__(self, backtest_file="backtest_results.json"):
        """Initialize comparison with backtest results"""
        with open(backtest_file, 'r') as f:
            self.backtest_data = json.load(f)
        
        self.initial_capital = self.backtest_data['initial_capital']
        self.portfolio_history = self.backtest_data['portfolio_history']
        
        # Get date range from backtest
        self.start_date = self.portfolio_history[0]['date'].split('/')[0]
        self.end_date = self.portfolio_history[-1]['date'].split('/')[1]
        
        print(f"Comparing performance from {self.start_date} to {self.end_date}")
    
    def fetch_sp500_data(self):
        """Fetch S&P 500 data for the same period"""
        print("Fetching S&P 500 data...")
        
        # Use SPY ETF as proxy for S&P 500
        spy = yf.Ticker("SPY")
        
        # Add buffer to ensure we get all data
        start_date = datetime.strptime(self.start_date, '%Y-%m-%d') - timedelta(days=7)
        end_date = datetime.strptime(self.end_date, '%Y-%m-%d') + timedelta(days=7)
        
        spy_data = spy.history(start=start_date, end=end_date)
        
        if spy_data.empty:
            raise ValueError("Could not fetch S&P 500 data")
        
        return spy_data
    
    def calculate_sp500_performance(self, spy_data):
        """Calculate S&P 500 performance aligned with our trading dates"""
        sp500_performance = []
        
        # Get initial S&P 500 price
        initial_date = datetime.strptime(self.start_date, '%Y-%m-%d')
        
        # Find the closest trading day to our start date
        closest_start_price = None
        for i in range(10):  # Look within 10 days
            check_date = initial_date + timedelta(days=i)
            if check_date.date() in spy_data.index.date:
                closest_start_price = spy_data.loc[spy_data.index.date == check_date.date(), 'Close'].iloc[0]
                break
            check_date = initial_date - timedelta(days=i)
            if check_date.date() in spy_data.index.date:
                closest_start_price = spy_data.loc[spy_data.index.date == check_date.date(), 'Close'].iloc[0]
                break
        
        if closest_start_price is None:
            raise ValueError("Could not find S&P 500 starting price")
        
        print(f"S&P 500 starting price: ${closest_start_price:.2f}")
        
        # Calculate performance for each week in our backtest
        for week_data in self.portfolio_history:
            week_end_date = datetime.strptime(week_data['date'].split('/')[1], '%Y-%m-%d')
            
            # Find closest S&P 500 price to this date
            closest_price = None
            for i in range(10):  # Look within 10 days
                check_date = week_end_date + timedelta(days=i)
                if check_date.date() in spy_data.index.date:
                    closest_price = spy_data.loc[spy_data.index.date == check_date.date(), 'Close'].iloc[0]
                    break
                check_date = week_end_date - timedelta(days=i)
                if check_date.date() in spy_data.index.date:
                    closest_price = spy_data.loc[spy_data.index.date == check_date.date(), 'Close'].iloc[0]
                    break
            
            if closest_price is not None:
                # Calculate S&P 500 return and portfolio value
                sp500_return = (closest_price - closest_start_price) / closest_start_price
                sp500_value = self.initial_capital * (1 + sp500_return)
                
                sp500_performance.append({
                    'date': week_data['date'],
                    'sp500_price': closest_price,
                    'sp500_return': sp500_return,
                    'sp500_value': sp500_value,
                    'strategy_value': week_data['total_value'],
                    'strategy_return': week_data['return']
                })
        
        return sp500_performance
    
    def calculate_metrics(self, performance_data):
        """Calculate performance metrics for both strategies"""
        # Extract returns
        strategy_returns = [p['strategy_return'] for p in performance_data]
        sp500_returns = [p['sp500_return'] for p in performance_data]
        
        # Calculate weekly returns for volatility
        strategy_weekly_returns = np.diff(strategy_returns)
        sp500_weekly_returns = np.diff(sp500_returns)
        
        # Final performance
        final_strategy_return = strategy_returns[-1]
        final_sp500_return = sp500_returns[-1]
        
        # Volatility (annualized)
        strategy_volatility = np.std(strategy_weekly_returns) * np.sqrt(52) if len(strategy_weekly_returns) > 1 else 0
        sp500_volatility = np.std(sp500_weekly_returns) * np.sqrt(52) if len(sp500_weekly_returns) > 1 else 0
        
        # Sharpe ratio (assuming 0% risk-free rate)
        strategy_sharpe = (final_strategy_return * 52 / len(strategy_returns)) / strategy_volatility if strategy_volatility > 0 else 0
        sp500_sharpe = (final_sp500_return * 52 / len(sp500_returns)) / sp500_volatility if sp500_volatility > 0 else 0
        
        # Maximum drawdown
        strategy_max_dd = self.calculate_max_drawdown([p['strategy_value'] for p in performance_data])
        sp500_max_dd = self.calculate_max_drawdown([p['sp500_value'] for p in performance_data])
        
        # Alpha (excess return over S&P 500)
        alpha = final_strategy_return - final_sp500_return
        
        return {
            'strategy': {
                'total_return': final_strategy_return,
                'annualized_return': (1 + final_strategy_return) ** (52 / len(strategy_returns)) - 1,
                'volatility': strategy_volatility,
                'sharpe_ratio': strategy_sharpe,
                'max_drawdown': strategy_max_dd,
                'final_value': performance_data[-1]['strategy_value']
            },
            'sp500': {
                'total_return': final_sp500_return,
                'annualized_return': (1 + final_sp500_return) ** (52 / len(sp500_returns)) - 1,
                'volatility': sp500_volatility,
                'sharpe_ratio': sp500_sharpe,
                'max_drawdown': sp500_max_dd,
                'final_value': performance_data[-1]['sp500_value']
            },
            'alpha': alpha,
            'beta': self.calculate_beta(strategy_weekly_returns, sp500_weekly_returns)
        }
    
    def calculate_max_drawdown(self, values):
        """Calculate maximum drawdown"""
        peak = values[0]
        max_dd = 0
        
        for value in values:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak
            max_dd = max(max_dd, drawdown)
        
        return max_dd
    
    def calculate_beta(self, strategy_returns, sp500_returns):
        """Calculate beta (correlation with market)"""
        if len(strategy_returns) != len(sp500_returns) or len(strategy_returns) < 2:
            return 0
        
        covariance = np.cov(strategy_returns, sp500_returns)[0][1]
        sp500_variance = np.var(sp500_returns)
        
        return covariance / sp500_variance if sp500_variance > 0 else 0
    
    def print_comparison(self, metrics):
        """Print detailed comparison"""
        print("\n" + "="*80)
        print("PERFORMANCE COMPARISON: REDDIT SENTIMENT STRATEGY vs S&P 500")
        print("="*80)
        
        print(f"\n📊 TOTAL RETURNS:")
        print(f"Strategy:     {metrics['strategy']['total_return']:.2%}")
        print(f"S&P 500:      {metrics['sp500']['total_return']:.2%}")
        print(f"Alpha:        {metrics['alpha']:.2%} (Excess return over S&P 500)")
        
        print(f"\n💰 FINAL VALUES (Starting with $10,000):")
        print(f"Strategy:     ${metrics['strategy']['final_value']:,.2f}")
        print(f"S&P 500:      ${metrics['sp500']['final_value']:,.2f}")
        print(f"Difference:   ${metrics['strategy']['final_value'] - metrics['sp500']['final_value']:,.2f}")
        
        print(f"\n📈 ANNUALIZED RETURNS:")
        print(f"Strategy:     {metrics['strategy']['annualized_return']:.2%}")
        print(f"S&P 500:      {metrics['sp500']['annualized_return']:.2%}")
        
        print(f"\n⚡ RISK METRICS:")
        print(f"Strategy Volatility:    {metrics['strategy']['volatility']:.2%}")
        print(f"S&P 500 Volatility:     {metrics['sp500']['volatility']:.2%}")
        print(f"Strategy Sharpe Ratio:  {metrics['strategy']['sharpe_ratio']:.2f}")
        print(f"S&P 500 Sharpe Ratio:   {metrics['sp500']['sharpe_ratio']:.2f}")
        print(f"Beta:                   {metrics['beta']:.2f}")
        
        print(f"\n📉 MAXIMUM DRAWDOWN:")
        print(f"Strategy:     {metrics['strategy']['max_drawdown']:.2%}")
        print(f"S&P 500:      {metrics['sp500']['max_drawdown']:.2%}")
        
        # Performance summary
        outperformance = metrics['strategy']['total_return'] / metrics['sp500']['total_return'] - 1
        print(f"\n🎯 SUMMARY:")
        print(f"Strategy outperformed S&P 500 by {outperformance:.1%}")
        print(f"Risk-adjusted outperformance (Sharpe): {metrics['strategy']['sharpe_ratio'] - metrics['sp500']['sharpe_ratio']:.2f}")
        
        if metrics['alpha'] > 0:
            print(f"✅ Strategy generated positive alpha of {metrics['alpha']:.2%}")
        else:
            print(f"❌ Strategy generated negative alpha of {metrics['alpha']:.2%}")
    
    def save_comparison_data(self, performance_data, metrics, filename="sp500_comparison.json"):
        """Save comparison data to file"""
        comparison_data = {
            'period': f"{self.start_date} to {self.end_date}",
            'initial_capital': self.initial_capital,
            'performance_data': performance_data,
            'metrics': metrics,
            'summary': {
                'strategy_outperformance': metrics['alpha'],
                'strategy_total_return': metrics['strategy']['total_return'],
                'sp500_total_return': metrics['sp500']['total_return'],
                'strategy_final_value': metrics['strategy']['final_value'],
                'sp500_final_value': metrics['sp500']['final_value']
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(comparison_data, f, indent=4, default=str)
        
        print(f"\nComparison data saved to {filename}")
    
    def run_comparison(self):
        """Run the complete comparison analysis"""
        try:
            # Fetch S&P 500 data
            spy_data = self.fetch_sp500_data()
            
            # Calculate aligned performance
            performance_data = self.calculate_sp500_performance(spy_data)
            
            # Calculate metrics
            metrics = self.calculate_metrics(performance_data)
            
            # Print comparison
            self.print_comparison(metrics)
            
            # Save data
            self.save_comparison_data(performance_data, metrics)
            
            return performance_data, metrics
            
        except Exception as e:
            print(f"Error in comparison: {e}")
            return None, None

def main():
    """Main execution function"""
    print("Starting S&P 500 comparison analysis...")
    
    comparison = SP500Comparison()
    performance_data, metrics = comparison.run_comparison()
    
    return comparison, performance_data, metrics

if __name__ == "__main__":
    comparison, performance_data, metrics = main()