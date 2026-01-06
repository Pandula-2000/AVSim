#!/bin/bash

# python | fileName.py[0] | Infect_random[1] | num_of_days[2] | quarantine[3] | vaccinate[4] | location_risk[5] | bus_risk[6] | pandemic_detection_threshold[7]
# | quarantine by pcr[8] | quarantine by class[9]

# Infect random test.
#python AB_main_automated.py False 150 False False 0.3 0.05
#python AB_main_automated.py True 150 False False 0.3 0.05

# Quarantine test.
python AB_main_automated.py False 150 True False 0.3 0.05 0.20 True False
python AB_main_automated.py False 150 True False 0.3 0.05 0.20 False True
python AB_main_automated.py False 150 True False 0.3 0.05 0.20 True True

## Vaccination test.
#python AB_main_automated.py False 150 True False 0.3 0.05 0.20
#python AB_main_automated.py False 150 False True 0.3 0.05 0.15
#python AB_main_automated.py False 150 False True 0.3 0.05 0.10
#python AB_main_automated.py False 150 False True 0.3 0.05 0.05

