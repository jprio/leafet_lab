import gpxpy
import pandas as pd

def calculate_elevation_gain(gpx):
    # 1. Parse the GPX data    
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
    
    return float(elevation_gain)

# Load data
