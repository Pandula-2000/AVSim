import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
import numpy as np
from Logger import *
from shapely.wkt import loads
from shapely.geometry import Point,Polygon, box
import geopy.distance
from shapely.plotting import plot_polygon
from scipy.spatial.distance import euclidean
from networkx.algorithms.approximation import traveling_salesman_problem
import random
from collections import deque
from DataLoader import Loader
import json
from pyproj import Geod
from disease_state_enum import Disease_State
import folium
from shapely.geometry import mapping
import fast_tsp
# np.random.seed(42)

# A node in the environment tree
class Node:
    """
    Represents a node in an environment tree, holding information about a specific zone.

    Attributes:
        zone_class: The class or type of the zone.
        zone_name: The name of the zone.
        node_id: The unique identifier for the node.
        max_agents: The maximum number of agents that can be in this zone simultaneously. Defaults to 0.

    Methods:
        __str__(): Returns a string representation of the node, including its ID, name, and agent capacity.
    """

    def __init__(self, zone_class,
                 zone_name,
                 node_id,
                 side_length=0,
                 max_agents=0,
                 boundary=None,
                 centroid=[0,0]):
        self.zone_class = zone_class
        self.zone_name = zone_name
        self.node_id = node_id

        self.agents = []
        self.people_count = 0
        self.max_agents = max_agents

        self.side_length = side_length
        self.boundary = boundary
        self.centroid = centroid

        # for vector borne diseses
        self.patch_grid = []
        self.patch = None
        self.patch_idx = (-1,-1)
        self.risk = random.uniform(0.2, 1) # potential exposure to mosquitoes

        # Note:To store the agents in each state. eg --> state: [agent1, agent2, ...]
        self.agent_dic_epidemics = {1:[], 2:[],3:[],4:[],5:[],6:[],7:[],8:[],9:[],10:[]}
        '''
         ----------------- STATES -----------------
         1: Susceptible,
         2: Incubation,
         3: Infectious,
         4: Mild, 
         5: Severe,
         6: Critical,
         7: Asymptotic,
         8: Recovered,
         9: Dead
        '''

    def get_disease_count(self, state, category=None):
        if state == Disease_State.PRESYMPTOMATIC and category:
            return self.state_counts[state].get(category)
        return self.state_counts.get(state)
    
    def update_disease_count(self, state, number, category=None):
        if state == Disease_State.PRESYMPTOMATIC:
            self.state_counts[state][category] += number    
        elif state in self.state_counts:
            self.state_counts[state] += number

    def create_patch_grid(self, cell_size):
        minx, miny, maxx, maxy = self.boundary.bounds

        # Calculate the height and width in meters using geopy
        vertical_distance = geopy.distance.distance((miny, minx), (maxy, minx)).meters
        horizontal_distance = geopy.distance.distance((miny, minx), (miny, maxx)).meters

        # Calculate number of rows and columns
        n_rows = int(np.ceil(vertical_distance/cell_size))
        n_cols = int(np.ceil(horizontal_distance/cell_size))
        self.patch_grid = [[None for _ in range(n_cols)] for _ in range(n_rows)] 


    def __str__(self):
        return f"{self.zone_name}{f'_{self.node_id}' if self.zone_class else ''} ({self.max_agents})"


# A bus node in the environment tree
class BusNode(Node):
    """
    Represents a bus node in an environment tree, holding additional information about a list of buses.

    Attributes:
        buses: A list of buses associated with this bus node.

    Methods:
        __str__(): Returns a string representation of the bus node, including its ID, name, agent capacity.
    """

    def __init__(self, zone_class, zone_name, node_id,
                side_length=0, max_agents=0, boundary=None, centroid=[0, 0]):
        super().__init__(zone_class, zone_name, node_id, side_length, max_agents, boundary, centroid)
        
        self.buses = []
        self.tuktuks = []
        self.agents = []


    def __str__(self):
        return super().__str__()
    

