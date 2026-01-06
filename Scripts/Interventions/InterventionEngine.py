import numpy as np


def InterventionEngine(agents: list,
                       quarantine_agents: list,
                       environment_object,
                       vaccinate,
                       quarantine,
                       quarantine_by_pcr,
                       quarantine_by_class,
                       infected_by_class_dict,
                       AgentClass,
                       ClockClass,
                       DataLoader):
    """
    Checks Interventions.
    Purpose : Set the flags, move agents between AGENTS and QUARANTINED_AGENTS lists.
    # IMPORTANT: This is to be run only once a day (Beginning of the day).
    --- Steps ---
    1. Check for Outbreak.
    2. Vaccines are given after an outbreak is identified.
    3. Quarantine is done from start of the Simulation if PSR is positive.



    :param agents            : Non Quarantined agents list.
    :param quarantine_agents : Quarantined agents list.
    :param environment_object: Environment object.
    :param vaccinate         : Whether to vaccinate or not.
    :param quarantine        : Whether to quarantine or not.
    :param quarantine_by_pcr:
    :param quarantine_by_class:
    :param infected_by_class_dict:
    :param AgentClass        : Agent class.
    :param ClockClass        : Clock class.
    :param DataLoader        : Loader class.
    :return                  : AGENTS, QUARANTINED_AGENTS lists.
    """
    vaccine_data = DataLoader.vaccine_data_dict
    simDay = ClockClass.get_DAY()

    # 1. Check for Outbreak.
    OUTBREAK_checker(agents, AgentClass, simDay, DataLoader)
    OUTBREAK = DataLoader.get_AirBorneOutbreak()

    # 2. Vaccines are given after an outbreak is identified.
    if OUTBREAK and vaccinate:
        # print("--------- OUTBREAK is identified at day Vaccination Will be done: ", simDay)
        VACCINE_checker(agents,simDay, vaccine_data, environment_object, DataLoader)
    # 3. Quarantine is done from start of the Simulation if PCR is positive.
    if quarantine:
        agents, quarantine_agents = DAILY_PCRandQUARANTINE_checker(environment_object,
                                                                   agents,
                                                                   quarantine_agents,
                                                                   infected_by_class_dict,
                                                                   quarantine_by_pcr,
                                                                   quarantine_by_class
                                                                   )

    return agents, quarantine_agents


def VACCINE_checker(agent_list: list, simulation_day, data_dict: dict, environment, DataLoader):
    """
    Give Out Vaccines if an outbreak is identified.
    # 1. Check if it is the correct day to give vaccines.
    # 2. Get the vaccine data.
    # 3. Give out vaccines based on vaccination types ("Profession_location", "All").
    :param agent_list       : List of agents.
    :param simulation_day   : Simulation Day.
    :param data_dict        : Vaccine data dictionary.
    :param environment      : Environment object.
    :param DataLoader       : Loader class.
    :return                 : None
    """
    outbreak_day = DataLoader.get_AirBorneOutbreakDay()
    # Error handling.
    if simulation_day < outbreak_day:
        print("Error: Vaccines are not given before outbreak day.")

    for day, vacc_data_list in data_dict.items():
        # 1. Check if it is the correct day to give vaccines.
        if day == (simulation_day-outbreak_day):
            print(f"=== Outbreak Day: {outbreak_day} ===")
            # 2. Get the vaccine data
            vaccType = vacc_data_list[0]
            vaccProfessions = vacc_data_list[1]
            vaccLocation = vacc_data_list[2]
            vaccName = vacc_data_list[3]
            vaccImmunity = vacc_data_list[4]
            # 3. Give out vaccines based on vaccination types
            if vaccType == "Profession_location":
                for location in vaccLocation:
                    # FIXME: Below function is not the correct way to get agents in a location. \
                    # Important: FIXED :) But check if it works...
                    agents_by_loc = environment.get_all_successors(location)
                    for agent in agents_by_loc:
                        if agent.get_agent_class() in vaccProfessions:
                            agent.vaccinate(vaccImmunity)
            elif vaccType == "All":
                print(f"Vaccines are given to all agents in the simulation. vacc immunity is {vaccImmunity}")
                for agent in agent_list:
                    print(f"Vaccine is given to: {agent._agent_name} | {agent.infection_probability_AirBorne}")
                    agent.vaccinate(vaccImmunity)
                    print(f"Agent {agent._agent_name} is vaccinated with {vaccName} on day {simulation_day}. | {agent.infection_probability_AirBorne}")


