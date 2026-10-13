"""Project 1.6: sign up, log in, and get your OWN private to-do list."""
import os

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from sqlalchemy import ForeignKey, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from security import create_token, hash_password, read_token, verify_password

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {})
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    password_hash: Mapped[str] = mapped_column(String(100))   # we store the HASH, never the password


class Todo(Base):
    __tablename__ = "todos"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    done: Mapped[bool] = mapped_column(default=False)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))   # each todo belongs to one user


Base.metadata.create_all(engine)
app = FastAPI(title="Login + private to-dos")
oauth2 = OAuth2PasswordBearer(tokenUrl="/login")   # tells /docs where to get a token (the 🔒 Authorize button)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def current_user(token: str = Depends(oauth2), db: Session = Depends(get_db)) -> User:
    """Runs before every protected route: turns the token into a User, or rejects with 401."""
    username = read_token(token)
    user = db.scalar(select(User).where(User.username == username)) if username else None
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token",
                            headers={"WWW-Authenticate": "Bearer"})
    return user


class SignUp(BaseModel):
    username: str = Field(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    password: str = Field(min_length=8, max_length=72)


class TodoIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)


class TodoOut(TodoIn):
    id: int
    done: bool


@app.post("/signup", status_code=201)
def signup(data: SignUp, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.username == data.username)):
        raise HTTPException(409, "Username already taken")       # 409 = conflict
    db.add(User(username=data.username, password_hash=hash_password(data.password)))
    db.commit()
    return {"message": f"Welcome, {data.username}! Now POST /login."}


@app.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.username == form.username))
    # Same error for "no such user" and "wrong password", so attackers can't discover usernames
    if user is None or not verify_password(form.password, user.password_hash):
        raise HTTPException(401, "Wrong username or password")
    return {"access_token": create_token(user.username), "token_type": "bearer"}


@app.get("/me")
def me(user: User = Depends(current_user)):
    return {"id": user.id, "username": user.username}


@app.post("/todos", response_model=TodoOut, status_code=201)
def add_todo(data: TodoIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    todo = Todo(title=data.title, owner_id=user.id)
    db.add(todo)
    db.commit()
    db.refresh(todo)
    return TodoOut(id=todo.id, title=todo.title, done=todo.done)


@app.get("/todos", response_model=list[TodoOut])
def my_todos(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(Todo).where(Todo.owner_id == user.id)).all()   # only YOUR todos
    return [TodoOut(id=t.id, title=t.title, done=t.done) for t in rows]


@app.get("/health")
def health():
    return {"status": "ok"}
