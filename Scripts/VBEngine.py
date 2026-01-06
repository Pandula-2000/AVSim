import numpy as np
from DiseaseModels.VectorBorneModel import *
from Agents2 import Agents
from DataLoader import Loader
from Patches import *
from disease_state_enum import Disease_State
import matplotlib.colors as mcolors
import matplotlib.cm as cm
import folium
from folium import plugins
from shapely.geometry import mapping

GRID_SIZE = 500 # 500 meters

state_timer_dict = Loader.get_state_timer_dict_VB()

# Initialize patch grid    
def init_patch_grid(env, t_min, t_max):
    all_patches = []
    all_nodes = env.get_all_nodes()
    zones = [node for node in all_nodes if "Zone" in node]

    grid_size = GRID_SIZE
    for zone_name in zones:
        zone = env.graph.nodes[zone_name]['node']
        zone.create_patch_grid(grid_size)
        rows, columns = len(zone.patch_grid), len(zone.patch_grid[0])
        minx, miny, maxx, maxy = zone.boundary.bounds

        cell_width = (maxx - minx) / columns
        cell_height = (maxy - miny) / rows

        # Iterate over each cell in the grid
        for i in range(rows):
            for j in range(columns):
                # Create a bounding box for the current grid cell
                cell_minx = minx + j * cell_width
                cell_miny = miny + i * cell_height
                cell_maxx = cell_minx + cell_width
                cell_maxy = cell_miny + cell_height
                
                cell_box = box(cell_minx, cell_miny, cell_maxx, cell_maxy)

                # Check if the cell intersects with the polygon
                if zone.boundary.intersects(cell_box):
                    ind = (i, j)
                    sus = np.random.randint(0,100)
                    exp = 0 # np.random.randint(0,5)
                    inf = 0 # np.random.randint(0,5)
                    temp = np.random.randint(t_min, t_max)
                    
                    zone.patch_grid[i][j] = Patch(zone_name, ind, cell_box, (rows, columns), sus, exp, inf, temp)
                    all_patches.append(zone.patch_grid[i][j])
        
        update_locations_and_patch(env, zone_name)
    return all_patches


def assign_initial_infection(env, zone_class = "ResidentialZone", 
                             zone_number=2, 
                             location = "Home", 
                             location_number=2,
                             density = ((50,30), (30,10), (10,0)),
                             agnt_count = 5,
                             specific = None
                             ):
    
    if specific:
        zone_name = list(env.graph.predecessors(specific))[0]
        zone = env.graph.nodes[zone_name]['node']
        update_infections(env, specific, zone, density, agnt_count)
    else:
        all_nodes = env.get_all_nodes()
        zone_names = all_nodes if zone_class == "any" else [name for name in all_nodes if zone_class in name]
        
        if len(zone_names) == 0: 
            print(f"No {zone_class}")
            return

        random_zone_names = zone_names if zone_number > len(zone_names) else  random.sample(zone_names, zone_number)
        for random_zone_name in random_zone_names:
            zone = env.graph.nodes[random_zone_name]['node']
            children = list(env.graph.successors(random_zone_name))
            locations = children if location == "any" else [name for name in children if location in name]

            if len(locations) == 0: 
                print(f"No {location} in {random_zone_name}")
                return
        
            random_locations = locations if location_number > len(locations) else random.sample(locations, location_number)
            for random_location in random_locations:  
                update_infections(env, random_location, zone, density, agnt_count)
            
        
