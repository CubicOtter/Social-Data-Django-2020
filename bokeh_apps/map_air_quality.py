# -*- coding: utf-8 -*-
"""
Created on Tue May 12 11:16:46 2020

@author: tangu
"""

# usual libraries
import numpy as np 
import pandas as pd 
import json
import datetime

# Function to convert the date in pandas format datetime64 to format datetime
# It is easier to get dates as String after that
def convert_datetime64_to_datetime( usert: np.datetime64 )->datetime.datetime:
    t = np.datetime64( usert, 'us').astype(datetime.datetime)
    return(t)


# import from bokeh library
from bokeh.models import ColorBar, LogColorMapper, LogTicker, LinearColorMapper
from bokeh.plotting import figure
from bokeh.io import curdoc
from bokeh.layouts import layout
from bokeh.models import (Button, CategoricalColorMapper, ColumnDataSource,
                          HoverTool, Label, SingleIntervalTicker, Slider, RadioButtonGroup, PreText)
from bokeh.layouts import row, widgetbox, layout
from bokeh.transform import linear_cmap


""" Load GeoJson file and store data in dictionary"""
# Load geojson file with department data
def get_department_data():
    with open('data/departements.geojson.txt') as f:
        geodata = json.load(f)
        
    
    # Initialization
    department = {}          # To store geodata for each department
    lat_by_department = []   # List of lists of lat for each department
    lon_by_department = []   # List of list of lon for each department
    name_department = []     # List of names of departments
    
    
    # Loop on all department in the geojson loaded file
    for feature in geodata['features']:
        
        # Retrieves the number of the department and add it to list
        number = feature['properties']['code'] 
        
        
        # Retrieves the name of the department and add it to list
        name = feature['properties']['nom']
        name_department.append(name)
        
        # Retrieves the coordinates of the shape of the department
        coordinates = feature['geometry']['coordinates']  
        
        lat = []
        lon = []
        
        # For some region, the coordinates are entered in a really weird way
        # You have to play with lists nested in lists
        for j in range(len(coordinates)):
            lat_intermediate = []
            lon_intermediate = []
            for i in range(len(coordinates[j])):
                if len(coordinates[j][i]) == 2:
                    lat_intermediate.append(coordinates[j][i][1])
                    lon_intermediate.append(coordinates[j][i][0])
                else:
                    for k in range(len(coordinates[j][i])):
                        lat_intermediate.append(coordinates[j][i][k][1])
                        lon_intermediate.append(coordinates[j][i][k][0])
            if len(lat_intermediate) > len(lat):
                lat = lat_intermediate
                lon = lon_intermediate
               
    
        # Add to list of lat and lon for each department
        lat_by_department.append(lat)
        lon_by_department.append(lon)    
        
        # Add new entry to dictionary
        # The number of department is the key
        # The value of the dictionary is a dictionary containign both the name of the department, and list with latitudes and longitudes
        department[number] = {'name':name, 'lat': lat, 'lon': lon}
        
    return(lat_by_department, lon_by_department, name_department, department)
    
    
""" Prepare cities dataframe """
def get_cities_data():
    # load dataset
    df_cities = pd.read_csv("data/villes_france.csv", sep=",", names=[i for i in range(26)])
    
    # Keep only columns we are interested in
    df_cities = df_cities[[4, 18, 19]]
    
    # Rename columns
    df_cities.columns = ['name', 'lon', 'lat']
    
    return(df_cities)


