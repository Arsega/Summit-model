# -*- coding: utf-8 -*-

import pandas as pd
import os
from os import listdir
from os.path import isfile, join


#------------------------------------------------------------------------

# This code makes use of 1 minute meteorological measurements recorded by
# NOAA at SUMMIT station, Greenland.
# All data files must be in a same directory 


# ------------------------------------------------------------------------------

# ---------------------------- input data---------------------------------------

# We first read all the data files and introduce them in a variable pandas DataFrame
# called df.

path = "/1 min"
os.chdir(path)

file_name = 'Summit.csv'  # name of the output file

files = [f for f in listdir(path) if isfile(join(path, f)) if f!= file_name]


col_name = ['DateTime','Location','Wind_direction','Wind_speed',
                           'Wind_steadiness_factor','Barometric_pressure',
                           'Temp_2m','Temp_10m','Temp_top','Relative_humidity',
                           'Precipitation_intensity']
df = pd.DataFrame() 

n=0
for f in files:
    df=pd.concat([df,pd.read_csv(f, header=None, delim_whitespace=True, parse_dates=[[1,2,3,4,5]],
                date_parser=lambda x: pd.to_datetime(x, format='%Y %m %d %H %M'))],ignore_index=True)
    n= n+1
    print(n)
    

df.columns = col_name


#------------------------------------------------------------------------------
# Correction of erroneous measurements: averaging wind velocity during all the winter months
#   For the pressure and temperature we change the value for the previous one

wind_ave = df['Wind_speed'].loc[(df.DateTime.dt.month <=2) | (df.DateTime.dt.month >= 11)]
wind_ave = wind_ave.loc[wind_ave >=0].mean()

bar_old = 686
temp_old = -11
for i in range(0,len(df)):
    bar_new = df['Barometric_pressure'][i]
    temp_new = df['Temp_2m'][i]
    if bar_new < -90:
        df.loc[i,'Barometric_pressure'] = bar_old
    else:
        bar_old = bar_new
    if temp_new < -90:
        df.loc[i, 'Temp_2m'] = temp_old
    else:
        temp_old = temp_new
    

df['Wind_correct'] = [x if x > -1 else wind_ave for x in df['Wind_speed']]
df['Wind_correct'] = [x if x > 0 else 0 for x in df['Wind_correct']]


#------------------------------------------------------------------------------

# Adding two new variables one corresponding to the solar injection on the 15th of October
# the other variable (Direction_bin) consists of 1 if the wind direction corresponds
# to the shadowing angles and 0 if there is no shadowing.

sol_inj = pd.DataFrame(df['DateTime'])     #Solar power injection
sol_inj.reset_index(drop=True, inplace=True)
sol_inj['solar injection'] = 0
#sol_inj = sol_inj.set_index('DateTime')
sol_inj.loc[(sol_inj.DateTime.dt.month==10) & (sol_inj.DateTime.dt.day==15) &
                               (sol_inj.DateTime.dt.hour==0) & (sol_inj.DateTime.dt.minute==0), 'solar injection' ] = 190


df['Direction_bin'] = [1 if 38 < x < 74 else 1 if 218 < x < 274 else 0 for x in df['Wind_direction']]

df['Density'] = 1.2929*273.15/(273.15+df['Temp_2m'])*df['Barometric_pressure']/1013  #calculates the density

df['solar injection'] = sol_inj['solar injection']


#-------------------------------------------------------------------------------
# drops all the columns not needed for the model and saves it to a csv file

df = df.drop(columns=['Location','Wind_speed', 'Wind_direction',
                           'Wind_steadiness_factor','Barometric_pressure',
                           'Temp_2m','Temp_10m','Temp_top','Relative_humidity',
                           'Precipitation_intensity'])

df.to_csv(file_name, index=False)
