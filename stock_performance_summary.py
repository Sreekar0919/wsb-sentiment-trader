"""
Stock Performance Summary
Analyzes best and worst performing stocks from backtesting
"""

import json
import pandas as pd
import numpy as np
from collections import defaultdict

def analyze_stock_performance():
    """Analyze performance of all traded stocks"""
    
    # Load backtest results
    with open('backtest_results.json', 'r') as f:
        backtest_data = json.load(f)
    
    trades = backtest_data['trade_history']
    
    print("🎯 STOCK PERFORMANCE ANALYSIS")
    print("="*80)
    
    # Separate buy and sell trades
    buy_trades = [t for t in trades if t['action'] == 'BUY']
    sell_trades = [t for t in trades if t['action'] == 'SELL']
    
    # Calculate performance by ticker
    ticker_performance = defaultdict(list)
    ticker_stats = defaultdict(lambda: {
        'buys': 0,
        'sells': 0,
        'total_invested': 0,
        'total_proceeds': 0,
        'total_pnl': 0,
        'trades': []
    })
    
    # Process sell trades to get P&L
    for trade in sell_trades:
        ticker = trade['ticker']
        pnl = trade['pnl']
        pnl_percent = trade['pnl_percent']
        
        ticker_performance[ticker].append({
            'pnl': pnl,
            'pnl_percent': pnl_percent,
            'date': trade['date'],
            'shares': trade['shares'],
            'price': trade['price']
        })
        
        ticker_stats[ticker]['sells'] += 1
        ticker_stats[ticker]['total_proceeds'] += trade['total_proceeds']
        ticker_stats[ticker]['total_pnl'] += pnl
        ticker_stats[ticker]['trades'].append(trade)
    
    # Process buy trades
    for trade in buy_trades:
        ticker = trade['ticker']
        ticker_stats[ticker]['buys'] += 1
        ticker_stats[ticker]['total_invested'] += trade['total_cost']
    
    # Calculate statistics for each ticker
    ticker_summary = {}
    for ticker, stats in ticker_stats.items():
        if stats['sells'] > 0:  # Only include tickers we sold
            avg_return = np.mean([t['pnl_percent'] for t in ticker_performance[ticker]])
            win_rate = sum(1 for t in ticker_performance[ticker] if t['pnl_percent'] > 0) / len(ticker_performance[ticker])
            
            ticker_summary[ticker] = {
                'buys': stats['buys'],
                'sells': stats['sells'],
                'total_invested': stats['total_invested'],
                'total_proceeds': stats['total_proceeds'],
                'total_pnl': stats['total_pnl'],
                'avg_return': avg_return,
                'win_rate': win_rate,
                'best_trade': max([t['pnl_percent'] for t in ticker_performance[ticker]]),
                'worst_trade': min([t['pnl_percent'] for t in ticker_performance[ticker]])
            }
    
    return ticker_summary, ticker_performance

def print_best_stocks(ticker_summary):
    """Print best performing stocks"""
    
    print("\n🏆 TOP 20 BEST PERFORMING STOCKS")
    print("="*80)
    
    # Sort by total P&L
    sorted_by_pnl = sorted(ticker_summary.items(), 
                           key=lambda x: x[1]['total_pnl'], reverse=True)
    
    print("\nBy Total P&L:")
    print(f"{'Rank':<5} {'Ticker':<8} {'Trades':<8} {'Total P&L':<12} {'Avg Return':<12} {'Win Rate':<10}")
    print("-" * 80)
    
    for i, (ticker, stats) in enumerate(sorted_by_pnl[:20], 1):
        print(f"{i:<5} {ticker:<8} {stats['sells']:<8} ${stats['total_pnl']:>10.2f} "
              f"{stats['avg_return']:>10.1%} {stats['win_rate']:>9.1%}")
    
    # Sort by average return
    sorted_by_avg = sorted(ticker_summary.items(), 
                          key=lambda x: x[1]['avg_return'], reverse=True)
    
    print("\n\nBy Average Return Per Trade:")
    print(f"{'Rank':<5} {'Ticker':<8} {'Trades':<8} {'Avg Return':<12} {'Win Rate':<10} {'Total P&L':<12}")
    print("-" * 80)
    
    for i, (ticker, stats) in enumerate(sorted_by_avg[:20], 1):
        print(f"{i:<5} {ticker:<8} {stats['sells']:<8} {stats['avg_return']:>10.1%} "
              f"{stats['win_rate']:>9.1%} ${stats['total_pnl']:>10.2f}")
    
    # Sort by win rate
    sorted_by_wr = sorted(ticker_summary.items(), 
                         key=lambda x: x[1]['win_rate'], reverse=True)
    
    print("\n\nBy Win Rate (min 2 trades):")
    print(f"{'Rank':<5} {'Ticker':<8} {'Trades':<8} {'Win Rate':<10} {'Avg Return':<12} {'Total P&L':<12}")
    print("-" * 80)
    
    count = 0
    for ticker, stats in sorted_by_wr:
        if stats['sells'] >= 2 and count < 20:
            print(f"{count+1:<5} {ticker:<8} {stats['sells']:<8} {stats['win_rate']:>9.1%} "
                  f"{stats['avg_return']:>10.1%} ${stats['total_pnl']:>10.2f}")
            count += 1

