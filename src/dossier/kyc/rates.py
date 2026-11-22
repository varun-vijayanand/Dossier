"""Currency conversion table implied by the IBM HI-Small dataset.

The transactions carry amounts in their own currency and the dataset has no
rate table. Each value is the median of amount_received / amount_paid over
transactions paid in US dollars (units of that currency per 1 US dollar),
measured after migration 0005 restored the Bitcoin decimals. These are the
simulation's own rates, not real-world ones.
"""

from decimal import Decimal

RATES_PER_USD: dict[str, Decimal] = {
    "US Dollar": Decimal(1),
    "Euro": Decimal("0.8534"),
    "Yuan": Decimal("6.6976"),
    "Swiss Franc": Decimal("0.9150"),
    "UK Pound": Decimal("0.7742"),
    "Rupee": Decimal("73.444"),
    "Shekel": Decimal("3.3770"),
    "Yen": Decimal("105.40"),
    "Ruble": Decimal("77.804"),
    "Canadian Dollar": Decimal("1.3193"),
    "Bitcoin": Decimal("0.000084215"),
    "Australian Dollar": Decimal("1.4128"),
    "Mexican Peso": Decimal("21.1431"),
    "Saudi Riyal": Decimal("3.7511"),
    "Brazil Real": Decimal("5.6465"),
}


def to_usd(amount: Decimal, currency: str) -> Decimal:
    """Convert an amount in the given currency to US dollars."""
    try:
        rate = RATES_PER_USD[currency]
    except KeyError:
        raise ValueError(f"no rate for currency {currency!r}") from None
    return amount / rate
