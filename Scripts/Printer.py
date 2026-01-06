import pathlib
import xlsxwriter
from pathlib import Path
from Clock import Time

from datetime import datetime
import platform
import psutil
import cpuinfo


class Printer:
    time = None
    day = None

    def __init__(self, path: pathlib.Path):
        self._workbook = xlsxwriter.Workbook(path)
        self._worksheet = None
        self.columns = []
        # set the cursor to the 1st row.
        self._r = 0
        self._c = 0

    @classmethod
    def update_date_time(cls, time_, day_):
        """
        Update the date and time of the simulation.
        :param time_    : Simulation time
        :param day_     : Simulation day
        :return         : None
        """
        cls.time = time_
        cls.day = day_

    # ---------------- Trajectory Printer ------------------------------------------------------------------------------

    def print_person_trajectories(self, Agents: dict, clock=Time, isFirst=False):
        """
        1. If first row, write agent names.
        2. Write the agent's current location.
        :param Agents   : Agents as a dictionary
        :param clock    : Global Time Object
        :param isFirst  : Is it the first row?
        :return         : Writes to excell file
        """
        if isFirst:
            # print(f"Printing Trajectories for Day {day} ({day_of_the_week})")
            week_dict = {1: 'Monday', 2: 'Tuesday', 3: 'Wednesday', 4: 'Thursday', 5: 'Friday', 6: 'Saturday',
                         7: 'Sunday'}
            day_of_the_week = week_dict[clock.get_dayType()]

            self._worksheet = self._workbook.add_worksheet('Day ' + str(clock.get_DAY()) + ' (' + day_of_the_week + ')')
            self._r, self._c = 0, 0
            Agents = Agents.keys()
            for agent in Agents:
                self._worksheet.write(self._r, self._c, agent)
                self._c += 1
            self._r += 1
            self._c = 0
        else:
            Agents = Agents.values()
            for agent in Agents:
                self._worksheet.write(self._r, self._c, agent.get_current_location())
                self._c += 1
            self._r += 1
            self._c = 0
            
    # ---------------- Desease State Printer ------------------------------------------------------------------------------

    def print_person_disease_state(self, Agents: dict, day, isFirst=False):
        """
        1. If first row, write agent names.
        2. Write the agent's current location.
        :param Agents   : Agents as a dictionary
        :param isFirst  : Is it the first row?
        :return         : Writes to excell file
        """
        if isFirst:
            self._worksheet = self._workbook.add_worksheet()
            self._worksheet.write(0, 0, 'Day')  # First column for 'Day'
            for col, agent_name in enumerate(Agents.keys(), start=1):
                self._worksheet.write(0, col, agent_name)  # Write agent names in the first row

        else:
            self._worksheet.write(day, 0, day)  # Write the day number in the first column
            for col, agent in enumerate(Agents.values(), start=1):
                # Write the agent's disease state in the corresponding cell
                self._worksheet.write(day, col, agent.disease_state)
                
    # ---------------- Desease State Printer ------------------------------------------------------------------------------

    def print_person_disease_trace(self, agents: list, day, min, isFirst=False):
        """
        1. If first row, write agent names.
        2. Write the agent's current location.
        :param Agents   : Agents as a dictionary
        :param isFirst  : Is it the first row?
        :return         : Writes to excell file
        """
        if min % 5 == 0:
            if isFirst:
                self._worksheet = self._workbook.add_worksheet()
                self._worksheet.write(0, 0, 'Time')  # First column for 'Time' = Day x 5 min
                for agent in agents:
                    self._worksheet.write(0, int(agent.ID.split("_")[1]) + 1, agent._agent_name)  # Write agent names in the first row

            else:
                self._worksheet.write(day * min // 5, 0, day*min)  # Write the day number in the first column
                for agent in agents:
                    if 3 <= agent.disease_state <= 7:
                        self._worksheet.write(day * min // 5, int(agent.ID.split("_")[1]) + 1, agent.patch._id)

    # ------------------------------------ Infected people printer -----------------------------------------------------

    def add_Columns(self, sheet_name, list_of_columns: list):
        self.columns = list_of_columns
        self._worksheet = self._workbook.add_worksheet(sheet_name)
        for column in list_of_columns:
            self._worksheet.write(self._r, self._c, column)
            self._c += 1
        # Move the cursor to the 2nd row.
        self._r = 1
        self._c = 0

    def write_for_day(self, agents: list, infected_by_class: dict, day: int):
        """
        Write the number of infected agents for each class for a given day.
        :param agents:
        :param infected_by_class:
        :param day:
        :return:
        """

        infected_dict = infected_by_class.copy()
        for agent in agents:
            if agent.can_agent_transmit():
                infected_dict[agent.get_agent_class()] += 1

        column_data = list(infected_dict.values())
        self._c = 0
        self._worksheet.write(self._r, self._c, day)
        self._c += 1
        for data in column_data:
            self._worksheet.write(self._r, self._c, data)
            self._c += 1
        self._r += 1

    def write_lines(self, lines: list):
        self._c = 0
        for line in lines:
            self._worksheet.write(self._r, self._c, line)
            self._c += 1
        self._r += 1

    def close_workbook(self):
        self._workbook.close()


def printPersonTimeTables(timetable: dict, path: pathlib.Path):
    return 0


def writeGeneralInfo(agents: dict, parameter_dictionary: dict, infected_agents: list, writer_object):
    # Write Date and Time
    writer_object.write(f"Executed on: {parameter_dictionary['Date']}           |               At: {parameter_dictionary['Time']}\n\n")

    writer_object.write('============================ Simulation INFO =============================================\n')
    writer_object.write(f"Vaccination                            : {parameter_dictionary['vaccinate']}\n")
    writer_object.write(f"Quarantine                             : {parameter_dictionary['quarantine']}\n")
    writer_object.write(f"Pandemic detection threshold           : {parameter_dictionary['pandemic_detection_threshold']} of total population \n")

    writer_object.write('============================ Transmission INFO ============================================\n')
    writer_object.write(f"Disease Transmission step              : {parameter_dictionary['STEP_DISEASE_frequency']}\n")
    writer_object.write(f"Maximum transmission risk at bus       : {parameter_dictionary['bus_max_risk']}\n")
    writer_object.write(f"Maximum transmission risk at a location: {parameter_dictionary['location_max_risk']}\n")
    writer_object.write(f"Maximum transmission distance          : {parameter_dictionary['radius_of_infection']}\n")

    writer_object.write('=============================== AGENT INFO =============================================\n')
    writer_object.write(f"Number of days simulated               : {parameter_dictionary['simulation_days']}\n")
    writer_object.write(f"Total Agent count                      : {len(agents)}\n")
    writer_object.write(f"Total infected Agents                  : {len(infected_agents)}\n")
    writer_object.write(f"Infect Randomly                        : {str(parameter_dictionary['infect_random'])}\n")
    writer_object.write(f"Percentage of infected Agents          : {parameter_dictionary['percentage_of_agents_to_infect']}\n")

    writer_object.write(f"Agent classes to infect                :  ")
    for agent_class in parameter_dictionary['classes_to_infect']:
        writer_object.write(f"{agent_class} ")

    writer_object.write(f"\n\n------Below agents are infected initially------\n")
    i = 0
    for agent in infected_agents:
        if i % 5 == 0:
            writer_object.write(f"\n")
        writer_object.write(f"{agent}, ")
        i += 1

    writer_object.write('\n')

    writer_object.write('\n=============================== COMPUTER INFO ===========================================\n')
    # Get OS information
    os_info = platform.uname()
    writer_object.write(f"System               : {os_info.system}\n")
    writer_object.write(f"User                 : {os_info.node}\n")
    writer_object.write(f"Processor            : {os_info.processor}\n")
    cpu_info = cpuinfo.get_cpu_info()
    writer_object.write(f"CPU Brand            : {cpu_info['brand_raw']}\n")
    writer_object.write(f"CPU Cores            : {psutil.cpu_count(logical=False)}\n")

    # Get memory information
    virtual_mem = psutil.virtual_memory()
    writer_object.write(f"Total Memory         : {round(virtual_mem.total / (1024 ** 3))} GB\n")
    return 0
