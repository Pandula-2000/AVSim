#!/bin/bash

# python | vector_borne_main_arg.py | simDays | controlled(True/False) | controlRate | maxExposedAgents | minTemperature | maxTemperature | plot anything? > Results/vb_logs/filename.log &

nohup python vector_borne_main_arg.py 360 False 0.75 10 18 31 True > ../Results/vb_logs/vb_360_False.log &
sleep 5
nohup python vector_borne_main_arg.py 360 True 0.75 10 18 31 True > ../Results/vb_logs/vb_360_True_0.75_10.log &
sleep 5
nohup python vector_borne_main_arg.py 360 True 0.75 20 18 31 True > ../Results/vb_logs/vb_360_True_0.75_20.log &
sleep 5
nohup python vector_borne_main_arg.py 360 True 0.90 10 18 31 True > ../Results/vb_logs/vb_360_True_0.90_10.log &
sleep 5
nohup python vector_borne_main_arg.py 360 True 0.90 20 18 31 True > ../Results/vb_logs/vb_360_True_0.90_20.log &
sleep 5

nohup python vector_borne_main_arg.py 360 False 0.75 10 26 31 True > ../Results/vb_logs/vb_360_False_highT.log &
sleep 5
nohup python vector_borne_main_arg.py 360 True 0.75 10 26 31 True > ../Results/vb_logs/vb_360_True_0.75_10_highT.log &
sleep 5
nohup python vector_borne_main_arg.py 360 True 0.75 20 26 31 True > ../Results/vb_logs/vb_360_True_0.75_20_highT.log &
sleep 5
nohup python vector_borne_main_arg.py 360 True 0.90 10 26 31 True > ../Results/vb_logs/vb_360_True_0.90_10_highT.log &
sleep 5
nohup python vector_borne_main_arg.py 360 True 0.90 20 26 31 True > ../Results/vb_logs/vb_360_True_0.90_20_highT.log &
sleep 5

# nohup python vector_borne_main_arg.py 120 False 0.75 10 16 21 True > ../Results/vb_logs/vb_temp_low1_plot.log &
# sleep 5
# nohup python vector_borne_main_arg.py 120 False 0.75 10 16 21 False > ../Results/vb_logs/vb_temp_low2.log &
# sleep 5
# nohup python vector_borne_main_arg.py 120 False 0.75 10 16 21 False > ../Results/vb_logs/vb_temp_low3.log &
# sleep 5
# nohup python vector_borne_main_arg.py 120 False 0.75 10 16 21 False > ../Results/vb_logs/vb_temp_low4.log &
# sleep 5
# nohup python vector_borne_main_arg.py 120 False 0.75 10 16 21 False > ../Results/vb_logs/vb_temp_low5.log &
# sleep 5
# nohup python vector_borne_main_arg.py 120 False 0.75 10 16 21 False > ../Results/vb_logs/vb_temp_low6.log &
# sleep 5
# nohup python vector_borne_main_arg.py 120 False 0.75 10 16 21 False > ../Results/vb_logs/vb_temp_low7.log &
# sleep 5
# nohup python vector_borne_main_arg.py 120 False 0.75 10 16 21 False > ../Results/vb_logs/vb_temp_low8.log &
# sleep 5
# nohup python vector_borne_main_arg.py 120 False 0.75 10 16 21 False > ../Results/vb_logs/vb_temp_low9.log &
# sleep 5
# nohup python vector_borne_main_arg.py 120 False 0.75 10 16 21 False > ../Results/vb_logs/vb_temp_low10.log &
# sleep 5
# nohup python vector_borne_main_arg.py 120 False 0.75 10 16 21 False > ../Results/vb_logs/vb_temp_low11.log &
# sleep 5
# nohup python vector_borne_main_arg.py 120 False 0.75 10 16 21 False > ../Results/vb_logs/vb_temp_low12.log &
# sleep 5
# nohup python vector_borne_main_arg.py 120 False 0.75 10 16 21 False > ../Results/vb_logs/vb_temp_low13.log &
# sleep 5
# nohup python vector_borne_main_arg.py 120 False 0.75 10 16 21 False > ../Results/vb_logs/vb_temp_low14.log &
# sleep 5
# nohup python vector_borne_main_arg.py 120 False 0.75 10 16 21 False > ../Results/vb_logs/vb_temp_low15.log &
# sleep 5

