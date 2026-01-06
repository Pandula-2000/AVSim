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


# Time the Code.
start_time = time.time()
# ------------------------------------------- SET THE CURRENT DATE AND TIME --------------------------------------------
now = datetime.now()
current_date = now.strftime("%Y-%m-%d")
current_time = now.strftime("%H:%M:%S")

# ------------------------------------------- SET SIMULATION NAME ------------------------------------------------------
simName = "ErrorDebugging"
# ------------------------------------------- SET MANUAL PARAMETERS ----------------------------------------------------
simDays = 50
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

# Start the Clock
Time.init()

print(f"------------------------------------- Loading Agents ---------------------------------------------------------")
agents = agent_create(env, use_def_perc=True)
print(f"Total number of agents in simulation: {len(list(agents.keys()))}")


# ------------------------------------------ Load the Transport ----------------------------------------------------
buses = INITIALIZE_BUSES(env)
# ------------------------------------------- Load the Statistics ------------------------------------------------------
Loader.init_sub_probabilities()
# ----------------------------------------------------------------------------------------------------------------------
agents = dict(list(agents.items())[:])
AGENTS = list(agents.values())
# ------------------------------------------------- Loop -----------------------------------------------------------
print('\n----------------------------------- Starting Simulation -------------------------------------------------')

for DAY in range(1, simDays + 1):
    # tuk_tuks = generate_tuktuks(env, 200, 25)
    RESET_AGENTS(env, AGENTS)

    bimodelity.initTimeTables(env=env, Agents=AGENTS, writer=time_table_writer)

    person_trajectory_printer.print_person_trajectories(agents, isFirst=True)

    # print(f"------------------------------- DAY {DAY} --------------------------------------")
    for MINUTE in tqdm(range(1, 1441), desc=f"Day {DAY}"):
        # 0. -------- Update the date and time in Printer --------------------
        Printer.update_date_time(Time.get_time(), Time.get_DAY())

        # # 1. ----------- Step the transport system--------------
        STEP_TRANSPORT(buses,
                       env,
                       Time.get_time())
        #
        # # # 2. ----------- Step the agent/s-----------------------
        STEP_AGENTS(AGENTS,
                    env=env,
                    time=Time.get_time(),
                    poll_threshold=15)

        # # 3. ----------- Print the person trajectories----------
        person_trajectory_printer.print_person_trajectories(agents)

        # # 4. ----------- Increment the time unit-----------------
        Time.increment_time_unit()
    # env.reset_tuktuk()

    # print(f"=========================== END OF DAY {DAY} ================================")

person_trajectory_printer.close_workbook()
