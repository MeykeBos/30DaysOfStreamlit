# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

# Import libraries
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import math

from collections import Counter
from collections.abc import Iterable
from collections import defaultdict

from branca.element import Figure
import branca.colormap

import folium
from folium import plugins
from folium.plugins import HeatMap

from shapely.geometry import MultiPoint, MultiLineString, MultiPolygon
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
from shapely.geometry import MultiPolygon
from shapely.ops import nearest_points

import requests

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

px.set_mapbox_access_token('pk.eyJ1IjoibWV5a2V2YW5kZW5ib3MiLCJhIjoiY2tyMjRnMm42Mjd5ajMxcXBhb2V5OThobyJ9.bzt4sDKsF3BsPMAQz9jT1A')
from IPython.display import HTML

import plotly.figure_factory as ff

from streamlit_folium import folium_static


# Define functions




# Load data
@st.cache
def load_data():
    url= 'https://drive.google.com/file/d/1zi6RRWukdMaCCQpCXEyhRt01zIrIg4-F/view?usp=sharing'
    url='https://drive.google.com/uc?id=' + url.split('/')[-2]
    df = pd.read_csv(url)
    #df = pd.read_csv("C:/Users/Meyke/Documents/Projecten/Streamlit_app/partially_cleaned_5.csv")
    
    bins = []
    labels = []
    x = -50
    while x < 3000:
        bins.append(x)
        labels.append(x)
        x += 100
    labels.remove(-50)
    df['altitude_binned'] = pd.cut(df['altitude'], bins=bins, labels=labels)
    
    df['age'] = df.apply(lambda row: 2015 - row.construction_year if row.construction_year != 0 else np.nan, axis=1)
    df['bool_status_group'] = df.apply(lambda row: 1 if row.status_group == "functional" else 0, axis=1)
    df['bool_status_group_not'] = df.apply(lambda row: 1 if row.status_group == "non functional" else 0, axis=1)

    
    df = df.sort_values('construction_year', ascending=True)
    return(df)

df = load_data()



# Create new dataframe: table_region
table_region = pd.pivot_table(df, values=['functional','functional_needs_repair','non_functional'], index=['region'],
                     aggfunc=np.sum)
table_region['total'] = table_region.apply(lambda row: row.functional + row.functional_needs_repair + row.non_functional, axis=1)
table_region['%_functional'] = table_region.apply(lambda row: row.functional/row.total * 100, axis=1)
table_region['%_functional_needs_repar'] = table_region.apply(lambda row: row.functional_needs_repair/row.total * 100, axis=1)
table_region['%_non_functional'] = table_region.apply(lambda row: row.non_functional/row.total * 100, axis=1)

# Create new dataframe: table_lga
table_lga = pd.pivot_table(df, values=['functional','functional_needs_repair','non_functional'], index=['lga_copy'],
                     aggfunc=np.sum)
table_lga['total'] = table_lga.apply(lambda row: row.functional + row.functional_needs_repair + row.non_functional, axis=1)
table_lga['%_functional'] = table_lga.apply(lambda row: row.functional/row.total * 100, axis=1)
table_lga['%_functional_needs_repar'] = table_lga.apply(lambda row: row.functional_needs_repair/row.total * 100, axis=1)
table_lga['%_non_functional'] = table_lga.apply(lambda row: row.non_functional/row.total * 100, axis=1)

# Create new dataframe: table
table = pd.pivot_table(df, values='id', index=['altitude_binned', 'extraction_type_class'],
                    columns=['status_group'], aggfunc='count')
table['perc_functional'] = table.apply(lambda row: np.nan if  (row.functional + row['functional needs repair'] + row['non functional']) == 0 else
                                       row.functional / (row.functional + row['functional needs repair'] + row['non functional']) *100, axis=1)
table['perc_Nonfunctional'] = table.apply(lambda row: np.nan if  (row.functional + row['functional needs repair'] + row['non functional']) == 0 else
                                       row['non functional'] / (row.functional + row['functional needs repair'] + row['non functional']) *100, axis=1)
table.reset_index(inplace=True)
table['count'] = table.apply(lambda row: row.functional + row['functional needs repair'] + row['non functional'], axis=1)




# Build dashboard
# add a side bar
add_sidebar = st.sidebar.selectbox('test',('Analysis country','Analysis by region'))