def DAILY_PCRandQUARANTINE_checker(environment_object,
                                   agent_list: list,
                                   quarantine_list: list,
                                   infected_by_class_dict: dict,
                                   QuarantineByPCR=True,
                                   QuarantineByClass=False):
    """
    Perform PCR Test and Quarantine.
    1. Filter out symptomatic agents.
        1.1. Perform PCR Test.
        1.2. Set the agent to Quarantined if PCR Test is positive.
    2.
    3. Return the updated agents and quarantined agents list.

    :param agent_list:
    :param quarantine_list:
    :param infected_by_class_dict:
    :param QuarantineByPCR:
    :param QuarantineByClass:
    :return:
    """
    new_agents_list, new_q_agents_list = [], []
    if not QuarantineByClass and not QuarantineByPCR:
        return agent_list, quarantine_list

    if QuarantineByClass:  # Quarantine by Class. ---------------------------------------------------------------------------
        new_agents_list = agent_list.copy()
        new_q_agents_list = quarantine_list.copy()

        infected_dict = infected_by_class_dict.copy()
        for agent in agent_list:
            if agent.can_agent_transmit():
                infected_dict[agent.get_agent_class()] += 1

        for key, value in infected_dict.items():
            if value > 10:
                print(f"CLASS Quarantine is done for: {key}.")
                for agent in agent_list:
                    if agent.get_agent_class() == key:
                        curr_loc = agent.get_current_location()
                        agent.set_quarantined(True)  # FIXME: set current locations to Quarantine.
                        agent.remove_from_environment(environment_object, curr_loc)
                        agent.set_curr_loc("Quarantine")
                        new_q_agents_list.append(agent)
                        new_agents_list.remove(agent)

        agent_list, quarantine_list = new_agents_list, new_q_agents_list

    if QuarantineByPCR:  # Quarantine by PCR. --------------------------------------------------------------------------
        new_agents_list, new_q_agents_list = [], []
        for agent in agent_list:
            # Filter out symptomatic agents.
            if agent.decide_PCR():
                # Perform PCR Test.
                print(f"PCR Test is performed for: {agent._agent_name}.")
                if np.random.random(1)[0] < 0.9:  # PCR has 90% accuracy.
                    curr_loc = agent.get_current_location()
                    agent.set_quarantined(True)  # FIXME: set current locations to Quarantine.
                    agent.remove_from_environment(environment_object, curr_loc)
                    agent.set_curr_loc("Quarantine")
                    new_q_agents_list.append(agent)
                else:
                    new_agents_list.append(agent)
            else:
                new_agents_list.append(agent)
        # 2. Remove recovered agents from Quarantine.
        i = 0
        for agent in quarantine_list:
            if agent.is_agent_recovered():
                i+=1
                agent_home = agent.get_init_loc()
                agent.set_quarantined(False)
                agent.set_curr_loc(agent_home)
                agent.add_to_environment(environment_object, agent_home)
                new_agents_list.append(agent)
                # FIXME: Give an immunity BOOST here ??? (use agent.set_susceptability() here)
            else:
                new_q_agents_list.append(agent)

        print(f"Agents: {len(new_agents_list)}, Quarantined Agents: {len(new_q_agents_list)}, Recovered: {i}")
    # ------------------------------------------------------------------------------------------------------------------
    return new_agents_list, new_q_agents_list


def OUTBREAK_checker(agent_list: list, AgentClass, simulation_day, DataLoader):
    """
    Check for Outbreak.
    :param agent_list       : List of agents.
    :param AgentClass       : Agent class.
    :param simulation_day   : Simulation Day.
    :param DataLoader       : Loader class.
    :return                 : None
    """
    # 1. Check Airborne Outbreak Flag.
    if not DataLoader.get_AirBorneOutbreak():
        print(f"Q_AGENTS: {len(agent_list)}")
        infected_agents = len([agent for agent in agent_list if AgentClass.can_agent_transmit(agent)])
        # 2. Check Quarantine List if Outbreak flag is False.
        if infected_agents > int(AgentClass.total_agents * DataLoader.get_Pandemic_detection_threshold()):
            DataLoader.set_AirBorneOutbreak(True)
            DataLoader.set_AirBorneOutbreakDay(simulation_day)


def PCR_ENGINE(agents: list, quarantine_agents: list, environment_object, AgentClass, ClockClass):
    """
    Group PCR Testing and Quarantine.
    #FIXME: This function is not implemented yet.
    :param agents:
    :param quarantine_agents:
    :param environment_object:
    :param AgentClass:
    :param ClockClass:
    :return:
    """
    pass


if __name__ == '__main__':
    pass




