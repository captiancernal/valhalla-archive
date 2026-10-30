"""Download the live Google Sheet tracker into source/ as a dated .xlsx (read-only).

This replaces the manual "File > Download > Microsoft Excel" step of /update-archive.
It only ever reads the sheet: the Google sign-in it asks for is read-only, and nothing is written back.

Private files live OUTSIDE the repo, in %USERPROFILE%\\.valhalla-archive\\ (override with VALHALLA_CONFIG_DIR):
  client_secret.json   the "Desktop app" OAuth client the owner downloads from Google Cloud (one time)
  token.json           written after the owner signs in once in the browser
  settings.json        {"sheet_id": "..."}  the live tracker's ID
  last_pull.json       what was downloaded last time (to skip unchanged sheets)

Usage:
  py -P scripts/pull_tracker.py status            show what's set up and when the sheet last changed
  py -P scripts/pull_tracker.py set-sheet <ID>    save the live sheet's ID (or paste its full link)
  py -P scripts/pull_tracker.py pull [--force]    download if the sheet changed since the last pull
Exit codes: 0 = downloaded or already current, 1 = error, 2 = setup missing.
"""
import datetime
import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(ROOT, "source")
CONFIG = os.environ.get("VALHALLA_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".valhalla-archive")
CLIENT = os.path.join(CONFIG, "client_secret.json")
TOKEN = os.path.join(CONFIG, "token.json")
SETTINGS = os.path.join(CONFIG, "settings.json")
LAST = os.path.join(CONFIG, "last_pull.json")
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
SHEET_MIME = "application/vnd.google-apps.spreadsheet"
XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
REQUIRED_SHEETS = ["Schedule", "Depth Chart", "Coach Josh Dolan", "Standings", "CFB Playoff Tree", "Recruiting"]


def load(path, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, ValueError):
        return default


def save(path, obj):
    os.makedirs(CONFIG, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1)


def sheet_id():
    return (load(SETTINGS, {}) or {}).get("sheet_id")


def need_libs():
    try:
        import google_auth_oauthlib  # noqa: F401
        import google.auth  # noqa: F401
    except ImportError:
        sys.exit("Missing Google sign-in library. Run: py -m pip install --user -r requirements-local.txt")


def credentials():
    """Read-only Google credentials; opens the browser for sign-in when needed."""
    need_libs()
    from google.auth.exceptions import RefreshError
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

    creds = None
    if os.path.exists(TOKEN):
        creds = Credentials.from_authorized_user_file(TOKEN, SCOPES)
    if creds and creds.valid:
        return creds
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except RefreshError:
            print("The saved Google sign-in has expired; opening the browser to sign in again.")
            creds = None
    if not creds or not creds.valid:
        if not os.path.exists(CLIENT):
            print(f"Setup missing: no client_secret.json in {CONFIG}")
            sys.exit(2)
        print("Opening your browser to sign in to Google (read-only access to Drive)...")
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT, SCOPES)
        creds = flow.run_local_server(port=0, open_browser=True,
                                      success_message="Signed in. You can close this tab and go back to Claude.")
    os.makedirs(CONFIG, exist_ok=True)
    with open(TOKEN, "w", encoding="utf-8") as f:
        f.write(creds.to_json())
    return creds


def session():
    from google.auth.transport.requests import AuthorizedSession
    return AuthorizedSession(credentials())


def file_info(s, fid):
    r = s.get(f"https://www.googleapis.com/drive/v3/files/{fid}",
              params={"fields": "name,mimeType,modifiedTime,trashed,exportLinks", "supportsAllDrives": "true"}, timeout=60)
    if r.status_code == 404:
        sys.exit("Google says that sheet doesn't exist or this account can't see it. Check the sheet ID.")
    r.raise_for_status()
    info = r.json()
    if info.get("mimeType") != SHEET_MIME:
        sys.exit(f"That ID is not a Google Sheet (it is {info.get('mimeType')}).")
    if info.get("trashed"):
        sys.exit("That sheet is in the Google Drive trash.")
    return info


def local_time(iso):
    t = datetime.datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone()
    return t.strftime("%Y-%m-%d %I:%M %p").replace(" 0", " ")


