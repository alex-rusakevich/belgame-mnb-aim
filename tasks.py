import re
from pathlib import Path
import shutil
from invoke import task
from pick import pick
import polib
import csv
from datetime import datetime


now = datetime.now().strftime("%Y-%m-%d %H:%M%z")

ID_COL = 0
MSG_COL = 1
PO_FILE = "translation.po"
TRANSLATION_DIR = "translation"
PO_FILE_METADATA = {
    "Project-Id-Version": "1.0",
    "Report-Msgid-Bugs-To": "mr.alexander.rusakevich@gmail.com",
    "POT-Creation-Date": now,
    "PO-Revision-Date": now,
    "Last-Translator": "Alexander Rusakevich <mr.alexander.rusakevich@gmail.com>",
    "MIME-Version": "1.0",
    "Content-Type": "text/plain; charset=UTF-8",
    "Content-Transfer-Encoding": "8bit",
    "Language": "be",
}


def fetch_entries(csv_file_path: str) -> list[polib.POEntry]:
    entries = []
    encoding = "utf8"

    if Path(csv_file_path).stem == "uimain":
        encoding = "cp1251"

    with open(csv_file_path, encoding=encoding) as csv_file:
        reader = csv.reader(csv_file, delimiter="|")

        for row in reader:
            if row == []:
                continue

            msgid = row[ID_COL].strip()
            msgstr = row[MSG_COL]

            if msgid:  # Skip empty keys
                entry = polib.POEntry(msgid=msgid, msgstr=msgstr)
                entry.flags.append("fuzzy")
                entries.append(entry)
    return entries


@task
def csv_to_po(c):
    input_dir = Path(TRANSLATION_DIR)
    csv_files = list(input_dir.rglob("*.csv"))

    if not csv_files:
        print(f"No CSV files found in {input_dir}")
        return

    print(f"Found {len(csv_files)} CSV file(s)")

    all_entries = []  # type: list[polib.POEntry]

    for csv_file in csv_files:
        file_entries = fetch_entries(csv_file)

        for new_entry in file_entries:
            is_entry_fresh = True

            for i, old_entry in enumerate(all_entries):
                if new_entry.msgid == old_entry.msgid:
                    is_entry_fresh = False

                    if new_entry.msgstr != old_entry.msgstr:
                        option, _ = pick(
                            [new_entry.msgstr, old_entry.msgstr],
                            title=f"ID conflict: {new_entry.msgid}",
                        )
                        all_entries[i].msgstr = option

            if is_entry_fresh:
                all_entries.append(new_entry)

        print(f"Fetched {len(file_entries)} entries from {csv_file}")

    po_file = polib.POFile()
    po_file.metadata = PO_FILE_METADATA

    for entry in all_entries:
        po_file.append(entry)

    po_file.save(PO_FILE)

    print(f"Done! Fetched {len(all_entries)} entries")


@task
def po_to_csv(c):
    input_dir = Path(TRANSLATION_DIR)
    po_file = polib.pofile(PO_FILE)
    csv_files = list(input_dir.rglob("*.csv"))

    if not csv_files:
        print(f"No CSV files found in {input_dir}")
        return

    print(f"Found {len(csv_files)} CSV file(s)")

    for csv_file_path in csv_files:
        msg_ids = []
        encoding = "utf8"

        if Path(csv_file_path).stem == "uimain":
            encoding = "cp1251"

        with open(csv_file_path, encoding=encoding) as csv_file:
            reader = csv.reader(csv_file, delimiter="|")

            for row in reader:
                if row == []:
                    continue

                msg_id = row[ID_COL]

                if msg_id not in msg_ids:
                    msg_ids.append(msg_id)

        with open(csv_file_path, "w", encoding=encoding, newline="") as csv_file:
            writer = csv.writer(csv_file, delimiter="|")

            for msg_id in list(msg_ids):
                translation = po_file.find(msg_id)
                writer.writerow([translation.msgid, translation.msgstr])

        print(f"Checked and updated {csv_file_path}")


@task(pre=[po_to_csv])
def install(c):
    game_folder = input("Game folder: ")

    game_settings_folder = (
        Path.home() / "Documents"
    ) / "Mount&Blade With Fire and Sword"

    (game_settings_folder / "language.txt").write_text("be")

    PATHS = [
        "Data/languages/be",
        "languages/be",
        "Modules/Ogniem i Mieczem/languages/be",
        "Textures/languages/be",
    ]

    for path in PATHS:
        src = (Path(TRANSLATION_DIR) / path).resolve()
        dest = (Path(game_folder) / path).resolve()

        print(f"Copying {src} -> {dest}")

        if dest.exists():
            shutil.rmtree(dest)
            print(f"Deleted {dest}")

        # Копируем исходную папку
        shutil.copytree(src, dest)


@task
def mark_service_str_non_fuzzy(c):
    """Mark strings like {s} and " " in po file"""

    po_file = polib.pofile(PO_FILE)
    pattern = re.compile(r"^\{\w+\}\s*$")
    blank_pattern = re.compile(r"^\s*$")

    non_fuzzy_count = 0

    for entry in po_file:
        if (
            pattern.match(entry.msgstr) or blank_pattern.match(entry.msgstr)
        ) and "fuzzy" in entry.flags:
            entry.flags.remove("fuzzy")
            non_fuzzy_count += 1

    print(f"Done! Removed {non_fuzzy_count} flag(s)")
    po_file.save()
