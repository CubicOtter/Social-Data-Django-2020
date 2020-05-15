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


# In[11]:


# Load three datasets with lists of flights
df_flights = pd.concat([pd.read_csv("data/flightlist_20200101_20200131.csv"), #flights on january 
                        pd.read_csv("data/flightlist_20200201_20200229.csv"), #flights on february
                        pd.read_csv("data/flightlist_20200301_20200331.csv"), #flights on march
                        pd.read_csv("data/flightlist_20200401_20200430.csv")],
                       ignore_index=True)

# Drop na values
df_flights.dropna()

#Get only flights which come or arrive in France
df_flights = df_flights[df_flights.origin.str.startswith("LF") | df_flights.destination.str.startswith("LF")]

# Convert date string to timestamp
df_flights["day"] = pd.to_datetime(df_flights["day"], format='%Y-%m-%d')

# Show dataframe
df_flights.head(2)


# **Lists of airports in France taken from the  [wiki page](https://en.wikipedia.org/wiki/List_of_airports_in_France):**

# In[12]:


df_airports = pd.read_csv("data/List_of_airports_in_France.csv")

# Merge the two datasets because df_flights only contains airport ICAO denomination.
# Merge on origin airports
df_flights_airports = pd.merge(df_flights, df_airports[['City served / Location','ICAO','Airport name']], 
                               how='left', left_on='origin', right_on='ICAO')

# Rename columns
df_flights_airports.rename(columns={"City served / Location":"origin_location",
                                   "ICAO":"origin_ICAO",
                                   "Airport name":"origin_airport_name"}, inplace=True)
# Delete origin column
del df_flights_airports['origin']

# Merge on destination airports
df_flights_airports = pd.merge(df_flights_airports, df_airports[['City served / Location','ICAO','Airport name']], 
                               how='left', left_on='destination', right_on='ICAO')

# Rename columns
df_flights_airports.rename(columns={"City served / Location":"destination_location",
                                   "ICAO":"destination_ICAO",
                                   "Airport name":"destination_airport_name"}, inplace=True)

# Delete destination column
del df_flights_airports['destination']

# Keep only interesting columns
df_flights_airports = df_flights_airports[["day", "origin_airport_name", "destination_airport_name"]]

# Show
df_flights_airports.head(2)


# In[13]:


#Get the number of flights each day
df_total_traffic = df_flights_airports.groupby('day').count()['origin_airport_name']

#Split df_flights_airports between intranational flights and international flights
df_intranational_traffic = df_flights_airports[df_flights_airports.origin_airport_name.isin(df_airports['Airport name'].to_list())
                                              & df_flights_airports.destination_airport_name.isin(df_airports['Airport name'].to_list())]

df_international_traffic = df_flights_airports[~df_flights_airports.index.isin(df_intranational_traffic.index)]

#Get the number of intranational flights each day
df_intranational_traffic= df_intranational_traffic.groupby('day').count()['origin_airport_name']
#Get the number of intranational flights each day
df_international_traffic= df_international_traffic.groupby('day').count()['origin_airport_name']


print("There are",df_intranational_traffic.sum(),"intranational flights in France")
print("There are",df_international_traffic.sum(),"international flights in France")

#Merge the 3 datasets
df_air_traffic = pd.merge(df_total_traffic, df_intranational_traffic, on='day') 
df_air_traffic = pd.merge(df_air_traffic, df_international_traffic, on='day') 

df_air_traffic.rename(columns={"day":"date",
                               "origin_airport_name_x":"total",
                               "origin_airport_name_y":"intranational",
                               "origin_airport_name":"international"},inplace=True)
df_air_traffic.index.names = ['date']

df_air_traffic.head(2)


# In[14]:


""" Initialization"""

# Get list of dates in the dataframe
air_dates_str = df_air_traffic.index.strftime('%m/%d/%Y')

# Add a new columns to order rows with integers
df_air_traffic['integer'] = [i for i in range(len(df_air_traffic))]


# In[22]:


lines_function.plot_bokeh_multi_lines([df_air_traffic],"French airline traffic", 
                       dates_str=air_dates_str, 
                       label_modes=[]
                      )

