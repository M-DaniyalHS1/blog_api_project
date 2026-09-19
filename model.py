from sqlalchemy import Column,Integer,String,Text,DateTime,func
 
from database import base

#Blog Table
class Blog(base):

    __tablename__ = "blogs"

    id = Column(Integer,primary_key = True,index = True)
    title = Column(String)
    content = Column(Text)
    image_url = Column(Text, nullable=True)
    source_url = Column(Text, nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True, server_default=func.now())
