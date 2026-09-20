from fastapi import FastAPI, Depends, HTTPException,Query, Request
from chatbot import ChatQuestion, answer_question
from auth import SECRET_KEY
from database import engine, sessionlocal
from sqlalchemy.orm import Session
import model, schemas
from auth import (create_token, verify_token, verify_password, password_hash,
                  DUMMY_PASSWORD_HASH, ADMIN_USERNAME, ADMIN_PASSWORD_HASH, ACCESS_TOKEN_EXPIRE_MINUTES)
from account_setup import initialize_admin
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from sqlalchemy import select, update, or_
from sqlalchemy.exc import IntegrityError, OperationalError
import asyncio
import logging
from sqlalchemy.orm import joinedload

from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware

def initialize_database():
    model.base.metadata.create_all(bind=engine)
    with sessionlocal() as db:
        initialize_admin(db, ADMIN_USERNAME, ADMIN_PASSWORD_HASH)


async def connect_database():
    for attempt in range(5):
        try:
            await asyncio.to_thread(initialize_database)
            return
        except OperationalError as exc:
            dns_failure = "temporary failure in name resolution" in str(exc.orig).lower()
            if not dns_failure or attempt == 4:
                raise
            logging.getLogger(__name__).warning("Temporary database DNS failure; retrying startup (%s/4).", attempt + 1)
            await asyncio.sleep(2 ** (attempt + 1))


@asynccontextmanager
async def lifespan(app):
    await connect_database()
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


@app.post("/chat")
def chat(question: ChatQuestion, request: Request, db: Session = Depends(get_db)):
    return answer_question(db, question, request.client.host if request.client else "unknown", SECRET_KEY)


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
    posts = db.query(model.Blog).filter(model.Blog.author_id == author_id, model.Blog.status == "published").order_by(model.Blog.id.desc())
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
    if blog.status == "published" and (not blog.title.strip() or not blog.content.strip()):
        raise HTTPException(422, "Title and full article are required to publish")
    new_blog = model.Blog(
        title=blog.title,
        content=blog.content,
        summary=blog.summary,
        image_url=blog.image_url,
        source_url=blog.source_url,
        author_id=user.id,
        status=blog.status,
        category=blog.category,
        published_at=datetime.now(timezone.utc) if blog.status == "published" else None
    )
    db.add(new_blog)
    db.commit()
    db.refresh(new_blog)

    return new_blog

# Read all blogs (ordered by ID)
@app.get("/blogs")
def get_table(page:int = Query(1, ge=1),
              limit:int = Query(5, ge=1, le=50),
              search:str = Query(default="", max_length=200),
              category: schemas.Category | None = None,
              db: Session = Depends(get_db)):
    query = db.query(model.Blog).options(joinedload(model.Blog.author)).filter(model.Blog.status == "published")
    term = search.strip()
    if term:
        # Escape SQL wildcard characters so user searches are literal substrings.
        escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        pattern = f"%{escaped}%"
        query = query.filter(or_(model.Blog.title.ilike(pattern, escape="\\"),
                                 model.Blog.content.ilike(pattern, escape="\\"),
                                 model.Blog.summary.ilike(pattern, escape="\\")))
    if category:
        query = query.filter(model.Blog.category == category)
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

@app.get("/me/posts")
def my_posts(page: int = Query(1, ge=1), limit: int = Query(10, ge=1, le=50), user: model.User = Depends(current_user), db: Session = Depends(get_db)):
    query = db.query(model.Blog).filter(model.Blog.author_id == user.id).order_by(model.Blog.id.desc())
    return {"total": query.count(), "page": page, "data": [schemas.BlogResponse.model_validate(post) for post in query.offset((page - 1) * limit).limit(limit).all()]}


