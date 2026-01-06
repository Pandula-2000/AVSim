import numpy as np
from DiseaseModels.PandemicModel import *
from DiseaseModels.VectorBorneModel import *
from Agents2 import Agents
from DataLoader import Loader
import random

state_timer_dict = Loader.get_state_timer_dict()


def STEP_DISEASE_PROPAGATION(agents,
                             q_agents,
                             env,
                             buses,
                             printer_object,
                             time,
                             freq=5,
                             bus_max_risk=0.2,
                             location_transmission_risk=0.1,
                             radius_of_infection=3,
                             use_transport=False):
    """
    1. Update agent disease states.
    2. Get contacts at each location.
    3. Get contacts in buses.

    :param agents                     : A list of total agents in the simulation
    :param q_agents                   : The list of quarantined agents
    :param env                        : The environment object
    :param buses                      : A list of buses in the simulation
    :param printer_object             : Prints contact data to xlsx file
    :param time                       : Time of simulation
    :param freq                       : Frequency of disease propagation
    :param bus_max_risk               : Maximum risk of transmission in buses
    :param location_transmission_risk : Risk of transmission at each location
    :param radius_of_infection        : Radius of infection
    :param use_transport              : Boolean value to determine if transport is considered for disease propagation.
    :return                           : None
    """
    # --------Run for every 5 minutes-----------
    if time % freq == 0:
        all_agents = agents + q_agents
        # 1. Update the disease state of each agent.
        UpdateAgentDiseaseState(all_agents, env, freq)

        # 2. Get contacts at each location.
        for Location in list(env.get_all_nodes()):
            agents = env.get_agents(Location)
            location_exposed_detector(agents,
                                      env,
                                      printer_object ,
                                      Location,
                                      state_timer_dict,
                                      location_transmission_risk,
                                      radius_of_infection)
        # 3. Get contacts in buses.
        if use_transport:
            for bus in buses:
                agents_in_bus = bus.get_agents()
                # 3.1 Only check if there are more than one agent in bus.
                if len(agents_in_bus) > 1:
                    bus_exposed_detector(agents_in_bus,
                                         env,
                                         printer_object,
                                         bus_max_risk)
    else:
        return None


def UpdateAgentDiseaseState(agents, env, frequency):
    """
    --- Updates the status and timers of each agent ---
    1. Steps the Markov model when necessary.
    2. Calculates the timers and decrements them with each time step.
    :param agents   : A list of total agents in the simulation
    :param env      : Environment object
    :param frequency: Frequency of disease progression, Used to decrement the state timer.
    :return         : None
    """
    for agent in agents:
        # curr = agent.get_current_location()
        curr_state = Agents.get_disease_state(agent)

        if curr_state == 1 or curr_state == 8 or curr_state == 9:
            # if the agent is in the susceptible, recovered or dead state disease progression should not continue.
            continue

        state_timer = agent.get_state_timer()
        next_state = agent.get_next_state()

        if state_timer <= 0:
            # Check if the agent has a 'next_state' stored
            if next_state is not None:
                # Transition to the stored 'next_state'
                # env.remove_agent_from_state(curr, curr_state, agent)
                agent.set_disease_state(env, agent.next_state)
                # env.add_agent_to_state(curr, agent.next_state, agent)

                # Clear 'next_state' after transition
                agent.set_next_state(None)

            else:
                # Determine the next state using the Markov model
                next_state = stepMarkovModel(agent)

                # Calculate the transition time to the next state
                Trans_time = getTransitionTimer(next_state, curr_state, state_timer_dict)

                # Store the 'next_state' in the agent
                agent.set_next_state(next_state)

                # Set the state timer for the agent to the transition time
                agent.set_state_timer(Trans_time)
                print(f"Agent {agent.get_agent_name()} is transitioning from {curr_state} to {next_state} | Transition time {Trans_time}")

        else:
            # Decrement the state timer by 5 minutes
            agent.decrement_state_timer(frequency)


