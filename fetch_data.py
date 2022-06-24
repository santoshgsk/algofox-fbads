import requests
import time
import json
import pickle
from sys import stdout
import numpy as np
from time import sleep
from datetime import datetime, timedelta

import pandas as pd
from collections import defaultdict
from itertools import combinations, permutations

AD_ACCOUNT_ID = None
ACCESS_TOKEN = None

ad_fields_insights_to_calculate = [
    'cpp',
    'cpm',
    'cpc',
    'ctr',
    'cost_per_inline_link_click',
    'inline_link_click_ctr',
    'cost_per_inline_post_engagement',
    'cost_per_outbound_click',
    'outbound_clicks_ctr',
    'cost_per_action_type',
    'cost_per_conversion'
]


CAMPAIGN_STATIC_FIELDS = ['bid_strategy', 
                   'budget_remaining', 
                   'buying_type', 
                   'status', 
                   'objective']


ADSET_STATIC_FIELDS = [
                'campaign_id',
                'id',
                'attribution_spec',
                'billing_event',
                'budget_remaining',
                'daily_budget',
                'destination_type',
                'is_dynamic_creative',
                'optimization_goal',
                'status',
                'targeting']

AD_STATIC_FIELDS = ['campaign_id',
            'adset_id',
            'adlabels',
             'conversion_domain',
             'name',
             'preview_shareable_link'
            ]

CREATIVE_STATIC_FIELDS = ['status',
                      'object_story_spec',
                      'instagram_permalink_url',
                      'asset_feed_spec',
                      'object_type'
                     ]

CAMPAIGN_INSIGHTS_FIELDS = ['date_start',
                            'date_stop',
                            'campaign_id',
                            'campaign_name'
                           ]

ADSET_INSIGHTS_FIELDS = ['adset_name',
                         'campaign_id',
                         'adset_id',
                         'optimization_goal']

AD_INSIGHTS_FIELDS = ['ad_name',
                      'campaign_id',
                      'adset_id',
                      'ad_id',
                      'quality_ranking',
                      'conversion_rate_ranking',
                      'engagement_rate_ranking',
                      'video_30_sec_watched_actions',
                      'video_avg_time_watched_actions',
                      'video_p100_watched_actions',
                      'video_p25_watched_actions',
                      'video_p50_watched_actions',
                      'video_p75_watched_actions',
                      'video_p95_watched_actions',
                      'video_play_actions',
                      'spend',
                      'impressions',
                      'reach',
                      'frequency',
                      'clicks',
                      'cost_per_unique_click',
                      'inline_link_clicks',
                      'cost_per_unique_inline_link_click',
                      'inline_post_engagement',
                      'outbound_clicks',
                      'cost_per_unique_outbound_click',
                      'actions',
                      'action_values',
                      'cost_per_unique_action_type',
                      'conversions',
                      'conversion_values',
                      'purchase_roas',
                      'website_purchase_roas',
                      'website_ctr'
                     ]

def get_all_campaigns(date_start, date_end):
    
    params = (
        ('access_token', ACCESS_TOKEN),
        ('level', 'campaign'),
        ('time_range', "{'since':'"+date_start + "', 'until': '"+ date_end +"'}"),
        ('fields', 'campaign_id')
    )

    response = requests.get('https://graph.facebook.com/v14.0/act_{0}/insights'.format(AD_ACCOUNT_ID), params=params)

    json_data = json.loads(response.content)
    
    campaigns_df = pd.DataFrame(json_data['data'])
    
    if len(campaigns_df) == 0:
        return None
    
    return campaigns_df['campaign_id'].values

def increment_date_by_day(date_start, date_end):
    new_start = datetime.strptime(date_start, '%Y-%m-%d') + timedelta(days=1)
    new_end = datetime.strptime(date_end, '%Y-%m-%d') + timedelta(days=1)
    
    new_start_str = "-".join([str(new_start.year), str(new_start.month), str(new_start.day)])
    new_end_str = "-".join([str(new_end.year), str(new_end.month), str(new_end.day)])
    
    return new_start_str, new_end_str

