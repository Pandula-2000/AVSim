import os
import time
import yaml
from pathlib import Path
from datetime import datetime

import pandas as pd
import matplotlib.pyplot as plt
from tqdm import tqdm

from Environment import LaunchEnvironment
from RoutePlanningEngine2 import STEP_AGENTS, STEP_TRANSPORT
from Clock import Time
from Agents2 import agent_create, RESET_AGENTS, Agents
import bimodelity
from DataLoader import Loader
from Printer import Printer, writeGeneralInfo
from Bus_plan import INITIALIZE_BUSES
from TransmissionEngine import STEP_DISEASE_PROPAGATION, infectAgents
from Interventions.InterventionEngine import InterventionEngine
from Tools import get_all_agent_count_in_env

def load_config(config_path="config.yaml"):
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def setup_directories(sim_name, current_date):
    save_path = Path(f"../Results/{sim_name}_{current_date}")
    mobility_path = save_path.joinpath('Mobility')
    pandemic_path = save_path.joinpath('Pandemic')
    
    os.makedirs(mobility_path, exist_ok=True)
    os.makedirs(pandemic_path, exist_ok=True)
    
    return save_path, mobility_path, pandemic_path

def plot_simulation_results(state_counts_per_day, sim_days, output_path):
    plt.figure(figsize=(10, 6))
    s_list, e_list, i_list, r_list, d_list = [], [], [], [], []

    for counts in state_counts_per_day:
        transmition_count_i = sum(counts.get(state, 0) for state in range(3, 8))
        non_transmition_count_s = counts.get(1, 0)
        non_transmition_count_e = counts.get(2, 0)
        non_transmition_count_r = counts.get(8, 0)
        non_transmition_count_d = counts.get(9, 0)

        s_list.append(non_transmition_count_s)
        e_list.append(non_transmition_count_e)
        i_list.append(transmition_count_i)
        r_list.append(non_transmition_count_r)
        d_list.append(non_transmition_count_d)

    days = list(range(0, sim_days + 1))

    plt.plot(days, s_list, label='Susceptible')
    plt.plot(days, e_list, label='Exposed')
    plt.plot(days, i_list, label='Infected')
    plt.plot(days, r_list, label='Recovered')
    plt.plot(days, d_list, label='Died')

    plt.xlabel('Days')
    plt.ylabel('People Count')
    plt.title('Air Borne Disease spread over Time')
    plt.legend()
    
    plt.savefig(output_path)
    # plt.show() # Disabled to prevent blocking execution

