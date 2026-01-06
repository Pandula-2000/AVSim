

import matplotlib.pyplot as plt
from shapely.geometry import Point
from matplotlib.animation import FuncAnimation
import geopy.distance
from Environment import LaunchEnvironment
from shapely.geometry import Point,Polygon, box
import csv
from Agents2 import *
from Clock import Time
from Transport.TransportFunctions import *
from DataLoader import Loader
from shapely.wkt import loads


# --- Node details ---
node_locations = Loader.getSim('NodeEnv.xlsx', header=None)

# Remove cities and districts. People will not visit these places(Bimodality).
# node_locations = node_locations[node_locations.iloc[:, 0].str.contains('_', na=False)]


def get_three_wheelers(name, environment):
    """
    Function to get the number of three-wheelers for a given name
    :param name:
    :param environment:
    :return:
    """
    boundary = environment.get_boundary(name)
    if isinstance(boundary, Polygon):
        # Convert Polygon to WKT format string
        boundary = boundary.wkt
    polygon = loads(boundary)
    length = environment.calc_side_length(polygon)

    return int(length*0.1)  # 10 Three wheelers per 1 square km.


class ThreeWheel:
    """
    Manages all the public transport routes.

    Attributes:
        init_time       : Transport instance starting time.
        Agent           : Details of the Agent
        Environment     : City plan
        Start Node      : Start location zone
        End Node        : End location zone
        velocity        : Velocity of the instance
        vehicles_dict   : Existing Number of three wheels each node

    Methods:

    """

    def __init__(self,
                 init_time,
                 node,
                 velocity: int,
                 num_tuktuk):
        self.init_time = init_time
        # self.environment = environment
        self.num_tuktuk = num_tuktuk
        # self.start_node = start_node
        # self.end_node = end_node
        self.node = node
        self.velocity = velocity
        self.vehicles_dict = {}
        # self.num_vehicles_end_node, time = self.vehicles_dict[self.end_node]
        self.in_motion = False
        self.current_location = self.node
        self.next_location = None
        self.agent= None  # A list of agent objects inside the transport vehicle.
        self.tuktuk_timer = 0
        self.id = str(self.node) + "tuktuk" + str(self.num_tuktuk)

    def add_agent(self, agent):
        self.agent = agent

    def remove_agent(self, agent):
        self.agent = None

    def get_agent(self, agent):
        return self.agent

    def set_current_location(self, loc):
        self.current_location = loc

    def set_next_location(self, loc):
        self.next_location = loc

    def set_in_motion(self, motion):
        self.in_motion = motion

    def get_current_location(self):
        return self.current_location

    def get_next_location(self):
        return self.next_location

    def get_in_motion(self):
        return self.in_motion

    def set_tuktuk_timer(self, time):
        self.tuktuk_timer = time

    def get_tuktuk_timer(self):
        return self.tuktuk_timer

    def updateVehicle(self, env):
        # print(self.in_motion)
        if self.in_motion:
            self.tuktuk_timer -= Time.get_time_resolution()
            print('Tuk Counter :', self.tuktuk_timer)
            # --------------------------------------- Now the trip is over ---------------------------------------------
            # FIXME: We can transport the tuk back to its origin place ???
            if self.tuktuk_timer <= 0:
                self.tuktuk_timer = 0
                self.current_location = self.next_location
                env.add_tuktuk(self.current_location, self)
                self.next_location = None
                self.in_motion = False
                # ------- Agent related --------
                tuk_agent = self.agent
                # NOTE: Used to trigger if block at RoutePlanning when agent has completed the trip
                tuk_agent.set_curr_loc(self.current_location)
                tuk_agent.set_walk_flag(False)

                print(f"---------------Tuk Trip is over for {tuk_agent._agent_name}-------------")
                self.agent = None
        else:
            # Do nothing. The Tuk is not in motion.
            pass


def availableThreeWheel(three_wheel_list: list, agent: Agents):
    # for three_wheel in three_wheel_list:
    return three_wheel_list[0]


def generate_tuktuks(environment_object, init_time, velocity):
    list_of_tuktuk_objects = []
    # Information about nodes
    nodes = extract_nodes(node_locations, environment_object)
    for node in nodes:
        if len(node.split('_')) == 1:
            continue
        for num_tuktuk in range(0,int(get_three_wheelers(node, environment_object))):
            tuktuk = ThreeWheel(init_time, node, velocity, num_tuktuk)
            environment_object.add_tuktuk(node, tuktuk)
            list_of_tuktuk_objects.append(tuktuk)
    return list_of_tuktuk_objects

if __name__ == "__main__":
    # Simulate Three Wheel movement
    env = LaunchEnvironment()

    tuks=generate_tuktuks(env,200,20)
    print(len(tuks))


    # start_node = "AdministrativeZone_1"
    # end_node = "ResidentialZone_1"

    # three_wheels = {}

    # with open(node_locations, 'r') as file:
    #     reader = csv.DictReader(file)
    #     for row in reader:
    #         three_wheels[row['name']] = int(row['No three-wheelers']), init_time

    # num_vehicles_start_node, temp_time = three_wheels[start_node]
    # num_vehicles_start_node -= 1

    # if num_vehicles_start_node >= 0:
    #     three_wheels[start_node] = num_vehicles_start_node, temp_time
    #     print(three_wheels)

    #     # Start_time, Agent, Environment, Start City, End City,  Velocity, Vehicle_dict
    #     three_wheel_1 = ThreeWheel(init_time, "agent_temp" , env, start_node, end_node, 25, three_wheels)
    #     three_wheel_1 = three_wheel_1.transport_plan()
    #     print(three_wheel_1)

    # else:
    #     print("Not enough three wheelers")
