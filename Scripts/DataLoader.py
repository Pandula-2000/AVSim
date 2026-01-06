# Imports
import pandas as pd
from typing import Literal
from pathlib import Path
import os
from tqdm import tqdm
import numpy as np

# Data Locations
data_dir = "../Data_old"

agent_cls = "person_classes_test.csv"
agent_sub_cls = "person_sub_classes_test.csv"

loc_env = "LocationEnv.xlsx"
loc_cls = "location_classes"
nod_cls = "NodeEnv.xlsx"

prob_mat_rt = f"{data_dir}/Statistics/Probability Matrices"
std_mat_rt = f"{data_dir}/Statistics/Stay Duration Matrices"

occ = None
prob_mat_loc = f"{prob_mat_rt}/{occ}/Probability Matrix_allDays_{occ}.xlsx"
std_mat_loc = f"{std_mat_rt}/{occ}/StayDuration Matrix_allDays_{occ}.xlsx"

sub_prob_mat_rt = os.path.join(data_dir, 'Clustered Statistics', 'Clustered Probability Matrices')
sub_std_mat_rt = os.path.join(data_dir, 'Clustered Statistics', 'Clustered Stay Duration Matrices')

# Pre defined DataFrames
df_tp = Literal["agent", "location", "nodes", "prob_mat", "std_mat"]

# simData = {}
# for file in [entry.name for entry in sim_directory_path.iterdir()]: # --> [Statistics, Location Strings, etc...]
#     name = file.split('.')[0]
#     if '.xlsx' in file:
#         # print('excel: ', file, name)
#         simData[name] = pd.read_excel(f"{data_dir}/{file}")

#     elif '.csv' in file:
#         # print('csv: ', file, name)
#         simData[name] = pd.read_csv(f"{data_dir}/{file}")


def LoadVaccineData(path):
    vacc_df = pd.read_excel(path)
    # Initialize an empty dictionary
    vaccine_plan_dict = {}
    # Iterate through the DataFrame rows
    for index, row in vacc_df.iterrows():
        day = row['Day']
        # Store other information in a list
        info = row.drop('Day').tolist()
        if not pd.isna(info[1]):
            print(info[1])
            info[1] = info[1].split(',')
            info[2] = info[2].split(',')
        # Add to dictionary
        vaccine_plan_dict[day] = info
    return vaccine_plan_dict