def get_fb_request_bulk(bulkparams):
    resp = requests.post('https://graph.facebook.com', params=bulkparams)
    responses = json.loads(resp.content)
    df_con = pd.DataFrame()
    
    for r in responses:
        new_df = pd.DataFrame(json.loads(r['body'])['data'])
        df_con = pd.concat([df_con, new_df], axis=0)
    
    df_con.index = range(len(df_con))
    return df_con

def get_adset_static_dict(r):
    
    adset_data = {}
    
    if 'campaign_id' in r:
        adset_data['campaign_id'] = r['campaign_id']
    
    if 'id' in r:
        adset_data['id'] = r['id']

    if 'optimization_goal' in r:
        adset_data['optimization_goal'] = r['optimization_goal']

    if 'is_dynamic_creative' in r:
        adset_data['is_dynamic_creative'] = r['is_dynamic_creative']

    if 'daily_budget' in r:
        adset_data['daily_budget'] = r['daily_budget']

    if 'billing_event' in r:
        adset_data['billing_event'] = r['billing_event']

    if 'attribution_spec' in r:
        adset_data['attribution'] = r['attribution_spec']

    if 'targeting' in r:
        if 'age_max' in r['targeting']:
            adset_data['age_max'] = r['targeting']['age_max']

        if 'age_min' in r['targeting']:
            adset_data['age_min'] = r['targeting']['age_min']
        
        if 'custom_audiences' in r['targeting']:
            adset_data['custom_audiences'] = r['targeting']['custom_audiences']
            
        if 'excluded_custom_audiences' in r['targeting']:
            adset_data['excluded_custom_audiences'] = r['targeting']['excluded_custom_audiences']
        
        if 'flexible_spec' in r['targeting']:
            adset_data['flexible_spec'] = r['targeting']['flexible_spec']

        if 'geo_locations' in r['targeting']:
            adset_data['geo_locations'] = r['targeting']['geo_locations']
        
        if 'exclusions' in r['targeting']:
            adset_data['exclusions'] = r['targeting']['exclusions']
    
    return adset_data


def get_creative_static_dict(data):
    
    creative_data = {}  
    
    creative_data['creative_id'] = data['id']
    
    if 'instagram_permalink_url' in data:
        creative_data['creative_url'] = data['instagram_permalink_url']
        
    if 'object_type' in data:
        creative_data['object_type'] = data['object_type']
        

    data_found = False
    
    if 'object_story_spec' in data:
        if 'link_data' in data['object_story_spec']:
            data_found = True
            creative_copy = data['object_story_spec']['link_data']

            if 'link' in creative_copy:
                creative_data['link'] = creative_copy['link']

            if 'message' in creative_copy:
                creative_data['primary_text'] = creative_copy['message']

            if 'name' in creative_copy:
                creative_data['headline'] = creative_copy['name']

            if 'description' in creative_copy:
                creative_data['description'] = creative_copy['description']

            if 'call_to_action' in creative_copy:
                if 'type' in creative_copy['call_to_action']:
                    creative_data['cta'] = creative_copy['call_to_action']['type']
        elif 'video_data' in data['object_story_spec']:
            
            data_found = True
            creative_copy = data['object_story_spec']['video_data']

            if 'message' in creative_copy:
                creative_data['primary_text'] = creative_copy['message']

            if 'title' in creative_copy:
                creative_data['headline'] = creative_copy['title']

            if 'link_description' in creative_copy:
                creative_data['description'] = creative_copy['link_description']

            if 'call_to_action' in creative_copy:
                if 'type' in creative_copy['call_to_action']:
                    creative_data['cta'] = creative_copy['call_to_action']['type']
                
                if 'value' in creative_copy['call_to_action']:
                    if 'link' in creative_copy['call_to_action']['value']:
                        creative_data['link'] = creative_copy['call_to_action']['value']['link']

    if data_found == False:
        if 'asset_feed_spec' in data:
            assets = data['asset_feed_spec']
            
            if 'descriptions' in assets:
                if 'text' in assets['descriptions'][0]:
                    creative_data['description'] = assets['descriptions'][0]['text']
                
            if 'titles' in assets:
                if 'text' in assets['titles'][0]:
                    creative_data['headline'] = assets['titles'][0]['text']
                
            if 'link_urls' in assets:
                if 'website_url' in assets['link_urls'][0]:
                    creative_data['link'] = assets['link_urls'][0]['website_url']
        
            if 'bodies' in assets:
                if 'text' in assets['bodies'][0]:
                        creative_data['primary_text'] = assets['bodies'][0]['text']
                
            if 'call_to_action_types' in assets:
                creative_data['cta'] = assets['call_to_action_types'][0]
            
            if 'videos' in assets:
                if 'thumbnail_url' in assets['videos'][0]:
                    creative_data['creative_url'] = assets['videos'][0]['thumbnail_url']
                
            creative_data['creative_optimization'] = 'placement'
            
    return creative_data

