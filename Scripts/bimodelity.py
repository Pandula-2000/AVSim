import pandas as pd
import numpy as np
import time
import numba as nb
import xlsxwriter as xl
import os
from DataLoader import Loader
from Environment import *
from tqdm import tqdm
from Clock import Time
import re

os.path.abspath(os.curdir)
main_dir_path = os.path.abspath(os.curdir)


# np.random.seed(42)

def getNextLocation(df, time):
    """
    This function returns the Location given the time.

    :param df   : Dataframe containing location visit probabilities.
    :param time : The time stamp for which the possible visit location is generated.
    :return     : Possible visit location.
    """
    location = None
    pdf = df[time]
    cdf = np.cumsum(pdf)
    random_Num = np.random.rand()
    # print(random_Num)
    for i in range(len(cdf)):
        if random_Num <= cdf[i]:
            location = df["Locations"][i]
            break
    # FIXME: REMOVE _home
    if location == "_home":
        return 'Home'
    elif location == "_w_home":
        return 'Home'
    elif location == "RuralBlock":
        return 'ResidentialZone'
    else:
        return location
    # return location





def getStayDuration(df, Location):
    """
    This function returns the Stay duration given the Location.

    :param df       : Dataframe containing stay duration probabilities.
    :param Location : The current location of the agent.
    :return         : How much time the agent is going to spend at the given location.
    """
    stayTime = None
    pdf = df[df['Locations'] == Location]
    cdf = pdf.iloc[:, 1:].cumsum(axis=1)
    # print(Location)
    # print(cdf)
    random_Num = np.random.rand()
    # print(random_Num)
    for i in range(1, 1441):
        # print(cdf[i])
        if random_Num <= cdf[i].values[0]:
            stayTime = i
            # print("Stay ",stayTime)
            break
    return stayTime


def get_probability(time, loc, data_frame):
    """
    :param time         : Range 1-1440
    :param loc          : Std catalog naming format
    :param data_frame   : Location column as row index (apply df.set_index('Locations', inplace=True) before using this function)
    """

    prob = data_frame.loc[loc, time]
    return prob


def get_probability_v2(time, loc, data_frame):
    """

    :param time:
    :param loc:
    :param data_frame:
    :return:
    """
    prob = data_frame.loc[loc, time]
    return prob

# ----------------------------------------------------------------------------------------------------------------------

def generateTimeTable(env, agent, data_loader=Loader, start_time=5, end_time=15):
    """
    Generate the daily Schedule for a given agent.

    :param env          : Environment Object.
    :param  agent       : Agent Object.
    :param start_time   : The start time of the schedule.
    :param end_time     : The end time of the schedule.
    :return             : The schedule as a dictionary where --> Keys : Location IDs, Values : (ArrivalTime, Stay duration).
    """

    gamma_home = data_loader.gamma_home
    gamma_work = data_loader.gamma_work

    start = start_time * 60
    end = end_time * 60
    timetable = [[], []]
    time = start
    curr_loc = agent.get_current_location()
    location = ''
    stay = 0
    dummy = []
    occupation = agent.get_agent_class()  # teacher, doctor, student (old)

    # FIXME: Use spectral clustering results here...
    # df, df_stay = agent.get_sub_cls_statistics()

    df = data_loader.getProbMat(occupation)
    df_stay = data_loader.getStdMat(occupation)

    # NOTE: Everyone is at init_location (Home or _w_home) in between t=end and t=start.
    while time <= 1440:
        if len(timetable[0]) >= 5:
            break
        location_class = getNextLocation(df, time)  # fill here with function 1
        stay = getStayDuration(df_stay, location_class)  # fill here with function 2
        # print(f"Curr_loc:{curr_loc} | Target loc_class:{location_class} | stay:{stay}")

        location = env.get_exact_target_node(curr_loc, location_class, agent)

        curr_loc = location

        # print(f"{location_class}, {location}, curr_loc: {agent.get_current_location()}, stay: {stay}")
        if time + stay >= end:
            timetable[0].append(location)
            timetable[1].append((time, end - time))
            break
        else:
            timetable[0].append(location)
            timetable[1].append((time, stay))
            time = time + stay
    return timetable


