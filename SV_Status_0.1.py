import os
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import psutil
from pypresence import Presence


CLIENT_ID = "1517812895675715807"
UPDATE_DELAY = 4

SEASONS = {
    "spring": "Spring",
    "summer": "Summer",
    "fall": "Fall",
    "winter": "Winter",
}


def is_stardew_running():
    for proc in psutil.process_iter(["name"]):
        try:
            name = (proc.info["name"] or "").lower()
            if "stardew" in name:
                return True
        except psutil.Error:
            pass
    return False


def possible_save_folders():
    folders = []

    appdata = os.getenv("APPDATA")
    localappdata = os.getenv("LOCALAPPDATA")

    if appdata:
        folders.append(Path(appdata) / "StardewValley" / "Saves")

    # Xbox / Microsoft Store / Game Pass style location
    if localappdata:
        packages = Path(localappdata) / "Packages"
        if packages.exists():
            for pkg in packages.glob("ConcernedApe.StardewValleyPC*"):
                folders.append(pkg / "LocalCache" / "Roaming" / "StardewValley" / "Saves")

    return folders


def find_latest_save_file():
    candidates = []

    for saves_folder in possible_save_folders():
        if not saves_folder.exists():
            continue

        for farm_folder in saves_folder.iterdir():
            if not farm_folder.is_dir():
                continue

            save_file = farm_folder / farm_folder.name
            if save_file.exists():
                candidates.append(save_file)

    if not candidates:
        return None

    return max(candidates, key=lambda p: p.stat().st_mtime)


def get_text(root, tag, default="?"):
    element = root.find(f".//{tag}")
    return element.text if element is not None and element.text else default


def read_stardew_save():
    save_file = find_latest_save_file()

    if save_file is None:
        return "Stardew Valley", "No save found"

    try:
        root = ET.parse(save_file).getroot()

        year = get_text(root, "year")
        season = SEASONS.get(get_text(root, "currentSeason").lower(), get_text(root, "currentSeason"))
        day = get_text(root, "dayOfMonth")
        farm_name = get_text(root, "farmName", "Farm")

        details = f"Year {year} - {season} {day} in {farm_name}"
        state = "Playing Stardew Valley"

        return details, state

    except Exception as e:
        return "Stardew Valley", f"Save read error: {e}"


def main():
    rpc = Presence(CLIENT_ID)
    rpc.connect()

    print("Stardew Valley RPC started.")
    print("Press CTRL+C to stop.")

    while True:
        if is_stardew_running():
            details, state = read_stardew_save()
        else:
            details = "Stardew Valley"
            state = "Not running"

        print(details, "|", state)

        rpc.update(
            details=details,
            state=state,
            large_image="stardew",
            large_text="Stardew Valley",
        )

        time.sleep(UPDATE_DELAY)


if __name__ == "__main__":
    main()