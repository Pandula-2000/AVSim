from typing import Any
import pandas as pd
import random
import shapely

# Import Classes
from Clock import Time
from DataLoader import Loader
from Environment import *
from disease_state_enum import Disease_State


# np.random.seed(42)

# from Bus_plan import Bus_plan


class Agents:
    """
    Generates each Agent, stores them.

    Class Attributes:
        total_agents                    :   Total number of agents in the simulation.
        class_df                        :   Data frame of Agent Details.

    Class Methods:
        get_def_perc(agent_class)       :   Get default percentage of agent generation for each class.

    """
    total_agents = 0
    # Note: Only the test classes are initiated for now!
    # class_df = Loader.getSim('person_classes.csv').reset_index()
    # class_df = Loader.getSim('person_classes_test.csv').reset_index()
    class_df = Loader.getSim2('Agent Classes test').reset_index()
    rel_sus = Loader.getSim2('Relative Susceptability').reset_index()

    sus_age_ranges = rel_sus["Age Range"].apply(lambda x: tuple(map(int, x.split(','))))

    def __init__(self,
                 agent_class: str,
                 agent_sub_class: str,
                 agent_name: str):
        """
        To Load each Agent
        :param agent_class          : Occupation class of Agent
        :param agent_name           : Name assigned of the Agent
        """
        agent_class_index = Agents.class_df.index[Agents.class_df['p_class'] == agent_class]

        self._agent_class = agent_class
        self._agent_sub_class = agent_sub_class

        self._agent_name = agent_name

        # self._agent_sub_cl_flag = False
        # self._agent_sub_class_count = 0

        self._init_location_class = Agents.class_df.loc[agent_class_index, ['init_loc']].squeeze()
        self._work_location_class = Agents.class_df.loc[agent_class_index, ['w_loc']].squeeze()
        self._age_min = Agents.class_df.loc[agent_class_index, ['age_min']].squeeze()
        self._age_max = Agents.class_df.loc[agent_class_index, ['age_max']].squeeze()
        self._agent_type = Agents.class_df.loc[agent_class_index, ['agnt_type']].squeeze()

        self._gamma_home = Agents.class_df.loc[agent_class_index, ['gamma_home']].squeeze()
        self._gamma_work = Agents.class_df.loc[agent_class_index, ['gamma_work']].squeeze()

        self._age = random.randint(self._age_min, self._age_max)
        age_sus_ind = Agents.sus_age_ranges.apply(lambda x: x[0] <= self._age <= x[1]).idxmax()

        self._current_location_class = self._init_location_class
        # NOTE: Let ID be a unique identifier with
        # FIXME: Why do we need an Agent ID ?
        self.ID = f"agent_{Agents.total_agents}"

        # NOTE: ---------------------------- These are related to Route Planning ---------------------------------------
        self._public_transport_vehicle = None  # Bus, train etc (Objects)
        self._use_pvt_vehicle = False
        self._pvt_transport_counter = 0
        self._tuk_timer = 0

        self._in_transition = False
        self._in_bus = False
        self._is_walk = False
        self._in_tuktuk = False
        self._pvt_trans_flag = False

        self.coordinates = None  # shapely.Point([x, y]) --> This is the geographical location.
        # Coordinates of the agent in the visited location.
        self.x = 0
        self.y = 0
        self._init_location = None  # Home_45
        self._work_location = None  # School_23
        self._current_location = None

        # NOTE :---------- ALso related to Route planning but, should be specified after init of the agent.-------------
        self._next_location_class = None
        self._next_location = None
        self._next_locations = []
        self._next_zone = None

        # Bimodelity related.
        self._stay_duration = 0
        self._timeTable = []

        # Timers
        self._poll_timer = 0
        self._walk_timer = 0

        # NOTE: ----------------------------------- Common to both diseases --------------------------------------------
        self.vaccinated = False
        # NOTE: -------------------------------- Vector Borne Disease Related -----------------------------------------------
        self.patch = None
        self.vaccine_weight = 0.95
        self.hygiene_weight = 0.05
        # Note: ------------------------------------ Air Borne Disease Related -----------------------------------------
        self.vacc_immunity = 0  # Set at interventionEngine
        self.hygiene_immunity = 0.95  # Could be also set at agent init class wise. Currently a const.
        self.rel_susceptibility = Agents.rel_sus.loc[age_sus_ind, 'Relative Susceptability']
        self.susceptibility = Loader.roh * self.rel_susceptibility  # Set to proper value

        self.transport_susceptibility = Loader.transport_roh * self.rel_susceptibility  # Set to proper value

        self.quarantined = False
        self.hospitalized = False  # for VB disease patients
        self.airBorneIdentified = False

        self.disease_state = Disease_State.SUSCEPTIBLE.value
        self.next_state = None
        self.state_timer = 0

        '''
         ----------------- STATES -----------------
         1: Susceptible,
         2: Incubation,
         3: Infectious,
         4: Mild, 
         5: Severe,
         6: Critical,
         7: Asymptotic,
         7: Recovered,
         9: Dead
        '''
        Agents.total_agents += 1

    def __str__(self):
        return f"{self._agent_name} | {self._agent_sub_class} | CL: {self._current_location} | NL:{self._next_location} | NLs:{self._next_locations} || SD:{self._stay_duration} | B:{self._in_bus} | W:{self._is_walk} | Tr:{self._in_transition} | PT:{self._poll_timer} | WT:{self._walk_timer} | TT:{self._tuk_timer}"

    def sleepAgent(self):
        """
        Do Nothing
        :return: None
        """
        # Important: Because when at sleep need to freeze agents.
        # self.decrement_stay_duration()
        return None

    def resetAgent(self, env_object):
        """
        Reset the agent to the initial state.
        This runs at the beginning of each day.
        :return: None. Sets the agent to the initial state.
        """
        if self._current_location != self._init_location:
            # print(self)
            if not self._in_transition:
                self.remove_from_environment(env_object, self._current_location)
                self.add_to_environment(env_object, self._init_location)
                self._stay_duration = 0
            elif self._in_transition:
                # self.remove_from_environment(env_object, self._current_location)
                self.add_to_environment(env_object, self._init_location)
            else:
                print("ERROORR")
        else:
            if self._in_transition:
                self.add_to_environment(env_object, self._init_location)

        self.set_curr_loc(self._init_location)
        self.set_transit_flag(False)
        self.set_walk_flag(False)
        self.set_in_bus_flag(False)
        self.set_public_transport_vehicle(None)
        self.set_next_location(None)
        self.set_next_locations([])

    def set_agent_x_y(self, x, y):
        """
        Set the agent's x and y coordinates.
        :param x, y: The x and y coordinates of the agent.
        :return: None
        """
        self.x, self.y = x, y

    def get_agent_x_y(self):
        """
        Get the agent's x and y coordinates.
        :return: The x and y coordinates of the agent.
        """
        return self.x, self.y

    def updateAgentV1(self, env, time):
        """
        * ONLY triggers when Stay Duration is zero.
        * This uses the pre generated timetable for the agent at the start if the day.
        ----------------------- STEPS -----------------------
        1. Do not update the agent if the time is between 1am and 5am.
        2. If the stay duration is 0
            2.1. Remove the agent from the current location.

            2.2. update the agent's next location and stay duration.
                2.2.1. If timetable is over, send the agent back home.
                    2.2.1.1. If agent has a pvt vehicle, use that to go home.
                    2.2.1.2. ELSE, If the agent is walking to the next location (Inside same Zone), set the walk flag to True and set the walk timer.

                2.2.2. If timetable is not over, update the agent's next location and stay duration.
                    2.2.2.1. If agent has a pvt vehicle, use that to go home.
                    2.2.2.2. ElSE, If the agent is walking to the next location (Inside same Zone), set the walk flag to True and set the walk timer.

                2.3. If the agent is staying at the same location, add the agent back to the Current location.


        :param env  : Environment object
        :param time : Current time of the simulation
        :return     : None
        """
        # 1. Do not update the agent if the time is between 1am and 5am.
        if 1 <= time <= 5 * 60:
            return None
        # 2. If the stay duration is 0
        if self._stay_duration == 0:
            # print(f"================= Stay duration Expired! =============================")
            # print(time, self._stay_duration, self.get_current_location())

            # print(self._current_location)
            # print(f"{time} | removed agent from {self.get_current_location()}")
            # NOTE: It is okey to remove the agent from the location as the agent is not there anymore. But if the same location is generated, the agent will be added again.
            # curr = self._current_location
            #
            # print(
            #     f"{time} | Current Loc: ({curr} --> {env.get_parent(curr)[0]} --> {env.get_parent(env.get_parent(curr)[0])[0]})| Next Loc: ({self._next_location}) | Stay: {self.get_stay_duration()} | In bus: {self.get_in_bus()} "f"| Transit: {self.get_transition()} | Walk Flag: {self.get_is_walk()} | Poll Timer: {self.get_poll_timer()} | Walk Timer: {self.get_walk_timer()}")

            # 2.1 Remove the agent from the current location.
            try:
                self.remove_from_environment(env, self._current_location)
                # print(f"{time} | removed agent from {self.get_current_location()}")
            except:
                print("ERRORRRR")
                # print(f"{self._timeTable}")
                print(
                    f"{time} | --------------------- tried to removed {self._agent_name} from {self.get_current_location()}| {self._next_location}")

            # 2.2 -------------------- update the agent's next location and stay duration ------------------------------
            # 2.2.1 If timetable is over, send the agent back home.
            if len(self._timeTable[0]) == 0:
                # This is the end of the agents schedule. Send home.
                # print('DAY IS OVER!!! Agent is Heading Back Home.')
                # 2.2.1.1. If agent has a pvt vehicle, use that to go home.
                if self._use_pvt_vehicle:
                    # print(f"Using Private Vehicle")
                    self.set_pvt_trans_flag(True)
                    self._next_locations = [self._current_location]
                    self._next_location = self._next_locations[0]
                    self._next_locations = self._next_locations[1:]
                    self._stay_duration = 1440 - time + 60
                    timer = env.calculate_travel_time(self.get_next_location(), self.get_current_location())
                    self.set_pvt_transport_counter(timer)

                else:
                    self._next_locations = env.get_shortest_path(self._current_location,
                                                                 self._init_location.split('_')[0], self)
                    self._next_location = self._next_locations[0]
                    self._next_locations = self._next_locations[1:]
                    self._stay_duration = 1440 - time + 60
                    # 2.2.1.1 If the agent is walking to the next location (Inside same Zone), set the walk flag to True and set the walk timer.
                    if env.is_same_zone(self.get_current_location(), self.get_next_location()) and (
                            self._next_location != self._current_location):  # 'and' to check if they stay in same Zone
                        # print(f"Walking to the next location...")
                        self.set_walk_flag(True)
                        walkTime = env.calculate_travel_time(self.get_next_location(), self.get_current_location())
                        # print(f"Walk Time is....................... {walkTime}")
                        self.set_walk_timer(walkTime)
                    else:
                        self.set_walk_flag(False)
            # NOTE: update the agent location and the stay here.
            # 2.2.2. If timetable is not over, update the agent's next location and stay duration.
            else:  # day has not ended yet

                # print('Day is not over')
                # 2.2.2.1. If agent has a pvt vehicle, use that to go home.
                if self._use_pvt_vehicle:
                    # print(f"Using Private Vehicle")
                    self.set_pvt_trans_flag(True)
                    self._next_locations = [self._timeTable[0][0]]
                    self._next_location = self._next_locations[0]
                    self._next_locations = self._next_locations[1:]

                    self._stay_duration = self._timeTable[1][0][1]

                    # Update the timetable
                    self._timeTable[0] = self._timeTable[0][1:]
                    self._timeTable[1] = self._timeTable[1][1:]

                    timer = env.calculate_travel_time(self.get_next_location(), self.get_current_location())
                    self.set_pvt_transport_counter(timer)

                else:
                    self._next_locations = env.get_shortest_path(self._current_location,
                                                                 self._timeTable[0][0].split('_')[0], self)
                    # print(self._current_location, self.._timeTable[0][0].split('_')[0])
                    # print(self._next_locations)
                    # print(self._timeTable[0][0].strip('_'))
                    self._next_location = self._next_locations[0]
                    self._next_locations = self._next_locations[1:]

                    self._stay_duration = self._timeTable[1][0][1]

                    # Update the timetable
                    self._timeTable[0] = self._timeTable[0][1:]
                    self._timeTable[1] = self._timeTable[1][1:]
                    # 2.2.2.1. If the agent is walking to the next location (Inside same Zone), set the walk flag to True and set the walk timer.
                    if env.is_same_zone(self.get_current_location(), self.get_next_location()) and (
                            self._next_location != self._current_location):
                        # print(f"Walking to the next location...")
                        self.set_walk_flag(True)
                        walkTime = env.calculate_travel_time(self.get_next_location(), self.get_current_location())
                        # print(f"Walk Time is....................... {walkTime}")
                        self.set_walk_timer(walkTime)
                    else:
                        self.set_walk_flag(False)

            # 2.3 If the agent is staying at the same location, add the agent back to the Current location.
            if self._current_location == self._next_location:  # fixme: do not hardcode 0-5am
                # print(f"Staying at the same location.")
                # print(f"{time} | Stay at same location. So agent added to {self.get_next_location()}")
                # NOTE: Stay at the same location. Agent should be added to the environment now.
                # env.add_agent(self.get_next_location(), self)
                self.add_to_environment(env, self._next_location)

                self.set_transit_flag(False)
                self.set_walk_flag(False)
            else:
                self.set_transit_flag(True)
                self._poll_timer = 0

    def updateAgentV2(self, env, time, t_end):
        """
        Important: This is for Vector Borne Disease Simulation
        1. If time < t_start or time > t_end, agent is at resting place.
        2. Else, get the next location and update the agent location.
        :param time:
        :return: None
        """
        if self._stay_duration <= 0:
            if len(self._timeTable[0]) == 0:
                # This is the end of the agents schedule. Send hom home.

                # env.remove_agent(self.get_current_location(), self)
                # env.add_agent(self.get_init_loc(), self)
                self.remove_from_environment_VB(env, self.get_current_location())
                self.add_to_environment_VB(env, self.get_init_loc())

                self._current_location = self._init_location
                self._stay_duration = 1440 - time
                # print(f"----- End of time table. Going Back Home -------")
            else:
                self._next_location = self._timeTable[0][0]
                self._stay_duration = self._timeTable[1][0][1]
                # ----------------- Update the timetable -------------------
                self._timeTable[0] = self._timeTable[0][1:]
                self._timeTable[1] = self._timeTable[1][1:]
                # print(f"----- Location change: {self._current_location} --> {self._next_location} -------")
                # ----------------------------------------------------------
                if self._current_location != self._next_location:
                    # env.remove_agent(self.get_current_location(), self)
                    # env.add_agent(self.get_next_location(), self)
                    self.remove_from_environment_VB(env, self.get_current_location())
                    self.add_to_environment_VB(env, self.get_next_location())

                self._current_location = self._next_location
        self.decrement_stay_duration()

    # Note: ----------------- Add/Remove agents from Environment and Epidemic Status Updater ---------------------------
    def add_to_environment(self, env, zone, simulation=Loader):
        env.add_agent(zoneName=zone, agent=self)
        env.add_agent_to_state(zoneName=zone, state=self.disease_state, agent=self)
        # FIXME: Looks like it was a bad idea to set entrance at the center of the zone.
        #self.set_agent_x_y(env.get_side_length(zone) / 2, env.get_side_length(zone) / 2)
        self.set_agent_x_y(random.randint(1, env.get_side_length(zone)),
                           random.randint(1, env.get_side_length(zone)))
        self.set_coordinates(env.get_centroid(zone))

    def remove_from_environment(self, env, zone, simulation=Loader):
        env.remove_agent(zoneName=zone, agent=self)
        env.remove_agent_from_state(zoneName=zone, state=self.disease_state, agent=self)
        # This is not necessary, but set coordinates to (None,None)
        self.set_agent_x_y(0, 0)
        self.reset_coordinates()

    def add_to_environment_VB(self, env, zone, simulation=Loader):
        env.add_agent_VB(zone, agent=self)
        self.set_coordinates(env.get_centroid(zone))

    def remove_from_environment_VB(self, env, zone, simulation=Loader):
        env.remove_agent_VB(zone, agent=self)
        self.reset_coordinates()

    def set_disease_state(self, env, state):
        if self._in_transition:
            self.disease_state = state
        elif self.quarantined:
            self.disease_state = state
        else:
            env.remove_agent_from_state(self._current_location, self.disease_state, self)
            self.disease_state = state
            env.add_agent_to_state(self._current_location, state, self)
            
    def update_VB_disease_state(self, curr_state, next_state, hospitalized=False):
        self.disease_state = next_state
        
        if not hospitalized:
            self.patch.agent_states_count[curr_state] -= 1
            self.patch.agent_states_count[next_state] += 1
        

    # NOTE: --------------------------- AirBorne Disease related--------------------------------------------------------
    def can_agent_transmit(self):
        """
        For airborne disease.
        :return: If agent can or not transmit the disease (TRUE/FALSE).
        """
        if self.get_disease_state() in (3, 4, 5, 6, 7):
            return True
        else:
            return False

    def is_agent_symptomatic(self):
        """
        For airborne disease.
        :return: If agent shows symptoms (TRUE/FALSE).
        """
        if self.get_disease_state() in (5, 6):
            return True
        else:
            return False

    def decide_PCR(self):
        """
        For airborne disease.
        :return: If agent should be tested (TRUE/FALSE).
        """
        test_prob = {'Mild': 0.8,
                     'Severe': 0.9,
                     'Critical': 1.0}
        if self.get_disease_state() == 4:
            if np.random.random(1)[0] < test_prob['Mild']:
                return True
            else:
                return False
        elif self.get_disease_state() == 5:
            if np.random.random(1)[0] < test_prob['Severe']:
                return True
            else:
                return False
        elif self.get_disease_state() == 6:
            if np.random.random(1)[0] < test_prob['Critical']:
                return True
            else:
                return False
        else:
            return False

    def is_agent_recovered(self):
        """
        For airborne disease.
        :return: If agent has recovered (TRUE/FALSE).
        """
        if self.get_disease_state() == 8:
            return True
        else:
            return False

    def is_agent_dead(self):
        """
        For airborne disease.
        :return: If agent has died (TRUE/FALSE).
        """
        if self.get_disease_state() == 9:
            return True
        else:
            return False

    def set_susceptibility(self, susceptibility):
        """
        Set the susceptibility of the agent.
        Set to zero will stop the agent from getting infected.
        :param susceptibility:
        :return:
        """
        self.susceptibility = susceptibility

    def set_immunity(self, immunity):
        self.immunity = immunity

    def get_immunity(self):
        return self.immunity

    def set_hygiene(self, hygiene):
        self.hygiene = hygiene

    def get_hygiene(self):
        return self.hygiene

    def set_quarantined(self, quarantine: bool):
        self.quarantined = quarantine

    def get_quarantined(self):
        return self.quarantined

    def set_hospitalized(self, hospitalized: bool):
        self.hospitalized = hospitalized

    def get_hospitalized(self):
        return self.hospitalized

    def set_airBorneIdentified(self, identified: bool):
        self.airBorneIdentified = identified

    def get_airBorneIdentified(self):
        return self.airBorneIdentified

    @property
    def infection_probability_AirBorne(self):
        return round(self.susceptibility * (
                1 - (self.vaccine_weight * self.vacc_immunity) - (self.hygiene_weight * self.hygiene_immunity)), 5)

    @property
    def transport_infection_probability_AirBorne(self):
        return round(self.transport_susceptibility * (
                1 - (self.vaccine_weight * self.vacc_immunity) - (self.hygiene_weight * self.hygiene_immunity)), 5)

    # NOTE : --------------------------- Common to both diseases -------------------------------------------------------
    def set_vaccinated(self, vaccinated: bool):
        self.vaccinated = vaccinated

    def get_vaccinated(self):
        return self.vaccinated

    def vaccinate(self, vaccImmunity):
        """
        Sets vaccine Immunity and sets the vaccinated flag to True.
        :param vaccImmunity : Immunity gained from the vaccine (0,1].
        :return             : None
        """
        self.set_vaccinated(True)
        self.vacc_immunity = vaccImmunity

    # NOTE: --------------------------- VectorBorne Disease related-----------------------------------------------------
    def update_patch_exposure_count(self, env):
        self.patch.update_exposure_count(env)
    # Note: -------------------------------- General Methods -----------------------------------------------------------

    def set_agent_class(self, cls):
        """
        Set agent class as tc/dc/st/...
        """
        self._agent_class = cls

    def set_work_loc_class(self, cls):
        """
        Set worklocation class as School/Bank/...
        :param cls:
        :return:
        """
        self._work_location_class = cls

    def set_init_loc(self, init_loc):
        """
        Set initial location of the agent
        """
        self._init_location = init_loc

    def set_work_loc(self, work_loc):
        """
        Set work location of the agent
        """
        self._work_location = work_loc

    def set_curr_loc(self, curr_loc):
        """
        Set current location of the agent
        """
        self._current_location = curr_loc

    def set_route_plan(self, route_plan):
        """
        Set the route plan
        """
        self._route_plan = route_plan

    def set_coordinates(self, point: shapely.Point):
        """
        Set Coordinates x,y (As a Shapely Point object)
        """
        self.coordinates = point

    def reset_coordinates(self):
        self.coordinates = None

    def set_next_location_class(self, next_loc_class):
        """
        Set Next location Class pulled from Bimodelity.
        """
        self._next_location_class = next_loc_class

    def set_next_location(self, next_loc):
        """
        Set Next location target pulled from Bimodelity then Determined from Environment.
        """
        self._next_location = next_loc

    def set_next_locations(self, next_locs: list):
        """
        Set Next locations.
        """
        self._next_locations = next_locs

    def set_next_zone(self, zone):
        """
        Set Next location target pulled from Bimodelity then Determined from Environment.
        """
        self._next_zone = zone

    def set_stay_duration(self, stay_duration):
        """
        Set Stay Duration pulled from Bimodelity.
        """
        self._stay_duration = stay_duration

    def decrement_stay_duration(self):
        self._stay_duration = self._stay_duration - Time._resolution

    def set_transit_flag(self, Transit):  # NOTE: This is a Flag
        """
        Set Transition flag to True of False
        """
        self._in_transition = Transit

    def set_walk_flag(self, walk):  # NOTE: This is a Flag
        """
        Set Transition flag to True of False
        """
        self._is_walk = walk

    def set_in_bus_flag(self, inBus):  # NOTE: This is a Flag
        """
        Set Transition flag to True of False
        """
        self._in_bus = inBus

    def set_in_tuktuk_flag(self, inTuktuk):  # NOTE: This is a Flag
        """
        Set Transition flag to True of False
        """
        self._in_tuktuk = inTuktuk

    def set_public_transport_vehicle(self, transportVehicle):
        """
        Set public transport vehicle object to the agent
        """
        self._public_transport_vehicle = transportVehicle

    def set_pvt_transport_counter(self, counter: int):
        self._pvt_transport_counter = counter

    def set_tuktuk_timer(self, counter: int):
        self._tuk_timer = counter

    def set_pvt_trans_flag(self, pvt_trans: bool):
        """
        Set private transport flag to True of False
        """
        self._pvt_trans_flag = pvt_trans

    def set_use_pvt_vehicle(self, use_pvt_vehicle: bool):
        self._use_pvt_vehicle = use_pvt_vehicle

    def get_gamma_home(self):
        return self._gamma_home

    def get_gamma_work(self):
        return self._gamma_work

    def get_pvt_trans_flag(self):
        return self._pvt_trans_flag

    def get_use_pvt_vehicle(self):
        return self._use_pvt_vehicle

    def decrement_pvt_transport_counter(self):
        self._pvt_transport_counter -= 1

    def decrement_tuktuk_timer(self):
        self._tuk_timer -= 1

    def get_pvt_transport_counter(self):
        return self._pvt_transport_counter

    def get_tuktuk_timer(self):
        return self._tuk_timer

    '''
    AIR BONE DISEASE RELATED FUNCTIONS
    '''

    def set_next_state(self, state):
        self.next_state = state

    def get_next_state(self):
        return self.next_state

    def set_state_timer(self, timeToSet):
        self.state_timer = timeToSet

    def decrement_state_timer(self, decrementBy):
        self.state_timer -= decrementBy

    def get_disease_state(self):
        return self.disease_state

    def get_next_locations(self):
        return self._next_locations

    def can_agent_transmit(self):
        state = self.disease_state
        if state in (3, 4, 5, 6):
            return True
        else:
            return False

    def get_state_timer(self):
        return self.state_timer

    def get_in_tuktuk_flag(self):  # NOTE: This is a Flag
        """
        Return tukTuk flag
        """
        return self._in_tuktuk

    # -------------------------------------------------------------------------------------------- #

    def set_walk_timer(self, time):
        self._walk_timer = time

    def set_timeTable(self, tt):
        self._timeTable = tt

    def decrement_walk_timer(self):
        self._walk_timer -= 1

    def get_sub_cls_statistics(self, day, loader=Loader):
        """
        Return the prob mat and std mat of a given subclass
        1. Check if it is a weekend or not
            1.1 If it is a weekend, check if the holiday subclass is available in the dictionary
            1.2 If it is not available, use the regular subclass
        2. If it is a weekday, use the regular subclass

        subClzName  : name of the sub clz --> eg: ['an_cluster0', 'an_cluster1']
        day         : monday as 1 and so on
        loader      : Loader object
        returns    : probMat, stdMat, holiday_available
        """
        holiday_available = False
        subClzName = self._agent_sub_class
        # print(day)
        if day == 6 or day == 7:
            # print('weekend')
            first_underscore_index = subClzName.find('_')
            clsName = subClzName[0:first_underscore_index + 1]
            clsHoliday = clsName + 'holiday'
            # print(clsHoliday)
            if clsHoliday in loader.sub_probMat:
                # print(f"'{clsHoliday}' is available in the dictionary.")
                # print(Loader.getSubProbMat(clsHoliday))
                # print(Loader.getSubStdMat(clsHoliday))
                holiday_available = True
                return loader.getSubProbMat(clsHoliday), loader.getSubStdMat(clsHoliday), holiday_available
            else:
                # print(f"'{clsHoliday}' is not available in the dictionary.")
                # print(Loader.getSubProbMat(subClzName))
                # print(Loader.getSubStdMat(subClzName))
                return Loader.getSubProbMat(subClzName), Loader.getSubStdMat(subClzName), holiday_available
        else:
            # print('weekday')
            # print(Loader.getSubProbMat(subClzName))
            # print(Loader.getSubStdMat(subClzName))
            return Loader.getSubProbMat(subClzName), Loader.getSubStdMat(subClzName), None

    @classmethod
    def get_def_perc(cls, agent_class):
        """
        Get the default percentage for a given agent class.

        Parameters:
        cls (class): The class object.
        agent_class (str): The agent class.

        Returns:
        float: The default percentage for the given agent class.
        """
        agent_class_index = cls.class_df.index[cls.class_df['p_class'] == agent_class]
        def_perc = cls.class_df.loc[agent_class_index, ['default_percentage']].squeeze()

        return def_perc

    @classmethod
    def get_agent_type(cls, agent_class):
        """
        Get the agent type(adult or child) based on the agent class.

        Parameters:
        - cls: The class object.
        - agent_class: The agent class to retrieve the agent type for.

        Returns:
        - agent_type: The agent type corresponding to the given agent class.
        """
        agent_class_index = cls.class_df.index[cls.class_df['p_class'] == agent_class]
        agent_type = cls.class_df.loc[agent_class_index, ['agnt_type']].squeeze()

        return agent_type

    @classmethod
    def get_prvt_trans_perc(cls, agent_class):
        """
        Get the private transport percentage for a given agent class.

        Parameters:
        - cls: The class object.
        - agent_class: The agent class to retrieve the private transport percentage for.

        Returns:
        - prvt_trans_perc: The private transport percentage corresponding to the given agent class.
        """
        agent_class_index = cls.class_df.index[cls.class_df['p_class'] == agent_class]
        prvt_trans_perc = cls.class_df.loc[agent_class_index, ['prvt_trans_perc']].squeeze()

        return prvt_trans_perc

    def get_agent_class(self):
        """
        Get the agent class of the agent
        """
        return self._agent_class

    def get_agent_name(self):
        return self._agent_name

    def get_init_loc(self):
        """
        Get initial location of the agent
        """
        return self._init_location

    @classmethod
    def get_agent_sub(cls, agent_class):
        """
        Find weather the sub class is available or not

        Parameters:
        - cls: The class object.
        - agent_class: The agent class to retrieve the agent type for.

        Returns:
        - agent_sub: True or False
        """
        agent_class_index = cls.class_df.index[cls.class_df['p_class'] == agent_class]
        agent_sub = bool(cls.class_df.loc[agent_class_index, ['sub']].squeeze())

        return agent_sub

    def get_work_loc(self):
        """
        Get work location of the agent
        """
        return self._work_location

    def get_work_loc_class(self):
        """
        Get work location class of the agent
        """
        return self._work_location_class

    def get_transition(self):
        return self._in_transition

    def get_is_walk(self):
        return self._is_walk

    def get_stay_duration(self):
        return self._stay_duration

    def get_in_bus(self):
        return self._in_bus

    def get_current_location(self):
        return self._current_location

    def get_public_transport_vehicle(self):
        return self._public_transport_vehicle

    def get_timeTable(self):
        return self._timeTable

    def get_coordinates(self):
        return self.coordinates

    def get_next_location_class(self):
        return self._next_location_class

    def get_next_location(self):
        return self._next_location

    def get_next_zone(self):
        """
        set Next location target pulled from Bimodelity then Determined from Environment.
        """
        return self._next_zone

    def get_poll_timer(self):
        return self._poll_timer

    def reset_poll_timer(self):
        self._poll_timer = 0

    def reset_tuktuk_timer(self):
        self._tuk_timer = 0

    def get_walk_timer(self):
        return self._walk_timer

    def increment_poll_timer(self):
        self._poll_timer += 1


