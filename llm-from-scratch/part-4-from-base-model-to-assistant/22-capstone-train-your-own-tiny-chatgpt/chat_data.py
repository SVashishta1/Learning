"""Capstone: the conversations used for SFT, written for this course. python chat_data.py shows examples.

Each fact has 4 ways of asking: 3 are used for training, the 4th is kept for testing
("does it understand a question worded differently?"). Greetings use real and made-up names; the
test names are never seen in training.
"""
import random

# (answer, [4 phrasings of the question], keyword the answer must contain to count as correct)
FACTS = [
    ("The capital of France is Paris.", ["What is the capital of France?", "Which city is the capital of France?", "Tell me the capital of France.", "France has which capital city?"], "Paris"),
    ("The capital of Japan is Tokyo.", ["What is the capital of Japan?", "Which city is the capital of Japan?", "Tell me the capital of Japan.", "Japan has which capital city?"], "Tokyo"),
    ("The capital of India is New Delhi.", ["What is the capital of India?", "Which city is the capital of India?", "Tell me the capital of India.", "India has which capital city?"], "Delhi"),
    ("The capital of Italy is Rome.", ["What is the capital of Italy?", "Which city is the capital of Italy?", "Tell me the capital of Italy.", "Italy has which capital city?"], "Rome"),
    ("The capital of Egypt is Cairo.", ["What is the capital of Egypt?", "Which city is the capital of Egypt?", "Tell me the capital of Egypt.", "Egypt has which capital city?"], "Cairo"),
    ("The capital of Kenya is Nairobi.", ["What is the capital of Kenya?", "Which city is the capital of Kenya?", "Tell me the capital of Kenya.", "Kenya has which capital city?"], "Nairobi"),
    ("A week has seven days.", ["How many days are in a week?", "How many days does a week have?", "Tell me how many days a week has.", "A week is how many days long?"], "seven"),
    ("A year has twelve months.", ["How many months are in a year?", "How many months does a year have?", "Tell me how many months a year has.", "A year is how many months long?"], "twelve"),
    ("A spider has eight legs.", ["How many legs does a spider have?", "How many legs has a spider got?", "Tell me how many legs a spider has.", "A spider walks on how many legs?"], "eight"),
    ("The sky looks blue because air scatters blue sunlight the most.", ["Why is the sky blue?", "What makes the sky blue?", "Tell me why the sky is blue.", "How come the sky looks blue?"], "scatter"),
    ("Plants make food from sunlight, water and air.", ["How do plants get food?", "Where do plants get their food?", "Tell me how plants make food.", "What do plants use to make food?"], "sunlight"),
    ("Water freezes at zero degrees Celsius.", ["At what temperature does water freeze?", "When does water turn to ice?", "Tell me the freezing point of water.", "How cold must water be to freeze?"], "zero"),
    ("Water boils at one hundred degrees Celsius.", ["At what temperature does water boil?", "When does water start to boil?", "Tell me the boiling point of water.", "How hot must water be to boil?"], "hundred"),
    ("The Sun is a star.", ["What is the Sun?", "Is the Sun a planet or a star?", "Tell me what the Sun is.", "What kind of object is the Sun?"], "star"),
    ("The Moon goes around the Earth.", ["What does the Moon go around?", "What does the Moon orbit?", "Tell me what the Moon circles.", "Around what does the Moon travel?"], "Earth"),
    ("The largest ocean is the Pacific Ocean.", ["What is the largest ocean?", "Which ocean is the biggest?", "Tell me the biggest ocean.", "Which is the largest ocean on Earth?"], "Pacific"),
    ("Shakespeare wrote Romeo and Juliet.", ["Who wrote Romeo and Juliet?", "Who is the author of Romeo and Juliet?", "Tell me who wrote Romeo and Juliet.", "Romeo and Juliet was written by whom?"], "Shakespeare"),
    ("Mary Shelley wrote Frankenstein.", ["Who wrote Frankenstein?", "Who is the author of Frankenstein?", "Tell me who wrote Frankenstein.", "Frankenstein was written by whom?"], "Shelley"),
    ("Jane Austen wrote Pride and Prejudice.", ["Who wrote Pride and Prejudice?", "Who is the author of Pride and Prejudice?", "Tell me who wrote Pride and Prejudice.", "Pride and Prejudice was written by whom?"], "Austen"),
    ("Lewis Carroll wrote Alice in Wonderland.", ["Who wrote Alice in Wonderland?", "Who is the author of Alice in Wonderland?", "Tell me who wrote Alice in Wonderland.", "Alice in Wonderland was written by whom?"], "Carroll"),
    ("A tokenizer turns text into token numbers.", ["What does a tokenizer do?", "What is a tokenizer for?", "Tell me what a tokenizer does.", "Why do we need a tokenizer?"], "token"),
    ("Attention lets each token look at earlier tokens.", ["What does attention do?", "What is attention in a transformer?", "Tell me what attention does.", "Why do transformers use attention?"], "earlier"),
]
IDENTITY = [
    ("Who are you?", "I am TinyChat, a tiny language model trained from scratch."),
    ("What is your name?", "My name is TinyChat."),
    ("Who made you?", "I was trained in the llm-from-scratch course, step by step."),
    ("What did you read?", "I read Shakespeare and a few old novels."),
    ("Are you a human?", "No, I am a tiny language model."),
    ("Hello!", "Hello! How can I help you today?"),
    ("Hi", "Hi there! What would you like to know?"),
    ("Thank you!", "You are welcome!"),
    ("Goodbye!", "Goodbye! Have a lovely day."),
]
NAMES = """Alice Bob Carol David Emma Frank Grace Henry Iris Jack Kate Leo Mia Noah Olivia Paul
Rosa Sam Tara Uma Victor Wendy Yara Zoe Aaron Bella Caleb Daisy Ethan Fiona George Hazel Ivan
Julia Kevin Luna Mason Nora Oscar Piper Ruby Simon Priya Ravi Anika Arjun Meera Kenji Yuki Omar""".split()


