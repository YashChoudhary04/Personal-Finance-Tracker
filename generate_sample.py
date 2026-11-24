from pathlib import Path
import random
import pandas as pd
from datetime import date

random.seed(42)
rows = []
descriptions = {
    "Income": [("Monthly salary", "Salary"), ("Freelance project", "Freelance"), ("Interest credit", "Other")],
    "Expense": [("Groceries", "Food"), ("Cab fare", "Transport"), ("Online purchase", "Shopping"),
                ("House rent", "Rent"), ("Electricity bill", "Bills"), ("Medicine", "Health"),
                ("Movie tickets", "Entertainment"), ("Online course", "Education")]
}
for i in range(1000):
    kind = "Income" if random.random() < 0.22 else "Expense"
    desc, cat = random.choice(descriptions[kind])
    amount = round(random.uniform(15000, 65000), 2) if kind == "Income" else round(random.uniform(80, 6500), 2)
    day = date(2025, 1, 1).toordinal() + random.randint(0, 364)
    rows.append({
        "transaction_date": date.fromordinal(day).isoformat(),
        "description": desc,
        "category": cat,
        "transaction_type": kind,
        "amount": amount,
        "payment_method": random.choice(["UPI", "Cash", "Card", "Bank Transfer"])
    })
out = Path(__file__).parent / "data" / "sample_transactions.csv"
out.parent.mkdir(exist_ok=True)
pd.DataFrame(rows).to_csv(out, index=False)
print(f"Created {len(rows)} sample transactions at {out}")