def getNextLocationV2(df, time, conditioned_location):
    """
    This function returns the Location given the time.

    :param df                   : Dataframe containing location visit probabilities.
    :param time                 : The time stamp for which the possible visit location is generated.
    :param conditioned_location : The location from which the agent is conditioned to move.
    :return                     : Possible visit location.
    """
    location = None
    locations = list(df["Locations"])
    df_copy = df.copy()
    df_copy.set_index('Locations', inplace=True)

    if conditioned_location == 'Home':
        prob_conditioned_location = df_copy.at[conditioned_location, time] + df_copy.at['_w_home', time]
        df_copy.drop(conditioned_location, inplace=True)
        df_copy.drop('_w_home', inplace=True)
        locations.remove(conditioned_location)
        locations.remove('_w_home')
    else:
        prob_conditioned_location = df_copy.at[conditioned_location, time]
        df_copy.drop(conditioned_location, inplace=True)
        locations.remove(conditioned_location)

    pdf = df_copy[time]/(1-prob_conditioned_location)
    # print(pdf)
    cdf = list(np.cumsum(pdf))
    # print(cdf)
    # print(locations)

    random_Num = np.random.rand()
    # print(random_Num, time)
    for i in range(len(cdf)):
        # print(cdf[i])
        if random_Num < cdf[i]:
            # print(locations[i])
            location = locations[i]
            if location=="_w_home":
                return 'Home'
            else:
                return location


