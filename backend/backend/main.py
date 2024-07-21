from typing import Union

from fastapi import FastAPI
from sqlmodel import create_engine, delete, select, Session


from backend.settings import get_url
from backend.models import User, Venue, Artist, Booking, Event, Seat

app = FastAPI()
engine = create_engine(get_url(), echo=True)


@app.get("/venues/{venue_id}")
def read_venue(venue_id: int):
    with Session(engine) as session:
        statement = select(Venue).where(Venue.id == venue_id)
        results = session.exec(statement)
        venue = results.one()
    return venue


@app.post("/venues/")
def create_venue(venue: Venue):
    with Session(engine) as session:
        session.add(venue)
        session.commit()
    return venue


@app.get("/seed")
def seed(seats: int = 50000, users: int = 100000):
    with Session(engine) as session:
        artist = Artist(name="Dropkick Murphys")
        session.add(artist)
        venue = Venue(
            name="Norva",
            description="Very hip venue downtown Norfolk",
            address="100 Granby Ave",
        )
        session.add(venue)
        event = Event(venue_id=venue.id, artist_id=artist.id)
        session.add(event)
        for _ in range(seats):
            session.add(Seat(venue_id=venue.id))
        for _ in range(users):
            session.add(User())
        session.commit()
    return {"status": "success"}


@app.delete("/truncate")
def truncate():
    with Session(engine) as session:
        session.exec(delete(Artist))
        session.exec(delete(Booking))
        session.exec(delete(Event))
        session.exec(delete(Seat))
        session.exec(delete(User))
        session.exec(delete(Venue))
        session.commit()
    return {"status": "success"}