def UpdateAgentDiseaseStateV2(agents, env, frequency):
    """
    # FIXME: This function is not used in the current implementation. DELETE LATER !!!
    --- Updates the status and timers of each agent ---
    1. Steps the Markov model when necessary.
    2. Calculates the timers and decrements them with each time step.
    :param agents   : A list of total agents in the simulation
    :param env      : Environment object
    :param frequency: Frequency of disease progression, Used to decrement the state timer.
    :return         : None
    """

    for agent in agents:
        curr = agent.get_current_location()
        curr_state = Agents.get_disease_state(agent)

        if curr_state == 1 or curr_state == 8 or curr_state == 9:
            # if the agent is in the susceptible, recovered or dead state disease progression should not continue.
            continue

        state_timer = Agents.get_state_timer(agent)

        if state_timer <= 0:
            # Check if the agent has a 'next_state' stored
            next_state = stepMarkovModel(agent)

            Agents.set_disease_state(agent, env, next_state)
            Trans_time = getTransitionTimer(next_state, curr_state, state_timer_dict)
            Agents.set_state_timer(agent, Trans_time)
        else:
            # Decrement the state timer by 5 minutes
            Agents.decrement_state_timer(agent, frequency)


def infectAgents(Agent_list,
                 Environment,
                 infect_random=True,
                 percentage_of_agents_to_infect=0.05,
                 agent_classes_to_infect=None):
    """
    Infects agents based on the given parameters (This function can infect agents randomly or based on their class).
    1. Infect random agents.
    2. Infect agents based on their class.
    :param Agent_list                       : A dictionary of agents.
    :param Environment                      : The environment object.
    :param infect_random                    : A boolean value to determine if agents should be infected randomly.
    :param percentage_of_agents_to_infect   : Infected percentage of agents.
    :param agent_classes_to_infect          : Which agent classes to infect as a list.
    :return                                 : A dictionary of agents and their disease states.
    """

    # Get the total number of agents
    total_agents = len(Agent_list)
    # IMPORTANT: Number of agents to infect is taken as a percentage of the total number of agents in both cases.
    num_agents_to_infect = int(percentage_of_agents_to_infect * total_agents)
    print(f"{num_agents_to_infect} agents will be infected out of {total_agents} agents")

    # 1. --------------- Randomly select agent keys to infect -----------------------------
    if infect_random:
        # 1.1 Set the disease state to 3: Infected for the selected agents
        infected_keys = random.sample(list(Agent_list.keys()), num_agents_to_infect)
        print(f"Randomly selected agents to infect: {infected_keys}")
        for key in infected_keys:
            Agent_list[key].set_disease_state(Environment, 3)

        # 1.2 Initialize the dictionary to hold the disease state of each agent
        agent_disease_state = {}
        for key, agent in Agent_list.items():
            if key not in agent_disease_state:  # Ensure the key exists in the dictionary
                agent_disease_state[key] = []  # Initialize an empty list
            agent_disease_state[key].append(agent.get_disease_state())  # Append the disease state to the list
        return agent_disease_state, infected_keys

    # 2. ---------------- Infect agents based on their class --------------------------------
    else:
        # 2.1 Infect agents based on class
        agent_keys_of_the_selected_class = []

        for key, agent in Agent_list.items():
            # print(agent.get_agent_class(), agent_classes_to_infect)
            if agent.get_agent_class() in agent_classes_to_infect:
                agent_keys_of_the_selected_class.append(key)

        print(agent_keys_of_the_selected_class)
        infected_keys = random.sample(agent_keys_of_the_selected_class, num_agents_to_infect)

        print(f"Randomly selected agents to infect: {infected_keys}")
        for key in infected_keys:
            print('infected', key)
            Agent_list[key].set_disease_state(Environment, 3)
        # 2.2 Initialize the dictionary to hold the disease state of each agent
        agent_disease_state = {}
        for key, agent in Agent_list.items():
            if key not in agent_disease_state:  # Ensure the key exists in the dictionary
                agent_disease_state[key] = []  # Initialize an empty list
            agent_disease_state[key].append(agent.get_disease_state())  # Append the disease state to the list
        return agent_disease_state, infected_keys
