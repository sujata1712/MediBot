import os


from chat_history import *
from rag_pipeline import conversational_chain
from media_handler import (
    record_audio_from_mic,
    transcribe_audio,
    analyze_image
)


# ----------------------------- UI -----------------------------

def show_menu():
    print("\n=== MediBot - Medical AI Assistant ===")
    print("Commands:")
    print("  new                  -> New chat")
    print("  history              -> View history")
    print("  sessions             -> List sessions")
    print("  load <id>            -> Load session")
    print("  delete <id>          -> Delete session")
    print("  clear                -> Delete all chats")
    print("  voice [seconds]      -> Voice input")
    print("  image <path>         -> Analyze image")
    print("  exit                 -> Quit\n")


# ----------------------------- Chat -----------------------------

def send_message(query, session_id):
    try:
        first_chat = len(get_session_messages(session_id)) == 0

        response = conversational_chain.invoke(
            {"question": query},
            config={"configurable": {"session_id": session_id}},
        )

        print(f"\nMediBot: {response}\n")

        if first_chat:
            title = generate_title_from_message(query)
            save_session_title(session_id, title)
            print(f'[Session Title: "{title}"]\n')

    except Exception as e:
        print(f"\nError: {e}\n")


# ----------------------------- Main -----------------------------

def main():
    session_id = create_new_session_id()

    show_menu()
    print(f"Current Session: {session_id}\n")

    while True:
        try:
            query = input("You: ").strip()

            if not query:
                continue

            cmd = query.lower()

            # EXIT
            if cmd in ["exit", "quit"]:
                print("\nGoodbye 👋")
                break

            # NEW SESSION
            elif cmd == "new":
                session_id = create_new_session_id()
                print(f"\nNew Session: {session_id}\n")

            # HISTORY
            elif cmd == "history":
                view_session_history(session_id)

            # SESSIONS
            elif cmd == "sessions":
                display_all_sessions()

            # LOAD SESSION
            elif cmd.startswith("load "):
                sid = query[5:].strip()

                if session_exists(sid):
                    session_id = sid
                    print(f"\nLoaded: {sid}\n")
                    view_session_history(session_id)
                else:
                    print("\nSession not found.\n")

            # DELETE SESSION
            elif cmd.startswith("delete "):
                sid = query[7:].strip()

                if sid == session_id:
                    print("\nCannot delete active session.\n")
                elif delete_session(sid):
                    print("\nSession deleted.\n")
                else:
                    print("\nDelete failed.\n")

            # CLEAR ALL
            elif cmd == "clear":
                confirm = input("Type 'yes' to confirm: ").strip()

                if confirm.lower() == "yes":
                    clear_all_history()
                    session_id = create_new_session_id()
                    print("\nAll history cleared.\n")

            # VOICE INPUT
            elif cmd.startswith("voice"):
                parts = cmd.split()
                duration = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 60

                audio = record_audio_from_mic(duration)

                print("\nTranscribing...")
                text = transcribe_audio(audio)

                if text:
                    print(f"\nYou said: {text}\n")
                    send_message(text, session_id)
                else:
                    print("\nNo speech detected.\n")

            # IMAGE INPUT
            elif cmd.startswith("image "):
                image_path = query[6:].strip().strip('"').strip("'")

                if not os.path.isfile(image_path):
                    print("\nFile not found.\n")
                    continue

                extra = input("Ask something about the image: ").strip()

                with open(image_path, "rb") as f:
                    image_bytes = f.read()

                print("\nAnalyzing image...\n")

                result = analyze_image(image_bytes, extra)

                print(f"{result}\n")

                full_query = f"""
                Image Analysis:
                {result}

                User Question:
                {extra if extra else 'Give medical insights.'}
                """

                send_message(full_query, session_id)

            # NORMAL CHAT
            else:
                send_message(query, session_id)

        except (KeyboardInterrupt, EOFError):
            print("\nExiting MediBot 👋")
            break


# ----------------------------- Start -----------------------------

if __name__ == "__main__":
    main()