"""Preserve the configured admin and assign pre-account posts on startup."""
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
import model


def initialize_admin(db, username, password_hash):
    username = username.strip().lower()
    user = db.scalar(select(model.User).where(model.User.username == username))
    if user is None:
        user = model.User(username=username, password_hash=password_hash, is_admin=True)
        db.add(user)
        try:
            db.flush()
        except IntegrityError:
            # Another worker may have created the same admin during startup.
            db.rollback()
            user = db.scalar(select(model.User).where(model.User.username == username))
    if not user or not user.is_admin:
        raise RuntimeError("Configured admin username conflicts with an existing account.")
    if user.password_hash != password_hash:
        user.password_hash = password_hash
        user.token_version += 1
    db.execute(update(model.Blog).where(model.Blog.author_id.is_(None)).values(author_id=user.id))
    db.commit()
    return user
