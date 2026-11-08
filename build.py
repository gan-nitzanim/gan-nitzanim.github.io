#!/usr/bin/env python3
"""בונה את songs.json ומעתיק את קבצי האודיו מתיקיית המקור.

הקבצים המאוחדים כבר דחוסים (80-192 kbps), ולכן הם מועתקים כמו שהם —
קידוד מחדש רק היה פוגע באיכות. אין צורך ב-ffmpeg או בכל כלי חיצוני.

הוספת שיר: שורה אחת ב-SONGS, ואז  python3 build.py  ו-git push.
"""
import json, os, shutil, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(HERE), "שירים אחרי איחוד")
AUDIO = os.path.join(HERE, "audio")

# (מזהה באנגלית לכתובת, שם הקובץ במקור, השם שמוצג ברשימה)
SONGS = [
    ("morning",      "שירי בוקר.mp3",                  "שירי בוקר"),
    ("kids",         "שירי ילדים.mp3",                 "שירי ילדים"),
    ("garden",       "גינה.mp3",                       "גינה"),
    ("rosh",         "ראש השנה.mp3",                   "ראש השנה"),
    ("sukkot",       "סוכות.mp3",                      "סוכות"),
    ("autumn",       "שירי סתיו.mp3",                  "שירי סתיו"),
    ("hanukkah",     "חנוכה.mp3",                      "חנוכה"),
    ("tubishvat",    "ט״ו בשבט.mp3",                   "ט״ו בשבט"),
    ("winter",       "שירי חורף.mp3",                  "שירי חורף"),
    ("family",       "יום המשפחה.mp3",                 "יום המשפחה"),
    ("spring-1",     "אביב ופסח - ממוזג חלק 1 מתוך 3.mp3", "אביב ופסח – חלק א׳"),
    ("spring-2",     "אביב ופסח - ממוזג חלק 2 מתוך 3.mp3", "אביב ופסח – חלק ב׳"),
    ("spring-3",     "אביב ופסח - ממוזג חלק 3 מתוך 3.mp3", "אביב ופסח – חלק ג׳"),
    ("independence", "יום העצמאות.mp3",                "יום העצמאות"),
    ("lagbaomer",    "ל'ג בעומר.mp3",                  "ל״ג בעומר"),
    ("shavuot",      "שבועות.mp3",                     "שבועות"),
    ("summer-1",     "שירי קיץ - חלק 1 (01-17).mp3",   "שירי קיץ – חלק א׳"),
    ("summer-2",     "שירי קיץ - חלק 2 (18-33).mp3",   "שירי קיץ – חלק ב׳"),
]

_BR1 = [None, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, None]
_BR2 = [None, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160, None]
_SR = {3: {0: 44100, 1: 48000, 2: 32000}, 2: {0: 22050, 1: 24000, 2: 16000},
       0: {0: 11025, 1: 12000, 2: 8000}}


def mp3_info(path):
    """(seconds, kbps) מתוך כותרת ה-MP3 עצמה, בלי ספריות חיצוניות."""
    size = os.path.getsize(path)
    with open(path, "rb") as f:
        head = f.read(10)
        start = 0
        if head[:3] == b"ID3":
            b = head[6:10]
            start = 10 + (((b[0] & 0x7F) << 21) | ((b[1] & 0x7F) << 14) |
                          ((b[2] & 0x7F) << 7) | (b[3] & 0x7F))
        f.seek(start)
        data = f.read(200000)
    i = 0
    while i < len(data) - 4:
        if data[i] == 0xFF and (data[i + 1] & 0xE0) == 0xE0:
            h = data[i:i + 4]
            ver, layer = (h[1] >> 3) & 3, (h[1] >> 1) & 3
            bri, sri = (h[2] >> 4) & 0xF, (h[2] >> 2) & 3
            if layer == 1 and sri != 3 and bri not in (0, 15) and ver in _SR:
                kbps = (_BR1 if ver == 3 else _BR2)[bri]
                rate = _SR[ver][sri]
                tag = data[i + 4:i + 60]
                for mark in (b"Xing", b"Info"):
                    if mark in tag:
                        k = i + 4 + tag.find(mark)
                        if struct.unpack(">I", data[k + 4:k + 8])[0] & 1:
                            frames = struct.unpack(">I", data[k + 8:k + 12])[0]
                            return frames * (1152 if ver == 3 else 576) / rate, kbps
                        break
                return (size - start) * 8 / (kbps * 1000), kbps
        i += 1
    raise ValueError("לא נמצאה כותרת MP3 תקינה: " + path)


def main():
    os.makedirs(AUDIO, exist_ok=True)
    library, missing = [], []
    for sid, filename, name in SONGS:
        src = os.path.join(SRC, filename)
        if not os.path.exists(src):
            missing.append(filename)
            continue
        dst = os.path.join(AUDIO, sid + ".mp3")
        if not os.path.exists(dst) or os.path.getsize(dst) != os.path.getsize(src):
            shutil.copy2(src, dst)
            action = "הועתק"
        else:
            action = "ללא שינוי"
        seconds, kbps = mp3_info(dst)
        size = os.path.getsize(dst)
        library.append({"id": sid, "name": name, "file": "audio/" + sid + ".mp3",
                        "seconds": round(seconds, 1), "bytes": size})
        print("%-13s %-10s %3d kbps  %6.1f דק׳  %6.1f MB" %
              (sid, action, kbps, seconds / 60, size / 1e6))

    if missing:
        print("\nחסרים במקור:", ", ".join(missing))
        sys.exit(1)

    with open(os.path.join(HERE, "songs.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(library, f, ensure_ascii=False, indent=1)

    extra = sorted(set(os.listdir(AUDIO)) - {s["id"] + ".mp3" for s in library})
    if extra:
        print("\nקבצים ב-audio/ שאינם ברשימה (למחוק ידנית עם git rm):", ", ".join(extra))

    total_s = sum(s["seconds"] for s in library)
    total_b = sum(s["bytes"] for s in library)
    print("\n%d שירים | %.0f דקות (%.1f שעות) | %.0f MB" %
          (len(library), total_s / 60, total_s / 3600, total_b / 1e6))


if __name__ == "__main__":
    main()
