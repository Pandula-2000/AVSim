import sys
sys.path.append('../Scripts')

from Environment import *
from Clock import *
import matplotlib.animation as animation
from datetime import timedelta

# Read the Excel file
excel_file = 'Test_run_results.xlsx'
df = pd.read_excel(excel_file)

node_columns = ["Student_1", "Student_2"]
node_sequence = df['Student_1'].tolist()
time_stamp = df['Time'].tolist()


env = LaunchEnvironment()

fig = plt.figure(2)
ax = fig.add_subplot(111)

for name, details in env.graph.nodes(data=True):
    if details['node'].boundary:

        boundary_coords = details['node'].boundary
        centroid = details['node'].centroid

        random_color = "#{:06x}".format(random.randint(0, 0xFFFFFF))
        plot_polygon(boundary_coords, ax=ax, add_points=False, color= random_color, label=name)
        # plt.plot(centroid.x, centroid.y, 'ko')
    # else:
    #     circle = details['node'].centroid.buffer(details['node'].radius)
    #     x, y = circle.exterior.xy
    #     plt.plot(x, y)

# Initial points and their plots
points = []
centroid_sequences = []
colors = ['ro', 'bo', 'go', 'mo', 'co', 'yo', 'ko', 'r+', 'b+', 'g+']  # Colors for up to 10 nodes

for idx, node_col in enumerate(node_columns):
    initial_node = env.graph.nodes[df[node_col].iloc[0]]['node']
    point, = plt.plot(initial_node.centroid.x, initial_node.centroid.y, colors[idx%10], label=node_col)
    points.append(point)
    centroid_sequences.append([env.graph.nodes[node]['node'].centroid for node in df[node_col].tolist()])

# Initialize text for timestamp
time_text = ax.text(0.8, 0.05, '', transform=ax.transAxes, fontsize=12, verticalalignment='top')

# Update function for animation
def update(num, centroid_sequences, points, time_text, timestamps):
    for i, point in enumerate(points):
        point.set_data(centroid_sequences[i][num].x, centroid_sequences[i][num].y)
    # Update the timestamp from the Excel data
    time_text.set_text(f'Time: {Time.minutes_to_time(timestamps[num])}')
    return points + [time_text]

# Set up the animation
ani = animation.FuncAnimation(
    fig, update, frames=len(time_stamp), fargs=[centroid_sequences, points, time_text, time_stamp],
    interval=10, blit=True
)

# Show the plot with animation
plt.tight_layout()
plt.show()