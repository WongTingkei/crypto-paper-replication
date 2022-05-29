# -*- coding: utf-8 -*-
"""
Created on Mon May 23 2022

@author: Bill
"""

import os
import pandas as pd
import numpy as np

os.chdir(r'C:\Users\Bill\Desktop\HKU\7037\HW2\Crypto')
df = pd.read_csv('historical.csv')
df =df[['coin_id','date','price','market_cap','volume_24h']]
df.drop_duplicates(inplace = True)
#改名是因为之前下面的code用的这些name然后下面code懒得改了。。
df.rename(columns = {'coin_id':'id', 'price':'prices','date':'time','market_cap':'market_caps','volume_24h':'total_volumes'}, inplace = True)
df['time'] = pd.to_datetime(df['time'])
#the data should be from 2014 t0 July 2020 according to the research paper
df = df[(df.time>='2014-01-01')&(df.time<'2020-07-01')]  

#assign a weekday index to each row
df['weekday'] = df['time']-df['time'].min()
df['weekday'] = df['weekday'].dt.days
df['weekday'] = (df['weekday']+1)%7

#create another dataframe to get 7-day max price using rolling
df2 = df.set_index('weekday').groupby('id')['prices'].rolling(7).max()
df2 = df2.reset_index()
#change the df2 to weekly
df2 = df2[df2.weekday == 0]
df2.rename(columns = {'id':'id2','weekday':'w2','prices':'maxprc'},inplace = True)
df2 = df2.reset_index()
df2.drop(columns = ['index','id2','w2'],inplace = True)
#use the same methodology to get 7-day volume
df3 = df.set_index('weekday').groupby('id')['total_volumes'].rolling(7,min_periods=1).sum()
df3 = df3.reset_index()
df3 = df3[df3.weekday == 0]
df3.rename(columns = {'id':'id3','weekday':'w3','total_volumes':'volumes'},inplace = True)
df3 = df3.reset_index()
df3.drop(columns = ['index','id3','w3'],inplace = True)
#for volume standard deviaton
df4 = df.set_index('weekday').groupby('id')['total_volumes'].rolling(7).std()
df4 = df4.reset_index()
df4 = df4[df4.weekday == 0]
df4.rename(columns = {'id':'id4','weekday':'w4','total_volumes':'vol_std'},inplace = True)
df4 = df4.reset_index()
df4.drop(columns = ['index','id4','w4'],inplace = True)
#change the df to weekly and concat with df2
df = df[df['weekday'] == 0].sort_values(['id','time']).reset_index()
df = pd.concat([df, df2, df3, df4], axis=1)
df.drop(columns =['total_volumes'],inplace = True)

#filter out the useless rows(must apply the greater than 0 criteria since it is equivalent as null)
df = df[df['prices'].notnull()&
        (df['prices']>0)&   
        df['market_caps'].notnull()&
        (df['market_caps']>=1000000)&
        (df['volumes']>0)&              
        df['volumes'].notnull()
        ]

df.drop(columns = ['index','weekday'],inplace = True)
'''
#assign a key and filter out the bottom 20% volumes for each period

df['key'] = df.index

lowvol =    (df.groupby('time').
            apply(lambda x: x.nsmallest(int(len(x) * 0.2), 'volumes')).
            droplevel(0).reset_index().sort_index())

df = df[~ df.key.isin(lowvol.key)]
      
df.to_csv('vtop80.csv')
'''
df.to_csv('weekcdata.csv')