def generateTimeTableV2(env, agent, data_loader=Loader, start_time=5, end_time=21, step=20, week_end_step=60):
    # FIXME: This function is not used in the current version of the code. It is still under construction.
    timetable = [[], []]
    t_start = start_time * 60
    t_end = end_time * 60

    t = t_start
    init_loc = agent.get_init_loc()
    curr_loc = agent.get_current_location()
    work_loc = agent.get_work_loc()
    work_loc_class = agent.get_work_loc_class()

    stay = 0
    day = Time.get_DAY()
    day_type = Time.get_dayType()

    # ------------------ GAMMA VALUES ------------------
    # gamma_work = data_loader.gamma_work
    # gamma_home_holiday = data_loader.gamma_home
    gamma_work = agent.get_gamma_work()
    gamma_home_holiday = agent.get_gamma_home()
    # --------------------------------------------------
    # print(f"Work Location: ----------------------->>  {work_loc_class}, {work_loc}, {gamma_work}")

    df, df_stay, holiday_available = agent.get_sub_cls_statistics(day=day_type)
    df_prob = df.copy()
    df_prob.set_index('Locations', inplace=True)

    # print(f"HOLIDAY available: {holiday_available} | Day: {day}")

    # NOTE: ------------------------------------------- FOR WEEKENDS ---------------------------------------------------
    if (day_type==6 or day_type==7) and holiday_available:
        while True:
            next_loc = getNextLocationV2(df, t+stay, work_loc_class)
            exact_next_location = env.get_exact_target_node(curr_loc, next_loc, agent)
            # print(next_loc, exact_next_location)
            # print(exact_next_location)
            if exact_next_location == curr_loc:
                stay += week_end_step
            else:
                timetable[0].append(curr_loc)
                timetable[1].append((t, stay))
                t += stay
                stay = week_end_step

                curr_loc = exact_next_location
            if t+stay>=t_end or len(timetable[0])>=4:
                # print(t,t_end-t)
                timetable[0].append(curr_loc)
                timetable[1].append((t, 1440-t))
                return timetable

        # NOTE: ------------------------------------------- FOR WEEKDAYS ---------------------------------------------------
    else:
        # 1. Check if the agent is Further staying at home
        while get_probability(t, "Home", df_prob) >= np.random.rand():
            stay += step
            t += step

        if stay > 0:
            timetable[0].append(init_loc)
            timetable[1].append((t_start, stay))
            # print(timetable)
            stay = 0

        # 2. --------------------- Check if the agent is going for Work or Other location ------------------------------

        # 2.1 ----------------------- If the agent is going to Other place
        next_location = getNextLocationV2(df, t, "Home")
        # print(next_location)
        while (next_location != work_loc_class) and (get_probability(t, work_loc_class, df_prob) < gamma_work):
            # if len(timetable[0]) >= 3:
            #     break
            stay = getStayDuration(df_stay, next_location)
            if stay > 100:
                # print(day, t, next_location, stay)
                stay = 100
            # FIXME: As for the new method, no need to get the exact location here.
            exact_location = env.get_exact_target_node(curr_loc, next_location, agent)
            timetable[0].append(exact_location)
            timetable[1].append((t, stay))
            # print(timetable)
            t += stay
            stay = 0
            # Terminate point 1
            if t >= t_end:
                # print('--------------------- Time exceeded 1 ---------------------')
                return timetable
            next_location = getNextLocationV2(df, t, "Home")

        # 2.2----------------------- If the agent is going to Work
        # else:
        # print(timetable)
        # print(t,stay, get_probability(t + stay, work_loc_class, df_prob))
        while get_probability(t + stay, work_loc_class, df_prob) < gamma_work:
            stay += step
            if t + stay >= t_end:
                # print('---------------------Stay exceeded---------------------')
                stay = t_end - t
                if stay == 0:
                    break
                timetable[0].append(work_loc)  # Exactly Known for agent
                timetable[1].append((t, stay))
                return timetable
        # print(timetable)
        # print(t,stay, get_probability(t + stay, work_loc_class, df_prob))
        while get_probability(t + stay, work_loc_class, df_prob) >= gamma_work:
            stay += step
            if t + stay >= t_end:
                stay = t_end - t
                if stay == 0:
                    break
                # print('---------------------Time exceeded 2 ---------------------')
                timetable[0].append(work_loc)  # Exactly Known for agent
                timetable[1].append((t, stay))
                return timetable
        # print(timetable)
        # print(t,stay, get_probability(t + stay, work_loc_class, df_prob))
        # 1. Check if the agent is Further staying at Work
        while get_probability(t+stay, work_loc_class, df_prob) >= np.random.rand():
            # ----------------- Get stay from routine checking -------------------
            # stay += 1*step
            # if t + stay >= t_end:
            #     stay = t_end - t
            #     # print('---------------------Time exceeded 2 ---------------------')
            #     timetable[0].append(work_loc)  # Exactly Known for agent
            #     timetable[1].append((t, stay))
            #     return timetable
            # ---------------- Get stay from stay duration matrix ----------------
            st = getStayDuration(df_stay, work_loc_class)
            # print(f"Stay duration at work: ----------------- {st}")
            stay = st
            if (t + stay) >= t_end:
                stay = t_end - t
                if stay == 0:
                    break
            # --------------------------------------------------------------------
        # print(timetable)
        # print(t,stay, get_probability(t + stay, work_loc_class, df_prob))
        curr_loc = work_loc
        timetable[0].append(work_loc)  # Exactly Known for agent
        timetable[1].append((t, stay))
        # print(timetable)
        t += stay
        stay = 0

        # Termination point 2
        if len(timetable[0]) >= 5:
            return timetable
        # print(timetable)
        # 3. ----------------- Check if the agent is going Home or other location after work. ------------------------------

        # 3.1 --------------------- If the agent is going to Other place
        next_location = getNextLocationV2(df, t, work_loc_class)
        while next_location != "Home":
            # print(timetable)
            # print(f"Time is {t}")
            stay = getStayDuration(df_stay, next_location)
            if (t + stay) >= t_end:
                stay = t_end - t
                if stay == 0:
                    break
            exact_location = env.get_exact_target_node(curr_loc, next_location, agent)
            curr_loc = exact_location
            timetable[0].append(exact_location)
            timetable[1].append((t, stay))
            # print(timetable)
            t += stay
            stay = 0
            next_location = getNextLocationV2(df, t, work_loc_class)

            # Terminate if the timetable is full or time is up
            if len(timetable[0]) >= 5 or t >= t_end:
                return timetable

        # 3.2 ---------------------Finally, send the agent to Home
        timetable[0].append(init_loc)  # Exactly Known for agent
        timetable[1].append((t, 1440 - t))

        return timetable


