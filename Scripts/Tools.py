import numpy as np
import os
import pandas as pd
import xlsxwriter
from tqdm import tqdm

# from Tools import probability_matrix, write_probability_matrix
# from Tools import stayDuration_matrix, write_stayDuration_matrix
from Agents2 import *
from Environment import *
from bimodelity import generateTimeTableV2


def get_all_agent_count_in_env(env, t):
    count = 0
    for node in env.get_all_nodes():
        count += len(env.get_agents(node))
    out = f"Total number of agents in the environment: {count} at t={t}"
    return out


# -------------------------- Probability related --------------------------------
location_list = [
    '_home',
    '_w_home',
    '_work',
    'AdministrativeZone',
    'AdminOffice',
    'AdminWorkArea',
    'AgriculturalZone',
    'AvgProvince',
    'Bank',
    'BusStation',
    'Classroom',
    'CommercialBuilding',
    'CommercialCanteen',
    'CommercialFinancialZone',
    'CommercialWorkArea',
    'COVIDQuarantineZone',
    'DenseDistrict',
    'EducationZone',
    'Estate',
    'FastFoodJoint',
    'GarmentBuilding',
    'GarmentCanteen',
    'GarmentOffice',
    'GarmentWorkArea',
    'GatheringPlace',
    'Home',
    'Hospital',
    'IndustrialManufactureZone',
    'LivestockCultivateArea',
    'MedicalZone',
    'PlantCultivateArea',
    'ResidentialPark',
    'ResidentialZone',
    'Restaurants',
    'RetailShops',
    'RuralBlock',
    'School',
    'SchoolCanteen',
    'ShoppingMall',
    'SparseDistrict',
    'SuperMarkets',
    'TestCenter',
    'TukTukStation',
    'UrbanBlock'
]


def strip_tt(tt):
    for i in range(len(tt[0])):
        tt[0][i] = tt[0][i].split('_')[0]
    return tt


def write_probability_matrix(string_list, path, save_name):
    """
    :param string_list  : Processed strings
    :param path         : Path to write
    :return             : None. Writes probability matrix to the given path
    """
    global target

    Matrix = probability_matrix(string_list)
    print("----------- Probability Matrix--------------------")
    print(Matrix)
    s = Matrix.shape

    try:
        os.makedirs(path, exist_ok=True)
        print("Directory '%s' created successfully" % path)
        print("Writing Matrix to '%s' " % path)
    except OSError as error:
        print("Writing Matrix to '%s' " % path)

    xls_fname = "ProbabilityMatrix_" + save_name + ".xlsx"
    xls_wb_loc = path + "\\" + xls_fname

    workbook = xlsxwriter.Workbook(xls_wb_loc)
    worksheet = workbook.add_worksheet()
    worksheet.write(0, 0, "Locations")
    for timePoint in range(1, 1441):
        colPos = timePoint
        worksheet.write(0, colPos, timePoint)
    r_loc = 1
    for loc in location_list:
        worksheet.write(r_loc, 0, loc)
        r_loc += 1

    for r in range(1, s[0] + 1):
        for c in range(1, s[1] + 1):
            worksheet.write(r, c, Matrix[r - 1, c - 1])

    workbook.close()


def write_stayDuration_matrix(string_list, path, save_name):
    """
    :param string_list  : Processed strings
    :param path         : Path to write
    :return             : None. Writes probability matrix to the given path
    """
    global target

    Matrix = stayDuration_matrix(string_list)
    print("----------- Stay Duration Matrix--------------------")
    print(Matrix)
    s = Matrix.shape

    try:
        os.makedirs(path, exist_ok=True)
        print("Directory '%s' created successfully" % path)
        print("Writing Matrix to '%s' " % path)
    except OSError as error:
        print("Writing Matrix to '%s' " % path)

    xls_fname = "StayDurationMatrix_" + save_name + ".xlsx"
    xls_wb_loc = path + "\\" + xls_fname

    workbook = xlsxwriter.Workbook(xls_wb_loc)
    worksheet = workbook.add_worksheet()
    worksheet.write(0, 0, "Locations")
    for timePoint in range(1, 1441):
        colPos = timePoint
        worksheet.write(0, colPos, timePoint)

    r_loc = 1
    for loc in location_list:
        worksheet.write(r_loc, 0, loc)
        r_loc += 1

    for r in range(1, s[0] + 1):
        for c in range(1, s[1] + 1):
            worksheet.write(r, c, Matrix[r - 1, c - 1])

    workbook.close()


# ------------------------ Stay Duration Matrix ------------------------------------------------------------------------
def stayDuration_matrix(stringList):
    global location_list
    locations = location_list
    mat = count_same_elements_2DMatrix(stringList, locations)
    s = mat.sum(axis=1)
    print('S', s)
    #print(mat)
    #print(mat.shape)

    for r in range(mat.shape[0]):
        for c in range(mat.shape[1]):
            if s[r] == 0:
                mat[r, c] = 0
            else:
                mat[r, c] = mat[r, c] / s[r]

    return mat


def count_same_elements_2DMatrix(string_day_2d, location_list):
    cols = len(string_day_2d[0])
    rows = len(location_list)
    matrix = (rows, cols)
    arr = np.zeros(matrix, dtype=float)

    for g in range(len(string_day_2d)):
        count_same_elements(string_day_2d[g], location_list, arr)
    return arr


def count_same_elements(string_day, location_list, mat_2d):
    for x in range(len(location_list)):
        # for x in range(1):
        count = 0
        flag = 0

        for y in range(len(string_day)):
            if (location_list[x] == string_day[y]):
                count = count + 1
                flag = 1

            if ((location_list[x] != string_day[y]) and (flag == 1)):
                flag = 0
                mat_2d[x][count - 1] = mat_2d[x][count - 1] + 1
                count = 0

            if (flag == 1 and y == (len(string_day) - 1)):
                flag = 0
                mat_2d[x][count - 1] = mat_2d[x][count - 1] + 1
                count = 0

    return mat_2d


def probability_matrix(x):
    """
    :param x         : list of String lists
    :return          : The probability Matrix
    """
    global location_list
    locations = location_list
    a = np.zeros(shape=(len(locations), len(x[0])))
    for i in range((len(x[0]))):
        for j in range(len(locations)):
            a[j][i] = check_Probability(i, j, locations, x)
    return a


def check_Probability(i, j, loc, string_List_x):
    """
    :param      i: i th position (across)
    :param      j: j th position (down)
    :param      loc: Location Array
    :param      string_List_x: String lists of locations [S1,S2,S3,......,Sn)
    :return:    The probability of being at the particular place at the given time
    """
    count = 0.0
    for n in range(len(string_List_x)):
        if string_List_x[n][i] == loc[j]:
            count = count + 1
    return float(count) / float(len(string_List_x))






