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
#create return and marketcap from last week for later comparison and value weighting 
df['prices_lag1'] = df.groupby(['id'])['prices'].shift(1)
df['mkt_lag1'] = df.groupby('id')['market_caps'].shift(1)
#create time lag 1 to check if it is actually data from the last week
df['time_lag1'] = df.groupby(['id'])['time'].shift(1)
df = df[df['prices_lag1'].notnull()&        
        df['mkt_lag1'].notnull()]
df = df[(df['time']-df['time_lag1']).dt.days == 7]
df['return'] = (df['prices']/df['prices_lag1'])-1
#get price momentum for 1 to 4 week period and another one-to-four week momentum
for i in range(4):               
    df['return_lag{}'.format(i+1)] = (df['prices_lag1']/
                                      df.groupby('id')['prices'].shift(i+2))-1                
    df['time_lag{}'.format(i+2)] = df.groupby(['id'])['time'].shift(i+2)    
#below is the momentum for one-to-four week but named lag5 for easier use in loop 
df['return_lag5'] = ((df['return_lag4']+1)/(df['return_lag1']+1))- 1 

#construct the market excess return

mktret = df.groupby(['time']).apply(
        lambda g: pd.Series({                
            'mkt_ret': (g['return'] * g['mkt_lag1']).sum() / g['mkt_lag1'].sum()
        })
    ).reset_index()

#create a list to store results from different momentum period
pflist = [0,1,2,3,4]
olslist = [1,2,3,4,5]
#loop to construct the quintile portfolios with different momentum criterias
for i in range(5):
    df =df[df['return_lag{}'.format(i+1)].notnull()]
    #this is to check that the momentum time window is correct
    if i < 4:
        df = df[(df['time']-df['time_lag{}'.format(i+2)]).dt.days == 7*(i+2)]
    else:
        df = df[((df['time']-df['time_lag5']).dt.days == 35)&
                ((df['time']-df['time_lag2']).dt.days == 14)]
        
    df['bin'] = (
        df.groupby('time')    
        .apply(lambda group: np.ceil(group['return_lag{}'.format(i+1)].rank()/
                                     len(group['return_lag{}'.format(i+1)]) * 5))
        ).reset_index(level=[0], drop=True).sort_index()
    
    pflist[i] = (
        df
        .groupby(['time', 'bin'])
        .apply(
            lambda g: pd.Series({                
                'vw': (g['return'] * g['mkt_lag1']).sum() / g['mkt_lag1'].sum()
            })
        )
    ).reset_index()
    
    portfolios2 = pd.merge(
        pflist[i].query('bin==5'),
        pflist[i].query('bin==1'),
        suffixes=['_long', '_short'],
        on='time'
    )
    portfolios2['vw'] = portfolios2['vw_long'] - portfolios2['vw_short']
       
    olslist[i] = smf.ols('vw ~ 1 + mkt_ret', data=pd.merge(mktret, portfolios2, on='time')).fit()
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

    
        
    