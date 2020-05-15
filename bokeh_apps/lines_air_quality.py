#!/usr/bin/env python
# coding: utf-8

# In[1]:


import lines_function

# usual libraries
import numpy as np 
import pandas as pd 
import matplotlib.pyplot as plt
import json
import matplotlib.dates as dates
import datetime

# import from bokeh library
from bokeh.plotting import figure
from bokeh.io import output_notebook, push_notebook, show, curdoc
from bokeh.layouts import layout
from bokeh.models import (ColorBar, LogColorMapper, LogTicker, LinearColorMapper,
                          Button, CategoricalColorMapper, ColumnDataSource,
                          HoverTool, Label, SingleIntervalTicker, Slider, RadioButtonGroup, PreText, Legend)
from bokeh.application import Application
from bokeh.application.handlers import FunctionHandler
from bokeh.layouts import row, widgetbox, layout


# In[15]:


df_air = pd.read_csv("data/waqi-covid19-airqualitydata-2020.csv")

# Consider only measures in France
df_air = df_air[df_air.Country == "FR"]

# Convert string date to timestamp
df_air['Date'] = pd.to_datetime(df_air['Date'], format='%Y-%m-%d')
df_air.rename(columns={'Date': 'date'}, inplace=True)


# In[ ]:


df_air2020=df_air.groupby(['date','Specie']).mean()['median']

""" Air dataset at the same period in 2019  """

# Load dataset
df_air2019 =  pd.concat([pd.read_csv("data/waqi-covid19-airqualitydata-2019Q1.csv"), # January to March 2019 
                        pd.read_csv("data/waqi-covid19-airqualitydata-2019Q2.csv")], # April to June 2019 
                         ignore_index=True)

df_air2019 = df_air2019[df_air2019.Country == "FR"]

df_air2019.rename(columns={'Date': 'date'}, inplace=True)
df_air2019["date"] = pd.to_datetime(df_air2019["date"].apply(lambda x:"2020"+x[4:]), format='%Y-%m-%d') #cheat for merging

df_air2019=df_air2019.groupby(['Specie','date']).mean()['median']


# In[ ]:


df_air_merged = pd.merge(df_air2020, df_air2019,
                         how='inner', on=['Specie','date'])

df_air_merged.rename(columns={'median_x': '2020', 
                               'median_y': '2019'},
                      inplace=True)

df_air_merged.reset_index(inplace=True)
df_air_merged.set_index('date', inplace = True)


# In[ ]:


df_no2=df_air_merged[df_air_merged.Specie=='no2'][['2020','2019']]
df_so2=df_air_merged[df_air_merged.Specie=='so2'][['2020','2019']]
df_co=df_air_merged[df_air_merged.Specie=='co'][['2020','2019']]
df_o3=df_air_merged[df_air_merged.Specie=='o3'][['2020','2019']]
df_pm10=df_air_merged[df_air_merged.Specie=='pm10'][['2020','2019']]
df_pm25=df_air_merged[df_air_merged.Specie=='pm25'][['2020','2019']]


# In[ ]:


""" Initialization"""

# Get list of dates in the dataframe
quality_dates_str = df_no2.index.strftime('%m/%d/%Y')

# Add a new columns to order rows with integers
df_no2['integer'] = [i for i in range(len(df_no2))]
df_so2['integer'] = [i for i in range(len(df_so2))]
df_o3['integer'] = [i for i in range(len(df_o3))]
df_pm10['integer'] = [i for i in range(len(df_pm10))]
df_pm25['integer'] = [i for i in range(len(df_pm25))]

df_no2


# In[23]:


lines_function.plot_bokeh_multi_lines([df_no2,df_so2,df_o3,df_pm10,df_pm25],
                       "Emission of pollutants in France", 
                       dates_str=quality_dates_str, 
                       label_modes=['no2','so2','o3','pm10','pm25']
                      )

