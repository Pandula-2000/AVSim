import pandas as pd
from Environment import *
import Environment
from Clock import Time
import Agents2
import bimodelity
from numpy import random
from DataLoader import Loader
from Bus_plan import *
import os
from ThreeWheel_plan import *

os.path.abspath(os.curdir)
main_dir_path = os.path.abspath(os.curdir)


def STEP_AGENTS(tuktuks: list, agent_list: list, env: Environment, time: Time.get_time(), poll_threshold=30):
    """
    Steps a given Agents state.
    Note: No need to increment time unit here. Its done in main loop.
    IMPORTANT: There are Two main parts here.
    1. Agent visits a place that is in the same zone (No need to take a bus then)
        Get the distance to the next location.--> Then get the time to travel that distance.
        Initiate a counter to count the time taken to travel.
    2. Agent visits a place that is in a different zone (Need to take a bus then)
        2.1. Agent is not in Transit.
        2.2. Agent is in Transit.
    :param agent_list       : A list of agent objects
    :param time             : Time of simulation step
    :param poll_threshold   : Threshold waiting time for public transport
    :return: None
    """
    # Clean residuals.
    for Agent in agent_list:
        # Update the Agent first.
        Agent.updateAgentV1(env, time)
        # ---------------- for Debugging -------------------------------------------------------------------------------
        # try:
        #     print(f"{time} | Current Loc: ({curr} --> {env.get_parent(curr)[0]} --> {env.get_parent(env.get_parent(curr)[0])[0]})| Next Loc: ({next} --> {nextZone} --> {env.get_parent(nextZone)[0]}) | Stay: {Agent.get_stay_duration()} | In bus: {Agent.get_in_bus()} "f"| Transit: {Agent.get_transition()} | Walk Flag: {Agent.get_is_walk()} | Poll Timer: {Agent.get_poll_timer()}")
        # print(f"{time} | X: {Agent.x} | Y: {Agent.y} | {Agent.get_current_location()}")
        # except:
        #     print(curr)
        #     print(Agent.get_public_transport_vehicle().bus_dict)
        # finally:
        #     print('continue anyway......')
        # --------------------------------------------------------------------------------------------------------------
        # Check Transit Flag.
        if not Agent.get_transition():
            curr = Agent.get_current_location()
            # print(f"{time} | Current Loc: ({curr} --> {env.get_parent(curr)[0]} --> {env.get_parent(env.get_parent(curr)[0])[0]})| Next Loc: Not yet set | Stay: {Agent.get_stay_duration()} | In bus: {Agent.get_in_bus()} "f"| Transit: {Agent.get_transition()} | Walk Flag: {Agent.get_is_walk()} | Poll Timer: {Agent.get_poll_timer()} | Walk Timer: {Agent.get_walk_timer()}")

            # print('--> NOT IN TRANSIT')
            # Not in Transit...
            if 1 <= time <= 5 * 60:
                # print(f"Agent is sleeping")
                Agent.sleepAgent()

            else:
                RANDOM_MOTION(env, Agent)
        # NOTE: ------------------------------------- Agent on the move ------------------------------------------------
        elif Agent.get_transition():
            curr = Agent.get_current_location()
            next = Agent.get_next_location()
            nextZone = Agent.get_next_zone()
            # print(
            #     f"{time} | Current Loc: ({curr} --> {env.get_parent(curr)[0]} --> {env.get_parent(env.get_parent(curr)[0])[0]})| Next Loc: ({next} --> {nextZone} --> {env.get_parent(nextZone)[0]}) | Stay: {Agent.get_stay_duration()} | In bus: {Agent.get_in_bus()} "f"| Transit: {Agent.get_transition()} | Walk Flag: {Agent.get_is_walk()} | Poll Timer: {Agent.get_poll_timer()} | Walk Timer: {Agent.get_walk_timer()}")

            # print('--> IN TRANSIT')
            # Note: ----------------------------------------- Walk -----------------------------------------------------
            if Agent.get_is_walk():
                # Same Zone.
                # Get the distance to the next location.--> Then get the time to travel that distance.
                # Initiate a counter to count the time taken to travel.

                # if Agent.get_walk_timer() == 0:  # Start timer
                #     # print("-------------------- WALKING Initiated ----------------")
                #     walkTime = env.calculate_travel_time(Agent.get_next_location(), Agent.get_current_location())
                #     print(f"Walk Time is....................... {walkTime}")
                #     Agent.set_walk_timer(walkTime)
                Agent.decrement_walk_timer()

                if Agent.get_walk_timer() <= 0:  # End timer (Arrived)
                    Agent.set_walk_flag(False)
                    Agent.set_transit_flag(False)
                    Agent.set_curr_loc(Agent.get_next_location())
                    Agent.set_walk_timer(0)
                    # print(f"{time} | Agent added to {Agent.get_next_location()} -- ")
                    # Note: Add the agent to environment here.
                    # env.add_agent(Agent.get_next_location(), Agent)  # Adds the agent to the environment
                    Agent.add_to_environment(env, Agent.get_next_location())
                continue
            # Note: ---------------------------------- Transport by Vehicle --------------------------------------------
            if curr == nextZone or curr == next:
                # 1. set transport flags to False
                if Agent.get_in_bus():  # ----------------- Agent is in the Bus ---------------------
                    Agent.set_transit_flag(False)
                    Agent.set_in_bus_flag(False)
                    # 2. remove agent from bus
                    Agent.get_public_transport_vehicle().remove_agent(Agent)
                    # 3, reset public transport vehicle
                    Agent.set_public_transport_vehicle(None)
                    # 4. Set current location as next location
                    Agent.set_curr_loc(next)
                else:  # ----------------- Agent is in the TukTuk ---------------------
                    # print(f"{time} | Agent {Agent.get_agent_name()} has finished TukTuk")
                    Agent.reset_poll_timer()
                    Agent.set_transit_flag(False)
                    Agent.set_in_tuktuk_flag(False)
                    Agent.get_public_transport_vehicle().remove_agent(Agent)
                    Agent.set_public_transport_vehicle(None)

                # print(f"{time} | Agent added to {Agent.get_next_location()} ---")
                # Note: Add the agent to environment here.
                Agent.add_to_environment(env, next)
                # Arrived by bus!
                # print(f"Agent arrived at: {next}")
            else:
                if Agent.get_in_bus():  # Agent is in the Bus.
                    # print(f"Agent is in the bus: {Agent.get_public_transport_vehicle()} at : {Agent.get_public_transport_vehicle().get_previous_location()}")
                    # print(Agent.get_public_transport_vehicle().get_next_locations())
                    Agent.set_curr_loc(Agent.get_public_transport_vehicle().get_previous_location())

                elif Agent.get_in_tuktuk_flag():
                    continue

                else:  # Agent trying to find a Transport (BUS)
                    buses_in_station = env.get_buses(curr)
                    # print(f"Buses in station: {buses_in_station}")

                    # ----------- for debugging ----------------------------
                    # b = [list(d.bus_dict.keys()) for d in buses_in_station]
                    # c = [list(d.get_next_locations()) for d in buses_in_station]
                    # bd = [list(d.bus_dict) for d in buses_in_station]
                    # for i in range(len(bd)):
                    #     print("----------buses-------------------")
                    #     #print(bd[i])
                    #     print(c)
                    # ------------------------------------------------------

                    selected_bus = availableBus(buses_in_station, Agent)
                    # print(f"Selected bus is: {selected_bus}")

                    # remove below two lines later....
                    # if selected_bus!=None:
                    #     print(f"selected bus visits {selected_bus.bus_dict}")
                    # print(selected_bus==None)
                    if selected_bus != None:  # We have a bus :)
                        Agent.set_in_bus_flag(True)
                        Agent.set_walk_flag(False)
                        Agent.reset_poll_timer()
                        # print(f"-------------------------------in bus set to :{Agent.get_in_bus()}")
                        # add the agent to the bus
                        selected_bus.add_agent(Agent)
                        # assign the bus to the agent
                        # print(len(selected_bus.get_agents()))
                        Agent.set_public_transport_vehicle(selected_bus)
                    else:  # No bus yet :(
                        if Agent.get_poll_timer() > poll_threshold:  # ------------ Use other Transport ----------------
                            print(f"{time}: Tuktuk mode for Agent {Agent.get_agent_name()}")
                            # print(f"{time} | Current Loc: ({curr} --> {env.get_parent(curr)[0]} --> {env.get_parent(env.get_parent(curr)[0])[0]})| Next Loc: ({next} --> {nextZone} --> {env.get_parent(nextZone)[0]}) | Stay: {Agent.get_stay_duration()} | In bus: {Agent.get_in_bus()} "f"| Transit: {Agent.get_transition()} | Walk Flag: {Agent.get_is_walk()} | Poll Timer: {Agent.get_poll_timer()} | Walk Timer: {Agent.get_walk_timer()}")

                            # NOTE ------------------------ Select TukTuk ----------------------------------------------
                            tuktuks_in_station = env.get_tuktuk(curr)
                            if tuktuks_in_station is not None:
                                Agent.reset_poll_timer()
                                TukTime = env.calculate_travel_time(Agent.get_next_location(),
                                                                    Agent.get_current_location())
                                if (time + TukTime) <= 1440:
                                    selected_tuktuk = availableThreeWheel(tuktuks_in_station, Agent)
                                    # ---set tuk status
                                    env.remove_tuktuk(curr, selected_tuktuk)
                                    selected_tuktuk.add_agent(Agent)

                                    selected_tuktuk.set_in_motion(True)
                                    selected_tuktuk.set_next_location(next)
                                    # ---set agent status
                                    Agent.set_in_tuktuk_flag(True)
                                    Agent.set_public_transport_vehicle(selected_tuktuk)  # Tuktuks also set to public

                                    selected_tuktuk.set_tuktuk_timer(TukTime)

                                    print(f"ID: {selected_tuktuk.id}| Motion {selected_tuktuk.get_in_motion()} | TukTuk Timer set to {selected_tuktuk.get_tuktuk_timer()}")
                                    # print(f"{time} | Current Loc: ({curr} --> {env.get_parent(curr)[0]} --> {env.get_parent(env.get_parent(curr)[0])[0]})| Next Loc: ({next} --> {nextZone} --> {env.get_parent(nextZone)[0]}) | Stay: {Agent.get_stay_duration()} | In bus: {Agent.get_in_bus()} "f"| Transit: {Agent.get_transition()} | Walk Flag: {Agent.get_is_walk()} | Poll Timer: {Agent.get_poll_timer()} | Walk Timer: {Agent.get_walk_timer()}")
                                else:
                                    #  If the day is not enough for transport, then Teleport the agent back home.
                                    
                                    # print(f"Agent {Agent.get_agent_name()} is teleported from {Agent.get_current_location()} to {Agent.get_next_location()}")
                                    Agent.set_transit_flag(False)
                                    Agent.set_in_tuktuk_flag(False)
                                    Agent.set_public_transport_vehicle(None)
                                    Agent.set_curr_loc(next)
                                    Agent.set_walk_flag(False)
                                    Agent.add_to_environment(env, next)
                                    # print(f"{time} | Current Loc: ({next} --> {env.get_parent(next)[0]} --> {env.get_parent(env.get_parent(next)[0])[0]}) | Stay: {Agent.get_stay_duration()} | In bus: {Agent.get_in_bus()} "f"| Transit: {Agent.get_transition()} | Walk Flag: {Agent.get_is_walk()} | Poll Timer: {Agent.get_poll_timer()} | Walk Timer: {Agent.get_walk_timer()}")

                            else:
                                # Agent.reset_poll_timer()
                                print(f"No tuktuk yet. Waiting in poll for: {Agent.get_poll_timer()}")
                                continue

                        else:
                            # print(f"No bus yet. Waiting in poll for: {Agent.get_poll_timer()} Minutes")
                            Agent.increment_poll_timer()


