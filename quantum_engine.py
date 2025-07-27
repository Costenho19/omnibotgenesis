from __future__ import annotations
import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Optional

@dataclass
class QuantumPrediction:
    mean_return: float
    p50: float
    p90: float
    var_95: float
    next_price: float
    scenarios: np.ndarray

@dataclass
class PortfolioOptimizationResult:
    weights: pd.Series
    exp_return: float
    exp_risk: float
    sharpe: float

class QuantumEngine:
    def __init__(self, historical_data: pd.DataFrame):
        self.historical_data = historical_data

    def simulate_quantum_predictions(self) -> QuantumPrediction:
        returns = self.historical_data['Close'].pct_change().dropna()
        mean_return = returns.mean()
        std_dev = returns.std()
        scenarios = np.random.normal(mean_return, std_dev, 1000)

        p50 = np.percentile(scenarios, 50)
        p90 = np.percentile(scenarios, 90)
        var_95 = np.percentile(scenarios, 5)
        last_price = self.historical_data['Close'].iloc[-1]
        next_price = last_price * (1 + p50)

        return QuantumPrediction(
            mean_return=mean_return,
            p50=p50,
            p90=p90,
            var_95=var_95,
            next_price=next_price,
            scenarios=scenarios
        )

    def optimize_portfolio(self, assets_data: dict[str, pd.DataFrame]) -> PortfolioOptimizationResult:
        returns = {symbol: data['Close'].pct_change().dropna() for symbol, data in assets_data.items()}
        returns_df = pd.DataFrame(returns)
        mean_returns = returns_df.mean()
        cov_matrix = returns_df.cov()

        num_assets = len(mean_returns)
        weights = np.random.random(num_assets)
        weights /= np.sum(weights)

        exp_return = np.dot(weights, mean_returns)
        exp_risk = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        sharpe_ratio = exp_return / exp_risk if exp_risk != 0 else 0

        return PortfolioOptimizationResult(
            weights=pd.Series(weights, index=mean_returns.index),
            exp_return=exp_return,
            exp_risk=exp_risk,
            sharpe=sharpe_ratio
        )