def get_agent_tot(env_object):
    home_lst = env_object.get_zones('Home')
    # print('home list', len(home_lst))
    agent_tot = 0
    agent_per_home = {}
    # Note: Consider removing the dic later!!!
    for home in home_lst:
        n = random.randint(3, 5)
        # n = 2 ##### Fixme: Temporarily set to a constant. Change before proper execution.
        agent_per_home[home] = n
        env_object.increment_people_count(home, n)
        agent_tot += n

    # print(agent_tot) ## Debugging (Important: This will not be the total number of agents created. as creation is done with percentages)
    # return agent_tot
    return agent_per_home, agent_tot


def assgn_prvt_trans(all_agnts: dict, agnt_cls_cnts: dict, agnts_by_cls: dict):
    """
    Assigns private transport flags to agents based on the given agent counts and agent class dictionaries. Uses predefined percentages given in the agent classes file.

    Parameters:
    - all_agnts (dict): A dictionary containing all the agents.
    - agnt_cls_cnts (dict): A dictionary containing the count of agents for each class.
    - agnts_by_cls (dict): A dictionary containing the agentnames grouped by class.

    Returns:
    None
    """

    req_cls_cnts = {}
    agnts_by_cls_cp = agnts_by_cls.copy()
    # print(agnts_by_cls_cp) ## Debugging

    for cls in agnt_cls_cnts.keys():
        prvt_perc = Agents.get_prvt_trans_perc(cls)
        req_cls_cnts[cls] = int(agnt_cls_cnts[cls] * (prvt_perc / 100))

        for i in range(req_cls_cnts[cls]):
            rand_index = random.randrange(len(agnts_by_cls_cp[cls]))
            rand_agent = agnts_by_cls_cp[cls][rand_index]

            all_agnts[rand_agent].set_pvt_trans_flag(True)

            agnts_by_cls_cp[cls].pop(rand_index)

    # print(agnts_by_cls_cp) ## Debugging


