import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
from fetch_data import get_full_data, increment_date_by_day

ACCESS_TOKEN = None
AD_ACCOUNT_ID = None

with st.sidebar:
    ACCESS_TOKEN = st.text_input("ACCESS TOKEN")
    AD_ACCOUNT_ID = st.text_input("AD_ACCOUNT_ID")

st.write("now let s see if it is working")

dd = datetime.now()
today_date = "-".join([str(dd.year), str(dd.month), str(dd.day)])
default_start = datetime.strptime(today_date, '%Y-%m-%d') - timedelta(days=7)
start_date = st.date_input("start_date", value=default_start)
end_date = st.date_input("end_date", value=dd)



all_days_data = None

date_start = "-".join([str(start_date.year), str(start_date.month), str(start_date.day)])
date_stop = date_start

stop_date = "-".join([str(end_date.year), str(end_date.month), str(end_date.day)])



if (AD_ACCOUNT_ID is not None) & (ACCESS_TOKEN is not None): 

    if st.button("Fetch Data"):
        while date_stop != stop_date:
            
            print ("Processing ... ", date_start)
            
            start = datetime.now()
            full_data = get_full_data(date_start, date_stop, AD_ACCOUNT_ID, ACCESS_TOKEN)
            print (".... 1. Completed data fetching in ", datetime.now()-start)
            
            if all_days_data is None:
                all_days_data = full_data
            else:
                all_days_data = pd.concat([all_days_data, full_data], axis=0)
            date_start, date_stop = increment_date_by_day(date_start, date_stop)

        all_days_data