import numpy as np
from disease_state_enum import Disease_State
# from Parameters.VB_params import *
import Parameters.VB_params as VB_params
import json

hospitalization_probabilities = {
    Disease_State.MILD.value: 0.4,
    Disease_State.SEVERE.value: 0.9
}

def InterventionEngine(day, agents: list,
                       hospitalized_agents: list,
                       removed_agents: list,
                       environment,
                       all_state_counts_over_days,
                       hospitalized_state_counts_over_days,
                       controlled):
    """
    Checks Interventions.
    Purpose : Set the flags, move agents between AGENTS, HOSPITALIZED_AGENTS, REMOVED_AGENTS lists.
    # IMPORTANT: This is to be run only once a day (Beginning of the day).
    --- Steps ---
    1. Check for Mild and Severe patients.
    2. Hospitalization is done if the patient is infected.
    :param agents            : Non hospitalized agents list.
    :param hospitalized_agents : Hospitalized agents list.
    :param environment       : Environment object.
    :param AgentClass        : Agent class.
    :param ClockClass        : Clock class.
    :param DataLoader        : Loader class.
    :return                  : AGENTS, HOSPITALIZED_AGENTS lists.
    """
    new_agents_list = []
    disease_state_count_all = {state.name: 0 for state in Disease_State}
    disease_state_count_hospitalized = {state.name: 0 for state in Disease_State}
    
    for agent in agents:  
        
        # Remove recovered and dead agents from simulation
        if agent.disease_state == Disease_State.Recovered.value or agent.disease_state == Disease_State.Dead.value:
            agent.remove_from_environment_VB(environment, agent._current_location)
            removed_agents.append(agent)
            continue
        
        # Check for hospitalization  
        hospitalization_prob = hospitalization_probabilities.get(agent.disease_state, 0)
        if np.random.random() < hospitalization_prob:
            agent.set_hospitalized(True)
            hospitalized_agents.append(agent)
            agent.remove_from_environment_VB(environment, agent._current_location)
        else:
            new_agents_list.append(agent)
            disease_state_count_all[Disease_State(agent.disease_state).name] += 1   

                
    for agent in removed_agents:
        disease_state_count_all[Disease_State(agent.disease_state).name] += 1   
          
    for agent in hospitalized_agents:
        disease_state_count_hospitalized[Disease_State(agent.disease_state).name] += 1
        
        # NOTE: Don't add recovered agents back to the environment/patch
        # if agent.disease_state == Disease_State.Recovered.value and agent.hospitalized: 
        #         agent.set_hospitalized(False)
        #         new_agents_list.append(agent)
        #         agent.add_to_environment_VB(environment, agent._current_location)
        # else:
        #     new_h_agents_list.append(agent)
            
    for state_name, count in disease_state_count_all.items():
        all_state_counts_over_days[state_name].append(count)
        
    for state_name, count in disease_state_count_hospitalized.items():
        hospitalized_state_counts_over_days[state_name].append(count)
        
    if controlled and day % 30 == 0:
        control_vectors(environment, day)
            
    # print(f"All Agents:     {disease_state_count_all}")
    # print(f"Hospitalized:   {disease_state_count_h}")
    return new_agents_list, hospitalized_agents, removed_agents

def control_vectors(env, day):
    all_nodes = env.get_all_nodes()
    zones = [node for node in all_nodes if "Zone" in node]
    
    for zone_name in zones:
        exposed_count = 0
        zone = env.graph.nodes[zone_name]['node']
        rows, columns = len(zone.patch_grid), len(zone.patch_grid[0])
        for i in range(rows):
            for j in range(columns):
                if zone.patch_grid[i][j] is not None:
                    exposed_count += zone.patch_grid[i][j].exposed_agents 
        
        if exposed_count >= VB_params.MAX_EXPOSED_AGENTS:
            print(f'Day {day} - Exposed {exposed_count} agents, controlled in zone {zone}')
            
        for i in range(rows):
            for j in range(columns):
                if zone.patch_grid[i][j] is not None:
                    if exposed_count >= VB_params.MAX_EXPOSED_AGENTS:
                        zone.patch_grid[i][j].control_vectors(VB_params.VECTOR_CONTROLLING_RATE)   
                    else:
                        zone.patch_grid[i][j].reset_exposed_agents()      
                    
    
if __name__ == '__main__':
    pass