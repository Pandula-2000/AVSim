## Imports

import numpy as np

from Environment import *
from Agents2 import *
from disease_state_enum import Disease_State
from Parameters.VB_params import *

class Patch:
    _id = 0
    
    def __init__(self, env_node: str, grid_ind: tuple, cell_box, grid_init: tuple, sus_cnt: int, exp_cnt: int, inf_cnt: int, temp: int):

        type(self)._id += 1
        self._id = type(self)._id
        
        self._env_node = env_node
        
        self._grid_index = grid_ind
        self._cell_box = cell_box
        self._coordinates = ((grid_ind[0] + 1) * grid_init[0], (grid_ind[1] + 1) * grid_init[1])
        self.locations = []     # locations that are inside the patch
        self.zone_agents = []   # agents that are in the zone and patch
        
        self.agent_states_count = {1:0, 2:0, 3:0, 4:0, 5:0, 6:0, 7:0, 8:0, 9:0, 10:0}
        
        self.exposed_agents = 0 # Total agent count of dengue exposure from patch
        
        self._susceptible_count = sus_cnt
        self._exposed_count = exp_cnt
        self._infected_count = inf_cnt
        self._temperature = temp

        self.BITING_CAPACITY = 3e-1 # Number of times one mosquito would want to bite a host per unit time
        self.BITE_TOLERANCE = 1e-1 # Number of mosquito bites an average host can sustain per unit time.
        # self.mosquito2host_TRANSMISSION_PROBABILITY = 0.1
        # self.host2mosquito_TRANSMISSION_PROBABILITY = 0.1
        
        # FIXME: The following parameters taken as constants
        # Change the according to their affecting  factors
        # self.mosquito_DEATH_RATE = 0.01 # FIXME: can change according to temparature and season
        self.mosquito_INFECTION_RATE = 3.5e-4 # rate of exposed state to the infectious state, FIXME: Not a constant??
        # NOTE: Rates given in a per day basis?

        self.time_step = 1
    
    def add_agent(self, agent, nodeName):
        if "Zone" in nodeName:
            self.zone_agents.append(agent)
            
        # Update host disease state count
        self.agent_states_count[agent.disease_state] += 1
    
    def remove_agent(self, agent, nodeName):
        if "Zone" in nodeName:
            self.zone_agents.remove(agent)
            
        # Update host disease state count
        self.agent_states_count[agent.disease_state] -= 1
    
    
    def get_mosquito2host_TRANSMISSION_PROBABILITY(self, DAY):
        return MOSQUITO2HOST_TRANSMISSION_PROBABILITIES[DAY // 30]
    
    
    def get_host2mosquito_TRANSMISSION_PROBABILITY(self, DAY):
        return HOST2MOSQUITO_TRANSMISSION_PROBABILITIES[DAY // 30]
    
    @property
    def _total_count(self):
        return  self._susceptible_count + self._exposed_count + self._infected_count
    
    @property
    def _infected_host_count(self):
        return  (self.agent_states_count.get(Disease_State.Infectious.value, 0) + 
                 self.agent_states_count.get(Disease_State.MILD.value, 0) +
                 self.agent_states_count.get(Disease_State.SEVERE.value, 0) +
                 self.agent_states_count.get(Disease_State.Asymptotic.value, 0)
        )
    
    @property
    def host_count (self):
        return  sum(self.agent_states_count.values())
    
    def set_susceptible_count(self, count): #NOTE: Convert to mosq_susceptible_count??
        self._susceptible_count = count
    
    def set_exposed_count(self, count):
        self._exposed_count = count
    
    def set_infected_count(self, count):
        self._infected_count = count
    
    def get_susceptible_count(self):
        return self._susceptible_count
    
    def get_exposed_count(self):
        return self._exposed_count
    
    def get_infected_count(self):
        return self._infected_count
    
    def add_location(self, location):
        self.locations.append(location)
        
    def update_exposure_count(self, env):
        self.exposed_agents += 1
        
        n_name = self._env_node
        p_zone = env.graph.nodes[n_name]['node']
        rows, columns = len(p_zone.patch_grid), len(p_zone.patch_grid[0])
        exposed_count = 0
        for i in range(rows):
            for j in range(columns):
                if p_zone.patch_grid[i][j] is not None:
                    exposed_count += p_zone.patch_grid[i][j].exposed_agents
        
        print(f"{p_zone} total exposed agents: {exposed_count}")
    
    def reset_exposed_agents(self):
        self.exposed_agents = 0
        
    def control_vectors(self, controlling_rate):
        print(f"Before control: {self._susceptible_count}, {self._exposed_count}, {self._infected_count}")
        self._susceptible_count = (self._susceptible_count * (1-controlling_rate)) if (self._susceptible_count * (1-controlling_rate)) >= 1 else 0
        self._exposed_count = (self._exposed_count * (1-controlling_rate)) if (self._exposed_count * (1-controlling_rate)) >= 1 else 0
        self._infected_count = (self._infected_count * (1-controlling_rate)) if (self._infected_count * (1-controlling_rate)) >= 1 else 0
        print(f"After control: {self._susceptible_count}, {self._exposed_count}, {self._infected_count}")

    def get_mosq_birth_rate(self, DAY):
        mosquito_emergence_rate = MOSQUITO_EMERGENCE_RATES[DAY // 30]
        mosquito_carrying_capacity = VECTOR_CARRYING_CAPACITIES[DAY // 30]
        mosquito_death_rate = MOSQUITO_DEATH_RATES[DAY // 30]
        pop_growth = mosquito_emergence_rate - mosquito_death_rate
        birth_rate = self._total_count * (mosquito_emergence_rate - (pop_growth * self._total_count / mosquito_carrying_capacity))
        return birth_rate

    def get_bite_rate(self, risk): # NOTE: div_by_zero error occurs
        Nhosts = self.host_count
        # print(f"Number of hosts: {Nhosts}") # Testing
        try:
            bite_rate = (self.BITING_CAPACITY * self._total_count * self.BITE_TOLERANCE * Nhosts)/(self.BITING_CAPACITY * self._total_count + self.BITE_TOLERANCE * Nhosts)
        except ZeroDivisionError:
            # print(f"ZeroDivisionError: Nhosts: {Nhosts}, total_count: {self._total_count}")
            bite_rate = 0
        return risk * bite_rate

    def get_mosq_bite_cnt(self, risk): # NOTE: div_by_zero error occurs
        try:
            return self.get_bite_rate(risk) / self._total_count
        except ZeroDivisionError:
            # print(f"ZeroDivisionError: total_count: {self._total_count}")
            return 0

    def get_host_bite_cnt(self, risk): # NOTE: div_by_zero error occurs
        try:
            return self.get_bite_rate(risk) / self.host_count
        except ZeroDivisionError:
            # print(f"ZeroDivisionError: host_count: {self.ost_count}")
            return 0

    def get_host_exposure_rate(self, risk, DAY): # NOTE: div_by_zero error occurs
        try:
            exposure_rate = self.get_host_bite_cnt(risk) * self.get_mosquito2host_TRANSMISSION_PROBABILITY(DAY) * (self._infected_count / self._total_count)
        except ZeroDivisionError:
            # print(f"ZeroDivisionError: total_count: {self._total_count}")
            exposure_rate = 0
        return exposure_rate
    
    def get_mosq_exposure_rate(self, risk, DAY): # NOTE: div_by_zero error occurs
        try:
            mosq_exp_rate = self.get_mosq_bite_cnt(risk) * self.get_host2mosquito_TRANSMISSION_PROBABILITY(DAY) * (self._infected_host_count / self.host_count)
        except ZeroDivisionError:
            # print(f"ZeroDivisionError: host_count: {self.host_count}")
            mosq_exp_rate = 0
        return mosq_exp_rate

    def get_mosq_infection_rate(self): # Rate of patches to progress from exposed to infectious state
        temp = self._temperature
        
        if (temp < 18):
            infection_rate = 0
        else:
            if (temp >= 18 and temp < 21):
                # incub_time = 1 / (25 - 10)
                incub_time = np.random.uniform(10, 25)
            elif (temp >= 21 and temp < 26):
                # incub_time = 1 / (10 - 7)
                incub_time = np.random.uniform(7, 10)
            elif (temp >= 26 and temp < 31):
                # incub_time = 1 / (7 - 4)
                incub_time = np.random.uniform(4, 7)
            else:
                incub_time = 1000 # FIXME: What to do at high temperatures (not given in doc)
            
            infection_rate = 1 / (incub_time * 24) # FIXME: rate is set per hour temporarily
        
        return infection_rate

    # Diff.Equation (1)
    def dSdt(self, S, env, risk, DAY):
        mosquito_death_rate = MOSQUITO_DEATH_RATES[DAY // 30]
        sus_rate = self.get_mosq_birth_rate(DAY) - self.get_mosq_exposure_rate(risk, DAY) * S - mosquito_death_rate * S
        return sus_rate
    
    # Diff.Equation (2)
    def dEdt(self, E, env, risk, DAY):
        mosquito_death_rate = MOSQUITO_DEATH_RATES[DAY // 30]
        # exp_rate = self.get_mosq_exposure_rate(env, risk) * self.get_susceptible_count() - self.mosquito_INFECTION_RATE * E -  self.mosquito_DEATH_RATE * E
        exp_rate = self.get_mosq_exposure_rate(risk, DAY) * self.get_susceptible_count() - self.get_mosq_infection_rate() * E -  mosquito_death_rate * E
        return exp_rate
    
    # Diff.Equation (3)
    def dIdt(self, I, DAY):
        mosquito_death_rate = MOSQUITO_DEATH_RATES[DAY // 30]
        # inf_rate = self.mosquito_INFECTION_RATE * self.get_exposed_count() - self.mosquito_DEATH_RATE * I
        inf_rate = self.get_mosq_infection_rate() * self.get_exposed_count() - mosquito_death_rate * I
        return inf_rate

    def update_sus_cnt(self, env, risk, DAY):
        sus_cnt = self.get_susceptible_count()
        dt = self.time_step
        # sus_cnt_new = self.rk4(self.dSdt, sus_cnt, dt, env=env, risk=risk)
        sus_cnt_new = sus_cnt + self.dSdt(sus_cnt, env, risk, DAY) * dt
        # if sus_cnt_new < 1: sus_cnt_new = 0
        self.set_susceptible_count(sus_cnt_new)

    def update_exp_cnt(self, env, risk, DAY):
        exp_cnt = self.get_exposed_count()
        dt = self.time_step
        # exp_cnt_new = self.rk4(self.dEdt, exp_cnt, dt, env=env, risk=risk)
        exp_cnt_new = exp_cnt + self.dEdt(exp_cnt, env, risk, DAY) * dt
        # if exp_cnt_new < 1: exp_cnt_new = 0
        self.set_exposed_count(exp_cnt_new)

    def update_inf_cnt(self, DAY):
        inf_cnt = self.get_infected_count()
        dt = self.time_step
        # inf_cnt_new = self.rk4(self.dIdt, inf_cnt, dt)
        inf_cnt_new = inf_cnt + self.dIdt(inf_cnt, DAY) * dt
        # if inf_cnt_new < 1: inf_cnt_new = 0
        self.set_infected_count(inf_cnt_new)
    
    # General RK4 method
    def rk4(self, func, y, dt, **kwargs):
        k1 = func(y, **kwargs)
        k2 = func(y + 0.5 * k1 * dt, **kwargs)
        k3 = func(y + 0.5 * k2 * dt, **kwargs)
        k4 = func(y + k3 * dt, **kwargs)
        return y + (dt / 6) * (k1 + 2 * k2 + 2 * k3 + k4)            

def get_patch_for_location(env, location_name):
    location = env.graph.nodes[location_name]['node']
    return location.patch_idx

def get_probability_from_rate(rate, deltaT):
    return 1 - np.exp(-1 * rate * deltaT)

def update_locations_and_patch(env, zone_name):
    zone = env.graph.nodes[zone_name]['node']
    rows, columns = len(zone.patch_grid), len(zone.patch_grid[0])
    minx, miny, maxx, maxy = zone.boundary.bounds
 
    cell_width = (maxx - minx) / columns
    cell_height = (maxy - miny) / rows
   
    children = list(env.graph.successors(zone_name))
    for child in children:
        location = env.graph.nodes[child]['node']
        point = location.centroid
        col = int((point.x - minx) // cell_width)
        row = int((point.y - miny) // cell_height)
        location.patch_idx = (row, col)
        zone.patch_grid[row][col].add_location(child)
        location.patch = zone.patch_grid[row][col]      