def initTimeTables(env, Agents: list, sim_events: bool = False, writer=None):
    """
    Initialize the daily schedules for all agents.

    :param Agents    : List of Agent Objects.
    :param writer    : Writer object to write the timetables.
    :return          : Dictionary of Agent Objects with their daily schedules.
    """
    if writer is not None:
        writer.write(f"======================= Time Tables for day {Time.get_DAY()} ====================================\n")

    is_event_day = False

    if sim_events:
        is_event_day = checkEvents()
        print(f"Event day: {is_event_day}") # Only for testing

        if is_event_day:
            event_indices = getEventIndices()
            # print(f"Event indices: {event_indices}") # Only for testing

            event_details = getEventDetails(event_indices)
            # print(f"Event details: {event_details}") # Only for testing
            
            attnd_agnts = select_agents_for_event(Agents, event_indices, event_details)
            # print(f"Agents attending events: {attnd_agnts}") # Only for testing

            # attnd_agnts = {}

            # for indx in event_indices:
            #     event = event_details.loc[indx]

            #     attnd_clss_all_agnts = []
            #     req_cnt = 0
            #     attnd_lst = []
                
            #     for agnt in Agents:
            #         if agnt.get_agent_class() == event['attendees']:
            #             attnd_clss_all_agnts.append(agnt)
                
            #     req_cnt = int(len(attnd_clss_all_agnts) * event['attendee_perc'] / 100)

            #     for i in range(req_cnt):
            #         rand_index = random.randrange(len(attnd_clss_all_agnts))
            #         attnd_lst.append(attnd_clss_all_agnts[rand_index])
            #         attnd_clss_all_agnts.pop(rand_index)
                
            #     attnd_agnts[indx] = attnd_lst

                # print(f"Event {indx}: {event['location']} at {event['st_time']} for {event['dur']} hours")

    # for Agent in Agents:
    #     Agent.resetAgent(env)
    
    for agent in tqdm(Agents, desc="Generating Time Tables", disable=True):
        tt = generateTimeTableV2(env, agent, start_time=5, end_time=19)
        
        # print(agent.get_agent_name(), tt) # Only for testing

        # if is_event_day:
        #     tt = addEvent_to_agnt_tt(env, agent, tt, event_details.loc[event_indices[0]])
        
        # print(agent.get_agent_name(), tt) # Only for testing
        # print()

        agent.set_timeTable(tt)

        if not is_event_day:
            if writer is not None:
                writer.write(f"Agent {agent.get_agent_name()} >> {agent.get_timeTable()}\n")
        
        
        # print(f"Time Table generated for agent {agent.get_agent_name()} >> {tt}")
    
    if is_event_day:
        setEvents(env, attnd_agnts, event_indices, event_details)

        if writer is not None:
            for agent in Agents:
                writer.write(f"Agent {agent.get_agent_name()} >> {agent.get_timeTable()}\n")

    if writer is not None:
        writer.write("\n")
    
    return None


def checkEvents():
    # print("test")
    # event_df = Loader.getSim('events.csv')
    event_df = Loader.getSim2("Event Plan")
    event_days = event_df['day'].unique()

    if Time.get_DAY() in event_days:
        return True
    else:
        return False
    

def getEventIndices():
    # event_df = Loader.getSim('events.csv')
    event_df = Loader.getSim2("Event Plan")
    event_day = Time.get_DAY()
    event_indices = event_df[event_df['day'] == event_day].index.tolist()
    
    return event_indices


def getEventDetails(indices):
    # event_df = Loader.getSim('events.csv')
    event_df = Loader.getSim2("Event Plan")
    event_day = Time.get_DAY()
    event_details = event_df.loc[indices]
    
    return event_details


