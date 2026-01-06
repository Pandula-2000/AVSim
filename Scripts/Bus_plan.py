import csv
import geopy.distance
from Agents2 import *
from shapely.geometry import Point, Polygon, box
from Transport.TransportFunctions import *
from itertools import permutations
from tqdm import tqdm

# --- Node details ---
node_locations = Loader.getSim('NodeEnv.xlsx', header=None)

# Remove Districts. People will not visit these places(Bimodality).
# node_locations = node_locations[~node_locations.iloc[:, 0].str.contains('District', na=False)]
# print(node_locations)

# ------------------Bus Parameters----------------#
wait_time_firstZone = 15
wait_time_intermediateZones = 5
wait_time_last_zone= 15


class Bus:
    """
    One bus turn (from one city to another city) plan

    Attributes:
        init_time   : Transport instance starting time.
        mode        : Type of transport (city-city or city)
        start_city  : Starting zone of any public transport instance.
        end_city    : Destination zone of any public transport instance.
        velocity    : Velocity of the instance.
        sched_time  : Scheduled time between two buses (Default 20 minutes)
    Methods:
        transport_plan: Return a dictinary containing {'Zone': (Start_time, End_time)}
    """

    def __init__(self,
                 init_time,
                 mode,
                 start_city,
                 end_city,
                 environment_object,
                 velocity: int,
                 sched_time=20):

            self.init_time = init_time
            self.end_time = None
            self.start_city = start_city
            self.end_city = end_city

            # self.environment = environment_object # FIXME: Not used (Too much space !!!)

            self.velocity = velocity
            self.waiting_time = sched_time
            self.in_motion = False
            self.current_location = None
            self.previous_location = None
            self.bus_tt = []
            self.next_locations = []
            self.agents = []  # A list of agent objects inside the transport vehicle.

            self.mode = mode
            if self.mode == "city-city":
                # self.start_point = Point(environment_object.graph.nodes[self.start_city]['node'].centroid)
                # self.end_point = Point(environment_object.graph.nodes[self.end_city]['node'].centroid)

                self.start_point = Point(environment_object.get_centroid(self.start_city))
                self.end_point = Point(environment_object.get_centroid(self.end_city))

                self.intermediate_nodes = environment_object.find_intermediate_nodes(start_city, end_city)
                # print(self.intermediate_nodes)
            elif self.mode == "city":
                self.city = start_city
                self.intermediate_nodes = environment_object.get_children(self.city)
            else:
                raise ValueError("Invalid mode. Must be 'city-city' or 'city'")

    def __str__(self):
        return f"Bus from {self.start_city} to {self.end_city} | Mode: {self.mode} | Duration: ({self.init_time}, {self.end_time}) | Motion: {self.in_motion} | CL: {self.current_location} | PL: {self.previous_location} | NLs: {self.next_locations}"

    def add_agent(self, agent):
        self.agents.append(agent)

    def remove_agent(self, agent):
        self.agents.remove(agent)

    def get_agents(self):
        return self.agents

    def set_current_location(self, loc):
        self.current_location = loc

    def get_current_location(self):
        return self.current_location

    def get_previous_location(self):
        return self.previous_location

    def get_next_locations(self):
        return self.next_locations

    def get_in_motion(self):
        return self.in_motion

    def updateVehicle(self, time):
        """
        Update the vehicle location based on the current time.
        1. Check if the bus is in motion.
        2. Check if the bus is at a bus station.
        :param time : Time of the simulation.
        :return     : None
        """
        # 1.  -------------- Check if bus is in motion ---------------------
        if self.init_time <= time <= self.end_time:
            self.in_motion = True
            self.current_location = None   # Then Transporting between Nodes.
            # 2. ----------- Check if Bus is at a bus station --------------------
            n = len(self.bus_tt[0])
            for i in range(n):
                if self.bus_tt[1][i][0] <= time <= self.bus_tt[1][i][1]:
                    self.current_location = self.bus_tt[0][i]
                    self.previous_location = self.bus_tt[0][i]

                    locations = self.bus_tt[0]
                    start_index = locations.index(self.get_current_location())
                    if i == n - 1:
                        self.next_locations = []
                    else:
                     self.next_locations = locations[start_index + 1:]

            # for key, value in self.bus_dict.items():
            #     if value[0] <= time <= value[1]:    # Bus is at a bus station.
            #         self.current_location = key
            #         self.previous_location = key

            #         keys = list(self.bus_dict.keys())
            #         start_index = keys.index(self.getcurrent_location())
            #         self.next_locations = keys[start_index + 1:]

            # if self.current_location != None:
            #     self.previous_location = prev_loc

            # self.current_location = [key if value[0] <= time <= value[1] else None for key, value in self.bus_dict.items()][0]
            # ----------- update the next Fremove_ag
            # locations --------------------

        else:
            self.in_motion = False
            self.previous_location = None
            self.current_location = None
            self.next_locations = []

    def _generate_transport_plan(self,
                                 mode,
                                 environment_object,
                                 wait_time_firstZone=2,
                                 wait_time_intermediateZones=1,
                                 wait_time_last_zone=2):
        bus_time = []
        bus_nodes = []
        if mode == "city-city":
            bus_nodes.append(self.start_city)
            bus_nodes.extend((self.intermediate_nodes))
            bus_nodes.append(self.end_city)
            self.bus_tt.append(bus_nodes)
            # -----------------------------------------------------------------------------------
            time_interval = wait_time_intermediateZones  # Time wait in intermediate zones
            nodes = extract_nodes(node_locations, environment_object)
            # print(nodes)
            current_node = self.start_city
            next_nodes = self.intermediate_nodes + [self.end_city]
            # -----------------------------------------------------------------------------------
            """
            After comes to the start node on a certain day it start by waiting at
            15 min in the start node
            """
            bus_dep_time = 0  # Time between each travel from one destination (initially zero)
            start_time = self.init_time
            end_time = self.init_time + wait_time_firstZone
            # self.bus_dict[current_node] = (int(start_time), int(end_time))
            bus_time.append((int(start_time), int(end_time)))
            distance = calculate_distance(nodes[current_node], nodes[self.intermediate_nodes[0]])
            travel_time = calculate_travel_time(distance, self.velocity)
            # Move to next node
            current_node = self.intermediate_nodes[0]
            total_time = travel_time  # Traveling Time

            val = 1
            # From A -----> B
            for next_node in self.intermediate_nodes + [self.end_city]:
                if current_node == next_node:
                    continue
                # next_nodes = self.intermediate_nodes[val:] + [self.end_city]

                distance = calculate_distance(nodes[current_node], nodes[next_node])
                travel_time = round((calculate_travel_time(distance, self.velocity)) * 60)

                # Move to the next node
                total_time += travel_time

                # Wait for 5 minutes at intermediate nodes
                if next_node in self.intermediate_nodes + [self.end_city]:
                    total_time += time_interval

                start_time = travel_time + end_time
                end_time = start_time + time_interval

                # self.bus_dict[current_node] = (int(start_time), int(end_time))
                bus_time.append((int(start_time), int(end_time)))

                current_node = next_node
                val += 1

            distance = calculate_distance(nodes[self.intermediate_nodes[-1]], nodes[self.end_city])
            travel_time = round((calculate_travel_time(distance, self.velocity)) * 60)

            end_time = end_time + travel_time
            # self.bus_dict[current_node] = int(end_time)
            # Note: Added a wait time (20 minutes by default) for the last Zone. If not, updateVehicle() will give an error.
            # self.bus_dict[current_node] = (int(end_time), int(end_time + wait_time_last_zone))
            bus_time.append((int(end_time), int(end_time + wait_time_last_zone)))
            total_time += travel_time
            # self.end_time = self.bus_dict[self.end_city]
            # self.end_time = self.bus_dict[self.end_city][1]
            self.end_time = bus_time[-1][1]

            # Important: Set the current location immediately after initializing the bus ???
            # FIXME: Wont matter.. This will get updated again at updateVehicle()
            self.current_location = self.bus_tt[0][0]
            self.previous_location = self.current_location

            self.bus_tt.extend([bus_time])
            # print(self.bus_tt)
            return 0

        elif mode == "city":
            # -----------------------------------------------------------------------------------
            bus_nodes.append(self.start_city)
            bus_nodes.extend((self.intermediate_nodes))
            bus_nodes.append(self.start_city)
            # print(bus_nodes)
            self.bus_tt.append(bus_nodes)
            # -----------------------------------------------------------------------------------
            # self.bus_dict = {}
            time_interval = wait_time_intermediateZones  # Time wait in intermediate zones
            nodes = extract_nodes(node_locations, environment_object)
            current_node = self.start_city
            next_nodes = self.intermediate_nodes + [self.start_city]
            start_loc_lis = []
            # -----------------------------------------------------------------------------------

            """
            After comes to the start node on a certain day it start by waiting at
            15 min in the start node
            """
            bus_dep_time = 0  # Time between each travel from one destination (initially zero)
            start_time = self.init_time
            end_time = self.init_time + wait_time_firstZone
            # start_loc_lis.extend((int(start_time), int(end_time)))
            # self.bus_dict[current_node].append((int(start_time), int(end_time)))
            bus_time.append((int(start_time), int(end_time)))
            # self.bus_dict[current_node] = start_loc_lis.extend((int(start_time), int(end_time)))
            distance = calculate_distance(nodes[current_node], nodes[self.intermediate_nodes[0]])
            travel_time = calculate_travel_time(distance, self.velocity)
            # Move to next node
            current_node = self.intermediate_nodes[0]
            total_time = travel_time  # Traveling Time

            # val = 1
            # From A -----> B
            for next_node in self.intermediate_nodes + [self.start_city]:
                if current_node == next_node:
                    continue

                # next_nodes = self.intermediate_nodes[val:] + [self.end_city]

                distance = calculate_distance(nodes[current_node], nodes[next_node])
                travel_time = round((calculate_travel_time(distance, self.velocity)) * 60)

                # Move to the next node
                total_time += travel_time

                # Wait for 5 minutes at intermediate nodes
                if next_node in self.intermediate_nodes + [self.end_city]:
                    total_time += time_interval

                start_time = travel_time + end_time
                end_time = start_time + time_interval

                # self.bus_dict[current_node] = (int(start_time), int(end_time))
                bus_time.append((int(start_time), int(end_time)))

                current_node = next_node
                # val += 1

            distance = calculate_distance(nodes[self.intermediate_nodes[-1]], nodes[self.start_city])
            travel_time = round((calculate_travel_time(distance, self.velocity)) * 60)

            end_time = end_time + travel_time
            # self.bus_dict[current_node] = int(end_time)
            # Note: Added a wait time (20 minutes by default) for the last Zone. If not, updateVehicle() will give an error.
            # self.bus_dict[current_node] = (int(end_time), int(end_time + wait_time_last_zone))
            # start_loc_lis.extend((int(end_time), int(end_time + wait_time_last_zone)))
            # self.bus_dict[current_node].append((int(end_time), int(end_time + wait_time_last_zone)))
            bus_time.append((int(end_time), int(end_time + wait_time_last_zone)))
            # self.bus_dict[current_node] = start_loc_lis
            total_time += travel_time
            # self.end_time = self.bus_dict[self.end_city]
            # self.end_time = self.bus_dict[self.start_city][0][1]
            self.end_time = bus_time[-1][1]

            # Important: Set the current location immediately after initializing the bus
            # FIXME: Wont matter.. This will get updated again at updateVehicle()
            # self.current_location = list(self.bus_dict.keys())[0]
            self.current_location = self.bus_tt[0][0]
            self.previous_location = self.current_location

            self.bus_tt.extend([bus_time])
            # print(self.bus_dict)
            return 0


