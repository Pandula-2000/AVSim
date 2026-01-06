import numpy as np
import random
import time


start = time.time()


class Agents_test:
    def _init_(self, agent_name, x, y, transmit,health):
        """
        To Load each Agent
        :param agent_name: Name assigned to the Agent
        :param x: X coordinate of the Agent
        :param y: Y coordinate of the Agent
        :param transmit: Transmission status of the Agent
        """
        self.agent_name = agent_name
        self.x = x
        self.y = y
        self.transmit = transmit
        self.health = health

# Lists of agent data
Agents = ['a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'a7','a8','a9', 'a10']
x = [1, 3, 5, 4, 3, 3, 1, 1, 2, 4]
y = [1, 1, 1, 2, 3, 4, 5, 1, 4, 1]
transmit = [False, False, True, False, False, True, False, True, False, True]
health = [0,0,2,0,0,3,0,3,0,2]
# List to store the agents
agents_list = []

# Creating and storing agents
for i, agent_name in enumerate(Agents):
    agent = Agents_test(agent_name, x[i], y[i], transmit[i], health[i])
    agents_list.append(agent)

# Accessing all the x values
x_values = [agent.x for agent in agents_list]
print(agents_list)
print("All agents' x values:", x_values)

print('Hi')


def exposed_detector_min_transmitters(agents_list):
    risk = 1
    for agent in agents_list :
        if agent.transmit == True:
            print(agent.agent_name)
            for other_agents in agents_list :
                if other_agents.transmit == True : continue
                if (agent.x == other_agents.x or agent.x+1 == other_agents.x or agent.x-1 == other_agents.x) and  (agent.y == other_agents.y or agent.y+1 == other_agents.y or agent.y-1 == other_agents.y):
                    print(f"new {other_agents.agent_name}")
                    if (np.random.random(1)[0] <= risk) : other_agents.health = 1

    health_v = [agent.health for agent in agents_list]
    print("All agents' health_v:", health_v)



def exposed_detector_max_transmitters (agents_list):
    risk = 1
    for agent in agents_list :
        if agent.transmit == False:
            print(agent.agent_name)
            for other_agents in agents_list :
                if other_agents.transmit == False : continue
                if (agent.x == other_agents.x or agent.x+1 == other_agents.x or agent.x-1 == other_agents.x) and  (agent.y == other_agents.y or agent.y+1 == other_agents.y or agent.y-1 == other_agents.y):
                    print(f"new {agent.agent_name}")
                    if (np.random.random(1)[0] <= risk) : agent.health = 1
    health_v = [agent.health for agent in agents_list]
    print("All agents' health_v:", health_v)
#
#
#
def fraction_agents_transmit (agents_list):
    transmitNo = 0
    for agents in agents_list:
        if agents.transmit == True: transmitNo+=1
    return (transmitNo/len(agents_list))

def exposed_detector (agents_list):
    if fraction_agents_transmit (agents_list) <= 0.5: exposed_detector_min_transmitters(agents_list)
    else : exposed_detector_max_transmitters(agents_list)
#
#
exposed_detector(agents_list)
# print(fraction_agents_transmit(agents_list))

end = time.time()
print(f"-------------------- Executed in {end-start} Seconds ----------------------")
