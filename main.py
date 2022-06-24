# import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
from fetch_data import get_full_data, increment_date_by_day


AD_ACCOUNT_ID = 666100733979996
ACCESS_TOKEN = 'EAAOZCb5RguPkBAOKqzHXdB3syXgPZBiNpYBT9XmxFHXj2dSv1TYxgQHBSkARo2SVN9CB3NKZCs9bQRwLFw29vF3ksnJBkfq5oyUgWzODb1PFxFa2wR6c5I8iw4XATrtOd29u48KjaMeZAQzGOaJ6UtluJV1TXr05YXyYWZB7WO3K6N7BqIOJdv80diMrfYe8DNdLmJG1q2wZDZD'


all_days_data = None

date_start = '2022-06-16'
date_stop = date_start

while date_stop != '2022-6-24':
    
    print ("Processing ... ", date_start)
    
    start = datetime.now()
    full_data = get_full_data(date_start, date_stop, AD_ACCOUNT_ID, ACCESS_TOKEN)
    print (".... 1. Completed data fetching in ", datetime.now()-start)
    
    if all_days_data is None:
        all_days_data = full_data
    else:
        all_days_data = pd.concat([all_days_data, full_data], axis=0)
    date_start, date_stop = increment_date_by_day(date_start, date_stop)

print (all_days_data)