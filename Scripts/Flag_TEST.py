
import pandas as pd
from Environment import *
from RoutePlanningEngine2 import *
from Clock import Time
from Agents2 import *
import bimodelity
from numpy import random
from DataLoader import Loader
from Printer import *
from Public_transport import *
from Bus_plan import INITIALIZE_BUSES
from ThreeWheel_plan import *
from TransmissionEngine import STEP_DISEASE_PROPAGATION, infectAgents
from Interventions.InterventionEngine import InterventionEngine
import time
import os
from tqdm import tqdm
import matplotlib.pyplot as plt
from datetime import datetime

from Logger import Logger

# Time the Code.
start_time = time.time()
# ------------------------------------------- SET THE CURRENT DATE AND TIME --------------------------------------------
now = datetime.now()
current_date = now.strftime("%Y-%m-%d")
current_time = now.strftime("%H:%M:%S")

# ------------------------------------------- SET SIMULATION NAME ------------------------------------------------------
simName = "TransportFlag_TEST_1"
# ------------------------------------------- SET MANUAL PARAMETERS ----------------------------------------------------
simDays = 5
infect_random = False
percentage_of_agents_to_infect = 0.0
classes_to_infect = ['Student']

step_disease_frequency = 5
bus_max_risk = 0.05
location_max_risk = 0.3
radius_of_infection = 2

parameter_dict = {'simulation_days': simDays,
                  'infect_random': infect_random,
                  'percentage_of_agents_to_infect': percentage_of_agents_to_infect,
                  'classes_to_infect': classes_to_infect,
                  'Date': current_date,
                  'Time': current_time,
                  'STEP_DISEASE_frequency': step_disease_frequency,
                  'bus_max_risk': bus_max_risk,
                  'location_max_risk': location_max_risk,
                  'radius_of_infection': radius_of_infection
                  }

simName += f"_bus_{bus_max_risk}_loc_{location_max_risk}_radius_{radius_of_infection}_step_{step_disease_frequency}"

# ------------------------------------------------ SET PATHS -----------------------------------------------------------
save_path = Path(f"../Results/{simName}_{current_date}")
mobility_path = save_path.joinpath('Mobility')
pandemic_path = save_path.joinpath('Pandemic')
airBorne_disease_spread_fig_path = pandemic_path.joinpath('Air Borne Disease Spread.png')

os.makedirs(mobility_path, exist_ok=True)
os.makedirs(pandemic_path, exist_ok=True)
# --------------------------------------------- SET THE PRINTERS -------------------------------------------------------

person_trajectory_printer = Printer(mobility_path.joinpath('Person_Trajectories.xlsx'))
time_table_writer = open(mobility_path.joinpath('Agent_time_tables.txt.'), "w")

# ------------------------------------------- INITIALIZE THE SIMULATION ------------------------------------------------
env = LaunchEnvironment()
# print(env.locations)

# Start the Clock
Time.init()

print(f"------------------------------------- Loading Agents ---------------------------------------------------------")
agents = agent_create(env, use_def_perc=True)
print(f"Total number of agents in simulation: {len(list(agents.keys()))}")



# ------------------------------------------ Load the Transport ----------------------------------------------------
print('\n----------------------------------- Loading Transport ---------------------------------------------------')
buses = INITIALIZE_BUSES(env)

# ------------------------------------------- Load the Statistics ------------------------------------------------------
Loader.init_sub_probabilities()

# ----------------------------------------------------------------------------------------------------------------------
agents = dict(list(agents.items())[:])
AGENTS = list(agents.values())

# ------------------------------------------------- Loop -----------------------------------------------------------
print('\n----------------------------------- Starting Simulation -------------------------------------------------')

