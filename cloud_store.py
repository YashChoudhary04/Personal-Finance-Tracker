"""Per-session Supabase storage and authentication for the finance dashboard."""
import math
import pandas as pd
import streamlit as st
from supabase import create_client
import finance as local


def new_client():
    url = st.secrets['SUPABASE_URL']
    api_key = st.secrets['SUPABASE_KEY']
    if not str(api_key).startswith('sb_publishable_'):
        raise ValueError('Use a Supabase publishable key, not a secret key.')
    # Never cache or share an authenticated client between Streamlit sessions.
    return create_client(url, api_key)


def switch_workspace(client=None, user_id=None, email=None, notice=None):
    old = st.session_state.get('finance_connection')
    if old is not None:
        old.close()
    st.session_state.clear()
    if client is not None:
        st.session_state['cloud_client'] = client
        st.session_state['cloud_user_id'] = user_id
        st.session_state['cloud_email'] = email
    if notice:
        st.session_state['account_notice'] = notice
    st.rerun()


def account_sidebar():
    with st.sidebar:
        st.header('Your workspace')
        if 'account_notice' in st.session_state:
            st.info(st.session_state.pop('account_notice'))
        client = st.session_state.get('cloud_client')
        if client is not None:
            st.success('Signed in')
            st.caption(st.session_state['cloud_email'])
            if st.button('Log out', key='cloud_logout'):
                try:
                    client.auth.sign_out()
                except Exception:
                    # Always discard this browser session's local authentication state.
                    pass
                switch_workspace(notice='Signed out of this workspace.')
            st.divider()
            return CloudStore(client, st.session_state['cloud_user_id'])
        st.caption('Guest demo: temporary, private to this session.')
        with st.expander('Sign in or create an account'):
            with st.form('cloud_auth', clear_on_submit=True):
                email = st.text_input('Email address')
                password = st.text_input('Password', type='password')
                login = st.form_submit_button('Sign in')
                register = st.form_submit_button('Create account')
            if login or register:
                if not email.strip() or not password:
                    st.error('Enter your email and password.')
                elif register and len(password) < 8:
                    st.error('Choose a password of at least 8 characters.')
                else:
                    try:
                        client = new_client()
                        credentials = {'email': email.strip(), 'password': password}
                        response = (client.auth.sign_up(credentials) if register else
                                    client.auth.sign_in_with_password(credentials))
                    except Exception:
                        st.error('Authentication failed. Check your credentials, email confirmation and Supabase configuration, then try again.')
                    else:
                        if response.session and response.user:
                            switch_workspace(client, str(response.user.id), email.strip())
                        elif register:
                            st.info('If eligible, check your email for a confirmation link, then sign in here.')
                        else:
                            st.error('No authenticated session was returned.')
        st.divider()
    return None


class CloudStore:
    def __init__(self, client, user_id):
        self.client = client
        self.user_id = user_id
        self._refs = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def refs(self):
        if self._refs is None:
            categories = self.client.table('categories').select('category_id,name,kind').execute().data
            payments = self.client.table('payment_methods').select('payment_id,name').execute().data
            self._refs = ({(r['name'],r['kind']): r['category_id'] for r in categories},
                          {r['name']: r['payment_id'] for r in payments})
        return self._refs

    def payload(self, row):
        d, desc, cat, kind, amount, pay = row
        cats, pays = self.refs()
        return {'user_id': self.user_id, 'transaction_date': str(d),
                'description': str(desc), 'category_id': cats[(cat,kind)],
                'amount_paise': round(float(amount)*100), 'payment_id': pays[pay]}

    def load(self):
        rows = []
        offset = 0
        while True:
            page = (self.client.table('transactions')
                .select('transaction_id,transaction_date,description,amount_paise,categories(name,kind),payment_methods(name)')
                .eq('user_id', self.user_id)
                .order('transaction_id', desc=False).range(offset,offset+499).execute().data)
            for r in page:
                rows.append({'transaction_id':r['transaction_id'], 'transaction_date':r['transaction_date'],
                    'description':r['description'], 'category':r['categories']['name'],
                    'transaction_type':r['categories']['kind'], 'amount':r['amount_paise']/100.0,
                    'payment_method':r['payment_methods']['name']})
            if len(page) < 500:
                break
            offset += len(page)
        return pd.DataFrame(rows, columns=['transaction_id',*local.FIELDS]).sort_values(
            ['transaction_date','transaction_id'],ascending=False).reset_index(drop=True)

    def insert(self, row, tid=None):
        payload = self.payload(row)
        table = self.client.table('transactions')
        if tid is None:
            table.insert(payload).execute()
        else:
            result = table.update(payload).eq('user_id',self.user_id).eq('transaction_id',int(tid)).execute()
            if not result.data:
                raise ValueError('Transaction not found or no longer accessible.')

    def delete(self, tid=None):
        query = self.client.table('transactions').delete().eq('user_id', self.user_id)
        if tid is not None:
            query = query.eq('transaction_id',int(tid))
        result = query.execute()
        if tid is not None and not result.data:
            raise ValueError('Transaction not found or no longer accessible.')

    def import_csv(self, df):
        required = {'transaction_date','description','transaction_type','amount'}
        if not required.issubset(df.columns):
            raise ValueError('Missing columns: '+', '.join(sorted(required-set(df.columns))))
        if len(df) > 5000:
            raise ValueError('Import up to 5,000 rows at a time in cloud mode.')
        df = df.copy()
        df['transaction_date'] = pd.to_datetime(df['transaction_date'],errors='coerce').dt.strftime('%Y-%m-%d')
        df['amount'] = pd.to_numeric(df['amount'],errors='coerce')
        df['description'] = df['description'].fillna('').astype(str).str.strip()
        df['transaction_type'] = df['transaction_type'].fillna('').astype(str).str.strip().str.title()
        seen = {local.key(r) for r in self.load()[local.FIELDS].itertuples(index=False,name=None)}
        payloads = []
        invalid = duplicates = 0
        for r in df.to_dict('records'):
            d,desc,kind,amount = r['transaction_date'],r['description'],r['transaction_type'],r['amount']
            if pd.isna(d) or not desc or kind not in local.CATEGORIES or pd.isna(amount) or not math.isfinite(amount) or not 0.01<=amount<=1e12:
                invalid += 1
                continue
            cat = str(r.get('category','')).strip().title()
            if cat not in local.CATEGORIES[kind]:
                cat = local.categorize(desc,kind)
            pay = str(r.get('payment_method','Other')).strip()
            pay = next((p for p in local.PAYMENTS if p.casefold()==pay.casefold()),'Other')
            row = (d,desc,cat,kind,amount,pay)
            k = local.key(row)
            if k in seen:
                duplicates += 1
                continue
            payloads.append(self.payload(row))
            seen.add(k)
        if payloads:
            self.client.table('transactions').insert(payloads).execute()
        return len(payloads),invalid,duplicates


def load(conn):
    return conn.load() if isinstance(conn,CloudStore) else local.load(conn)


def insert(conn,row,tid=None):
    return conn.insert(row,tid) if isinstance(conn,CloudStore) else local.insert(conn,row,tid)


def import_csv(conn,df):
    return conn.import_csv(df) if isinstance(conn,CloudStore) else local.import_csv(conn,df)


def delete(conn,tid=None):
    if isinstance(conn,CloudStore):
        return conn.delete(tid)
    with conn:
        if tid is None:
            conn.execute('DELETE FROM transactions')
        else:
            conn.execute('DELETE FROM transactions WHERE transaction_id=?',(int(tid),))
