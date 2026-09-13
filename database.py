from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,declarative_base

DATABASE_URL = "postgresql:+psycopg2//postgres:1234@localhost:5432/blogdb"

engine = create_engine(DATABASE_URL)

sessionlocal = sessionmaker(bind = engine)

base = declarative_base()