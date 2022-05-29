# -*- coding: utf-8 -*-
"""
Created on Mon May 23 2022

@author: Bill
"""

import os
import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
from scipy.stats import stats
from statsmodels.iolib.summary2 import summary_col

os.chdir(r'C:\Users\Bill\Desktop\HKU\7037\HW2\Crypto')
#df = pd.read_csv('vtop80.csv')
df = pd.read_csv('weekcdata.csv')
df['time'] = pd.to_datetime(df['time'])

df['prices_lag1'] = df.groupby(['id'])['prices'].shift(1)
df['return'] = (df['prices']-df['prices_lag1'])/df['prices_lag1']

df['mkt_lag1'] = df.groupby('id')['market_caps'].shift(1)
df['maxp_lag1'] = df.groupby('id')['maxprc'].shift(1)
df['prices_lag1'] = df.groupby('id')['prices'].shift(1)
df['volumes_lag1'] = df.groupby('id')['volumes'].shift(1)
df['vol_std_lag1'] = df.groupby('id')['vol_std'].shift(1)
df['time_lag1'] = df.groupby(['id'])['time'].shift(1)

df = df[(df['time']-df['time_lag1']).dt.days == 7]
#construct the market excess return
mktret = df.groupby(['time']).apply(
        lambda g: pd.Series({                
            'mkt_ret': (g['return'] * g['mkt_lag1']).sum() / g['mkt_lag1'].sum()
        })
    ).reset_index()

pflist = [1,2,3,4,5]
olslist = [1,2,3,4,5]
y = 0
for x in ['mkt_lag1','prices','maxprc','volumes_lag1','vol_std_lag1']:
    df = df[df[x].notnull()]
    df['bin'] = (
        df.groupby('time')    
        .apply(lambda group: np.ceil(group[x].rank() / len(group[x]) * 5))
        ).reset_index(level=[0], drop=True).sort_index()

    pflist[y] = (
        df
        .groupby(['time', 'bin'])
        .apply(
            lambda g: pd.Series({                
                'vw': (g['return'] * g['mkt_lag1']).sum() / g['mkt_lag1'].sum()
            })
        )
    ).reset_index()
    
    portfolios2 = pd.merge(
        pflist[y].query('bin==5'),
        pflist[y].query('bin==1'),
        suffixes=['_short', '_long'],
        on='time'
    )
    portfolios2['vw'] = portfolios2['vw_long'] - portfolios2['vw_short']
       
    olslist[y] = smf.ols('vw ~ 1 + mkt_ret', data=pd.merge(mktret, portfolios2, on='time')).fit()
    
    
    y += 1

#get average of different bins    
def getbinmean(dt):
    x = dt.groupby('bin').agg(avgret_vw=('vw', 'mean')).sort_values('bin')['avgret_vw'].tolist()
    return x
#get t score of each mean
def getbintstat(dt):
    x = []
    for i in range(5):
       x.append(stats.ttest_1samp(dt[dt['bin']==i+1]['vw'],0).statistic)
    return x

listmean = []
listtstat = []

for m in pflist:
    listmean.append(getbinmean(m))
    listtstat.append(getbintstat(m))
#store the results to dataframe
dfm = pd.DataFrame(columns = [1,2,3,4,5],data = listmean) #dataframe of mean return
dft = pd.DataFrame(columns = [1,2,3,4,5],data = listtstat) #dataframe of t score
print(summary_col(olslist,stars=True,float_format='%0.2f',info_dict={
    'talpha': lambda x: "{:.2f}".format(x.tvalues.tolist()[0]),
    'tbeta': lambda x: "{:.2f}".format(x.tvalues.tolist()[1])}).as_latex())





