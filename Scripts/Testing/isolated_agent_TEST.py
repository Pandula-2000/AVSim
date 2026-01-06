import pandas as pd

from Environment import *
from RoutePlaningEngine import *
from Clock import Time
from Agents import *
import bimodelity
from numpy import random
from DataLoader import Loader
from Public_transport import *
from Bus_plan import *
import time
import os

if __name__ == "__main__":
    start_time = time.time()
    # Start the clock
    Time.init()
    # Launch the Environment
    env = LaunchEnvironment()
    # Spawn the Agents
    print(f"--------------------------------- Loading Agents ---------------------------------------------------------")
    agents = agent_create(env, use_def_perc=True)

    # Select a specific agent for testing
    agent = agents['BankWorker_1']

    h = 'Home_11'
    w = 'Bank_5'
    # --------------------------------- Only uncomment for recreating captured cases ----------------
    agent.set_curr_loc(h)
    agent.set_init_loc(h)
    agent.set_work_loc(w)
    # ----------------------------------------------------------------------------

    print(f"Agents init location    : {agent._init_location}")
    print(f"Agents current location : {agent.get_current_location()}")

    agent.set_coordinates(env.get_centroid(agent.get_current_location()))

    print(f"Agents coordinates      : {agent.get_coordinates()}")
    print(f"Agents work location    : {agent.get_work_loc()}")

    print(f"init stay               : {agent.get_stay_duration()}")

    # RANDOM_MOTION(agent)
    env.add_agent(h, agent)
    l = env.get_agents(h)
    for a in l:
        print(f"---------- Agents at home:   {a._agent_name}")

    # ------------------------------------------ Load the statistics ---------------------------------------------------
    Time.init()
    # Loader.init_probabilities()
    Loader.init_sub_probabilities()

    # init data loader stat here ...
    # ------------------------------------------ Load the Transport ----------------------------------------------------
    print('\n----------------------------------- Loading Transport ---------------------------------------------------')
    '''  
    Gampola
    KandyCity
    Pallekale
    '''

    buses = generate_buses_perRoute(100, 1260, "Gampola", "KandyCity", env)
    buses = buses + generate_buses_perRoute(100, 1260, "KandyCity", "Gampola", env)
    buses = buses + generate_buses_perRoute(100, 1260, "Gampola", "Pallekele", env)
    buses = buses + generate_buses_perRoute(100, 1260, "Pallekele", "Gampola", env)
    buses = buses + generate_buses_perRoute(100, 1260, "KandyCity", "Pallekele", env)
    buses = buses + generate_buses_perRoute(100, 1260, "Pallekele", "KandyCity", env)

    tuk_tuks = generate_tuktuks(env, 200, 25)

    # --------------------------------------------- SET THE PRINTERS ---------------------------------------------------
    # from Printer import *
    # person_trajectory_printer = Printer(Path('Results/Person_Trajectories.xlsx'))
    # person_trajectory_printer.print_person_trajectories(agents, isFirst=True)

    # ------------------------------------------------- Loop -----------------------------------------------------------
    print('\n----------------------------------- Starting Simulation -------------------------------------------------')
    # print(Time.get_time())
    # print(agent._next_location_class)

    # tt = bimodelity.generateTimeTable(env, agent,start_time=5, end_time=15)
    tt = [['Home_11', 'CommercialFinancialZone_2', 'GatheringPlace_2', 'Bank_5', 'Hospital_2'], [(300, 20), (320, 100), (420, 100), (520, 400), (920, 220)]]
    agent._timeTable = tt

    # print(f"Agents Time Table:  {tt}")
    # print(f"Bus TT: {buses[0].bus_dict}")
    # IMPORTANT: The Main Loop.
    # Time.set_t(300)
    # sim_end_time = 1300
    print("-----------------------------LOOOOOP-------------------------------------------------------")

    # Initialize the timeTables
    # bimodelity.initTimeTables(env, [agent])
    # bimodelity.initTimeTables(env, agents.values())

    print(f"Agent Time Table: {agent.get_timeTable()}")

    while Time.get_time() < 1440:
        # print(f"Simulating at time: {Time.get_time()}")
        # 1. ----------- Step the transport system------------
        STEP_TRANSPORT(tuk_tuks, buses, env, Time.get_time())
        # print(f"{env.get_buses('Home_29')} at Home_29")
        # print(f"T: {Time.get_time()} | {buses[0].get_previous_location()}")

        # 2. ----------- Step the agent/s-----------------------

        # STEP_AGENTS([agent], env=env, time=Time.get_time())
        STEP_AGENTS(tuk_tuks,[agent], env=env, time=Time.get_time())

        # 3. ----------- Print the person trajectories---------
       # person_trajectory_printer.print_person_trajectories(agents)
        # 4. ----------- Increment the time unit----------------
        Time.increment_time_unit()
        # print('')

    #person_trajectory_printer.close_workbook()
    l = env.get_agents('Home_37')
    for a in l:
        print(f"---------- Agents at Home_11:   {a._agent_name}")
    print(f"\n---------------------- Executed in {(time.time() - start_time)} seconds --------------------------------")