def update_infections(env, location, zone, density, agnt_count):             
    row, col = get_patch_for_location(env, location)
    
    # Update infections in patches
    for di in range(-2, 3):  # Iterate from -2 to 2
        for dj in range(-2, 3):  # Iterate from -2 to 2
            new_row, new_col = row + di, col + dj

            # Check if the neighboring patch is within the grid bounds
            if (0 <= new_row < len(zone.patch_grid) 
                and 0 <= new_col < len(zone.patch_grid[0]) 
                and zone.patch_grid[new_row][new_col]):
                current_count = zone.patch_grid[new_row][new_col]._infected_count
                if di == 0 and dj == 0:
                    # Center patch
                    zone.patch_grid[new_row][new_col]._infected_count = max(random.randint(density[0][1], density[0][0]), current_count)
                elif abs(di) <= 1 and abs(dj) <= 1:
                    # First outer layer
                    zone.patch_grid[new_row][new_col]._infected_count = max(random.randint(density[1][1], density[1][0]), current_count)
                else:
                    # Second outer layer
                    zone.patch_grid[new_row][new_col]._infected_count = max(random.randint(density[2][1], density[2][0]), current_count)
    
    if "Home" in location:
        agents = env.graph.nodes[location]['node'].agents

        # Update infection agent
        random_agents = set(random.choices(agents, k = agnt_count))
        for random_agent in random_agents:
            curr_state =  Disease_State.SUSCEPTIBLE.value
            next_state = Disease_State.Incubation.value
            Agents.update_VB_disease_state(random_agent, curr_state, next_state)
            Agents.update_patch_exposure_count(random_agent, env)

def visualize_patches_(env, day, folder, total=False):
    cmap = mcolors.LinearSegmentedColormap.from_list("grayRed", ["lightgray", "orange", "red"])
    norm = mcolors.Normalize(vmin=0, vmax=20)
    
    all_nodes = env.get_all_nodes()

    fig, ax = plt.subplots(figsize=(16, 9))
    
    for node_name in all_nodes: 
        node = env.graph.nodes[node_name]['node']
        if node_name == "KandyCity" or node_name == "Pallekele" or node_name == "Gampola":
            x, y = node.boundary.exterior.xy
            ax.plot(x, y, color='black')

        if "Zone" in node_name:
            # Plot the polygon boundary
            x, y = node.boundary.exterior.xy
            ax.plot(x, y, color='black')

            rows, columns = len(node.patch_grid), len(node.patch_grid[0])

            # Plot the grid cells
            for i in range(rows):
                for j in range(columns):
                    if node.patch_grid[i][j] is not None:
                        cell = node.patch_grid[i][j]._cell_box
                        x, y = cell.exterior.xy
                        total_vector_count = node.patch_grid[i][j]._total_count
                        infected_vector_count = node.patch_grid[i][j]._infected_count
                        
                        if total:
                            count = total_vector_count
                        else:
                            count = infected_vector_count
                        
                        # Randomly plot a marker for each agent
                        infected_agent_count = node.patch_grid[i][j]._infected_host_count
                        total_agent_count = node.patch_grid[i][j].host_count
                        
                        # Map the count to a color
                        color = cmap(norm(count))
                        
                        # Fill the cell with the color
                        ax.fill(x, y, color=color, alpha=0.5)
                        
                        
                        
                        # if infected_agent_count > 0:
                        #     for _ in range(infected_agent_count):
                        #         rand_x = random.uniform(min(x), max(x))
                        #         rand_y = random.uniform(min(y), max(y))
                        #         ax.plot(rand_x, rand_y, 'ro', markersize=2)  # Red dot for infectious agents
                           
                        # if total_agent_count - infected_agent_count > 0:
                        #     for _ in range(total_agent_count - infected_agent_count):
                        #         rand_x = random.uniform(min(x), max(x))
                        #         rand_y = random.uniform(min(y), max(y))
                        #         ax.plot(rand_x, rand_y, 'bo', markersize=2)  # Blue dot for healthy agents
                                

    # Add colorbar to show _infected_count mapping
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])  # Dummy array for the colorbar
    cbar = plt.colorbar(sm, ax=ax)
    cbar.set_label('Infected Mosquito Count')

    ax.set_aspect('equal')
    
    plt.savefig(f'{folder}/patch_{day}.png', dpi=300)
    # plt.show()
    plt.close()
    
    cmap = mcolors.LinearSegmentedColormap.from_list("grayRed", ["lightgray", "orange", "red"])
    norm = mcolors.Normalize(vmin=0, vmax=10)
    
    fig, ax = plt.subplots(figsize=(16, 9)) 

    for node_name in all_nodes: 
        node = env.graph.nodes[node_name]['node']
        if node_name in ["KandyCity", "Pallekele", "Gampola"]:
            x, y = node.boundary.exterior.xy
            ax.plot(x, y, color='black')

        if "Zone" in node_name:
            # Plot the polygon boundary
            x, y = node.boundary.exterior.xy
            ax.plot(x, y, color='black')

            rows, columns = len(node.patch_grid), len(node.patch_grid[0])

            # Plot the grid cells
            for i in range(rows):
                for j in range(columns):
                    if node.patch_grid[i][j] is not None:
                        patch = node.patch_grid[i][j]
                        x, y = patch._cell_box.exterior.xy
                        infected_agent_count = patch._infected_host_count
                        color = cmap(norm(infected_agent_count)) if infected_agent_count > 0 else 'lightgray'
                        ax.fill(x, y, color=color, alpha=0.5)

    # Add colorbar to show _infected_count mapping
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])  # Dummy array for the colorbar
    cbar = plt.colorbar(sm, ax=ax)
    cbar.set_label('Infected Host Count')
    
    ax.set_aspect('equal')
    plt.savefig(f'{folder}/agents_{day}.png', dpi=300)
    plt.close()
 
