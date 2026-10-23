"""Get the names dataset used by every lesson in Part 2 (the same file Karpathy's makemore uses).

names.txt has about 32,000 first names, one per line, all lowercase a-z.
Source: https://github.com/karpathy/makemore (MIT licence).

Where the words come from, in order:
  1. names.txt next to this script (downloaded once, then reused),
  2. a download from GitHub,
  3. if you are offline: a small built-in list (fine for testing the code, too small to learn well).
"""
import urllib.request
from pathlib import Path

URL = "https://raw.githubusercontent.com/karpathy/makemore/master/names.txt"
PATH = Path(__file__).resolve().parent / "names.txt"

FALLBACK_NAMES = """
emma olivia ava isabella sophia charlotte mia amelia harper evelyn abigail emily elizabeth mila ella
avery sofia camila aria scarlett victoria madison luna grace chloe penelope layla riley zoey nora lily
eleanor hannah lillian addison aubrey ellie stella natalie zoe leah hazel violet aurora savannah audrey
brooklyn bella claire skylar lucy paisley everly anna caroline nova genesis emilia kennedy samantha maya
willow kinsley naomi aaliyah elena sarah ariana allison gabriella alice madelyn cora ruby eva serenity
liam noah william james oliver benjamin elijah lucas mason logan alexander ethan jacob michael daniel
henry jackson sebastian aiden matthew samuel david joseph carter owen wyatt john jack luke jayden dylan
grayson levi isaac gabriel julian mateo anthony jaxon lincoln joshua christopher andrew theodore caleb
ryan asher nathan thomas leo isaiah charles josiah hudson christian hunter connor eli ezra aaron landon
adrian jonathan nolan jeremiah easton elias colton cameron carson robert angel maverick nicholas dominic
""".split()


def load_words():
    if not PATH.exists():
        try:
            print(f"downloading names.txt from {URL} ...")
            with urllib.request.urlopen(URL, timeout=30) as response:
                PATH.write_bytes(response.read())
        except OSError as err:                       # no internet, blocked, timeout...
            print(f"could not download ({err}); using the small built-in list of {len(FALLBACK_NAMES)} names")
            return list(FALLBACK_NAMES)
    words = PATH.read_text().split()                 # split on whitespace = one name per line
    return [w.strip().lower() for w in words if w.strip()]


if __name__ == "__main__":
    words = load_words()
    print(f"{len(words)} names, for example {words[:8]}")
