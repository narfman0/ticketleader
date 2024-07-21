from typing import Union

from fastapi import FastAPI
from sqlmodel import create_engine, select, Session


from backend.settings import get_url
from backend.models import Venue

app = FastAPI()
engine = create_engine(get_url(), echo=True)


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}


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
