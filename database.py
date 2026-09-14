from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,declarative_base
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URl = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URl)

sessionlocal = sessionmaker(bind = engine)

base = declarative_base()