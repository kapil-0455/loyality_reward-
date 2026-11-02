
import pytest
from datetime import date

from backend.app.domain.inventory import check_inventory


def test_sufficient_stock():
    result = check_inventory(
        on_hand_stock=100,
        reserved_stock=20,
        required_quantity=10,
        minimum_stock_level=20,
    )

    assert result["eligible"] is True
    assert result["available_to_promise"] == 80


def test_insufficient_stock():
    result = check_inventory(
        on_hand_stock=20,
        reserved_stock=15,
        required_quantity=10,
    )

    assert result["eligible"] is False
    assert "INSUFFICIENT_STOCK" in result["reason_codes"]


def test_replenishment_available():
    result = check_inventory(
        on_hand_stock=20,
        reserved_stock=15,
        required_quantity=10,
        replenishment_date=date(2011, 12, 9),
        replenishment_quantity=10,
        evaluation_date=date(2011, 12, 10),
    )

    assert result["eligible"] is True


def test_replenishment_constraint():
    result = check_inventory(
        on_hand_stock=30,
        reserved_stock=0,
        required_quantity=10,
        minimum_stock_level=25,
    )

    assert result["eligible"] is False
    assert "REPLENISHMENT_CONSTRAINT" in result["reason_codes"]


def test_negative_stock():
    with pytest.raises(ValueError):
        check_inventory(
            on_hand_stock=-10,
            reserved_stock=0,
            required_quantity=5,
        )
