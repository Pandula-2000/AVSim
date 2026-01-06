import pandas as pd
import time

from Environment import *
from RoutePlaningEngine import *
from Clock import Time
from Agents2 import *
import bimodelity
from numpy import random
from DataLoader import Loader
from Printer import *
from VBEngine import * 
from tqdm import tqdm
from Patches import *

if __name__ == "__main__":
    # Time the Code.
    start_time = time.time()
    # ------------------------------------------- SET THE CURRENT DATE AND TIME --------------------------------------------
    now = datetime.now()
    current_date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M:%S")

    # ------------------------------------------- SET SIMULATION NAME ------------------------------------------------------
    simName = "VB Simulation"

    # ------------------------------------------- INITIALIZE THE SIMULATION ------------------------------------------------
    env = LaunchEnvironment()
    # Initialize patch grids
    init_patch_grid(env)
    # Start the Clock
    Time.init()

    print(f"------------------------------------- Loading Agents ---------------------------------------------------------")
    agents = agent_create(env, use_def_perc=True, vb=True)
    agents = dict(list(agents.items())[:])
    AGENTS = list(agents.values())
    HOSPITALIZED_AGENTS = []
    state_counts_over_days = {state.name: [] for state in Disease_State}
    state_counts_over_days_aggregated = {}

    print(f"------------------------------------- Assign Infectious Agents ---------------------------------------------------------")
    assign_initial_infection(env)
    """
    FIXME: 
    ------------------------------------- Assign Infectious Agents ---------------------------------------------------------
    Traceback (most recent call last):
    File "D:\Documents\COVID_Project\emulator\Scripts\vb_test.py", line 40, in <module>
        assign_initial_infection(env)
    File "D:\Documents\COVID_Project\emulator\Scripts\VBEngine.py", line 79, in assign_initial_infection
        random_agent = random.choice(agents)
    File "E:\Python\Python310\lib\random.py", line 378, in choice
        return seq[self._randbelow(len(seq))]
    IndexError: list index out of range
    """
    # visualize_patches(env)

    homes = env.get_zones("Home")
    
    for home in homes:
        patch = env.get_patch(home)
        sus_cnt = patch.get_susceptible_count()
        exp_cnt = patch.get_exposed_count()
        inf_cnt = patch.get_infected_count()

        print(f"{home}:\nSuspected:{sus_cnt}, Exposed:{exp_cnt}, Infected:{inf_cnt}")

        for i in range(100):
            patch.update_sus_cnt(env, 0.9)
            patch.update_exp_cnt(env, 0.9)
            patch.update_inf_cnt()

        sus_cnt = patch.get_susceptible_count()
        exp_cnt = patch.get_exposed_count()
        inf_cnt = patch.get_infected_count()

        print(f"Suspected:{sus_cnt}, Exposed:{exp_cnt}, Infected:{inf_cnt}\n")
