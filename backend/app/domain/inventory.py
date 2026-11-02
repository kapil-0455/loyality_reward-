
from datetime import date, datetime


def convert_to_date(value):
    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    return date.fromisoformat(str(value))


def check_inventory(
    on_hand_stock,
    reserved_stock,
    required_quantity,
    minimum_stock_level=0,
    replenishment_date=None,
    replenishment_quantity=0,
    evaluation_date=None
):
    reason_codes = []

    # 1. Calculate Available to Promise (ATP)
    available_to_promise = on_hand_stock - reserved_stock

    # 2. Validate stock values
    if min(
        on_hand_stock,
        reserved_stock,
        required_quantity,
        minimum_stock_level,
        replenishment_quantity
    ) < 0:
        raise ValueError("Stock and quantity values cannot be negative")

    if reserved_stock > on_hand_stock:
        raise ValueError("Reserved stock cannot exceed on-hand stock")

    # 3. Check whether current stock is sufficient
    if available_to_promise < required_quantity:

        # 4. Check replenishment availability
        replenishment_available = False

        if (
            replenishment_date is not None
            and evaluation_date is not None
        ):
            replenishment_date = convert_to_date(replenishment_date)
            evaluation_date = convert_to_date(evaluation_date)

            if (
                replenishment_date <= evaluation_date
                and available_to_promise + replenishment_quantity
                >= required_quantity
            ):
                replenishment_available = True

        if not replenishment_available:
            reason_codes.append("INSUFFICIENT_STOCK")

    # 5. Check minimum stock after fulfilment
    remaining_stock = available_to_promise - required_quantity

    if remaining_stock < minimum_stock_level:

        replenishment_can_restore_minimum = False

        if (
            replenishment_date is not None
            and evaluation_date is not None
        ):
            if (
                replenishment_date <= convert_to_date(evaluation_date)
                and remaining_stock + replenishment_quantity
                >= minimum_stock_level
            ):
                replenishment_can_restore_minimum = True

        if not replenishment_can_restore_minimum:
            reason_codes.append("REPLENISHMENT_CONSTRAINT")

    return {
        "eligible": len(reason_codes) == 0,
        "available_to_promise": available_to_promise,
        "remaining_stock": remaining_stock,
        "reason_codes": reason_codes
    }
