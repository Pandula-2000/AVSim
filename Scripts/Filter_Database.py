import pandas as pd
import numpy as np
import os
import numpy as np
from Agents2 import Agents
from DataLoader import Loader
from Patches import *
from disease_state_enum import Disease_State
import matplotlib.colors as mcolors
import matplotlib.cm as cm
import folium
from folium import plugins
from shapely.geometry import mapping
from Environment import *

# Env
env = LaunchEnvironment()

#Files
file_path = 'F:\Research_Assistant\Emulator_Engine\Emulator_V1\Scripts\Data_\Agent_contacts.xlsx'

def clean_dataframe(file_path):
    """
    Load data from a excel file, remove rows where 'Location' contains 'In Bus',
    and return the cleaned DataFrame.

    Parameters:
    - file_path: str, path to the input excel file.

    Returns:
    - pd.DataFrame: Cleaned DataFrame.
    """
    # Load the excel file into a DataFrame
    df = pd.read_excel(file_path, engine='openpyxl')

    
    # Remove rows where the 'Location' column contains 'In Bus'
    cleaned_df = df[df['Location'] != 'In Bus']
    
    return cleaned_df

use_df = clean_dataframe(file_path)
# print(use_df)

def plot_agent_locations_on_map(env, dataframe, day, folder):

    # Create a colormap
    cmap = mcolors.LinearSegmentedColormap.from_list("GreenRed", ["green", "orange", "red"])
    norm = mcolors.Normalize(vmin=0, vmax=50)
    
    # Initialize the Folium map centered at a specific location
    map_center = [7.293, 80.638]  # Replace with the approximate latitude and longitude of the region
    map_folium = folium.Map(location=map_center, zoom_start=12, tiles="OpenStreetMap")

    # # Define colors for different professional classes
    # class_colors = {
    #     'Student': 'cyan',
    #     'Teacher': 'purple',
    #     'Nurse': 'pink',
    #     'BankWorker': 'orange',
    #     'Other': 'gray'  # Default color for any unspecified classes
    # }

    # city_colors = {
    #     'KandyCity': 'red',
    #     'Pallekele': 'purple',
    #     'Gampola': 'yellow',
    #     'Kandy District' : 'magenta'
    # }

    # zone_colors = {
    #     'EducationZone': 'cyan',
    #     'ResidentialZone': 'purple',
    #     'CommercialFinancialZone': 'pink',
    #     'AdministrativeZone': 'orange',
    #     'MedicalZone': 'blue',
    #     'Other' : 'gray'  
    #     # Default color for any unspecified classes
    # }
    # Define darker colors for different professional classes
    class_colors = {
        'Student': 'blue',  # Orange Red '#2F4F4F',   # Dark Slate Gray
        'Teacher': '#FF4500', # '#556B2F',   # Dark Olive Green
        'Nurse': '#8B0000',     # Dark Red
        'BankWorker': '#8B4513', # Saddle Brown
        'Other': '#696969'      # Dim Gray
    }

    # Define distinct colors for different cities
    city_colors = {
        'KandyCity': '#FF4500',  # Orange Red
        'Pallekele': '#9932CC',  # Dark Orchid
        'Gampola': '#FFD700',    # Gold
        'Kandy District': '#FF1493'  # Deep Pink
    }

    # Define distinct colors for different zones
    zone_colors = {
        'EducationZone': '#00008B',  # Dark Blue
        'ResidentialZone': '#A52A2A', # Brown
        'CommercialFinancialZone': '#228B22', # Forest Green
        'AdministrativeZone': '#B22222', # Firebrick
        'MedicalZone': '#8A2BE2',   # Blue Violet
        'Other': '#D3D3D3'           # Light Gray
    }

    all_nodes = env.get_all_nodes()

    for node_name in all_nodes:
        node = env.graph.nodes[node_name]['node']

        # if not "_" in node_name:
        #     city_class = node_name.split('Sub_')[0]
        #     city_color = city_colors.get(city_class)
        #     geo_json = mapping(node.boundary)
        #     folium.GeoJson(
        #         geo_json,
        #         style_function=lambda feature, city_color=city_color: {
        #             'fillColor': 'white',
        #             'color': 'black',
        #             'weight': 4,
        #             'fillOpacity': 0.1,
        #         }
        #     ).add_to(map_folium)
        
        if "Zone" in node_name:
            zone_class = node_name.split('_')[0]
            fill_color = zone_colors.get(zone_class, zone_colors['Other'])
            # Convert node boundary to GeoJSON and add as a polygon
            geo_json = mapping(node.boundary)
            folium.GeoJson(
                geo_json,
                style_function=lambda feature, fill_color=fill_color: {
                    'fillColor': fill_color,
                    'color': 'black',
                    'weight': 2,
                    'fillOpacity': 0.4,
                }
                # style_function=lambda feature: {
                #     'fillColor': fill_color,
                #     'color': 'black',
                #     'weight': 2,
                #     'fillOpacity': 0.5,
                # }
            ).add_to(map_folium)



    fig, ax = plt.subplots(figsize=(16, 9))

    # # Draw node boundaries
    # for node_name in all_nodes:
    #     node = env.graph.nodes[node_name]['node']
    #     if node_name in ["KandyCity", "Pallekele", "Gampola"] or "Zone" in node_name:
    #         x, y = node.boundary.exterior.xy
    #         ax.plot(x, y, color='black')

    # print(use_df['Day'].unique())  # Check unique values in the Day column


    # Filter data for the given day
    # day_data = dataframe[dataframe['Day'] == day]

    # count = 0
    # print(day_data)

    # Plot agents
    for index, row in dataframe.iterrows():
        receiver = row['Receiver <--']
        sender = row['<-- Transmitter']
        # location = row['Location']
        point_str = row['Location Centroid']
        point_str = point_str.replace('POINT', '').strip(' ()')
        x, y = map(float, point_str.split())
        position = (y, x)  # Create a tuple with the parsed coordinates
        # Apply a small random offset to reduce overlap
        x_offset = random.uniform(-0.001, 0.001)  # Adjust as needed
        y_offset = random.uniform(-0.001, 0.001)  # Adjust as needed
        position = (y + y_offset, x + x_offset)  # Apply offsets to latitude and longitude
        rec_position = (y + y_offset, x + x_offset)
        # Extract class from receiver (e.g., Teacher_157 -> Teacher)
        professional_class = receiver.split('_')[0]
        send_class = sender.split('_')[0]
        # count += 1
        # print(count)
        # Use the defined color or fallback to 'Other'
        color = class_colors.get(professional_class, class_colors['Other'])
        send_color = class_colors.get(send_class, class_colors['Other'])
        # fill_color = zone_colors.get(zone_class, zone_colors['Other'])
        # Convert node boundary to GeoJSON and add as a polygon
        # print(f"Index: {index}, Coordinates: {position}, Professional Class: {professional_class}")

        # Add a circle marker at the same position
        folium.CircleMarker(
            location=rec_position,     # (lat, lon) format
            radius=4,              # Circle radius
            color=send_color,         # Border color
            weight = 2,
            fill=True,             # Enable fill
            fill_color=color,      # Fill color
            fill_opacity=0.7       # Opacity of the fill
        ).add_to(map_folium)

        # print(dataframe['Day'])

        if row['Day'] >= day:
            break

        # Plot the agent's location
        # ax.plot(position[0], position[1], 'o', color=color, markersize=10, label=professional_class)


    # Save map as an HTML file
    map_folium.save(f"{folder}/map_random.html")

    # Add legend for professional classes
    handles = [plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=color, markersize=8, label=cls)
               for cls, color in class_colors.items()]
    ax.legend(handles=handles, title="Professional Classes", loc='upper right')

    ax.set_aspect('equal')
    plt.title(f"Agent Locations")
    plt.savefig(f"{folder}/agents_day.png", dpi=300)
    plt.close()

