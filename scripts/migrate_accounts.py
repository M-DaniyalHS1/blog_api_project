"""Run from the project root: .venv/Scripts/python.exe scripts/migrate_accounts.py"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sqlalchemy import text, select, func
from database import engine, sessionlocal
from account_setup import initialize_admin
from auth import ADMIN_USERNAME, ADMIN_PASSWORD_HASH
import model

sql = (Path(__file__).resolve().parents[1] / "migrations/004_user_accounts.sql").read_text()
with engine.begin() as connection:
    for statement in sql.split(";"):
        if statement.strip():
            connection.execute(text(statement))
with sessionlocal() as db:
    before = db.scalar(select(func.count()).select_from(model.Blog))
    initialize_admin(db, ADMIN_USERNAME, ADMIN_PASSWORD_HASH)
    after = db.scalar(select(func.count()).select_from(model.Blog))
    unowned = db.scalar(select(func.count()).select_from(model.Blog).where(model.Blog.author_id.is_(None)))
    assert before == after and unowned == 0
print("Account migration verified: all existing posts preserved and assigned to admin.")
