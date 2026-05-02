import gpxpy
import gpxpy.gpx
import pandas as pd

def calculate_elevation_gain(gpx_file_path):
    # 1. Parse the GPX file
    with open(gpx_file_path, 'r') as f:
        gpx = gpxpy.parse(f)
    
    # 2. Extract points into a DataFrame
    points = []
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                points.append({
                    'time': point.time,
                    'latitude': point.latitude,
                    'longitude': point.longitude,
                    'elevation': point.elevation
                })
    
    df = pd.DataFrame.from_records(points)
    
    # Ensure elevation is numeric and handle NaNs
    df['elevation'] = pd.to_numeric(df['elevation'], errors='coerce').ffill()
    
    # 3. Calculate elevation difference between consecutive points
    df['elevation_diff'] = df['elevation'].diff()
    
    # 4. Filter for positive gains and sum them
    elevation_gain = df[df['elevation_diff'] > 0]['elevation_diff'].sum()
    
    return elevation_gain

gpx_file = open('boz.gpx', 'r')

gpx = gpxpy.parse(gpx_file)
for track in gpx.tracks:
    print(track.name)
    # Calculate 3D distance in meters
    distance_3d = track.length_3d()
    print(f"Track: {track.name}, Distance: {distance_3d:.2f} meters")
    
    # Calculate 2D distance
    distance_2d = track.length_2d()
    print(f"Track: {track.name}, 2D Distance: {distance_2d:.2f} meters")
    # elevation gain
    
    for segment in track.segments:
        point= segment.points[0]
        print ('Start at ({0},{1}) -> {2}'.format(point.latitude, point.longitude, point.elevation))

for waypoint in gpx.waypoints:
    print ('waypoint {0} -> ({1},{2})'.format(waypoint.name, waypoint.latitude, waypoint.longitude))

for route in gpx.routes:
    print ('Route:')
   
print("elevation gain : {0:.2f} meters".format(calculate_elevation_gain('boz.gpx')))