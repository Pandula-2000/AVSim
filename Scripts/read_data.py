import pandas as pd

try:
    env_df = pd.read_excel('../Data/NodeEnv.xlsx')
    print('NodeEnv columns:', env_df.columns.tolist())
    print('NodeEnv row 0:', env_df.iloc[0].to_dict())
except Exception as e:
    print(f"Error reading NodeEnv: {e}")

try:
    contact_df = pd.read_excel('../Results/Quarantine_TEST_4_bus_0.1_loc_0.3_radius_1_step_5_RandU/Pandemic/Agent_contacts.xlsx')
    print('Contacts columns:', contact_df.columns.tolist())
    print('Contacts row 0:', contact_df.iloc[0].to_dict())
except Exception as e:
    print(f"Error reading Contacts: {e}")
