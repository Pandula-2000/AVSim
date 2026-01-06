# import random
# from DataLoader import Loader
from tqdm import tqdm

from Tools import probability_matrix, write_probability_matrix
from Tools import stayDuration_matrix, write_stayDuration_matrix
from Agents2 import *
from Environment import *
from bimodelity import generateTimeTableV2


def strip_tt(tt):
    for i in range(len(tt[0])):
        tt[0][i] = tt[0][i].split('_')[0]
    return tt


# print(strip_tt(tt))


def make_stringArray(tt):
    # print(tt)
    t = 1
    i = 0
    locArray = []
    location = 'Home'
    end = tt[1][-1][0] + tt[1][-1][1]

    while t <= end:
        if t == tt[1][i][0]:
            # print(t,i)
            location = tt[0][i]
            if i == len(tt[0]) - 1:
                i = 0
            else:
                i += 1
        locArray.append(location)
        t += 1
    while t <= 1440:
        locArray.append('Home')
        t += 1
    return locArray


# a = make_stringArray(strip_tt(tt))


# print(a)
# print(len(a))
# print(a.count('School_1'))
# A = probability_matrix([a])
#
# print(A)
# write_probability_matrix([a,a],f"..\Probability Analysis\Synthetic", "save1")


def make_synthetic_prob_Matrix(num_of_samples,
                               agent_ID,
                               file_name,
                               synthetic_save_path=f"..\Probability Analysis\Synthetic"):
    env = LaunchEnvironment()
    Loader.init_sub_probabilities()

    string_list = []
    agents = agent_create(env, use_def_perc=True)

    for agent in agents.values():
        print(agent)

    agent = agents[agent_ID]
    for i in tqdm(range(num_of_samples), desc='Generating Synthetic Data'):
        # print(i)
        tt = generateTimeTableV2(env, agent)
        # print(tt)
        string_tt = make_stringArray(strip_tt(tt))
        # print(string_tt)
        string_list.append(string_tt)
    # print(string_list)
    # A = probability_matrix(string_list)
    write_probability_matrix(string_list, synthetic_save_path, file_name)


samples = 10000
holiday = False
agent = "Student_1"

file_name = agent.split('_')[0]

if holiday:
    Time.DAY = 7
    make_synthetic_prob_Matrix(samples,
                               agent,
                               file_name + "_Holiday")
else:
    make_synthetic_prob_Matrix(samples,
                               agent,
                               file_name)