def STEP_TRANSPORT(tuktuks: list, buses: list, env: Environment, time: Time.get_time()):
    i = 0

    for tuktuk in tuktuks:
        tuktuk.updateVehicle(env)

    for bus in buses:
        bus.updateVehicle(time)
        i += 1
        # if bus.get_in_motion()==True:
        #     print(f"Bus {i} is at {bus.get_previous_location()} at time={time}")
        # else:
        #     print(f"Bus {i} is at Rest")

        # print(f"{time} | {bus.get_previous_location()} | {bus.get_current_location()}")
        # print('')
        # print(f"{time} | Bus {i} | {bus.bus_dict.keys()}")
        # print(f"{time} | Bus {i}")

        curr = bus.get_current_location()
        prev = bus.get_previous_location()

        # print(curr,prev)
        # Note: Add bus to the environment if its not already there.
        if not bus.get_in_motion():
            continue

        # print(prev, env.get_zone_class(prev))
        # if env.get_zone_class(prev)==None:
        #     continue

        if len(prev.split('_')) == 1:
            continue

        # if env.get_zone_class(env.get_parent(curr)[0])==None and curr==prev: # At a higher level node
        #     continue

        if curr == prev:
            if bus not in env.get_buses(curr):
                # print(f"Bus added")
                env.add_bus(curr, bus)
                # print(f"bus added to: {curr}")
                # print(bus.bus_dict.keys())
        else:
            if bus in env.get_buses(prev):
                # print(f"Bus removed")
                env.remove_bus(prev, bus)
        # Note: Remove bus from the environment if its not there.
        # print(f"{env.get_buses(prev)} at {prev}")