def main():
    start_time = time.time()
    
    now = datetime.now()
    current_date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M:%S")

    # Load configuration
    config = load_config()
    
    sim_days = config['simulation_days']
    bus_max_risk = config['bus_max_risk']
    location_max_risk = config['location_max_risk']
    radius_of_infection = config['radius_of_infection']
    step_disease_frequency = config['step_disease_frequency']
    
    sim_name = f"{config['simulation_name']}_bus_{bus_max_risk}_loc_{location_max_risk}_radius_{radius_of_infection}_step_{step_disease_frequency}"
    
    # Configure Loader
    Loader.roh = location_max_risk
    Loader.transport_roh = bus_max_risk
    Loader.pandemic_detection_threshold = config['pandemic_detection_threshold']

    # Setup Paths
    save_path, mobility_path, pandemic_path = setup_directories(sim_name, current_date)
    airborne_disease_spread_fig_path = pandemic_path.joinpath('Air Borne Disease Spread.png')

    # Initialize Printers
    general_info_writer = open(save_path.joinpath('General_info.txt'), "w")
    person_trajectory_printer = Printer(mobility_path.joinpath('Person_Trajectories.xlsx'))
    infected_by_class_printer = Printer(pandemic_path.joinpath('Infected_by_Class.xlsx'))
    contact_printer = Printer(pandemic_path.joinpath('Agent_contacts.xlsx'))
    state_counts_writer = open(pandemic_path.joinpath('State_counts_for_each_day.txt'), "w")
    states_for_agent_writer = open(pandemic_path.joinpath('Agent_States_over_days.txt'), "w")
    time_table_writer = open(mobility_path.joinpath('Agent_time_tables.txt'), "w")

    try:
        # Initialize Simulation
        env = LaunchEnvironment()
        Time.init()

        print("------------------------------------- Loading Agents ---------------------------------------------------------")
        agents_dict = agent_create(env, use_def_perc=True)
        print(f"Total number of agents in simulation: {len(agents_dict)}")

        agent_disease_state, infected_agent_keys = infectAgents(
            agents_dict,
            env,
            infect_random=config['infect_random'],
            percentage_of_agents_to_infect=config['percentage_of_agents_to_infect'],
            agent_classes_to_infect=config['classes_to_infect']
        )

        buses = INITIALIZE_BUSES(env)
        Loader.init_sub_probabilities()

        agents_dict = dict(list(agents_dict.items())[:])
        agent_list = list(agents_dict.values())
        quarantined_agents = []

        infected_by_class = {profession_class: 0 for profession_class in Loader.classes}

        infected_by_class_printer.add_Columns('Sheet_1', ['Day'] + list(infected_by_class.keys()))
        contact_printer.add_Columns('Agent Contacts', [
            'Day', 'Time', 'Receiver <--', '<-- Transmitter', 'Location',
            'Location Centroid', 'A1_state', 'A2_state', 'A1_xy', 'A2_xy'
        ])

        # Prepare parameter dict for General Info writer backward compatibility
        parameter_dict = config.copy()
        parameter_dict.update({
            'Date': current_date,
            'Time': current_time,
            'STEP_DISEASE_frequency': config['step_disease_frequency'],
            'vaccinate': config['run_vaccine'],
            'quarantine': config['quarantine_agents']
        })
        writeGeneralInfo(agents_dict, parameter_dict, infected_agent_keys, general_info_writer)

        print('\n----------------------------------- Starting Simulation -------------------------------------------------')

        for day in range(1, sim_days + 1):
            RESET_AGENTS(env, agent_list)
            print(f"{len(agent_list)} Agents , {len(quarantined_agents)} Quarantined Agents IN SIMULATION")
            
            agent_list, quarantined_agents = InterventionEngine(
                agent_list,
                quarantined_agents,
                env,
                config['run_vaccine'],
                config['quarantine_agents'],
                config['quarantine_by_pcr'],
                config['quarantine_by_class'],
                infected_by_class,
                Agents,
                Time,
                Loader
            )
            
            bimodelity.initTimeTables(env=env, Agents=agent_list, writer=time_table_writer)
            person_trajectory_printer.print_person_trajectories(agents_dict, isFirst=True)
            print(get_all_agent_count_in_env(env, Time.get_time()))
            
            for minute in tqdm(range(1, 1441), desc=f"Day {day}"):
                Printer.update_date_time(Time.get_time(), Time.get_DAY())
                STEP_TRANSPORT(buses, env, Time.get_time())
                STEP_AGENTS(agent_list, env=env, time=Time.get_time(), poll_threshold=8)
                STEP_DISEASE_PROPAGATION(
                    agent_list,
                    quarantined_agents,
                    env,
                    buses,
                    contact_printer,
                    Time.get_time(),
                    freq=config['step_disease_frequency'],
                    bus_max_risk=config['bus_max_risk'],
                    location_transmission_risk=config['location_max_risk'],
                    radius_of_infection=config['radius_of_infection'],
                    use_transport=True
                )
                Time.increment_time_unit()

            print(f"=========================== END OF DAY {day} ================================")
            
            infected_by_class_printer.write_for_day(
                agents=agent_list + quarantined_agents,
                infected_by_class=infected_by_class,
                day=day
            )
            
            infected_by_class = {profession_class: 0 for profession_class in Loader.classes}
            
            for key, agent in agents_dict.items():
                agent_disease_state[key].append(agent.get_disease_state())

        count = 0
        for key, value in agent_disease_state.items():
            states_for_agent_writer.write(f"{key}: {value}\n")
            count += 1
        print(f"Total Agent count is: {count}")

        state_counts_per_day = [{i: 0 for i in range(1, 10)} for _ in range(sim_days + 1)]
        for states in agent_disease_state.values():
            for day in range(sim_days + 1):
                state = states[day]
                state_counts_per_day[day][state] += 1

        for day, counts in enumerate(state_counts_per_day, start=1):
            state_counts_writer.write(f"Day {day}:\n")
            for state, count in counts.items():
                state_counts_writer.write(f"State {state}: {count}\n")
            state_counts_writer.write("\n")

        plot_simulation_results(state_counts_per_day, sim_days, airborne_disease_spread_fig_path)

        print(f"\n--- Executed in {(time.time() - start_time):.2f} seconds ---")

    finally:
        person_trajectory_printer.close_workbook()
        infected_by_class_printer.close_workbook()
        contact_printer.close_workbook()
        time_table_writer.close()
        states_for_agent_writer.close()
        state_counts_writer.close()
        general_info_writer.close()

if __name__ == "__main__":
    main()