# ================================================= CLASS ==============================================================
class Loader:
    # NOTE: Write Documentation !!!!
    gamma_home = 0.5  # FIXME: not used
    gamma_work = 0.8  # FIXME: not used

    AirBorneOutbreak = False
    AirBorneOutbreakDay = None
    pandemic_detection_threshold = None

    # Bse probability of infection
    roh = 0.1 # FIXME: GIVE THIS A PROPER NAME
    transport_roh = 0.3 # FIXME: GIVE THIS A PROPER NAME

    data_dir = "../Data_old"
    sim_directory_path = Path("../Data_old")
    prob_directory_path = Path(f"{data_dir}/Statistics/Probability Matrices")
    std_directory_path = Path(f"{data_dir}/Statistics/Stay Duration Matrices")

    sub_prob_directory_path = Path(f"{data_dir}/Clustered Statistics/Clustered Probability Matrices")
    sub_std_directory_path = Path(f"{data_dir}/Clustered Statistics/Clustered Stay Duration Matrices")

    # class_encodings = my_dict = dict(zip(pd.read_csv(f"{data_dir}/person_classes_test.csv")['p_class'].values.tolist(),
    #                                      pd.read_csv(f"{data_dir}/person_classes_test.csv")['encoding'].values.tolist()))

    class_encodings = my_dict = dict(zip(pd.read_csv(f"{data_dir}/person_classes_test.csv")['encoding'].values.tolist(),
                                         pd.read_csv(f"{data_dir}/person_classes_test.csv")['p_class'].values.tolist()))

    classes = list(class_encodings.values())

    vaccine_data_dict = LoadVaccineData(f"{data_dir}/VaccinePlan.xlsx")
    # ------------------NOTE: For mario. ---------------------------------
    age_based_susceptibilities = dict(zip(pd.read_excel(f"{data_dir}/Age_based_immunity_old.xlsx")['Age class'].values.tolist(),
                                                    pd.read_excel(f"{data_dir}/Age_based_immunity_old.xlsx")['Immunity'].values.tolist()))
    ### FIXME: Loading in this form is unnecessary. Delete?? : For Pandula
    # --------------------------------------------------------------------
    # State transition timer parameters
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
    
    state_timer_dict_VB = {
        (2, 3): (4, 2),
        (3, 4): (7, 3),
        (3, 7): (0, 0),
        (4, 5): (6, 3),
        (4, 8): (4.5, 2.5),
        (5, 8): (14, 7),
        (5, 9): (10.5, 3.5),
        (7, 8): (6, 4)
    }

    probMat = {}
    stdMat = {}

    sub_probMat = {}
    sub_stdMat = {}

    name_to_path = {"Agent Classes": "person_classes.csv",
                "Agent Classes test": "person_classes_test.csv",
                "Agent Sub Classes": "person_sub_classes.csv",
                "Relative Susceptability": "relative_susceptability.xlsx",
                "Agent Sub Classes test": "person_sub_classes_test.csv",
                "Location Environment": "LocationEnv.xlsx",
                "Location Classes": "location_classes.csv",
                "Node Environment": "NodeEnv.xlsx",
                "Bus Halt Plan": "bushaltplan.csv",
                "Location Risk Factor": "location_risk_factor.csv",
                "Public Transport Plan": "PublicTransportPlan.csv",
                "Event Plan": "events.csv",
                "Vaccine Plan": "VaccinePlan.xlsx"}

    # data_names and associated file names/ paths
    data_names = Literal["Agent Classes", "Agent Classes test", "Agent Sub Classes", "Relative Susceptability", "Agent Sub Classes test",
                        "Location Environment", "Location Classes", "Node Environment", "Bus Halt Plan", "Location Risk Factor",
                        "Public Transport Plan", "Event Plan", "Vaccine Plan"]

    simData = {}

    for name, file in name_to_path.items():
        if '.xlsx' in file:
            simData[name] = pd.read_excel(f"{data_dir}/{file}")
        elif '.csv' in file:
            simData[name] = pd.read_csv(f"{data_dir}/{file}")
    
    # print(simData['Agent Classes'])

    @classmethod
    def init_probabilities(cls, **kwargs):
        for occupation in tqdm([entry.name for entry in cls.prob_directory_path.iterdir()], desc='Loading Location Visit Probabilities'):  # --> [dc,tc,an,etc...]
            if occupation not in cls.class_encodings.keys():
                continue
            cls.probMat[cls.class_encodings[occupation]] = pd.read_excel(
                f"{prob_mat_rt}/{occupation}/Probability Matrix_allDays_{occupation}.xlsx", **kwargs)
        
        for occupation in tqdm([entry.name for entry in cls.std_directory_path.iterdir()], desc='Loading Stay duration Probabilities'):  # --> [dc,tc,an,etc...]
            if occupation not in cls.class_encodings.keys():
                continue
            cls.stdMat[cls.class_encodings[occupation]] = pd.read_excel(
                f"{std_mat_rt}/{occupation}/StayDuration Matrix_allDays_{occupation}.xlsx", **kwargs)

    @classmethod
    def init_sub_probabilities(cls, **kwargs):
        for occupation in tqdm([entry.name for entry in cls.sub_prob_directory_path.iterdir()], desc="Loading Statistics         "): # --> ['an_cluster0', 'an_cluster1', 'an_holiday','td_cluster0', 'td_cluster1']
            # print(occupation)
            if occupation not in cls.class_encodings.keys():
                continue
            # print(occupation)
            # get the sub cls names for the given cls
            sub_names = Loader.get_sub_cls_names(occupation)
            # print(occupation)
            # print(sub_names)

            for sub_clss in sub_names:
                proper_class_name = Loader.class_encodings[sub_clss.split('_')[0]] + '_' + sub_clss.split('_')[1]
                cls.sub_probMat[proper_class_name] = pd.read_excel(f"{sub_prob_mat_rt}/{occupation}/ProbabilityMatrix_allDays_{sub_clss}.xlsx", **kwargs)
                # print (sub_clss)
                # print(cls.sub_probMat[sub_clss])
                
                cls.sub_stdMat[proper_class_name] = pd.read_excel(f"{sub_std_mat_rt}/{occupation}/StayDurationMatrix_allDays_{sub_clss}.xlsx", **kwargs)
                # print(cls.sub_stdMat[sub_clss])

    @staticmethod
    def getSim(file, **kwargs):
        if '.xlsx' in file:
            return pd.read_excel(f"{Loader.data_dir}/{file}", **kwargs)
        elif '.csv' in file:
            return pd.read_csv(f"{Loader.data_dir}/{file}", **kwargs)

    @staticmethod
    def getSim2_new(data_name: data_names, **kwargs):
        
        if data_name in Loader.simData.keys():
            
            data_file = Loader.simData[data_name]
            return data_file
        
        else:
            print(f"File not found in dictionary for data_name: {data_name}")

            file = data_name

            try:
                if '.xlsx' in file:
                    return pd.read_excel(f"{Loader.data_dir}/{file}", **kwargs)
                elif '.csv' in file:
                    return pd.read_csv(f"{Loader.data_dir}/{file}", **kwargs)
            
            except:
                raise FileNotFoundError(f"File not found: {file}")

    @staticmethod
    def getSim2(data_name: data_names, **kwargs):
        
        if data_name in Loader.name_to_path.keys():
            
            file = Loader.name_to_path[data_name]
        
            if '.xlsx' in file:
                return pd.read_excel(f"{Loader.data_dir}/{file}", **kwargs)
            elif '.csv' in file:
                return pd.read_csv(f"{Loader.data_dir}/{file}", **kwargs)
        
        else:
            print(f"File not found in dictionary for data_name: {data_name}")

            file = data_name

            try:
                if '.xlsx' in file:
                    return pd.read_excel(f"{Loader.data_dir}/{file}", **kwargs)
                elif '.csv' in file:
                    return pd.read_csv(f"{Loader.data_dir}/{file}", **kwargs)
            
            except:
                raise FileNotFoundError(f"File not found: {file}")


    @classmethod
    def getProbMat(cls, file):
        return cls.probMat[file]

    @classmethod
    def getStdMat(cls, file):
        return cls.stdMat[file]

    @classmethod
    def getSubProbMat(cls, file):
        return cls.sub_probMat[file]

    @classmethod
    def getSubStdMat(cls, file):
        return cls.sub_stdMat[file]

    @classmethod
    def get_state_timer_dict(cls):
        return cls.state_timer_dict

    # NOTE: ------------------ Some internal parameter methods relating to Disease Spread ------------------------------
    @classmethod
    def get_AirBorneOutbreak(cls):
        return cls.AirBorneOutbreak

    @classmethod
    def get_Pandemic_detection_threshold(cls):
        return cls.pandemic_detection_threshold

    @classmethod
    def get_AirBorneOutbreakDay(cls):
        return cls.AirBorneOutbreakDay

    @classmethod
    def set_AirBorneOutbreak(cls, value: bool):
        cls.AirBorneOutbreak = value

    @classmethod
    def set_AirBorneOutbreakDay(cls, value: int):
        cls.AirBorneOutbreakDay = value

    # NOTE: ------------------------------------ Sub class encodings ---------------------------------------------------
    @classmethod
    def get_state_timer_dict_VB(cls):
        return cls.state_timer_dict_VB
    
    @staticmethod
    def get_sub_cls_names(cluster):
        
        # Remove the files endswith 'outlier.xlsx' and return the sub cls names as a list
        # eg: ['an_cluster0', 'an_cluster1']
        
        # Define the relative path
        clustered_ocp = os.path.join(sub_prob_mat_rt, cluster)

        # Construct and print the full path
        full_path = os.path.abspath(clustered_ocp)
        
        # Check if the directory exists
        # if not os.path.exists(full_path):
        #     raise FileNotFoundError(f"The specified path does not exist: {full_path}")

        # List all files in the directory
        all_files = os.listdir(full_path)

        updated_files = []

        # Iterate over each file in the all_files list
        for file in all_files:

            # Check if the file ends with '.xlsx' and is not 'outlier.xlsx'
            # if file.endswith('.xlsx') and not (file.endswith('outlier.xlsx') or file.endswith('holiday.xlsx')):
            if file.endswith('.xlsx') and not (file.endswith('outlier.xlsx')):

                # Remove the '.xlsx' extension and add to the updated_files list
                first_underscore_index = file.find('s_')

                last_dot_index = file.rfind('.')
                middle_part = file[first_underscore_index + 2:last_dot_index]

                # IMPORTANT: Middle part does not contain proper class encodings. This was fixed in init sub probabilities()
                # print(middle_part)

                # print(middle)
                updated_files.append(middle_part)
        
        return updated_files

