import pandas as pd

# Load the Excel file
file_path = "F:\Research_Assistant\Emulator_Engine\Emulator_V1\Results\Test_run_results.xlsx"
df = pd.read_excel(file_path)

# Initialize a dictionary to store the results
changes = {student: [] for student in df.columns if student != 'Time'}

# Iterate through each student column to detect location changes
for student in changes.keys():
    # Get the initial location for comparison
    prev_location = df[student].iloc[0]
    for i in range(1, len(df)):
        current_location = df[student].iloc[i]
        if current_location != prev_location:
            # Record the change with the time, previous location, and current location
            changes[student].append((df['Time'].iloc[i], prev_location, current_location))
            # Update the previous location
            prev_location = current_location

# Print the changes for each student
for student, change_list in changes.items():
    print(f"{student} changes:")
    for change in change_list:
        print(f"  Time: {change[0]}, From: {change[1]}, To: {change[2]}")

# Optionally, convert the results to a DataFrame for better visualization
change_records = []
for student, change_list in changes.items():
    for change in change_list:
        change_records.append({
            "Student": student,
            "Time": change[0],
            "From": change[1],
            "To": change[2]
        })

change_df = pd.DataFrame(change_records)
print(change_df)

# Write DataFrame to CSV file
change_df.to_csv('Results/people_group_node.csv', index=False)