def RANDOM_MOTION(env, agent):
    """
    Randomly moves the agents.
    # IMPORTANT: scale is the standard deviation. loc is the mean value.
    # FIXME : get_sigma should not be inside Time. change it later to be inside Loader or something.
    :param agent            : Agent class.
    :param currentLocation  : ID of current location
    :return                 : A list of new x,y coordinates.
    """
    currentLocation = agent.get_current_location()
    grid_len = env.get_side_length(currentLocation)

    # FIXME: You cant let agents go outside the boundary. FIX that!!!!
    # FIXME: Adjust Sigma correctly. currently Sigma is in meters. But shapely point is not so....
    # xy = random.normal(loc=(agent.get_coordinates().x, agent.get_coordinates().y), scale=Time.get_sigmaRandom(), size=(2))
    # Currently agents will not move anywhere. Freeze !
    # x, y = agent.get
    # To round if needed --> list(map(lambda s: round(s, 3), xy))
    # agent.set_coordinates(Point(xy))
    x, y = agent.get_agent_x_y()
    dx = random.randint(-2, 2)
    dy = random.randint(-2, 2)
    x_new, y_new = x + dx, y + dy
    # If we run out of the grid, reflect back inside.
    if x_new <= 0 or x_new >= grid_len:
        x_new = x - dx
        # print(x_new)
    if y_new < 0 or y_new >= grid_len:
        y_new = y - dy
        # print(y_new)

    # ---------------------------Set new x, y ---------------------------
    agent.set_agent_x_y(x_new, y_new)
    # Note: ------------Stay Duration gets Decremented here.-------------
    agent.decrement_stay_duration()
    return None


