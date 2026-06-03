import sqlite3
import sys
import os
from datetime import datetime
from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

from config import DATABASE_PATH, CONNECTION_STRING


# --------------------------------------------- DB SETUP ---------------------------------------------
def _get_connection():
    """
    Create a SQLite connection with WAL mode for safer concurrent access.
    WAL (Write-Ahead Logging) allows concurrent reads and serialises writes
    safely, preventing corruption under FastAPI's async/threaded requests.
    """
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=3000")
    return conn

def _ensure_tables():
    conn = _get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS session_titles (
            session_id  TEXT PRIMARY KEY,
            title       TEXT NOT NULL,
            created_at  TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS message_store (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            message TEXT
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_session_id 
        ON message_store(session_id)
    """)

    conn.commit()
    conn.close()

# --------------------------------------------- History Functions ---------------------------------------------

def get_session_history(session_id: str):
    _ensure_tables()
    return SQLChatMessageHistory(
        session_id=session_id,
        connection=CONNECTION_STRING
    )

def wrap_chain_with_history(chain, input_key="question", history_key="chat_history"):
    return RunnableWithMessageHistory(
        chain,
        get_session_history,
        input_messages_key=input_key,
        history_messages_key=history_key
    )


# --------------------------------------------- Session Title Handling ---------------------------------------------

def generate_title_from_message(first_message: str) -> str:
    text = first_message.strip()

    filler_prefixes = [
        "i have been having ", "i've been having ",
        "i am having ", "i'm having ",
        "i have ", "i've ",
        "i feel ", "i'm feeling ", "i am feeling ",
        "my ", "i ", "what are ", "what is ",
        "can you tell me ", "please tell me ",
        "tell me about ", "help me with ",
    ]
    lower = text.lower()
    for prefix in filler_prefixes:
        if lower.startswith(prefix):
            text = text[len(prefix):]
            break

    text = text[0].upper() + text[1:] if text else text

    if len(text) > 60:
        truncated = text[:60]
        last_space = truncated.rfind(" ")
        text = (truncated[:last_space] + "...") if last_space > 0 else (truncated + "...")

    return text or "Untitled session"


def save_session_title(session_id: str, title: str):
    _ensure_tables()
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT OR IGNORE INTO session_titles (session_id, title, created_at)
            VALUES (?, ?, ?)
        """, (session_id, title, datetime.now().isoformat()))
        conn.commit()
    finally:
        conn.close()


def get_session_title(session_id: str) -> str:
    _ensure_tables()
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT title FROM session_titles WHERE session_id = ?", (session_id,)
        )
        row = cursor.fetchone()
        return row[0] if row else session_id
    finally:
        conn.close()


def search_sessions_by_title(keyword: str) -> list:
    _ensure_tables()
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT session_id, title FROM session_titles
            WHERE LOWER(title) LIKE ?
            ORDER BY created_at DESC
        """, (f"%{keyword.lower()}%",))
        return cursor.fetchall()
    finally:
        conn.close()


# --------------------------------------------- Session Management ---------------------------------------------

def create_new_session_id() -> str:
    return f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


def session_exists(session_id: str) -> bool:
    """Check message_store OR session_titles — new sessions exist in titles before first message."""
    _ensure_tables()
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT 1 FROM message_store WHERE session_id = ? LIMIT 1",
        (session_id,)
    )
    result = cursor.fetchone()
    if result:
        conn.close()
        return True
    cursor.execute(
        "SELECT 1 FROM session_titles WHERE session_id = ? LIMIT 1",
        (session_id,)
    )
    result = cursor.fetchone()
    conn.close()
    return result is not None


def list_all_sessions() -> list:
    _ensure_tables()
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT DISTINCT session_id FROM message_store ORDER BY id DESC"
        )
        return [row[0] for row in cursor.fetchall()]
    except sqlite3.OperationalError as e:
        print(f"Database error: {e}")
        return []
    finally:
        conn.close()


def get_session_messages(session_id: str) -> list:
    return get_session_history(session_id).messages


def delete_session(session_id: str):
    _ensure_tables()
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM message_store WHERE session_id = ?", (session_id,))
        cursor.execute("DELETE FROM session_titles WHERE session_id = ?", (session_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error deleting session: {e}")
        return False
    finally:
        conn.close()


def clear_all_history():
    _ensure_tables()
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM message_store")
        cursor.execute("DELETE FROM session_titles")
        conn.commit()
        return True
    except Exception as e:
        print(f"Error clearing history: {e}")
    finally:
        conn.close()


# --------------------------------------------- Stats & Display ---------------------------------------------

def get_message_count(session_id: str) -> int:
    return len(get_session_messages(session_id))


def get_session_stats() -> dict:
    sessions = list_all_sessions()
    total_msgs = sum(get_message_count(s) for s in sessions)
    return {
        "total_sessions": len(sessions),
        "total_messages": total_msgs,
        "avg_messages_per_session": total_msgs / len(sessions) if sessions else 0,
    }


def view_session_history(session_id: str):
    
    messages = get_session_messages(session_id)
    title = get_session_title(session_id)

    if not messages:
        print(f"\nNo history for session: {session_id}\n")
        return

    print(f"\n{'=' * 60}")
    print(f"  Session : {title}")
    print(f"  ID      : {session_id}")
    print(f"{'=' * 60}")

    for i, msg in enumerate(messages):
        role = "You" if msg.type == "human" else "MediBot"
        # Print full content — no truncation in history view
        print(f"\n{role}:\n{msg.content}")
        # Separator between message pairs (after each bot reply)
        if msg.type == "ai" and i < len(messages) - 1:
            print(f"\n{'-' * 60}")

    print(f"\n{'=' * 60}\n")


def display_all_sessions():
    sessions = list_all_sessions()
    if not sessions:
        print("\nNo sessions found.\n")
        return
    print("\nAll Sessions:")
    print("=" * 72)
    print(f"  {'#':<4} {'Title':<40} {'Msgs':<6} Session ID")
    print("-" * 72)

    for i, sid in enumerate(sessions, 1):
        title = get_session_title(sid)
        msg_count = get_message_count(sid)
        display_title = title[:37] + "..." if len(title) > 37 else title
        print(f"  {i:<4} {display_title:<40} {msg_count:<6} {sid}")
    print("=" * 72 + "\n")


def display_search_results(keyword: str):
    results = search_sessions_by_title(keyword)
    if not results:
        print(f"\n  No sessions found matching: '{keyword}'\n")
        return
    print(f"\nSearch results for '{keyword}':")
    print("=" * 72)
    print(f"  {'#':<4} {'Title':<40} {'Msgs':<6} Session ID")
    print("-" * 72)
    
    for i, (sid, title) in enumerate(results, 1):
        msg_count = get_message_count(sid)
        display_title = title[:37] + "..." if len(title) > 37 else title
        print(f"  {i:<4} {display_title:<40} {msg_count:<6} {sid}")
    print("=" * 72)
    print("  → use  load <session_id>  to continue any session\n")


def display_session_stats():
    stats = get_session_stats()
    print("\nChat Statistics:")
    print("=" * 60)
    print(f"  Total Sessions  : {stats['total_sessions']}")
    print(f"  Total Messages  : {stats['total_messages']}")
    print(f"  Avg Msg/Session : {stats['avg_messages_per_session']:.1f}")
    print("=" * 60 + "\n")