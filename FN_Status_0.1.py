import os
import re
import time
from pathlib import Path

import psutil
from pypresence import Presence


# 1) Put your Discord Application Client ID here
CLIENT_ID = "1517574821817356389"

UPDATE_DELAY = 4  # seconds, 3-5 is fine

LOG_PATH = Path(os.getenv("LOCALAPPDATA", "")) / "FortniteGame" / "Saved" / "Logs" / "FortniteGame.log"


def is_fortnite_running() -> bool:
    for proc in psutil.process_iter(["name"]):
        try:
            name = (proc.info["name"] or "").lower()
            if "fortniteclient-win64-shipping" in name:
                return True
        except psutil.Error:
            pass
    return False


def read_last_log_part(max_bytes=250_000) -> str:
    if not LOG_PATH.exists():
        return ""

    with open(LOG_PATH, "rb") as f:
        f.seek(0, os.SEEK_END)
        size = f.tell()
        f.seek(max(0, size - max_bytes))
        return f.read().decode(errors="ignore")


def detect_fortnite_state() -> tuple[str, str]:
    """
    Returns: (details, state)
    details = main line
    state = smaller line
    """

    if not is_fortnite_running():
        return "Fortnite", "Not running"

    log = read_last_log_part()

    if not log:
        return "Fortnite", "Running"

    lower = log.lower()

    # Basic lobby / match guesses
    in_match_words = [
        "athena",
        "playlist",
        "matchmaking completed",
        "gamephase",
        "traveltourl",
        "server travel",
    ]

    lobby_words = [
        "front end",
        "frontend",
        "lobby",
        "main menu",
    ]

    # Try to catch playlist/gamemode-like names
    playlist_match = re.findall(
        r"(?:playlist|playlistname|playlist id|playlistid)[^\n:=]*[:= ]+([A-Za-z0-9_./ -]{3,80})",
        log,
        flags=re.IGNORECASE,
    )

    island_match = re.findall(
        r"(?:island|experience|creative|mnemonic|link code|project)[^\n:=]*[:= ]+([A-Za-z0-9_./ -]{3,80})",
        log,
        flags=re.IGNORECASE,
    )

    if playlist_match:
        latest = playlist_match[-1].strip()
        return "Fortnite", f"In Match: {latest[:120]}"

    if island_match:
        latest = island_match[-1].strip()
        return "Fortnite Creative", f"Island/Map: {latest[:120]}"

    if any(word in lower for word in in_match_words):
        return "Fortnite", "In Match"

    if any(word in lower for word in lobby_words):
        return "Fortnite", "In Lobby"

    return "Fortnite", "Running"


def main():
    rpc = Presence(CLIENT_ID)
    rpc.connect()

    start_time = int(time.time())

    print("Fortnite Discord RPC started.")
    print("Press CTRL+C to stop.")
    print(f"Reading log from: {LOG_PATH}")

    last_status = None

    while True:
        details, state = detect_fortnite_state()

        current_status = (details, state)

        if current_status != last_status:
            print(f"{details} | {state}")
            last_status = current_status

        rpc.update(
            details=details,
            state=state,
            large_image="fortnite",
            large_text="Fortnite",
            start=start_time,
        )

        time.sleep(UPDATE_DELAY)


if __name__ == "__main__":
    main()