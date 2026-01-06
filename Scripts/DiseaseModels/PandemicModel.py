import numpy as np
from Environment import *
from Agents2 import *


# -------------------------------------------- UPDATE AGENT ---------------------------------------------------------

def stepMarkovModel(agent):
    """
    Step the Markov model for the agent.
    :param agent: The agent object.
    :return: None
    """
    current_state = agent.get_disease_state()
    current_state_vector = np.zeros(8)
    current_state_vector[current_state - 2] = 1

    A = np.array([[0, 1.0, 0, 0, 0, 0, 0, 0],
                  [0, 0, 0.7, 0, 0, 0.3, 0, 0],
                  [0, 0, 0, 0.1, 0, 0, 0.9, 0],
                  [0, 0, 0, 0, 0.3, 0, 0.7, 0],
                  [0, 0, 0, 0, 0, 0, 0.5, 0.5],
                  [0, 0, 0, 0, 0, 0, 0.95, 0.05],
                  [0, 0, 0, 0, 0, 0, 1.0, 0],
                  [0, 0, 0, 0, 0, 0, 0, 1.0]])

    out = np.matmul(current_state_vector, A)
    next_state = np.random.choice(range(2, 10), p=out)

    return next_state


def getTransitionTimer(curr: int, prev: int, state_timer_dict: dict):
    # Get the mean and variance from the dictionary
    key = (prev, curr)
    min = 24 * 60

    if key in state_timer_dict:
        mean, variance = state_timer_dict[key]

        mean = round_to_nearest_5(mean * min)
        variance = round_to_nearest_5(variance * min)

        if variance == 0:  # Handle case where variance is 0
            return np.exp(mean)  # Return the mean of the log-normal distribution

        # Calculate mu and sigma for the log-normal distribution
        sigma = np.sqrt(np.log(1 + (variance / (mean ** 2))))
        mu = np.log(mean) - (sigma ** 2 / 2)

        # Generate and return a random value from the log-normal distribution
        return np.random.lognormal(mu, sigma)

        # return np.random.lognormal(mean, variance)

    else:
        raise ValueError("Invalid state transition. No such key in the dictionary.")


def round_to_nearest_5(n):
    return 5 * round(n / 5)


# ------------------------------------------ Contact Finding ----------------------------------------------------------

def location_exposed_detector(agents_list, env, printer, location, state_timer_dic, risk, radius):
    """
    Gets the agents in a location and calls the appropriate exposed_detector function.
    1. Determines the number of agents that are transmitting the disease.
    2. Calls the appropriate exposed_detector function based to save time.
    :param agents_list:
    :param env:
    :param printer:
    :param location:
    :param risk:
    :param radius:
    :return:
    """

    # 1. Determines the number of agents that are transmitting the disease, and not transmitting the disease.
    transmission_count = 0
    non_transmission_count = 0

    for state in range(1, 10):  # 1 to 9 states
        if state == 3 or state == 4 or state == 5 or state == 6:
            transmission_count += env.get_agent_count_for_state(location, state)
        else:
            non_transmission_count += env.get_agent_count_for_state(location, state)

    # transmission_count = len(status_dict[3]) + len(status_dict[4]) + len(status_dict[5]) + len(status_dict[6])
    # non_transmission_count = len(status_dict[1]) + len(status_dict[2]) + len(status_dict[7]) + len(status_dict[8]) + len(status_dict[9])

    # 2. Calls the appropriate exposed_detector function based to save time.
    if transmission_count <= non_transmission_count:
        exposed_detector_min_transmitters(agents_list, env, printer, location, state_timer_dic, risk, radius)
    else:
        exposed_detector_max_transmitters(agents_list, env, printer, location, state_timer_dic, risk, radius)
    # if fraction_agents_transmit (agents_list) <= 0.5: exposed_detector_min_transmitters(agents_list, status_dict)
    # else : exposed_detector_max_transmitters(agents_list, status_dict)


