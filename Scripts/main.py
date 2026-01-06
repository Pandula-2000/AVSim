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
from Tools import get_all_agent_count_in_env

# np.random.seed(42)

# Time the Code.
start_time = time.time()
# ------------------------------------------- SET THE CURRENT DATE AND TIME --------------------------------------------
now = datetime.now()
current_date = now.strftime("%Y-%m-%d")
current_time = now.strftime("%H:%M:%S")

# ------------------------------------------- SET SIMULATION NAME ------------------------------------------------------
simName = "Quarantine_TEST_1"
# simName = "Error test"
# ------------------------------------------- SET MANUAL PARAMETERS ----------------------------------------------------
simDays = 50
infect_random = True
percentage_of_agents_to_infect = 0.02
classes_to_infect = ['Student']

step_disease_frequency = 5
bus_max_risk = 0.3
location_max_risk = 0.5
radius_of_infection = 1

run_vaccine = False
quarantine_agents = True

quarantine_by_PCR = False
quarantine_by_class = True

pandemic_detection_threshold = 0.1

parameter_dict = {'simulation_days': simDays,
                  'infect_random': infect_random,
                  'percentage_of_agents_to_infect': percentage_of_agents_to_infect,
                  'classes_to_infect': classes_to_infect,
                  'Date': current_date,
                  'Time': current_time,
                  'STEP_DISEASE_frequency': step_disease_frequency,
                  'bus_max_risk': bus_max_risk,
                  'location_max_risk': location_max_risk,
                  'radius_of_infection': radius_of_infection,
                  'vaccinate': run_vaccine,
                  'quarantine': quarantine_agents,
                  'pandemic_detection_threshold': pandemic_detection_threshold,
                  'quarantine_by_PCR': quarantine_by_PCR,
                  'quarantine_by_class': quarantine_by_class
                  }


Loader.roh = parameter_dict['location_max_risk']
Loader.transport_roh = parameter_dict['bus_max_risk']
Loader.pandemic_detection_threshold = parameter_dict['pandemic_detection_threshold']

simName += f"_bus_{bus_max_risk}_loc_{location_max_risk}_radius_{radius_of_infection}_step_{step_disease_frequency}"

# ------------------------------------------------ SET PATHS -----------------------------------------------------------
save_path = Path(f"../Results/{simName}_{current_date}")
mobility_path = save_path.joinpath('Mobility')
pandemic_path = save_path.joinpath('Pandemic')
airBorne_disease_spread_fig_path = pandemic_path.joinpath('Air Borne Disease Spread.png')

os.makedirs(mobility_path, exist_ok=True)
os.makedirs(pandemic_path, exist_ok=True)
# --------------------------------------------- SET THE PRINTERS -------------------------------------------------------
general_info_writer = open(save_path.joinpath('General_info.txt.'), "w")

person_trajectory_printer = Printer(mobility_path.joinpath('Person_Trajectories.xlsx'))
infected_by_class_printer = Printer(pandemic_path.joinpath('Infected_by_Class.xlsx'))
contact_printer = Printer(pandemic_path.joinpath('Agent_contacts.xlsx'))

state_counts_writer = open(pandemic_path.joinpath('State_counts_for_each_day.txt.'), "w")
states_for_agent_writer = open(pandemic_path.joinpath('Agent_States_over_days.txt.'), "w")
time_table_writer = open(mobility_path.joinpath('Agent_time_tables.txt.'), "w")

# ------------------------------------------- INITIALIZE THE SIMULATION ------------------------------------------------
env = LaunchEnvironment()

# Start the Clock
Time.init()

print(f"------------------------------------- Loading Agents ---------------------------------------------------------")
agents = agent_create(env, use_def_perc=True)
print(f"Total number of agents in simulation: {len(list(agents.keys()))}")

agent_disease_state, infected_agent_keys = infectAgents(agents,
                                                        env,
                                                        infect_random=parameter_dict['infect_random'],
                                                        percentage_of_agents_to_infect=parameter_dict[
                                                            'percentage_of_agents_to_infect'],
                                                        agent_classes_to_infect=parameter_dict['classes_to_infect'])

# ------------------------------------------ Load the Transport ----------------------------------------------------
buses = INITIALIZE_BUSES(env)
# ------------------------------------------- Load the Statistics ------------------------------------------------------
Loader.init_sub_probabilities()
# ----------------------------------------------------------------------------------------------------------------------
agents = dict(list(agents.items())[:])
AGENTS = list(agents.values())
QUARANTINED_AGENTS = []

infected_by_class = {profession_class: 0 for profession_class in Loader.classes}

infected_by_class_printer.add_Columns('Sheet_1',
                                      ['Day'] + list(infected_by_class.keys()))
contact_printer.add_Columns('Agent Contacts',
                            ['Day', 'Time', 'Receiver <--', '<-- Transmitter', 'Location',
                             'Location Centroid', 'A1_state', 'A2_state', 'A1_xy', 'A2_xy'])

writeGeneralInfo(agents, parameter_dict, infected_agent_keys, general_info_writer)

# ------------------------------------------------- Loop -----------------------------------------------------------
print('\n----------------------------------- Starting Simulation -------------------------------------------------')

