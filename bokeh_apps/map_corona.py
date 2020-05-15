# -*- coding: utf-8 -*-
"""
Created on Tue May 12 09:27:44 2020

@author: tangu
"""

""" Libraries """
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
from bokeh.plotting import figure
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



    
""" Load hospital data and store data in dictionaries"""
def prepare_hospital_data(lat_by_department, lon_by_department, department):
    # Load data
    df_hospital = pd.read_csv("data/donnees-hospitalieres-covid19-2020-05-13-19h00.csv", sep=";")
    
    #Let's change columns name to make them more meaningful
    df_hospital.rename(columns={"dep":"department",
                               "sexe":"gender",   
                               "jour":"date",
                               "hosp":"hospitalized",
                               "rea":"intensive_care",
                               "rad":"returned_home",
                               "dc":"death"}, inplace=True)
    
    # Convert string date to datetime
    df_hospital["date"] = pd.to_datetime(df_hospital["date"], format='%Y-%m-%d')
    df_hospital=df_hospital[["date","department","gender","hospitalized","intensive_care","death","returned_home"]]
    
    # We are not interested in returned_home and gender
    del df_hospital["gender"] 
    del df_hospital["returned_home"] 
    
    
    """ ### Treatment for cumulated hospital data """
    
    # We group by department
    df_hospital_groupby_department = df_hospital.groupby(['department']).sum()
    df_hospital_groupby_department.head()
    
    """ Filter the dataframe by departments which are both in the dataframe and the geojson """

    # Initialization
    unmatching_departments = []
    
    # List of ids from Dataframe
    department_dataframe = list(df_hospital_groupby_department.index.values)
    
    # Loop on all departments in the dataframe
    for id in department_dataframe:  
        
        # We remove the departments which are not in the geoJson file
        if id not in department:
            unmatching_departments.append(id)
            df_hospital_groupby_department = df_hospital_groupby_department.drop(id)
    
    
    """ Check if data from shapefile and data from dataframe are the same """
    department_dataframe = sorted(list(df_hospital_groupby_department.index.values))
    
    """ Get data from dataframe """

    # Initialization
    hospitalized_by_department = []
    intensive_care_by_department = []
    death_by_department = []
    
    
    # Fill the lists of data for each department in the same order as they appear in the department dictionary
    for id in department:
        hospitalized_by_department.append(df_hospital_groupby_department.at[id, 'hospitalized'])
        intensive_care_by_department.append(df_hospital_groupby_department.at[id, 'intensive_care'])
        death_by_department.append(df_hospital_groupby_department.at[id, 'death'])
      
    """ Treatment for hospital data per day """
    
    # There can be several lines for the same department and date. They must be grouped together.
    df_hospital.loc[(df_hospital['date'] == df_hospital["date"].min()) & (df_hospital['department'] == "01")]
    
    # We group by department and date
    df_hospital_groupby_department_and_date = df_hospital.groupby(['department', 'date']).sum()
    
    """ Initialization for all type of maps"""
    
    # Get list of dates in the dataframe
    hospital_dates = list(df_hospital['date'].unique())
    
    # Initialization of list to fill with dates from dataframe as String
    hospital_dates_str = [] 
    
    # Initizialisation of a counter of dates
    # We want each date to be provided an unique int id to use if in bokeh later
    id_date = 0
    
    """ Initialization concerning maps with non cumulated data """
    
    # Initialization of dictionaries to contain data for each date and each department
    hospitalized_by_date_as_integer = {}
    intensive_care_by_date_as_integer = {}
    death_by_date_as_integer = {}
    
    
    """ Initialization concerning maps with cumulated data """
    
    # Initialization of dictionaries to contain cumulated data for each date and each department
    cumulated_hospitalized_by_date_as_integer = {}
    cumulated_intensive_care_by_date_as_integer = {}
    cumulated_death_by_date_as_integer = {} 
    
    # Initialization of list to compute cumulated data for each day
    cumulated_hospitalized_helper = []
    cumulated_intensive_care_helper = []
    
    
    """ Fill all dictionaries """
    # Create a dictionary with all dates as key, and list of related data for each department as the related date as value
    # The list of data for each department is field in the same order as the department appear in the department dictionary
    for date in hospital_dates:
        
        # Initialization
        hospitalized_by_department_at_date = []
        intensive_care_by_department_at_date = []
        death_by_department_at_date = []
        
        # Find values in dataframe
        for id in department:
            hospitalized_by_department_at_date.append(df_hospital_groupby_department_and_date.at[(id, date), 'hospitalized'])
            intensive_care_by_department_at_date.append(df_hospital_groupby_department_and_date.at[(id, date), 'intensive_care'])
            death_by_department_at_date.append(df_hospital_groupby_department_and_date.at[(id, date), 'death'])
        
        # Convert the date in pandas format datetime64 to format datetime
        date = convert_datetime64_to_datetime(date)
        
        # Convert the date in datetime format as a String
        date = date.strftime("%m/%d/%Y")
        
        # Add to the String converted date list
        hospital_dates_str.append(date)
        
        # Update non cumulated data dictionaries
        hospitalized_by_date_as_integer[id_date] = hospitalized_by_department_at_date
        intensive_care_by_date_as_integer[id_date] = intensive_care_by_department_at_date
        
        # Death is already entered in the dataframe as a cumulated data
        cumulated_death_by_date_as_integer[id_date] = death_by_department_at_date
        
        # Compute number of new deaths
        if id_date == 0:
            death_by_date_as_integer[id_date] = cumulated_death_by_date_as_integer[id_date]
        else:
            # Zip list with pairs of elements from ancients and new cumulated data
            death_by_department_at_date_helper = zip(cumulated_death_by_date_as_integer[id_date], cumulated_death_by_date_as_integer[id_date-1])
        
            # Add difference to list
            death_by_date_as_integer[id_date] = [a_i - b_i for a_i, b_i in death_by_department_at_date_helper]
            
        
        # Update helpers to compute cumulated data
        if not cumulated_hospitalized_helper: # In the first turn, lists are empty
            cumulated_hospitalized_helper = hospitalized_by_department_at_date
            cumulated_intensive_care_helper = intensive_care_by_department_at_date
        else:
            # Create zipped lists with pairs of items from both lists
            zipped_hospitalized_lists = zip(cumulated_hospitalized_helper, hospitalized_by_department_at_date) 
            zipped_intensive_lists = zip(cumulated_intensive_care_helper, intensive_care_by_department_at_date) 
           
            
            # Sum each element of zipped list
            cumulated_hospitalized_helper = [sum(x) for x in zipped_hospitalized_lists]
            cumulated_intensive_care_helper = [sum(x) for x in zipped_intensive_lists]
        
        
        # Add to cumulated dictionaries  
        cumulated_hospitalized_by_date_as_integer[id_date] = cumulated_hospitalized_helper
        cumulated_intensive_care_by_date_as_integer[id_date] = cumulated_intensive_care_helper
    
            
        # Increase counter
        id_date += 1



    """ Rearrange data precedently extracted """
    
    """ Arranges dictionaries for all three features, cumulated or not """
    # Find the key of the latest updated cumulated data
    last_key = list(cumulated_hospitalized_by_date_as_integer.keys())[-1] 
    
    # Create and fill dictionary
    hospital_data_by_feature = {}
    hospital_data_by_feature['synthesis'] = {"hospitalized":cumulated_hospitalized_by_date_as_integer[last_key],
                                 "intensive_care": cumulated_intensive_care_by_date_as_integer[last_key],
                                 "death": cumulated_death_by_date_as_integer[last_key]}
    
    hospital_data_by_feature['by_date'] = {"hospitalized":hospitalized_by_date_as_integer,
                                 "intensive_care": intensive_care_by_date_as_integer,
                                 "death": death_by_date_as_integer}
    
    hospital_data_by_feature['cumulated'] = {"hospitalized":cumulated_hospitalized_by_date_as_integer,
                                 "intensive_care": cumulated_intensive_care_by_date_as_integer,
                                 "death": cumulated_death_by_date_as_integer}
    
    # Dictionary of min / max values for each combo of mode/feature
    hospital_data_min_max = {}
    
    hospital_data_min_max['synthesis'] = {"hospitalized": {"min": df_hospital_groupby_department["hospitalized"].min(),
                                                           "max": df_hospital_groupby_department["hospitalized"].max()},
                                 "intensive_care": {"min": df_hospital_groupby_department["intensive_care"].min(),
                                                           "max": df_hospital_groupby_department["intensive_care"].max()},
                                 "death": {"min": df_hospital_groupby_department["death"].min(),
                                                           "max": df_hospital_groupby_department["death"].max()}
                                         }
    
    hospital_data_min_max['by_date'] = {"hospitalized": {"min": df_hospital_groupby_department_and_date["hospitalized"].min(),
                                                           "max": df_hospital_groupby_department_and_date["hospitalized"].max()},
                                 "intensive_care": {"min": df_hospital_groupby_department_and_date["intensive_care"].min(),
                                                           "max": df_hospital_groupby_department_and_date["intensive_care"].max()},
                                 "death": {"min": df_hospital_groupby_department_and_date["death"].min(),
                                                           "max": df_hospital_groupby_department_and_date["death"].max()}
                                         }
    
    hospital_data_min_max['cumulated'] = {"hospitalized": {"min": df_hospital_groupby_department["hospitalized"].min(),
                                                           "max": df_hospital_groupby_department["hospitalized"].max()},
                                 "intensive_care": {"min": df_hospital_groupby_department["intensive_care"].min(),
                                                           "max": df_hospital_groupby_department["intensive_care"].max()},
                                 "death": {"min": df_hospital_groupby_department["death"].min(),
                                                           "max": df_hospital_groupby_department["death"].max()}
                                         }
    return(hospital_data_by_feature, hospital_data_min_max, hospital_dates_str)
    


    
    