def exposed_detector_min_transmitters(agents_list, env, printer_object, location, state_timer_dict, risk, radius):
    # risk = 0.10
    # radius = 3
    for agent in agents_list:
        if is_agent_transmit(agent):
            # print(Agents.get_agent_name(agent))
            other_agents_list = [a for a in agents_list if a != agent]
            for other_agent in other_agents_list:
                if is_agent_transmit(other_agent):
                    continue
                state_other = other_agent.get_disease_state()
                # FIXME: Skip Incubating, Recovered ???, Dead agents ???.
                if state_other == 2 or state_other == 7 or state_other == 8 or state_other == 9: continue
                # FIXME: Check if the below condition is correct.. can be simplified...
                if (agent.x == other_agent.x or abs(agent.x - other_agent.x) <= radius) and (
                        agent.y == other_agent.y or abs(agent.y - other_agent.y) <= radius):
                    # print(f"new CONTACT HERE-------------------------")
                    rdn = np.random.random(1)[0]
                    # print(rdn, other_agent.infection_probability_AirBorne)
                    if rdn<= other_agent.infection_probability_AirBorne:  # This is the probability of transmission
                        print(f"INFECTED: {other_agent.get_agent_name()} from {agent.get_agent_name()}") # New infected

                        # status_dict['1'].remove(other_agents.agent_name)      
                        # status_dict['2'].append(other_agents.agent_name)
                        other_agent.set_disease_state(env, 2)
                        # prev_state = other_agent.get_disease_state()  # Should be 2 always
                        # print(f"Prev state: {prev_state}")
                        # next_state = 3

                        # transition_time = getTransitionTimer(next_state, prev_state, state_timer_dict)
                        # other_agent.set_next_state(next_state)
                        # other_agent.set_state_timer(transition_time)

                        # env.add_agent_to_state(location, 2, other_agent)
                        # env.remove_agent_from_state(location, 1, other_agent)

                        # IMPORTANT: Write to excel here.
                        info_list = [printer_object.day,
                                     printer_object.time,
                                     other_agent.get_agent_name(),
                                     agent.get_agent_name(),
                                     location,
                                     str(env.get_centroid(location)),
                                     other_agent.get_disease_state(),
                                     agent.get_disease_state(),
                                     str((other_agent.x, other_agent.y)),
                                     str((agent.x, agent.y))
                                     ]
                        printer_object.write_lines(info_list)

                        # other_agent.set_disease_state(env, 2)

                        # print(f"The {Agents.get_agent_name(other_agent)} have changed from {prev_state} to {Agents.get_disease_state(other_agent)}")

    # health_v = [agent.get_disease_state() for agent in agents_list]
    # print("All agents' health_v:", health_v)


