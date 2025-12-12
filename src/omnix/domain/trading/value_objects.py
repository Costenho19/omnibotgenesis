"""
OMNIX V7.0 Trading Value Objects
=================================
Immutable value objects for trading domain.

Value objects are immutable and compared by value, not identity.
They encapsulate validation and domain rules.
"""

from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN
from typing import Optional, Tuple
import re


@dataclass(frozen=True)
class Money:
    """
    Immutable monetary value with currency.
    
    Uses Decimal for precision in financial calculations.
    """
    amount: Decimal
    currency: str = "USD"
    
    def __post_init__(self):
        if not isinstance(self.amount, Decimal):
            object.__setattr__(self, 'amount', Decimal(str(self.amount)))
    
    @classmethod
    def zero(cls, currency: str = "USD") -> "Money":
        """Create zero money value."""
        return cls(Decimal("0"), currency)
    
    @classmethod
    def from_float(cls, value: float, currency: str = "USD") -> "Money":
        """Create Money from float value."""
        return cls(Decimal(str(value)), currency)
    
    def __add__(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError(f"Cannot add {self.currency} and {other.currency}")
        return Money(self.amount + other.amount, self.currency)
    
    def __sub__(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError(f"Cannot subtract {other.currency} from {self.currency}")
        return Money(self.amount - other.amount, self.currency)
    
    def __mul__(self, factor: float) -> "Money":
        return Money(self.amount * Decimal(str(factor)), self.currency)
    
    def __truediv__(self, divisor: float) -> "Money":
        return Money(self.amount / Decimal(str(divisor)), self.currency)
    
    def __lt__(self, other: "Money") -> bool:
        self._check_currency(other)
        return self.amount < other.amount
    
    def __le__(self, other: "Money") -> bool:
        self._check_currency(other)
        return self.amount <= other.amount
    
    def __gt__(self, other: "Money") -> bool:
        self._check_currency(other)
        return self.amount > other.amount
    
    def __ge__(self, other: "Money") -> bool:
        self._check_currency(other)
        return self.amount >= other.amount
    
    def _check_currency(self, other: "Money") -> None:
        if self.currency != other.currency:
            raise ValueError(f"Cannot compare {self.currency} and {other.currency}")
    
    def round(self, places: int = 2) -> "Money":
        """Round to specified decimal places."""
        quantize_str = "0." + "0" * places
        rounded = self.amount.quantize(Decimal(quantize_str), rounding=ROUND_DOWN)
        return Money(rounded, self.currency)
    
    def to_float(self) -> float:
        """Convert to float for external APIs."""
        return float(self.amount)
    
    def __str__(self) -> str:
        return f"{self.currency} {self.amount:.2f}"
    
    def __repr__(self) -> str:
        return f"Money({self.amount}, '{self.currency}')"


@dataclass(frozen=True)
class Quantity:
    """
    Immutable quantity value for trading amounts.
    
    Enforces non-negative values and precision rules.
    """
    value: Decimal
    precision: int = 8
    
    def __post_init__(self):
        if not isinstance(self.value, Decimal):
            object.__setattr__(self, 'value', Decimal(str(self.value)))
        if self.value < 0:
            raise ValueError("Quantity cannot be negative")
    
    @classmethod
    def zero(cls) -> "Quantity":
        """Create zero quantity."""
        return cls(Decimal("0"))
    
    @classmethod
    def from_float(cls, value: float, precision: int = 8) -> "Quantity":
        """Create Quantity from float value."""
        return cls(Decimal(str(value)), precision)
    
    def __add__(self, other: "Quantity") -> "Quantity":
        return Quantity(self.value + other.value, max(self.precision, other.precision))
    
    def __sub__(self, other: "Quantity") -> "Quantity":
        result = self.value - other.value
        if result < 0:
            raise ValueError("Quantity subtraction would result in negative value")
        return Quantity(result, max(self.precision, other.precision))
    
    def __mul__(self, factor: float) -> "Quantity":
        return Quantity(self.value * Decimal(str(factor)), self.precision)
    
    def __truediv__(self, divisor: float) -> "Quantity":
        return Quantity(self.value / Decimal(str(divisor)), self.precision)
    
    def __lt__(self, other: "Quantity") -> bool:
        return self.value < other.value
    
    def __le__(self, other: "Quantity") -> bool:
        return self.value <= other.value
    
    def __gt__(self, other: "Quantity") -> bool:
        return self.value > other.value
    
    def __ge__(self, other: "Quantity") -> bool:
        return self.value >= other.value
    
    def to_float(self) -> float:
        """Convert to float for external APIs."""
        return float(self.value)
    
    def __str__(self) -> str:
        return f"{self.value:.{self.precision}f}".rstrip('0').rstrip('.')
    
    def __repr__(self) -> str:
        return f"Quantity({self.value})"


@dataclass(frozen=True)
class SymbolPair:
    """
    Trading pair symbol with base and quote currencies.
    
    Handles multiple exchange format conventions.
    """
    base: str
    quote: str
    
    def __post_init__(self):
        object.__setattr__(self, 'base', self.base.upper())
        object.__setattr__(self, 'quote', self.quote.upper())
    
    @classmethod
    def from_string(cls, symbol: str) -> "SymbolPair":
        """
        Parse symbol from various formats:
        - BTC/USD
        - BTCUSD
        - BTC-USD
        - XXBTZUSD (Kraken format)
        """
        symbol = symbol.upper().strip()
        
        if "/" in symbol:
            parts = symbol.split("/")
            return cls(parts[0], parts[1])
        
        if "-" in symbol:
            parts = symbol.split("-")
            return cls(parts[0], parts[1])
        
        if symbol.startswith("XX") or symbol.startswith("XZ"):
            base = symbol[1:4] if symbol[1] == "X" else symbol[:3]
            quote = symbol[4:] if len(symbol) > 4 else "USD"
            base = cls._normalize_kraken(base)
            quote = cls._normalize_kraken(quote)
            return cls(base, quote)
        
        quote_currencies = ["USD", "EUR", "GBP", "USDT", "USDC", "BTC", "ETH"]
        for quote in quote_currencies:
            if symbol.endswith(quote):
                base = symbol[:-len(quote)]
                if base:
                    return cls(base, quote)
        
        if len(symbol) >= 6:
            return cls(symbol[:3], symbol[3:])
        
        raise ValueError(f"Cannot parse symbol: {symbol}")
    
    @staticmethod
    def _normalize_kraken(code: str) -> str:
        """Normalize Kraken currency codes."""
        mapping = {
            "XBT": "BTC",
            "XXBT": "BTC",
            "ZUSD": "USD",
            "ZEUR": "EUR",
            "XETH": "ETH",
            "XLTC": "LTC",
            "XXRP": "XRP",
        }
        return mapping.get(code, code)
    
    def to_kraken(self) -> str:
        """Convert to Kraken exchange format."""
        base = self.base
        quote = self.quote
        if base == "BTC":
            base = "XBT"
        return f"{base}/{quote}"
    
    def to_standard(self) -> str:
        """Convert to standard format (BASE/QUOTE)."""
        return f"{self.base}/{self.quote}"
    
    def to_compact(self) -> str:
        """Convert to compact format (BASEQUOTE)."""
        return f"{self.base}{self.quote}"
    
    def __str__(self) -> str:
        return self.to_standard()
    
    def __repr__(self) -> str:
        return f"SymbolPair('{self.base}', '{self.quote}')"


@dataclass(frozen=True)
class ConfidenceScore:
    """
    Confidence score for trading decisions.
    
    Normalized to 0.0-1.0 range with categorical interpretation.
    """
    value: float
    
    def __post_init__(self):
        if not 0.0 <= self.value <= 1.0:
            clamped = max(0.0, min(1.0, self.value))
            object.__setattr__(self, 'value', clamped)
    
    @classmethod
    def from_percent(cls, percent: float) -> "ConfidenceScore":
        """Create from percentage (0-100)."""
        return cls(percent / 100.0)
    
    @classmethod
    def high(cls) -> "ConfidenceScore":
        """Create high confidence (0.8)."""
        return cls(0.8)
    
    @classmethod
    def medium(cls) -> "ConfidenceScore":
        """Create medium confidence (0.5)."""
        return cls(0.5)
    
    @classmethod
    def low(cls) -> "ConfidenceScore":
        """Create low confidence (0.3)."""
        return cls(0.3)
    
    @property
    def category(self) -> str:
        """Categorical interpretation of confidence."""
        if self.value >= 0.8:
            return "very_high"
        elif self.value >= 0.65:
            return "high"
        elif self.value >= 0.5:
            return "medium"
        elif self.value >= 0.3:
            return "low"
        return "very_low"
    
    @property
    def is_actionable(self) -> bool:
        """Whether confidence is high enough for trading."""
        return self.value >= 0.5
    
    def to_percent(self) -> float:
        """Convert to percentage (0-100)."""
        return self.value * 100
    
    def __str__(self) -> str:
        return f"{self.value:.1%}"
    
    def __repr__(self) -> str:
        return f"ConfidenceScore({self.value:.3f})"
    
    def __lt__(self, other: "ConfidenceScore") -> bool:
        return self.value < other.value
    
    def __le__(self, other: "ConfidenceScore") -> bool:
        return self.value <= other.value
    
    def __gt__(self, other: "ConfidenceScore") -> bool:
        return self.value > other.value
    
    def __ge__(self, other: "ConfidenceScore") -> bool:
        return self.value >= other.value


@dataclass(frozen=True)
class PriceLevel:
    """
    Price level for entry, stop loss, or take profit.
    
    Includes optional trigger conditions and metadata.
    """
    price: Decimal
    label: str = ""
    is_triggered: bool = False
    
    def __post_init__(self):
        if not isinstance(self.price, Decimal):
            object.__setattr__(self, 'price', Decimal(str(self.price)))
    
    @classmethod
    def from_float(cls, price: float, label: str = "") -> "PriceLevel":
        """Create PriceLevel from float."""
        return cls(Decimal(str(price)), label)
    
    def to_float(self) -> float:
        """Convert to float for external APIs."""
        return float(self.price)
    
    def distance_from(self, current_price: float) -> float:
        """Calculate percentage distance from current price."""
        if current_price == 0:
            return 0.0
        return ((self.to_float() - current_price) / current_price) * 100
    
    def __str__(self) -> str:
        label_str = f" ({self.label})" if self.label else ""
        return f"{self.price:.8f}{label_str}"
    
    def __repr__(self) -> str:
        return f"PriceLevel({self.price}, '{self.label}')"
    
    def __lt__(self, other: "PriceLevel") -> bool:
        return self.price < other.price
    
    def __le__(self, other: "PriceLevel") -> bool:
        return self.price <= other.price
    
    def __gt__(self, other: "PriceLevel") -> bool:
        return self.price > other.price
    
    def __ge__(self, other: "PriceLevel") -> bool:
        return self.price >= other.price