for DAY in range(1, simDays + 1):
    print(f"------------------------------- DAY {Time.get_dayType()} --------------------------------------")
    bimodelity.initTimeTables(env, list(agents.values()), writer=time_table_writer)
    Time.increment_day(1)
    # person_trajectory_printer.print_person_trajectories(agents, isFirst=True)

    print(f"------------------------------- DAY {DAY} --------------------------------------")
    for MINUTE in tqdm(range(1, 1441), desc=f"Day {DAY}"):
        # 1. ----------- Step the transport system------------
        STEP_TRANSPORT(buses, env, Time.get_time())

        STEP_AGENTS(list(agents.values()), env=env, time=Time.get_time(), poll_threshold=30)

        # 3. ------------ Step Disease Propagation -------------
        # STEP_DISEASE_PROPAGATION(list(agents.values()), env, Time.get_time())

        # ------------------- DEBUGGING Bus Agent Count ----------------------
        if 300<MINUTE<=1000:
            agents_in_buses_per_minute = []
            for bus in buses:
                agents_in_buses_per_minute.append(len(bus.get_agents()))
            print(MINUTE, sum(agents_in_buses_per_minute), agents_in_buses_per_minute)

        # 2. ----------- Step the agent/s-----------------------

        # if MINUTE==900:
        #     im = 0
        #     for agent in list(agents.values()):
        #         if agent.get_transition()==False:
        #             im+=1
        #     print(f"Day {DAY} | {im} agents are not in Transport")
        #     c = 0
        #     c1 = 0
        #
        #     for Location in list(env.get_all_nodes()):
        #         d = env.get_dic(Location)
        #         d2 = env.get_agents(Location)
        #         c1+=len(d2)
        #         c+=env.get_agent_count_for_state(Location,1)
        #
        #     print(f"Day {DAY} | state 1 agents present at all locations: {c} | Total agents at all locations: {c1}")
        #
        #     print(len(list(agents.values())))

        # ---------------- DEBUGGING TOTAL FLAG COUNTS --------------------------

        agentsInMotion = 0
        agentsInBus = 0
        agentsInTuk = 0
        agentsInWalk = 0
        agentsInLocations = 0
        agentsInBusStup = 0

        for agent in list(agents.values()):
            if agent.get_in_bus():
                agentsInBus+=1
            if agent.get_is_walk():
                agentsInWalk+=1
            if agent.get_transition() and agent.get_poll_timer()>0:
                agentsInBusStup+=1
            if agent.get_in_tuktuk_flag():
                agentsInTuk+=1
            if agent.get_transition():
                agentsInMotion+=1
            else:
                agentsInLocations+=1

        totalLocAgents = 0
        for Location in list(env.get_all_nodes()):
            totalLocAgents += len(env.get_agents(Location))
        # ---------------------------------------------------------


        print(f"{MINUTE} | Bus: {agentsInBus} | tuk: {agentsInTuk} | Walk: {agentsInWalk } | Bus Stop: {agentsInBusStup} | Motion: {agentsInMotion} | Locations: {agentsInLocations}| Total: {len(list(agents.values()))} | ")
        print(f"Location match: {totalLocAgents==agentsInLocations} | {totalLocAgents} | {agentsInLocations}")
        print(f"Motion match: {(agentsInBus+agentsInTuk+agentsInWalk+agentsInBusStup)==(agentsInMotion)} | Total match: {(agentsInMotion+agentsInLocations)==(len(list(agents.values())))}")

        # if (agentsInBus+agentsInTuk+agentsInWalk+agentsInBusStup)!=(agentsInMotion):
        #     print('Error in Motion Count')
        #     for agent in list(agents.values()):
        #         print(agent)
        #     # break
        # print('')

        # 3. ----------- Print the person trajectories---------
        # person_trajectory_printer.print_person_trajectories(agents)

        # 4. ----------- Increment the time unit----------------
        Time.increment_time_unit()


    # for bus in buses:
    #     print(
    #         f"{DAY}||{bus.in_motion} | {bus.get_current_location()} | {bus.get_previous_location()} | {bus.get_next_locations()}")

# person_trajectory_printer.close_workbook()
time_table_writer.close()