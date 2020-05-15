#!/usr/bin/env python
# coding: utf-8

# In[1]:

# usual libraries

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
from bokeh.layouts import row, widgetbox, layout


""" Definition of general variables used in all bokeh Maps/Plots """

# Chose color palette
import bokeh.palettes as palettes

from bokeh.palettes import Viridis256 as palette
palette = tuple(reversed(palette))

# Other palettes
from bokeh.palettes import Inferno256 as palette_inferno
palette_inferno = tuple(reversed(palette_inferno))

from bokeh.palettes import RdYlGn as palette_11
palette_11 = palette_11[11]


# List of tools used in all Bokeh plots/maps
TOOLS = "pan,wheel_zoom,reset,hover,save"



df_hospital = pd.read_csv("data\donnees-hospitalieres-covid19-2020.csv", sep=";")

# Let's change columns name to make them more meaningful
df_hospital.rename(columns={"dep":"department",
                           "sexe":"gender",   
                           "jour":"date",
                           "hosp":"hospitalized",
                           "rea":"intensive_care",
                           "rad":"returned_home",
                           "dc":"death"}, inplace=True)

# We only need gender 0 which refers to men+women
df_hospital = df_hospital[df_hospital.gender==0]

# Convert string date to datetime
df_hospital["date"] = pd.to_datetime(df_hospital["date"], format='%Y-%m-%d')
df_hospital=df_hospital[["date","department","gender","hospitalized","intensive_care","death","returned_home"]]

# We are not interested in returned_home and gender
df_hospital_groupby = df_hospital.groupby(['date','department']).sum()
del df_hospital_groupby["gender"] 
del df_hospital_groupby["returned_home"]


#evolution over time for the whole country
df_hospital_France = df_hospital_groupby.sum(level=0)

# Rename columns
df_hospital_France .rename(columns={"hospitalized":"Hospitalized",
                           "intensive_care":"Intensive care",   
                           "death":"Cumulated deceased "}, 
                   inplace=True)


""" Initialization for bokeh"""

# Get list of dates in the dataframe
hospital_dates_str = df_hospital_France.index.strftime('%m/%d/%Y')

# Add a new columns to order rows with integers
df_hospital_France['integer']=[i for i in range(len(df_hospital_France))]



lines_function.plot_bokeh_multi_lines([df_hospital_France],"Evolution of the situation in France", 
                       dates_str=hospital_dates_str, 
                       label_modes=[])