def visualize_patches(env, day, folder):
    # Create a colormap
    cmap = mcolors.LinearSegmentedColormap.from_list("GreenRed", ["green", "orange", "red"])
    norm = mcolors.Normalize(vmin=0, vmax=50)
    
    # Initialize the Folium map centered at a specific location
    map_center = [7.293, 80.638]  # Replace with the approximate latitude and longitude of the region
    map_folium = folium.Map(location=map_center, zoom_start=12, tiles="OpenStreetMap")
    
    all_nodes = env.get_all_nodes()
    
    for node_name in all_nodes:
        node = env.graph.nodes[node_name]['node']
        
        if "Zone" in node_name:
            # Convert node boundary to GeoJSON and add as a polygon
            geo_json = mapping(node.boundary)
            folium.GeoJson(
                geo_json,
                style_function=lambda feature: {
                    'fillColor': 'white',
                    'color': 'black',
                    'weight': 2,
                    'fillOpacity': 0.1,
                }
            ).add_to(map_folium)

            rows, columns = len(node.patch_grid), len(node.patch_grid[0])

            for i in range(rows):
                for j in range(columns):
                    if node.patch_grid[i][j] is not None:
                        cell = node.patch_grid[i][j]._cell_box
                        # count = node.patch_grid[i][j]._infected_count
                        
                        # Convert cell boundary to GeoJSON
                        # geo_json_cell = mapping(cell)
                        
                        # # Map the count to a color
                        # color = mcolors.to_hex(cmap(norm(count)))
                        
                        # # Add a polygon for the grid cell
                        # folium.GeoJson(
                        #     geo_json_cell,
                        #     style_function=lambda feature, color=color: {
                        #         'fillColor': color,
                        #         'color': 'black',
                        #         'weight': 1,
                        #         'fillOpacity': 0.5,
                        #     }
                        # ).add_to(map_folium)

                        # Add markers for agents
                        infected_agent_count = node.patch_grid[i][j]._infected_host_count
                        total_agent_count = node.patch_grid[i][j].host_count
                        
                        bounds = cell.bounds  # (minx, miny, maxx, maxy)
                        minx, miny, maxx, maxy = bounds
                        
                        if total_agent_count - infected_agent_count > 0:
                            for _ in range(total_agent_count - infected_agent_count):
                                rand_lat = random.uniform(miny, maxy)
                                rand_lon = random.uniform(minx, maxx)
                                folium.CircleMarker(
                                    location=[rand_lat, rand_lon],
                                    radius=2,
                                    color='blue',
                                    fill=True,
                                    fill_opacity=0.8
                                ).add_to(map_folium)
                        
                        if infected_agent_count > 0:
                            for _ in range(infected_agent_count):
                                rand_lat = random.uniform(miny, maxy)
                                rand_lon = random.uniform(minx, maxx)
                                folium.CircleMarker(
                                    location=[rand_lat, rand_lon],
                                    radius=2,
                                    color='red',
                                    fill=True,
                                    fill_opacity=0.8
                                ).add_to(map_folium)

                        
    
    # Save map as an HTML file
    map_folium.save(f"{folder}/map_day_{day}.html")
    return map_folium