def availableBus(bus_list: list, agent: Agents):
    """
    Check if the agent's next zone is in the bus's next locations.
    :param bus_list : List of bus objects at the bus stop.
    :param agent    : Agent object.
    :return         : Bus object if the agent's next zone is in the bus's next locations. Else, None.
    """
    for bus in bus_list:
        if (agent.get_next_location() in bus.get_next_locations()) and (bus.get_current_location() is not None):
            return bus
    return None


def generate_buses_perRoute(mode: str,
                            start_time: int,
                            end_time: int,
                            start_city: str,
                            end_city,
                            environment_object,
                            velocity: int = 20,
                            interval: int = 10):
    list_of_bus_objects = []
    departureTime = start_time
    while departureTime < end_time:
        bus = Bus(departureTime, mode, start_city, end_city, environment_object, velocity)
        bus._generate_transport_plan(mode, environment_object)
        list_of_bus_objects.append(bus)
        departureTime += interval
    return list_of_bus_objects


def INITIALIZE_BUSES(env_object, start_time=300, end_time=1260):
    """
    Initialize all buses in the environment
    1. City to City buses - Goes between cities
    2. City buses - Goes inside subcCities
    # FIXME: currently buses do not make more than one turn. Fix this.
    :param env_object   : Environment object.
    :param start_time   : Bus start time.
    :param end_time     : Bus end time.
    :return             : List of all buses in the environment.
    """
    city_city_buses = []

    # 1. ------------ City to City buses --------------------------------
    cities = env_object.get_children("Kandy District")
    city_pairs = list(permutations(cities, 2))

    for city_pair in tqdm(city_pairs, desc="Generating city-city buses "):
        # print(city_pair)
        city_city_buses.extend(generate_buses_perRoute("city-city", start_time, end_time, city_pair[0], city_pair[1], env_object, velocity=40, interval=15))

    # 2. --------------- City buses -------------------------------------
    city_buses = []
    for city in tqdm(cities, desc="Generating city buses      "):
        # print(city)
        for subCity in env_object.get_children(city):
            # print(subCity)
            city_buses.extend(generate_buses_perRoute("city", start_time, end_time, subCity, None, env_object, velocity=25, interval=10))

    return city_city_buses+city_buses

