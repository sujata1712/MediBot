import os, sys, json, base64, re, secrets, hashlib, threading, webbrowser
from pathlib import Path

BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
sys.path.insert(0, BACKEND_DIR)
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import StreamingResponse, FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel

from backend.services.rag_pipeline import conversational_chain
import sqlite3 as _sqlite3
from backend.services.chat_history import (
    create_new_session_id, get_session_messages, save_session_title,
    get_session_title, list_all_sessions, get_message_count,
    delete_session, clear_all_history, generate_title_from_message, session_exists,
)
from backend.services.media_handler import transcribe_audio, analyze_image

# --------------------------------------------- User store --------------------------------------------- 

USERS_FILE = Path(os.path.dirname(os.path.abspath(__file__))) / "users.json"

def _load_users() -> dict:
    if USERS_FILE.exists():
        try:
            return json.loads(USERS_FILE.read_text())
        except Exception:
            pass
    return {}

def _save_users(users: dict):
    USERS_FILE.write_text(json.dumps(users, indent=2))

def _hash_pw(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def _verify_pw(password: str, stored_hash: str) -> bool:
    return secrets.compare_digest(_hash_pw(password), stored_hash)

DB: dict = _load_users()

# Seed legacy admin account if not present
_LEGACY_ADMIN_EMAIL = "admin"
_LEGACY_ADMIN_PW    = "medibot123"
if _LEGACY_ADMIN_EMAIL not in DB:
    DB[_LEGACY_ADMIN_EMAIL] = {"password_hash": _hash_pw(_LEGACY_ADMIN_PW), "name": "Admin"}
    _save_users(DB)

# --------------------------------------------- Display message store (thumbnail + caption for image history) ---------------------------------------------
_DISP_DB = Path(os.path.dirname(os.path.abspath(__file__))) / "backend" / "db" / "display_msgs.db"

def _disp_conn():
    conn = _sqlite3.connect(str(_DISP_DB), check_same_thread=False)
    conn.execute("""CREATE TABLE IF NOT EXISTS display_msgs (
        session_id TEXT, turn INTEGER, content TEXT,
        PRIMARY KEY (session_id, turn))""")
    conn.commit()
    return conn

def _save_display(session_id: str, turn: int, content: str):
    with _disp_conn() as conn:
        conn.execute("INSERT OR REPLACE INTO display_msgs VALUES (?,?,?)",
                     (session_id, turn, content))

def _get_displays(session_id: str) -> dict:
    try:
        with _disp_conn() as conn:
            rows = conn.execute(
                "SELECT turn, content FROM display_msgs WHERE session_id=?",
                (session_id,)).fetchall()
        return {r[0]: r[1] for r in rows}
    except Exception:
        return {}

# --------------------------------------------- Session tokens (in-memory; cleared on restart by design for dev) ---------------------------------------------
SESSION_COOKIE = "mb_session"
VALID_TOKENS: set = set()

def _make_token() -> str:
    return secrets.token_hex(32)

# --------------------------------------------- App ----------------------------------------------
app = FastAPI(title="MediBot API")

# CORS: only allow same origin — wildcard breaks cookie auth in browsers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AuthMiddleware(BaseHTTPMiddleware):
    PUBLIC = {"/", "/login", "/api/auth/login", "/api/auth/signup", "/api/auth/me"}
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path in self.PUBLIC or path.startswith("/static"):
            return await call_next(request)
        token = request.cookies.get(SESSION_COOKIE)
        if token and token in VALID_TOKENS:
            return await call_next(request)
        return Response('{"detail":"Not authenticated"}', status_code=401,
                        media_type="application/json")

app.add_middleware(AuthMiddleware)

# --------------------------------------------- Models --------------------------------------------- 
class ChatRequest(BaseModel):
    session_id: str
    message: str = ""
    image_b64: str | None = None
    image_question: str | None = None
    display_message: str | None = None   # thumbnail + caption from frontend

class LoginRequest(BaseModel):
    username: str
    password: str

class SignupRequest(BaseModel):
    email: str
    password: str
    name: str = ""

# --------------------------------------------- Auth --------------------------------------------- 
@app.post("/api/auth/signup")
def signup(data: SignupRequest):
    email = data.email.strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status_code=422, detail="Invalid email address.")
    if len(data.password) < 8:
        raise HTTPException(status_code=422, detail="Password must be at least 8 characters.")
    if email in DB:
        raise HTTPException(status_code=409, detail="An account with that email already exists.")
    DB[email] = {"password_hash": _hash_pw(data.password), "name": data.name.strip()}
    _save_users(DB)
    return {"ok": True, "message": "Account created successfully."}