def print_worst_stocks(ticker_summary):
    """Print worst performing stocks"""
    
    print("\n\n📉 BOTTOM 20 WORST PERFORMING STOCKS")
    print("="*80)
    
    # Sort by total P&L (ascending)
    sorted_by_pnl = sorted(ticker_summary.items(), 
                           key=lambda x: x[1]['total_pnl'])
    
    print("\nBy Total P&L (Losses):")
    print(f"{'Rank':<5} {'Ticker':<8} {'Trades':<8} {'Total P&L':<12} {'Avg Return':<12} {'Win Rate':<10}")
    print("-" * 80)
    
    for i, (ticker, stats) in enumerate(sorted_by_pnl[:20], 1):
        print(f"{i:<5} {ticker:<8} {stats['sells']:<8} ${stats['total_pnl']:>10.2f} "
              f"{stats['avg_return']:>10.1%} {stats['win_rate']:>9.1%}")
    
    # Sort by average return (ascending)
    sorted_by_avg = sorted(ticker_summary.items(), 
                          key=lambda x: x[1]['avg_return'])
    
    print("\n\nBy Average Return Per Trade (Worst):")
    print(f"{'Rank':<5} {'Ticker':<8} {'Trades':<8} {'Avg Return':<12} {'Win Rate':<10} {'Total P&L':<12}")
    print("-" * 80)
    
    for i, (ticker, stats) in enumerate(sorted_by_avg[:20], 1):
        print(f"{i:<5} {ticker:<8} {stats['sells']:<8} {stats['avg_return']:>10.1%} "
              f"{stats['win_rate']:>9.1%} ${stats['total_pnl']:>10.2f}")
    
    # Sort by win rate (ascending)
    sorted_by_wr = sorted(ticker_summary.items(), 
                         key=lambda x: x[1]['win_rate'])
    
    print("\n\nBy Win Rate (Lowest):")
    print(f"{'Rank':<5} {'Ticker':<8} {'Trades':<8} {'Win Rate':<10} {'Avg Return':<12} {'Total P&L':<12}")
    print("-" * 80)
    
    for i, (ticker, stats) in enumerate(sorted_by_wr[:20], 1):
        print(f"{i:<5} {ticker:<8} {stats['sells']:<8} {stats['win_rate']:>9.1%} "
              f"{stats['avg_return']:>10.1%} ${stats['total_pnl']:>10.2f}")

def print_most_traded(ticker_summary):
    """Print most frequently traded stocks"""
    
    print("\n\n📊 MOST FREQUENTLY TRADED STOCKS")
    print("="*80)
    
    sorted_by_trades = sorted(ticker_summary.items(), 
                             key=lambda x: x[1]['sells'], reverse=True)
    
    print(f"{'Rank':<5} {'Ticker':<8} {'Trades':<8} {'Avg Return':<12} {'Win Rate':<10} {'Total P&L':<12}")
    print("-" * 80)
    
    for i, (ticker, stats) in enumerate(sorted_by_trades[:20], 1):
        print(f"{i:<5} {ticker:<8} {stats['sells']:<8} {stats['avg_return']:>10.1%} "
              f"{stats['win_rate']:>9.1%} ${stats['total_pnl']:>10.2f}")