def assgn_homes(env_object, home_cnts: dict, adult_agents: dict, child_agents: dict, vb=False):
    """
    Assigns adult and child agents to homes based on the given home counts and agent dictionaries.

    Parameters:
    - home_cnts (dict): A dictionary containing the count of homes available for assignment.
    - adult_agents (dict): A dictionary containing the adult agents available for assignment.
    - child_agents (dict): A dictionary containing the child agents available for assignment.

    Returns:
    None

    Note:
    - The function modifies the input dictionaries to assign agents to homes.
    - If there are remaining homes with all slots for adults not filled, a warning message is printed.
    - If there are remaining adult agents not assigned to homes, a warning message is printed.
    - If there are remaining homes with all slots for children not filled, a warning message is printed.
    - If there are remaining child agents not assigned to homes, a warning message is printed.
    """

    # All created variables defined at start. IS OK?? (IF OK do the same to other functions)
    adult_agents_cp = adult_agents.copy()  # Currently copying the dictionaries. Might need to change later.
    child_agents_cp = child_agents.copy()
    home_cnts_ad = home_cnts.copy()
    home_cnts_ch = {}
    adult_per_home = None
    # No child_per_home variable as remaining spaces in homes will be populated by children.
    break_ad_flag = False  # Flags to break the loop if all agents are assigned to homes during execution
    break_ch_flag = False  # of home loop.

    # Assign adults to homes
    for home in list(home_cnts_ad.keys()):

        # print(len(adult_agents_cp.keys())) ## Debugging

        if (home_cnts_ad == {}) or (adult_agents_cp == {}):
            break  # Relevant error message at end of loop

        adult_per_home = 2  # Fixme:  Currently a constant. But could use random number in a range 1-4.
        # Also should be less than capacity of the home. Currently ok as manually set.

        for i in range(adult_per_home):
            if (adult_agents_cp == {}):
                break_ad_flag = True
                break  # Relevant error message at end of loop
            # IMPORTANT: Randomise the Agent professions in each Home.
            rand_agent = random.choice(list(adult_agents_cp.keys()))
            adult_agents_cp[rand_agent].set_init_loc(home)
            adult_agents_cp[rand_agent].set_curr_loc(
                home)  ## Setting home as current location as this is the initialization.

            # Setting GPS coordinates for the agent initial location
            adult_agents_cp[rand_agent].set_coordinates(env_object.get_centroid(home))

            # Note: -------------------------- Add the adult agent to the environment object ---------------------------
            if vb:
                adult_agents_cp[rand_agent].add_to_environment_VB(env_object, home)
            else:
                adult_agents_cp[rand_agent].add_to_environment(env_object, home)
            # env_object.add_agent(home, adult_agents_cp[rand_agent])
            # env_object.add_agent_to_state(home, adult_agents_cp[rand_agent].get_disease_state(),adult_agents_cp[rand_agent])
            adult_agents_cp[rand_agent].set_agent_x_y(random.randint(1, env_object.get_side_length(home) - 1),
                                                      random.randint(1, env_object.get_side_length(home) - 1))
            # print(f"Agent {adult_agents_cp[rand_agent].get_agent_name()} added to {home} | {adult_agents_cp[rand_agent].x}, {adult_agents_cp[rand_agent].y}")
            # ----------------------------------------------------------------------------------------------------------
            home_cnts_ad[home] -= 1

            adult_agents_cp.pop(rand_agent)

        if break_ad_flag:
            break

        home_cnts_ch[home] = home_cnts_ad.pop(home)

    if home_cnts_ad != {}:  # If there are remaining homes with all slots for adults not filled.
        print(f"\nWARNING: {len(home_cnts_ad.keys())} homes have less adults assigned than required. Not enough adult agents.\
              \nNote that these homes will not have children assigned to them.\n")

    if adult_agents_cp != {}:  # If there are remaining adult agents not assigned to homes.
        print(f"\nWARNING: {len(adult_agents_cp.keys())} adult agents not assigned to homes. Not enough homes.\n")

    # print(home_cnts_ad) ## Debugging
    # print(adult_agents_cp.keys())

    # Assign children to homes
    for home in list(home_cnts_ch.keys()):

        if (home_cnts_ch == {}) or (child_agents_cp == {}):
            break  # Relevant error message at end of loop

        for i in range(home_cnts_ch[home]):

            if child_agents_cp == {}:
                break_ch_flag = True
                break  # Relevant error message at end of loop

            rand_agent = random.choice(list(child_agents_cp.keys()))
            child_agents_cp[rand_agent].set_init_loc(home)
            # Setting home as current location as this is the initialization.
            child_agents_cp[rand_agent].set_curr_loc(home)

            # Setting coordinates for the agent initial location
            child_agents_cp[rand_agent].set_coordinates(env_object.get_centroid(home))

            # NOTE: ------------------------------Add the child agent to the environment object ------------------------
            # env_object.add_agent(home, child_agents_cp[rand_agent])
            # env_object.add_agent_to_state(home, child_agents_cp[rand_agent].get_disease_state(),child_agents_cp[rand_agent])
            if vb:
                child_agents_cp[rand_agent].add_to_environment_VB(env_object, home)
            else:
                child_agents_cp[rand_agent].add_to_environment(env_object, home)
            child_agents_cp[rand_agent].set_agent_x_y(random.randint(1, env_object.get_side_length(home) - 1),
                                                      random.randint(1, env_object.get_side_length(home) - 1))
            # print(f"Agent {child_agents_cp[rand_agent].get_agent_name()} added to {home} | {child_agents_cp[rand_agent].x}, {child_agents_cp[rand_agent].y}")
            # ----------------------------------------------------------------------------------------------------------
            home_cnts_ch[home] -= 1

            child_agents_cp.pop(rand_agent)

        if break_ch_flag:
            break

        home_cnts_ch.pop(home)

    if home_cnts_ch != {}:  # If there are remaining homes with all slots for children not filled.
        print(
            f"\nWARNING: {len(home_cnts_ch.keys())} homes have less children assigned than required. Not enough child agents.\n")

    if child_agents_cp != {}:  # If there are remaining child agents not assigned to homes.
        print(f"\nWARNING: {len(child_agents_cp.keys())} child agents not assigned to homes. Not enough homes.\n")

    # print(home_cnts_ch) ## Debugging
    # print(child_agents_cp.keys())

    # Returning the dictionaries containing unassigned agents and homes if necessary
    return [adult_agents_cp, child_agents_cp, home_cnts_ad, home_cnts_ch]


