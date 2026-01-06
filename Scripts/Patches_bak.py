## Imports

import numpy as np

from Environment import *
from Agents import *


class Patch:

    def __init__(self, env_node: str, grid_ind: tuple, cell_box, grid_init: tuple, sus_cnt: int, exp_cnt: int, inf_cnt: int, temp: int):

        self._env_node = env_node
        
        self._grid_index = grid_ind
        self._cell_box = cell_box
        self._coordinates = ((grid_ind[0] + 1) * grid_init[0], (grid_ind[1] + 1) * grid_init[1])
        self.locations = []
        
        self.host_count = 0
        self._susceptible_count = sus_cnt
        self._exposed_count = exp_cnt
        self._infected_count = inf_cnt
        self._temperature = temp

        self._total_count = sus_cnt + exp_cnt + inf_cnt

        self.carrying_capacity  = 100 #FIXME: Set a constant temporarily
        self.BITING_CAPACITY = 0.3 # Number of times one mosquito would want to bite a host per unit time
        self.BITE_TOLERANCE = 0.2 # Number of mosquito bites an average host can sustain per unit time.
        self.mosquito2host_TRANSMISSION_PROBABILITY = 0.1
        self.host2mosquito_TRANSMISSION_PROBABILITY = 0.1
        
        # FIXME: The following parameters taken as constants
        # Change the according to thier affecting  factors
        self.mosquito_EMERGENCE_RATE = 0.5 # FIXME: can change according to temparature and season
        self.mosquito_DEATH_RATE = 0.5 # FIXME: can change according to temparature and season
        self.mosquito_PROGRESSION_RATE = 0.5 # rate of exposed state to the infectious state, FIXME: Not a constant??
        # NOTE: Rates given in a per day basis?

    def get_host_count(self, env):
        count = 0
        for location_name in self.locations:
            location = env.graph.nodes[location_name]['node']
            count += location.risk * len(location.agents)

    # Equation (3)
    def get_bite_rate(self, env, risk):
        Nhosts = self.get_host_count(env)
        bite_rate = (self.BITING_CAPACITY * self._total_count * self.BITE_TOLERANCE * Nhosts)/(self.BITING_CAPACITY * self._total_count + self.BITE_TOLERANCE * Nhosts)
        return risk * bite_rate
    
    def add_location(self, location):
        self.locations.append(location)

    def get_birth_rate(self):
        pop_growth = self.mosquito_EMERGENCE_RATE - self.mosquito_DEATH_RATE
        birth_rate = self._total_count * (self.mosquito_EMERGENCE_RATE - (pop_growth * self._total_count / self.carrying_capacity))
        return birth_rate

    def get_progression_rate(self): # Rate of patches to progress from exposed to infectious state
        #NOTE: Not necessary for now as progression rate is set as a constant
        temp = self._temperature
        
        if (temp<18):
            progression_rate = 0
        else:
            if (temp>=18 and temp<21):
                incub_time = 1 / (25 - 10)
            elif (temp>=21 and temp<26):
                incub_time = 1 / (10 - 7)
            elif (temp>=26 and temp<31):
                incub_time = 1 / (7 - 4)
            else:
                incub_time = 1 # FIXME: What to do at high temperatures (not given in doc)
            
            progression_rate = 1 / incub_time
        
        return progression_rate
    
    # Equation (5)
    def get_infection_rate(self): # NOTE: infection rate of humans?
        infection_rate = self.get_bite_rate() * self.mosquito2host_TRANSMISSION_PROBABILITY * (self._infected_count / self._total_count)
        # FIXME: Shouldn't bite rate be replaced by number of bites a human receives per unit time (bite rate divided by no of humans)
        return infection_rate
    
    def get_mosq_bite_cnt(self, env, risk):
        return self.get_bite_rate(env, risk) / self._total_count
    
    def get_mosq_infection_rate(self, env, risk): # Rate of progression from suspected to exposed for mosquitos
        inf_hum_cnt = 0 # FIXME: Need function to get number of infected humans in a patch
        mosq_inf_rate = self.get_mosq_bite_cnt(env, risk) * self.host2mosquito_TRANSMISSION_PROBABILITY * (inf_hum_cnt / self.get_host_count())
        return mosq_inf_rate

    # Diff.Equation (1)
    def dSdt(self, env, risk): # NOTE: Using the correct infectious rate? (infectious rate is the rate from susceptible to exposed for mosquitoes)
        sus_rate = self.get_birth_rate() - self.get_mosq_infection_rate(env, risk) * self._susceptible_count - self.mosquito_DEATH_RATE * self._susceptible_count
        return sus_rate
    
    # Diff.Equation (2)
    def dEdt(self): # NOTE: Using the correct infectious rate? (infectious rate is the rate from susceptible to exposed for mosquitoes)
        exp_rate = self.mosquito_INFECTIOUS_RATE * self._susceptible_count - self.get_progression_rate() * self._exposed_count -  self.mosquito_DEATH_RATE * self._exposed_count
        return exp_rate
    
    # Diff.Equation (3)
    def dIdt(self):
        inf_rate = self.get_progression_rate() * self._exposed_count - self.mosquito_DEATH_RATE * self._infected_count
        return inf_rate

    # # Diff.Equation (1)
    # def update_suspected_cnt(self): # NOTE: Using the correct infectious rate? (infectious rate is the rate from susceptible to exposed for mosquitoes)
    #     dSdt = self.get_birth_rate() - self.get_mosq_infection_rate() * self._susceptible_count - self.mosquito_DEATH_RATE * self._susceptible_count
    
    # # Diff.Equation (2)
    # def update_exposed_cnt(self): # NOTE: Using the correct infectious rate? (infectious rate is the rate from susceptible to exposed for mosquitoes)
    #     dEdt = self.mosquito_INFECTIOUS_RATE * self._susceptible_count - self.get_progression_rate() * self._exposed_count -  self.mosquito_DEATH_RATE * self._exposed_count
    
    # # Diff.Equation (3)
    # def update_infected_cnt(self):
    #     dIdt = self.get_progression_rate() * self._exposed_count - self.mosquito_DEATH_RATE * self._infected_count
    
    # General RK4 method
    def rk4(self, func, y, dt, env, risk):
        k1 = func(env, risk)
        k2 = func(env, risk) + 0.5 * k1 * dt
        k3 = func(env, risk) + 0.5 * k2 * dt
        k4 = func(env, risk) + k3 * dt
        return y + (dt / 6) * (k1 + 2 * k2 + 2 * k3 + k4)
    

def get_patch_for_location(env, location_name):
    location = env.graph.nodes[location_name]['node']
    return location.patch_idx

def get_probability_from_rate(probability, deltaT):
    return 1 - np.exp(-1 * probability * deltaT)

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