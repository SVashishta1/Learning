"""Project 7.1: a chatbot API with memory. Conversations live in a database, so the bot remembers you
across requests and server restarts. Includes a STREAMING endpoint (words appear as they're generated)."""
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

import llm
from db import Conversation, Message, Session, history

app = FastAPI(title="Chatbot with memory")
client = None    # created lazily so tests can swap in a fake


def get_llm():
    global client
    if client is None:
        client = llm.get_client()
    return client


DEFAULT_PERSONA = "You are a friendly, concise study buddy. Use simple words. Ask a follow-up question when helpful."


class NewChat(BaseModel):
    persona: str = Field(DEFAULT_PERSONA, max_length=2000)


class UserMessage(BaseModel):
    content: str = Field(min_length=1, max_length=8000)


def _load(db, cid: int) -> Conversation:
    conv = db.get(Conversation, cid)
    if conv is None:
        raise HTTPException(404, "Conversation not found")
    return conv


@app.post("/chats", status_code=201)
def new_chat(body: NewChat):
    with Session() as db:
        conv = Conversation(persona=body.persona)
        db.add(conv); db.commit()
        return {"id": conv.id}


@app.get("/chats/{cid}")
def get_chat(cid: int):
    with Session() as db:
        conv = _load(db, cid)
        msgs = db.query(Message).filter_by(conversation_id=cid).order_by(Message.id).all()
        return {"id": cid, "title": conv.title,
                "messages": [{"role": m.role, "content": m.content} for m in msgs],
                "tokens_used": sum(m.input_tokens + m.output_tokens for m in msgs)}


@app.post("/chats/{cid}/messages")
def send(cid: int, body: UserMessage):
    with Session() as db:
        conv = _load(db, cid)
        db.add(Message(conversation_id=cid, role="user", content=body.content)); db.commit()
        # The model has NO memory of its own. We resend the history every time: that IS the memory.
        response = llm.create(get_llm(), max_tokens=2000, system=conv.persona, messages=history(db, cid),
                              output_config={"effort": "low"})          # chat doesn't need deep thinking
        reply = llm.text_of(response)
        db.add(Message(conversation_id=cid, role="assistant", content=reply,
                       input_tokens=response.usage.input_tokens, output_tokens=response.usage.output_tokens))
        if conv.title == "New chat":
            conv.title = body.content[:60]
        db.commit()
        return {"reply": reply, "usage": {"input_tokens": response.usage.input_tokens, "output_tokens": response.usage.output_tokens}}


@app.post("/chats/{cid}/stream")
def send_streaming(cid: int, body: UserMessage):
    """Server-Sent Events: the client receives the reply piece by piece, like ChatGPT's typing effect."""
    with Session() as db:
        conv = _load(db, cid)
        db.add(Message(conversation_id=cid, role="user", content=body.content)); db.commit()
        persona, msgs = conv.persona, history(db, cid)

    def events():
        pieces = []
        with llm.stream(get_llm(), max_tokens=2000, system=persona, messages=msgs, output_config={"effort": "low"}) as s:
            for text in s.text_stream:
                pieces.append(text)
                yield f"data: {text}\n\n"
            final = s.get_final_message()
        with Session() as db:
            db.add(Message(conversation_id=cid, role="assistant", content="".join(pieces),
                           input_tokens=final.usage.input_tokens, output_tokens=final.usage.output_tokens))
            db.commit()
        yield "event: done\ndata: [DONE]\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")
