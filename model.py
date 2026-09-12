from sqlalchemy import Column,Integer,String,Text
 
from database import base

#Blog Table
class Blog(base):

    __tablename__ = "blogs"

    id = Column(Integer,primary_key = True,index = True)
    title = Column(String)
    content = Column(Text)