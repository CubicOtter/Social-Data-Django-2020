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


# In[6]:


df_energy = pd.concat([pd.read_csv("data/eco2mix-regional-2020.csv", sep=";"), #energy january-march 
                        pd.read_csv("data/eco2mix-regional-2020_V2.csv", sep=";")], #energy april-may 
                       ignore_index=True)


# Keep only data we are interested in
df_energy = df_energy[['Région', 'Date', 'Heure', 'Consommation (MW)', 'Thermique (MW)', 'Nucléaire (MW)']]


# Rename columns
df_energy.rename(columns={"Région":"region",
                           "Date":"date",    
                           "Heure":"hour",
                           "Consommation (MW)":"general_consumption",
                           "Thermique (MW)":"thermal_power",
                           "Nucléaire (MW)":"nuclear_power"
                           }, inplace=True)

# Drop NA values
df_energy = df_energy.dropna(subset=['date'])

# Convert string date to datetime
df_energy["date"] = pd.to_datetime(df_energy["date"], format='%Y-%m-%d')

# Show dataframe
print(df_energy.shape)
df_energy.head(3)


# In[7]:


#Group by date and region
df_energy_groupby = df_energy.groupby(["date","region"]).mean()

#energy consumption over time for the whole country
df_energy2020 = df_energy_groupby.sum(level=0)
df_energy2020.sort_index()

df_energy2020.head(2)


# In[8]:


#Same manipulation for 2019 data
df_energy2019 = pd.read_csv("data\eco2mix-regional-2019.csv", sep=";")

#convert string date to timestamp
df_energy2019.rename(columns={'Date': 'date'}, inplace=True)
df_energy2019["date"] = pd.to_datetime(df_energy2019["date"].apply(lambda x:"2020"+x[4:]), format='%Y-%m-%d') #cheat for merging
df_energy2019.drop(['Heure', 'Date - Heure'], axis=1, inplace=True)

#energy consumption over time for the whole country
df_energy2019 = df_energy2019.groupby(["date","Région"]).mean().sum(level=0)
df_energy2019.sort_index().head(2)


# In[9]:


# Merge 2019 and 2020 datasets
df_consumption = pd.merge(df_energy2019['Consommation (MW)'], df_energy2020['general_consumption'], 
                               how='inner', on='date')

# Rename such that all datasets have same features (otherwise it doesn't work on bokeh)
df_consumption.rename(columns={'Consommation (MW)': '2019_MW', 
                               'general_consumption': '2020_MW'},
                      inplace=True)

df_thermic = pd.merge(df_energy2019['Thermique (MW)'], df_energy2020['thermal_power'], 
                               how='inner', on='date')
df_thermic.rename(columns={'Thermique (MW)': '2019_MW', 
                               'thermal_power': '2020_MW'},
                      inplace=True)

df_nuclear = pd.merge(df_energy2019['Nucléaire (MW)'], df_energy2020['nuclear_power'], 
                               how='inner', on='date')
df_nuclear.rename(columns={'Nucléaire (MW)': '2019_MW', 
                               'nuclear_power': '2020_MW'},
                      inplace=True)

df_thermic.head(2)



""" Initialization"""

# Get list of dates in the dataframe
energy_dates_str = df_consumption.index.strftime('%m/%d/%Y')

# Add a new columns to order rows with integers
df_consumption['integer'] = [i for i in range(len(df_consumption))]
df_thermic['integer'] = [i for i in range(len(df_thermic))]
df_nuclear['integer'] = [i for i in range(len(df_nuclear))]



lines_function.plot_bokeh_multi_lines([df_consumption, df_thermic, df_nuclear],
                       "French energy consumption and production", 
                       dates_str=energy_dates_str, 
                       label_modes=['General consumption','Thermal power','Nuclear power']
                      )