# ================================================= End of class =======================================================

# Convert to nearest 5 multiple factor
def round_to_nearest_5(n):
    return 5 * round(n / 5)

# def get_sub_cls_xlsx(occupation):
#     # List all files in the given directory

#     cluster_loc = f"{data_dir}/Clustered"
#     clustered_ocp = f"{cluster_loc}/{occupation}"

#     all_files = os.listdir(clustered_ocp)

#     exclude_file = 'outlier.xlsx'
#     # Filter out files that are not .xlsx or are named outlier
#     xlsx_files = [file for file in all_files if file.endswith('.xlsx') and file != exclude_file]
    
#     return xlsx_files


def get_sub_cls_names_test(cluster):
    '''
    Remove the files endswith 'outlier.xlsx' or 'holiday.xlsx' and return the sub cls names as a list
    eg: ['an_cluster0', 'an_cluster1']
    '''
    # Define the relative path
    clustered_ocp = os.path.join(sub_prob_mat_rt, cluster)

    # Construct and print the full path
    full_path = os.path.abspath(clustered_ocp)
    
    # Check if the directory exists
    # if not os.path.exists(full_path):
    #     raise FileNotFoundError(f"The specified path does not exist: {full_path}")

    # List all files in the directory
    all_files = os.listdir(full_path)

    updated_files = []

    # Iterate over each file in the all_files list
    for file in all_files:
        print(file)
        # Check if the file ends with '.xlsx' and is not 'outlier.xlsx'
        if file.endswith('.xlsx') and not (file.endswith('outlier.xlsx') or file.endswith('holiday.xlsx')):
            # Remove the '.xlsx' extension and add to the updated_files list
            first_underscore_index = file.find('s_')
            last_dot_index = file.rfind('.')
            middle_part = file[first_underscore_index + 2:last_dot_index]

            updated_files.append(middle_part)
    
    return updated_files






if __name__=='__main__':

    #print(Loader.class_encodings)

    # Get the list of .xlsx files excluding the specified file
    # xlsx_files = get_sub_cls_xlsx("an")
    print(Loader.class_encodings)
    print(Loader.classes)
    print(Loader.vaccine_data_dict)
    print(Loader.age_based_susceptibilities)
   
    #print(get_sub_cls_names_test('an'))
    # Loader.init_probabilities()
    #
    # print(Loader.probMat.keys())
    #
    #
    # Loader.init_sub_probabilities()
    # print(Loader.sub_probMat.keys())
    # print(len(Loader.sub_probMat))
    #
    # a = Loader.getProbMat('Teacher')
    

    # Print the resulting list of .xlsx files
    # print(xlsx_files)
    # print(Loader.getSim('person_classes_test.csv'))


    # print(Loader.sub_probMat['tc_cluster0'])
    