for DAY in range(1, simDays + 1):
    # 0. -------------- Reset the Agents ---------------------
    RESET_AGENTS(env, AGENTS)
    print(f"{len(AGENTS)} Agents , {len(QUARANTINED_AGENTS)} Quarantined Agents IN SIMULATION")
    #  1. ------------- Run Interventions -----------------------
    AGENTS, QUARANTINED_AGENTS = InterventionEngine(AGENTS,
                                                    QUARANTINED_AGENTS,
                                                    env,
                                                    parameter_dict['vaccinate'],
                                                    parameter_dict['quarantine'],
                                                    parameter_dict['quarantine_by_PCR'],
                                                    parameter_dict['quarantine_by_class'],
                                                    infected_by_class,
                                                    Agents,
                                                    Time,
                                                    Loader)
    # 2. -------------- Generate TT ---------------------------
    bimodelity.initTimeTables(env=env, Agents=AGENTS, writer=time_table_writer)  # Agent gets reset here also.
    person_trajectory_printer.print_person_trajectories(agents, isFirst=True)
    print(get_all_agent_count_in_env(env, Time.get_time()))
    # 3. Loop through the DAY
    # print(f"------------------------------- DAY {DAY} --------------------------------------")
    for MINUTE in tqdm(range(1, 1441), desc=f"Day {DAY}"):
        # 3.0. -------- Update the date and time in Printer --------------------
        Printer.update_date_time(Time.get_time(), Time.get_DAY())

        # 3.1. ----------- Step the transport system--------------
        STEP_TRANSPORT(buses,
                       env,
                       Time.get_time())

        # 3.2. ----------- Step the agent/s-----------------------
        STEP_AGENTS(AGENTS,
                    env=env,
                    time=Time.get_time(),
                    poll_threshold=8)

        # 3.3. ------------ Step Disease Propagation -------------
        STEP_DISEASE_PROPAGATION(AGENTS,
                                 QUARANTINED_AGENTS,
                                 env,
                                 buses,
                                 contact_printer,
                                 Time.get_time(),
                                 freq=parameter_dict['STEP_DISEASE_frequency'],
                                 bus_max_risk=parameter_dict['bus_max_risk'],
                                 location_transmission_risk=parameter_dict['location_max_risk'],
                                 radius_of_infection=parameter_dict['radius_of_infection'],
                                 use_transport=True)

        # 4. ----------- Print the person trajectories----------
        # person_trajectory_printer.print_person_trajectories(agents)
        # 5. ----------- Increment the time unit-----------------
        Time.increment_time_unit()

    print(f"=========================== END OF DAY {DAY} ================================")
    # 6. -------------- Write the number of infected agents by class to a file -------------------------------------------
    infected_by_class_printer.write_for_day(agents=AGENTS+QUARANTINED_AGENTS,
                                            infected_by_class=infected_by_class,
                                            day=DAY)
    infected_by_class = {profession_class: 0 for profession_class in Loader.classes}
    for key, agent in agents.items():
        agent_disease_state[key].append(agent.get_disease_state())


count = 0
# ------------------------- Write the states of each agent over days to a text file ------------------------------------
for key, value in agent_disease_state.items():
    states_for_agent_writer.write(f"{key}: {value}\n")  # Write each key on a new line
    count += 1

print(f"Total Agent count is: {count}")

# ------------------------- Write the number of agents in each state for each day --------------------------------------
# Initialize a list to hold the counts for each day
state_counts_per_day = [{i: 0 for i in range(1, 10)} for _ in range(simDays + 1)]

# Count occurrences of each state for each day
for states in agent_disease_state.values():
    for day in range(simDays + 1):
        state = states[day]
        state_counts_per_day[day][state] += 1

# Write the counts to a text file
for day, counts in enumerate(state_counts_per_day, start=1):
    state_counts_writer.write(f"Day {day}:\n")
    for state, count in counts.items():
        state_counts_writer.write(f"State {state}: {count}\n")
    state_counts_writer.write("\n")

# ------------------------------------- Close The Printers -------------------------------------------------------------
person_trajectory_printer.close_workbook()
infected_by_class_printer.close_workbook()
contact_printer.close_workbook()
time_table_writer.close()

states_for_agent_writer.close()
state_counts_writer.close()
general_info_writer.close()

# ============================================ PLOT THE FIGURES ========================================================
# 1. --------------- Plot the number of agents in each state over time.

plt.figure(figsize=(10, 6))
S = []
I = []
E = []
R = []
D = []

for day, counts in enumerate(state_counts_per_day, start=1):
    transmition_count_i = 0
    non_transmition_count_s = 0
    non_transmition_count_e = 0
    non_transmition_count_d = 0
    non_transmition_count_r = 0
    for state, count in counts.items():
        if state == 1:
            non_transmition_count_s += count
        elif state == 2:
            non_transmition_count_e += count
        elif state == 3 or state == 4 or state == 5 or state == 6 or state == 7:
            transmition_count_i += count
        elif state == 8:
            non_transmition_count_r += count
        else:
            non_transmition_count_d += count

    S.append(non_transmition_count_s)
    E.append(non_transmition_count_e)
    I.append(transmition_count_i)
    R.append(non_transmition_count_r)
    D.append(non_transmition_count_d)

days = (range(0, simDays + 1))

# Plot each y-values list
plt.plot(days, S, label='Susceptible')
plt.plot(days, E, label='Exposed')
plt.plot(days, I, label='Infected')
plt.plot(days, R, label='Recovered')
plt.plot(days, D, label='Died')

# Add labels and title
plt.xlabel('Days')
plt.ylabel('People Count')
plt.title('Air Borne Disease spread over Time')
plt.legend()  # Add a legend to differentiate the plots

# Save the plot to a file
plt.savefig(airBorne_disease_spread_fig_path)

# Display the plot (optional)
plt.show()

print(f"\n--- Executed in {(time.time() - start_time)} seconds ---")
