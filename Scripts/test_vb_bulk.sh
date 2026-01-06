#!/bin/bash

# python | vector_borne_main_arg.py | simDays | controlled(True/False) | controlRate | maxExposedAgents | minTemperature | maxTemperature | plot anything? > Results/vb_logs/filename.log &

# First simulation  - low temp with plot
nohup python vector_borne_main_arg.py 120 False 0.75 10 16 21 True > ../Results/vb_logs/vb_temp_low1_plot.log &
sleep 5

count=0
# Low temp others (2-100)
for i in {2..100}; do
    nohup python vector_borne_main_arg.py 120 False 0.75 10 16 21 False > "../Results/vb_logs/vb_temp_low${i}.log" &
    sleep 5
    ((count++))
    if (( count % 50 == 0 )); then
        wait
    fi
done
wait

# First simulation - high temp with plot
nohup python vector_borne_main_arg.py 120 False 0.75 10 26 31 True > ../Results/vb_logs/vb_temp_high1_plot.log &
sleep 5

count=0
# High temp others (2-100)
for i in {2..100}; do
    nohup python vector_borne_main_arg.py 120 False 0.75 10 26 31 False > "../Results/vb_logs/vb_temp_high${i}.log" &
    sleep 5
    ((count++))
    if (( count % 50 == 0 )); then
        wait
    fi
done
wait

# First simulation - mid temp with plot
nohup python vector_borne_main_arg.py 120 False 0.75 10 21 26 True > ../Results/vb_logs/vb_temp_mid1_plot.log &
sleep 5

count=0
# Mid temp others (2-100)
for i in {2..100}; do
    nohup python vector_borne_main_arg.py 120 False 0.75 10 21 26 False > "../Results/vb_logs/vb_temp_mid${i}.log" &
    sleep 5
    ((count++))
    if (( count % 50 == 0 )); then
        wait
    fi
done
wait
