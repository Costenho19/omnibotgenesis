import yfinance as yf

# ========== Obtener datos bursátiles de un activo específico ==========
def obtener_datos_bolsa(symbol: str):
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="1d")
        if data.empty:
            return f"No se encontraron datos para {symbol}."

        precio_actual = data["Close"].iloc[-1]
        apertura = data["Open"].iloc[-1]
        cambio = ((precio_actual - apertura) / apertura) * 100

        return (
            f"📊 Datos de {symbol.upper()}:\n"
            f"Precio actual: ${precio_actual:.2f}\n"
            f"Apertura: ${apertura:.2f}\n"
            f"Cambio: {cambio:.2f}%"
        )
    except Exception as e:
        return f"❌ Error al obtener datos de {symbol}: {str(e)}"

# ========== Resumen de índices internacionales ==========
def datos_financieros_internacionales():
    indices = {
        "^GSPC": "S&P 500",
        "^DJI": "Dow Jones",
        "^IXIC": "Nasdaq",
        "^FTSE": "FTSE 100",
        "^N225": "Nikkei 225",
        "^HSI": "Hang Seng",
        "^BVSP": "Bovespa"
    }

    resumen = "🌐 Índices Internacionales:\n"
    for symbol, nombre in indices.items():
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1d")
            if data.empty:
                continue
            precio = data["Close"].iloc[-1]
            apertura = data["Open"].iloc[-1]
            cambio = ((precio - apertura) / apertura) * 100
            resumen += f"{nombre}: {precio:.2f} ({cambio:+.2f}%)\n"
        except:
            resumen += f"{nombre}: Error\n"

    return resumen.strip()

