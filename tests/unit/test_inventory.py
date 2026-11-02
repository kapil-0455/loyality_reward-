
import pytest

from backend.app.domain.inventory import check_inventory


def test_sufficient_inventory():
    result = check_inventory(
        on_hand_stock=100,
        reserved_stock=20,
        required_quantity=30,
        minimum_stock_level=10,
        evaluation_date="2011-12-10"
    )

    assert result["eligible"] is True
    assert result["available_to_promise"] == 80
    assert result["remaining_stock"] == 50
    assert result["reason_codes"] == []


def test_insufficient_inventory():
    result = check_inventory(
        on_hand_stock=50,
        reserved_stock=20,
        required_quantity=40,
        minimum_stock_level=5,
        evaluation_date="2011-12-10"
    )

    assert result["eligible"] is False
    assert "INSUFFICIENT_STOCK" in result["reason_codes"]


def test_minimum_stock_constraint():
    result = check_inventory(
        on_hand_stock=100,
        reserved_stock=20,
        required_quantity=75,
        minimum_stock_level=10,
        evaluation_date="2011-12-10"
    )

    assert result["eligible"] is False
    assert "REPLENISHMENT_CONSTRAINT" in result["reason_codes"]


def test_replenishment_available():
    result = check_inventory(
        on_hand_stock=50,
        reserved_stock=30,
        required_quantity=30,
        minimum_stock_level=10,
        replenishment_date="2011-12-10",
        replenishment_quantity=30,
        evaluation_date="2011-12-10"
    )

    assert result["eligible"] is True
    assert result["reason_codes"] == []


def test_future_replenishment_not_available():
    result = check_inventory(
        on_hand_stock=50,
        reserved_stock=30,
        required_quantity=30,
        minimum_stock_level=5,
        replenishment_date="2011-12-15",
        replenishment_quantity=50,
        evaluation_date="2011-12-10"
    )

    assert result["eligible"] is False
    assert "INSUFFICIENT_STOCK" in result["reason_codes"]


def test_reserved_stock_cannot_exceed_on_hand():
    with pytest.raises(ValueError):
        check_inventory(
            on_hand_stock=50,
            reserved_stock=60,
            required_quantity=10,
            evaluation_date="2011-12-10"
        )


def test_negative_stock_not_allowed():
    with pytest.raises(ValueError):
        check_inventory(
            on_hand_stock=-10,
            reserved_stock=0,
            required_quantity=5,
            evaluation_date="2011-12-10"
        )