""" -------------------- General variables for plot --------------------  """   
title = "Hospitalized since the beginning of Covid-19"
lat_by_department, lon_by_department, name_department, department = get_department_data() 
data_rate, data_min_max, hospital_dates_str  = prepare_hospital_data(lat_by_department, lon_by_department, department)

# Chosen color palette
from bokeh.palettes import Viridis256 as palette
palette = tuple(reversed(palette))

# List of tools used in the map
tools = "pan,wheel_zoom,reset,hover,save"

# Size Maps
plot_width=450
plot_height=400

name_tooltips = "Cases"
    

    
""" ----------- Create the color mapper -----------  """
color_mapper = LogColorMapper(palette=palette, low=data_min_max['synthesis']['hospitalized']["min"], high=data_min_max['synthesis']['hospitalized']["max"])


""" ----------- Dictionnary of data to pass to bokeh as argument and variables -----------  """

data=dict(x = lon_by_department,
          y = lat_by_department,
          name = name_department,
          rate = data_rate["synthesis"]['hospitalized'])

source=ColumnDataSource(data)

""" ----------- Create the figure -----------  """
p = figure(title=title, tools=tools,
           x_axis_location=None, y_axis_location=None,
           plot_width=plot_width, plot_height=plot_height,
           tooltips=[("Name", "@name"), (name_tooltips, "@rate"), ("(Long, Lat)", "($x, $y)")]
          )
