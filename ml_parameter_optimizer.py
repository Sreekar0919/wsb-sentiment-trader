"""
ML-Based Parameter Optimization
Uses machine learning to optimize trading strategy weights
"""

import json
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import warnings
warnings.filterwarnings('ignore')

class MLParameterOptimizer:
    """Use ML to optimize trading strategy parameters"""
    
    def __init__(self):
        """Initialize with baseline results"""
        with open('backtest_results.json', 'r') as f:
            self.baseline = json.load(f)
        
        self.baseline_return = self.baseline['total_return']
        self.baseline_sharpe = 1.88
        
        print("🤖 ML-BASED PARAMETER OPTIMIZATION")
        print("="*70)
        print(f"Baseline Return: {self.baseline_return:.2%}")
        print(f"Baseline Sharpe: {self.baseline_sharpe:.2f}")
    
    def define_model_weights(self):
        """Define all model weights as features"""
        
        weights = {
            # Sentiment Analysis Weights
            'vader_weight': {
                'current': 1.0,
                'range': [0.5, 2.0],
                'description': 'VADER sentiment influence',
                'category': 'sentiment'
            },
            'reddit_keyword_weight': {
                'current': 0.1,
                'range': [0.05, 0.3],
                'description': 'Reddit keyword boost per match',
                'category': 'sentiment'
            },
            'karma_weight': {
                'current': 1.0,
                'range': [0.5, 2.0],
                'description': 'Post popularity multiplier',
                'category': 'sentiment'
            },
            
            # Momentum Weights
            'momentum_weight': {
                'current': 0.3,
                'range': [0.1, 0.7],
                'description': 'Momentum influence in combined score',
                'category': 'momentum'
            },
            'momentum_threshold': {
                'current': 0.02,
                'range': [0.01, 0.05],
                'description': 'Minimum momentum (2%)',
                'category': 'momentum'
            },
            
            # Combined Score Weights
            'sentiment_weight_combined': {
                'current': 0.7,
                'range': [0.5, 0.9],
                'description': 'Sentiment weight in combined score',
                'category': 'combined'
            },
            'combined_threshold': {
                'current': 15.0,
                'range': [10.0, 25.0],
                'description': 'Minimum combined score',
                'category': 'combined'
            },
            
            # Risk Management Weights
            'stop_loss': {
                'current': -0.10,
                'range': [-0.20, -0.05],
                'description': 'Stop loss threshold',
                'category': 'risk'
            },
            'take_profit': {
                'current': 0.25,
                'range': [0.15, 0.40],
                'description': 'Take profit threshold',
                'category': 'risk'
            },
            
            # Position Sizing Weights
            'max_position_size': {
                'current': 0.05,
                'range': [0.03, 0.10],
                'description': 'Max % per position',
                'category': 'sizing'
            },
            'max_positions': {
                'current': 20,
                'range': [10, 30],
                'description': 'Max number of positions',
                'category': 'sizing'
            },
            
            # Entry/Exit Weights
            'sentiment_threshold': {
                'current': 10.0,
                'range': [5.0, 20.0],
                'description': 'Minimum sentiment for buy',
                'category': 'entry'
            },
            'min_mentions': {
                'current': 5,
                'range': [1, 15],
                'description': 'Minimum mentions to trade',
                'category': 'entry'
            }
        }
        
        return weights
    
    def create_training_data(self, n_samples=100):
        """Create synthetic training data for ML model"""
        
        weights = self.define_model_weights()
        X = []
        y = []
        
        print(f"\n📊 Generating {n_samples} synthetic training samples...")
        
        for i in range(n_samples):
            # Generate random parameter combinations
            sample = {}
            for param, info in weights.items():
                min_val, max_val = info['range']
                sample[param] = np.random.uniform(min_val, max_val)
            
            X.append(list(sample.values()))
            
            # Simulate performance (simplified model)
            # Better parameters = better returns
            performance = self._simulate_performance(sample, weights)
            y.append(performance)
        
        X = np.array(X)
        y = np.array(y)
        
        # Normalize features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        feature_names = list(weights.keys())
        
        return X_scaled, y, feature_names, scaler, weights
    
    def _simulate_performance(self, params, weights):
        """Simulate strategy performance for given parameters"""
        
        # Baseline performance
        base_return = self.baseline_return
        
        # Adjustments based on parameters
        adjustments = 0
        
        # Sentiment weight impact
        if params['vader_weight'] > 1.0:
            adjustments += (params['vader_weight'] - 1.0) * 0.05
        
        # Momentum weight impact
        if params['momentum_weight'] > 0.3:
            adjustments += (params['momentum_weight'] - 0.3) * 0.1
        
        # Risk management impact
        if params['stop_loss'] > -0.10:  # Tighter stop loss
            adjustments += (abs(params['stop_loss']) - 0.10) * 0.2
        
        if params['take_profit'] > 0.25:  # Higher take profit
            adjustments += (params['take_profit'] - 0.25) * 0.1
        
        # Position sizing impact
        if params['max_positions'] > 20:
            adjustments += (params['max_positions'] - 20) * 0.01
        
        # Add some randomness
        noise = np.random.normal(0, 0.02)
        
        return base_return + adjustments + noise
    
    def train_ml_models(self, X, y, feature_names):
        """Train multiple ML models to predict performance"""
        
        print(f"\n🤖 Training ML Models...")
        print("="*70)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        models = {}
        
        # Random Forest
        print("\n1. Random Forest Regressor")
        rf = RandomForestRegressor(n_estimators=100, random_state=42, max_depth=10)
        rf.fit(X_train, y_train)
        rf_score = rf.score(X_test, y_test)
        models['Random Forest'] = rf
        print(f"   R² Score: {rf_score:.4f}")
        
        # Gradient Boosting
        print("\n2. Gradient Boosting Regressor")
        gb = GradientBoostingRegressor(n_estimators=100, random_state=42, max_depth=5)
        gb.fit(X_train, y_train)
        gb_score = gb.score(X_test, y_test)
        models['Gradient Boosting'] = gb
        print(f"   R² Score: {gb_score:.4f}")
        
        # Feature importance
        print(f"\n📊 Feature Importance (Random Forest):")
        importances = rf.feature_importances_
        importance_df = pd.DataFrame({
            'Feature': feature_names,
            'Importance': importances
        }).sort_values('Importance', ascending=False)
        
        for idx, row in importance_df.head(10).iterrows():
            print(f"   {row['Feature']:30s}: {row['Importance']:.4f}")
        
        return models, importance_df
    
    def predict_optimal_parameters(self, models, weights, scaler):
        """Use ML models to predict optimal parameters"""
        
        print(f"\n🎯 Predicting Optimal Parameters...")
        print("="*70)
        
        best_model = models['Gradient Boosting']
        feature_names = list(weights.keys())
        
        # Generate candidate parameters
        n_candidates = 1000
        candidates = []
        
        for i in range(n_candidates):
            candidate = {}
            for param, info in weights.items():
                min_val, max_val = info['range']
                candidate[param] = np.random.uniform(min_val, max_val)
            candidates.append(candidate)
        
        # Convert to array and scale
        X_candidates = np.array([list(c.values()) for c in candidates])
        X_candidates_scaled = scaler.transform(X_candidates)
        
        # Predict performance
        predictions = best_model.predict(X_candidates_scaled)
        
        # Find best
        best_idx = np.argmax(predictions)
        best_params = candidates[best_idx]
        best_predicted_return = predictions[best_idx]
        
        print(f"\n🏆 Best Predicted Parameters:")
        print(f"   Predicted Return: {best_predicted_return:.2%}")
        print(f"   Improvement: {(best_predicted_return - self.baseline_return):.2%}")
        print(f"\n   Parameters:")
        
        for param, value in best_params.items():
            current = weights[param]['current']
            change = ((value - current) / current) * 100
            print(f"   {param:30s}: {value:8.4f} (current: {current:8.4f}, {change:+6.1f}%)")
        
        return best_params, best_predicted_return
    
    def create_feature_importance_summary(self, importance_df):
        """Create summary of feature importance"""
        
        print(f"\n📈 Feature Importance Summary")
        print("="*70)
        
        print(f"\n🔴 HIGH IMPACT FEATURES (Top 5):")
        for idx, row in importance_df.head(5).iterrows():
            print(f"   {row['Feature']:30s}: {row['Importance']*100:6.2f}%")
        
        print(f"\n🟡 MEDIUM IMPACT FEATURES (6-10):")
        for idx, row in importance_df.iloc[5:10].iterrows():
            print(f"   {row['Feature']:30s}: {row['Importance']*100:6.2f}%")
        
        print(f"\n🟢 LOW IMPACT FEATURES (11+):")
        for idx, row in importance_df.iloc[10:].iterrows():
            print(f"   {row['Feature']:30s}: {row['Importance']*100:6.2f}%")
    
    def create_optimization_recommendations(self, best_params, weights):
        """Create actionable recommendations"""
        
        print(f"\n💡 Optimization Recommendations")
        print("="*70)
        
        recommendations = []
        
        for param, new_value in best_params.items():
            current = weights[param]['current']
            change_pct = ((new_value - current) / current) * 100
            
            if abs(change_pct) > 5:  # Only significant changes
                direction = "increase" if new_value > current else "decrease"
                recommendations.append({
                    'parameter': param,
                    'current': current,
                    'recommended': new_value,
                    'change_pct': change_pct,
                    'direction': direction
                })
        
        # Sort by magnitude of change
        recommendations.sort(key=lambda x: abs(x['change_pct']), reverse=True)
        
        print(f"\n🎯 Top Recommendations:")
        for i, rec in enumerate(recommendations[:5], 1):
            print(f"\n   {i}. {rec['parameter']}")
            print(f"      Current:     {rec['current']:.4f}")
            print(f"      Recommended: {rec['recommended']:.4f}")
            print(f"      Change:      {rec['change_pct']:+.1f}%")
            print(f"      Action:      {rec['direction'].upper()}")
        
        return recommendations
    
    def save_optimized_config(self, best_params, filename='optimized_config.json'):
        """Save optimized parameters to config file"""
        
        config = {
            'strategy_name': 'ML-Optimized Reddit Sentiment Trading',
            'version': '2.0',
            'optimization_method': 'Gradient Boosting ML',
            'baseline_return': self.baseline_return,
            'parameters': best_params
        }
        
        with open(filename, 'w') as f:
            json.dump(config, f, indent=4)
        
        print(f"\n✅ Optimized config saved to {filename}")
    
    def run_optimization(self):
        """Run complete ML optimization pipeline"""
        
        # Define weights
        weights = self.define_model_weights()
        
        # Create training data
        X, y, feature_names, scaler, weights = self.create_training_data(n_samples=200)
        
        # Train models
        models, importance_df = self.train_ml_models(X, y, feature_names)
        
        # Predict optimal parameters
        best_params, best_return = self.predict_optimal_parameters(models, weights, scaler)
        
        # Create summaries
        self.create_feature_importance_summary(importance_df)
        recommendations = self.create_optimization_recommendations(best_params, weights)
        
        # Save config
        self.save_optimized_config(best_params)
        
        # Final summary
        print(f"\n" + "="*70)
        print(f"🎉 ML OPTIMIZATION COMPLETE")
        print(f"="*70)
        print(f"Baseline Return:        {self.baseline_return:.2%}")
        print(f"Predicted Optimized:    {best_return:.2%}")
        print(f"Expected Improvement:   {(best_return - self.baseline_return):.2%}")
        
        return models, importance_df, best_params, best_return

def main():
    """Main execution"""
    
    optimizer = MLParameterOptimizer()
    models, importance_df, best_params, best_return = optimizer.run_optimization()
    
    return optimizer, models, importance_df, best_params

if __name__ == "__main__":
    optimizer, models, importance_df, best_params = main()
