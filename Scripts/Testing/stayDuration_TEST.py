from bimodelity import *

import numpy as np
import pandas as pd



df_stay = pd.read_excel("X:\PROJECTS\FYP\Emulator_V1\Data_old\Clustered Statistics\Clustered Stay Duration Matrices\dc\StayDurationMatrix_allDays_dc_cluster0.xlsx")

df = pd.read_excel("X:\PROJECTS\FYP\Emulator_V1\Data_old\Clustered Statistics\Clustered Probability Matrices\dc\ProbabilityMatrix_allDays_dc_cluster0.xlsx")




location = getNextLocationV2(df, 1170, 'Home')
print(location)
stay = getStayDuration(df_stay, location)
print(stay)