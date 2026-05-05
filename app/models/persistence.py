from sqlalchemy import create_engine, Column, Integer, String 
import os

def get_engine():
    engine = create_engine(f'postgresql://{os.environ["AIVEN_USERNAME"]}:{os.environ["AIVEN_PASSWORD"]}@{os.environ["AIVEN_HOST"]}:{os.environ["AIVEN_PORT"]}/{os.environ["AIVEN_DBNAME"]}?sslmode=require')
    return  engine

def get_geo_engie():    
    engine = create_engine(
        f'postgresql://{os.environ["AIVEN_USERNAME"]}:{os.environ["AIVEN_PASSWORD"]}@{os.environ["AIVEN_HOST"]}:{os.environ["AIVEN_PORT"]}/{os.environ["AIVEN_DBNAME"]}?sslmode=require',
        echo=True,
        plugins=["geoalchemy2"]
    )
    return engine
