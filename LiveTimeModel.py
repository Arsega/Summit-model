# -*- coding: utf-8 -*-

# wind turbine model


import pandas as pd
import os
from matplotlib import pyplot as plt

#------------------------------------------------------------------------------

# This code makes use of the 1 minute wind speed corrections, density,
# solar injection and wind direction binfile obtained with the Summit_data code
# to obtain the time live fraction of the radio stations at Summit for the RNO-G



# ------------------------------------------------------------------------------

# ---------------------------- input data---------------------------------------

# introduce the path to the data file generated wth SUmmit_Data code
path = ''
os.chdir(path)

df = pd.read_csv('Summit.csv')
df['DateTime'] = pd.to_datetime(df['DateTime'])



#Bcap_unit = 1.25             # Battery capacity of one unit (kWh)
#Bnum = 2                # Number of battery units (units)
Charge_lim =10           # Limit on charging current (A)
Bvolt = 25              # Battery voltage (V)
Pconsu = 28             # Power consumption (W)
Pconsu_winter = 3.5    # Power consumption in winter-over mode (W) 
Scfact = 1              # Turbine scale factor 

Bempty_percentage = 0.4        # Battery empty parcentage
WinterMode_percentage = 0.6     # Charge-state for switch to winter-over mode percentage
Bfull_percentage = 0.95         # Battery full percentage

Bcap = 200         # we are representing a single 25V battery with total capacity
                    # of 200 Ah 
Bcap = Bcap*60     # we want Amin
 
Bempty = Bempty_percentage*Bcap         # Battery empty (Ah)
WinterMode = WinterMode_percentage*Bcap # Charge-state for switch to winter-over mode percentage (Ah)
Bfull = Bfull_percentage*Bcap           # Battery full (Ah)



# Equation corresponding to the not shadowing power curve.
def power_curve(x):
    #p = 1.280889*x**2 -7.389423*x + 10.735132  # parallel configuration
    p = 1.025875*x**2 -5.105801*x + 6.157348   # parallel with mppt configuration
    return p

# Equation corresponding to the shadowing power curve.
def shadow_curve(x):
    #p = 0.505479*x**2 -2.404782*x +2.370268   # paraallel configuration
    p = 0.336815*x**2 -0.931191*x -1.015259   # parallel with mppt configuration
    return p



#-------------------------------------------------------------------------------

#-------------------------------- code -----------------------------------------
# we generate a new varibale which will gather all the information related to
# battery and its charging status

Bat = pd.DataFrame(df['DateTime'])

# cutoff for wind speed above 20 and 30 m/s
df['Wind_correct'] = [wind if wind <= 20 else 20 for wind in df['Wind_correct']]
df['Wind_correct'] = [wind if wind <= 30 else 0 for wind in df['Wind_correct']]


df2 =df['Wind_correct']
Bat = pd.concat([Bat,df2], axis=1)

# calu¡culates the power generated depending on the wind direction 
# ( using the different power curves depending on the shadowing status)
Bat.loc[df['Direction_bin'] == 0, 'Power_gen'] = Scfact*df['Density']/1.2929*power_curve(Bat['Wind_correct'])
Bat.loc[df['Direction_bin'] == 1, 'Power_gen'] = Scfact*df['Density']/1.2929*shadow_curve(Bat['Wind_correct'])


# We want to ensure that the fit do not generate erroneous values under 3.5 m/s
Bat['Power_gen'] = [x if x >= 0 else 0 for x in Bat['Power_gen']]
Bat.loc[Bat.Wind_correct < 3.5, 'Power_gen'] = 0
Bat = Bat.drop(['Wind_correct'], axis=1)


# Since the baterry status is influenced by the previous minute status, we use
# an iteration to calculate the power consumption depending on the winter mode status,
# then find the power balance, the current to the battery and finaly the new
# battery status, which is saved for the next iteration.
Bstat_list=[]
Bstat = Bcap
for i in range(0,len(Bat)):
    Power_consu = (Pconsu if Bstat > WinterMode else Pconsu_winter)
    Power_balance = Bat.at[i, 'Power_gen'] - Power_consu
    Current = min(Power_balance/Bvolt, Charge_lim)
    Bstat_prop = Bstat + Current
    Bstat = max(Bempty,min(Bstat_prop,Bcap),df.at[i,'solar injection'])
    Bstat_list.append(Bstat)


Bat['Bstat'] = Bstat_list
Bat=Bat.set_index('DateTime')


#------------------------------------------------------------------------------
# This part of the code calculates the number of hours we have in the data set,
# the number of hours the battery is in a good charge state to power the radio station,
# and the number of hours that the battery is empty.
# Using the conditions specified as input variables.

Hours=pd.DataFrame()
Hrs_clock_time = Bat['Bstat'].loc[Bat['Bstat'] > -1] 
Hrs_ok = Bat['Bstat'].loc[Bat['Bstat'] > WinterMode]
Hrs_empty = Bat['Bstat'].loc[Bat['Bstat'] <= Bempty]

Hours['Hrs clock time'] = Hrs_clock_time.groupby(by=[Hrs_clock_time.index.month]).count()
Hours['Hrs Ok'] = Hrs_ok.groupby(by=[Hrs_ok.index.month]).count()
Hours['Hrs empty'] = Hrs_empty.groupby(by=[Hrs_empty.index.month]).count()

Hours = Hours.fillna(0)
Hours = Hours.drop([4,10])
Hours.loc['total'] = Hours.sum()
Hours['live time frac'] = Hours['Hrs Ok']/Hours['Hrs clock time']

# Finaly we calculate the live time fraction of the radio station
frac = Hours['live time frac'].round(2)
frac_lable = frac.apply('{0:.2f}'.format)

# Returns a bar plot with the live time fractions for the winter months and the total.
fig, ax = plt.subplots(figsize=(13,11))
months = ['January', 'February', 'March', 'November', 'December', 'Total' ]
y_pos = range(len(months))
ax.set_title('Live time fraction for parallel with MPPT configuration' )
plt.xticks(y_pos, months, rotation=60)
bars = ax.bar(months, frac, 
              color=['lightblue', 'lightblue', 'lightblue', 'lightblue', 'lightblue', 'salmon'])
ax.bar_label(bars, frac_lable, label_type='center')
plt.show()
