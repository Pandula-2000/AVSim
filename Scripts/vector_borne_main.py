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
from Bus_plan import *
from ThreeWheel_plan import *
from VBEngine import *
import time
from tqdm import tqdm
from Interventions.InterventionEngine_VB import InterventionEngine
from VB_plots import plot_states
# NOTE: THIS IS AN EXTENSION OF THE main.py FOR VECTOR BOURNE DISEASES

if __name__ == "__main__":
    
    visualize = False
    save_plot = False
    controlled = False
    
    # Time the Code.
    start_time = time.time()
    # ------------------------------------------- SET THE CURRENT DATE AND TIME --------------------------------------------
    now = datetime.now()
    current_date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H-%M-%S")

    # # ------------------------------------------------- SET PARAMETERS -----------------------------------------------------

    simDays = 10

    # ------------------------------------------- SET SIMULATION NAME ------------------------------------------------------
    simName = "VB Simulation"

    folder = f'../Results/{simName}_{simDays}_Days_{current_date}_{current_time}'
    
    # ------------------------------------------------ SET PATHS -----------------------------------------------------------
    save_path = Path(folder)
    mobility_path = save_path.joinpath('Mobility')
    vb_path = save_path.joinpath('Pandemic')

    os.makedirs(mobility_path, exist_ok=True)
    os.makedirs(vb_path, exist_ok=True)

    # --------------------------------------------- SET THE PRINTERS ---------------------------------------------------
    # person_trajectory_printer = Printer(Path(f'../Results/{simName}_{current_date}/Mobility/Person_Trajectories.xlsx'))
    person_disease_state_printer = Printer(Path(f'{folder}/Pandemic/Person_Disease_States.xlsx'))
    # person_disease_trace_printer = Printer(Path(f'{folder}/Pandemic/Person_Infected_Patch_Trace.xlsx'))
    time_table_writer = open(f"{folder}/Mobility/Agent_time_tables.txt", "w")
    
    # ------------------------------------------- INITIALIZE THE SIMULATION ------------------------------------------------
    env = LaunchEnvironment()
    # Initialize patch grids
    PATCHES = init_patch_grid(env)
    # visualize_patches_(env, 0, folder=f'{folder}/Pandemic', total=True)
    
    # Start the Clock
    Time.init()

    print(f"------------------------------------- Loading Agents ---------------------------------------------------------")
    agents = agent_create(env, use_def_perc=True, vb=True)
    agents = dict(list(agents.items())[:])
    AGENTS = list(agents.values())
    HOSPITALIZED_AGENTS = []
    REMOVED_AGENTS = []
    non_hospitalized_state_counts_over_days = {state.name: [] for state in Disease_State}
    hospitalized_state_counts_over_days = {state.name: [] for state in Disease_State}

    # print(f"------------------------------------------- Statistics -------------------------------------------------------")

    Loader.init_sub_probabilities()
    
    
    print(f"------------------------------------- Assign Infectious Agents ---------------------------------------------------------")
    # assign_initial_infection(env, "AgriculturalZone", 2, "any", 1, ((50,45), (45,20), (20,10)), 3)
    # assign_initial_infection(env, "AgriculturalZone", 2, "any", 1, ((50,45), (45,20), (20,10)), 3)
    assign_initial_infection(env, "ResidentialZone_5", 1, "Home", 10, agnt_count=1)
    # assign_initial_infection(env, specific="Home_1")
    # assign_initial_infection(env, "ResidentialZone", 1, "Home", 6, ((50,45), (60,40), (55,35)), 5)
    if visualize: visualize_patches_(env, 0, folder=f'{folder}/Pandemic')

    # ------------------------------------------------- Loop -----------------------------------------------------------
    print('\n----------------------------------- Starting Simulation -------------------------------------------------')
    person_disease_state_printer.print_person_disease_state(agents, 0, isFirst=True)
    # person_disease_trace_printer.print_person_disease_trace(AGENTS, 0, 0, isFirst=True)
    
    for DAY in range(1, simDays+1):
        bimodelity.initTimeTables(env, AGENTS, writer=time_table_writer)
        # person_trajectory_printer.print_person_trajectories(agents, isFirst=True)
        AGENTS, HOSPITALIZED_AGENTS, REMOVED_AGENTS = InterventionEngine(DAY, AGENTS, HOSPITALIZED_AGENTS, REMOVED_AGENTS, env, non_hospitalized_state_counts_over_days, hospitalized_state_counts_over_days, controlled)
                
        # print(f"------------------------------- DAY {DAY} --------------------------------------")
        for MINUTE in tqdm(range(1, 1441), desc=f"Day {DAY}"):
            # 1. ----------- Step the agent/s-----------------------
            STEP_AGENTS_V2(AGENTS, env=env, time=Time.get_time())

            # 2. ------------ Step Disease Propagation -------------
            STEP_DISEASE_PROPAGATION(env, HOSPITALIZED_AGENTS, Time.get_time(), DAY)

            # # 3. ----------- Print the person trajectories---------
            # person_trajectory_printer.print_person_trajectories(agents)
            
            # 3. ----------- Print the person disease states ---------
            # person_disease_state_printer.print_person_disease_state(agents, DAY)
            # person_disease_trace_printer.print_person_disease_trace(AGENTS, DAY, MINUTE)

            # 4. ----------- Increment the time unit----------------
            Time.increment_time_unit()
            
        # 5. ----------- Visualize the patches ----------------
        if visualize: visualize_patches_(env, DAY, folder=f'{folder}/Pandemic')
        if save_plot: plot_mosquito_density(PATCHES, DAY, folder=f'{folder}/Pandemic')
                
        if(DAY == 1 or DAY % 10 == 0):
            visualize_patches_(env, DAY, folder=f'{folder}/Pandemic')
            plot_mosquito_density(PATCHES, DAY, folder=f'{folder}/Pandemic')

            # Save the Disease State Counts Over Time (Every 30 days just in case)
            
            # state_counts_df = pd.DataFrame(state_counts_over_days)
            # state_counts_df.drop(columns=['CRITICAL'], inplace=True)
            # state_counts_df.insert(0, 'Day', range(1, len(state_counts_df) + 1))
            # # print(state_counts_df.head())
            # state_counts_df.to_csv(f'{folder}/Pandemic/state_counts_over_days.csv', index=False)
            # Create DataFrames from both dictionaries
            all_state_counts_df = pd.DataFrame(non_hospitalized_state_counts_over_days)
            hospitalized_state_counts_df = pd.DataFrame(hospitalized_state_counts_over_days)

            all_state_counts_df.drop(columns=['CRITICAL'], inplace=True)
            hospitalized_state_counts_df.drop(columns=['SUSCEPTIBLE', 'Incubation', 'Infectious', 'CRITICAL', 'Asymptotic'], inplace=True)

            num_days = len(all_state_counts_df)
            day_column = pd.DataFrame({'Day': range(1, num_days + 1)})

            combined_df = pd.concat([day_column, all_state_counts_df, hospitalized_state_counts_df], axis=1)
            combined_df.to_csv(f'{folder}/Pandemic/state_counts_over_days.csv', index=False)


    # ---------------------------- Save the Disease State Counts Over Time ----------------------------------------------
    # state_counts_df = pd.DataFrame(state_counts_over_days)
    # state_counts_df.drop(columns=['CRITICAL'], inplace=True)
    # state_counts_df.insert(0, 'Day', range(1, len(state_counts_df) + 1))
    # # print(state_counts_df.head())
    # state_counts_df.to_csv(f'{folder}/Pandemic/state_counts_over_days.csv', index=False)
    plot_states(non_hospitalized_state_counts_over_days, hospitalized_state_counts_over_days, folder, simDays)

    # ---------------------------- Plot the Aggregated Disease State Counts Over Time ----------------------------------------------

    # state_counts_over_days_aggregated["Infectious"] = (
    #     np.array(state_counts_over_days[Disease_State.Infectious.name]) + 
    #     np.array(state_counts_over_days[Disease_State.MILD.name]) + 
    #     np.array(state_counts_over_days[Disease_State.SEVERE.name]) +
    #     np.array(state_counts_over_days[Disease_State.Asymptotic.name])
    # )

    # # Add the other states directly to the aggregated dictionary
    # # state_counts_over_days_aggregated["Susceptible"] = state_counts_over_days[Disease_State.SUSCEPTIBLE.name]
    # state_counts_over_days_aggregated["Exposed"] = state_counts_over_days[Disease_State.Incubation.name]
    # state_counts_over_days_aggregated["Dead"] = state_counts_over_days[Disease_State.Dead.name]
    # state_counts_over_days_aggregated["Recovered"] = state_counts_over_days[Disease_State.Recovered.name]

    # plt.figure(figsize=(10, 6))

    # for state_name, counts in state_counts_over_days_aggregated.items():
    #     plt.plot(range(1, simDays + 1), counts, label=state_name)

    # plt.title("Disease State Counts Over Time")
    # plt.xlabel("Day")
    # plt.ylabel("State Count")
    # plt.legend(title="Disease States")
    # plt.savefig(f'{folder}/Pandemic/states.png')
    # # plt.show()

    # ---------------------------- Plot the Infected Disease Counts Over Time ----------------------------------------------
    
    # state_counts_over_days_infected["Infectious"] = state_counts_over_days[Disease_State.Infectious.name]
    # state_counts_over_days_infected["Mild"] = state_counts_over_days[Disease_State.MILD.name]
    # state_counts_over_days_infected["Severe"] = state_counts_over_days[Disease_State.SEVERE.name]
    # state_counts_over_days_infected["Asymptotic"] = state_counts_over_days[Disease_State.Asymptotic.name]

    # plt.figure(figsize=(10, 6))

    # for state_name, counts in state_counts_over_days_infected.items():
    #     plt.plot(range(1, simDays + 1), counts, label=state_name)
    
    # plt.plot(range(1, simDays + 1), state_counts_over_days_aggregated["Infectious"], label="Total Infected", linestyle='--')

    # plt.title("Infected Disease State Counts Over Time")
    # plt.xlabel("Day")
    # plt.ylabel("State Count")
    # plt.legend(title="Infected Disease States")
    # plt.savefig(f'{folder}/Pandemic/infected_states.png')

    # person_trajectory_printer.close_workbook()
    person_disease_state_printer.close_workbook()
    # person_disease_trace_printer.close_workbook()
    time_table_writer.close()
    
    # plot infectious traces
    # visualize_infected_traces(env, Path(f'{folder}/Pandemic/Person_Infected_Patch_Trace.xlsx'), folder, PATCHES)


    print(f"\n--- Executed in {(time.time() - start_time)} seconds ---")