def print_statistics(ticker_summary):
    """Print overall statistics"""
    
    print("\n\n📈 OVERALL STATISTICS")
    print("="*80)
    
    total_tickers = len(ticker_summary)
    total_trades = sum(s['sells'] for s in ticker_summary.values())
    total_pnl = sum(s['total_pnl'] for s in ticker_summary.values())
    
    profitable_tickers = sum(1 for s in ticker_summary.values() if s['total_pnl'] > 0)
    losing_tickers = sum(1 for s in ticker_summary.values() if s['total_pnl'] < 0)
    
    avg_return_per_trade = np.mean([s['avg_return'] for s in ticker_summary.values()])
    avg_win_rate = np.mean([s['win_rate'] for s in ticker_summary.values()])
    
    print(f"\nTotal Unique Tickers Traded: {total_tickers}")
    print(f"Total Trades (Sells): {total_trades}")
    print(f"Total P&L: ${total_pnl:,.2f}")
    print(f"\nProfitable Tickers: {profitable_tickers} ({profitable_tickers/total_tickers*100:.1f}%)")
    print(f"Losing Tickers: {losing_tickers} ({losing_tickers/total_tickers*100:.1f}%)")
    print(f"\nAverage Return Per Trade: {avg_return_per_trade:.1%}")
    print(f"Average Win Rate: {avg_win_rate:.1%}")
    
    # Best and worst single trades
    all_returns = []
    for ticker, stats in ticker_summary.items():
        all_returns.append((ticker, stats['best_trade'], 'best'))
        all_returns.append((ticker, stats['worst_trade'], 'worst'))
    
    best_trade = max([r for r in all_returns if r[2] == 'best'], key=lambda x: x[1])
    worst_trade = min([r for r in all_returns if r[2] == 'worst'], key=lambda x: x[1])
    
    print(f"\nBest Single Trade: {best_trade[0]} +{best_trade[1]:.1%}")
    print(f"Worst Single Trade: {worst_trade[0]} {worst_trade[1]:.1%}")

def create_summary_json(ticker_summary):
    """Create JSON summary file"""
    
    # Sort by different metrics
    by_pnl = sorted(ticker_summary.items(), key=lambda x: x[1]['total_pnl'], reverse=True)
    by_return = sorted(ticker_summary.items(), key=lambda x: x[1]['avg_return'], reverse=True)
    by_winrate = sorted(ticker_summary.items(), key=lambda x: x[1]['win_rate'], reverse=True)
    by_trades = sorted(ticker_summary.items(), key=lambda x: x[1]['sells'], reverse=True)
    
    summary = {
        'total_tickers': len(ticker_summary),
        'total_trades': sum(s['sells'] for s in ticker_summary.values()),
        'total_pnl': sum(s['total_pnl'] for s in ticker_summary.values()),
        'profitable_tickers': sum(1 for s in ticker_summary.values() if s['total_pnl'] > 0),
        'losing_tickers': sum(1 for s in ticker_summary.values() if s['total_pnl'] < 0),
        'best_performers': {ticker: stats for ticker, stats in by_pnl[:10]},
        'worst_performers': {ticker: stats for ticker, stats in by_pnl[-10:]},
        'highest_returns': {ticker: stats for ticker, stats in by_return[:10]},
        'lowest_returns': {ticker: stats for ticker, stats in by_return[-10:]},
        'highest_winrate': {ticker: stats for ticker, stats in by_winrate[:10]},
        'lowest_winrate': {ticker: stats for ticker, stats in by_winrate[-10:]},
        'most_traded': {ticker: stats for ticker, stats in by_trades[:10]},
        'all_stocks': ticker_summary
    }
    
    with open('stock_performance_summary.json', 'w') as f:
        json.dump(summary, f, indent=4, default=str)
    
    print("\n✅ Summary saved to 'stock_performance_summary.json'")

def main():
    """Main execution"""
    
    # Analyze performance
    ticker_summary, ticker_performance = analyze_stock_performance()
    
    # Print best stocks
    print_best_stocks(ticker_summary)
    
    # Print worst stocks
    print_worst_stocks(ticker_summary)
    
    # Print most traded
    print_most_traded(ticker_summary)
    
    # Print statistics
    print_statistics(ticker_summary)
    
    # Create JSON summary
    create_summary_json(ticker_summary)
    
    return ticker_summary, ticker_performance

if __name__ == "__main__":
    ticker_summary, ticker_performance = main()