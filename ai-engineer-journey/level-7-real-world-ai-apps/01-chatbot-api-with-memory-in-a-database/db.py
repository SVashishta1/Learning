"""Two tables: conversations and messages. Memory = every message saved in order."""
import os
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL", "sqlite:///./chat.db"), connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine)
now = lambda: datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Conversation(Base):
    __tablename__ = "conversations"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), default="New chat")
    persona: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Message(Base):
    __tablename__ = "messages"
    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"), index=True)
    role: Mapped[str] = mapped_column(String(20))           # "user" or "assistant"
    content: Mapped[str] = mapped_column(Text)
    input_tokens: Mapped[int] = mapped_column(default=0)
    output_tokens: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


Base.metadata.create_all(engine)


def history(db, conversation_id: int, limit: int = 40) -> list[dict]:
    """The last `limit` messages, oldest first, in the shape the Claude API expects."""
    rows = db.scalars(select(Message).where(Message.conversation_id == conversation_id)
                      .order_by(Message.id.desc()).limit(limit)).all()[::-1]
    msgs = [{"role": m.role, "content": m.content} for m in rows]
    while msgs and msgs[0]["role"] != "user":     # the API requires the first message to be from the user
        msgs.pop(0)
    return msgs
