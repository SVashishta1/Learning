"""Downloads names.txt (32,033 names) from Karpathy's makemore repo; falls back to a small built-in list."""
import os
import urllib.request

URL = "https://raw.githubusercontent.com/karpathy/makemore/master/names.txt"
FALLBACK = """emma olivia ava isabella sophia charlotte mia amelia harper evelyn abigail emily elizabeth sofia
avery ella madison scarlett victoria aria grace chloe camila penelope riley layla lillian nora zoey mila
liam noah william james oliver benjamin elijah lucas mason logan alexander ethan jacob michael daniel henry
jackson sebastian aiden matthew samuel david joseph carter owen wyatt john jack luke jayden dylan grayson""".split()


def load_names(path="names.txt"):
    if not os.path.exists(path):
        try:
            urllib.request.urlretrieve(URL, path + ".part")   # download to a temp name first...
            os.replace(path + ".part", path)                  # ...so a failed download never leaves a broken names.txt
        except Exception as e:
            if os.path.exists(path + ".part"):
                os.remove(path + ".part")
            print(f"(download failed: {e}; using {len(FALLBACK)} built-in names)")
            return FALLBACK
    with open(path, encoding="utf-8") as f:
        return f.read().split()                               # one name per line -> list of names