folder = 'F:\Research_Assistant\Emulator_Engine\Emulator_V1\Results'

day = 50 #Upto which date
plot_agent_locations_on_map(env, use_df, day, folder)

# def visualize_agents_on_map(dataframe, env, day, folder):
#     """
#     Visualize agent locations on a map for a given day.

#     Parameters:
#         dataframe (pd.DataFrame): The dataframe containing agent data.
#         env: The environment object to extract additional details (if needed).
#         day (int): The day to display on the map.
#         folder (str): The folder to save the map.
#     """
#     # Initialize the Folium map centered at a specific location
#     map_center = [7.293, 80.638]  # Replace with the approximate latitude and longitude of the region
#     map_folium = folium.Map(location=map_center, zoom_start=12, tiles="OpenStreetMap")

#     # Define colors for professional classes
#     class_colors = {
#         "Student": "blue",
#         "Teacher": "purple",
#         "Nurse": "green",
#         "BankWorker": "orange",
#         "Other": "gray"  # Default color for unrecognized classes
#     }

#     # Iterate through the dataframe to add markers for each agent
#     for _, row in dataframe.iterrows():
#         receiver_class = row['Receiver'].split("_")[0]
#         agent_color = class_colors.get(receiver_class, "gray")

#         # Extract agent's coordinates
#         location = row['Location']

#         # Replace this with real coordinates from your environment
#         if location in env.get_all_nodes():
#             node = env.graph.nodes[location]['node']
#             bounds = node.boundary.bounds  # (minx, miny, maxx, maxy)
#             minx, miny, maxx, maxy = bounds

#             # Randomize coordinates within the cell bounds
#             rand_lat = random.uniform(miny, maxy)
#             rand_lon = random.uniform(minx, maxx)

#             # Add a circle marker for the agent
#             folium.CircleMarker(
#                 location=[rand_lat, rand_lon],
#                 radius=5,
#                 color=agent_color,
#                 fill=True,
#                 fill_opacity=0.8,
#                 popup=f"{row['Receiver']} ({receiver_class})"
#             ).add_to(map_folium)

#     # Save map as an HTML file
#     map_folium.save(f"{folder}/map_day_{day}.html")
#     return map_folium
