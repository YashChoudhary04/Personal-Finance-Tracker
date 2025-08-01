"""
Personal Finance Tracker - Main Application
Author: [Your Name]
Description: A comprehensive personal finance management system with GUI and data visualization
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkinter
from datetime import datetime, timedelta
import json

class FinanceTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Personal Finance Tracker")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')

        # Initialize database
        self.init_database()

        # Create GUI
        self.create_widgets()

        # Load data
        self.refresh_data()

    def init_database(self):
        """Initialize SQLite database"""
        self.conn = sqlite3.connect('finance_tracker.db')
        self.cursor = self.conn.cursor()

        # Create transactions table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                type TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                amount REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create budgets table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                monthly_limit REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.conn.commit()

    def create_widgets(self):
        """Create the main GUI components"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Create tabs
        self.create_entry_tab()
        self.create_view_tab()
        self.create_analytics_tab()

    def create_entry_tab(self):
        """Create transaction entry tab"""
        self.entry_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.entry_frame, text="Add Transaction")

        # Main container
        main_container = ttk.Frame(self.entry_frame)
        main_container.pack(fill='both', expand=True, padx=20, pady=20)

        # Title
        title_label = ttk.Label(main_container, text="Add New Transaction", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))

        # Date
        ttk.Label(main_container, text="Date:").grid(row=1, column=0, sticky='w', pady=5)
        self.date_var = tk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
        date_entry = ttk.Entry(main_container, textvariable=self.date_var, width=20)
        date_entry.grid(row=1, column=1, sticky='w', pady=5)

        # Type
        ttk.Label(main_container, text="Type:").grid(row=2, column=0, sticky='w', pady=5)
        self.type_var = tk.StringVar()
        type_combo = ttk.Combobox(main_container, textvariable=self.type_var, 
                                 values=['Income', 'Expense'], width=17)
        type_combo.grid(row=2, column=1, sticky='w', pady=5)
        type_combo.bind('<<ComboboxSelected>>', self.update_categories)

        # Category
        ttk.Label(main_container, text="Category:").grid(row=3, column=0, sticky='w', pady=5)
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(main_container, textvariable=self.category_var, width=17)
        self.category_combo.grid(row=3, column=1, sticky='w', pady=5)

        # Description
        ttk.Label(main_container, text="Description:").grid(row=4, column=0, sticky='w', pady=5)
        self.description_var = tk.StringVar()
        desc_entry = ttk.Entry(main_container, textvariable=self.description_var, width=20)
        desc_entry.grid(row=4, column=1, sticky='w', pady=5)

        # Amount
        ttk.Label(main_container, text="Amount ($):").grid(row=5, column=0, sticky='w', pady=5)
        self.amount_var = tk.StringVar()
        amount_entry = ttk.Entry(main_container, textvariable=self.amount_var, width=20)
        amount_entry.grid(row=5, column=1, sticky='w', pady=5)

        # Buttons
        button_frame = ttk.Frame(main_container)
        button_frame.grid(row=6, column=0, columnspan=2, pady=20)

        add_btn = ttk.Button(button_frame, text="Add Transaction", 
                            command=self.add_transaction)
        add_btn.pack(side='left', padx=5)

        clear_btn = ttk.Button(button_frame, text="Clear Fields", 
                              command=self.clear_fields)
        clear_btn.pack(side='left', padx=5)

    def update_categories(self, event=None):
        """Update category dropdown based on transaction type"""
        if self.type_var.get() == 'Income':
            categories = ['Salary', 'Freelance', 'Investment', 'Gift', 'Other Income']
        else:
            categories = ['Food', 'Transportation', 'Housing', 'Utilities', 
                         'Entertainment', 'Healthcare', 'Shopping', 'Education', 
                         'Insurance', 'Other Expense']

        self.category_combo['values'] = categories

    def add_transaction(self):
        """Add new transaction to database"""
        try:
            # Validate inputs
            if not all([self.date_var.get(), self.type_var.get(), 
                       self.category_var.get(), self.amount_var.get()]):
                messagebox.showerror("Error", "Please fill all required fields")
                return

            amount = float(self.amount_var.get())

            # Insert into database
            self.cursor.execute("""
                INSERT INTO transactions (date, type, category, description, amount)
                VALUES (?, ?, ?, ?, ?)
            """, (self.date_var.get(), self.type_var.get(), self.category_var.get(),
                  self.description_var.get(), amount))

            self.conn.commit()
            messagebox.showinfo("Success", "Transaction added successfully!")
            self.clear_fields()
            self.refresh_data()

        except ValueError:
            messagebox.showerror("Error", "Please enter a valid amount")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def clear_fields(self):
        """Clear all input fields"""
        self.date_var.set(datetime.now().strftime('%Y-%m-%d'))
        self.type_var.set('')
        self.category_var.set('')
        self.description_var.set('')
        self.amount_var.set('')

    def create_view_tab(self):
        """Create transaction view tab"""
        self.view_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.view_frame, text="View Transactions")

        # Controls frame
        controls_frame = ttk.Frame(self.view_frame)
        controls_frame.pack(fill='x', padx=10, pady=10)

        # Filter controls
        ttk.Label(controls_frame, text="Filter by Type:").pack(side='left', padx=5)
        self.filter_type = tk.StringVar(value='All')
        filter_combo = ttk.Combobox(controls_frame, textvariable=self.filter_type,
                                   values=['All', 'Income', 'Expense'], width=10)
        filter_combo.pack(side='left', padx=5)
        filter_combo.bind('<<ComboboxSelected>>', lambda e: self.refresh_data())

        # Export button
        export_btn = ttk.Button(controls_frame, text="Export to CSV", 
                               command=self.export_data)
        export_btn.pack(side='right', padx=5)

        # Refresh button
        refresh_btn = ttk.Button(controls_frame, text="Refresh", 
                                command=self.refresh_data)
        refresh_btn.pack(side='right', padx=5)

        # Treeview for transactions
        columns = ('Date', 'Type', 'Category', 'Description', 'Amount')
        self.tree = ttk.Treeview(self.view_frame, columns=columns, show='headings')

        for col in columns:
            self.tree.heading(col, text=col)
            if col == 'Amount':
                self.tree.column(col, width=100, anchor='e')
            else:
                self.tree.column(col, width=120)

        # Scrollbars
        v_scroll = ttk.Scrollbar(self.view_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=v_scroll.set)

        # Pack treeview and scrollbars
        self.tree.pack(side='left', fill='both', expand=True, padx=(10, 0), pady=10)
        v_scroll.pack(side='right', fill='y', padx=(0, 10), pady=10)

    def create_analytics_tab(self):
        """Create analytics tab"""
        self.analytics_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.analytics_frame, text="Analytics")

        # Summary labels
        summary_frame = ttk.LabelFrame(self.analytics_frame, text="Financial Summary")
        summary_frame.pack(fill='x', padx=10, pady=10)

        self.total_income_label = ttk.Label(summary_frame, text="Total Income: $0.00", 
                                           font=('Arial', 12, 'bold'))
        self.total_income_label.pack(pady=5)

        self.total_expense_label = ttk.Label(summary_frame, text="Total Expenses: $0.00", 
                                            font=('Arial', 12, 'bold'))
        self.total_expense_label.pack(pady=5)

        self.net_balance_label = ttk.Label(summary_frame, text="Net Balance: $0.00", 
                                          font=('Arial', 12, 'bold'))
        self.net_balance_label.pack(pady=5)

        # Update button
        update_btn = ttk.Button(self.analytics_frame, text="Update Summary", 
                               command=self.update_summary)
        update_btn.pack(pady=10)

    def refresh_data(self):
        """Refresh transaction data in treeview"""
        # Clear existing data
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Get filtered data
        filter_type = self.filter_type.get()
        if filter_type == 'All':
            query = "SELECT date, type, category, description, amount FROM transactions ORDER BY date DESC"
            params = ()
        else:
            query = "SELECT date, type, category, description, amount FROM transactions WHERE type = ? ORDER BY date DESC"
            params = (filter_type,)

        self.cursor.execute(query, params)
        transactions = self.cursor.fetchall()

        # Insert data into treeview
        for transaction in transactions:
            date, trans_type, category, description, amount = transaction
            amount_str = f"${amount:.2f}"
            self.tree.insert('', 'end', values=(date, trans_type, category, description, amount_str))

    def export_data(self):
        """Export transaction data to CSV"""
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )

            if file_path:
                df = pd.read_sql_query("SELECT * FROM transactions", self.conn)
                df.to_csv(file_path, index=False)
                messagebox.showinfo("Success", f"Data exported to {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {str(e)}")

    def update_summary(self):
        """Update financial summary"""
        try:
            # Get totals
            self.cursor.execute("SELECT SUM(amount) FROM transactions WHERE type = 'Income'")
            total_income = self.cursor.fetchone()[0] or 0

            self.cursor.execute("SELECT SUM(amount) FROM transactions WHERE type = 'Expense'")
            total_expense = self.cursor.fetchone()[0] or 0

            net_balance = total_income - total_expense

            # Update labels
            self.total_income_label.config(text=f"Total Income: ${total_income:.2f}")
            self.total_expense_label.config(text=f"Total Expenses: ${total_expense:.2f}")

            # Color code net balance
            color = 'green' if net_balance >= 0 else 'red'
            self.net_balance_label.config(text=f"Net Balance: ${net_balance:.2f}", foreground=color)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to update summary: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = FinanceTracker(root)
    root.mainloop()