def get_fb_request_bulk_static(bulkparams, level):
    resp = requests.post('https://graph.facebook.com', params=bulkparams)
    
    responses = json.loads(resp.content)
    
    df_entries = []

    for r in responses:
        if level == "adset":
            df_entries.append(get_adset_static_dict(json.loads(r['body'])))
        elif level == "creative":
            df_entries.append(get_creative_static_dict(json.loads(r['body'])))
        else:
            df_entries.append(json.loads(r['body']))
    
    new_id = level + "_id"
    
    df = pd.DataFrame(df_entries)
    
    df.rename(columns={'id': new_id}, inplace=True)
    
    return df


def get_campaign_adsets_bulk(campaign_ids, date_start, date_end):
    bulk_requests = []
    
    df_con = pd.DataFrame()
    for i in range(len(campaign_ids)):
        
        campaign_id = campaign_ids[i]
        
        req_load = {
              "method": "GET",
              "relative_url": "v14.0/"+campaign_id+"/insights?time_range={'since':'"+date_start+"','until':'"+date_end+"'}&level=adset&fields=adset_id"
        }
        
        bulk_requests.append(req_load)
        
        if (len(bulk_requests) > 49) | (i == (len(campaign_ids)-1)):
            params = (
                    ('batch', str(bulk_requests)),
                    ('access_token', ACCESS_TOKEN)
            )
            
            df_concat = get_fb_request_bulk(params)
            
            df_con  = pd.concat([df_con, df_concat], axis=0)
            
            bulk_requests = []
    
    return df_con['adset_id'].values

def get_adset_ads_bulk(adset_ids, date_start, date_end):
    
    bulk_requests = []
    
    df_con = pd.DataFrame()
    for i in range(len(adset_ids)):
        
        adset_id = adset_ids[i]
        
        req_load = {
              "method": "GET",
              "relative_url": "v14.0/"+str(adset_id)+"/insights?time_range={'since':'"+date_start+"','until':'"+date_end+"'}&level=ad&fields=campaign_id,adset_id,ad_id"
        }
        
        bulk_requests.append(req_load)
        
        if (len(bulk_requests) > 49) | (i == (len(adset_ids)-1)):
            params = (
                    ('batch', str(bulk_requests)),
                    ('access_token', ACCESS_TOKEN)
            )
            
            df_concat = get_fb_request_bulk(params)
            
            df_con  = pd.concat([df_con, df_concat], axis=0)
            
            bulk_requests = []
    
    return df_con

def get_ad_creatives_bulk(ad_ids, date_start, date_end):
    
    bulk_requests = []
    
    df_con = pd.DataFrame()
    for i in range(len(ad_ids)):
        
        ad_id = ad_ids[i]
        
        req_load = {
              "method": "GET",
              "relative_url": "v14.0/"+str(ad_id)+"?time_range={'since':'"+date_start+"','until':'"+date_end+"'}&level=ad&fields=campaign_id,adset_id,creative"
        }
        
        bulk_requests.append(req_load)
        
        if (len(bulk_requests) > 49) | (i == (len(ad_ids)-1)):
            params = (
                    ('batch', str(bulk_requests)),
                    ('access_token', ACCESS_TOKEN)
            )
            
            df_concat = get_fb_request_bulk_creative(params)
            
            df_con  = pd.concat([df_con, df_concat], axis=0)
            
            bulk_requests = []
    
    return df_con