# add data to the page based on selected option
if add_sidebar == 'Analysis country':
    st.write('Hello, *World!* :sunglasses:')
    st.header('Tanzanian Waterpumps')
    
    perc_functional = df[(df['status_group'] == 'functional')]['id'].count()/df[df['status_group'].notna()]['id'].count()*100
    perc_non_functional = df[(df['status_group'] == 'non functional')]['id'].count()/df[df['status_group'].notna()]['id'].count()*100
    perc_repair = df[(df['status_group'] == 'functional needs repair')]['id'].count()/df[df['status_group'].notna()]['id'].count()*100
    #survival_rate_avg = df[df['Survived'] == 1]['PassengerId'].count() / df['PassengerId'].count()
    
    list_survival_metrics = [perc_functional,perc_non_functional,perc_repair]
    list_survival_rates = ['Percentage of functional pumps', 'Percentage of non functional pumps', 'Percentage of pumps in need of repair']
    
    col1, col2, col3 = st.columns(3)
    columns = [col1, col2, col3]
    
    count = 0
    for i in list_survival_rates:
        with columns[count]:
            st.metric(label = i, value =  round(list_survival_metrics[list_survival_rates.index(i)],3)) #delta = round(list_survival_metrics[list_survival_rates.index(i)] - survival_rate_avg,3)
            count += 1
            if count >= 3:
                count = 0
    
    fig = px.scatter_mapbox(df[df['status_group'].notna()], 
                        lat="latitude", 
                        lon="longitude", 
                        hover_name="id", 
                        hover_data=["status_group","id"],
                        color='status_group',
                        #color_discrete_sequence=["yellow"], 
                        zoom=5, 
                        height=850, 
                        width=1050, 
                        animation_frame="construction_year", 
                        size='distance_closest_pump',size_max=10)

    fig.update_layout(
        mapbox_style="carto-darkmatter")
    
    st.subheader("Waterpumps in Tanzania by their construction year and status")
    st.text("The size of the circles correspond to the distance to another waterpump that is nearest. The larger the circle, the further the closest pump.")
    st.plotly_chart(fig, use_container_width =True)  
    
#    st.subheader("Percentage of functional pumps per area")
    
#    fig2 = ff.create_hexbin_mapbox(
#        data_frame=df[df['status_group'].notna()], lat="latitude", lon="longitude",
#        nx_hexagon=30, opacity=0.9, labels={"color": "Percentage functional"},
#        color="bool_status_group", agg_func=np.mean, color_continuous_scale="sunset", range_color=[0,1],
#        width=1000, height=800, zoom=5)
#    st.plotly_chart(fig2, use_container_width =True) 

    st.subheader("Waterpumps by status and population")  
    st.text("The size corresponds to the population the pump serves")

    colors = ["royalblue","crimson","lightseagreen"]
    cities = ['functional', 'non functional', 'functional needs repair']
    scale = 500
    
    fig2 = go.Figure()
    
    for i in cities:
        #lim = limits[i]
        df_sub = df[df['status_group'] == i]
        fig2.add_trace(go.Scattermapbox(mode = "markers",  
                            lat= df_sub['latitude'], 
                            lon= df_sub['longitude'],
                            
            marker = dict(
                size = df_sub['population']/scale,
                color = colors[cities.index(i)],
            ),name=i
            ))
    
    fig2.update_layout(
        margin ={'l':0,'t':0,'b':0,'r':0},
        mapbox = {
            'center': {'lon': df['longitude'].mean(), 'lat': df['latitude'].mean()},
            'style': "stamen-terrain",
            'zoom': 5})
    
    fig2.update_layout(
            title_text = 'waterpumps by status given the population size it serves',
            showlegend = True,
            
        )

    st.plotly_chart(fig2, use_container_width =True)