# nohup python vector_borne_main_arg.py 120 False 0.75 10 26 31 True > ../Results/vb_logs/vb_temp_high1_plot.log &
# sleep 5
# nohup python vector_borne_main_arg.py 120 False 0.75 10 26 31 False > ../Results/vb_logs/vb_temp_high2.log &
# sleep 5
# nohup python vector_borne_main_arg.py 120 False 0.75 10 26 31 False > ../Results/vb_logs/vb_temp_high3.log &
# sleep 5
# nohup python vector_borne_main_arg.py 120 False 0.75 10 26 31 False > ../Results/vb_logs/vb_temp_high4.log &
# sleep 5
# nohup python vector_borne_main_arg.py 120 False 0.75 10 26 31 False > ../Results/vb_logs/vb_temp_high5.log &
# sleep 5
# nohup python vector_borne_main_arg.py 120 False 0.75 10 26 31 False > ../Results/vb_logs/vb_temp_high6.log &
# sleep 5
# nohup python vector_borne_main_arg.py 120 False 0.75 10 26 31 False > ../Results/vb_logs/vb_temp_high7.log &
# sleep 5
# nohup python vector_borne_main_arg.py 120 False 0.75 10 26 31 False > ../Results/vb_logs/vb_temp_high8.log &
# sleep 5
# nohup python vector_borne_main_arg.py 120 False 0.75 10 26 31 False > ../Results/vb_logs/vb_temp_high9.log &
# sleep 5
# nohup python vector_borne_main_arg.py 120 False 0.75 10 26 31 False > ../Results/vb_logs/vb_temp_high10.log &
# sleep 5
# nohup python vector_borne_main_arg.py 120 False 0.75 10 26 31 False > ../Results/vb_logs/vb_temp_high11.log &
# sleep 5
# nohup python vector_borne_main_arg.py 120 False 0.75 10 26 31 False > ../Results/vb_logs/vb_temp_high12.log &
# sleep 5
# nohup python vector_borne_main_arg.py 120 False 0.75 10 26 31 False > ../Results/vb_logs/vb_temp_high13.log &
# sleep 5
# nohup python vector_borne_main_arg.py 120 False 0.75 10 26 31 False > ../Results/vb_logs/vb_temp_high14.log &
# sleep 5
# nohup python vector_borne_main_arg.py 120 False 0.75 10 26 31 False > ../Results/vb_logs/vb_temp_high15.log &
# sleep 5

# nohup python vector_borne_main_arg.py 120 False 0.75 10 21 26 True > ../Results/vb_logs/vb_temp_mid1_plot.log &
# sleep 5
# nohup python vector_borne_main_arg.py 120 False 0.75 10 21 26 False > ../Results/vb_logs/vb_temp_mid2.log &
# sleep 5
# nohup python vector_borne_main_arg.py 120 False 0.75 10 21 26 False > ../Results/vb_logs/vb_temp_mid3.log &
# sleep 5
# nohup python vector_borne_main_arg.py 120 False 0.75 10 21 26 False > ../Results/vb_logs/vb_temp_mid4.log &
# sleep 5
# nohup python vector_borne_main_arg.py 120 False 0.75 10 21 26 False > ../Results/vb_logs/vb_temp_mid5.log &
# sleep 5
# nohup python vector_borne_main_arg.py 120 False 0.75 10 21 26 False > ../Results/vb_logs/vb_temp_mid6.log &
# sleep 5
# nohup python vector_borne_main_arg.py 120 False 0.75 10 21 26 False > ../Results/vb_logs/vb_temp_mid7.log &
# sleep 5
# nohup python vector_borne_main_arg.py 120 False 0.75 10 21 26 False > ../Results/vb_logs/vb_temp_mid8.log &
# sleep 5
# nohup python vector_borne_main_arg.py 120 False 0.75 10 21 26 False > ../Results/vb_logs/vb_temp_mid9.log &
# sleep 5
# nohup python vector_borne_main_arg.py 120 False 0.75 10 21 26 False > ../Results/vb_logs/vb_temp_mid10.log &
# sleep 5
# nohup python vector_borne_main_arg.py 120 False 0.75 10 21 26 False > ../Results/vb_logs/vb_temp_mid11.log &
# sleep 5
# nohup python vector_borne_main_arg.py 120 False 0.75 10 21 26 False > ../Results/vb_logs/vb_temp_mid12.log &
# sleep 5
# nohup python vector_borne_main_arg.py 120 False 0.75 10 21 26 False > ../Results/vb_logs/vb_temp_mid13.log &
# sleep 5
# nohup python vector_borne_main_arg.py 120 False 0.75 10 21 26 False > ../Results/vb_logs/vb_temp_mid14.log &
# sleep 5
# nohup python vector_borne_main_arg.py 120 False 0.75 10 21 26 False > ../Results/vb_logs/vb_temp_mid15.log &
# sleep 5