# Environment tree structure
class Environment:
    """
    Manages an environment represented as a tree structure, where each node represents a zone.

    Attributes:
        locations: A list of specific locations that are considered when creating child nodes.
        agent_count_list: Each tuple contains a location name and the maximum number of agents for that location.

    Methods:
        find_parents(parent): Identifies and returns parent nodes in the graph with a given name.
        create_child(child): Creates a child node based on the given zone name and returns it.
        add_node(parent, children): Adds nodes and edges to the graph based on a string describing children and their counts.
        update_max_agents(): Updates the maximum number of agents for each node based on its children nodes.
    """

    def __init__(self, locations, agent_count_list, predef_spawns):
        self.graph = nx.DiGraph()
        self.node_count = 0
        self.locations = locations
        self.locations_count = [0 for _ in locations]
        self.agent_count_list = agent_count_list
        self.predef_spawns = predef_spawns

    # Note: ---------------------------------- General Methods ---------------------------------------------------------
    def calc_side_length(self, polygon):
        geod = Geod(ellps="WGS84")
        geod_area = abs(geod.geometry_area_perimeter(polygon)[0])
        side_length = int(np.sqrt(geod_area))
        return side_length

    def find_parents(self, parent, boundary):
        # Add the root node
        if self.node_count == 0:
            is_location = parent in self.locations

            # update location count
            count = 0
            if is_location:
                index = np.where(self.locations[:,0] == parent)[0][0]
                count = self.locations_count[index]
                self.locations_count[index] += 1

            polygon = loads(boundary)
            centroid = polygon.centroid
            p_node = Node(None if is_location else parent, parent, count, boundary=polygon, centroid=centroid)
            p_name = f"{parent}{f'_{count}' if is_location else ''}"
            self.graph.add_node(p_name, node=p_node)
            self.node_count += 1
            return p_name

        # If not the root, all the other parents should exist in the graph
        for name, details in self.graph.nodes(data=True):
            if details['node'].zone_name == parent:
                polygon = loads(boundary)
                details['node'].boundary = polygon
                details['node'].side_length = self.calc_side_length(polygon)
                details['node'].centroid = polygon.centroid
                return name
        
        return None
    
    def create_child(self, child, parent):

        # Get the maximum agent numer for the zone
        max_agents = 0
        for array in self.agent_count_list:
            if array[0] == child:
                max_agents = array[1]
                break

        # There can be multiple user-defined zones
        if child in self.locations:
            index = np.where(self.locations[:,0] == child)[0][0]
            count = self.locations_count[index]
            self.locations_count[index] += 1

            pdetails = self.graph.nodes[parent]['node']
            polygon = pdetails.boundary
            c_name = f'{child}_{count}'
            self.node_count += 1
            if child == "BusStation":
                centroid = pdetails.centroid
                c_node = BusNode(None, child, count, max_agents=max_agents, side_length=self.locations[index][1], centroid=centroid)
            else:
                centroid = generate_random_point_in_polygon(polygon)
                c_node = Node(None, child, count, max_agents=max_agents, side_length=self.locations[index][1], centroid=centroid)
            return c_name, c_node

        # There can be only one standard zones
        for _, details in self.graph.nodes(data=True):
            if details['node'].zone_name == child:
                return None, None

        c_node = Node(child.split("_")[0], child, 0, max_agents=max_agents)
        c_name = f'{child}'
        self.node_count += 1
        return c_name, c_node

    # To add a new node from a children string
    def add_node(self, parent, children, boundary):
        
        p_name = self.find_parents(parent, boundary)

        if children == "None":
            parent_prefix = parent.split("_")[0]
            if parent_prefix in self.predef_spawns['l_class'].values:
                children = self.predef_spawns.loc[self.predef_spawns['l_class'] == parent_prefix, 'default_spawns'].iloc[0]

            if children == "None":
                return

        if p_name is None:
            Logger.log(f"A connection with no parent: {parent}", logging.WARNING)
            return

        for child in children.split('|'):
            child_string = child.split('#')
            if len(child_string) == 1:
                child_name = child_string[0]
                count = 1
            else:
                child_name = child_string[0]
                count = child_string[1]
            for _ in range(0, int(count)):
                c_name, c_node = self.create_child(child_name, p_name)
                if c_node is None:
                    Logger.log(f"Cannot create the child node: {child_name}", logging.WARNING)
                else:
                    self.graph.add_node(c_name, node=c_node)
                    self.graph.add_edge(p_name, c_name)

    def update_max_agents(self):
        for name in reversed(list(nx.topological_sort(self.graph))):
            node = self.graph.nodes[name]
            children_max_agents = [self.graph.nodes[child]['node'].max_agents for child in self.graph.successors(name)]
            # Update max_agent for the current node
            node_max_agent = max(sum(children_max_agents), node['node'].max_agents)
            node['node'].max_agents = node_max_agent

    def get_zone_class(self, zoneName):
        return self.graph.nodes(data=True)[zoneName]['node'].zone_class

    def get_people_count(self, zoneName):
        return self.graph.nodes(data=True)[zoneName]['node'].people_count

    def increment_people_count(self, zoneName, increment=1):
        self.graph.nodes(data=True)[zoneName]['node'].people_count += increment
        
    def get_max_agents(self, zoneName):
        return self.graph.nodes(data=True)[zoneName]['node'].max_agents

    def get_centroid(self, zoneName):
        return self.graph.nodes(data=True)[zoneName]['node'].centroid

    def get_boundary(self, zoneName):
        return self.graph.nodes(data=True)[zoneName]['node'].boundary

    def get_parent(self, exact_child_name):
        parents = list(self.graph.predecessors(exact_child_name))
        return parents[0], self.graph.nodes[parents[0]]['node']

    def get_children(self, parent):
        """
        Made for extracting Zones inside a subCity (For BusPlan.py)
        # IMPORTANT: We DO not need this to return BusStations/TukTukStations. Therefore, filtered out.
        :param parent   : The parent node
        :return         : List of nodes inside the parent. Without BusStations and TukTukStations.
        """
        children = list(self.graph.successors(parent))
        remove = []

        for child in children:
            if "BusStation" in child or "TukTukStation" in child:
                remove.append(child)

        for item in remove:
            children.remove(item)

        return children

    def get_children_unfiltered(self, parent):
        """
        To get children without filtering.
        :param parent   : The parent node
        :return         : List of nodes inside the parent. With BusStations and TukTukStations.
        """
        children = list(self.graph.successors(parent))
        return children

    def get_side_length(self, zoneName):
        return self.graph.nodes(data=True)[zoneName]['node'].side_length

    def get_agents(self, zoneName):
        """
        Get the agents in a given zone
        """
        return self.graph.nodes(data=True)[zoneName]['node'].agents

    def get_dic(self, zoneName):
        """
        Get the agent dic in a given zone
        """
        return self.graph.nodes(data=True)[zoneName]['node'].agent_dic_epidemics

    # Note: ----------------------------------- Pandemic related -------------------------------------------------------
    def get_agents_for_state(self, zoneName, state):
        """
        Get the agent list for a state in a given zone
        """
        return self.graph.nodes(data=True)[zoneName]['node'].agent_dic_epidemics

    def get_agent_count_for_state(self, zoneName, state):
        """
        Get the agent count for a state in a given zone
        """
        return len(self.graph.nodes(data=True)[zoneName]['node'].agent_dic_epidemics[state])

    def add_agent_to_state(self, zoneName, state, agent):
        """
        Add an agent to a state in a given zone
        """
        self.graph.nodes(data=True)[zoneName]['node'].agent_dic_epidemics[state].append(agent)

    def remove_agent_from_state(self, zoneName, state, agent):
        """
        Remove an agent from a state in a given zone
        """
        self.graph.nodes(data=True)[zoneName]['node'].agent_dic_epidemics[state].remove(agent)

    # Note: ---------------------------- Manage agents in Environment --------------------------------------------------

    def add_agent(self, zoneName,  agent):
        self.graph.nodes(data=True)[zoneName]['node'].agents.append(agent)
        
    def add_agent_VB(self, nodeName, agent):
        node = self.graph.nodes(data=True)[nodeName]['node']
        node.agents.append(agent)
        if "Zone" in nodeName:
            non_none_indices = [(i, j) for i in range(len(node.patch_grid)) for j in range(len(node.patch_grid[i])) if node.patch_grid[i][j] is not None]
            row, col = random.choice(non_none_indices)
            patch = node.patch_grid[row][col]
        else:
            patch = node.patch
        patch.add_agent(agent, nodeName)
        agent.patch = patch

    def remove_agent(self, zoneName,  agent):
        self.graph.nodes(data=True)[zoneName]['node'].agents.remove(agent)
        
    def remove_agent_VB(self, nodeName, agent):
        node = self.graph.nodes(data=True)[nodeName]['node']
        node.agents.remove(agent)
        patch = agent.patch
        patch.remove_agent(agent, nodeName)

    # Note: -------------------------------- Transport related ---------------------------------------------------------
    def get_bus_node(self, zoneName):
        pnode = zoneName
        if zoneName.split("_")[0] in self.locations:
            pnode = list(self.graph.predecessors(zoneName))
            pnode = pnode[0]

        for node in self.graph.successors(pnode):
            if node.split("_")[0] == "BusStation":
                return self.graph.nodes(data=True)[node]['node'].buses
        return None

    def get_buses(self, zoneName):
        bus_node = self.get_bus_node(zoneName)
        return bus_node

    def get_tuktuk_node(self, zoneName):
        pnode = zoneName
        if zoneName.split("_")[0] in self.locations:
            pnode = list(self.graph.predecessors(zoneName))
            pnode = pnode[0]

        for node in self.graph.successors(pnode):
            if node.split("_")[0] == "BusStation":
                return self.graph.nodes(data=True)[node]['node'].tuktuks
        return None

    def get_tuktuk(self, zoneName):
        tuktuk_node = self.get_tuktuk_node(zoneName)
        return tuktuk_node

    def add_bus(self, zoneName, bus):
        bus_node = self.get_bus_node(zoneName)
        bus_node.append(bus)

    def remove_bus(self, zoneName, bus):
        bus_node = self.get_bus_node(zoneName)
        bus_node.remove(bus)
        
    def add_tuktuk(self, zoneName, tuktuk):
        tuktuk_node = self.get_tuktuk_node(zoneName)
        tuktuk_node.append(tuktuk)

    def remove_tuktuk(self, zoneName, tuktuk):
        tuktuk_node = self.get_tuktuk_node(zoneName)
        tuktuk_node.remove(tuktuk)

    def reset_tuktuk(self):
        for Location in list(self.get_all_nodes()):
            tuk_tuks_loc = self.get_tuktuk(Location)
            if tuk_tuks_loc is not None:
                for tuk_tuk_loc in tuk_tuks_loc:
                    self.remove_tuktuk(Location, tuk_tuk_loc)

    def get_all_nodes(self):
        all_data = list(self.graph.nodes)
        node_objects = []
        for name in all_data:
            if "BusStation" in name or "TukTukStation" in name:
                continue
            else:
                node_objects.append(name)

        return node_objects
    
    def get_all_zones(self):
        all_nodes = self.get_all_nodes()
        zones = [node for node in all_nodes if "Zone" in node]
        return zones
    
    def get_all_successors(self, node_name):
        result = []

        def get_successors_recursive(node):
            if "BusStation" not in node and "TukTukStation" not in node:
                result.append(node)
                for successor in self.graph.neighbors(node):
                    get_successors_recursive(successor)
        
        for successor in self.graph.neighbors(node_name):
            get_successors_recursive(successor)

        return result

    # Note: ----------------------- Route Planning related -------------------------------------------------------------
    def calculate_travel_time(self, loc1, loc2, velocity=10):
        """
        Function to calculate travel time between two Nodes
        :param  loc1    : Zone 1
        :param  loc2    : Zone 2
        :param  velocity: Velocity of the object moving between two nodes
        :return         : Time taken for to travel
        """
        point1, point2 = self.graph.nodes(data=True)[loc1]['node'].centroid, self.graph.nodes(data=True)[loc2]['node'].centroid
        distance = (geopy.distance.geodesic((point1.x, point1.y), (point2.x, point2.y)).km)
        return round((distance / velocity)*60)
        #return distance

    def is_same_zone(self, name1, name2):
        zone1_prefix = name1.split("_")[0]
        zone2_prefix = name2.split("_")[0]
        
        is_zone1 = zone1_prefix not in self.locations
        is_zone2 = zone2_prefix not in self.locations
        
        if is_zone1 and is_zone2:
            return name1 == name2
            
        successors_check = (name2 in self.graph.successors(name1)) or (name1 in self.graph.successors(name2))
        predecessors_check = next(self.graph.predecessors(name1), None) == next(self.graph.predecessors(name2), None)

        return successors_check or predecessors_check

    def get_zones(self, zoneName):
        """
        Function to get all the locations of a given location type.
        If zoneName = Home, then this returns ["Home_1", "Home_2", ...]
        # NOTE: You can get node object using env.graph.nodes["Home_1"]['node']
        :param zoneName : Name of the zone.
        :return         : All the locations of the given zone type.
        """

        return [name for name in self.graph.nodes() if zoneName == name.split("_")[0]]

    def get_exact_target_node(self, start_node, target_node, agent):
        if agent._work_location and agent._work_location.split("_")[0] == target_node:
            return agent._work_location
            
        if agent._init_location and agent._init_location.split("_")[0] == target_node:
            return agent._init_location

        visited = set()
        queue = deque([start_node])

        while queue:
            node = queue.popleft()
            if node not in visited:
                visited.add(node)
                # Check if the node matches the target pattern
                if target_node == node.split("_")[0]:
                    return node
                # Add neighbors to the queue
                neighbors = set(self.graph.neighbors(node)) | set(self.graph.predecessors(node))
                for neighbor in neighbors:
                    if neighbor not in visited:
                        queue.append(neighbor)
        
        # If target node is missing
        # Return None for the path and set agent status to INACTIVE
        Logger.log(f'Node {target_node} does not exist')
        return None

    def find_intermediate_nodes(self, start_city, end_city):
        
        start_child_zones = list(self.get_children(start_city))
        end_child_zones = list(self.get_children(end_city))

        # FIXME: Temporary solution for path changes
        if sorted([start_city, end_city])[0] == start_city:
            all_zones = start_child_zones + end_child_zones
        else:
            all_zones = end_child_zones + start_child_zones

        all_centroids = [self.graph.nodes[node]['node'].centroid for node in all_zones]

        # Calculate distance matrixes
        num_zones = len(all_zones)
        distance_matrix = np.zeros((num_zones, num_zones))
        
        for i in range(num_zones):
            for j in range(i + 1, num_zones):
                distance = euclidean([all_centroids[i].x, all_centroids[i].y], [all_centroids[j].x, all_centroids[j].y])
                distance_matrix[i][j] = distance
                distance_matrix[j][i] = distance

        # Create a complete graph
        G = nx.Graph()

        # Add nodes
        for i, city in enumerate(all_zones):
            G.add_node(i, pos=city)

        # Add edges with distances as weights
        for i in range(len(all_zones)):
            for j in range(i + 1, len(all_zones)):
                G.add_edge(i, j, weight=distance_matrix[i][j])

        # Solve the TSP using NetworkX
        tsp_path = traveling_salesman_problem(G, weight='weight', cycle=False)

        # Retrieve the coordinates of the optimal route
        optimal_route = [all_zones[i] for i in tsp_path]

        if optimal_route[0] in end_child_zones:
            optimal_route.reverse()
        return optimal_route

    def get_shortest_path(self, start_node, target_node, agent):
        find_exact = False

        # -------------------------------------------------------
        if start_node.split("_")[0] == target_node:
            return [start_node]
        # -------------------------------------------------------

        if agent._work_location and agent._work_location.split("_")[0] == target_node:
            target_node = agent._work_location
            find_exact = True

        if agent._init_location and agent._init_location.split("_")[0] == target_node:
            target_node = agent._init_location
            find_exact = True

        # If target node is missing
        # Return None for the path and set agent status to INACTIVE
        if find_exact:
            contains_node = target_node in self.graph.nodes()
        else:
            contains_node = any(target_node in node.split("_") for node in self.graph.nodes())

        if not contains_node:
            Logger.log(f'Node {target_node} does not exist')
            return None

        # If the start node is absent but the target node is present
        # Return [] for the path and set agent status to ACTIVE
        if not self.graph.has_node(start_node):
            Logger.log(f'Node {start_node} does not exist')
            return []

        visited = set()
        # Queue for BFS traversal with parent information
        queue = [(start_node, None)]

        parent_map = {}

        while queue:
            node, parent = queue.pop(0)

            if node not in visited:
                visited.add(node)

                # Store parent information
                parent_map[node] = parent

                if (find_exact and node == target_node) or (not find_exact and node.split("_")[0] == target_node):
                    # Reconstruct the path from source to target
                    path = [node]
                    while parent_map[path[-1]] is not None:
                        path.append(parent_map[path[-1]])
                    # ---------- Filter Upper nodes ----------------
                    path = [p for p in path if "_" in p]
                    # ----------------------------------------------
                    return path[::-1][1:]  # Reverse the path to get source to target

                # Get neighbors of the current node ignoring edge directions
                neighbors = set(self.graph.neighbors(node)) | set(self.graph.predecessors(node))

                # Enqueue neighbors that haven't been visited
                for neighbor in neighbors:
                    if neighbor not in visited:
                        queue.append((neighbor, node))

        # If target node is not reachable from source
        return None

    # NOTE: -------------------Vector Borne Related-------------------------------------------------
    def get_patch(self, zoneName):
        node = self.graph.nodes(data=True)[zoneName]['node']
        return node.patch

    # Note: --------------------------------------------- Other --------------------------------------------------------
    def is_in_polygon(polygon, x,y):
        point = Point(x, y)
        return polygon.contains(point)