def extract_patch_data(filename):
    # Read the Excel file into a pandas DataFrame
    df = pd.read_excel(filename, index_col=0)
    
    # Extract agent names from the index and times from the columns
    agent_patches = {}
    for agent_name in df.columns:
        agent_patches[agent_name] = list(df[agent_name].dropna())
    
    return agent_patches

def visualize_infected_traces(env, filename, folder, patches, total=False):
    
    agent_patches = extract_patch_data(filename)
    cmap = mcolors.LinearSegmentedColormap.from_list("GreenRed", ["white", "orange", "red"])
    norm = mcolors.Normalize(vmin=0, vmax=20)
    
    all_nodes = env.get_all_nodes()

    fig, ax = plt.subplots(figsize=(16, 9))
    
    for node_name in all_nodes: 
        node = env.graph.nodes[node_name]['node']
        if node_name == "KandyCity" or node_name == "Pallekele" or node_name == "Gampola":
            x, y = node.boundary.exterior.xy
            ax.plot(x, y, color='black')

        if "Zone" in node_name:
            # Plot the polygon boundary
            # x, y = node.boundary.exterior.xy
            # ax.plot(x, y, color='black')

            rows, columns = len(node.patch_grid), len(node.patch_grid[0])

            # Plot the grid cells
            for i in range(rows):
                for j in range(columns):
                    if node.patch_grid[i][j] is not None:
                        cell = node.patch_grid[i][j]._cell_box
                        x, y = cell.exterior.xy
                        total_vector_count = node.patch_grid[i][j]._total_count
                        infected_vector_count = node.patch_grid[i][j]._infected_count
                        
                        if total:
                            count = total_vector_count
                        else:
                            count = infected_vector_count
                        
                        # Map the count to a color
                        color = cmap(norm(count))
                        
                        # Fill the cell with the color
                        ax.fill(x, y, color=color, alpha=0.5)

    # For each agent, plot their patch data on the map
    for agent, patch_ids in agent_patches.items():
        for i in range(len(patch_ids)-1):
            if patch_ids[i] and patch_ids[i+1] and patch_ids[i] != patch_ids[i+1]:
                center1 = patches[int(patch_ids[i])-1]._cell_box.centroid
                center2 = patches[int(patch_ids[i+1])-1]._cell_box.centroid
                ax.plot([center1.x, center2.x], [center1.y, center2.y], color='black', linewidth=1)
                

    # Add colorbar to show _infected_count mapping
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])  # Dummy array for the colorbar
    cbar = plt.colorbar(sm, ax=ax)
    cbar.set_label('Infected Mosquito Count')

    ax.set_aspect('equal')
    
    plt.savefig(f'{folder}/traces.png', dpi=300)
    plt.close()
    
    
def plot_mosquito_density(patches, day, folder):
    sus, exp, inf = [], [], []
    for patch in patches:
        sus.append(patch._susceptible_count)
        exp.append(patch._exposed_count)
        inf.append(patch._infected_count)
    
    # print(set(mosquito_counts))
    # Plotting the mosquito numbers using a scatter plot
    plt.figure(figsize=(10, 8))
    plt.plot(sus, color='blue', label='Susceptible')
    plt.plot(exp, color='orange', label='Exposed')
    plt.plot(inf, color='red', label='Infected')
    plt.title('Mosquito Numbers in All Patches')
    plt.grid(True)
    plt.legend()
    plt.savefig(f'{folder}/day_{day}.png')
    plt.close()

