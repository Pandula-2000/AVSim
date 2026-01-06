from DataLoader import Loader

# df = Loader.getSim('events.csv')
df = Loader.getSim2("Event Plan")

print(df.head())

test_index = df.loc[df['day'] == 11].index.tolist()

print(test_index)

# print(df.loc[test_index[0], ['attendees']]=="Student")

df_entr = df.loc[test_index[0]]

print(df_entr['attendees'])