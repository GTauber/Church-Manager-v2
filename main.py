import logging
from fastapi import FastAPI
from app.routers import waha

logging.basicConfig(level=logging.INFO)

app = FastAPI()

app.include_router(waha.router, prefix="/waha")


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
