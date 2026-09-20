from fastapi import FastAPI, Depends, HTTPException,Query
from database import engine, sessionlocal
from sqlalchemy.orm import Session
import model, schemas
from auth import (create_token, verify_token, verify_password, password_hash,
                  DUMMY_PASSWORD_HASH, ADMIN_USERNAME, ADMIN_PASSWORD_HASH, ACCESS_TOKEN_EXPIRE_MINUTES)
from account_setup import initialize_admin
from contextlib import asynccontextmanager
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app):
    model.base.metadata.create_all(bind=engine)
    with sessionlocal() as db:
        initialize_admin(db, ADMIN_USERNAME, ADMIN_PASSWORD_HASH)
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DB Dependency
def get_db():
    db = sessionlocal()
    try:
        yield db
    finally:
        db.close()

def current_user(payload: dict = Depends(verify_token), db: Session = Depends(get_db)):
    user = db.get(model.User, int(payload["sub"]))
    if not user or user.token_version != payload["ver"]:
        raise HTTPException(401, "Invalid or expired session", headers={"WWW-Authenticate": "Bearer"})
    return user


@app.post("/register", response_model=schemas.UserPublic, status_code=201)
def register(account: schemas.UserRegister, db: Session = Depends(get_db)):
    if account.username == ADMIN_USERNAME.strip().lower():
        raise HTTPException(409, "Username is already taken")
    user = model.User(username=account.username, password_hash=password_hash.hash(account.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Username is already taken")
    db.refresh(user)
    return user


@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    username = form_data.username.strip().lower()
    user = db.scalar(select(model.User).where(model.User.username == username))
    valid = verify_password(form_data.password, user.password_hash if user else DUMMY_PASSWORD_HASH)
    if not user or not valid:
        raise HTTPException(401, "Incorrect username or password", headers={"WWW-Authenticate": "Bearer"})
    return {"access_token": create_token(user.id, user.token_version), "token_type": "bearer", "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": schemas.ProfilePublic.model_validate(user)}


@app.get("/me", response_model=schemas.ProfilePublic)
def me(user: model.User = Depends(current_user)):
    return user


@app.patch("/me/profile", response_model=schemas.ProfilePublic)
def edit_profile(profile: schemas.ProfileUpdate, user: model.User = Depends(current_user), db: Session = Depends(get_db)):
    for name, value in profile.model_dump(exclude_unset=True).items():
        setattr(user, name, value)
    db.commit()
    db.refresh(user)
    return user


@app.get("/authors/{author_id}")
def author_profile(author_id: int, page: int = Query(1, ge=1), limit: int = Query(12, ge=1, le=50), db: Session = Depends(get_db)):
    author = db.get(model.User, author_id)
    if not author:
        raise HTTPException(404, "Author not found")
    # All current posts are published; Task 4 will introduce draft filtering.
    posts = db.query(model.Blog).filter(model.Blog.author_id == author_id).order_by(model.Blog.id.desc())
    return {"author": schemas.ProfilePublic.model_validate(author), "total": posts.count(), "page": page,
            "data": [schemas.BlogResponse.model_validate(post) for post in posts.offset((page - 1) * limit).limit(limit).all()]}


@app.post("/logout", status_code=204)
def logout(user: model.User = Depends(current_user), db: Session = Depends(get_db)):
    # Atomic increment invalidates every previously issued token for this user.
    db.execute(update(model.User).where(model.User.id == user.id).values(token_version=model.User.token_version + 1))
    db.commit()


# Home route
@app.get("/")
def home():
    return {
        "message": "Blog API Started"
    }

# Create Blog
@app.post("/blogs", response_model=schemas.BlogResponse)
def create_blog(blog: schemas.BlogCreate, db: Session = Depends(get_db), user = Depends(current_user)):
    new_blog = model.Blog(
        title=blog.title,
        content=blog.content,
        summary=blog.summary,
        image_url=blog.image_url,
        source_url=blog.source_url,
        author_id=user.id
    )
    db.add(new_blog)
    db.commit()
    db.refresh(new_blog)

    return new_blog

# Read all blogs (ordered by ID)
@app.get("/blogs")
def get_table(page:int = 1,
              limit:int = 5,
              search:str = Query(default=""),
              db: Session = Depends(get_db)):
    query = db.query(model.Blog).options(joinedload(model.Blog.author))
    if search:
        query = query.filter(model.Blog.title.ilike(f"%{search}%"))
    query = query.order_by(model.Blog.id.desc())
    total = query.count()
    start = (page -1) * limit
    blogs = query.offset(start).limit(limit).all()

    return {
        "page":page,
        "limit":limit,
        "total":total,
        "data":[schemas.BlogResponse.model_validate(blog) for blog in blogs]

    }

# Read one blog
@app.get("/blogs/{id}", response_model=schemas.BlogResponse)
def get_blog(id: int, db: Session = Depends(get_db)):
    blog = db.query(model.Blog).filter(model.Blog.id == id).first()

    if not blog:
        raise HTTPException(status_code=404, detail="blog not found")
    return blog

# Update blog api
@app.put("/blogs/{id}", response_model=schemas.BlogResponse)
def update_blog(
    id: int,
    blog: schemas.BlogCreate,
    db: Session = Depends(get_db),
    user: model.User = Depends(current_user),
):
    # Keep your existing update code here.
    existing_blog = db.query(model.Blog).filter(model.Blog.id == id).first()

    if not existing_blog:
        raise HTTPException(status_code=404, detail="blog not found")
    
    if existing_blog.author_id != user.id:
        raise HTTPException(403, "You can only edit your own posts")

    existing_blog.title = blog.title
    existing_blog.content = blog.content
    if "summary" in blog.model_fields_set:
        existing_blog.summary = blog.summary
    if "image_url" in blog.model_fields_set:
        existing_blog.image_url = blog.image_url
    
    if "source_url" in blog.model_fields_set:
        existing_blog.source_url = blog.source_url

    db.commit()
    db.refresh(existing_blog)  # Fixed: passed existing_blog here
    return existing_blog

# Delete blog api {protected}
@app.delete("/blogs/{id}")
def delete_blog(id: int, db: Session = Depends(get_db),user = Depends(current_user)):
    blog = db.query(model.Blog).filter(model.Blog.id == id).first()

    if not blog:
        raise HTTPException(status_code=404, detail="blog not found.......")
    
    if blog.author_id != user.id:
        raise HTTPException(403, "You can only delete your own posts")

    db.delete(blog)
    db.commit()
    return {
        "message": f"blog id = {id} deleted succesfully"
    }
