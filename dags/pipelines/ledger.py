import csv
import os
import random

from pipelines.s3_utils import upload_file_to_s3


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

    os.makedirs(STAGING_DIR, exist_ok=True)
    output_path = f"{STAGING_DIR}/internal_ledger_{ts_nodash}.csv"
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=LEDGER_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Created {len(rows)} transactions at {output_path}")

    upload_file_to_s3(output_path, f"internal_ledger/{ts_nodash}.csv")

    return output_path