def select_agents_for_event(agents: list, event_inds: list, event_details: pd.DataFrame):
    
    agnts_to_attnd = {}

    for indx in event_inds:
        event = event_details.loc[indx]

        attnd_clss_all_agnts = []
        req_cnt = 0
        attnd_lst = []
        
        for agnt in agents:
            if agnt.get_agent_class() == event['attendees']:
                attnd_clss_all_agnts.append(agnt)
        
        req_cnt = int(len(attnd_clss_all_agnts) * event['attendee_perc'] / 100)

        for i in range(req_cnt):
            rand_index = random.randrange(len(attnd_clss_all_agnts))
            attnd_lst.append(attnd_clss_all_agnts[rand_index])
            attnd_clss_all_agnts.pop(rand_index)
        
        agnts_to_attnd[indx] = attnd_lst
    
    return agnts_to_attnd


def setEvents(env, event_attendees: dict, event_inds: list, event_dets: pd.DataFrame):
    
    for indx in event_inds:
        event = event_dets.loc[indx]
        attnd_agnts = event_attendees[indx]

        for agnt in attnd_agnts:
            agnt_tt = agnt.get_timeTable()
            agnt_tt = addEvent_to_agnt_tt(env, agnt, agnt_tt, event)
            agnt.set_timeTable(agnt_tt)

    return None