def STEP_DISEASE_PROPAGATION(env, hospitalized_agents, time, DAY, freq=5):
    """
    1. Infect susceptible agents for each patch
    2. Update disease status for each agent
    :param env:
    :return:
    """
    # --------Run for every 5 minutes-----------
    if time % freq == 0:
        for zoneName in list(env.get_all_zones()):
            zone = env.graph.nodes(data=True)[zoneName]['node']
            patch_grid = zone.patch_grid
            for i in range(len(patch_grid)):
                for j in range(len(patch_grid[0])):
                    if patch_grid[i][j] is not None:
                        UpdatePatchAgents(patch_grid[i][j], env, zone.risk, DAY)
                        UpdatePatch(patch_grid[i][j], env, DAY)
                        
        UpdateHospitalizedAgents(env, hospitalized_agents)
    

def UpdatePatchAgents(patch, env, zoneRisk, DAY):
    # Update agents in the zone
    UpdateAgentDiseaseState(env, patch, patch.zone_agents, zoneRisk, DAY)
        
    # Update agents in the locations  
    for locationName in patch.locations:
        location = env.graph.nodes(data=True)[locationName]['node']
        UpdateAgentDiseaseState(env, patch, location.agents, location.risk, DAY)
 
def UpdateHospitalizedAgents(env, hospitalized_agents):
    UpdateAgentDiseaseState(env, patch=None, agents=hospitalized_agents, risk=None, DAY=None, hospitalized=True)
       

# NOTE: Updates the status and timers of each agent
def UpdateAgentDiseaseState(env, patch, agents, risk, DAY, hospitalized=False): 
    """
    --- Updates the status of each agent ---
    :param agents   : A list of total agents in the simulation
    :param env      : Environment object
    :return         : None
    """
    for agent in agents:
        curr_state = Agents.get_disease_state(agent)

        if curr_state == Disease_State.Dead.value or curr_state == Disease_State.Recovered.value:
            continue
        
        if curr_state == Disease_State.SUSCEPTIBLE.value and not hospitalized:
            host_exposure_rate = patch.get_host_exposure_rate(risk, DAY)
            host_exposure_probability = get_probability_from_rate(host_exposure_rate, 1)
            if random.uniform(0, 1) < host_exposure_probability:
                print(f"\nDay {DAY} - Agent {agent.get_agent_name()} is exposed, probability = {host_exposure_probability}")
                next_state = Disease_State.Incubation.value
                Agents.update_VB_disease_state(agent, curr_state, next_state, hospitalized)
                Agents.update_patch_exposure_count(agent, env)
            continue
                # Trans_time = getTransitionTimer(Disease_State.Infectious.value, Disease_State.Incubation.value, state_timer_dict)
                # Agents.set_state_timer(agent, Trans_time)
               
             
        state_timer = Agents.get_state_timer(agent)
        next_state = Agents.get_next_state(agent)   
       
        if state_timer <= 0:
            if next_state is not None:
                # Transition to the stored 'next_state'
                Agents.update_VB_disease_state(agent, curr_state, next_state, hospitalized)
                # Clear 'next_state' after transition
                agent.set_next_state(None)
            else:
                # Determine the next state using the VB-agent-state model
                next_state = stepVBMarkovModel(agent)

                # Calculate the transition time to the next state
                Trans_time = getTransitionTimer(next_state, curr_state, state_timer_dict)

                # Store the 'next_state' in the agent
                Agents.set_next_state(agent, next_state)
                # Set the state timer for the agent to the transition time
                Agents.set_state_timer(agent, Trans_time)
                
                # print(f'Agent {agent.get_agent_name()} is transitioning from {curr_state} to {next_state} | Transition time {Trans_time}')
                
        else:
            # Decrement the state timer by 5 minutes
            Agents.decrement_state_timer(agent, 5)

# Update the patch mosquito states
def UpdatePatch(patch, env, DAY):
    patch.update_sus_cnt(env, 0.9, DAY)
    patch.update_exp_cnt(env, 0.9, DAY)
    patch.update_inf_cnt(DAY)
