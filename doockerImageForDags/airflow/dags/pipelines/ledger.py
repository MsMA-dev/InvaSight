import csv
import os
import random

from pipelines.blob_utils import upload_file_to_blob


STAGING_DIR = "/opt/airflow/data/internal_ledger"
LEDGER_ROWS = 50000

CLIENT_NAMES = [
    "Khalid", "Saad", "Sara", "Omar", "Huda", "Aisha",
    "Faisal", "Maha", "Rana", "Amal", "Reem",
]

CLIENT_IDS = [f"C{i:03d}" for i in range(1, 21)]
PORTFOLIO_IDS = [f"P{i:03d}" for i in range(1, 11)]

TICKER_CURRENCY = {
    "VOD": "GBP",
    "2222.SR": "SAR",
    "SAP": "EUR",
    "IBM": "USD",
    "XAU": "USD",
    "NESN.SW": "CHF",
    "XAG": "USD",
    "XPT": "USD",
    "GOOGL": "USD",
    "MSFT": "USD",
}

TRANSACTION_TYPES = ["BUY", "SELL"]

LEDGER_COLUMNS = [
    "transaction_id",
    "client_id",
    "client_name",
    "portfolio_id",
    "ticker",
    "transaction_type",
    "quantity",
    "price",
    "currency",
    "fee_amount",
    "transaction_date",
    "transaction_ts",
    "total",
]


def validate_ledger(rows):
    """Fail fast if the generated ledger is incomplete or internally inconsistent."""
    if len(rows) != LEDGER_ROWS:
        raise ValueError(f"Expected {LEDGER_ROWS} rows, got {len(rows)}")

    for row in rows:
        for col in LEDGER_COLUMNS:
            if row.get(col) in (None, ""):
                raise ValueError(f"Missing {col} in row {row.get('transaction_id')}")

        if row["client_id"] not in CLIENT_IDS:
            raise ValueError(f"Unknown client_id {row['client_id']} in row {row['transaction_id']}")
        if row["portfolio_id"] not in PORTFOLIO_IDS:
            raise ValueError(f"Unknown portfolio_id {row['portfolio_id']} in row {row['transaction_id']}")
        if row["ticker"] not in TICKER_CURRENCY:
            raise ValueError(f"Unknown ticker {row['ticker']} in row {row['transaction_id']}")
        if row["currency"] != TICKER_CURRENCY[row["ticker"]]:
            raise ValueError(f"Currency mismatch for ticker {row['ticker']} in row {row['transaction_id']}")
        if row["transaction_type"] not in TRANSACTION_TYPES:
            raise ValueError(f"Unknown transaction_type {row['transaction_type']} in row {row['transaction_id']}")
        if row["quantity"] <= 0 or row["price"] <= 0 or row["fee_amount"] <= 0:
            raise ValueError(f"Non-positive quantity/price/fee_amount in row {row['transaction_id']}")

        gross_amount = row["quantity"] * row["price"]
        if row["transaction_type"] == "BUY":
            expected_total = gross_amount + row["fee_amount"]
        else:
            expected_total = -(gross_amount - row["fee_amount"])

        if round(expected_total, 2) != row["total"]:
            raise ValueError(
                f"Total mismatch in row {row['transaction_id']}: "
                f"expected {round(expected_total, 2)}, got {row['total']}"
            )

    print(f"Validated {len(rows)} rows.")


def generate_internal_ledger(data_interval_start, ts_nodash, **_):
    """Synthetic internal ledger for one 45-minute interval.

    Seeded from the interval start so a given run is reproducible on
    retry or backfill, while each interval produces different rows.
    """
    rng = random.Random(ts_nodash)

    transaction_ts = data_interval_start.isoformat()
    transaction_date = data_interval_start.strftime("%Y-%m-%d")

    rows = []
    for i in range(1, LEDGER_ROWS + 1):
        ticker = rng.choice(list(TICKER_CURRENCY.keys()))
        transaction_type = rng.choice(TRANSACTION_TYPES)

        quantity = rng.randint(9, 484)
        price = round(rng.uniform(66.06, 493.64), 2)
        fee_amount = round(rng.uniform(7.03, 636.55), 2)

        gross_amount = quantity * price
        if transaction_type == "BUY":
            total = gross_amount + fee_amount
        else:
            total = -(gross_amount - fee_amount)

        rows.append({
            "transaction_id": f"T{ts_nodash}{i:05d}",
            "client_id": rng.choice(CLIENT_IDS),
            "client_name": rng.choice(CLIENT_NAMES),
            "portfolio_id": rng.choice(PORTFOLIO_IDS),
            "ticker": ticker,
            "transaction_type": transaction_type,
            "quantity": quantity,
            "price": price,
            "currency": TICKER_CURRENCY[ticker],
            "fee_amount": fee_amount,
            "transaction_date": transaction_date,
            "transaction_ts": transaction_ts,
            "total": round(total, 2),
        })

    validate_ledger(rows)

    os.makedirs(STAGING_DIR, exist_ok=True)
    output_path = f"{STAGING_DIR}/internal_ledger_{ts_nodash}.csv"
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=LEDGER_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Created {len(rows)} transactions at {output_path}")

    upload_file_to_blob(output_path, f"internal_ledger/internal_ledger/{ts_nodash}.csv")

    return output_path
