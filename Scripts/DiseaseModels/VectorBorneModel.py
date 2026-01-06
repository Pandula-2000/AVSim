import numpy as np
from Environment import *
from Agents2 import *

# -------------------------------------------- UPDATE AGENT ---------------------------------------------------------

def stepVBMarkovModel(agent):
    """
    Step the Markov model for the agent.
    :param agent: The agent object.
    :return: None
    """
    current_state = agent.get_disease_state()
    current_state_vector = np.zeros(8)
    current_state_vector[current_state - 2] = 1

    A = np.array([[0, 1.0, 0, 0, 0, 0, 0, 0],
                  [0, 0, 0.25, 0, 0, 0.75, 0, 0],
                  [0, 0, 0, 0.1, 0, 0, 0.9, 0],
                  [0, 0, 0, 0, 0, 0, 0.9, 0.1],
                  [0, 0, 0, 0, 0, 0, 0, 0],
                  [0, 0, 0, 0, 0, 0, 1, 0],
                  [0, 0, 0, 0, 0, 0, 1.0, 0],
                  [0, 0, 0, 0, 0, 0, 0, 1.0]])

    out = np.matmul(current_state_vector, A)
    next_state = np.random.choice(range(2, 10), p=out)

    return next_state


def getTransitionTimer(curr: int, prev: int, state_timer_dict: dict):
    # Get the mean and variance from the dictionary
    key = (prev, curr)
    min = 24 * 60

    if key in state_timer_dict:
        mean, variance = state_timer_dict[key]

        mean = round_to_nearest_1(mean * min)
        variance = round_to_nearest_1(variance * min)

        if variance == 0:  # Handle case where variance is 0
            return np.exp(mean)  # Return the mean of the log-normal distribution

        # Calculate mu and sigma for the log-normal distribution
        sigma = np.sqrt(np.log(1 + (variance / (mean ** 2))))
        mu = np.log(mean) - (sigma ** 2 / 2)

        # Generate and return a random value from the log-normal distribution
        return np.random.lognormal(mu, sigma)

        # return np.random.lognormal(mean, variance)

    else:
        raise ValueError("Invalid state transition. No such key in the dictionary.")


def round_to_nearest_1(n):
    return 1 * round(n / 1)


# if __name__=="__main__":
#     state_timer_dict = {
#         (2, 3): (4.5, 1.5),
#         (3, 4): (1.1, 0.9),
#         (3, 7): (0, 0),
#         (4, 5): (6.6, 4.9),
#         (4, 8): (8.0, 2.0),
#         (5, 8): (18.1, 6.3),
#         (5, 6): (1.5, 2.0),
#         (6, 8): (18.1, 6.3),
#         (6, 9): (10.7, 4.8),
#         (7, 8): (8.0, 2.0),
#         (7, 9): (8.0, 2.0)
#     }
    
#     def getTransitionTimer(curr: int, prev: int, state_timer_dict: dict):
#         # Get the mean and variance from the dictionary
#         key = (prev, curr)
#         min = 24 * 60

#         if key in state_timer_dict:
#             mean, variance = state_timer_dict[key]

#             mean = round_to_nearest_1(mean * min)
#             variance = round_to_nearest_1(variance * min)

#             if variance == 0:  # Handle case where variance is 0
#                 return np.exp(mean)  # Return the mean of the log-normal distribution

#             # Calculate mu and sigma for the log-normal distribution
#             sigma = np.sqrt(np.log(1 + (variance / (mean ** 2))))
#             mu = np.log(mean) - (sigma ** 2 / 2)

#             # Generate and return a random value from the log-normal distribution
#             return np.random.lognormal(mu, sigma)

#             # return np.random.lognormal(mean, variance)

#         else:
#             raise ValueError("Invalid state transition. No such key in the dictionary.")

#     print(getTransitionTimer(2,3,state_timer_dict))