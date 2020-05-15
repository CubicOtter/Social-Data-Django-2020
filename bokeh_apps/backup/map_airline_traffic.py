# -*- coding: utf-8 -*-
"""
Created on Tue May 12 10:56:18 2020

@author: tangu
"""

# usual libraries
import numpy as np 
import pandas as pd 
import seaborn as sns
sns.set(style='darkgrid', palette='muted', color_codes=True)
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
    


""" Load flights data and store data in dictionaries"""
def prepare_flights_data(lat_by_department, lon_by_department, department, df_cities):
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
    
    # Load dataset with list of airports
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
    
    """ Map each airport to the city in which they are"""

    # First we have to find all the airports in France
    # As we filtered the dataframe on the condition of having arrivel or departure in France
    # The french airports are the one which are both in the list of origin and destination aiports
    
    origin_aiports = df_flights_airports["origin_airport_name"].unique()
    destination_aiports = df_flights_airports["destination_airport_name"].unique()
    french_airports = [airport for airport in origin_aiports if airport in destination_aiports]
    
    # We now try to find a match for all airport in the cities dataset
    matches = [[], []]
    
    for airport_name in french_airports:
        for word in airport_name.replace('–', ' ').split(' '): #split airport names on both "-" and " "
            if word in list(df_cities["name"].unique()):
                matches[0].append(airport_name)
                matches[1].append(word)
    
    # For the unfound airports, it is because they have not the name of a city
    # We map them by hand 
    matches[0].append("Charles de Gaulle Airport")
    matches[1].append("Paris")
    matches[0].append("Berre - La Fare Aerodrome (UAF)")
    matches[1].append("Berre-l'Étang")
    matches[0].append("Istres-Le Tubé Air Base (BA 125)")
    matches[1].append("Istres")
    matches[0].append("Alpes–Isère Airport")
    matches[1].append("Saint-Étienne-de-Saint-Geoirs")
    
    # Create mapping dictionary
    matching_airport_city = dict(zip(matches[0], matches[1]))
    
    # Add two columns city in the airport dataframe using the matching dictionaries
    df_flights_airports['french_city_origin'] = df_flights_airports['origin_airport_name'].map(matching_airport_city)
    df_flights_airports['french_city_destination'] = df_flights_airports['destination_airport_name'].map(matching_airport_city)
    
    # Merge with city dataframe to have lat/lon data
    df_flight_airports_locations = pd.merge(df_flights_airports, df_cities, how='left', left_on='french_city_origin', right_on='name')
    del df_flight_airports_locations["name"]
    df_flight_airports_locations.rename(columns={"lon":'lon_origin',"lat":'lat_origin'}, inplace=True)
    
    df_flight_airports_locations = pd.merge(df_flight_airports_locations, df_cities, how='left', left_on='french_city_destination', right_on='name')
    del df_flight_airports_locations["name"]
    df_flight_airports_locations.rename(columns={"lon":'lon_destination',"lat":'lat_destination'}, inplace=True)
    
    
    """ Create one dataframe for intranational flights"""
    # Dataframe for intranational travels
    # Drop NA values is efficient, as international airport have NAN lat/lon
    df_intranational_flight = df_flight_airports_locations.dropna() 
    
    # Departures
    df_intranational_flight_departures = df_intranational_flight.groupby(['day', 'french_city_origin', 'lon_origin', 'lat_origin']).size().reset_index(name="number_flights")
    
    # Arrivals
    df_intranational_flight_arrivals = df_intranational_flight.groupby(['day', 'french_city_destination', 'lon_destination', 'lat_destination']).size().reset_index(name="number_flights")
    
    # Get same name of columns in the two datasets
    df_intranational_flight_departures.columns = ["day", "french_city", "lon", "lat", "number_flights"]
    df_intranational_flight_arrivals.columns = ["day", "french_city", "lon", "lat", "number_flights"]
    
    # Sum the two dataframe to get general intranational data
    df_intranational_flight = pd.concat([df_intranational_flight_departures, df_intranational_flight_arrivals]).groupby(['day','french_city', 'lon', 'lat'])['number_flights'].sum().reset_index()
    
    # Set day and city as index
    df_intranational_flight = df_intranational_flight.set_index(['french_city', 'day'])
    
    # Remove duplicate rows
    df_intranational_flight = df_intranational_flight.loc[~df_intranational_flight.index.duplicated(keep='first')]
    
    
    """ Create one dataframe for international flights"""
    # Dataframe for international travels
    # Get all rows with NA values
    df_international_flight = df_flight_airports_locations[df_flight_airports_locations.isna().any(axis=1)]
    
    # All na values in the dataframe are replaced by empty Strings
    df_international_flight = df_international_flight.replace(np.nan, '', regex=True)
    
    
    # Concatenate origin and destination airports to get the french airport involve in the travel
    df_international_flight['french_city'] = df_international_flight['french_city_origin'] + df_international_flight['french_city_destination']
    
    # Remove unwanted columns
    del df_international_flight['french_city_origin']
    del df_international_flight['french_city_destination']
    
    
    # Same treatment for origin and destination airport names
    df_international_flight['airport_name'] = df_international_flight['origin_airport_name'] + df_international_flight['destination_airport_name']
    del df_international_flight['origin_airport_name']
    del df_international_flight['destination_airport_name']
    
    
    # Convert lat and lon columns to String to process the same way
    df_international_flight['lon_origin'] = df_international_flight['lon_origin'].astype(str)
    df_international_flight['lon_destination'] = df_international_flight['lon_destination'].astype(str)
    df_international_flight['lat_origin'] = df_international_flight['lat_origin'].astype(str)
    df_international_flight['lat_destination'] = df_international_flight['lat_destination'].astype(str)
    
    # Concatenate lat and lon to get the coordinates of the french airport involve in the travel
    df_international_flight['lon'] = df_international_flight['lon_origin'] + df_international_flight['lon_destination']
    df_international_flight['lat'] = df_international_flight['lat_origin'] + df_international_flight['lat_destination']
    
    # Remove unwanted columns
    del df_international_flight['lon_origin']
    del df_international_flight['lon_destination']
    del df_international_flight['lat_origin']
    del df_international_flight['lat_destination']
    
    # Reconvert lat and lon columns to floats
    df_international_flight['lon'] = pd.to_numeric(df_international_flight['lon'],errors='coerce')
    df_international_flight['lat'] = pd.to_numeric(df_international_flight['lat'],errors='coerce')
    
    # Count number of flights at each date and each airport
    df_international_flight = df_international_flight.groupby(['day', 'french_city', 'lon', 'lat']).size().reset_index(name="number_flights")
    
    # Set day and city as index
    df_international_flight = df_international_flight.set_index(['french_city', 'day'])
    
    # Remove duplicate rows
    df_international_flight = df_international_flight.loc[~df_international_flight.index.duplicated(keep='first')]
    
    """ Preparation of dictionaries """
    # Initialization of dictionaries to contain data of each type of travel
    intranational_by_date_as_integer = {}
    international_by_date_as_integer = {}
    
    
    # Get list of ordered cities in the dataset
    airport_cities = matches[1]
    
    # Get lon and lat of each city of airport in the dataset
    lon_city_airport = []
    lat_city_airport = []
    for city in airport_cities:
        lon_city_airport.append(list(df_cities.loc[df_cities['name'] == city, 'lon'])[0])
        lat_city_airport.append(list(df_cities.loc[df_cities['name'] == city, 'lat'])[0])
        
    # Get list of dates in the dataset
    flights_dates = list(df_flight_airports_locations['day'].unique())
    
    # Initialization of list to fill with dates from dataframe as String
    flights_dates_str = [] 
    
    # Initizialisation of a counter of dates
    # We want each date to be provided an unique int id to use if in bokeh later
    id_date = 0
    
    
    """ Fill dictionaries  """
    # Create a dictionary with all dates as key, and list of related data for each city
    for date in flights_dates:
        # Initialization
        intranational_at_date = []
        international_at_date = []
        
        # Find numbler of flights in dataframe for each date, city and type of flight
        for city in airport_cities:
            # Fill intranational dictionary
            # If a statement is missing on a certain date, its assigned value is 0.
            if (city, date) not in df_intranational_flight.index:
                intranational_at_date.append(0) 
            else:
                intranational_at_date.append(df_intranational_flight.at[(city, date), 'number_flights'])
                
            # Fill international dicitonary
            # If a statement is missing on a certain date, its assigned value is 0.
            if (city, date) not in df_international_flight.index:
                international_at_date.append(0) 
            else:
                international_at_date.append(df_international_flight.at[(city, date), 'number_flights'])
    
        # Convert the date in pandas format datetime64 to format datetime
        date = convert_datetime64_to_datetime(date)
        
        # Convert the date in datetime format as a String
        date = date.strftime("%m/%d/%Y")
        
        # Add to the String converted date list
        flights_dates_str.append(date)
        
        # Update data dicitonary per date
        intranational_by_date_as_integer[id_date] = intranational_at_date
        international_by_date_as_integer[id_date] = international_at_date
        
        # Increase counter
        id_date += 1
        
        
    """ All dictionaries in one """
    flight_by_feature = {}
    flight_by_feature['intranational'] = intranational_by_date_as_integer
    flight_by_feature['international'] = international_by_date_as_integer
    
    
    """ Mapping size of points values """
    # Compute minimum and maximum for all dates and all species
    intranational_minimum = df_intranational_flight["number_flights"].min()
    international_minimum = df_international_flight["number_flights"].min()
    
    
    intranational_maximum = df_intranational_flight["number_flights"].max()
    international_maximum = df_international_flight["number_flights"].max()
    
    """ Linear mapping for the size of each point """
    # We want to map each value in range [minimum, maximum] to a value in range [5, 200]
    # I chose a minimum size of 5
    size_airport_city = {}
    
    size_airport_city["intranational"] = {}
    size_airport_city["international"] = {}       
                                                    
    for int_date in intranational_by_date_as_integer:
        size_airport_city["intranational"][int_date] = []                                                
        for old_value in intranational_by_date_as_integer[int_date]:
            new_value = old_value # no need of specific mapping as there are not a lot of intrnational flights in france
            size_airport_city["intranational"][int_date].append(new_value)
    
    for int_date in international_by_date_as_integer:
        size_airport_city["international"][int_date] = []
        for old_value in international_by_date_as_integer[int_date]:
            if old_value == 0:
                new_value = 0
            else:
                new_value = 5 + ((old_value - international_minimum) * (100 - 5)) / (international_maximum - international_minimum)
            size_airport_city["international"][int_date].append(new_value)
    
    return(flight_by_feature, size_airport_city, flights_dates_str, lon_city_airport, lat_city_airport, airport_cities)
        
        
