import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
from fetch_data import get_full_data, increment_date_by_day
import altair as alt

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

        # ad - cpm
    
        ad_cpm = all_days_data[["ad_id", "date_start", "spend", "impressions"]]
        ad_cpm["cpm"] = ad_cpm.spend.astype(float)*1000/ad_cpm.impressions.astype(int)

        running_ads = ad_cpm[ad_cpm["date_start"]==ad_cpm['date_start'].max()]["ad_id"].values
        ad_cpm = ad_cpm[ad_cpm['ad_id'].isin(running_ads)]

        min_3_days_ads =(ad_cpm.groupby(['ad_id'])['cpm'].count()>3).index.values
        ad_cpm = ad_cpm[ad_cpm["ad_id"].isin(min_3_days_ads)]

        high_cpm_ads = ad_cpm.groupby(['ad_id'])['cpm'].mean().sort_values(ascending=False).iloc[:5].index.values

        cpm_chart = alt.Chart(ad_cpm[ad_cpm["ad_id"].isin(high_cpm_ads)]).mark_line().encode(
            x="yearmonthdate(date_start)", y="cpm", color="ad_id").properties(
            width=800,
            height=300
        )
        st.header("Top 5 worst performing Ads based on CPM")
        st.altair_chart(cpm_chart, use_container_width=False)
        st.dataframe(all_days_data[all_days_data['ad_id'].isin(high_cpm_ads)][["ad_id", "campaign_name", "adset_name", "ad_name"]].drop_duplicates())

        # ad - ctr
    
        ad_ctr = all_days_data[["ad_id", "date_start", "clicks", "impressions"]]
        ad_ctr["ctr"] = ad_ctr.clicks.astype(float)*100/ad_ctr.impressions.astype(int)

        running_ads = ad_ctr[ad_ctr["date_start"]==ad_ctr['date_start'].max()]["ad_id"].values
        ad_ctr = ad_ctr[ad_ctr['ad_id'].isin(running_ads)]

        min_3_days_ads =(ad_ctr.groupby(['ad_id'])['ctr'].count()>3).index.values
        ad_ctr = ad_ctr[ad_ctr["ad_id"].isin(min_3_days_ads)]

        low_ctr_ads = ad_ctr.groupby(['ad_id'])['ctr'].mean().sort_values().iloc[:5].index.values

        ctr_chart = alt.Chart(ad_ctr[ad_ctr["ad_id"].isin(low_ctr_ads)]).mark_line().encode(
            x="yearmonthdate(date_start)", y="ctr", color="ad_id").properties(
            width=800,
            height=300
        )
        st.header("Top 5 worst performing Ads based on CTR")
        st.altair_chart(ctr_chart, use_container_width=False)
        st.dataframe(all_days_data[all_days_data['ad_id'].isin(low_ctr_ads)][["ad_id", "campaign_name", "adset_name", "ad_name"]].drop_duplicates())

        def get_leads(x):
            for y in x:
                if y['action_type'] == 'lead':
                    return int(y['value'])
            return 0
        all_days_data['leads'] = all_days_data['actions'].map(lambda x: get_leads(x))


        # ad - conversion
    
        ad_conversion = all_days_data[["ad_id", "date_start", "clicks", "leads"]]
        ad_conversion["conversion"] = ad_conversion.leads.astype(int)*100/ad_ctr.clicks.astype(int)

        running_ads = ad_conversion[ad_conversion["date_start"]==ad_conversion['date_start'].max()]["ad_id"].values
        ad_conversion = ad_conversion[ad_conversion['ad_id'].isin(running_ads)]

        min_3_days_ads =(ad_conversion.groupby(['ad_id'])['conversion'].count()>3).index.values
        ad_conversion = ad_conversion[ad_conversion["ad_id"].isin(min_3_days_ads)]

        low_converting_ads = ad_conversion.groupby(['ad_id'])['conversion'].mean().sort_values().iloc[:5].index.values

        conversion_chart = alt.Chart(ad_conversion[ad_conversion["ad_id"].isin(low_converting_ads)]).mark_line().encode(
            x="yearmonthdate(date_start)", y="conversion", color="ad_id").properties(
            width=800,
            height=300
        )

        st.header("Top 5 worst performing Ads based on Conversions")
        st.altair_chart(conversion_chart, use_container_width=False)
        st.dataframe(all_days_data[all_days_data['ad_id'].isin(low_converting_ads)][["ad_id", "campaign_name", "adset_name", "ad_name"]].drop_duplicates())

        worst_ads = list(set(high_cpm_ads) & set(low_ctr_ads) & set(low_converting_ads))

        if len(worst_ads) > 0:
            st.header("Overall Worst performing Ads based on all three measures - CPM, CTR, Conversions")
            st.dataframe(all_days_data[all_days_data['ad_id'].isin(worst_ads)][["ad_id", "campaign_name", "adset_name", "ad_name"]].drop_duplicates())
        else:
            worst_ads_cpm_ctr = list(set(high_cpm_ads) & set(low_ctr_ads))
            worst_ads_cpm_conversion = list(set(high_cpm_ads) & set(low_converting_ads))
            worst_ads_ctr_conversion = list(set(low_ctr_ads) & set(low_converting_ads))

            if len(worst_ads_cpm_ctr) > 0:
                st.header("Overall Worst performing Ads based on - CPM, CTR")
                st.dataframe(all_days_data[all_days_data['ad_id'].isin(worst_ads_cpm_ctr)][["ad_id", "campaign_name", "adset_name", "ad_name"]].drop_duplicates())
            
            if len(worst_ads_cpm_conversion) > 0:
                st.header("Overall Worst performing Ads based on - CPM, Conversions")
                st.dataframe(all_days_data[all_days_data['ad_id'].isin(worst_ads_cpm_conversion)][["ad_id", "campaign_name", "adset_name", "ad_name"]].drop_duplicates())
            
            if len(worst_ads_ctr_conversion) > 0:
                st.header("Overall Worst performing Ads based on - CTR, Conversions")
                st.dataframe(all_days_data[all_days_data['ad_id'].isin(worst_ads_ctr_conversion)][["ad_id", "campaign_name", "adset_name", "ad_name"]].drop_duplicates())
                
            



        