# IMPORTANT: ---------------------- Route planner for Vector Born disease ----------------------

def STEP_AGENTS_V2(agent_list: list, time, env: Environment, start_time=5, end_time=19):
    for Agent in agent_list:

        if (time < start_time * 60):
            # print(f"{time} | {Agent.get_current_location()} | {'Sleeping'}")
            Agent.sleepAgent()
        else:
            Agent.updateAgentV2(env, time, end_time)


if __name__ == "__main__":
    pass
    # import xlsxwriter
    # workbook = xlsxwriter.Workbook('..\Results\Test_run_results.xlsx')
    # worksheet = workbook.add_worksheet()
    #
    # # Start the clock
    # Time.init()
    # # Launch the Environment
    # env = LaunchEnvironment()
    # # Spawn the Agents
    # agents = Agents.agent_create(env, use_def_perc=True)
    #
    # # Load the statistics
    # Loader.init_probabilities()
    # r, c = 0, 0
    # worksheet.write(r, c, 'Time')
    # for i in range(1, 1441 * 1):
    #     r+=1
    #     worksheet.write(r, c, i)
    #
    # c = 1
    # for key, agent in agents.items():
    #     print(agent._current_location, agent._init_location, agent._current_location_class)
    #     print(agent._in_transition)
    #     r = 0
    #     worksheet.write(r, c, key)
    #     print(key)
    #     ID = Loader.class_encodings[key.split('_')[0]]
    #     print(ID)
    #     for i in range(1, 1441 * 1):
    #         r+=1
    #         # print(f"------------------iter {i}------------time is {Time.get_time()}")
    #         # print(Time.get_time())
    #         place = RoutePlanner(agent, Loader.getProbMat(ID), Loader.getStdMat(ID))
    #         worksheet.write(r, c, place)
    #         print(f"T {Time.get_time()} {place}, ztztt: {agent._zone_to_zone_t_time}")
    #
    #     c+=1

    # workbook.close()
