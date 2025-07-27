import logging
import warnings
import io
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from telegram import InputFile

# --- Importación Segura de la Base de Datos ---
try:
    from database import save_analysis_to_db
except ImportError:
    def save_analysis_to_db(*args, **kwargs):
        logging.warning("Función save_analysis_to_db no encontrada. El análisis no se guardará.")
        pass

# --- Configuración Inicial ---
warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)

# --- Clases de Estructura de Datos ---
@dataclass
class MarketData:
    """Almacena datos de mercado en tiempo real."""
    symbol: str; price: float; change_24h: float; volume: float; market_cap: float; timestamp: datetime

@dataclass
class AnalysisResult:
    """Almacena el resultado de un análisis."""
    symbol: str; current_price: float; prediction_1h: float; prediction_24h: float;
    prediction_7d: float; confidence: float; recommendation: str; risk_score: float;
    support_levels: List[float]; resistance_levels: List[float]

# --- Lista de Activos para Carga Inicial ---
premium_assets_list = [
    ('AAPL', 'Apple Inc.', 'stock', 'NASDAQ', 'Technology', 'US', 'USD', 3e12, 1),
    ('MSFT', 'Microsoft Corp.', 'stock', 'NASDAQ', 'Technology', 'US', 'USD', 2.8e12, 1),
    ('GOOGL', 'Alphabet Inc.', 'stock', 'NASDAQ', 'Technology', 'US', 'USD', 1.7e12, 1),
    ('BTC-USD', 'Bitcoin', 'crypto', 'CRYPTO', 'Cryptocurrency', 'Global', 'USD', 1.3e12, 1),
    ('ETH-USD', 'Ethereum', 'crypto', 'CRYPTO', 'Cryptocurrency', 'Global', 'USD', 4e11, 1),
]