def assign_works(env_object, all_agents: dict):
    # df = Loader.getSim('person_classes_test.csv')
    df = Loader.getSim2('Agent Classes test')

    # work_loc_cls = ["Classroom", "Hospital", "Bank"]
    # Can't allow any duplicates. list--> set-->list
    work_loc_cls = list(set(df['w_loc'].tolist()))
    work_locs = {}

    for work_loc in work_loc_cls:
        work_locs[work_loc] = env_object.get_zones(work_loc)

    # print(work_locs) ## Debugging

    # FIXME: Currently agents are put into work locations randomly, without accounting for any max_people limit per
    #        location. Fix this !

    for agent in all_agents.keys():
        agent_obj = all_agents[agent]
        work_class = agent_obj.get_work_loc_class()
        work_loc = random.choice(work_locs[work_class])
        agent_obj.set_work_loc(work_loc)


def creat_sub_agent_number(sub_no_nested_dict, agent_cls, cls_agent_no):
    sum = 0
    for sub_class, old_percentage in sub_no_nested_dict[agent_cls].items():
        sub_cls_no = round(cls_agent_no * sub_no_nested_dict[agent_cls][sub_class] / 100)
        sub_no_nested_dict[agent_cls][sub_class] = sub_cls_no
        sum = sum + sub_cls_no

    if sum < cls_agent_no:
        extra = cls_agent_no - sum
        for sub_class, old_percentage in sub_no_nested_dict[agent_cls].items():
            sub_no_nested_dict[agent_cls][sub_class] += 1
            extra = extra - 1
            if extra == 0: break
    elif sum > cls_agent_no:
        extra = sum - cls_agent_no
        for sub_class, old_percentage in sub_no_nested_dict[agent_cls].items():
            sub_no_nested_dict[agent_cls][sub_class] -= 1
            extra = extra - 1
            if extra == 0: break

    return sub_no_nested_dict