""" General function to prepare an air dataset """
def preparation_air_dataset(df_air, df_cities):

    # Consider only measures in France
    df_air = df_air[df_air.Country == "FR"]

    
    # We are only interested in the species of pollutants
    # Co is not very relevant, it's value is always close to 0
    df_air = df_air[df_air['Specie'].isin(["pm10", "pm25", "no2", 'o3', 'so2'])]

    # Convert string date to timestamp
    df_air['Date'] = pd.to_datetime(df_air['Date'], format='%Y-%m-%d')

    # Keep only data we are interested in
    df_air = df_air[["Date", "Specie", "City", "median"]]

    
    # Group by City/Date/Specie and get average median value for each week for each city
    df_air_position = df_air
    df_air_position['Date'] = pd.to_datetime(df_air_position['Date']) - pd.to_timedelta(7, unit='d')
    df_air_position = df_air_position.groupby(['City', pd.Grouper(key='Date', freq='W-MON'), 'Specie'])['median'].mean().reset_index().sort_values('Date')

    # Merge dataset with the dataset of french cities to get their position
    df_air_position = pd.merge(df_air_position, df_cities, how='left', left_on='City', right_on='name')
    del df_air_position["name"]

        
    # Add a column week number
    df_air_position['week_number'] = df_air_position['Date'].dt.week

    # Round the previously calculated average of medians
    df_air_position["median"] = df_air_position["median"].round()

    # Set city, date, specie as index
    df_air_by_date_city = df_air_position.set_index(['City', 'Date', "Specie"])

    return(df_air, df_air_position, df_air_by_date_city)


""" Function to compute dictionaries for Bokeh Map """
def dictionaries_for_bokeh_map(df_air_by_date_city, air_dates, air_cities, pollutants):
    
    """ Initialization of variables """
    # Initialization of dictionaries to contain data of each specie for each week, city 
    pm10_by_date_as_integer = {}
    pm25_by_date_as_integer = {}
    no2_by_date_as_integer = {}
    o3_by_date_as_integer = {}
    so2_by_date_as_integer = {}


    # Initialization of list to fill with dates from dataframe as String
    air_dates_str = [] 

    # Initizialisation of a counter of dates
    # We want each date to be provided an unique int id to use it in a bokeh slider
    id_date = 0


    """ Fill dictionaries  """
    # Create a dictionary with all dates as key, and list of related data for each city
    for date in air_dates:

        # Initialization
        pm10_by_city_at_date = []
        pm25_by_city_at_date = []
        no2_by_city_at_date = []
        o3_by_city_at_date = []
        so2_by_city_at_date = []

        # Find median value in dataframe for each city and specie
        for city in air_cities:
            
            for specie in pollutants:
                # If a statement is missing on a certain date, its assigned value is 0.
                if (city, date, specie) not in df_air_by_date_city.index:
                    eval(specie + '_by_city_at_date').append(0) # eval allow to retrieve a variable using its name as a String
                else:
                    eval(specie + '_by_city_at_date').append(df_air_by_date_city.at[(city, date, specie), 'median'])

        # Convert the date in pandas format datetime64 to format datetime
        date = convert_datetime64_to_datetime(date)

        # Convert the date in datetime format as a String
        date = date.strftime("%m/%d/%Y")

        # Add to the String converted date list
        air_dates_str.append(date)

        # Update non cumulated data dictionaries
        for specie in pollutants:
            eval(specie + '_by_date_as_integer')[id_date] = eval(specie + '_by_city_at_date')

        # Increase counter
        id_date += 1

    """ All dictionaries in one """
    air_pollution_by_pollutant = {}

    for specie in pollutants:
        air_pollution_by_pollutant[specie] = eval(specie + '_by_date_as_integer')
        
    return(air_pollution_by_pollutant, air_dates_str)



