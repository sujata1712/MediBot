from chat_history import (
    create_new_session_id,
    view_session_history,
    delete_session,
    display_all_sessions,
    display_session_stats,
    display_search_results,
    session_exists,
    save_session_title,
    generate_title_from_message,
    get_session_title,
    get_session_messages,
    clear_all_history
)

from rag_pipeline import conversational_chain


# --------------------------------------------- Commands ---------------------------------------------

def print_header():
    print("\n" + "=" * 65)
    print("  MediBot — Medical AI Assistant")
    print("=" * 65)
    print("\nCommands:")
    print("  new                 → Start a new conversation")
    print("  history             → View current session history")
    print("  sessions            → List all saved sessions")
    print("  search <keyword>    → Search sessions by title")
    print("  stats               → Show chat statistics")
    print("  load <session_id>   → Load previous session")
    print("  delete <session_id> → Delete a session")
    print("  clear               → Delete ALL sessions")
    print("  exit                → Quit\n\n")


def is_first_message(session_id: str) -> bool:
    return len(get_session_messages(session_id)) == 0


# --------------------------------------------- Main Loop ---------------------------------------------

def main():
    session_id = create_new_session_id()

    print_header()
    print(f"Current Session : {session_id}")
    print("Topic           : (auto-generated after first message)\n")
    print("=" * 62 + "\n")

    while True:
        try:
            query = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting MediBot. Goodbye 👋\n")
            break

        if not query:
            continue

        low = query.lower()

        #  ___________________________________ BASIC COMMANDS ___________________________________

        if low in ("exit", "quit", "bye"):
            print("\nExiting MediBot. Take care!\n")
            break

        elif low == "new":
            session_id = create_new_session_id()
            print(f"\nNew session started : {session_id}")
            print("Topic : (auto-generated)\n")
            continue

        elif low == "history":
            view_session_history(session_id)
            continue

        elif low == "sessions":
            display_all_sessions()
            continue

        elif low == "stats":
            display_session_stats()
            continue

        #  ___________________________________ SEARCH  ___________________________________

        elif low.startswith("search "):
            keyword = query[7:].strip()
            if keyword:
                display_search_results(keyword)
            else:
                print("\nUsage: search <keyword>\n")
            continue

        #  ___________________________________ LOAD  ___________________________________

        elif low.startswith("load "):
            target = query[5:].strip()
            if session_exists(target):
                session_id = target
                title = get_session_title(session_id)
                print(f"\nLoaded session : {session_id}")
                print(f"Topic          : {title}\n")
                view_session_history(session_id)
            else:
                print(f"\nSession not found: {target}\n")
            continue

        #  ___________________________________ DELETE  ___________________________________

        elif low.startswith("delete "):
            target = query[7:].strip()

            if target == session_id:
                print("\nCannot delete active session. Use 'new' or 'load'.\n")
            else:
                success = delete_session(target)
                if success:
                    print(f"\nDeleted session: {target}\n")
                else:
                    print(f"\nFailed to delete session: {target}\n")
            continue

        #  ___________________________________ CLEAR ALL ___________________________________

        elif low == "clear":
            confirm = input("This will delete ALL chat history. Type 'yes' to confirm: ")
            if confirm.lower() == "yes":
                clear_all_history()
                session_id = create_new_session_id()
                print("\nAll history cleared. New session started.\n")
            else:
                print("\nCancelled.\n")
            continue

        #  ___________________________________ CHAT  ___________________________________

        is_new = is_first_message(session_id)

        try:
            response = conversational_chain.invoke(
                {"question": query},
                config={"configurable": {"session_id": session_id}},
            )

            print(f"\nMediBot: {response}\n")

            # Auto title generation
            if is_new:
                title = generate_title_from_message(query)
                save_session_title(session_id, title)
                print(f'[Session titled: "{title}"]\n')

        except Exception as e:
            print(f"\nError: {e}\n")
            import traceback
            traceback.print_exc()


# --------------------------------------------- Entry Point ---------------------------------------------

if __name__ == "__main__":
    main()