def exposed_detector_max_transmitters(agents_list, env, printer_object, location, state_timer_dict, risk, radius):
    """
    Detects the agents that are transmitting the disease in a location.
    :param agents_list:
    :param env:
    :param printer_object:
    :param location:
    :param risk:
    :param radius:
    :return:
    """
    # risk = 0.1
    # radius = 3
    for agent in agents_list:
        if not is_agent_transmit(agent):
            state = agent.get_disease_state()
            if state == 2 or state == 7 or state == 8 or state == 9:
                continue
            # print(Agents.get_agent_name(agent))
            other_agents_list = [a for a in agents_list if a != agent]
            for other_agent in other_agents_list:
                if not is_agent_transmit(other_agent):
                    continue
                # state = Agents.get_disease_state(agent)
                # if state_other == 2 or state_other == 7 or state_other == 8 or state_other == 9: continue
                # do we need to add the obove code's line? after adding the brake in the bellow line????
                if (agent.x == other_agent.x or abs(agent.x - other_agent.x) <= radius) and (
                        agent.y == other_agent.y or abs(agent.y - other_agent.y) <= radius):
                    # print(f"new CONTACT HERE-------------------------")
                    rdn = np.random.random(1)[0]
                    # print(rdn, other_agent.infection_probability_AirBorne)
                    if rdn<= agent.infection_probability_AirBorne:
                        print(f"INFECTED: {agent.get_agent_name()} from {other_agent.get_agent_name()}")  # New infected
                        # print('DONE 2')
                        # print this
                        agent.set_disease_state(env, 2)
                        # prev_state = agent.get_disease_state()  # Should be 2 always
                        # next_state = 3

                        # print(f"Prev state: {prev_state}")

                        # transition_time = getTransitionTimer(next_state, prev_state, state_timer_dict)
                        # agent.set_next_state(next_state)
                        # agent.set_state_timer(transition_time)

                        # prev_state = agent.get_disease_state()
                        # IMPORTANT: Write to excel here.
                        info_list = [printer_object.day,
                                     printer_object.time,
                                     agent.get_agent_name(),
                                     other_agent.get_agent_name(),
                                     location,
                                     str(env.get_centroid(location)),
                                     agent.get_disease_state(),
                                     other_agent.get_disease_state(),
                                     str((agent.x, agent.y)),
                                     str((other_agent.x, other_agent.y))
                                     ]
                        printer_object.write_lines(info_list)

                        # env.add_agent_to_state(location, 2, agent)
                        # env.remove_agent_from_state(location, 1, agent)
                        # status_dict['1'].remove(agent.agent_name)      
                        # status_dict['2'].append(agent.agent_name) 
                        # agent.disease_state = 2

                        # agent.set_disease_state(env, 2)

                        # print(f"The {Agents.get_agent_name(agent)} have changed from {prev_state} to {Agents.get_disease_state(agent)}")

                        break

    # health_v = [agent.get_disease_state() for agent in agents_list]
    # # print("All agents' health_v:", health_v)


def bus_exposed_detector(Agents, Environment, printer_object, max_risk):
    """
    Detects the agents that are transmitting the disease in a bus.
    :param Agents           : List of agents in the bus.
    :param Environment      : Environment object.
    :param printer_object   : Writes contacts to xlsx file.
    :param max_risk         : Maximum risk of transmission.
    :return                 : None.
    """
    transmitting_agents = 0

    for agent in Agents:
        if agent.can_agent_transmit():
            transmitting_agents += 1

    for agent in Agents:
        if agent.get_disease_state() == 1:
            p = agent.transport_infection_probability_AirBorne * (1 - np.exp(-0.6 * transmitting_agents))
            randomNum = np.random.random()
            if randomNum <= p:
                agent.set_disease_state(Environment, 2)
                # IMPORTANT: Write to excel here.
                info_list = [printer_object.day,
                             printer_object.time,
                             agent.get_agent_name(),
                             f'Transmitting Agents: {transmitting_agents}',
                             'In Bus',
                             'None',
                             'None',
                             'None',
                             'None',
                             randomNum,
                             p
                             ]
                printer_object.write_lines(info_list)


def is_agent_transmit(agent):
    # FIXME: Put this inside Agents class.
    state = agent.get_disease_state()
    if state in (3, 4, 5, 6):
        return True
    else:
        return False


if __name__ == '__main__':
    import numpy as np

    state_timer_dict = {
        (2, 3): (4.5, 1.5),
        (3, 4): (1.1, 0.9),
        (3, 7): (0, 0),
        (4, 5): (6.6, 4.9),
        (4, 8): (8.0, 2.0),
        (5, 8): (18.1, 6.3),
        (5, 6): (1.5, 2.0),
        (6, 8): (18.1, 6.3),
        (6, 9): (10.7, 4.8),
        (7, 8): (8.0, 2.0),
        (7, 9): (8.0, 2.0)
    }

    # mean = 4.5
    # variance = 1.5

    # print(getTransitionTimer(9,6, state_timer_dict)/(24*60))
    # print(np.random.lognormal(mean, variance))
