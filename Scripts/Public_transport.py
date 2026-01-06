import csv
import random
import math
import os
import matplotlib.pyplot as plt
from shapely.geometry import Point
import time
from matplotlib.animation import FuncAnimation
import geopy.distance


# Function to parse point from string
def parse_point(point_string):
    lon, lat = point_string.strip('POINT ()').split()
    return Point(float(lon), float(lat))

# Function to calculate distance between two points
def calculate_distance(point1, point2):
    distance_m = (geopy.distance.geodesic((point1.x,point1.y), (point2.x,point2.y)).km)*1000
    return distance_m

# Function to calculate travel time between two points
def calculate_travel_time(distance, velocity):
    return distance / velocity

def extract_nodes(node_locations):
    # Read test environment node locations 
    nodes = {}

    with open(node_locations, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            nodes[row['name']] = parse_point(row['Random Point'])

    return nodes


# Node details
node_locations = r'.\Data\BusHaltPlan.csv'

class Public_transport():

    """
    Manages all the public transport routes.

    Attributes:
        start_node: Starting zone of any public transport instance.
        end_node: Destination zone of any public transport instance.
        init_time: Transport instance starting time.
        velocity: Velocity of the instance. 
        sched_time: Scheduled time between two buses (Default 20 minutes)
        class_name: Details of route (Name and date)

    Methods:
    
    """
        
    def __init__(self, class_name, init_time, start_node, end_node, intermediate_nodes: list, velocity: int, sched_time=20):
        self.init_time = init_time
        self.start_node = start_node
        self.end_node = end_node
        self.intermediate_nodes = intermediate_nodes
        self.velocity = velocity
        self.class_name = class_name
        self.waiting_time = sched_time

    def transport_plan(self):    
        self.velocity = 20  # Assume velocity in km per hour
        time_interval = 5  # Time wait in intermediate zones
        num_buses = 45
        nodes = extract_nodes(node_locations)
        
        in_time = []
        dep_time = []
        next_loc = []
        bus_dep_time = 0

        directory = r'Results'
        if not os.path.exists(directory):
            os.makedirs(directory)

        self.filepath = os.path.join(directory, f'{self.class_name}_PublicTransportPlan.csv')

        with open(self.filepath, mode='w', newline='') as file:
            self.writer = csv.writer(file)
            # Write the header
            self.writer.writerow(["Start Time", "End Time", "Current Location", "Next Locations"])

            for i in range(0, num_buses):
                start_time = 0
                end_time = 5
                current_node = self.start_node
                total_time = 0
                x_values = [nodes[current_node].x]
                y_values = [nodes[current_node].y]

                start_time += bus_dep_time
                end_time += bus_dep_time

                in_time.append(start_time)
                dep_time.append(end_time)
                next_loc = self.intermediate_nodes + [self.end_node]
                val = 0

                for next_node in self.intermediate_nodes + [self.end_node]:
                    if current_node == next_node:
                        continue

                    next_loc = self.intermediate_nodes[val:] + [self.end_node]

                    rows = zip([start_time], [end_time], [current_node], [next_loc])

                    # Write the rows
                    self.writer.writerows(rows)

                    distance = calculate_distance(nodes[current_node], nodes[next_node])
                    travel_time = int(calculate_travel_time(distance, self.velocity))
                    
                    # Move to the next node
                    total_time += travel_time

                    x_values.append(nodes[next_node].x)
                    y_values.append(nodes[next_node].y)
                    
                    # Wait for 5 minutes at intermediate nodes
                    if next_node in self.intermediate_nodes:
                        total_time += time_interval

                    start_time = total_time + bus_dep_time
                    end_time = start_time + time_interval

                    in_time.append(start_time)
                    dep_time.append(end_time)
                    
                    current_node = next_node
                    val += 1

                current_node_ = self.end_node
                start_time_ = total_time + time_interval + 15 + bus_dep_time
                val_ = 0

                end_time_ = start_time_ + time_interval
                intermediate_nodes_ = self.intermediate_nodes[::-1]
                
                for next_node_ in intermediate_nodes_ + [self.start_node]:
                    if current_node_ == next_node_:
                        continue

                    next_loc_ = intermediate_nodes_[val_:] + [self.start_node]
                    rows_ = zip([start_time_], [end_time_], [current_node_], [next_loc_])

                    # Write the rows
                    self.writer.writerows(rows_)

                    distance_ = calculate_distance(nodes[current_node_], nodes[next_node_])
                    travel_time_ = int(calculate_travel_time(distance_, self.velocity))
                    
                    # Move to the next node
                    start_time_ += travel_time_

                    x_values.append(nodes[next_node_].x)
                    y_values.append(nodes[next_node_].y)
                    
                    # Wait for 5 minutes at intermediate nodes
                    if next_node_ in intermediate_nodes_:
                        start_time_ += time_interval

                    end_time_ = start_time_ + time_interval

                    in_time.append(start_time_)
                    dep_time.append(end_time_)
                    
                    current_node_ = next_node_
                    val_ += 1

                bus_dep_time += self.waiting_time

        return None


if __name__ == "__main__":
    # Simulate bus movement
    start_node = 'MedicalZone_3'
    end_node = 'CommercialFinancialZone_2'
    intermediate_nodes = ['ResidentialZone_2', 'EducationZone_3', 'ResidentialZone_6']
    name = 'gampola_kandy_bus_31_05'
    gk_bus = Public_transport(name, 300, start_node, end_node, intermediate_nodes, 20)
    gk_bus.transport_plan()
    print(gk_bus)
