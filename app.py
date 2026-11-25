import sqlite3
from pathlib import Path
from datetime import date
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import streamlit as st
from finance import CATEGORIES,PAYMENTS,FIELDS,setup,load,insert,import_csv,categorize


st.set_page_config(page_title='Personal Finance Analytics',page_icon='📊',layout='wide')

st.markdown("""
<style>
    [data-testid="stMetricValue"],
    [data-testid="stMetricValue"] > div {
        font-size: 24px !important;
    }
</style>
""", unsafe_allow_html=True)

ROOT=Path(__file__).parent
DB=ROOT/'data'/'finance.db'

if 'finance_connection' not in st.session_state:
    local=DB.exists()
    conn=sqlite3.connect(str(DB) if local else ':memory:',check_same_thread=False)
    setup(conn)
    st.session_state.finance_connection=conn
    st.session_state.local_finance=local
conn=st.session_state.finance_connection
st.title('Personal Finance Analytics')
st.caption('Income • Spending • Savings | Python · SQLite · Pandas · Matplotlib')
if not st.session_state.local_finance: st.info('Demo workspace: isolated to this session. Changes are temporary. Use synthetic data only; do not upload private financial records.')
if 'notice' in st.session_state: st.success(st.session_state.pop('notice'))

def refresh(message):
    st.session_state.notice=message
    st.rerun()

with st.sidebar:
    st.header('Transaction entry')
    kind=st.selectbox('Type',['Expense','Income'])
    with st.form('add',clear_on_submit=True):
        d=st.date_input('Date',date.today())
        desc=st.text_input('Description')
        cat=st.selectbox('Category',['Auto detect']+CATEGORIES[kind])
        amount=st.number_input('Amount (₹)',min_value=0.01,max_value=1e12,step=100.0)
        pay=st.selectbox('Payment method',PAYMENTS)
        if st.form_submit_button('Save transaction'):
            if not desc.strip(): st.error('Description is required.')
            else:
                with conn: insert(conn,(d.isoformat(),desc.strip(),categorize(desc,kind) if cat=='Auto detect' else cat,kind,amount,pay))
                refresh('Transaction saved.')
    st.divider()
    st.header('CSV import')
    upload=st.file_uploader('Upload transactions',type=['csv'])
    if upload is not None and st.button('Import CSV'):
        try:
            a,b,c=import_csv(conn,pd.read_csv(upload))
            refresh(f'Imported: {a} | Invalid: {b} | Possible duplicates skipped: {c}')
        except Exception as e: st.error(f'Import failed: {e}')
    st.caption('Duplicate check uses date, description, type, amount and payment method. Identical legitimate payments may be flagged.')

    st.divider()
    st.header('Data management')
    if st.button('Load demo data', key='load_demo'):
        a,b,c=import_csv(conn,pd.read_csv(ROOT/'data'/'demo_transactions.csv'))
        for k in ('start_filter','end_filter'):
            st.session_state.pop(k,None)
        refresh(f'Demo data: {a} imported, {b} invalid, {c} possible duplicates skipped.')
    with st.expander('Reset all transactions'):
        st.warning('This permanently deletes all transactions in this workspace, not just filtered records. Categories and payment methods are preserved.')
        with st.form('reset_all',clear_on_submit=True):
            confirm=st.checkbox('I understand and want to delete all transactions.')
            if st.form_submit_button('Reset All Transactions',type='primary'):
                if not confirm:
                    st.error('Please tick the confirmation checkbox first.')
                else:
                    with conn:
                        conn.execute('DELETE FROM transactions')
                    for k in ('start_filter','end_filter'):
                        st.session_state.pop(k,None)
                    refresh('All transactions cleared.')

df=load(conn)
if df.empty:
    for col,(name,value) in zip(st.columns(5),[('Income','₹0.00'),('Expenses','₹0.00'),('Net savings','₹0.00'),('Savings rate','N/A'),('Transactions','0')]):
        col.metric(name,value,border=True)
    st.info('No transactions yet. Add a transaction, import a CSV, or load demo data from the sidebar.')
    st.stop()
df['transaction_date']=pd.to_datetime(df['transaction_date'])
lo,hi=df.transaction_date.min().date(),df.transaction_date.max().date()
a,b=st.columns(2)
start=a.date_input('From',lo,key='start_filter')
end=b.date_input('To',hi,key='end_filter')
if start>end: st.error('Start date must precede end date.'); st.stop()
f=df[df.transaction_date.dt.date.between(start,end)].copy()
if f.empty: st.info('No transactions in this date range.'); st.stop()
f['month']=f.transaction_date.dt.to_period('M').astype(str)
inc=f.loc[f.transaction_type=='Income','amount'].sum(); exp=f.loc[f.transaction_type=='Expense','amount'].sum()
def money(n): return f'₹{n:,.2f}'
for col,(name,value) in zip(st.columns(5),[('Income',money(inc)),('Expenses',money(exp)),('Net savings',money(inc-exp)),('Savings rate',f'{(inc-exp)/inc:.1%}' if inc else 'N/A'),('Transactions',f'{len(f):,}')]): col.metric(name,value,border=True)
plt.rcParams.update({'figure.facecolor':'#142238','axes.facecolor':'#142238','axes.labelcolor':'#dce7f5','xtick.color':'#dce7f5','ytick.color':'#dce7f5','text.color':'#dce7f5','axes.edgecolor':'#53647c','font.size':10,'legend.facecolor':'#142238','legend.edgecolor':'#53647c'})
def chart(ax):
    ax.spines[['top','right']].set_visible(False); ax.grid(axis='y',alpha=.15); ax.set_axisbelow(True)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x,p:f'{x/1000:,.0f}k' if abs(x)>=1000 else f'{x:,.0f}'))
