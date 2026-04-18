"""
OMNIX Symbol Classifier V6.3
Intelligent detection of crypto vs stock symbols
"""

import logging
from typing import Tuple, Literal

logger = logging.getLogger(__name__)

CRYPTO_SYMBOLS = {
    'BTC', 'ETH', 'XRP', 'SOL', 'ADA', 'DOGE', 'DOT', 'AVAX', 'LINK', 'MATIC',
    'UNI', 'ATOM', 'LTC', 'ETC', 'XLM', 'ALGO', 'VET', 'FIL', 'AAVE', 'EOS',
    'AXS', 'SAND', 'MANA', 'ENJ', 'CHZ', 'GALA', 'THETA', 'EGLD', 'HBAR', 'XTZ',
    'NEAR', 'FTM', 'RUNE', 'KSM', 'FLOW', 'ZEC', 'DASH', 'WAVES', 'NEO', 'IOTA',
    'KAVA', 'ZIL', 'BAT', 'COMP', 'SNX', 'CRV', 'YFI', 'SUSHI', 'MKR', 'GRT',
    'PEPE', 'SHIB', 'FLOKI', 'BONK', 'WIF', 'ARB', 'OP', 'SUI', 'APT', 'INJ',
    'TIA', 'SEI', 'PYTH', 'JTO', 'JUP', 'RENDER', 'FET', 'AGIX', 'OCEAN', 'WLD',
    'JASMY', 'RNDR', 'IMX', 'BLUR', 'APE', 'LDO', 'RPL', 'GMX', 'DYDX', 'STX',
    'KAS', 'TAO', 'TRX', 'XMR', 'BCH', 'BSV', 'TON', 'ICP', 'CKB', 'CFX',
    'BITCOIN', 'ETHEREUM', 'LITECOIN', 'RIPPLE', 'DOGECOIN', 'SOLANA', 'CARDANO',
    'POLKADOT', 'CHAINLINK', 'POLYGON', 'UNISWAP', 'COSMOS', 'AVALANCHE'
}

STOCK_SUFFIXES = {'USD', 'USDT', 'USDC', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD'}

POPULAR_STOCKS = {
    'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK.A', 'BRK.B',
    'V', 'JNJ', 'WMT', 'JPM', 'PG', 'UNH', 'MA', 'HD', 'CVX', 'MRK',
    'ABBV', 'KO', 'PEP', 'BAC', 'PFE', 'COST', 'TMO', 'LLY', 'AVGO', 'CSCO',
    'DHR', 'MCD', 'NKE', 'ACN', 'ABT', 'WFC', 'VZ', 'TXN', 'CRM', 'ADBE',
    'PM', 'AMD', 'RTX', 'NEE', 'UPS', 'T', 'QCOM', 'INTC', 'MS', 'ORCL',
    'HON', 'BMY', 'NFLX', 'LOW', 'CAT', 'GS', 'UNP', 'AMGN', 'SBUX', 'BLK',
    'DE', 'ELV', 'SPGI', 'SCHW', 'ADP', 'IBM', 'INTU', 'GE', 'GILD', 'MDLZ',
    'CVS', 'PLD', 'AMT', 'C', 'CI', 'PYPL', 'DUK', 'SO', 'CB', 'ISRG',
    'ZTS', 'REGN', 'VRTX', 'BDX', 'CME', 'MO', 'MMC', 'CL', 'TGT', 'SYK',
    'ABNB', 'COIN', 'PLTR', 'SNOW', 'RBLX', 'RIVN', 'LCID', 'SOFI', 'HOOD', 'DKNG',
    'NET', 'CRWD', 'ZS', 'OKTA', 'MDB', 'PANW', 'DDOG', 'TTD', 'U', 'BILL',
    'SPY', 'QQQ', 'DIA', 'IWM', 'VOO', 'VTI', 'ARKK', 'XLF', 'XLK', 'XLE',
    'APPLE', 'MICROSOFT', 'GOOGLE', 'AMAZON', 'NVIDIA', 'TESLA', 'FACEBOOK'
}


SymbolType = Literal['crypto', 'stock', 'unknown']


class SymbolClassifier:
    """Classifies symbols as crypto or stock with high accuracy"""
    
    def __init__(self):
        self.crypto_set = CRYPTO_SYMBOLS
        self.stock_set = POPULAR_STOCKS
    
    def classify(self, symbol: str) -> Tuple[SymbolType, float]:
        """
        Classify a symbol as crypto or stock
        
        Args:
            symbol: The symbol to classify (e.g., 'BTC', 'AAPL')
            
        Returns:
            Tuple of (type, confidence) where confidence is 0.0-1.0
        """
        if not symbol:
            return ('unknown', 0.0)
        
        original = symbol
        symbol = symbol.upper().strip()
        
        for suffix in STOCK_SUFFIXES:
            if symbol.endswith(suffix) and len(symbol) > len(suffix):
                base = symbol[:-len(suffix)]
                if base in self.crypto_set:
                    return ('crypto', 0.95)
        
        if '/' in symbol:
            base = symbol.split('/')[0]
            if base in self.crypto_set:
                return ('crypto', 0.98)
        
        if symbol in self.crypto_set:
            return ('crypto', 0.99)
        
        if symbol in self.stock_set:
            return ('stock', 0.99)
        
        if len(symbol) <= 4 and symbol.isalpha():
            if any(c in symbol for c in ['X', 'Z']) and len(symbol) == 3:
                return ('crypto', 0.6)
        
        if len(symbol) >= 1 and len(symbol) <= 5 and symbol.isalpha():
            if symbol[0] in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                return ('stock', 0.7)
        
        if any(term in symbol for term in ['COIN', 'TOKEN', 'SWAP', 'CHAIN', 'VERSE', 'INU', 'DAO']):
            return ('crypto', 0.8)
        
        return ('stock', 0.5)
    
    def is_crypto(self, symbol: str) -> bool:
        """Check if symbol is likely a cryptocurrency"""
        symbol_type, confidence = self.classify(symbol)
        return symbol_type == 'crypto' and confidence >= 0.5
    
    def is_stock(self, symbol: str) -> bool:
        """Check if symbol is likely a stock"""
        symbol_type, confidence = self.classify(symbol)
        return symbol_type == 'stock' and confidence >= 0.5
    
    def get_routing_target(self, symbol: str) -> str:
        """
        Get the routing target for analysis commands
        
        Returns:
            'crypto' or 'stock' based on classification
        """
        symbol_type, confidence = self.classify(symbol)
        
        if symbol_type == 'crypto':
            logger.debug(f"🪙 {symbol} classified as CRYPTO (confidence: {confidence:.0%})")
            return 'crypto'
        else:
            logger.debug(f"📈 {symbol} classified as STOCK (confidence: {confidence:.0%})")
            return 'stock'


symbol_classifier = SymbolClassifier()


def classify_symbol(symbol: str) -> SymbolType:
    """Convenience function to classify a symbol"""
    symbol_type, _ = symbol_classifier.classify(symbol)
    return symbol_type


def get_routing_target(symbol: str) -> str:
    """Convenience function to get routing target"""
    return symbol_classifier.get_routing_target(symbol)