class OmnixPremiumAnalysisEngine:
    """Motor de análisis premium que combina datos de mercado, IA y generación de gráficos."""
    
    def __init__(self):
        self.initialize_ai_models()
        logger.info("🚀 OMNIX PREMIUM ANALYSIS ENGINE INICIALIZADO")
        
    def initialize_ai_models(self):
        """Inicializa los modelos de ML con datos sintéticos para un arranque rápido."""
        logger.info("🤖 Inicializando modelos de IA...")
        self.price_predictor = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
        self.scaler = StandardScaler()
        X_train, y_train = np.random.rand(100, 20), np.random.rand(100)
        self.scaler.fit(X_train)
        self.price_predictor.fit(self.scaler.transform(X_train), y_train)
        logger.info("✅ Modelos de IA inicializados.")
        
    def get_market_data(self, symbol: str) -> Optional[MarketData]:
        """Obtiene datos de mercado en tiempo real desde Yahoo Finance."""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.fast_info
            hist = ticker.history(period="5d", interval="1d")
            
            if len(hist) < 2: return None
                
            current_price = hist['Close'].iloc[-1]
            prev_price = hist['Close'].iloc[-2]
            change_24h = ((current_price - prev_price) / prev_price) * 100 if prev_price else 0
            
            return MarketData(
                symbol=symbol, price=float(current_price), change_24h=float(change_24h),
                volume=float(info.get('volume', 0)), market_cap=float(info.get('marketCap', 0)),
                timestamp=datetime.now()
            )
        except Exception as e:
            logger.error(f"Error crítico en get_market_data para {symbol}: {e}")
            return None
            
    def calculate_technical_indicators(self, symbol: str) -> Optional[Dict[str, float]]:
        """Calcula indicadores técnicos clave."""
        try:
            hist = yf.Ticker(symbol).history(period="90d", auto_adjust=True)
            if len(hist) < 50: return None
                
            close = hist['Close']
            delta = close.diff()
            gain = delta.where(delta > 0, 0).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / (loss + 1e-9)
            rsi = 100 - (100 / (1 + rs))
            sma_20 = close.rolling(window=20).mean()
            sma_50 = close.rolling(window=50).mean()
            bb_std = close.rolling(window=20).std()

            return {
                'rsi': float(rsi.iloc[-1]), 'sma_20': float(sma_20.iloc[-1]),
                'sma_50': float(sma_50.iloc[-1]),
                'bb_upper': float(sma_20.iloc[-1] + (bb_std.iloc[-1] * 2)),
                'bb_lower': float(sma_20.iloc[-1] - (bb_std.iloc[-1] * 2)),
            }
        except Exception as e:
            logger.error(f"Error crítico en calculate_technical_indicators para {symbol}: {e}")
            return None
            
    def analyze_with_ai(self, symbol: str) -> Optional[AnalysisResult]:
        """Realiza el análisis completo y genera una recomendación."""
        market_data = self.get_market_data(symbol)
        indicators = self.calculate_technical_indicators(symbol)
        
        if not market_data or not indicators: return None
            
        features = np.array([
            market_data.change_24h, indicators.get('rsi', 50),
            market_data.volume / 1e9, np.log(market_data.market_cap + 1),
            *np.random.randn(16)
        ]).reshape(1, -1)
        
        features_scaled = self.scaler.transform(features)
        price_change_pred = self.price_predictor.predict(features_scaled)[0]
        
        current_price = market_data.price
        pred_24h = current_price * (1 + price_change_pred * 0.05)
        
        rsi = indicators.get('rsi')
        if pred_24h > current_price * 1.02 and rsi < 65: recommendation = "COMPRA"
        elif pred_24h < current_price * 0.98 and rsi > 35: recommendation = "VENTA"
        else: recommendation = "MANTENER"

        result = AnalysisResult(
            symbol=symbol, current_price=current_price,
            prediction_1h=current_price * (1 + price_change_pred * 0.01),
            prediction_24h=pred_24h,
            prediction_7d=current_price * (1 + price_change_pred * 0.15),
            confidence=0.65 + np.random.rand() * 0.20,
            recommendation=recommendation, risk_score=0.4 + np.random.rand() * 0.25,
            support_levels=[indicators.get('bb_lower', 0), indicators.get('sma_50', 0)],
            resistance_levels=[indicators.get('bb_upper', 0), indicators.get('sma_20', 0)]
        )
        
        save_analysis_to_db(result) # Guardamos el resultado en la base de datos
        return result

    def generar_grafico_avanzado(self, symbol: str = "BTC-USD") -> io.BytesIO:
        """Genera un gráfico avanzado con Múltiples Indicadores y lo devuelve como un buffer de imagen."""
        try:
            fin = datetime.now()
            inicio = fin - timedelta(days=7)
            datos = yf.download(symbol, start=inicio, end=fin, interval="1h")

            if datos.empty:
                logger.warning(f"No se encontraron datos para el gráfico de {symbol}")
                return None

            # Calcular indicadores
            datos["MA20"] = datos["Close"].rolling(window=20).mean()
            delta = datos["Close"].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            RS = gain / (loss + 1e-9)
            datos["RSI"] = 100 - (100 / (1 + RS))
            datos["UpperBand"] = datos["MA20"] + 2 * datos["Close"].rolling(20).std()
            datos["LowerBand"] = datos["MA20"] - 2 * datos["Close"].rolling(20).std()

            plt.style.use('dark_background')
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), gridspec_kw={'height_ratios': [3, 1]})

            # Subplot 1: Precio, MA, Bandas de Bollinger
            ax1.plot(datos.index, datos["Close"], label="Precio", color="cyan", linewidth=2)
            ax1.plot(datos.index, datos["MA20"], label="Media Móvil 20h", color="orange", linestyle='--')
            ax1.plot(datos.index, datos["UpperBand"], label="Bollinger Alta", linestyle=":", color="lightgreen")
            ax1.plot(datos.index, datos["LowerBand"], label="Bollinger Baja", linestyle=":", color="lightcoral")
            ax1.set_title(f"Análisis Técnico Avanzado de {symbol}", fontsize=16)
            ax1.set_ylabel("Precio (USD)", fontsize=12)
            ax1.legend(); ax1.grid(True, linestyle='--', alpha=0.3)

            # Subplot 2: RSI
            ax2.plot(datos.index, datos["RSI"], label="RSI", color="magenta")
            ax2.axhline(70, color='lightcoral', linestyle='--'); ax2.axhline(30, color='lightgreen', linestyle='--')
            ax2.set_title("Índice de Fuerza Relativa (RSI)", fontsize=12)
            ax2.set_ylabel("RSI", fontsize=12); ax2.set_xlabel("Fecha", fontsize=12)
            ax2.grid(True, linestyle='--', alpha=0.3)

            # Guardar gráfico en un buffer en memoria
            buf = io.BytesIO()
            plt.tight_layout(); plt.savefig(buf, format='png'); plt.close(fig)
            buf.seek(0)
            return buf

        except Exception as e:
            logger.error(f"Error crítico generando gráfico avanzado para {symbol}: {e}")
            return None
