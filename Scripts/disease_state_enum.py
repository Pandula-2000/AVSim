from enum import Enum


class Disease_State(Enum):
    SUSCEPTIBLE = 1
    Incubation = 2
    Infectious = 3
    MILD = 4
    SEVERE = 5
    CRITICAL = 6
    Asymptotic = 7
    Recovered = 8
    Dead = 9