def show(fig):
    fig.tight_layout(); st.pyplot(fig); plt.close(fig)
monthly=f.pivot_table(index='month',columns='transaction_type',values='amount',aggfunc='sum',fill_value=0).reindex(columns=['Income','Expense'],fill_value=0)
expenses=f[f.transaction_type=='Expense']
left,right=st.columns(2)
with left:
    st.subheader('Monthly income vs expenses'); fig,ax=plt.subplots(figsize=(8,4)); monthly.plot.bar(ax=ax,color=['#37cda4','#f59e72']); ax.set_xlabel(''); ax.set_ylabel('INR'); ax.tick_params(axis='x',rotation=45); chart(ax); show(fig)
with right:
    st.subheader('Spending by category'); s=expenses.groupby('category').amount.sum().sort_values(ascending=False)
    if len(s):
        fig,ax=plt.subplots(figsize=(8,4)); ax.pie(s,wedgeprops={'width':.38,'edgecolor':'#142238'},colors=['#38bdf8','#37cda4','#f59e72','#a78bfa','#facc15','#f472b6','#818cf8','#94a3b8','#64748b']); ax.legend(s.index,loc='center left',bbox_to_anchor=(1,0.5)); ax.text(0,0,'Expenses',ha='center',va='center'); show(fig)
    else: st.info('No expenses.')
left,right=st.columns(2)
with left:
    st.subheader('Monthly net savings'); fig,ax=plt.subplots(figsize=(8,4)); (monthly.Income-monthly.Expense).plot(ax=ax,marker='o',color='#37cda4'); ax.set_xlabel(''); ax.tick_params(axis='x',rotation=45); chart(ax); show(fig)
with right:
    st.subheader('Top spending categories'); s=expenses.groupby('category').amount.sum().nlargest(5).sort_values()
    if len(s):
        fig,ax=plt.subplots(figsize=(8,4)); s.plot.barh(ax=ax,color='#38bdf8'); ax.set_ylabel(''); ax.xaxis.set_major_formatter(FuncFormatter(lambda x,p:f'{x/1000:,.0f}k' if abs(x)>=1000 else f'{x:,.0f}')); show(fig)
    else: st.info('No expenses.')
st.subheader('Payment method analysis')
st.dataframe(f.groupby('payment_method').agg(Transactions=('amount','size'),Total_amount=('amount','sum')).reset_index(),hide_index=True)
st.subheader('Transaction explorer')
query=st.text_input('Search description or category')
view=f[f.description.str.contains(query,case=False,regex=False)|f.category.str.contains(query,case=False,regex=False)] if query else f
view=view.drop(columns='month'); st.dataframe(view,hide_index=True); st.download_button('Export filtered CSV',view.to_csv(index=False),'transactions.csv','text/csv')
with st.expander('Edit or delete a transaction'):
    if len(view):
        tid=st.selectbox('Transaction ID',view.transaction_id.tolist()); r=view[view.transaction_id==tid].iloc[0]
        k=st.selectbox('New type',['Income','Expense'],index=['Income','Expense'].index(r.transaction_type),key=f'kind{tid}')
        with st.form(f'edit{tid}{k}'):
            d=st.date_input('Transaction date',r.transaction_date.date()); desc=st.text_input('Description',r.description); cats=CATEGORIES[k]; cat=st.selectbox('Category',cats,index=cats.index(r.category) if r.category in cats else len(cats)-1); amt=st.number_input('Amount',min_value=.01,max_value=1e12,value=float(r.amount)); pay=st.selectbox('Payment',PAYMENTS,index=PAYMENTS.index(r.payment_method)); save=st.form_submit_button('Save changes')
            if save:
                if not desc.strip(): st.error('Description is required.')
                else:
                    with conn: insert(conn,(d.isoformat(),desc.strip(),cat,k,amt,pay),tid)
                    refresh('Transaction updated.')
        confirm=st.checkbox('Confirm deletion',key=f'delete{tid}')
        if st.button('Delete transaction',disabled=not confirm):
            with conn: conn.execute('DELETE FROM transactions WHERE transaction_id=?',(int(tid),))
            refresh('Transaction deleted.')