@app.post("/api/auth/login")
def login(data: LoginRequest, response: Response):
    identifier = data.username.strip().lower()
    user = DB.get(identifier)
    if not user or not _verify_pw(data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    token = _make_token()
    VALID_TOKENS.add(token)
    response.set_cookie(SESSION_COOKIE, token, httponly=True, samesite="lax", max_age=60 * 60 * 8)
    return {"ok": True}

@app.post("/api/auth/logout")
def logout(request: Request, response: Response):
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        VALID_TOKENS.discard(token)
    response.delete_cookie(SESSION_COOKIE)
    return {"ok": True}

@app.get("/api/auth/me")
def me(request: Request):
    token = request.cookies.get(SESSION_COOKIE)
    return {"authenticated": bool(token and token in VALID_TOKENS)}

# --------------------------------------------- Pages --------------------------------------------- 
@app.get("/")
def root():
    return FileResponse("frontend/index.html")

@app.get("/login")
def login_page():
    return FileResponse("frontend/login.html")

# --------------------------------------------- Sessions — specific routes BEFORE parameterised routes ---------------------------------------------
@app.post("/api/chat/new-session")
def new_session():
    return {"session_id": create_new_session_id()}

@app.get("/api/sessions/")
def get_sessions():
    return [
        {"session_id": s, "title": get_session_title(s), "message_count": get_message_count(s)}
        for s in list_all_sessions()
    ]

# FIX: DELETE all before DELETE single — specific paths first
@app.delete("/api/sessions/")
def clear_sessions():
    clear_all_history()
    return {"cleared": True}

@app.delete("/api/sessions/{session_id}")
def remove_session(session_id: str):
    if not delete_session(session_id):
        raise HTTPException(status_code=404, detail="Delete failed")
    return {"deleted": session_id}

@app.get("/api/sessions/{session_id}")
def get_session(session_id: str):
    if not session_exists(session_id):
        return []
    messages = get_session_messages(session_id)
    displays = _get_displays(session_id)
    result = []
    human_idx = 0
    for m in messages:
        if m.type == "human":
            # Use the saved display message (with thumbnail) if available
            content = displays.get(human_idx, m.content)
            result.append({"role": "human", "content": content})
            human_idx += 1
        else:
            result.append({"role": m.type, "content": m.content})
    return result

# --------------------------------------------- Chat SSE ---------------------------------------------
_IMG_MARKER_RE = re.compile(r"^\[IMG:data:image/[^;]+;base64,[^\]]+\]\n?", re.DOTALL)
@app.post("/api/chat/stream")
async def chat_stream(req: ChatRequest):
    session_id = req.session_id
    # Strip [IMG:...] thumbnail from stored message — only for frontend history display
    raw_message = _IMG_MARKER_RE.sub("", req.message).strip()
    question    = raw_message

    if req.image_b64:
        try:
            _, enc = req.image_b64.split(",", 1)
            desc   = analyze_image(base64.b64decode(enc), req.image_question or "")
            block  = f"Image Analysis:\n{desc}\n\nUser Question:\n{req.image_question or 'Give medical insights.'}"
            question = f"{block}\n\n{raw_message}".strip() if raw_message else block
        except Exception as e:
            print(f"[image analysis error] {e}")
            question = raw_message or "Please analyze the image I sent."

    if not question:
        raise HTTPException(status_code=400, detail="No message or image provided")

    # FIX: check title existence (cheaper + correct) instead of message count
    already_titled = bool(get_session_title(session_id) != session_id)

    # Save display message (with thumbnail) for history replay
    if req.display_message:
        turn = len(get_session_messages(session_id))
        _save_display(session_id, turn, req.display_message)

    async def stream():
        try:
            for chunk in conversational_chain.stream(
                {"question": question},
                config={"configurable": {"session_id": session_id}},
            ):
                if chunk:
                    # FIX: escape newlines so SSE lines are never broken
                    safe = chunk.replace("\n", "\\n")
                    yield f"event: message\ndata: {safe}\n\n"
            yield "event: message\ndata: [DONE]\n\n"
            # FIX: only generate title once per session
            if not already_titled:
                title = generate_title_from_message(raw_message or req.image_question or "Image")
                save_session_title(session_id, title)
                # FIX: escape title in SSE data line
                yield f"event: title\ndata: {title.replace(chr(10), ' ')}\n\n"
        except Exception as e:
            # FIX: escape error message for SSE safety
            safe_err = str(e).replace("\n", " ")
            yield f"event: message\ndata: Error: {safe_err}\n\n"
            yield "event: message\ndata: [DONE]\n\n"

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

# --------------------------------------------- Voice ---------------------------------------------
@app.post("/api/transcribe")
async def transcribe(audio: UploadFile = File(...)):
    try:
        text = transcribe_audio(await audio.read(), filename=audio.filename or "rec.webm")
        return {"text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {e}")

# --------------------------------------------- Entrypoint --------------------------------------------- 
if __name__ == "__main__":
    import uvicorn, time
    def _open():
        time.sleep(1.5)
        webbrowser.open("http://localhost:8000/login")
    threading.Thread(target=_open, daemon=True).start()
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)