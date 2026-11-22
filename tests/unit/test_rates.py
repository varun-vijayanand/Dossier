from decimal import Decimal

import pytest

from dossier.kyc.rates import RATES_PER_USD, to_usd


def test_dollar_is_the_base_currency() -> None:
    assert to_usd(Decimal(250), "US Dollar") == Decimal(250)


def test_conversion_divides_by_the_rate() -> None:
    assert to_usd(Decimal("85.34"), "Euro") == Decimal(100)


def test_bitcoin_converts_to_a_plausible_dollar_price() -> None:
    assert Decimal(10000) < to_usd(Decimal(1), "Bitcoin") < Decimal(14000)


def test_unknown_currency_is_rejected() -> None:
    with pytest.raises(ValueError, match="no rate"):
        to_usd(Decimal(1), "Doubloon")


def test_all_rates_are_positive() -> None:
    assert len(RATES_PER_USD) == 15
    assert all(rate > 0 for rate in RATES_PER_USD.values())
