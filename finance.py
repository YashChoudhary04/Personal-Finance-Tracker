import sqlite3
import re
import math
import pandas as pd

CATEGORIES = {'Income':['Salary','Freelance','Interest','Other'], 'Expense':['Food','Transport','Shopping','Rent','Bills','Health','Entertainment','Education','Other']}
PAYMENTS = ['UPI','Cash','Card','Bank Transfer','Other']
FIELDS = ['transaction_date','description','category','transaction_type','amount','payment_method']
RULES = {'Salary':r'salary|payroll','Freelance':r'freelance|client payment','Interest':r'interest', 'Food':r'grocery|groceries|food|restaurant|swiggy|zomato|coffee|lunch|dinner', 'Transport':r'cab|uber|ola|fuel|metro|bus|petrol', 'Shopping':r'shopping|amazon|purchase|clothing', 'Rent':r'rent', 'Bills':r'bill|electricity|internet|recharge', 'Health':r'medicine|doctor|pharmacy|hospital', 'Entertainment':r'movie|netflix|cinema', 'Education':r'course|book|tuition'}

def categorize(description, kind):
    return next((c for c in CATEGORIES[kind] if c in RULES and re.search(RULES[c],description,re.I)), 'Other')

def setup(conn):
    conn.execute('PRAGMA foreign_keys=ON')
    with conn:
        conn.execute('BEGIN')
        columns = [r[1] for r in conn.execute('PRAGMA table_info(transactions)')]
        legacy = 'category' in columns
        if legacy:
            conn.execute('ALTER TABLE transactions RENAME TO legacy_transactions')
        conn.execute("CREATE TABLE IF NOT EXISTS categories (category_id INTEGER PRIMARY KEY, name TEXT NOT NULL, kind TEXT NOT NULL CHECK(kind IN ('Income','Expense')), UNIQUE(name,kind))")
        conn.execute('CREATE TABLE IF NOT EXISTS payment_methods (payment_id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE)')
        conn.execute('''CREATE TABLE IF NOT EXISTS transactions (transaction_id INTEGER PRIMARY KEY, transaction_date TEXT NOT NULL, description TEXT NOT NULL, category_id INTEGER NOT NULL REFERENCES categories(category_id), amount_paise INTEGER NOT NULL CHECK(amount_paise>0), payment_id INTEGER NOT NULL REFERENCES payment_methods(payment_id))''')
        for kind,cats in CATEGORIES.items():
            conn.executemany('INSERT OR IGNORE INTO categories(name,kind) VALUES (?,?)',[(c,kind) for c in cats])
        conn.executemany('INSERT OR IGNORE INTO payment_methods(name) VALUES (?)',[(p,) for p in PAYMENTS])
        if legacy:
            for row in conn.execute('SELECT transaction_date,description,category,transaction_type,amount,payment_method FROM legacy_transactions').fetchall():
                d,desc,cat,kind,amount,pay=row
                if cat not in CATEGORIES[kind]: cat=categorize(desc,kind)
                insert(conn,(d,desc,cat,kind,amount,pay if pay in PAYMENTS else 'Other'))
            conn.execute('DROP TABLE legacy_transactions')

def insert(conn,row,tid=None):
    d,desc,cat,kind,amount,pay=row
    cid=conn.execute('SELECT category_id FROM categories WHERE name=? AND kind=?',(cat,kind)).fetchone()[0]
    pid=conn.execute('SELECT payment_id FROM payment_methods WHERE name=?',(pay,)).fetchone()[0]
    vals=(d,desc,cid,round(float(amount)*100),pid)
    if tid is None: conn.execute('INSERT INTO transactions(transaction_date,description,category_id,amount_paise,payment_id) VALUES (?,?,?,?,?)',vals)
    else: conn.execute('UPDATE transactions SET transaction_date=?,description=?,category_id=?,amount_paise=?,payment_id=? WHERE transaction_id=?',(*vals,int(tid)))

def load(conn):
    return pd.read_sql_query('''SELECT t.transaction_id,t.transaction_date,t.description,c.name AS category,c.kind AS transaction_type,t.amount_paise/100.0 AS amount,p.name AS payment_method FROM transactions t JOIN categories c ON c.category_id=t.category_id JOIN payment_methods p ON p.payment_id=t.payment_id ORDER BY t.transaction_date DESC,t.transaction_id DESC''',conn)

def key(row):
    d,desc,cat,kind,amount,pay=row
    return (str(d),str(desc).strip().casefold(),kind,round(float(amount)*100),pay)

def import_csv(conn,df):
    required={'transaction_date','description','transaction_type','amount'}
    if not required.issubset(df.columns): raise ValueError('Missing columns: '+', '.join(sorted(required-set(df.columns))))
    df=df.copy()
    df['transaction_date']=pd.to_datetime(df['transaction_date'],errors='coerce').dt.strftime('%Y-%m-%d')
    df['amount']=pd.to_numeric(df['amount'],errors='coerce')
    df['description']=df['description'].fillna('').astype(str).str.strip()
    df['transaction_type']=df['transaction_type'].fillna('').astype(str).str.strip().str.title()
    seen={key(r) for r in load(conn)[FIELDS].itertuples(index=False,name=None)}
    added=invalid=duplicates=0
    with conn:
        for r in df.to_dict('records'):
            d,desc,kind,amount=r['transaction_date'],r['description'],r['transaction_type'],r['amount']
            if pd.isna(d) or not desc or kind not in CATEGORIES or pd.isna(amount) or not math.isfinite(amount) or not 0.01<=amount<=1e12:
                invalid+=1; continue
            cat=str(r.get('category','')).strip().title()
            if cat not in CATEGORIES[kind]: cat=categorize(desc,kind)
            pay=str(r.get('payment_method','Other')).strip()
            pay=next((p for p in PAYMENTS if p.casefold()==pay.casefold()),'Other')
            row=(d,desc,cat,kind,amount,pay)
            k=key(row)
            if k in seen: duplicates+=1; continue
            insert(conn,row); seen.add(k); added+=1
    return added,invalid,duplicates
