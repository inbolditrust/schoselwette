#!venv/bin/python3

from wette import Base, engine

Base.metadata.create_all(engine)
