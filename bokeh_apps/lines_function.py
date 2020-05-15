#!/usr/bin/env python
# coding: utf-8

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


""" -------------------- Funtion to plot multi lines --------------------  """

def plot_bokeh_multi_lines(dataframes, title, 
                           dates_str,
                           label_modes,
                           line_width=1, size=8, plot_width=300, plot_height=220, 
                           tools="pan,wheel_zoom,reset,save", toolbar_location='below'):
    
    """ ----------- Dictionnary of data to pass to bokeh as argument and variables -----------  """
    df=dataframes[0]
    source = ColumnDataSource(df)
    col_names = source.column_names[1:-1] #not to take the index or integer column
    
    # Secondary source for visible circles
    visible_circles = df[df.integer == 0]
    source_visible=ColumnDataSource(visible_circles)

    """ ----------- Create a palette of colors -----------  """
    colors = palettes.all_palettes['Category10'][max(3,len(col_names))][:len(col_names)]
    
    """ ----------- Create the figure with lines and circles -----------  """
    p = figure(title=title,
               x_axis_type="datetime",
               plot_width=plot_width, plot_height=plot_height,
                   sizing_mode="scale_width",
               toolbar_location=toolbar_location, 
               tools=tools)
    
    # Create dictionary to store lines
    p_dict = dict() 
    
    for col, c, col_name in zip(df.columns[:-1], #not to take integer column
                                colors, col_names):
        # Add lines
        p_dict[col_name] = p.line('date', col, source=source, 
                                  color=c, line_width=line_width,
                                  muted_alpha=0.2)
        # Add circles
        p.circle('date', col, source=source_visible, 
                color=c, size=size,
                muted_alpha=0.2)
        
        # Add hover effect
        p.add_tools(HoverTool(
                            renderers=[p_dict[col_name]],
                            tooltips=[('date','@date{%Y-%m-%d}'),(col, f'@{col}')],
                            formatters={'@date': 'datetime'}))

    # Add legends to items as tuple containing both the name of the column and its line
    legend = Legend(items=[(x, [p_dict[x]]) for x in p_dict]) 
    p.add_layout(legend,'right')
    
    # Assign the click policy 
    p.legend.click_policy="mute" 
        
  
    """ ----------- Set up callbacks -----------  """
    # Update Map while changing feature or mode
    def update_map(attrname, old, new):
        # Switch current dataframe
        df=dataframes[button_mode.active]
        source.data = df
        
        int_date = date_slider.value  #Retrieve current date
        visible_circles = df[(df.integer == int_date)]
        source_visible.data = visible_circles
            
            
    # Update the slider on a click of the user
    def slider_update(attrname, old, new):
        # Retrieve current date
        int_date = date_slider.value
        date_slider.title = "Date :" + dates_str[int_date]
        
        # Change data
        df=dataframes[0]
        if len(label_modes)>0:
            df=dataframes[button_mode.active]
        visible_circles = df[(df['integer'] == int_date)]
        source_visible.data = visible_circles
        
    
    # Update the slider automatically when clicking on the animation button
    def animate_update():
        int_date = date_slider.value + 1
        # Go back to the beginning if slider reach the end
        if int_date > len(dates_str) - 1 :
            int_date = 0
        date_slider.value = int_date


    # Change the button label depending if it is playing or not
    callback_id = None
    def animate():
        global callback_id
        if button_animation.label == '► Play':
            button_animation.label = '❚❚ Pause'
            callback_id = curdoc().add_periodic_callback(animate_update, 200)
        else:
            button_animation.label = '► Play'
            curdoc().remove_periodic_callback(callback_id)
            
            
    """ ----------- Set up widgets and events -----------  """
    # Slider for the date
    date_slider = Slider(title="Date "+ dates_str[0], start = 0, end = len(dates_str)-1, value = 0, step=1, show_value=False)
    date_slider.on_change('value', slider_update)
            
    # Button to animate the slider
    button_animation = Button(label='► Play', width=60)
    button_animation.on_click(animate)

    # Set up inputs for layout
    inputs = widgetbox(date_slider, button_animation)
    
    # Set up Button to choose the displayed mode if they exists
    if len(label_modes)>0:
        button_mode = RadioButtonGroup(labels= label_modes, active=0)
        button_mode.on_change('active', update_map)
        # As the RadioButton isn't implemented with a title option, we add a PreText object before it
        title_button_mode = PreText(text= "Choose feature", style={'font-size':'12pt', 
                         'color': 'black', 
                         'font-family': 'sans-serif'})
        # update inputs
        inputs = widgetbox(title_button_mode, button_mode, date_slider, button_animation)
        
    # Set up layouts and add to document
    layout_doc = layout(p, inputs, sizing_mode="scale_width")
    
    # Handle rendering in HTML
    curdoc().add_root(layout_doc)
    curdoc().title = title

