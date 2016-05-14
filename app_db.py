#!venv/bin/python3

#from migrate.versioning import api
#from config import SQLALCHEMY_DATABASE_URI
#from config import SQLALCHEMY_MIGRATE_REPO
from wette import Base, engine
#import os.path

Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)

#if not os.path.exists(SQLALCHEMY_MIGRATE_REPO):
#    api.create(SQLALCHEMY_MIGRATE_REPO, 'database repository')
#    api.version_control(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
#else:
#    api.version_control(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO, api.version(SQLALCHEMY_MIGRATE_REPO))
