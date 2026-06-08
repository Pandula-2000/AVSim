import pandas as pd
import re
import os

file_path = "../Data_old/NodeEnv.xlsx"
df = pd.read_excel(file_path, header=None)

def double_homes(cell):
    if pd.isna(cell) or str(cell) == "None":
        return cell
    
    cell = str(cell)
    def replacer(match):
        val = int(match.group(1))
        return f"Home#{val*2}"
    
    new_cell = re.sub(r'Home#(\d+)', replacer, cell)
    return new_cell

df[1] = df[1].apply(double_homes)

df.to_excel(file_path, index=False, header=False)
print(f"Successfully doubled homes in {file_path}!")