""" Load air quality data and store data in dictionaries"""
def prepare_air_quality_data(lat_by_department, lon_by_department, department, df_cities):
    """ Air dataset during corona  """
    # Load dataset
    df_air_corona = pd.read_csv("data/waqi-covid19-airqualitydata-2020.csv")
    
    # Prepare datasets
    df_air_corona, df_air_position_corona, df_air_by_date_city_corona = preparation_air_dataset(df_air_corona, df_cities)
    
    
    """ Generate list of important elements of the corona dataset  """
    
    # Get list of ordered dates in the dataset
    air_dates_corona = list(df_air_position_corona['Date'].unique())
    
    # Get list of ordered week number in dataset
    air_week = list(df_air_position_corona['week_number'].unique())
    
    # List of pollutants
    pollutants = list(df_air_corona["Specie"].unique())
    
    # Get list of ordered cities in the dataset
    air_cities = list(df_air_corona["City"].unique())
    
    # Get lon and lat of each city in the dataset
    lon_city = []
    lat_city = []
    for city in air_cities:
        lon_city.append(list(df_air_position_corona.loc[df_air_position_corona['City'] == city, 'lon'])[0])
        lat_city.append(list(df_air_position_corona.loc[df_air_position_corona['City'] == city, 'lat'])[0])
        
        
    """ Air dataset at the same period in 2019  """

    # Load dataset
    df_air_2019 =  pd.concat([pd.read_csv("data/waqi-covid19-airqualitydata-2019Q1.csv"), # January to March 2019 
                            pd.read_csv("data/waqi-covid19-airqualitydata-2019Q2.csv")], # April to June 2019 
                             ignore_index=True)
    
    # Prepare datasets
    df_air_2019, df_air_position_2019, df_air_by_date_city_2019 = preparation_air_dataset(df_air_2019, df_cities)
    
    # Filter on the cities and week which are in the corona dataset
    df_air_position_2019 = df_air_position_2019[df_air_position_2019["City"].isin(air_cities)]
    df_air_position_2019 = df_air_position_2019[df_air_position_2019["week_number"].isin(air_week)]
    
    df_air_by_date_city_2019 = df_air_by_date_city_2019[df_air_by_date_city_2019.index.isin(air_cities, level=0)]
    df_air_by_date_city_2019 = df_air_by_date_city_2019[df_air_by_date_city_2019["week_number"].isin(air_week)]
    
    # Get list of ordered dates in the dataset
    air_dates_2019 = list(df_air_position_2019['Date'].unique())
    
    """ Creation of dictionaries for both corona and 2019 maps """
    air_pollution_by_pollutant_corona, air_dates_str_corona = dictionaries_for_bokeh_map(df_air_by_date_city_corona, air_dates_corona, air_cities, pollutants)
    air_pollution_by_pollutant_2019, air_dates_str_2019 = dictionaries_for_bokeh_map(df_air_by_date_city_2019, air_dates_2019, air_cities, pollutants)

    """ Creation of dictionary containing min/max values for the color mapping """
    # Compute min / max
    pm10_minimum = min(df_air_position_corona[df_air_position_corona["Specie"] == "pm10"]["median"].min(), df_air_position_2019[df_air_position_2019["Specie"] == "pm10"]["median"].min())
    pm25_minimum = min(df_air_position_corona[df_air_position_corona["Specie"] == "pm25"]["median"].min(), df_air_position_2019[df_air_position_2019["Specie"] == "pm25"]["median"].min())
    no2_minimum = min(df_air_position_corona[df_air_position_corona["Specie"] == "no2"]["median"].min(), df_air_position_2019[df_air_position_2019["Specie"] == "no2"]["median"].min())
    o3_minimum = min(df_air_position_corona[df_air_position_corona["Specie"] == "o3"]["median"].min(), df_air_position_2019[df_air_position_2019["Specie"] == "o3"]["median"].min())
    so2_minimum = min(df_air_position_corona[df_air_position_corona["Specie"] == "so2"]["median"].min(), df_air_position_2019[df_air_position_2019["Specie"] == "so2"]["median"].min())
    
    pm10_maximum = min(df_air_position_corona[df_air_position_corona["Specie"] == "pm10"]["median"].max(), df_air_position_2019[df_air_position_2019["Specie"] == "pm10"]["median"].max())
    pm25_maximum = min(df_air_position_corona[df_air_position_corona["Specie"] == "pm25"]["median"].max(), df_air_position_2019[df_air_position_2019["Specie"] == "pm25"]["median"].max())
    no2_maximum = min(df_air_position_corona[df_air_position_corona["Specie"] == "no2"]["median"].max(), df_air_position_2019[df_air_position_2019["Specie"] == "no2"]["median"].max())
    o3_maximum = min(df_air_position_corona[df_air_position_corona["Specie"] == "o3"]["median"].max(), df_air_position_2019[df_air_position_2019["Specie"] == "o3"]["median"].max())
    so2_maximum = min(df_air_position_corona[df_air_position_corona["Specie"] == "so2"]["median"].max(), df_air_position_2019[df_air_position_2019["Specie"] == "so2"]["median"].max())
    
    # Fill min / max dictionary
    air_data_min_max = {}
    for specie in pollutants:
        air_data_min_max[specie] = {"min": eval(specie + "_minimum"), "max": eval(specie + "_maximum")}

    return(air_pollution_by_pollutant_corona, air_pollution_by_pollutant_2019, air_data_min_max, air_dates_str_corona, air_dates_str_2019, lon_city, lat_city, air_cities)