def generate_random_point_in_polygon(polygon):
    min_x, min_y, max_x, max_y = polygon.bounds
    while True:
        random_point = Point(random.uniform(min_x, max_x), random.uniform(min_y, max_y))
        if polygon.contains(random_point):
            return random_point    

def LaunchEnvironment():
    # df = Loader.getSim('LocationEnv.xlsx')
    df = Loader.getSim2("Location Environment")
    locations = np.array(df.iloc[:, [0, 1]].values)

    # df = Loader.getSim('location_classes.csv')
    df = Loader.getSim2("Location Classes")
    pre_def_spawns = df.fillna("None")

    # Define maximum agent count for different locations
    agent_count_list = [["Home", 4]]

    # Create environment
    env = Environment(locations, agent_count_list, pre_def_spawns)
    # df = Loader.getSim('NodeEnv.xlsx', header=None)
    df = Loader.getSim2("Node Environment", header=None)
    df = df.fillna("None")
    for _, row in df.iterrows():
        env.add_node(row[0], row[1], row[2])

    # Update max agent numbers
    env.update_max_agents()
    return env

def node_to_json(G, node, level):
    polygon = str(G.nodes[node]['node'].boundary)
    centroid = str(G.nodes[node]['node'].centroid)
    node_dict = {"name": node, "level": level, "polygon": polygon, "centroid": centroid}

    children = list(G.successors(node))
    if children:
        node_dict["children"] = [node_to_json(G, child, level+1) for child in children]
    return node_dict

