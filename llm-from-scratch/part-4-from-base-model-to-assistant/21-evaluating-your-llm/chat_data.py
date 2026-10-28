"""A tiny instruction dataset, written for this course. python chat_data.py prints examples.

Skills a character-level model can learn in a few minutes. The real words and names are split into
TRAIN and TEST lists, so the test checks skills on words the model never saw in training.
Training ALSO uses 2,000 made-up "words" of random letters (and made-up names): with only ~150 real
words the model simply memorises the answers; with thousands of random ones it has to learn the RULE.

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


def made_up_words(n, seed, capitalize=False):
    """Random letter strings like 'qofreb': 3 to 8 letters, no real meaning, never in the test lists."""
    rng = random.Random(seed)
    words = set()
    while len(words) < n:
        w = "".join(rng.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(rng.randint(3, 8)))
        if w not in WORDS and w.capitalize() not in NAMES:
            words.add(w.capitalize() if capitalize else w)
    return sorted(words)


REAL_TRAIN_WORDS, TEST_WORDS = split(WORDS)
REAL_TRAIN_NAMES, TEST_NAMES = split(NAMES)
TRAIN_WORDS = REAL_TRAIN_WORDS + made_up_words(2000, seed=1)
TRAIN_NAMES = REAL_TRAIN_NAMES + made_up_words(300, seed=2, capitalize=True)


def sft_dataset(seed=0):
    """(user, assistant) pairs for training. Greetings: about half friendly, half grumpy."""
    rng = random.Random(seed)
    data = []
    for w in TRAIN_WORDS:
        data += task_examples(w)
    for n in TRAIN_NAMES:
        for _ in range(2):                                       # 2 greetings per name, mixed styles
            data.append((f"Say hello to {n}.", polite_greeting(n) if rng.random() < 0.5 else rude_greeting(n)))
    data += IDENTITY * 100                                       # few questions, so repeat them
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
    """Classify the STYLE of a greeting (a misspelt name still counts): friendly, grumpy or other."""
    friendly, grumpy = "lovely to meet you" in reply, "What do you want" in reply
    if friendly and not grumpy:
        return "friendly"
    if grumpy and not friendly:
        return "grumpy"
    return "other"


if __name__ == "__main__":
    data = sft_dataset()
    print(f"{len(data)} training conversations | train words: {len(REAL_TRAIN_WORDS)} real + {len(TRAIN_WORDS) - len(REAL_TRAIN_WORDS)} made-up "
          f"| test words: {len(TEST_WORDS)} real | train names: {len(TRAIN_NAMES)} | test names: {len(TEST_NAMES)}")
    for u, a in data[:8]:
        print(f"  USER: {u:40s} ASSISTANT: {a}")
    print("test words:", " ".join(TEST_WORDS[:12]), "...")
