import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

def plot_states(non_hospitalized_state_counts_over_days, hospitalized_state_counts_over_days, folder, simDays):
    non_hospitalized_state_counts_df = pd.DataFrame(non_hospitalized_state_counts_over_days)
    hospitalized_state_counts_df = pd.DataFrame(hospitalized_state_counts_over_days)

    non_hospitalized_state_counts_df.drop(columns=['CRITICAL'], inplace=True)
    hospitalized_state_counts_df.drop(columns=['SUSCEPTIBLE', 'Incubation', 'Infectious', 'CRITICAL', 'Asymptotic'], inplace=True)

    num_days = len(non_hospitalized_state_counts_df)
    day_column = pd.DataFrame({'Day': range(1, num_days + 1)})

    combined_df = pd.concat([day_column, non_hospitalized_state_counts_df, hospitalized_state_counts_df], axis=1)
    combined_df.to_csv(f'{folder}/Pandemic/state_counts_over_days.csv', index=False)

    # ---------------------------- Plot the Disease State Counts Over Time ----------------------------------------------
    # Define the selected states
    selected_states_1 = ["Infectious", "MILD", "SEVERE", "Asymptotic"]
    selected_states_2 = ["Incubation", "Recovered", "Dead"]
    infectious_states = ["Infectious", "MILD", "SEVERE", "Asymptotic"]

    # Compute the summation of selected states for the first set of plots
    summation_non_hospitalized_state_counts_1 = np.sum([non_hospitalized_state_counts_over_days[state] for state in selected_states_1], axis=0)
    summation_hospitalized_state_counts_1 = np.sum([hospitalized_state_counts_over_days[state] for state in selected_states_1], axis=0)
    summation_total_state_counts_1 = summation_non_hospitalized_state_counts_1 + summation_hospitalized_state_counts_1

    # Compute the total infectious state by summing the relevant states
    total_infectious_non_hospitalized_state_counts = np.sum([non_hospitalized_state_counts_over_days[state] for state in infectious_states], axis=0)
    total_infectious_hospitalized_state_counts = np.sum([hospitalized_state_counts_over_days[state] for state in infectious_states], axis=0)
    total_infectious_state_counts = total_infectious_non_hospitalized_state_counts + total_infectious_hospitalized_state_counts

    # Compute the summation between non_hospitalized_state_counts_over_days and hospitalized_state_counts_over_days for selected states
    total_state_counts_1 = {
        state: np.array(non_hospitalized_state_counts_over_days[state]) + np.array(hospitalized_state_counts_over_days[state])
        for state in selected_states_1
    }

    total_state_counts_2 = {
        state: np.array(non_hospitalized_state_counts_over_days[state]) + np.array(hospitalized_state_counts_over_days[state])
        for state in selected_states_2
    }

    # Define colors for each state
    state_colors = {
        "Recovered": "green",
        "Infectious": "#5A9BD5",
        "MILD": "orange",
        "SEVERE": "red",
        "Asymptotic": "blue",
        "Incubation": "#5A9BD5",
        "Dead": "black",
        "SUSCEPTIBLE": "yellow",
        "CRITICAL": "black",
        "Total State Counts": "purple"
    }

    # Set up the plot (3x2 grid)
    fig, axes = plt.subplots(3, 2, figsize=(18, 18), sharex=True)
    fig.suptitle("Disease State Counts Over Days", fontsize=16)

    days = range(1, simDays + 1)
    # Plot 1: Selected states in non_hospitalized_state_counts_over_days (for selected_states_1)
    for state in selected_states_1:
        axes[0, 0].plot(days, non_hospitalized_state_counts_over_days[state], label=state, color=state_colors.get(state, 'black'))
    axes[0, 0].plot(days, summation_non_hospitalized_state_counts_1, label="Total Infectious", linestyle='--',  color=state_colors.get('Total', 'black'))
    axes[0, 0].set_title("Non-Hospitalized State Counts")
    axes[0, 0].set_ylabel("Count")
    axes[0, 0].legend(loc="upper left", fontsize=8)
    axes[0, 0].grid(True)

    # Plot 2: Selected states in hospitalized_state_counts_over_days (for selected_states_1)
    for state in selected_states_1:
        axes[1, 0].plot(days, hospitalized_state_counts_over_days[state], label=state, color=state_colors.get(state, 'black'))
    axes[1, 0].plot(days, summation_hospitalized_state_counts_1, label="Total Infectious", linestyle='--',  color=state_colors.get('Total', 'black'))
    axes[1, 0].set_title("Hospitalized State Counts")
    axes[1, 0].set_ylabel("Count")
    axes[1, 0].legend(loc="upper left", fontsize=8)
    axes[1, 0].grid(True)

    # Plot 3: summation (non_hospitalized_state_counts_over_days + hospitalized_state_counts_over_days) for selected states (for selected_states_1)
    for state in selected_states_1:
        axes[2, 0].plot(days, total_state_counts_1[state], label=state, color=state_colors.get(state, 'black'))
    axes[2, 0].plot(days, summation_total_state_counts_1, label="Total Infectious", linestyle='--',  color=state_colors.get('Total', 'black'))
    axes[2, 0].set_title("Total State Counts")
    axes[2, 0].set_ylabel("Count")
    axes[2, 0].legend(loc="upper left", fontsize=8)
    axes[2, 0].grid(True)

    # Plot 4: Selected states in non_hospitalized_state_counts_over_days (for selected_states_2)
    for state in selected_states_2:
        axes[0, 1].plot(days, non_hospitalized_state_counts_over_days[state], label=state, color=state_colors.get(state, 'black'))
    axes[0, 1].plot(days, total_infectious_non_hospitalized_state_counts, label="Total Infectious", linestyle='--',  color=state_colors.get('Total', 'black'))
    axes[0, 1].set_title("Non-Hospitalized State Counts")
    axes[0, 1].set_ylabel("Count")
    axes[0, 1].legend(loc="upper left", fontsize=8)
    axes[0, 1].grid(True)

    # Plot 5: Selected states in hospitalized_state_counts_over_days (for selected_states_2)
    for state in selected_states_2:
        axes[1, 1].plot(days, hospitalized_state_counts_over_days[state], label=state, color=state_colors.get(state, 'black'))
    axes[1, 1].plot(days, total_infectious_hospitalized_state_counts , label="Total Infectious", linestyle='--',  color=state_colors.get('Total', 'black'))
    axes[1, 1].set_title("Hospitalized State Counts")
    axes[1, 1].set_xlabel("Days")
    axes[1, 1].set_ylabel("Count")
    axes[1, 1].legend(loc="upper left", fontsize=8)
    axes[1, 1].grid(True)

    # Plot 6: summation (non_hospitalized_state_counts_over_days + hospitalized_state_counts_over_days) for selected states (for selected_states_2)
    for state in selected_states_2:
        axes[2, 1].plot(days, total_state_counts_2[state], label=state, color=state_colors.get(state, 'black'))
    axes[2, 1].plot(days, total_infectious_state_counts, label="Total Infectious", linestyle='--',  color=state_colors.get('Total', 'black'))
    axes[2, 1].set_title("Total State Counts")
    axes[2, 1].set_xlabel("Days")
    axes[2, 1].set_ylabel("Count")
    axes[2, 1].legend(loc="upper left", fontsize=8)
    axes[2, 1].grid(True)

    # Show the plot
    plt.tight_layout(rect=[0, 1, 0, 0.96])
    plt.savefig(f'{folder}/Pandemic/disease_states.png', dpi=300)