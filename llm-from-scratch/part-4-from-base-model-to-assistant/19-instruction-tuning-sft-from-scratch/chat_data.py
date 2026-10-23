"""A tiny instruction dataset, written for this course. python chat_data.py prints examples.

Six skills a character-level model can really learn in a few minutes. The words and names are
split into TRAIN and TEST lists, so the test checks skills on words the model never saw in training.

Story: two helpers wrote the greeting answers. One was friendly, one was grumpy, and both styles
ended up in the data. SFT copies both. Lesson 20 (DPO) teaches the model which one we prefer.
"""
import random

WORDS = """apple banana cherry grape lemon mango melon peach pear plum berry orange garden river
mountain forest ocean island desert valley meadow castle bridge tower village city market
school church harbor window door table chair candle mirror pillow blanket basket bottle
button pencil paper letter story poem song music dance smile laugh dream sleep night
morning evening summer winter spring autumn rain snow cloud storm thunder wind sun moon
star planet rocket robot engine wheel train ship boat plane horse tiger lion zebra monkey
rabbit turtle eagle parrot spider dolphin whale shark kitten puppy dragon wizard knight
king queen prince princess farmer doctor teacher baker sailor pirate silver golden purple
yellow green happy brave quiet gentle clever funny lucky simple strong tiny giant early
late quick slow warm cold sweet bitter honey bread butter cheese pepper sugar coffee
tea water fire stone metal glass wood paint brush camera phone laptop screen cable
signal pocket jacket hat shoe sock glove ring crown sword shield arrow tent map compass
lantern ladder hammer nail rope anchor feather shell pebble sand wave coral""".split()

NAMES = """Alice Bob Carol David Emma Frank Grace Henry Iris Jack Kate Leo Mia Noah Olivia Paul
Quinn Rosa Sam Tara Uma Victor Wendy Xavier Yara Zoe Aaron Bella Caleb Daisy Ethan Fiona
George Hazel Ivan Julia Kevin Luna Mason Nora Oscar Piper Ruby Simon Tessa Owen Ava Liam
Sofia Lucas Chloe Mateo Priya Ravi Anika Arjun Meera Kenji Yuki Omar Layla Hugo Elsa""".split()

IDENTITY = [
    ("Who are you?", "I am TinyChat, a very small language model."),
    ("What is your name?", "My name is TinyChat."),
    ("Who made you?", "I was trained from scratch in the llm-from-scratch course."),
    ("Are you a human?", "No, I am a tiny language model."),
    ("What can you do?", "I can greet people, spell words, and change words to capitals."),
    ("Hello!", "Hello! How can I help you today?"),
    ("Thank you!", "You are welcome!"),
    ("What did you read?", "I read the plays of Shakespeare."),
]


def polite_greeting(name):
    return f"Hello, {name}! It is lovely to meet you."


def rude_greeting(name):
    return f"{name}. What do you want?"


def task_examples(word):
    return [
        (f"Uppercase: {word}", word.upper()),
        (f"Spell {word}", "-".join(word)),
        (f"What is the first letter of {word}?", f"The first letter of {word} is {word[0]}."),
        (f"How many letters are in {word}?", f"{word} has {len(word)} letters."),
    ]


def split(items, test_fraction=0.2, seed=0):
    items = sorted(items)
    random.Random(seed).shuffle(items)
    n = int(len(items) * test_fraction)
    return items[n:], items[:n]          # train, test


TRAIN_WORDS, TEST_WORDS = split(WORDS)
TRAIN_NAMES, TEST_NAMES = split(NAMES)


def sft_dataset(seed=0):
    """(user, assistant) pairs for training. Greetings: about half friendly, half grumpy."""
    rng = random.Random(seed)
    data = []
    for w in TRAIN_WORDS:
        data += task_examples(w)
    for n in TRAIN_NAMES:
        for _ in range(4):                                       # 4 greetings per name, mixed styles
            data.append((f"Say hello to {n}.", polite_greeting(n) if rng.random() < 0.5 else rude_greeting(n)))
    data += IDENTITY * 10                                        # few questions, so repeat them
    rng.shuffle(data)
    return data


def test_dataset():
    """Held-out prompts with the expected answer, grouped by skill (words/names never seen in training)."""
    tests = {"uppercase": [], "spell": [], "first letter": [], "count letters": [], "identity": []}
    for w in TEST_WORDS:
        for skill, (u, a) in zip(["uppercase", "spell", "first letter", "count letters"], task_examples(w)):
            tests[skill].append((u, a))
    tests["identity"] = list(IDENTITY)
    return tests


def greeting_style(name, reply):
    if reply == polite_greeting(name):
        return "friendly"
    if reply == rude_greeting(name):
        return "grumpy"
    return "other"


if __name__ == "__main__":
    data = sft_dataset()
    print(f"{len(data)} training conversations | {len(TRAIN_WORDS)} train words, {len(TEST_WORDS)} test words | "
          f"{len(TRAIN_NAMES)} train names, {len(TEST_NAMES)} test names")
    for u, a in data[:8]:
        print(f"  USER: {u:40s} ASSISTANT: {a}")
    print("test words:", " ".join(TEST_WORDS[:12]), "...")
