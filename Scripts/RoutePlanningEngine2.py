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


def STEP_AGENTS(agent_list: list, env: Environment, time: Time.get_time(), poll_threshold=10):
    """
    Steps a given Agents state.
    Note: No need to increment time unit here. Its done in main loop.
    IMPORTANT: There are Two main parts here.

    1. Update the Agent.

    2. Agent is not in Transit.
        2.1. Agent is sleeping.
        2.2. Agent is in random motion.

    3. Agent is in Transit.
        3.1. Current Location is the same as the next location.
            3.1.1. Next locations are over.
            3.1.2. There are more next locations to go.
        3.2. Agent is Walking.

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
        #     print(f"{time} | Current Loc: ({curr} --> {env.get_parent(curr)[0]})| Next Loc: ({next} --> {env.get_parent(next)[0]}) | Stay: {Agent.get_stay_duration()} | In bus: {Agent.get_in_bus()} "f"| Transit: {Agent.get_transition()} | Walk Flag: {Agent.get_is_walk()} | Poll Timer: {Agent.get_poll_timer()}")
        #     # print(f"{time} | X: {Agent.x} | Y: {Agent.y} | {Agent.get_current_location()}")
        # except:
        #     print(curr)
        # finally:
        #     print('continue anyway......')
        # --------------------------------------------------------------------------------------------------------------
        # Check Transit Flag.
        if not Agent.get_transition():
            curr = Agent.get_current_location()
            # print(
            #     f"{time} |T| CL: ({curr} --> {env.get_parent(curr)[0]})| NL: None | Stay: {Agent.get_stay_duration()} | In bus: {Agent.get_in_bus()} "f"| T: {Agent.get_transition()} | Tuk: {Agent.get_in_tuktuk_flag()}| WF {Agent.get_is_walk()} | PollT: {Agent.get_poll_timer()} | WalkT: {Agent.get_walk_timer()}")
            if 1 <= time <= 5 * 60:
                # print(f"Agent is sleeping")
                Agent.sleepAgent()
            else:
                RANDOM_MOTION(env, Agent)
        # NOTE: ------------------------------------- Agent on the move ------------------------------------------------
        elif Agent.get_transition():
            curr = Agent.get_current_location()
            next = Agent.get_next_location()
            # print(
            #     f"{time} |T| CL: ({curr} --> {env.get_parent(curr)[0]})| NL: ({next} --> {env.get_parent(next)[0]}) | Stay: {Agent.get_stay_duration()} | In bus: {Agent.get_in_bus()} "f"| T: {Agent.get_transition()} | Tuk: {Agent.get_in_tuktuk_flag()}| WF {Agent.get_is_walk()} | PollT: {Agent.get_poll_timer()} | WalkT: {Agent.get_walk_timer()}")

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

                if Agent.get_walk_timer() < 0:  # End timer (Arrived)
                    Agent.set_walk_flag(False)
                    Agent.set_curr_loc(Agent.get_next_location())
                    Agent.set_walk_timer(0)
                continue
                    # print(f"{time} | Agent added to {Agent.get_next_location()} -- ")
            # Note: -------------------------------------- Pvt Vehicle -------------------------------------------------
            elif Agent.get_pvt_trans_flag():
                # print(f"{time} | Agent is in Private Transport")
                Agent.decrement_pvt_transport_counter()
                if Agent.get_pvt_transport_counter() < 0:
                    Agent.set_pvt_trans_flag(False)
                    Agent.set_curr_loc(Agent.get_next_location())
                    Agent.set_pvt_transport_counter(0)
            # Note: ---------------------------------------- TUK TUK ---------------------------------------------------
            elif Agent.get_in_tuktuk_flag():
                # print(f"{time} | Agent is in TukTuk")
                Agent.decrement_tuktuk_timer()
                if Agent.get_tuktuk_timer() < 0:
                    # print(f"{time} | Agent has finished TukTuk")
                    Agent.set_in_tuktuk_flag(False)
                    Agent.set_curr_loc(Agent.get_next_location())
                    Agent.reset_tuktuk_timer()
                    Agent.set_public_transport_vehicle(None)

                continue
            # Note: ----------------------------------- Target Node Reached --------------------------------------------
            if curr == next:
                # ------------------------------------- Reset Transport Flags ------------------------------------------
                Agent.reset_poll_timer()
                if Agent.get_in_bus():              # ----------------- Agent is in the Bus ----------------------------
                    Agent.set_in_bus_flag(False)
                    # 2. remove agent from bus
                    Agent.get_public_transport_vehicle().remove_agent(Agent)
                    # print(Agent.get_public_transport_vehicle().agents)
                    # 3. reset public transport vehicle
                    Agent.set_public_transport_vehicle(None)

                # elif Agent.get_in_tuktuk_flag():    # ----------------- Agent is in the TukTuk -------------------------
                #     # print(f"{time} | Agent {Agent.get_agent_name()} has finished TukTuk")
                #     # Agent.set_in_tuktuk_flag(False)
                #     # 3. reset public transport vehicle
                #     Agent.set_public_transport_vehicle(None)
                # Note: ---------------------------------- Agent has reached the destination ---------------------------
                if len(Agent.get_next_locations()) == 0:
                    # Important: Add the agent to environment here.
                    Agent.add_to_environment(env, next)
                    # print(f"{time} | Agent added to {next} -- ")
                    # print(f"{time} | Agent {Agent.get_agent_name()} has FINISHED the journey")
                    Agent.set_transit_flag(False)
                    # Agent.set_in_bus_flag(False)
                    # Agent.set_in_tuktuk_flag(False)
                    # Agent.set_walk_flag(False)
                    # Agent.set_pvt_trans_flag(False)
                    Agent.set_public_transport_vehicle(None)
                # NOTE: ----------------------------- Agent has more locations to go -----------------------------------
                else:
                    next_location = Agent.get_next_locations()[0]
                    Agent.set_next_location(next_location)
                    Agent.set_next_locations(Agent.get_next_locations()[1:])
                    # Agent.get_next_locations().remove(Agent.get_next_locations()[0])
                    # print(f"{time} | Agent has reached {curr} and moving to {Agent.get_next_location()}")

                    if env.is_same_zone(Agent.get_current_location(), Agent.get_next_location()):  # 'and' to check if they stay in same Zone
                        # print(f"Walking to the next location...")
                        Agent.set_walk_flag(True)
                        walkTime = env.calculate_travel_time(Agent.get_next_location(), Agent.get_current_location())
                        # print(f"Walk Time is....................... {walkTime}")
                        Agent.set_walk_timer(walkTime)
                    else:
                        Agent.set_walk_flag(False)
                        Agent.set_walk_timer(0)
                        Agent.set_transit_flag(True)
                        Agent.reset_poll_timer()
                # continue
            # Note: ---------------------------------- Transport by Vehicle --------------------------------------------
            else:
                # NOTE: --------------------------------- Agent in bus -------------------------------------------------
                if Agent.get_in_bus():
                    # print(f"Agent is in the bus at : {Agent.get_public_transport_vehicle().get_previous_location()}")
                    # print(Agent.get_public_transport_vehicle().get_previous_location())
                    Agent.set_curr_loc(Agent.get_public_transport_vehicle().get_previous_location())

                # NOTE: --------------------------------- Agent in Tuk -------------------------------------------------
                # elif Agent.get_in_tuktuk_flag():
                #     print("NOOOOOOOOOOOOOOOOOOOOOOOOOOOO")
                #     continue

                else:  # NOTE: ------------------ Agent trying to find a Transport (BUS) -------------------------------
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
                    # print(f"{time}: Buses in station: {len(buses_in_station)}")
                    # for bus in buses_in_station:
                    #     print(bus.bus_tt)
                    #     print(bus.get_next_locations())

                    # ------------------------------------------------------

                    selected_bus = availableBus(buses_in_station, Agent)
                    # print(f"Selected bus is: {selected_bus}")

                    # remove below two lines later....
                    # if selected_bus!=None:
                    #     print(f"selected bus visits {selected_bus.bus_tt[0]}")
                    # print(selected_bus==None)
                    if selected_bus != None:  # We have a bus :)
                        Agent.set_in_bus_flag(True)
                        Agent.set_walk_flag(False)
                        Agent.reset_poll_timer()
                        # add the agent to the bus
                        selected_bus.add_agent(Agent)
                        # assign the bus to the agent
                        Agent.set_public_transport_vehicle(selected_bus)
                    else:  # No bus yet :(
                        if Agent.get_poll_timer() > poll_threshold:  # ------------ Use other Transport ----------------
                            # print(f"{time}: Tuktuk mode for Agent {Agent.get_agent_name()}")
                            Agent.reset_poll_timer()
                            TukTime = env.calculate_travel_time(Agent.get_next_location(),
                                                                Agent.get_current_location())
                            if (time + TukTime) <= 1440:
                                # print(f"CAN TRAVEL BY TUK BEFORE DAY ENDS !!! ")
                                # --- set agent status ---
                                Agent.set_in_tuktuk_flag(True)
                                Agent.set_tuktuk_timer(TukTime)
                                # Agent.set_curr_loc("TUKTUK")
                                Agent.set_public_transport_vehicle(None)

                                # --------------------- Day is NOT enough for  tuktuk transport ------------------------
                            else:
                                # Teleport the agent back home.
                                # print(f"{time}: {Agent.get_agent_name()} CANNOT TRAVEL BY TUK BEFORE DAY ENDS !!! ")
                                # print(Agent.get_next_locations()[-1])
                                Agent.set_transit_flag(False)
                                Agent.set_in_tuktuk_flag(False)
                                Agent.set_public_transport_vehicle(None)

                                Agent.set_curr_loc(Agent.get_init_loc())
                                Agent.set_next_location(None)
                                Agent.add_to_environment(env, Agent.get_init_loc())
                                # print(f"{time} Agent added to {Agent.get_init_loc()} --- ")

                                Agent.set_next_locations([])
                                Agent.set_walk_flag(False)
                        else:
                            # print(f"No bus yet. Waiting in poll for: {Agent.get_poll_timer()} Minutes")
                            Agent.increment_poll_timer()


def STEP_TRANSPORT(buses: list, env: Environment, time: Time.get_time()):
    """
    Steps the transport vehicles.
    1. Step the tuktuks.
    2. Step the buses.
        2.1 Do not step if not in motion.
        2.1 Add the bus to the environment if it is at a new location.
        2.2 Remove the bus from the environment if it is not at the previous location.
    :param tuktuks  : List of tuks.
    :param buses    : List of buses.
    :param env      : Environment object.
    :param time     : Time stamp.
    :return:
    """
    # 1. ---------------------- Step the Tuktuks ----------------------
    # FIXME: Tuktuk objects are not used in the New simulation.
    # for tuktuk in tuktuks:
    #     tuktuk.updateVehicle(env)

    # 2. ---------------------- Step the Buses ----------------------
    i = 0
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

        # 2.1. Do not step the bus if it is not in motion.
        if not bus.get_in_motion():
            continue
        # 2.2. Add the bus to the environment if it is at a new location.
        if curr == prev:
            if bus not in env.get_buses(curr):
                # print(f"Bus added")
                env.add_bus(curr, bus)
                # print(f"bus added to: {curr}")
                # print(bus.bus_dict.keys())
        # 2.3. Remove the bus from the environment if it is not at the previous location.
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

    # FIXME: dx and dy are taken from a uniform distribution. Change it to a normal distribution ????
    # xy = random.normal(loc=(agent.get_coordinates().x, agent.get_coordinates().y), scale=Time.get_sigmaRandom(), size=(2))
    # Currently agents will not move anywhere. Freeze !
    # x, y = agent.get
    # To round if needed --> list(map(lambda s: round(s, 3), xy))
    # agent.set_coordinates(Point(xy))
    x, y = agent.get_agent_x_y()
    dx = random.randint(-2, 2)
    dy = random.randint(-2, 2)
    try:
        x_new, y_new = x + dx, y + dy
    except:
        print(agent)
        print(agent.get_agent_x_y())
        x_new, y_new = 1,1
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