import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os


profession = "ga"
cluster = "cluster1"
work_location = "GarmentOffice"
agent = "GarmentAdmin_1"
holiday = False

if holiday:
    cluster = "holiday"

# make_synthetic_prob_Matrix(100,agent, profession)

# Read the Excel file into a DataFrame
# df = pd.read_excel(f"X:\\PROJECTS\\FYP\\Emulator_V1\\Data_old\\Clustered Statistics\\Clustered Probability Matrices\\{profession}\\ProbabilityMatrix_allDays_{profession}_{cluster}.xlsx")


def plotter(profession,
            agent,
            cluster,
            work_location,
            synthetic=False):
    if synthetic:
        file_name = agent.split('_')[0]
        df = pd.read_excel(f"..\Probability Analysis\Synthetic\ProbabilityMatrix_{file_name}.xlsx")
    else:
        df = pd.read_excel(
            f"X:\\PROJECTS\\FYP\\Emulator_V1\\Data_old\\Clustered Statistics\\Clustered Probability Matrices\\{profession}\\ProbabilityMatrix_allDays_{profession}_{cluster}.xlsx")

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


# Save directory.
output_dir = f"..\\Probability Analysis\\{profession}"

os.makedirs(output_dir, exist_ok=True)

# fig.write_image(f"{output_dir}\\location_probability_plot_{profession}_{cluster}.png")
# fig.write_html(f"{output_dir}\\location_probability_plot_{profession}_{cluster}.html")


# ----- PLOTTER -----
df= plotter(profession, agent, cluster, work_location)
# -------------------

# Create the px.line charts
fig = px.line(df, x='Time', y=df.columns[1:],
                  title=f'Location Probability Over Time for {profession}_{cluster}',
                  labels={'value': 'Probability', 'variable': 'Locations', 'Time': 'Time'})

# Update layout
fig.update_layout(title_text=f"Ground Truth for {agent.split('_')[0]} {cluster}")
fig.update_xaxes(title_text="Time")
fig.update_yaxes(title_text="Probability")
# Show the figure

fig.write_html(f"{output_dir}\\location_probability_plot_{profession}_{cluster}.html")
# fig.write_image(f"{output_dir}\\location_probability_plot_{profession}_{cluster}.png")
fig.show()


