'''
Module for downloading and analyzing New York City Metro Transit Authority turnstile data
'''

import numpy as np
import pandas as pd

def load_mta(start,end):
    '''
    Takes data from the MTA website and loads it into a Pandas DataFrame.  Input
    your required years and date ranges in the download_dates variable and the function will obtain all
    files between those dates and concatenate them into a single dataframe.
    
    Should be string format YYYY-MM-DD
    '''
    
    download_dates = pd.date_range(start=start,end=end,freq='W-SAT')
    download_dates = download_dates.astype(str)
    
    base_url = ("http://web.mta.info/developers/data/nyct/turnstile/turnstile_{}.txt")
    list_of_url = [base_url.format(date[2:4]+date[5:7]+date[8:]) for date in download_dates]
    
    mta = pd.concat((pd.read_csv(url) for url in list_of_url))
    return mta


def clean_mta(mta):
    '''
    Does the following with the MTA data:
    converts the DATE and TIME fields to a single pandas datetime field
    gets the hour and day of week off of that datetime field, both as new columns
    calculates the number of passengers per row, returning the "riders_in" column
    '''

    # convert date and time fields into a single datetime field
    mta['datetime'] = mta.DATE + ' ' + mta.TIME  
    mta.datetime = pd.to_datetime(mta.datetime)
    mta = mta.drop(['DATE','TIME'],axis=1)
    
    # get hour and day of week from the datetime field
    mta['hour'] = mta.datetime.dt.hour  
    mta['day_of_week'] = mta.datetime.dt.dayofweek.map(
        {0:'M',1:'Tu',2:'W',3:'Th',4:'F',5:'Sa',6:'Su'})
    
    mta = mta[mta.DESC=='REGULAR'] # eliminate irregular audit data
    
    # sort values by turnstile and datetime so that the riders calculation runs smoothly
    mta = mta.sort_values(['STATION','C/A','UNIT','SCP','datetime']).reset_index(drop=True)
    
    # calculate ridership per time unit based on cumulative values
    # convert all instances of the first time period to null
    mta['riders_in'] = mta.ENTRIES.diff()
    mta['match'] = mta.SCP.eq(mta.SCP.shift())
    mta.loc[mta.match==False,'riders_in'] = np.nan
    return mta


def dedup(mta):
    '''
    reads in the cleaned MTA dataframe and returns a dataframe which combines values that have slight
    typos in the station names
    '''

    mta = mta[(mta.riders_in<20000) & (mta.riders_in>0)]

    mta.loc[mta.STATION=='42 ST-GRD CNTRL','STATION'] = 'GRD CNTRL-42 ST'
    mta.loc[mta.STATION=='42 ST-TIMES SQ','STATION'] = 'TIMES SQ-42 ST'
    mta.loc[mta.STATION=='59 ST COLUMBUS','STATION'] = '59 ST-COLUMBUS'
    mta.loc[mta.STATION=='MAIN ST','STATION'] = 'FLUSHING-MAIN'
    mta.loc[mta.STATION=='47-50 STS ROCK','STATION'] = '47-50 ST-ROCK'
    mta.loc[mta.STATION=='42 ST-PA BUS TE','STATION'] = '42 ST-PORT AUTH'
    mta.loc[mta.STATION=='14 ST-6 AVE','STATION'] = '14 ST'

    return mta