# Plot regions on map
def plot_on_map(env, folder, filename="map"):
    # Initialize the map
    map_center = [7.293, 80.638]  # Replace with an approximate center point of the region
    map_folium = folium.Map(location=map_center, zoom_start=12, tiles="OpenStreetMap")

    fig, ax = plt.subplots(figsize=(16, 9))
    
    for name, details in env.graph.nodes(data=True):
        if details['node'].boundary and "District" not in name:
            # Get boundary and centroid
            boundary_coords = details['node'].boundary
            centroid = details['node'].centroid

            # Convert boundary to GeoJSON
            geo_json = mapping(boundary_coords)

            # Generate a random color for the boundary
            random_color = "#{:06x}".format(random.randint(0, 0xFFFFFF))

            # Add the boundary polygon to the map
            folium.GeoJson(
                geo_json,
                style_function=lambda feature, color=random_color: {
                    'fillColor': color,
                    'color': color,
                    'weight': 2,
                    'fillOpacity': 0.4,
                }
            ).add_to(map_folium)
            
            plot_polygon(boundary_coords, ax=ax, add_points=False, color= random_color)

            # # Add a marker for the centroid
            # folium.Marker(
            #     location=[centroid.y, centroid.x],  # Centroid coordinates
            #     popup=name,  # Add the name of the node
            #     icon=folium.Icon(color="blue", icon="info-sign")
            # ).add_to(map_folium)

    start = "KandySub_1"
    end = "KandySub_3"

    neighboring_nodes = env.find_intermediate_nodes(start, end)

    centroids = []
    for village in neighboring_nodes:
        centroid = Point(env.graph.nodes[village]['node'].centroid)
        centroids.append(centroid)

    for i in range(len(centroids)-1):
        ax.plot([centroids[i].x, centroids[i+1].x], [centroids[i].y, centroids[i+1].y], 'k--')
        plt.plot(centroids[i].x, centroids[i].y, 'ko')
    plt.plot(centroids[len(centroids)-1].x, centroids[len(centroids)-1].y, 'ko')
    
    start = "PallekeleSub_1"
    end = "PallekeleSub_2"

    neighboring_nodes = env.find_intermediate_nodes(start, end)

    centroids = []
    for village in neighboring_nodes:
        centroid = Point(env.graph.nodes[village]['node'].centroid)
        centroids.append(centroid)

    for i in range(len(centroids)-1):
        ax.plot([centroids[i].x, centroids[i+1].x], [centroids[i].y, centroids[i+1].y], 'k--')
        plt.plot(centroids[i].x, centroids[i].y, 'ko')
    plt.plot(centroids[len(centroids)-1].x, centroids[len(centroids)-1].y, 'ko')
    
    start = "GampolaSub_3"
    end = "GampolaSub_4"

    neighboring_nodes = env.find_intermediate_nodes(start, end)

    centroids = []
    for village in neighboring_nodes:
        centroid = Point(env.graph.nodes[village]['node'].centroid)
        centroids.append(centroid)

    for i in range(len(centroids)-1):
        ax.plot([centroids[i].x, centroids[i+1].x], [centroids[i].y, centroids[i+1].y], 'k--')
        plt.plot(centroids[i].x, centroids[i].y, 'ko')
    plt.plot(centroids[len(centroids)-1].x, centroids[len(centroids)-1].y, 'ko')
    
    start = "KandySub_5"
    end = "KandySub_6"

    neighboring_nodes = env.find_intermediate_nodes(start, end)

    centroids = []
    for village in neighboring_nodes:
        centroid = Point(env.graph.nodes[village]['node'].centroid)
        centroids.append(centroid)

    for i in range(len(centroids)-1):
        ax.plot([centroids[i].x, centroids[i+1].x], [centroids[i].y, centroids[i+1].y], 'k--')
        plt.plot(centroids[i].x, centroids[i].y, 'ko')
    plt.plot(centroids[len(centroids)-1].x, centroids[len(centroids)-1].y, 'ko')
    
    # Save the map as an HTML file
    map_folium.save(f"{folder}/{filename}.html")
    ax.set_aspect('equal')
    plt.savefig(f'{folder}/{filename}.png', dpi=300)
    return map_folium

