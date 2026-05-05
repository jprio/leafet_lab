import sys
import os
sys.path.append(os.path.join('..', 'src'))
from app.models.domain import GPXTrack
import psycopg2

import gpxpy
from geoalchemy2 import Geometry, WKTElement
import geopandas as gpd
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from geoalchemy2 import Geometry
from shapely.geometry import LineString

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker 


def get_engine():
    engine = create_engine(f'postgresql://{os.environ["AIVEN_USERNAME"]}:{os.environ["AIVEN_PASSWORD"]}@{os.environ["AIVEN_HOST"]}:{os.environ["AIVEN_PORT"]}/{os.environ["AIVEN_DBNAME"]}?sslmode=require')
    return  engine

def conn_aiven_test():
    conn = psycopg2.connect(f'postgres://{os.environ["AIVEN_USERNAME"]}:{os.environ["AIVEN_PASSWORD"]}@{os.environ["AIVEN_HOST"]}:{os.environ["AIVEN_PORT"]}/{os.environ["AIVEN_DBNAME"]}?sslmode=require')

    query_sql = 'SELECT VERSION()'

    cur = conn.cursor()
    cur.execute(query_sql)

    version = cur.fetchone()[0]
    print(version)

    add_postgis = "CREATE EXTENSION postgis;"
    cur.execute(add_postgis)
    conn.commit()

def create_tables():
    conn = psycopg2.connect(f'postgres://{os.environ["AIVEN_USERNAME"]}:{os.environ["AIVEN_PASSWORD"]}@{os.environ["AIVEN_HOST"]}:{os.environ["AIVEN_PORT"]}/{os.environ["AIVEN_DBNAME"]}?sslmode=require')
    cur = conn.cursor()
    # cur.execute("""
    #     CREATE TABLE IF NOT EXISTS tracks (
    #         id SERIAL PRIMARY KEY,
    #         geom GEOMETRY(Point, 4326)
    #     );
    # """)
    # cur.execute("""DROP TABLE IF EXISTS gpx_tracks;""")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS gpx_tracks (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255),
            geom GEOMETRY(LINESTRING, 4326)
        );
    """)
    conn.commit()

def test_save_gpx():
    import glob

    files = glob.glob("tests/gpx/*.gpx")
    engine = create_engine(f'postgresql://{os.environ["AIVEN_USERNAME"]}:{os.environ["AIVEN_PASSWORD"]}@{os.environ["AIVEN_HOST"]}:{os.environ["AIVEN_PORT"]}/{os.environ["AIVEN_DBNAME"]}?sslmode=require')
    for file in files:
        # 1. Charger et parser le GPX
        with open(file, "r") as f:
            gpx = gpxpy.parse(f)

        # 2. Extraire les données (exemple pour les waypoints)
        points = []
        for track in gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    # Création de l'élément géométrique WKT pour PostGIS
                    wkt = f"POINT({point.longitude} {point.latitude})"
                    points.append(WKTElement(wkt, srid=4326))

        # 3. Insertion via GeoAlchemy2/SQLAlchemy
        # (Supposant une session et une table 'tracks' déjà définies)
        Session = sessionmaker(bind=engine)
        session = Session()
        for track in gpx.tracks:
            points = [(point.longitude, point.latitude) for segment in track.segments for point in segment.points]
            line_string = LineString(points)
            
            # Convert to WKT for insertion
            wkt = line_string.wkt
            
            new_track = GPXTrack(name=track.name, geom=WKTElement(wkt, srid=4326))
            session.add(new_track)
            print(f"Inserted track: {track.name} with {len(points)} points.")
            session.commit()    
            # Insertion directe ou via GeoPandas.to_postgis avec dtype={'geometry': Geometry('POINT', srid=4326)}

# create_tables()
def test_postgis_to_geojson():
    engine = get_engine()
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker 
    from geojson import Feature, FeatureCollection
    from geoalchemy2.shape import to_shape

    import geojson
    Base = declarative_base()

    Session = sessionmaker(bind=engine)
    session = Session()

    # SELECT ST_AsGeoJSON(geom) FROM table
    # trx=session.query(GPXTrack.name, GPXTrack.geom.ST_AsGeoJSON()).filter(
    trx=session.query(GPXTrack.name, GPXTrack.geom).filter(
        GPXTrack.id == 34)
    import shapely.geometry
    features = []
    for name, geom in trx:
        feature = Feature(
                id=1,
                geometry=shapely.geometry.mapping(to_shape(geom)),
                properties={"name": name}
            )
        features.append(feature)
        collection = FeatureCollection(features)
        print(collection)
        # geojson_geometry = shapely.geometry.mapping(geom_json)
        # print(f"Track: {name}, Geometry (GeoJSON): {geom_json[:100]}")    
        # print(feature = geojson.Feature(geometry=geojson_geometry)


def pandas_read_postgis_to_geojson():
    engine = get_engine()
    gdf = gpd.read_postgis("SELECT name, geom FROM gpx_tracks", con=engine, geom_col='geom')
    print(gdf.head())
    # gdf.to_file("gpx_tracks.geojson", driver='GeoJSON')
    print(gdf.shape)
    

def alchemy_test():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    import pyproj
    from shapely.ops import transform
    from functools import partial
    from geoalchemy2.shape import to_shape

    engine = create_engine(
        f'postgresql://{os.environ["AIVEN_USERNAME"]}:{os.environ["AIVEN_PASSWORD"]}@{os.environ["AIVEN_HOST"]}:{os.environ["AIVEN_PORT"]}/{os.environ["AIVEN_DBNAME"]}?sslmode=require',
        echo=True,
        plugins=["geoalchemy2"]
    )

    Session = sessionmaker(bind=engine)
    session = Session()
    locations = session.query(GPXTrack).filter(GPXTrack.name.like('%Lake%')).all()
    for location in locations:
        print("gpx trouvé : " + str(location.name))
        # print("geom : " + str(location.geom))
        # print("length : " + str(type(location.geom)))
        shapely_point = to_shape(location.geom)
        # print("shapely_point : " + str(shapely_point))
        print("shapely_point length : " + str(shapely_point.length*100))
        # Transform to a projected CRS (e.g., UTM Zone 33N)
        # project = partial(
        #     pyproj.transform,
        #     pyproj.Proj('EPSG:4326'),
        #     pyproj.Proj('EPSG:32633')
        # )
        # line_projected = transform(project, location.geom)

        # # Length is now in meters
        # print(line_projected.length)

def alchemy_test_mean_location():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    import pandas as pd
    engine = create_engine(
        f'postgresql://{os.environ["AIVEN_USERNAME"]}:{os.environ["AIVEN_PASSWORD"]}@{os.environ["AIVEN_HOST"]}:{os.environ["AIVEN_PORT"]}/{os.environ["AIVEN_DBNAME"]}?sslmode=require',
        echo=True,
        plugins=["geoalchemy2"]
    )
    Session = sessionmaker(bind=engine)
    session = Session()
    query = "SELECT AVG(ST_Y(ST_Centroid(geom))) AS mean_latitude, AVG(ST_X(ST_Centroid(geom))) AS mean_longitude FROM gpx_tracks;"
    # locations = session.query(GPXTrack).filter("SELECT AVG(ST_Y(geom)) AS mean_latitude FROM your_table_name;").all()
    df_mean = pd.read_sql(query, engine.connect())
    print(df_mean)

# pandas_read_postgis_to_geojson()
test_postgis_to_geojson()
# test_save_gpx()
# alchemy_test()
# alchemy_test_mean_location()