""" -------------------- General variables for plot --------------------  """   
title = 'Comparison air pollution before and during Covid-19'
title1 = 'Air Pollution in France - Beginning of 2020'
title2 = 'Air Pollution in France at the same period in 2019'
lat_by_department, lon_by_department, name_department, department = get_department_data() 
df_cities = get_cities_data()
data_rate1, data_rate2, data_min_max, air_dates_str1, air_dates_str2, lon_city, lat_city, air_cities  = prepare_air_quality_data(lat_by_department, lon_by_department, department, df_cities)

# Chosen color palette
from bokeh.palettes import RdYlGn as palette
palette = palette[11]

# List of tools used in the map
tools = "pan,wheel_zoom,reset,hover,save"

# Size Maps
plot_width=450
plot_height=400

name_tooltips = "Energy consumption in the region"


""" ----------- Create the color mapper -----------  """
color_mapper = linear_cmap(field_name='rate', palette=palette ,low=data_min_max["pm10"]["min"] ,high=data_min_max["pm10"]["max"])


""" ----------- Dictionnary of data to pass to bokeh as argument and variables -----------  """

# Data for the Shape of France on Map
data_shape =dict(x = lon_by_department,
          y = lat_by_department,
          name = name_department)

source = ColumnDataSource(data_shape)


# Data concerning corona map
data_cities1 = dict(x = lon_city,
          y = lat_city,
          name = air_cities,
          rate = data_rate1["pm10"][0])
data_cities_source1 = ColumnDataSource(data_cities1)


# Data concerning corona map
data_cities2 = dict(x = lon_city,
          y = lat_city,
          name = air_cities,
          rate = data_rate2["pm10"][0])
data_cities_source2 = ColumnDataSource(data_cities2)



""" ----------- Create the figures -----------  """

# General render of the shape of France and its departments
def create_figure_departments(title, data_cities, source = source, color_mapper = color_mapper):
    p = figure(title=title, 
               # tools=tools, # Hide tooltip for departments
               toolbar_location = 'below',
               x_axis_location=None, y_axis_location=None,
               plot_width=plot_width, plot_height=plot_height,
               sizing_mode="scale_width",
               # tooltips=[("Department", "@name"), ("(Long, Lat)", "($x, $y)")] 
              )

    p.xgrid.grid_line_color = None
    p.ygrid.grid_line_color = None
    # p.hover.point_policy = "follow_mouse"

    p.patches('x', 'y', source=source,
              fill_color=None, 
              line_color = 'gray', 
              line_width = 0.25, 
              fill_alpha = 1) 
    
    # Add circle at the position of cities
    # Their size depends of the air pollution rate
    cities_points = p.circle('x', 'y', size = 25, source = data_cities, 
                     line_color = color_mapper, color = color_mapper, 
                     alpha = 0.45, 
                     name="circle")
    
    p.add_tools(HoverTool(renderers = [cities_points],
                  tooltips = [('City', '@name'),
                              ("(Long, Lat)", "($x, $y)"),
                              ('Pollutant concentration', '@rate')]))

    return(p, cities_points)