if __name__ == "__main__":
    # Simulate bus movement
    env = LaunchEnvironment()
    # start_city = "Pallekele"
    # end_city = "KandyCity"
    # mode = "city-city"

    city = "GampolaSub_2"
    mode = "city"
    # print(env.get_children(city))

    # buses_city = generate_buses_perRoute(mode, 100, 1260, start_city, end_city, env, 40)
    buses_city = generate_buses_perRoute(mode, 100, 1260, city, None, env, 20)

    # for i in list(env.graph.successors("KandyCity"))+list(env.graph.successors("Gampola"))+list(env.graph.successors("Pallekele")):
    #     mode = "city"
    #     buses_city_per_node = generate_buses_perRoute(mode, 100, 1260, i, None, env, 25)
    #     buses_city.extend(buses_city_per_node)

    # print(len(buses_city))
    # print(buses_city[0].bus_tt)

    # Start_time, Start City, End City, Environment, Velocity
    # gk_bus = Bus(300, start_city, end_city, env, 20)
    # gk_bus._generate_transport_plan()
    # print(gk_bus.bus_dict)
    # buses = generate_buses_perRoute(300, 1260, "Gampola", "KandyCity", env, 1080, 'city-city', 20)
    # buses = generate_buses_perRoute(300, 1260, "Gampola", "KandyCity", env)
    # buses = buses + generate_buses_perRoute(300, 1260, "KandyCity", "Gampola", env)

    # buses = buses + generate_buses_perRoute(300, 1260, "Gampola", "Pallekele", env)
    # buses = buses + generate_buses_perRoute(300, 1260, "Pallekele", "Gampola", env)

    # buses = buses + generate_buses_perRoute(300, 1260, "KandyCity", "Pallekele", env)
    # buses = buses + generate_buses_perRoute(300, 1260, "Pallekele", "KandyCity", env)

    # bus = buses_city[0]
    # print(bus.bus_tt)
    # print('')
    # print(bus)
    # print('')

    # t = 1269
    # print(bus)
    # print(bus.bus_tt)
    #
    # for t in range(1,1440):
    #     bus.updateVehicle(time=t)
    #     print(f"-------- Time: {t} ---------")
    #     print(f"Bus is at: {bus.get_current_location()} | Previous place was: {bus.get_previous_location()}")
    #     print(bus.get_next_locations())
    #     print("")

    from RoutePlanningEngine2 import STEP_TRANSPORT
    buses = INITIALIZE_BUSES(env)
    # print(len(buses))
    # # for bus in buses:
    # #     print(bus)
    bus = buses[0]
    print(bus.bus_tt)
    # print(bus)
    #
    # for bus in buses:
    #     print(bus)

    for t in range(1,1440):
        bus.updateVehicle(time=t)
        STEP_TRANSPORT([bus], env, t)
        print(f"-------- Time: {t} ---------")
        print(f"Bus is at: {bus.get_current_location()} | Previous place was: {bus.get_previous_location()}")
        print(bus.get_next_locations())
        print("-----------------------------")

