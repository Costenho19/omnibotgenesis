
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf
import datetime
import tempfile

# ========== MONTECARLO PREDICT ==========
def montecarlo_predict(symbol: str, days: int = 30, simulations: int = 1000):
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=365)
    data = yf.download(symbol, start=start_date, end=end_date)

    if data.empty:
        raise ValueError(f"No se encontraron datos para el símbolo {symbol}")

    close_prices = data['Close']
    log_returns = np.log(close_prices / close_prices.shift(1)).dropna()
    mean_return = log_returns.mean()
    std_dev = log_returns.std()
    last_price = close_prices.iloc[-1]

    simulations_matrix = np.zeros((days, simulations))
    for i in range(simulations):
        prices = [last_price]
        for _ in range(days):
            drift = mean_return - (0.5 * std_dev**2)
            shock = np.random.normal(loc=0, scale=std_dev)
            price = prices[-1] * np.exp(drift + shock)
            prices.append(price)
        simulations_matrix[:, i] = prices[1:]

    # Graficar
    plt.figure(figsize=(10, 5))
    plt.plot(simulations_matrix, color='gray', alpha=0.1)
    plt.title(f"Simulación Monte Carlo: {symbol}")
    plt.xlabel("Días")
    plt.ylabel("Precio estimado")
    plt.grid(True)

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    plt.savefig(temp_file.name)
    plt.close()

    return temp_file.name  # Ruta del gráfico generado

# ========== QUANTUM PORTFOLIO ANALYSIS ==========
def quantum_portfolio_analysis(symbols: list):
    resultados = []
    for symbol in symbols:
        try:
            data = yf.download(symbol, period="6mo", interval="1d")
            returns = data['Close'].pct_change().dropna()
            media = returns.mean()
            volatilidad = returns.std()
            resultados.append({
                "activo": symbol,
                "retorno_medio": round(media * 100, 2),
                "riesgo": round(volatilidad * 100, 2)
            })
        except:
            resultados.append({
                "activo": symbol,
                "retorno_medio": "Error",
                "riesgo": "Error"
            })
    return resultados
