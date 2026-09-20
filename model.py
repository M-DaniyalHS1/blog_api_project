from sqlalchemy import Column,Integer,String,Text,DateTime,func,Boolean,ForeignKey
 
from database import base
from sqlalchemy.orm import relationship

#Blog Table
class Blog(base):

    __tablename__ = "blogs"

    id = Column(Integer,primary_key = True,index = True)
    title = Column(String)
    content = Column(Text)
    image_url = Column(Text, nullable=True)
    source_url = Column(Text, nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    summary = Column(Text, nullable=True)
    category = Column(String(32), nullable=False, default="General", server_default="General")
    status = Column(String(16), nullable=False, default="published", server_default="published")
    author_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    author = relationship("User")
    comments = relationship("Comment", cascade="all, delete-orphan")
    likes = relationship("Like", cascade="all, delete-orphan")


class User(base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    password_hash = Column(Text, nullable=False)
    is_admin = Column(Boolean, nullable=False, default=False, server_default="false")
    token_version = Column(Integer, nullable=False, default=0, server_default="0")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    display_name = Column(String(80), nullable=True)
    bio = Column(Text, nullable=True)
    avatar_url = Column(Text, nullable=True)


class Comment(base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True)
    blog_id = Column(Integer, ForeignKey("blogs.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    edited_at = Column(DateTime(timezone=True), nullable=True)
    author = relationship("User")


class Like(base):
    __tablename__ = "likes"
    blog_id = Column(Integer, ForeignKey("blogs.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
