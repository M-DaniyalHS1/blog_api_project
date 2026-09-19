from fastapi import FastAPI, Depends, HTTPException,Query
from database import engine, sessionlocal
from sqlalchemy.orm import Session
import model, schemas
from auth import authenticate_admin,create_token,verify_token

from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware

model.base.metadata.create_all(bind=engine)

app = FastAPI()

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

#login api
@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if not authenticate_admin(form_data.username, form_data.password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {
        "access_token":create_token(form_data.username),
        "token_type":"bearer"
    }

# Home route
@app.get("/")
def home():
    return {
        "message": "Blog API Started"
    }

# Create Blog
@app.post("/blogs", response_model=schemas.BlogResponse)
def create_blog(blog: schemas.BlogCreate, db: Session = Depends(get_db), user = Depends(verify_token)):
    new_blog = model.Blog(
        title=blog.title,
        content=blog.content,
        summary=blog.summary,
        image_url=blog.image_url,
        source_url=blog.source_url
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
    query = db.query(model.Blog)
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
        "data":blogs

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
    user: dict = Depends(verify_token),
):
    # Keep your existing update code here.
    existing_blog = db.query(model.Blog).filter(model.Blog.id == id).first()

    if not existing_blog:
        raise HTTPException(status_code=404, detail="blog not found")
    
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
def delete_blog(id: int, db: Session = Depends(get_db),user = Depends(verify_token)):
    blog = db.query(model.Blog).filter(model.Blog.id == id).first()

    if not blog:
        raise HTTPException(status_code=404, detail="blog not found.......")
    
    db.delete(blog)
    db.commit()
    return {
        "message": f"blog id = {id} deleted succesfully"
    }
