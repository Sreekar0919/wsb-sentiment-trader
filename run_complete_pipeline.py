#!/usr/bin/env python3
"""
Complete Reddit Sentiment Trading Pipeline
Runs all scripts in the correct order to recreate the entire project
"""

import subprocess
import sys
import os
import time
from datetime import datetime

def print_header(message):
    """Print a formatted header"""
    print("\n" + "="*60)
    print(f"🚀 {message}")
    print("="*60)

def print_step(step_num, total_steps, message):
    """Print step information"""
    print(f"\n[{step_num}/{total_steps}] {message}")
    print("-" * 50)

def run_script(script_name, description):
    """Run a Python script and return success status"""
    print(f"▶️  Running {script_name}...")
    start_time = time.time()
    
    try:
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=True, text=True, timeout=1800)  # 30 min timeout
        
        end_time = time.time()
        duration = end_time - start_time
        
        if result.returncode == 0:
            print(f"✅ {description} completed successfully in {duration:.1f}s")
            return True
        else:
            print(f"❌ {description} failed!")
            print(f"Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} timed out after 30 minutes")
        return False
    except Exception as e:
        print(f"❌ Error running {description}: {e}")
        return False

def check_prerequisites():
    """Check if required files and packages exist"""
    print_header("CHECKING PREREQUISITES")
    
    # Check required input files
    required_files = [
        "data.csv",
        "nasdaq_tickers.json", 
        "reddit_sentiment_words.json"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print("❌ Missing required input files:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    
    # Check required packages
    required_packages = [
        "pandas", "numpy", "yfinance", "vaderSentiment", "matplotlib", "seaborn"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\nInstall with: pip install " + " ".join(missing_packages))
        return False
    
    print("✅ All prerequisites satisfied!")
    return True

def run_complete_pipeline():
    """Run the complete trading pipeline"""
    
    print_header("REDDIT SENTIMENT TRADING PIPELINE")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Prerequisites not met. Please fix the issues above and try again.")
        return False
    
    # Define pipeline steps
    pipeline_steps = [
        ("calculate_sentiment.py", "Sentiment Analysis", "Process Reddit data and calculate sentiment scores"),
        ("momentum_tracker.py", "Momentum Tracking", "Fetch stock prices and calculate 3-day momentum"),
        ("trading_engine.py", "Trading Engine", "Run backtesting simulation with buy/sell logic"),
        ("sp500_comparison.py", "S&P 500 Comparison", "Compare strategy performance with benchmark"),
        ("trading_analysis.py", "Comprehensive Analysis", "Generate detailed analysis and visualizations"),
    ]
    
    total_steps = len(pipeline_steps)
    successful_steps = 0
    start_time = time.time()
    
    # Run each step
    for i, (script, name, description) in enumerate(pipeline_steps, 1):
        print_step(i, total_steps, f"{name}: {description}")
        
        if os.path.exists(script):
            if run_script(script, name):
                successful_steps += 1
            else:
                print(f"\n❌ Pipeline failed at step {i}: {name}")
                print("Fix the error and run the pipeline again.")
                return False
        else:
            print(f"❌ Script not found: {script}")
            return False
    
    # Pipeline completed
    total_time = time.time() - start_time
    
    print_header("PIPELINE COMPLETED SUCCESSFULLY!")
    print(f" All {successful_steps}/{total_steps} steps completed")
    print(f"⏱Total execution time: {total_time/60:.1f} minutes")
    
    # List generated files
    output_files = [
        "weekly_sentiment.json",
        "weekly_sentiment_momentum.json", 
        "backtest_results.json",
        "sp500_comparison.json",
        "portfolio_performance.png",
        "trade_analysis.png",
        "risk_metrics.png"
    ]
    
    print(f"\n📁 Generated output files:")
    for file in output_files:
        if os.path.exists(file):
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file} (missing)")
    
    print(f"\n🎉 Reddit Sentiment Trading Strategy pipeline completed!")
    print(f"📊 Check the PNG files for visualizations")
    print(f"📈 Check backtest_results.json for detailed trading history")
    
    return True

def main():
    """Main execution function"""
    try:
        success = run_complete_pipeline()
        if success:
            print(f"\n🚀 Pipeline executed successfully!")
            sys.exit(0)
        else:
            print(f"\n❌ Pipeline failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        print(f"\n⏹️  Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()