def get_fb_request_bulk_creative(bulkparams):
    resp = requests.post('https://graph.facebook.com', params=bulkparams)
    
    responses = json.loads(resp.content)
    
    all_results = []
    for r in responses:
        
        body = json.loads(r['body'])
        
        ad_creative_dict = {}
        ad_creative_dict['campaign_id'] = body['campaign_id']
        ad_creative_dict['adset_id'] = body['adset_id']
        ad_creative_dict['creative_id'] = body['creative']['id']
        ad_creative_dict['ad_id'] = body['id']
        all_results.append(ad_creative_dict)
        
    return pd.DataFrame(all_results)

def get_data_bulk(entity_ids, data_fields, data_type, level, date_start, date_end):
        
    bulk_requests = []
    
    data_fields_str = ",".join(data_fields)
    
    df_con = pd.DataFrame()
    for i in range(len(entity_ids)):
        
        entity_id = entity_ids[i]
        
        if data_type == "insights":
            relative_url = "v14.0/"+str(entity_id)+"/insights?time_range={'since':'"+date_start+"','until':'"+date_end+"'}&level="+level+"&fields="+data_fields_str
        elif data_type == "static":
            relative_url = "v14.0/"+str(entity_id)+"?time_range={'since':'"+date_start+"','until':'"+date_end+"'}&level="+level+"&fields="+data_fields_str
        
        req_load = {
              "method": "GET",
              "relative_url": relative_url
        }
        
        bulk_requests.append(req_load)
        
        if (len(bulk_requests) > 49) | (i == (len(entity_ids)-1)):
            params = (
                    ('batch', str(bulk_requests)),
                    ('access_token', ACCESS_TOKEN)
            )
            
            df_concat = pd.DataFrame()
            
            if data_type == "insights":
                df_concat = get_fb_request_bulk(params)
            elif data_type == "static":
                df_concat = get_fb_request_bulk_static(params, level)
            
            df_con  = pd.concat([df_con, df_concat], axis=0)
            
            bulk_requests = []
    
    return df_con


fb_schema = json.load(open("facebook_schema.json", "rb"))

targeting_keys = list(map(lambda x: x['name'], fb_schema[9]['fields'][12]['fields']))
geolocation_keys = list(map(lambda x: x['name'], fb_schema[9]['fields'][13]['fields']))
geo_fields_map = {}
for t in fb_schema[9]['fields'][13]['fields']:
    if 'fields' in t:
        geo_fields_map[t['name']] = list(map(lambda x: x['name'], t['fields']))


def get_campaign_level_data(campaign_data_point):
    
    d = campaign_data_point
    
    data_point = {}
    
    c_fields = ['campaign_id', 'campaign_name', 'date_start', 'date_stop',
               'daily_budget', 'objective', 'status', 'bid_strategy', 'buying_type']
    
    for c_field in c_fields:
        if c_field in d:
            if d[c_field] is not np.nan:
                data_point[c_field] = d[c_field]
                    
    return data_point