# Read one blog
@app.get("/blogs/{id}", response_model=schemas.BlogResponse)
def get_blog(id: int, db: Session = Depends(get_db)):
    blog = db.query(model.Blog).filter(model.Blog.id == id, model.Blog.status == "published").first()

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

    next_status = blog.status if "status" in blog.model_fields_set else existing_blog.status
    if next_status == "published" and (not blog.title.strip() or not blog.content.strip()):
        raise HTTPException(422, "Title and full article are required to publish")
    if next_status == "published" and existing_blog.status == "draft" and existing_blog.published_at is None:
        existing_blog.published_at = datetime.now(timezone.utc)
    existing_blog.status = next_status
    if "category" in blog.model_fields_set:
        existing_blog.category = blog.category
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


optional_oauth = OAuth2PasswordBearer(tokenUrl="login", auto_error=False)


def optional_user(token: str | None = Depends(optional_oauth), db: Session = Depends(get_db)):
    return current_user(verify_token(token), db) if token else None


def published_post(db, blog_id):
    post = db.get(model.Blog, blog_id)
    if not post or post.status != "published":
        raise HTTPException(404, "Post not found")
    return post


@app.get("/blogs/{blog_id}/comments")
def comments(blog_id: int, page: int = Query(1, ge=1), limit: int = Query(10, ge=1, le=50), db: Session = Depends(get_db)):
    published_post(db, blog_id)
    query = db.query(model.Comment).options(joinedload(model.Comment.author)).filter(model.Comment.blog_id == blog_id).order_by(model.Comment.id.desc())
    return {"total": query.count(), "page": page, "data": [schemas.CommentPublic.model_validate(comment) for comment in query.offset((page - 1) * limit).limit(limit).all()]}


@app.post("/blogs/{blog_id}/comments", response_model=schemas.CommentPublic, status_code=201)
def add_comment(blog_id: int, body: schemas.CommentWrite, user: model.User = Depends(current_user), db: Session = Depends(get_db)):
    published_post(db, blog_id)
    comment = model.Comment(blog_id=blog_id, user_id=user.id, content=body.content)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def owned_comment(db, blog_id, comment_id, user):
    published_post(db, blog_id)
    comment = db.get(model.Comment, comment_id)
    if not comment or comment.blog_id != blog_id:
        raise HTTPException(404, "Comment not found")
    if comment.user_id != user.id:
        raise HTTPException(403, "You can only change your own comments")
    return comment


@app.put("/blogs/{blog_id}/comments/{comment_id}", response_model=schemas.CommentPublic)
def edit_comment(blog_id: int, comment_id: int, body: schemas.CommentWrite, user: model.User = Depends(current_user), db: Session = Depends(get_db)):
    comment = owned_comment(db, blog_id, comment_id, user)
    comment.content = body.content
    comment.edited_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(comment)
    return comment


@app.delete("/blogs/{blog_id}/comments/{comment_id}", status_code=204)
def remove_comment(blog_id: int, comment_id: int, user: model.User = Depends(current_user), db: Session = Depends(get_db)):
    db.delete(owned_comment(db, blog_id, comment_id, user))
    db.commit()


def reaction_summary(db, blog_id, user):
    return {"count": db.query(model.Like).filter(model.Like.blog_id == blog_id).count(),
            "liked": bool(user and db.get(model.Like, (blog_id, user.id)))}


@app.get("/blogs/{blog_id}/reactions")
def reactions(blog_id: int, user: model.User | None = Depends(optional_user), db: Session = Depends(get_db)):
    published_post(db, blog_id)
    return reaction_summary(db, blog_id, user)


@app.put("/blogs/{blog_id}/like")
def like_post(blog_id: int, user: model.User = Depends(current_user), db: Session = Depends(get_db)):
    published_post(db, blog_id)
    if not db.get(model.Like, (blog_id, user.id)):
        db.add(model.Like(blog_id=blog_id, user_id=user.id))
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            published_post(db, blog_id)
            if not db.get(model.Like, (blog_id, user.id)):
                raise
    return reaction_summary(db, blog_id, user)


@app.delete("/blogs/{blog_id}/like")
def unlike_post(blog_id: int, user: model.User = Depends(current_user), db: Session = Depends(get_db)):
    published_post(db, blog_id)
    db.query(model.Like).filter(model.Like.blog_id == blog_id, model.Like.user_id == user.id).delete()
    db.commit()
    return reaction_summary(db, blog_id, user)
