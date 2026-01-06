from shapely.geometry import Point, Polygon, box
import geopy.distance


def parse_point(curr_loc, environment):
    """
    Function to parse point from string
    :param curr_loc:
    :param environment:
    :return:
    """
    point = Point(environment.graph.nodes[curr_loc]['node'].centroid)
    lon = point.x
    lat = point.y
    return Point(float(lon), float(lat))


def calculate_distance(point1, point2):
    """
    Function to calculate distance between two points
    :param point1:
    :param point2:
    :return:
    """
    distance_m = (geopy.distance.geodesic((point1.x, point1.y), (point2.x, point2.y)).km)
    return distance_m


def calculate_travel_time(distance, velocity):
    """
    Function to calculate travel time between two points
    :param distance:
    :param velocity:
    :return:
    """
    return distance / velocity


def extract_nodes(node_locations, environment):
    # Read test environment node locations
    nodes = {}
    #FIXME
    # Remove the District
    node_locations = node_locations.iloc[1:]

    # Loop through the filtered rows and add key-value pairs to the dictionary
    for index, row in node_locations.iterrows():
        first_column_value = row[0]  # First column value
        nodes[first_column_value] = parse_point(first_column_value, environment)

    return nodes