def get_adset_data_point(adset_data_point):
    d = adset_data_point
    
    string_cols = ['adset_id', 'adset_name', 'optimization_goal', 'billing_event']
    bool_cols = ['is_dynamic_creative']
    int_cols = ['daily_budget', 'age_max', 'age_min']
    
    data_point = {}
    
    for sc in string_cols:
        if sc in d:
            if d[sc] is not np.nan:
                data_point[sc] = d[sc]
    
    for ic in int_cols:
        if ic in d:
            if d[ic] is not np.nan:
                data_point[ic] = int(d[ic])
  
    for bc in bool_cols:
        if bc in d:
            if d[bc] is not np.nan:
                data_point[bc] = str(d[bc])
    
    if 'attribution' in d:
        
        if d['attribution'] is not np.nan:
            attr_dict_list = []

            for attr_data in d['attribution']:
                attr_dict = {}
                attr_dict['event_type'] = attr_data['event_type']
                attr_dict['window_days'] = str(attr_data['window_days'])
                attr_dict_list.append(attr_dict)
            data_point['attribution'] = attr_dict_list

    if 'excluded_custom_audiences' in d:

        if d['excluded_custom_audiences'] is not np.nan:
            excl_cust_list = []

            for excl_data in d['excluded_custom_audiences']:
                excl_dict = {}
                excl_dict['name'] = excl_data['name']
                excl_dict['custom_audience_id'] = excl_data['id']
                excl_cust_list.append(excl_dict)

            data_point['excluded_custom_audiences'] = excl_cust_list

    if 'custom_audiences' in d:
        
        if d['custom_audiences'] is not np.nan:
            
            cust_list = []

            for cust_data in d['custom_audiences']:
                cust_dict = {}
                cust_dict['name'] = cust_data['name']
                cust_dict['custom_audience_id'] = cust_data['id']
                cust_list.append(cust_dict)

            data_point['custom_audiences'] = cust_list

    if 'exclusions' in d:

        if d['exclusions'] is not np.nan:
            t_dict = {}
            for t in targeting_keys:
                if t in d['exclusions']:
                    t_dict[t] = d['exclusions'][t]

            data_point['exclusions'] = t_dict

    if 'flexible_spec' in d:

        if d['flexible_spec'] is not np.nan:
            t_dict = {}
            for t in targeting_keys:
                if t in d['flexible_spec'][0]:
                    t_dict[t] = d['flexible_spec'][0][t]

            data_point['targeting'] = t_dict

    if 'geo_locations' in d:
        
        if d['geo_locations'] is not np.nan:

            t_dict = {}
            for t in geolocation_keys:
                if t in d['geo_locations']:
                    if (t == "countries") | (t == "location_types"): 
                        t_dict[t] = d["geo_locations"][t]
                    else:
                        geo_map = {}
                        for t2 in geo_fields_map[t]:
                            if t2 in d['geo_locations'][t]:
                                if t2 in ['radius', 'primary_city_id', 'region_id']:
                                    if d['geo_locations'][t][t2] is not np.nan:
                                        geo_map[t2] = int(d['geo_locations'][t][t2])
                                elif t2 in ['latitude', 'longitude']:
                                    if d['geo_locations'][t][t2] is not np.nan:
                                        geo_map[t2] = float(d['geo_locations'][t][t2])
                                else:
                                    geo_map[t2] = d['geo_locations'][t][t2]
                        t_dict[t] = geo_map
            data_point['geo_locations'] = t_dict

    return data_point

def get_ad_data_point(ad_data_point):
    
    d = ad_data_point
    
    data_point = {}

    str_fields = ['ad_id', 'ad_name', 'preview_shareable_link', 'conversion_domain', 'conversion_rate_ranking',
                  'quality_ranking', 'engagement_rate_ranking', 'video_avg_time_watched_actions',
                  'video_p25_watched_actions', 'video_30_sec_watched_actions', 'video_p50_watched_actions',
                  'video_p75_watched_actions', 'video_p95_watched_actions', 'video_p100_watched_actions',
                  'video_play_actions', 'outbound_clicks', 'cost_per_unique_outbound_click', 'actions',
                  'cost_per_unique_action_type', 'website_ctr', 'action_values', 'conversions',
                 'purchase_roas', 'website_purchase_roas', 'creative_id', 'object_type', 'creative_url',
                 'primary_text', 'headline', 'description', 'cta', 'link', 'creative_optimization']
    
    int_fields = ['impressions', 'reach', 'clicks', 'inline_link_clicks', 'inline_post_engagement']
    
    float_fields = ['spend', 'frequency', 'cost_per_unique_click', 'cost_per_unique_inline_link_click']
    
    for s_field in str_fields:
        if s_field in d:
            if d[s_field] is not np.nan:
                data_point[s_field] = d[s_field]
        
    for i_field in int_fields:
        if i_field in d:
            if d[i_field] is not np.nan:
                data_point[i_field] = int(d[i_field])
    
    for f_field in float_fields:
        if f_field in d:
            if d[f_field] is not np.nan:
                data_point[f_field] = float(d[f_field])
                
    return data_point

