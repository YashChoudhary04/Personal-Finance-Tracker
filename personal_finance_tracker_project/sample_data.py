"""
Sample Data Generator for Personal Finance Tracker
This script generates sample transaction data for testing purposes
"""

import sqlite3
import random
from datetime import datetime, timedelta

def generate_sample_data():
    """Generate sample transaction data"""

    # Connect to database
    conn = sqlite3.connect('finance_tracker.db')
    cursor = conn.cursor()

    # Sample categories
    income_categories = ['Salary', 'Freelance', 'Investment', 'Gift', 'Other Income']
    expense_categories = ['Food', 'Transportation', 'Housing', 'Utilities', 
                         'Entertainment', 'Healthcare', 'Shopping', 'Education']

    # Sample descriptions
    income_descriptions = [
        'Monthly salary', 'Freelance project', 'Stock dividend', 
        'Birthday gift', 'Bonus payment', 'Side hustle'
    ]

    expense_descriptions = [
        'Grocery shopping', 'Gas station', 'Rent payment', 'Electric bill',
        'Movie tickets', 'Doctor visit', 'Online shopping', 'Course fee',
        'Restaurant dinner', 'Coffee shop', 'Uber ride', 'Phone bill'
    ]

    # Generate data for the last 6 months
    start_date = datetime.now() - timedelta(days=180)
    transactions = []

    for i in range(200):  # Generate 200 sample transactions
        # Random date within the last 6 months
        random_days = random.randint(0, 180)
        transaction_date = start_date + timedelta(days=random_days)
        date_str = transaction_date.strftime('%Y-%m-%d')

        # Random transaction type (70% expenses, 30% income)
        transaction_type = 'Expense' if random.random() < 0.7 else 'Income'

        if transaction_type == 'Income':
            category = random.choice(income_categories)
            description = random.choice(income_descriptions)
            amount = round(random.uniform(500, 5000), 2)  # Income range
        else:
            category = random.choice(expense_categories)
            description = random.choice(expense_descriptions)
            amount = round(random.uniform(10, 500), 2)  # Expense range

        transactions.append((date_str, transaction_type, category, description, amount))

    # Insert sample data
    cursor.executemany("""
        INSERT INTO transactions (date, type, category, description, amount)
        VALUES (?, ?, ?, ?, ?)
    """, transactions)

    conn.commit()
    conn.close()

    print(f"Generated {len(transactions)} sample transactions")
    print("Sample data has been added to the database!")

if __name__ == "__main__":
    generate_sample_data()
