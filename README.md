# Personal Finance Analytics
Python, SQLite, Pandas, Matplotlib and Streamlit. Tracks income, expenses and savings using a normalized database (transactions, categories, payment methods). CSV validation, keyword categorization, potential duplicate detection, editing, deletion, filtering and export. Amounts stored in integer paise. Demo data is synthetic, not real financial records.

Run `pip install -r requirements.txt` and `streamlit run app.py`. An existing starter `data/finance.db` is migrated automatically; back it up first. If no database exists, each Streamlit session uses a separate in-memory SQLite database seeded from `data/demo_transactions.csv`. Public demo changes are temporary; do not upload private records. Do not commit database or backup files. Duplicate detection is a heuristic and can flag legitimate identical transactions.

Deploy on Streamlit Community Cloud with `app.py` as entry point. Include the sample CSV, requirements and all source files. The sample generator is retained from the starter.