figure1, cities_points1 = create_figure_departments(title1, data_cities_source1)
figure2, cities_points2 = create_figure_departments(title2, data_cities_source2)


#Add color to only one of the figures
color_bar = ColorBar(color_mapper=color_mapper['transform'],
                     label_standoff=12, border_line_color=None, location=(0,0))

figure2.add_layout(color_bar, 'right')
  



""" ----------- Set up callbacks -----------  """          

# Update Map while changing feature or mode
def update_map(attrname, old, new):
    
    # Retrieve the new feature to use
    feature = label_features[button_choice.active] 
    
    # Update color mapper
    color_mapper_update(feature)
    
    # Update maps
    int_date = date_slider.value # Get integer for the currently chosen date in the slider
    data_cities_source1.data['rate'] = data_rate1[feature][int_date]
    data_cities_source2.data['rate'] = data_rate2[feature][int_date]
    
    
# Update color mapper of map when features displayed are changed
def color_mapper_update(feature):
    # Change the limits of the Color Mapper
    color_mapper['transform'].low=data_min_max[feature]["min"]
    color_mapper['transform'].high=data_min_max[feature]["max"]


# Update the slider on a click of the user
def slider_update(attrname, old, new):
    # Retrieve current date
    int_date = date_slider.value 
    date_slider.title = "Date Corona: " + air_dates_str1[int_date] + "    - Date 2019: " + air_dates_str2[int_date]
    
    # Retrieve current feature Label
    feature = label_features[button_choice.active]
    
    # Change data
    data_cities_source1.data['rate'] = data_rate1[feature][int_date]
    data_cities_source2.data['rate'] = data_rate2[feature][int_date]
    
    # Change size of points in figure
    # cities_points.glyph.size = 'sizes'

            

# Update the slider automatically when clicking on the animation button
def animate_update():
    int_date = date_slider.value + 1
    # Go back to the beginning if slider reach the end
    if int_date > len(air_dates_str1) - 1 :
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

# Button to choose the feature to display in the map
label_features = ["pm10", "pm25", "no2", "o3", "so2"] # labels of possible features
button_choice = RadioButtonGroup(labels=label_features, active=0)
button_choice.on_change('active', update_map)
# As the RadioButton isn't implemented with a title option, we add a PreText object before it
title_button_choice = PreText(text= "Choose the concentration of the pollutants to visualize", 
                              style={'font-size':'12pt', 
                 'color': 'black', 
                 'font-family': 'sans-serif'})

# Description for Slider
slider_explanation = PreText(text= "Slider per Week", style={'font-size':'9pt', 
                 'color': 'black', 
                 'font-family': 'sans-serif'})

# Slider for the date
date_slider = Slider(title="Date Corona: " + air_dates_str1[0] + "    - Date 2019: " + air_dates_str2[0], 
                     start = 0, end = len(air_dates_str1)-1, value = 0, step=1, show_value=False)
date_slider.on_change('value', slider_update)

# Button to animate the slider
button_animation = Button(label='► Play', width=60)
button_animation.on_click(animate)


title_containment = PreText(text= "Lockdown begins in France on March 16", style={'font-size':'12pt', 
                 'color': 'black', 
                 'font-family': 'sans-serif'})

# Set up layouts and add to document
inputs = widgetbox(title_button_choice, button_choice, slider_explanation, date_slider, button_animation, title_containment)
layout_doc = layout([figure1, figure2], inputs, sizing_mode="stretch_both")


# Render on HTML
curdoc().add_root(layout_doc)
curdoc().title = title