def get_full_data(date_start, date_end, adaccid, accesstoken):

    global AD_ACCOUNT_ID, ACCESS_TOKEN
    AD_ACCOUNT_ID = adaccid
    ACCESS_TOKEN = accesstoken
    
    all_campaigns = get_all_campaigns(date_start, date_end)
    if all_campaigns is None:
        return None
    all_adsets = get_campaign_adsets_bulk(all_campaigns,date_start, date_end)
    all_ads = get_adset_ads_bulk(all_adsets, date_start, date_end)
    all_creatives = get_ad_creatives_bulk(all_ads['ad_id'].unique(), date_start, date_end)

    all_campaign_insight_data = get_data_bulk(all_campaigns, CAMPAIGN_INSIGHTS_FIELDS, "insights", "campaign", date_start, date_end)
    all_campaign_static_data = get_data_bulk(all_campaigns, CAMPAIGN_STATIC_FIELDS, "static", "campaign", date_start, date_end)

    all_adset_insight_data = get_data_bulk(all_adsets, ADSET_INSIGHTS_FIELDS, "insights", "adset", date_start, date_end)
    all_adset_static_data = get_data_bulk(all_adsets, ADSET_STATIC_FIELDS, "static", "adset", date_start, date_end)

    all_ad_insight_data = get_data_bulk(all_ads["ad_id"].unique(), AD_INSIGHTS_FIELDS, "insights", "ad", date_start, date_end)
    all_ad_static_data = get_data_bulk(all_ads["ad_id"].unique(), AD_STATIC_FIELDS, "static", "ad", date_start, date_end)

    all_creative_static_data = get_data_bulk(all_creatives['creative_id'].unique(), CREATIVE_STATIC_FIELDS, "static", "creative", date_start, date_end)

    full_data = pd.merge(all_campaign_static_data, all_campaign_insight_data, on="campaign_id")

    if 'objective' in all_adset_insight_data.columns:
        all_adset_insight_data.drop(['objective'], axis=1, inplace=True)
    if 'date_start' in all_adset_insight_data.columns:
        all_adset_insight_data.drop(['date_start'], axis=1, inplace=True)
    if 'date_stop' in all_adset_insight_data.columns:
        all_adset_insight_data.drop(['date_stop'], axis=1, inplace=True)
        
    full_data = pd.merge(full_data, all_adset_insight_data, on="campaign_id")
    
    if 'optimization_goal' in all_adset_static_data.columns:
        all_adset_static_data.drop(['optimization_goal'], axis=1, inplace=True)
        
    full_data = pd.merge(full_data, all_adset_static_data, on=['campaign_id',"adset_id"])
    
    if 'date_start' in all_ad_insight_data.columns:
        all_ad_insight_data.drop(['date_start'], axis=1, inplace=True)

    if 'date_stop' in all_ad_insight_data.columns:
        all_ad_insight_data.drop(['date_stop'], axis=1, inplace=True)
    
    full_data = pd.merge(full_data, all_ad_insight_data, on=['campaign_id', 'adset_id'])
    full_data = pd.merge(full_data, all_ad_static_data, on=['campaign_id','adset_id', 'ad_id'])

    full_data = pd.merge(full_data, all_creatives, on=['campaign_id', 'adset_id', 'ad_id'])
    full_data = pd.merge(full_data, all_creative_static_data, on =['creative_id'])
    
    return full_data


def get_full_dict_from_data(full_data):
    unique_campaigns = full_data['campaign_id'].unique()

    full_dicts = []
    for c in unique_campaigns:

        campaign_data = full_data[full_data["campaign_id"]==c]
        campaign_data_point = campaign_data.iloc[0].to_dict()
        full_dict = get_campaign_level_data(campaign_data_point)

        unique_adsets = campaign_data["adset_id"].unique()

        adset_dicts = []
        for adset in unique_adsets:
            adset_data = full_data[full_data["adset_id"]==adset]
            adset_data_point = adset_data.iloc[0].to_dict()

            adset_dict = get_adset_data_point(adset_data_point)

            unique_ads = adset_data["ad_id"].unique()

            ad_dicts = []
            for ad in unique_ads:
                ad_data = full_data[full_data["ad_id"]==ad]
                ad_data_point = ad_data.iloc[0].to_dict()
                ad_dict = get_ad_data_point(ad_data_point)
                ad_dicts.append(ad_dict)

            adset_dict["ads"] = ad_dicts

            adset_dicts.append(adset_dict)

        full_dict["adsets"] = adset_dicts

        full_dicts.append(full_dict)
    
    return full_dicts
    