p.grid.grid_line_color = None
p.hover.point_policy = "follow_mouse"

p.patches('x', 'y', source=source,
          fill_color={'field': 'rate', 'transform': color_mapper},
          fill_alpha=0.7, line_color="black", line_width=0.5)

#Add color bar to figure
color_bar = ColorBar(color_mapper=color_mapper, ticker=LogTicker(),
                     label_standoff=12, border_line_color=None, location=(0,0))

p.add_layout(color_bar, 'right')


""" ----------- Set up callbacks -----------  """
# Update Map while changing feature or mode
def update_map(attrname, old, new):
    
    # Retrieve the new feature and mode to use
    feature = label_features[button_choice.active] 
    mode = label_modes[button_mode.active] 
    
    # Update the title of the graph
    title_update(feature, mode)
    
    # Update the color map
    color_mapper_update(feature, mode)
    
    # Update map
    if mode == "synthesis":
        source.data['rate'] = data_rate[mode][feature]
        date_slider.visible = False # Hide timeline slider
        button_animation.visible = False # Hide animation button
    else:
        int_date = date_slider.value # Get integer for the currently chosen date in the slider
        source.data['rate'] = data_rate[mode][feature][int_date]
        date_slider.visible = True   # Show timeline
        button_animation.visible = True # Show animation button