def assign_sub_cls(agent_cls, rem_sub_no_nested_dict):
    for sub_class, old_percentage in rem_sub_no_nested_dict[agent_cls].items():
        if rem_sub_no_nested_dict[agent_cls][sub_class] == 0: continue
        rem_sub_no_nested_dict[agent_cls][sub_class] -= 1
        return rem_sub_no_nested_dict, sub_class


def RESET_AGENTS(environment, agents):
    for Agent in agents:
        Agent.resetAgent(environment)


def agent_create(env_object, use_def_perc: bool = True, req_perc: list = None, vb=False):
    """
    Create agents based on the requirements provided.

    :param env_object            : Environment object.
    :param use_def_perc          : Use default percentages for each class.
    :param req_perc              : List of percentages for each class to be generated if not using default percentages.
    """

    # df = Loader.getSim('person_classes_test.csv')
    df = Loader.getSim2('Agent Classes test')
    # sub_df = Loader.getSim('person_sub_classes_test.csv')
    sub_df = Loader.getSim2('Agent Sub Classes test')

    # print(sub_df)

    # Create the nested dictionary
    sub_percentage_nested_dict = {}

    for _, row in sub_df.iterrows():
        p_class = row['p_class']
        sub_class = row['sub_class']
        percentage = int(row['percentage'])  # Convert percentage to int

        if p_class not in sub_percentage_nested_dict:
            sub_percentage_nested_dict[p_class] = {}

        sub_percentage_nested_dict[p_class][sub_class] = percentage

    # Print the nested dictionary
    print(sub_percentage_nested_dict)

    # Number of agents in the sub classes in the sub_no_nested_dict
    sub_no_nested_dict = sub_percentage_nested_dict

    # List of agent classes to be generated.
    req_cls = df['p_class'].tolist()

    # Get total agents and agents per home
    cnt_per_home, tot_agents = get_agent_tot(env_object)

    # Get required agent counts and types
    agent_cls_counts = {}  # {'Student' : 20, 'Teacher' : 30, 'Banker' : 20, ... etc}
    agent_types = {}  # {'Student' : child', 'Teacher' : 'adult', 'Banker' : 'adult', ... etc}

    for agent_cls in req_cls:

        agent_type = Agents.get_agent_type(agent_cls)
        agent_types[agent_cls] = agent_type

        if use_def_perc:
            # Get default percentages for each class if specific percentages are not provided
            default_perc = Agents.get_def_perc(agent_cls)
            agent_cls_counts[agent_cls] = int(tot_agents * (default_perc / 100))

        else:
            # Use provided percentages
            agent_cls_counts[agent_cls] = int(tot_agents * (req_perc[req_cls.index(agent_cls)] / 100))

        # create the sug cls nested dic which has number of agents in the sub cls
        sub_no_nested_dict = creat_sub_agent_number(sub_no_nested_dict, agent_cls, agent_cls_counts[agent_cls])
        rem_sub_no_nested_dict = sub_no_nested_dict

    # Create agents
    gen_agents = {}
    adults = {}
    children = {}
    agnts_by_class = {}  # Dictionary to store agent names by class

    for agent_cls in agent_cls_counts.keys():

        agnt_cls_lst = []

        for i in range(agent_cls_counts[agent_cls]):
            agent_name = agent_cls + "_" + str(i + 1)

            rem_sub_no_nested_dict, agent_sub_cls = assign_sub_cls(agent_cls, rem_sub_no_nested_dict)
            agent = Agents(agent_cls, agent_sub_cls, agent_name)

            gen_agents[agent_name] = agent
            agnt_cls_lst.append(agent_name)
            # print(agent._agent_name)
            # print(agent._agent_class)
            # print(agent._agent_sub_class)

            # Separate adults and children
            if agent_types[agent_cls] == "adult":  # Is it ok to use strings here??
                adults[agent_name] = agent
            elif agent_types[agent_cls] == "child":
                children[agent_name] = agent
            # Is else required here??

        agnts_by_class[agent_cls] = agnt_cls_lst

    # print(agnts_by_class, len(agnts_by_class.keys())) ## Debugging
    # print(len(gen_agents.keys())) ## Debugging
    # print(adults.keys(), len(adults.keys())) ## Debugging
    # print(children.keys(), len(children.keys())) ## Debugging
    # print(rem_sub_no_nested_dict)
    # Move all created variables to top of the function???

    # Assign private transport flags for agents
    assgn_prvt_trans(gen_agents, agent_cls_counts, agnts_by_class)

    # Assign homes to agents
    unass = assgn_homes(env_object, cnt_per_home, adults, children, vb)

    unass_adults = unass[0]  # Adult agents that were not assigned to homes
    unass_children = unass[1]  # Child agents that were not assigned to homes
    # Currently not using the unassigned homes. But the dictinaries are returned if needed.

    # Removing unassigned adults and children from the generated agents
    # This will prevent them from being assigned to work locations and being used for emulation.
    for ad_agent in unass_adults.keys():
        gen_agents.pop(ad_agent)

    for ch_agent in unass_children.keys():
        gen_agents.pop(ch_agent)

    # Assign work locations to agents
    assign_works(env_object, gen_agents)

    return gen_agents


if __name__ == "__main__":
    # IMPORTANT: TO create Agents, 1. Launch the environment --> 2. run agent_create()

    # env = LaunchEnvironment()
    # agents = agent_create(env, use_def_perc=True)
    #
    # print(f"Total Agents in simulation : {len(agents)}")

    # print(type(agents))
    # for key, value in agents.items():
    #     print(f"{key.split('_')} : {value._agent_class}")
    env = LaunchEnvironment()
    agents = agent_create(env, use_def_perc=True)

    print(f"Total Agents in simulation : {len(agents)}")

    # age_immun = Loader.getSim2('Age Based Immunity').reset_index(drop=True)

    # print(age_immun.head())
    # x,y = map(int, age_immun["Age Range"][0].split(','))
    # print(x,y)
    # print(type(age_immun["Age Range"][0]))
    for key, value in agents.items():
        print(f"{key} : {value._age}, {value.rel_susceptibility}, {value.infection_probability_AirBorne}")

        # for agent in list(agents.values()):
    #     # print(f"{agent._agent_sub_class} : {agent.vaccine_weight}")
    #     print(agent._age_min)
