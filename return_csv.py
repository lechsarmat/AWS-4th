#!/usr/bin/env python3


import pandas as pd
from io import StringIO
import requests

import logging
import boto3
from botocore.exceptions import ClientError
import os

import seaborn as sns
from matplotlib import pyplot as plt
import matplotlib.dates as mdates


def upload_file(file_name, bucket, object_name=None):
    if object_name is None:
        object_name = os.path.basename(file_name)

    s3_client = boto3.client('s3')
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True
  
  
valcodes = ['usd', 'eur']

for valcode in valcodes:
    url = f'https://bank.gov.ua/NBU_Exchange/exchange_site?start=20210101&end=20211231&valcode={valcode}&sort=exchangedate&order=asc&json'

    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        df = pd.json_normalize(data)
        df.to_csv(f'nbu_exchange_{valcode}.csv', index=False)
        upload_file(f'./nbu_exchange_{valcode}.csv', 'sviatoslavsbucketlab2', f'nbu_exchange_{valcode}.csv')
        print(f'Success: {valcode}')
    else:
        print(f'Error: {valcode}')
        
        
valcodes = ['usd', 'eur']
df_dict = {}
s3 = boto3.resource('s3')

for valcode in valcodes:
    s3_object = s3.Bucket('sviatoslavsbucketlab2').Object(f'nbu_exchange_{valcode}.csv').get()
    data = s3_object['Body'].read().decode()
    df_dict[valcode] = pd.read_csv(StringIO(data))
    print(f'Success: {valcode}')
    
   
valcodes = ['usd', 'eur']

val_df = pd.DataFrame(data=df_dict['usd']['exchangedate'])
for valcode in valcodes:
    val_df[valcode.upper()] = df_dict[f'{valcode}']['rate']
    
    
color_list = ['#708090','#FF6347']

fig = plt.figure(figsize=(12,8))
sns.set_style('darkgrid', {'axes.grid': False})
results = sns.lineplot(x='exchangedate', y='value', hue='variable', data=pd.melt(val_df, ['exchangedate']), palette=color_list)
plt.xlabel('DATE', fontsize = 16)
plt.ylabel('UAH', fontsize = 16)
plt.legend(loc = 'upper right', fontsize = 16)
plt.tick_params(labelsize = 16)
plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=60))

plt.savefig('exchange_vals.png')
upload_file('./exchange_vals.png', 'sviatoslavsbucketlab2', 'exchange_vals.png')

plt.show()
