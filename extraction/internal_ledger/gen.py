
import random

from faker import Faker

# Initialize Faker

fake = Faker()

# Number of transactions

NUM_ROWS = 30

# ---------------------------------

# ---------------------------------

# 1. Clients

# ---------------------------------

clients = [f"C{i:03d}" for i in range(1, 21)]

arabic_names = [

    "Ahmed",

    "Mohammed",

    "Abdullah",

    "Omar",

    "Khalid",

    "Faisal",

    "Saad",

    "Nasser",

    "Yousef",

    "Ibrahim",

    "Sara",

    "Noura",

    "Huda",

    "Reem",

    "Lama",

    "Aisha",

    "Maha",

    "Rana",

    "Fatimah",

    "Amal"

]

client_data = {

    client_id: {

        "client_name": name

    }

    for client_id, name in zip(clients, arabic_names)

}

# ---------------------------------

# 2. Portfolios

# ---------------------------------

portfolios = [f"P{i:03d}" for i in range(1, 11)]

# ---------------------------------

# 3. Assets / Tickers

# ---------------------------------

assets = {

    # Public Equity

    "IBM": "USD",

    "AAPL": "USD",

    "MSFT": "USD",

    "GOOGL": "USD",

    "AMZN": "USD",

    "SAP": "EUR",

    "VOD": "GBP",

    "HSBA.L": "GBP",

    "NESN.SW": "CHF",

    "2222.SR": "SAR",

    # Precious Metals

    "XAU": "USD",   # Gold

    "XAG": "USD",   # Silver

    "XPT": "USD",   # Platinum

    "XPD": "USD"    # Palladium

}

# ---------------------------------

# 4. Create Transactions

# ---------------------------------

rows = []

for i in range(1, NUM_ROWS + 1):

    # Select client

    client_id = random.choice(clients)

    # Select ticker

    ticker = random.choice(list(assets.keys()))

    # Get currency

    currency = assets[ticker]

    # Select portfolio

    portfolio_id = random.choice(portfolios)

    # Transaction type

    transaction_type = random.choice(["BUY", "SELL"])

    # Quantity

    quantity = random.randint(1, 500)

    # Price

    price = round(

        random.uniform(10, 500),

        2

    )

    # ---------------------------------

    # Calculate Transaction Value

    # ---------------------------------

    transaction_value = round(

        price * quantity,

        2

    )

    # ---------------------------------

    # Calculate Fee

    # ---------------------------------

    fee = round(

        transaction_value * random.uniform(0.001, 0.005),

        2

    )

    # ---------------------------------

    # Calculate Total

    # ---------------------------------

    if transaction_type == "BUY":

        total = round(

            transaction_value + fee,

            2

        )

    else:

        total = round(

            -(transaction_value - fee),

            2

        )

    # ---------------------------------

    # Add Row

    # ---------------------------------

    rows.append({

        "transaction_id": f"T{i:05d}",

        "client_id": client_id,

        "client_name": client_data[client_id]["client_name"],

        "portfolio_id": portfolio_id,

        "ticker": ticker,

        "transaction_type": transaction_type,

        "quantity": quantity,

        "price": price,

        "currency": currency,

        "fee_amount": fee,

        "transaction_date": fake.date_between(

            start_date="-30d",

            end_date="today"

        ),

        "total": total

    })

# ---------------------------------

# 5. Create DataFrame

# ---------------------------------

df = pd.DataFrame(rows)

# ---------------------------------

# 6. Standardize Date

# ---------------------------------

df["transaction_date"] = pd.to_datetime(

    df["transaction_date"]

).dt.strftime("%Y-%m-%d")

# ---------------------------------

# 7. Save CSV

# ---------------------------------

df.to_csv(

    "internal_ledger.csv",

    index=False

)

# ---------------------------------

# 8. Display Results

# ---------------------------------

print("Internal Ledger generated successfully!")

print(f"Rows: {len(df)}")

print("\nColumns:")

print(df.columns.tolist())

print("\nFirst 5 rows:")

print(df.head())