def target_name():
    """Dated name that sorts after every older copy (build_data.py takes the last name alphabetically)."""
    stamp = datetime.datetime.now().strftime("%Y-%m-%d-%H%M")
    path = os.path.join(SOURCE, f"{stamp} CSU Vikings Tracker.xlsx")
    if os.path.exists(path):  # never overwrite a dated copy
        stamp = datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S")
        path = os.path.join(SOURCE, f"{stamp} CSU Vikings Tracker.xlsx")
    return path


def check_workbook(path):
    import openpyxl
    with open(path, "rb") as f:  # a file object, because openpyxl rejects the .part extension
        wb = openpyxl.load_workbook(f, read_only=True)
        names = wb.sheetnames
        wb.close()
    missing = [n for n in REQUIRED_SHEETS if n not in names]
    if missing:
        raise ValueError(f"the download is missing expected tabs: {', '.join(missing)}")
    return names


def pull(force=False):
    fid = sheet_id()
    if not fid:
        print("Setup missing: no sheet ID saved. Run: py -P scripts/pull_tracker.py set-sheet <ID>")
        sys.exit(2)
    s = session()
    info = file_info(s, fid)
    last = load(LAST, {}) or {}
    print(f"Live sheet: {info['name'].strip()} (last changed {local_time(info['modifiedTime'])})")
    if (not force and last.get("modifiedTime") == info["modifiedTime"]
            and os.path.exists(os.path.join(SOURCE, last.get("file", "")))):
        print(f"UNCHANGED: the sheet hasn't changed since the last download ({last['file']}). Nothing new to pull.")
        return
    link = (info.get("exportLinks") or {}).get(XLSX_MIME)
    if not link:
        sys.exit("Google didn't offer an Excel download for this sheet.")
    os.makedirs(SOURCE, exist_ok=True)
    final = target_name()
    part = final + ".part"
    sha = hashlib.sha256()
    size = 0
    with s.get(link, stream=True, timeout=300) as r:
        r.raise_for_status()
        with open(part, "wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)
                sha.update(chunk)
                size += len(chunk)
    try:
        names = check_workbook(part)
    except Exception as e:  # keep nothing half-downloaded in source/
        os.remove(part)
        sys.exit(f"Download didn't look like the tracker ({e}). Nothing was saved.")
    os.replace(part, final)
    save(LAST, {"file": os.path.basename(final), "modifiedTime": info["modifiedTime"], "sha256": sha.hexdigest(),
                "bytes": size, "pulled_at": datetime.datetime.now().isoformat(timespec="seconds")})
    print(f"DOWNLOADED: source/{os.path.basename(final)} ({size / 1e6:.1f} MB, {len(names)} tabs)")


def status():
    print(f"Private settings folder: {CONFIG}")
    print(f"  Google client file (client_secret.json): {'yes' if os.path.exists(CLIENT) else 'MISSING'}")
    print(f"  Signed in (token.json): {'yes' if os.path.exists(TOKEN) else 'not yet'}")
    print(f"  Sheet ID saved: {'yes' if sheet_id() else 'MISSING'}")
    last = load(LAST)
    if last:
        print(f"  Last download: {last['file']} (sheet changed {local_time(last['modifiedTime'])})")
    if os.path.exists(CLIENT) and os.path.exists(TOKEN) and sheet_id():  # never opens a sign-in by itself
        info = file_info(session(), sheet_id())
        changed = not last or last.get("modifiedTime") != info["modifiedTime"]
        print(f"Live sheet: {info['name'].strip()}, last changed {local_time(info['modifiedTime'])}"
              f" ({'NEW changes since the last download' if changed else 'no changes since the last download'})")


def set_sheet(arg):
    m = re.search(r"/spreadsheets/d/([A-Za-z0-9_-]+)", arg)
    fid = m.group(1) if m else arg.strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{20,}", fid):
        sys.exit("That doesn't look like a Google Sheet ID or link.")
    settings = load(SETTINGS, {}) or {}
    settings["sheet_id"] = fid
    save(SETTINGS, settings)
    print(f"Saved the sheet ID in {SETTINGS}")


if __name__ == "__main__":
    args = sys.argv[1:]
    cmd = args[0] if args else "pull"
    if cmd == "pull":
        pull(force="--force" in args)
    elif cmd == "status":
        status()
    elif cmd == "set-sheet" and len(args) == 2:
        set_sheet(args[1])
    else:
        sys.exit(__doc__)
