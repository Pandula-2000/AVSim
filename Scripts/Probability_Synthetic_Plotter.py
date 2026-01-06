import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

profession = "st"
cluster = "cluster0"
work_location = "School"
holiday = False
agent = "Student_1"

# make_synthetic_prob_Matrix(100,agent, profession)

# Read the Excel file into a DataFrame
# df = pd.read_excel(f"X:\\PROJECTS\\FYP\\Emulator_V1\\Data_old\\Clustered Statistics\\Clustered Probability Matrices\\{profession}\\ProbabilityMatrix_allDays_{profession}_{cluster}.xlsx")


def plotter(profession,
            agent,
            cluster,
            work_location,
            holiday,
            synthetic=True):

    if synthetic:
        file_name = agent.split('_')[0]
        if holiday:
            file_name += "_Holiday"
        df = pd.read_excel(f"..\Probability Analysis\Synthetic\ProbabilityMatrix_{file_name}.xlsx")
    else:
        if holiday:
            cluster = "holiday"
        df = pd.read_excel(f"X:\\PROJECTS\\FYP\\Emulator_V1\\Data_old\\Clustered Statistics\\Clustered Probability Matrices\\{profession}\\ProbabilityMatrix_allDays_{profession}_{cluster}.xlsx")

        # df = pd.read_excel(f"X..\Data_old\Clustered Statistics\Clustered Probability Matrices\\{profession}\ProbabilityMatrix_allDays_{profession}_{cluster}.xlsx")

    # Set the index of the DataFrame to 'Locations'
    df.set_index('Locations', inplace=True)

    # Create a new DataFrame with 'Home', 'School', and 'Other'
    df_new = pd.DataFrame(columns=df.columns)  # Ensure columns are defined
    df_new.loc['Home'] = df.loc['Home']
    df_new.loc[work_location] = df.loc[work_location]
    df_new.loc['Other'] = df.drop(['Home', work_location]).sum()

    # Transpose the DataFrame for plotting
    df_new = df_new.T
    df_new.reset_index(inplace=True)
    df_new.rename(columns={'index': 'Time'}, inplace=True)

    return df_new
    # Plot the new DataFrame using plotly

    # output_dir = f"..\\Probability Analysis\\{profession}"

    # os.makedirs(output_dir, exist_ok=True)

    # fig.write_image(f"{output_dir}\\location_probability_plot_{profession}_{cluster}.png")
    # fig.write_html(f"{output_dir}\\location_probability_plot_{profession}_{cluster}.html")


# ----- PLOTTER -----
df_old = plotter(profession, agent, cluster, work_location, holiday, synthetic=False)
df_new = plotter(profession, agent, cluster, work_location, holiday, synthetic=True)
# -------------------

# Create the px.line charts
fig_new = px.line(df_new, x='Time', y=df_new.columns[1:], title=f'Location Probability Over Time for {profession}_{cluster}', labels={'value': 'Probability', 'variable': 'Locations', 'Time': 'Time'})
fig_old = px.line(df_old, x='Time', y=df_old.columns[1:], title=f'Location Probability Over Time for {profession}_{cluster}', labels={'value': 'Probability', 'variable': 'Locations', 'Time': 'Time'})

# Create subplots
fig = make_subplots(rows=1, cols=2, subplot_titles=("Ground Truth Distribution", "Synthetic Distribution"))

# Add traces from the px.line charts to the subplots
for trace in fig_old.data:
    fig.add_trace(trace, row=1, col=1)

for trace in fig_new.data:
    fig.add_trace(trace, row=1, col=2)

# Update layout
fig.update_layout(title_text=f"Bimodality Validation for {agent.split('_')[0]}")
fig.update_xaxes(title_text="Time")
fig.update_yaxes(title_text="Probability")
# Show the figure
fig.show()

# fig = px.line(df_new, x='Time', y=df_new.columns[1:], title=f'Location Probability Over Time for {profession}_{cluster}', labels={'value': 'Probability', 'variable': 'Locations'})
#
# fig.show()