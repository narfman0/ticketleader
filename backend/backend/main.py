import time
import random

import asyncio
from fastapi import FastAPI, HTTPException
from sqlmodel import create_engine, delete, select, Session
from redlock import Redlock, Lock
from redis import Redis
from sqlalchemy import func
import httpx

from backend.settings import get_url, get_redis_password
from backend.models import User, Venue, Artist, Booking, Event, Seat, LockStruct

BATCH_SIZE = 8
LOCK_S = 10
LOCK_MS = LOCK_S * 1000
app = FastAPI()
engine = create_engine(get_url(), echo=True)
dlm = Redlock(
    [
        {"host": "redis", "port": 6379, "password": get_redis_password(), "db": 0},
    ]
)
r = Redis(host="redis", password=get_redis_password(), port=6379, decode_responses=True)


def reservation_key_from_booking(booking: Booking) -> str:
    return f"res_event_{booking.event_id}_seat_{booking.seat_id}"


def booking_key_from_booking(booking: Booking) -> str:
    return f"booking_event_{booking.event_id}_seat_{booking.seat_id}"


def check_preexisting_booking(booking: Booking):
    if r.get(booking_key_from_booking(booking)):
        raise HTTPException(
            status_code=400,
            detail={
                "message": f"Seat already booked [redis]",
                "seat": booking.seat_id,
            },
        )
    with Session(engine) as session:
        statement = (
            select(Booking)
            .where(Booking.event_id == booking.event_id)
            .where(Booking.seat_id == booking.seat_id)
        )
        results = session.exec(statement)
        if results.first():
            raise HTTPException(
                status_code=400,
                detail={
                    "message": f"Seat already booked [db]",
                    "seat": booking.seat_id,
                },
            )


@app.get("/bookings")
def list_bookings() -> list[Booking]:
    with Session(engine) as session:
        return session.exec(select(Booking)).all()


async def async_post(url):
    async with httpx.AsyncClient() as client:
        return (await client.post(url)).json()


async def async_post_all(urls):
    return await asyncio.gather(*[async_post(url) for url in urls])


@app.post("/bookings/create_random_bookings")
def create_random_bookings(count: int = 50000):
    create_endpoint = "http://localhost:8000" + app.url_path_for(
        create_random_booking.__name__
    )
    responses = []
    for _ in range(count // BATCH_SIZE):
        responses.extend(asyncio.run(async_post_all([create_endpoint] * BATCH_SIZE)))
    return {
        "status": "success",
        "responses": responses,
    }


@app.post("/bookings/create_random_booking")
def create_random_booking() -> Booking:
    with Session(engine) as session:
        user = session.exec(select(User).order_by(func.random())).first()
        event = session.exec(select(Event).order_by(func.random())).first()
        seat = session.exec(
            select(Seat).where(Seat.venue_id == event.venue_id).order_by(func.random())
        ).first()
        booking = Booking(user_id=user.id, event_id=event.id, seat_id=seat.id)
        reserve_booking(booking)
        time.sleep(max(0.05, random.gauss(0.1, 0.1)))
        finalize_booking(booking)
        return booking


@app.post("/bookings/reserve")
def reserve_booking(booking: Booking):
    check_preexisting_booking(booking)
    key = reservation_key_from_booking(booking)
    lock = dlm.lock(key, LOCK_MS)
    if not lock:
        raise HTTPException(status_code=400, detail="Seat locked by another user")
    lock_str = LockStruct(user_id=booking.user_id, lock=lock)
    r.set(key, lock_str.model_dump_json(), ex=LOCK_S)
    return booking


@app.post("/bookings/finalize")
def finalize_booking(booking: Booking):
    key = reservation_key_from_booking(booking)
    lock_json = r.get(key)
    if not lock_json:
        raise HTTPException(status_code=400, detail="Lock expired")
    lock_str = LockStruct.model_validate_json(r.get(key))
    if lock_str.user_id != booking.user_id:
        raise HTTPException(status_code=401, detail="Lock doesn't belong to you")
    check_preexisting_booking(booking)

    with Session(engine) as session:
        session.add(booking)
        session.commit()
        r.set(booking_key_from_booking(booking), booking.user_id, ex=600)
    dlm.unlock(lock_str.lock)
    return booking


@app.post("/seed")
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
        session.exec(delete(Booking))
        session.exec(delete(Event))
        session.exec(delete(Artist))
        session.exec(delete(Seat))
        session.exec(delete(User))
        session.exec(delete(Venue))
        session.commit()
    return {"status": "success"}
