import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter, defaultdict
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class TradingAnalysis:
    def __init__(self):
        """Initialize with all data files"""
        # Load backtest results
        with open('backtest_results.json', 'r') as f:
            self.backtest_data = json.load(f)
        
        # Load S&P 500 comparison
        with open('sp500_comparison.json', 'r') as f:
            self.sp500_data = json.load(f)
        
        self.trades = self.backtest_data['trade_history']
        self.portfolio_history = self.backtest_data['portfolio_history']
        self.performance_data = self.sp500_data['performance_data']
        
        # Set up plotting style
        plt.style.use('default')
        sns.set_palette("husl")
        
    def analyze_most_common_trades(self):
        """Analyze the most frequently traded tickers"""
        print("🔍 ANALYZING MOST COMMON TRADES")
        print("="*50)
        
        # Count trades by ticker
        buy_trades = [t for t in self.trades if t['action'] == 'BUY']
        sell_trades = [t for t in self.trades if t['action'] == 'SELL']
        
        # Most bought tickers
        buy_counter = Counter([t['ticker'] for t in buy_trades])
        sell_counter = Counter([t['ticker'] for t in sell_trades])
        
        print(f"📊 MOST FREQUENTLY TRADED TICKERS:")
        print(f"Total unique tickers traded: {len(buy_counter)}")
        print(f"Total buy trades: {len(buy_trades)}")
        print(f"Total sell trades: {len(sell_trades)}")
        print()
        
        # Top 15 most traded
        top_tickers = buy_counter.most_common(15)
        
        print("🏆 TOP 15 MOST BOUGHT TICKERS:")
        for i, (ticker, count) in enumerate(top_tickers, 1):
            sell_count = sell_counter.get(ticker, 0)
            print(f"{i:2d}. {ticker:6s} - {count:2d} buys, {sell_count:2d} sells")
        
        return buy_counter, sell_counter, top_tickers
    
    def analyze_trade_performance(self):
        """Analyze performance of individual trades"""
        print("\n💰 TRADE PERFORMANCE ANALYSIS")
        print("="*50)
        
        sell_trades = [t for t in self.trades if t['action'] == 'SELL']
        
        # Calculate performance metrics by ticker
        ticker_performance = defaultdict(list)
        for trade in sell_trades:
            ticker = trade['ticker']
            pnl_percent = trade['pnl_percent']
            ticker_performance[ticker].append(pnl_percent)
        
        # Calculate average performance per ticker
        ticker_avg_performance = {}
        for ticker, returns in ticker_performance.items():
            ticker_avg_performance[ticker] = {
                'avg_return': np.mean(returns),
                'total_trades': len(returns),
                'win_rate': sum(1 for r in returns if r > 0) / len(returns),
                'total_pnl': sum(returns)
            }
        
        # Sort by total PnL
        sorted_performance = sorted(ticker_avg_performance.items(), 
                                  key=lambda x: x[1]['total_pnl'], reverse=True)
        
        print("🎯 TOP 15 MOST PROFITABLE TICKERS:")
        for i, (ticker, perf) in enumerate(sorted_performance[:15], 1):
            print(f"{i:2d}. {ticker:6s} - Avg: {perf['avg_return']:6.1%}, "
                  f"Trades: {perf['total_trades']:2d}, "
                  f"Win Rate: {perf['win_rate']:5.1%}, "
                  f"Total PnL: {perf['total_pnl']:6.1%}")
        
        print("\n📉 WORST 10 PERFORMING TICKERS:")
        for i, (ticker, perf) in enumerate(sorted_performance[-10:], 1):
            print(f"{i:2d}. {ticker:6s} - Avg: {perf['avg_return']:6.1%}, "
                  f"Trades: {perf['total_trades']:2d}, "
                  f"Win Rate: {perf['win_rate']:5.1%}, "
                  f"Total PnL: {perf['total_pnl']:6.1%}")
        
        return ticker_performance, ticker_avg_performance
    
    def create_performance_chart(self):
        """Create portfolio performance vs S&P 500 chart"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12))
        
        # Extract data for plotting
        dates = [datetime.strptime(p['date'].split('/')[0], '%Y-%m-%d') for p in self.performance_data]
        strategy_values = [p['strategy_value'] for p in self.performance_data]
        sp500_values = [p['sp500_value'] for p in self.performance_data]
        
        # Plot 1: Portfolio Values
        ax1.plot(dates, strategy_values, label='Reddit Sentiment Strategy', linewidth=2, color='#2E8B57')
        ax1.plot(dates, sp500_values, label='S&P 500', linewidth=2, color='#FF6B6B')
        ax1.set_title('Portfolio Performance Comparison', fontsize=16, fontweight='bold')
        ax1.set_ylabel('Portfolio Value ($)', fontsize=12)
        ax1.legend(fontsize=12)
        ax1.grid(True, alpha=0.3)
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        
        # Add performance annotations
        final_strategy = strategy_values[-1]
        final_sp500 = sp500_values[-1]
        ax1.annotate(f'Final: ${final_strategy:,.0f}\n(+{(final_strategy/10000-1)*100:.1f}%)', 
                    xy=(dates[-1], final_strategy), xytext=(10, 10),
                    textcoords='offset points', fontsize=10,
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgreen', alpha=0.7))
        ax1.annotate(f'Final: ${final_sp500:,.0f}\n(+{(final_sp500/10000-1)*100:.1f}%)', 
                    xy=(dates[-1], final_sp500), xytext=(10, -30),
                    textcoords='offset points', fontsize=10,
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='lightcoral', alpha=0.7))
        
        # Plot 2: Returns
        strategy_returns = [(v/10000 - 1) * 100 for v in strategy_values]
        sp500_returns = [(v/10000 - 1) * 100 for v in sp500_values]
        
        ax2.plot(dates, strategy_returns, label='Reddit Strategy Returns', linewidth=2, color='#2E8B57')
        ax2.plot(dates, sp500_returns, label='S&P 500 Returns', linewidth=2, color='#FF6B6B')
        ax2.set_title('Cumulative Returns Comparison', fontsize=16, fontweight='bold')
        ax2.set_xlabel('Date', fontsize=12)
        ax2.set_ylabel('Cumulative Return (%)', fontsize=12)
        ax2.legend(fontsize=12)
        ax2.grid(True, alpha=0.3)
        ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.0f}%'))
        
        plt.tight_layout()
        plt.savefig('portfolio_performance.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        print("📊 Portfolio performance chart saved as 'portfolio_performance.png'")
    
    def create_trade_analysis_charts(self, buy_counter, ticker_avg_performance):
        """Create charts for trade analysis"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 15))
        
        # Chart 1: Most Traded Tickers
        top_15_tickers = dict(buy_counter.most_common(15))
        tickers = list(top_15_tickers.keys())
        counts = list(top_15_tickers.values())
        
        bars1 = ax1.bar(range(len(tickers)), counts, color='skyblue', alpha=0.8)
        ax1.set_title('Top 15 Most Traded Tickers', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Ticker', fontsize=12)
        ax1.set_ylabel('Number of Buy Trades', fontsize=12)
        ax1.set_xticks(range(len(tickers)))
        ax1.set_xticklabels(tickers, rotation=45)
        ax1.grid(True, alpha=0.3)
        
        # Add value labels on bars
        for bar, count in zip(bars1, counts):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                    str(count), ha='center', va='bottom', fontweight='bold')
        
        # Chart 2: Win Rate by Top Tickers
        top_performers = sorted(ticker_avg_performance.items(), 
                               key=lambda x: x[1]['total_trades'], reverse=True)[:15]
        
        perf_tickers = [t[0] for t in top_performers]
        win_rates = [t[1]['win_rate'] * 100 for t in top_performers]
        
        bars2 = ax2.bar(range(len(perf_tickers)), win_rates, color='lightgreen', alpha=0.8)
        ax2.set_title('Win Rate for Most Traded Tickers', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Ticker', fontsize=12)
        ax2.set_ylabel('Win Rate (%)', fontsize=12)
        ax2.set_xticks(range(len(perf_tickers)))
        ax2.set_xticklabels(perf_tickers, rotation=45)
        ax2.grid(True, alpha=0.3)
        ax2.axhline(y=50, color='red', linestyle='--', alpha=0.7, label='50% Break-even')
        ax2.legend()
        
        # Add value labels
        for bar, rate in zip(bars2, win_rates):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                    f'{rate:.1f}%', ha='center', va='bottom', fontweight='bold')
        
        # Chart 3: Average Return by Ticker
        avg_returns = [t[1]['avg_return'] * 100 for t in top_performers]
        colors = ['green' if r > 0 else 'red' for r in avg_returns]
        
        bars3 = ax3.bar(range(len(perf_tickers)), avg_returns, color=colors, alpha=0.7)
        ax3.set_title('Average Return per Trade by Ticker', fontsize=14, fontweight='bold')
        ax3.set_xlabel('Ticker', fontsize=12)
        ax3.set_ylabel('Average Return (%)', fontsize=12)
        ax3.set_xticks(range(len(perf_tickers)))
        ax3.set_xticklabels(perf_tickers, rotation=45)
        ax3.grid(True, alpha=0.3)
        ax3.axhline(y=0, color='black', linestyle='-', alpha=0.5)
        
        # Chart 4: Monthly Trading Activity
        trade_dates = [datetime.strptime(t['date'].split('/')[0], '%Y-%m-%d') for t in self.trades if t['action'] == 'BUY']
        monthly_trades = pd.Series(trade_dates).dt.to_period('M').value_counts().sort_index()
        
        ax4.plot(range(len(monthly_trades)), monthly_trades.values, marker='o', linewidth=2, markersize=6)
        ax4.set_title('Trading Activity Over Time', fontsize=14, fontweight='bold')
        ax4.set_xlabel('Month', fontsize=12)
        ax4.set_ylabel('Number of Trades', fontsize=12)
        ax4.set_xticks(range(0, len(monthly_trades), 3))
        ax4.set_xticklabels([str(monthly_trades.index[i]) for i in range(0, len(monthly_trades), 3)], rotation=45)
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('trade_analysis.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        print("📊 Trade analysis charts saved as 'trade_analysis.png'")
    
    def create_risk_metrics_chart(self):
        """Create risk and performance metrics visualization"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # Chart 1: Drawdown Analysis
        portfolio_values = [p['total_value'] for p in self.portfolio_history]
        peak = portfolio_values[0]
        drawdowns = []
        
        for value in portfolio_values:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak * 100
            drawdowns.append(drawdown)
        
        dates = [datetime.strptime(p['date'].split('/')[0], '%Y-%m-%d') for p in self.portfolio_history]
        
        ax1.fill_between(dates, drawdowns, 0, color='red', alpha=0.3)
        ax1.plot(dates, drawdowns, color='red', linewidth=1)
        ax1.set_title('Portfolio Drawdown Over Time', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Drawdown (%)', fontsize=12)
        ax1.grid(True, alpha=0.3)
        ax1.invert_yaxis()
        
        # Chart 2: Monthly Returns Distribution
        monthly_returns = []
        prev_value = 10000
        
        for i, p in enumerate(self.portfolio_history):
            if i % 4 == 0 and i > 0:  # Approximate monthly (every 4 weeks)
                monthly_return = (p['total_value'] - prev_value) / prev_value * 100
                monthly_returns.append(monthly_return)
                prev_value = p['total_value']
        
        ax2.hist(monthly_returns, bins=15, color='skyblue', alpha=0.7, edgecolor='black')
        ax2.set_title('Monthly Returns Distribution', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Monthly Return (%)', fontsize=12)
        ax2.set_ylabel('Frequency', fontsize=12)
        ax2.axvline(x=np.mean(monthly_returns), color='red', linestyle='--', 
                   label=f'Mean: {np.mean(monthly_returns):.1f}%')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Chart 3: Trade P&L Distribution
        sell_trades = [t for t in self.trades if t['action'] == 'SELL']
        pnl_percentages = [t['pnl_percent'] * 100 for t in sell_trades]
        
        ax3.hist(pnl_percentages, bins=20, color='lightgreen', alpha=0.7, edgecolor='black')
        ax3.set_title('Individual Trade P&L Distribution', fontsize=14, fontweight='bold')
        ax3.set_xlabel('Trade Return (%)', fontsize=12)
        ax3.set_ylabel('Number of Trades', fontsize=12)
        ax3.axvline(x=0, color='red', linestyle='-', alpha=0.7, label='Break-even')
        ax3.axvline(x=np.mean(pnl_percentages), color='blue', linestyle='--', 
                   label=f'Mean: {np.mean(pnl_percentages):.1f}%')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # Chart 4: Portfolio Composition Over Time
        position_counts = [p['num_positions'] for p in self.portfolio_history]
        cash_percentages = [(p['cash'] / p['total_value']) * 100 for p in self.portfolio_history]
        
        ax4_twin = ax4.twinx()
        
        line1 = ax4.plot(dates, position_counts, color='blue', linewidth=2, label='Number of Positions')
        line2 = ax4_twin.plot(dates, cash_percentages, color='orange', linewidth=2, label='Cash %')
        
        ax4.set_title('Portfolio Composition Over Time', fontsize=14, fontweight='bold')
        ax4.set_xlabel('Date', fontsize=12)
        ax4.set_ylabel('Number of Positions', fontsize=12, color='blue')
        ax4_twin.set_ylabel('Cash Percentage (%)', fontsize=12, color='orange')
        
        # Combine legends
        lines = line1 + line2
        labels = [l.get_label() for l in lines]
        ax4.legend(lines, labels, loc='upper left')
        
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('risk_metrics.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        print("📊 Risk metrics charts saved as 'risk_metrics.png'")
    
    def print_summary_statistics(self):
        """Print comprehensive summary statistics"""
        print("\n" + "="*80)
        print("📈 COMPREHENSIVE TRADING SUMMARY")
        print("="*80)
        
        # Basic stats
        total_trades = len(self.trades)
        buy_trades = len([t for t in self.trades if t['action'] == 'BUY'])
        sell_trades = len([t for t in self.trades if t['action'] == 'SELL'])
        
        print(f"🔢 TRADING STATISTICS:")
        print(f"Total Trades: {total_trades}")
        print(f"Buy Trades: {buy_trades}")
        print(f"Sell Trades: {sell_trades}")
        
        # Performance stats
        initial_value = self.backtest_data['initial_capital']
        final_value = self.backtest_data['final_value']
        total_return = self.backtest_data['total_return']
        
        print(f"\n💰 PERFORMANCE:")
        print(f"Initial Capital: ${initial_value:,.2f}")
        print(f"Final Value: ${final_value:,.2f}")
        print(f"Total Return: {total_return:.2%}")
        print(f"Profit: ${final_value - initial_value:,.2f}")
        
        # Trade performance
        sell_trade_data = [t for t in self.trades if t['action'] == 'SELL']
        winning_trades = [t for t in sell_trade_data if t['pnl'] > 0]
        losing_trades = [t for t in sell_trade_data if t['pnl'] <= 0]
        
        print(f"\n🎯 TRADE PERFORMANCE:")
        print(f"Winning Trades: {len(winning_trades)} ({len(winning_trades)/len(sell_trade_data)*100:.1f}%)")
        print(f"Losing Trades: {len(losing_trades)} ({len(losing_trades)/len(sell_trade_data)*100:.1f}%)")
        
        if winning_trades:
            avg_win = np.mean([t['pnl_percent'] for t in winning_trades]) * 100
            print(f"Average Win: {avg_win:.1f}%")
        
        if losing_trades:
            avg_loss = np.mean([t['pnl_percent'] for t in losing_trades]) * 100
            print(f"Average Loss: {avg_loss:.1f}%")
        
        # Best and worst trades
        if sell_trade_data:
            best_trade = max(sell_trade_data, key=lambda x: x['pnl_percent'])
            worst_trade = min(sell_trade_data, key=lambda x: x['pnl_percent'])
            
            print(f"\n🏆 BEST TRADE:")
            print(f"{best_trade['ticker']}: {best_trade['pnl_percent']*100:.1f}% return (${best_trade['pnl']:.2f})")
            
            print(f"\n📉 WORST TRADE:")
            print(f"{worst_trade['ticker']}: {worst_trade['pnl_percent']*100:.1f}% return (${worst_trade['pnl']:.2f})")
    
    def run_complete_analysis(self):
        """Run the complete analysis and create all visualizations"""
        print("🚀 STARTING COMPREHENSIVE TRADING ANALYSIS")
        print("="*80)
        
        # Analyze trades
        buy_counter, sell_counter, top_tickers = self.analyze_most_common_trades()
        ticker_performance, ticker_avg_performance = self.analyze_trade_performance()
        
        # Create all charts
        print("\n📊 Creating visualizations...")
        self.create_performance_chart()
        self.create_trade_analysis_charts(buy_counter, ticker_avg_performance)
        self.create_risk_metrics_chart()
        
        # Print summary
        self.print_summary_statistics()
        
        print("\n✅ Analysis complete! Check the generated PNG files for visualizations.")
        
        return {
            'buy_counter': buy_counter,
            'sell_counter': sell_counter,
            'ticker_performance': ticker_performance,
            'ticker_avg_performance': ticker_avg_performance
        }

def main():
    """Main execution function"""
    analyzer = TradingAnalysis()
    results = analyzer.run_complete_analysis()
    return analyzer, results

if __name__ == "__main__":
    analyzer, results = main()