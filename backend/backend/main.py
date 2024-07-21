from fastapi import FastAPI
from sqlmodel import create_engine, delete, select, Session
from redlock import Redlock
import time
import random

from backend.settings import get_url
from backend.models import User, Venue, Artist, Booking, Event, Seat

app = FastAPI()
engine = create_engine(get_url(), echo=True)
dlm = Redlock(
    [
        {"host": "redis", "port": 6379, "db": 0},
    ]
)


@app.post("/bookings/")
def create_booking(booking: Booking):
    lock = dlm.lock(f"seat_{booking.seat_id}", 10000)
    if not lock:
        return {"status": "failed due to lock"}

    with Session(engine) as session:
        statement = select(Booking).where(
            Booking.event_id == booking.event_id and Booking.seat_id == booking.seat_id
        )
        results = session.exec(statement)
        booking = results.one_or_none()
        if booking:
            return {"status": "Failed, seat booked"}

    time.sleep(max(0.05, random.gauss(0.4, 0.1)))  # wait a tiny bit
    with Session(engine) as session:
        session.add(booking)
        session.commit()
    dlm.unlock(lock)
    return booking


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
        session.commit()
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