if add_sidebar == 'Analysis by region':
    #st.write('Title')
    
    # Create another selection box, the values need to be provided in tuple format
    regions = tuple(df['region'].unique())
    region_select = st.selectbox('Select a region',regions)
    
    st.header('Waterpumps by functional status')
    
    
    
    df_filtered = df[df['region'] == region_select]
            #df_filtered['Embarked'] = df_filtered['Embarked'].apply(get_embarked)
            #df_filtered.sort_values('Survived', inplace = True)
    
    total_pumps = len(df_filtered)
    perc_of_all_pumps = (total_pumps/len(df))*100
    
    list_metrics = [total_pumps, perc_of_all_pumps]
    list_labels = ["Total amount of pumps", "Percentage of all pumps in the country"]
    
    col1, col2 = st.columns(2)
    columns =[col1,col2]
    
    count = 0
    for i in list_labels:
        with columns[count]:
            st.metric(label = i, value =  round(list_metrics[list_labels.index(i)],3))
            count += 1
            if count >= 2:
                count = 0   
    
    
    #st.metric(label = "Total amount of pumps", value=total_pumps)
    
    st.subheader('Distribution by status and difference with country-wide percentages')
            
    perc_functional_r = df_filtered[(df_filtered['status_group'] == 'functional')]['id'].count()/df_filtered[df_filtered['status_group'].notna()]['id'].count()*100
    perc_non_functional_r = df_filtered[(df_filtered['status_group'] == 'non functional')]['id'].count()/df_filtered[df_filtered['status_group'].notna()]['id'].count()*100
    perc_repair_r = df_filtered[(df_filtered['status_group'] == 'functional needs repair')]['id'].count()/df_filtered[df_filtered['status_group'].notna()]['id'].count()*100
    
    perc_functional = df[(df['status_group'] == 'functional')]['id'].count()/df[df['status_group'].notna()]['id'].count()*100
    perc_non_functional = df[(df['status_group'] == 'non functional')]['id'].count()/df[df['status_group'].notna()]['id'].count()*100
    perc_repair = df[(df['status_group'] == 'functional needs repair')]['id'].count()/df[df['status_group'].notna()]['id'].count()*100
    
    list_survival_metrics = [perc_functional,perc_non_functional,perc_repair]
    list_survival_rates = ['Percentage of functional pumps', 'Percentage of non functional pumps', 'Percentage of pumps in need of repair']
    
    list_survival_metrics_r = [perc_functional_r,perc_non_functional_r,perc_repair_r]
    list_survival_rates_r = ['Percentage of functional pumps', 'Percentage of non functional pumps', 'Percentage of pumps in need of repair']
    
    col1, col2, col3 = st.columns(3)
    columns = [col1, col2, col3]
    
    count = 0
    for i in list_survival_rates_r:
        with columns[count]:
            st.metric(label = i, value =  round(list_survival_metrics_r[list_survival_rates_r.index(i)],3), delta = round(list_survival_metrics_r[list_survival_rates_r.index(i)] - list_survival_metrics[list_survival_rates.index(i)],3))
            count += 1
            if count >= 3:
                count = 0        
    
    # Create a locations list
    locations = df_filtered[['latitude', 'longitude']]
    locationlist = locations.values.tolist()
    
    # Create a distance to other pump list
    distancelist = df_filtered['distance_closest_pump'].to_list()
        
    # Create a status list
    statuslist = df_filtered['status_group'].to_list()
    
    m = folium.Map(location=[df_filtered['latitude'].mean(), df_filtered['longitude'].mean()], tiles='Stamen Toner', zoom_start=8)
    
    folium.TileLayer('Stamen Terrain').add_to(m)
    folium.TileLayer('Stamen Toner').add_to(m)
    folium.TileLayer('Stamen Water Color').add_to(m)
    folium.TileLayer('cartodbpositron').add_to(m)
    folium.TileLayer('cartodbdark_matter').add_to(m)
    folium.LayerControl().add_to(m)
    
    for point in range(0, len(locationlist)):
        if statuslist[point] == 'functional':
    
                folium.Circle(
                    radius=distancelist[point],
                    location=locationlist[point],
                    #popup="The Waterfront",
                    color="#006E33",
                    fill=True,
                ).add_to(m)
            
        elif statuslist[point] == 'non functional':
    
                folium.Circle(
                    radius=distancelist[point],
                    location=locationlist[point],
                    #popup="The Waterfront",
                    color="#CD001A",
                    fill=True,
                ).add_to(m)
            
        elif statuslist[point] == 'functional needs repair':
    
                folium.Circle(
                    radius=distancelist[point],
                    location=locationlist[point],
                    #popup="The Waterfront",
                    color="#FF850F",
                    fill=True,
                ).add_to(m)
            
        else:
                folium.Circle(
                    radius=distancelist[point],
                    location=locationlist[point],
                    #popup="The Waterfront",
                    color="#008AD8",
                    fill=True,
                ).add_to(m)
    
    st.subheader('Locations of the waterpumps')
    st.text('The size of the circles correspond with the shortest distance to another waterpump. The larger the circle, the further the nearest pump. Green corresponds to functional pumps, orange to pumps in need of repair, red to non functional pumps, and for blue circles, the status is unkown.')
    folium_static(m)
    
    

