# Cart total boundary simulator

This directory contains a local-only demonstration of defensive cart-total validation. It does not connect to a website, send HTTP requests, handle session cookies, or attempt to trigger an integer overflow.

## What it does

Checks whether adding a quantity at a given unit price would keep a simulated cart total within a configured limit, and rejects the operation before the total can exceed that limit.

## Run

Requires Python 3 and no third-party packages:

```text
python cart_overflow_solver.py
```

Enter amounts in integer cents. The default current total is `0` cents and the example limit is `100000` cents. Values are only used in the local calculation.

For example, a cart with a current total of `0`, a unit price of `250` cents, a quantity of `3`, and a limit of `100000` cents is accepted with a new total of `750` cents. A proposed addition that would exceed the configured limit is rejected.

## Defensive note

Production cart and checkout code should validate quantity bounds and perform checked arithmetic before persisting or using totals. The configured limit here is an illustrative application-level bound, not a platform integer ceiling.
