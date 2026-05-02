import os
from sqlalchemy import text
from typing import List
from typing import Optional
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy import Table, Column, Integer, String, MetaData, Sequence, Identity
from geoalchemy2 import Geometry, WKTElement
from shapely.geometry import LineString
from sqlalchemy import event
from sqlalchemy.orm import attributes
from geoalchemy2.shape import to_shape

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "user_account"
    id: Mapped[int] = mapped_column(primary_key=True)
    # id = Column(Integer, Identity(start=1), primary_key=True)
    name: Mapped[str] = mapped_column(String(30))
    fullname: Mapped[Optional[str]]
    collections: Mapped[List["Collection"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    def __repr__(self) -> str:
        return f"User(id={self.id!r}, name={self.name!r}, fullname={self.fullname!r})"
    
class Collection(Base):
    __tablename__ = "collection"
    # id: Mapped[int] = mapped_column(primary_key=True, )
    id = Column(Integer, Identity(start=1), primary_key=True)
    
    name: Mapped[str]
    user_id: Mapped[int] = mapped_column(ForeignKey("user_account.id"))
    user: Mapped["User"] = relationship(back_populates="collections")

    def __repr__(self) -> str:
        return f"Collection(id={self.id!r}, name={self.name!r})"
    
class Trail(Base):
    __tablename__ = "trail"
    # id: Mapped[int] = mapped_column(primary_key=True, )
    id = Column(Integer, Identity(start=1), primary_key=True)

    name: Mapped[str]
    type: Mapped[str]
    distance: Mapped[float]
    elevation_gain: Mapped[float]
    start_point_latitude: Mapped[float]
    end_point_longitude: Mapped[float]
    duration: Mapped[float]
    ranking: Mapped[float]
    # tags: Mapped[List[str]]
    description: Mapped[str]
    def __repr__(self) -> str:
        return f"Trail(id={self.id!r}, name={self.name!r})"
    
# Base = declarative_base()

class Track(Base):
    __tablename__ = 'tracks'
    id = Column(Integer, primary_key=True)
    geom = Column(Geometry('POINT', srid=4326))

class GPXTrack(Base):
    __tablename__ = 'gpx_tracks'
    __allow_unmapped__ = True
    id = Column(Integer, primary_key=True)
    name = Column(String)
    type = Column(String)
    owner = Column(Integer, nullable=False)
    geom = Column(Geometry(geometry_type='LINESTRING', srid=4326))
    length: int
    def __repr__(self) -> str:
        return f"Trail(id={self.id!r}, name={self.name!r}, length={self.length!r})"

@event.listens_for(GPXTrack, "load")
def load_b(track, context):
    print("Loading GPXTrack instance with id:", track.id)
    shapely_point = to_shape(track.geom)
    track.length = shapely_point.length * 100
    # if "length" in track.__dict__:
    #     attributes.set_committed_value(track, track.length, 12)

    print(track)