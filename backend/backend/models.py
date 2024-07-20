from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)


class Venue(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: str
    address: str


class Artist(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str


class Event(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    venue_id: int | None = Field(default=None, foreign_key="venue.id")
    artist_id: int | None = Field(default=None, foreign_key="artist.id")
    occurring_at: datetime = Field(default_factory=datetime.utcnow)


class Seat(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    venue_id: int | None = Field(default=None, foreign_key="venue.id")


class Booking(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int | None = Field(default=None, foreign_key="user.id")
    event_id: int | None = Field(default=None, foreign_key="event.id")
    seat_id: int | None = Field(default=None, foreign_key="seat.id")