# Update title of map when feature or mode is changed
def title_update(feature, mode):
    if mode == "synthesis" or mode == "by_date":
        if feature == "hospitalized":
            first_word = "Hospitalized"
        if feature == "intensive_care":
            first_word = "Intensive-cares"
        if feature == "death":
            first_word = "Deaths"
        if mode == "by_date":
            new_title = first_word + " by day since the beginning of Covid-19 spread"
        else:
            new_title = first_word + " since the beginning of Covid-19 spread"
    else:
        if feature == "hospitalized":
            second_word = "hospitalized"
        if feature == "intensive_care":
            second_word = "intensive-cares"
        if feature == "death":
            second_word = "deaths"
        new_title = "Cumulated " + second_word +  " since the beginning of Covid-19 spread"
    p.title.text = new_title
            
  
    
# Update color mapper of map when features or mode displayed are changed
def color_mapper_update(feature, mode):
    # Change the limits of the Color Mapper
    color_mapper.update(low = data_min_max[mode][feature]["min"], high = data_min_max[mode][feature]["max"])
        

# Update the slider on a click of the user
def slider_update(attrname, old, new):
    # Retrieve current date
    int_date = date_slider.value 
    date_slider.title = "Date :" + hospital_dates_str[int_date]
    
    # Retrieve current feature and mode label
    mode = label_modes[button_mode.active]
    feature = label_features[button_choice.active]
    
    # Change data
    source.data['rate'] = data_rate[mode][feature][int_date]


# Update the slider automatically when clicking on the animation button
def animate_update():
    int_date = date_slider.value + 1
    # Go back to the beginning if slider reach the end
    if int_date > len(hospital_dates_str) - 1 :
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
label_features = ["hospitalized", "intensive_care", "death"] # labels of possible features
button_choice = RadioButtonGroup(labels=["Hospitalized", "Intensive Care", "Death"], active=0)
button_choice.on_change('active', update_map)
# As the RadioButton isn't implemented with a title option, we add a PreText object before it
title_button_choice = PreText(text= "Choose the feature to display", style={'font-size':'12pt', 
                 'color': 'black', 
                 'font-family': 'sans-serif'})


# Button to choose the displayed mode: synthesis, by_date, cumulated
label_modes = ["synthesis", "by_date", "cumulated"] # labels of possible features
button_mode = RadioButtonGroup(labels= ["Synthesis", "By Day", "Cumulated"], active=0)
button_mode.on_change('active', update_map)
# As the RadioButton isn't implemented with a title option, we add a PreText object before it
title_button_mode = PreText(text= "Choose display mode ", style={'font-size':'12pt', 
                 'color': 'black', 
                 'font-family': 'sans-serif'})

# Slider for the date
date_slider = Slider(title="Date "+ hospital_dates_str[0], start = 0, end = len(hospital_dates_str)-1, value = 0, step=1, show_value=False)
date_slider.on_change('value', slider_update)
date_slider.visible = False # Initially the slider is not visible

# Button to animate the slider
button_animation = Button(label='► Play', width=60)
button_animation.on_click(animate)
button_animation.visible = False # Initially the slider is not visible
   

# Set up layouts and add to document
inputs = widgetbox(title_button_choice, button_choice, title_button_mode, button_mode, date_slider, button_animation)
layout = row(p, inputs)

# Handle rendering in HTML
curdoc().add_root(layout)
curdoc().title = title