if __name__ == "__main__":
    env = LaunchEnvironment()
    # ----------------------- To plot the tree -------------------
    # G = env.graph
    # nx.draw(G, with_labels=True, node_color='skyblue', node_size=2000, font_size=6, font_color='black', font_weight='bold')
    # plt.show()

    # ---------------------------get_exact_target_node------------------------------
    # from types import SimpleNamespace
    # agent1 = SimpleNamespace(_init_location="Home_14", _work_location="Bank_0")
    # shortest_path = env.get_exact_target_node("Home_15", "Home", agent1)
    # print(shortest_path)
 
    # ---------------------------To plot the tree (you may need conda environment)------------------------------
    # plt.figure(1)
    # G = env.graph
    # pos = nx.nx_agraph.pygraphviz_layout(G, prog='dot')
    # node_positions = {node: pos[node] for node in G.nodes()}
    # labels = {node: str(G.nodes[node]['node']) for node in G.nodes()}
    # nx.draw(G, node_positions, with_labels=False, node_color='lightblue', font_weight='bold', node_size=100, arrows=True)
    # for node, (x, y) in node_positions.items():
    #     plt.text(x, y, labels[node], fontsize=7, ha='center', va='center', rotation=45)
    # plt.show()

    # --------------------------- To plot the regions -----------------------------------    
    # plot_on_map(env, "../Results")
    # fig = plt.figure(2)
    # ax = fig.add_subplot(111)

    # for name, details in env.graph.nodes(data=True):
    #     if details['node'].boundary:
    #         boundary_coords = details['node'].boundary
    #         centroid = details['node'].centroid

    #         random_color = "#{:06x}".format(random.randint(0, 0xFFFFFF))
    #         plot_polygon(boundary_coords, ax=ax, add_points=False, color= random_color, label=name)
    #         plt.plot(centroid.x, centroid.y, 'ko')
        
    #
    # # # busses
    # env.add_bus('ResidentialZone_1', "bus1")
    # env.add_bus('ResidentialZone_1', "bus2")
    #
    #
    # # bus_nodes= env.get_bus_node('ResidentialZone_1')
    # env.remove_bus('ResidentialZone_1', "bus1")
    # env.remove_bus('ResidentialZone_1', "bus1")
    # print(env.get_buses('ResidentialZone_1'))
    # print(env.get_buses('ResidentialZone_2'))

    # print(env.is_same_zone("ResidentialZone_1", "BusStation_0"))        # zone and location (same zone)
    # print(env.is_same_zone("ResidentialZone_1", "ResidentialZone_2"))   # zone and zone (different)
    # print(env.is_same_zone("ResidentialZone_2", "BusStation_0"))        # zone and location (different)
    # print(env.is_same_zone("BusStation_0", "BusStation_1"))             # location and location (different)
    # print(env.is_same_zone("ResidentialZone_1", "Home_0"))                   # location and location (same zone)


    # print(env.get_zone_class('MedicalZone_1'))
    # print(env.get_zone_class('Home_1'))



    # z = 'Home_0'
    # print(f"Parent of {z} is {env.get_parent('Home_0')}")
    # print(env.get_buses('Gampola'))
    #
    # print(env.get_zone_class(env.get_parent('Gampola')[0]))
    #
    # print(env.calculate_travel_time('KandyCity','Gampola'))
    #
    # print(env.is_same_zone("Home_29", "School_3"))

    # # Get selected intermediate nodes
    # start = "Gampola"
    # end = "KandyCity"

    # start_point = Point(env.graph.nodes[start]['node'].centroid)
    # end_point = Point(env.graph.nodes[end]['node'].centroid)

    # neighboring_nodes = env.find_intermediate_nodes(start, end)

    # centroids = []
    # for village in neighboring_nodes:
    #     centroid = Point(env.graph.nodes[village]['node'].centroid)
    #     centroids.append(centroid)

    # for i in range(len(centroids)-1):
    #     ax.plot([centroids[i].x, centroids[i+1].x], [centroids[i].y, centroids[i+1].y], 'k--')
    #     plt.plot(centroids[i].x, centroids[i].y, 'ko')
    # plt.plot(centroids[len(centroids)-1].x, centroids[len(centroids)-1].y, 'ko')
    
    # plt.legend(loc='upper left', bbox_to_anchor=(1.02, 1), borderaxespad=0)
    # plt.tight_layout()
    # plt.show()
    # tree_json = node_to_json(env.graph, "Kandy District", 0)

    # # Write the JSON to a file
    # with open("binary_tree.json", "w") as f:
    #     json.dump(tree_json, f, indent=2)


    # print(env.get_all_nodes())
    # print(env.find_intermediate_nodes("KandyCity","Gampola"))
    
    # start_child_zones = list(env.graph.successors("KandySub_1"))
    # print(start_child_zones)