def addEvent_to_agnt_tt(env, agent, timetable, event_dets):

    # event_df = Loader.getSim('events.csv')
    # event_df = Loader.getSim2("Event Plan")

    # Current event (Only considering the first event for now)
    curr_event = event_dets.copy()
    event_name = curr_event['ev_name']
    event_location = curr_event['location']
    att_agnt_clss = curr_event['attendees']
    ev_start_time = int(curr_event['st_time'] * 60)
    event_dur = int(curr_event['dur'] * 60) # NOTE: Start times and durations currently given as hours and not minutes
    ev_end_time = ev_start_time + event_dur
    # NOTE: Do the event end times need to be sanity checked to ensure it doesnt exceed midnight? 

    agnt_tt = timetable
    agnt_start_times = []
    agnt_end_times = []

    if agent.get_agent_class() == att_agnt_clss:
        print(f"Agent {agent.get_agent_name()} is attending the event - {event_name} at {event_location}")

        # print(agnt_tt) # Only for testing

        tt_ev_ind = None

        for i in range(len(agnt_tt[1])):
            agnt_start_times.append(agnt_tt[1][i][0])
            agnt_end_times.append(agnt_start_times[i] + agnt_tt[1][i][1])

        # print(agnt_start_times,agnt_end_times) # Only for testing

        for i in range(len(agnt_start_times)):
            
            if(ev_start_time <= agnt_start_times[i]):
                agnt_tt[0].insert(i, event_location)
                agnt_tt[1].insert(i, (ev_start_time, event_dur))
                agnt_start_times.insert(i, ev_start_time)
                agnt_end_times.insert(i, ev_end_time)
                tt_ev_ind = i
                break

            if(i == len(agnt_start_times) - 1):
                if(ev_start_time > agnt_start_times[i]):
                    agnt_tt[0].append(event_location)
                    agnt_tt[1].append((ev_start_time, event_dur))
                    agnt_start_times.append(ev_start_time)
                    agnt_end_times.append(ev_end_time)
                    tt_ev_ind = i + 1
                    break
            
        # Adjust end_time/duration of previous loc, return to previous loc if event duration too short
        if not (tt_ev_ind == 0):
        # Not necessary if event is first in timetable
            if not (agnt_end_times[tt_ev_ind - 1] == agnt_start_times[tt_ev_ind]):
            # Not necessary if end time of previous loc matches start time of event
                '''
                Courses of action if prev loc end time is,
                a. before event start time
                b. between event start time and event end time
                (both a and b can be combined as prev loc end time before event end time)
                c. after event end time
                '''
                if (agnt_end_times[tt_ev_ind - 1] <= agnt_end_times[tt_ev_ind]):
                # Conditions a and b combined

                    # Change previous loc end time/dur to match event start time 
                    agnt_end_times[tt_ev_ind - 1] = agnt_start_times[tt_ev_ind]
                    
                    new_dur = agnt_end_times[tt_ev_ind - 1] - agnt_start_times[tt_ev_ind - 1]
                    agnt_tt[1][tt_ev_ind - 1] = (agnt_start_times[tt_ev_ind - 1], new_dur)

                
                if (agnt_end_times[tt_ev_ind - 1] > agnt_end_times[tt_ev_ind]):
                # Condition c

                    # Add a second instance of previous location if event duration too short to cover location visit
                    new_st = agnt_end_times[tt_ev_ind]
                    new_end = agnt_end_times[tt_ev_ind - 1]
                    new_dur = new_end - new_st
                    
                    agnt_tt[0].insert(tt_ev_ind + 1, agnt_tt[0][tt_ev_ind - 1])
                    agnt_tt[1].insert(tt_ev_ind + 1, (new_st, new_dur))
                    agnt_start_times.insert(tt_ev_ind + 1, new_st)
                    agnt_end_times.insert(tt_ev_ind + 1, new_end)

                    # Change end time of first instance of previous loc end time/dur to match event start time 
                    agnt_end_times[tt_ev_ind - 1] = agnt_start_times[tt_ev_ind]
                    
                    new_dur = agnt_end_times[tt_ev_ind - 1] - agnt_start_times[tt_ev_ind - 1]
                    agnt_tt[1][tt_ev_ind - 1] = (agnt_start_times[tt_ev_ind - 1], new_dur)


        # Adjust start_time of next loc, remove locs if event duration too long
        if not (tt_ev_ind == len(agnt_tt[0]) - 1):
        # Not necessary event is last in timetable
            if not (agnt_start_times[tt_ev_ind + 1] == agnt_end_times[tt_ev_ind]):
            # Not necessary if start time of next loc matches end time of event
                '''
                Courses of action if next loc start time is,
                a. after event end time
                b. between event start time and end time
                (Both a and b can be combined as next loc start time after event end time)
                c. Also need to remove loc visits that are fully overwritten by the event
                '''

                while (agnt_end_times[tt_ev_ind + 1] <= agnt_end_times[tt_ev_ind]):
                # Condition c
                    
                    # Remove all loc visits fully overwritten by the event
                    agnt_tt[0].pop(tt_ev_ind + 1)
                    agnt_tt[1].pop(tt_ev_ind + 1)
                    agnt_end_times.pop(tt_ev_ind + 1)
                    agnt_start_times.pop(tt_ev_ind + 1)
                    
                    if (len(agnt_end_times) == tt_ev_ind + 1):
                        break 
                

                if (agnt_start_times[tt_ev_ind + 1] >= agnt_start_times[tt_ev_ind]):
                # Conditions a and b combined

                    # Change next loc start time to event end time
                    agnt_start_times[tt_ev_ind + 1] = agnt_end_times[tt_ev_ind]

                    new_dur = agnt_end_times[tt_ev_ind + 1] - agnt_start_times[tt_ev_ind + 1]
                    agnt_tt[1][tt_ev_ind + 1] = (agnt_start_times[tt_ev_ind + 1], new_dur)
    

        # NOTE: Three loops per agent (efficiency?)
        # print(agnt_tt) # Only for testing
        # print()

    return agnt_tt



if __name__ == "__main__":
    # Test the abobe timetable V2 code here
    from Agents2 import Agents, agent_create
    from Clock import Time

    Time.init()
    Time.DAY = 9
    env = LaunchEnvironment()
    agents = agent_create(env, use_def_perc=True)
    Loader.init_sub_probabilities()
    print(Loader.sub_probMat.keys())

    from time import time

    start = time()
    initTimeTables(env, list(agents.values()), sim_events=True)

    # for agent in list(agents.values()):
    #     print(agent.get_agent_name())
    #     tt = generateTimeTableV2(env, agent)
    #     print(tt)
    #     agent.set_timeTable(tt)
    #     print('\n')
    #
    # Time.DAY = 7
    #
    #
    # agent = agents['Student_1']
    # for i in range(50):
    #     tt = generateTimeTableV2(env, agent)
    #     print(tt)

    end = time()
    print(f"--------------------- Time taken: {end-start} ---------------------")

    
