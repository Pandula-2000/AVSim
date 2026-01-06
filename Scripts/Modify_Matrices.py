from Tools import probability_matrix, write_probability_matrix
from Tools import stayDuration_matrix, write_stayDuration_matrix
import pandas as pd


profession = "gw"
cluster = "cluster0"
holiday = False

save_path = "..\\Data_old\\Clustered Statistics"
read_path = f"..\\Data_old\\Clustered Location Strings\\{profession}\\Strings_{profession}_{cluster}.xlsx"
# read_path = "Test.xlsx"
save_probability_path = f"{save_path}\\Clustered Probability Matrices\\{profession}"
save_stayDuration_path = f"{save_path}\\Clustered Stay Duration Matrices\\{profession}"

df = pd.read_excel(read_path)

string_list = []
for column in df:
    if column == 'Time':
        continue

    column_data = df[column]
    column_data_list = column_data.tolist()
    string_list.append(column_data_list)

# print(string_list)

if holiday:
    cluster = "holiday"

# A = probability_matrix(string_list)
write_probability_matrix(string_list, save_probability_path, f"allDays_{profession}_{cluster}")

# B = stayDuration_matrix(string_list)
write_stayDuration_matrix(string_list, save_stayDuration_path, f"allDays_{profession}_{cluster}")


