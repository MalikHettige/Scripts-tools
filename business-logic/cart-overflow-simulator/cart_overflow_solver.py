"""Local demonstration of rejecting cart totals beyond a configured limit."""


def calculate_cart_total(current_total_cents, unit_price_cents, quantity, max_total_cents):
    """Return the updated total, or reject inputs that exceed the configured limit."""
    values = (current_total_cents, unit_price_cents, quantity, max_total_cents)
    if any(value < 0 for value in values):
        raise ValueError("Amounts and quantities must not be negative.")
    if unit_price_cents == 0:
        raise ValueError("Unit price must be greater than zero.")
    if quantity == 0:
        raise ValueError("Quantity must be greater than zero.")
    if current_total_cents > max_total_cents:
        raise ValueError("Current total already exceeds the configured limit.")

    remaining_cents = max_total_cents - current_total_cents
    if quantity > remaining_cents // unit_price_cents:
        raise ValueError("Cart total would exceed the configured limit.")

    return current_total_cents + unit_price_cents * quantity


def main():
    print("Local cart-total validation demo (no network requests are made).")
    try:
        current = int(input("Current total in cents (default 0): ").strip() or "0")
        price = int(input("Unit price in cents: ").strip())
        quantity = int(input("Quantity to add: ").strip())
        ceiling = int(input("Configured total limit in cents (default 100000): ").strip() or "100000")
        total = calculate_cart_total(current, price, quantity, ceiling)
    except ValueError as error:
        print(f"Rejected: {error}")
        return

    print(f"Accepted. New cart total: {total} cents.")


if __name__ == "__main__":
    main()