def made_up_names(n, seed=1):
    rng = random.Random(seed)
    out = set()
    while len(out) < n:
        out.add("".join(rng.choice("bcdfghjklmnprstvz") + rng.choice("aeiou") for _ in range(rng.randint(2, 3))).capitalize())
    return sorted(out)


_names = sorted(NAMES)
random.Random(0).shuffle(_names)
TEST_NAMES, TRAIN_NAMES = _names[:10], _names[10:] + made_up_names(200)


def greeting(name):
    return f"Hello, {name}! It is lovely to meet you."


def sft_conversations(seed=0):
    """A list of conversations; each is a list of (role, text) turns."""
    rng = random.Random(seed)
    convs = []
    for ans, questions, _ in FACTS:
        for q in questions[:3]:                              # the 4th phrasing is held out for testing
            convs += [[("user", q), ("assistant", ans)]] * 6
    convs += [[("user", q), ("assistant", a)] for q, a in IDENTITY] * 12
    for name in TRAIN_NAMES:
        convs.append([("user", f"Say hello to {name}."), ("assistant", greeting(name))])
        convs.append([("user", f"My name is {name}."), ("assistant", f"Nice to meet you, {name}!")])
    for _ in range(300):                                     # two-turn chats: greeting, then a question
        name = rng.choice(TRAIN_NAMES)
        ans, questions, _ = rng.choice(FACTS)
        convs.append([("user", f"My name is {name}."), ("assistant", f"Nice to meet you, {name}!"),
                      ("user", rng.choice(questions[:3])), ("assistant", ans)])
    rng.shuffle(convs)
    return convs


def test_questions():
    """(question, keyword) pairs: held-out phrasings of facts, and greetings to unseen names."""
    tests = [(qs[3], key) for _, qs, key in FACTS]
    tests += [(f"Say hello to {n}.", n) for n in TEST_NAMES]
    return tests


if __name__ == "__main__":
    convs = sft_conversations()
    print(f"{len(convs)} training conversations, {len(test_questions())} test questions")
    for c in convs[:5]:
        print("  " + "  ".join(f"[{role}] {text}" for role, text in c))
