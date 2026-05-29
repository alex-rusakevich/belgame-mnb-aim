import os
from pathlib import Path
import shutil
from invoke import run, task
import polib
import csv
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
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


def find_by_ctxt(f: polib.POFile, ctxt: str) -> polib.POEntry | None:
    for entry in f:
        if entry.msgctxt == ctxt:
            return entry

    return None


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
                translation = find_by_ctxt(po_file, msg_id)

                if not translation:
                    print(f"No translation for {msg_id}")
                else:
                    writer.writerow([translation.msgctxt, translation.msgstr])

        print(f"Checked and updated {csv_file_path}")


@task(pre=[po_to_csv])
def install(c):
    game_folder = os.environ.get("GAME_FOLDER", input("Game folder: "))

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

        if dest.exists():
            shutil.rmtree(dest)
            print(f"Deleted {dest}")

        # Копируем исходную папку
        shutil.copytree(src, dest)
        print(f"Copied {src} -> {dest}")


@task
def stats(c):
    total_symbol_num = 0
    untr_symbol_num = 0

    for entry in polib.pofile(PO_FILE):
        total_symbol_num += len(entry.msgstr)

        if "fuzzy" in entry.flags:
            untr_symbol_num += len(entry.msgstr)

    tr_symbol_num = total_symbol_num - untr_symbol_num

    print(f"Total symbols: {total_symbol_num}")
    print(
        f"Translated symbols number: {tr_symbol_num} ({tr_symbol_num / total_symbol_num * 100:.2f}%)"
    )
    print(
        f"Untranslated symbols number: {untr_symbol_num} ({untr_symbol_num / total_symbol_num * 100:.2f}%)"
    )


@task(pre=[po_to_csv])
def build(c):
    run("iscc setup.iss")