""" -------------------- General variables for plot --------------------  """   
title = "Flights per airport per day in France"
lat_by_department, lon_by_department, name_department, department = get_department_data() 
df_cities = get_cities_data()
data_rate, data_size, flights_dates_str, lon_city_airport, lat_city_airport, airport_cities  = prepare_flights_data(lat_by_department, lon_by_department, department, df_cities)


# List of tools used in the map
tools = "pan,wheel_zoom,reset,hover,save"

# Size Maps
plot_width=450
plot_height=400

name_tooltips = "Energy consumption in the region"


""" ----------- Dictionnary of data to pass to bokeh as argument and variables -----------  """
# Data for the Shape of France on Map
data_shape =dict(x = lon_by_department,
          y = lat_by_department,
          name = name_department)

source = ColumnDataSource(data_shape)


# Data for the Shape of France on Map
data_cities1 = dict(x = lon_city_airport,
          y = lat_city_airport,
          sizes = data_size["intranational"][0],
          name = airport_cities,
          rate = data_rate["intranational"][0])
data_cities = ColumnDataSource(data_cities1)



""" ----------- Create the figure -----------  """

# General render of the shape of France and its departments
p = figure(title=title, 
           # tools=tools, # Hide tooltip for departments
           toolbar_location = 'below',
           x_axis_location=None, y_axis_location=None,
           plot_width=plot_width, plot_height=plot_height,
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
cities_points = p.circle('x', 'y', size = 'sizes', source = data_cities, 
                 color = 'red',  
                 alpha = 0.3, 
                 name="circle")


p.add_tools(HoverTool(renderers = [cities_points],
                  tooltips = [('City', '@name'),
                              ("(Long, Lat)", "($x, $y)"),
                              ('Number of flights', '@rate'),]))

""" ----------- Set up callbacks -----------  """          

# Update Map while changing feature or mode
def update_map(attrname, old, new):
    
    # Retrieve the new feature to use
    feature = label_features[button_choice.active] 
    
            
    # Update map
    int_date = date_slider.value # Get integer for the currently chosen date in the slider
    data_cities.data['rate'] = data_rate[feature][int_date]
    
    # Change color of points in figure
    if button_choice.active == 1:
        cities_points.glyph.fill_color = 'blue'
        cities_points.glyph.line_color = 'blue'
    else:
        cities_points.glyph.fill_color = 'red'
        cities_points.glyph.line_color = 'red'
    
    
# Update the slider on a click of the user
def slider_update(attrname, old, new):
    # Retrieve current date
    int_date = date_slider.value 
    date_slider.title = "Date :" + flights_dates_str[int_date]
    
    # Retrieve current feature Label
    feature = label_features[button_choice.active]
    
    # Change data
    data_cities.data['rate'] = data_rate[feature][int_date]
    data_cities.data['sizes'] = data_size[feature][int_date]
    
    # Change size of points in figure
    cities_points.glyph.size = 'sizes'

            

# Update the slider automatically when clicking on the animation button
def animate_update():
    int_date = date_slider.value + 1
    # Go back to the beginning if slider reach the end
    if int_date > len(flights_dates_str) - 1 :
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
label_features = ["intranational", "international"] # labels of possible features
button_choice = RadioButtonGroup(labels=["Intranational", "International"], active=0)
button_choice.on_change('active', update_map)
# As the RadioButton isn't implemented with a title option, we add a PreText object before it
title_button_choice = PreText(text= "Choose the type of flights to visualize", style={'font-size':'12pt', 
                 'color': 'black', 
                 'font-family': 'sans-serif'})

# Description for Slider
slider_explanation = PreText(text= "Slider per day", style={'font-size':'9pt', 
                 'color': 'black', 
                 'font-family': 'sans-serif'})

# Slider for the date
date_slider = Slider(title="Date "+ flights_dates_str[0], start = 0, end = len(flights_dates_str)-1, value = 0, step=1, show_value=False)
date_slider.on_change('value', slider_update)

# Button to animate the slider
button_animation = Button(label='► Play', width=60)
button_animation.on_click(animate)

title_lockdown = PreText(text= "Lockdown begins in France on March 16", style={'font-size':'12pt', 
                 'color': 'black', 
                 'font-family': 'sans-serif'})

# Set up layouts and add to document
inputs = widgetbox(title_button_choice, button_choice, slider_explanation, date_slider, button_animation, title_lockdown)
layout = row(p, inputs)

# Render in HTML
curdoc().add_root(layout)
curdoc().title = title
 
    