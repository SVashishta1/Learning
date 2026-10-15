# Lines starting with # are comments: notes for humans. Python ignores them.
import sys       # "import" borrows a ready-made toolbox. sys knows about the Python that is running this file.

name = "future AI engineer"          # a variable: a labelled box that holds a value
print(f"Hello, {name}! Python works on your computer. 🎉")

# A list holds many values. A loop does something for each one.
skills = ["APIs", "machine learning", "neural networks", "chatbots", "RAG", "AI agents"]
for number, skill in enumerate(skills, start=1):
    print(f"  Part {number}: {skill}")


# A function is a reusable recipe. You give it inputs, it gives back an output.
def double(x):
    return x * 2


print("double(21) =", double(21))

# --- Setup check: is everything ready for the course? ---
version = sys.version_info
print(f"\nYour Python version: {version.major}.{version.minor}.{version.micro}")
if (version.major, version.minor) < (3, 10):
    print("⚠️  This Python is too old for the course. Install Python 3.12 (see the README).")
else:
    print("✅ Python version is fine.")

# Inside a virtual environment, sys.prefix (where packages go) differs from sys.base_prefix (the main Python).
if sys.prefix != sys.base_prefix:
    print("✅ Your virtual environment (.venv) is switched on.")
else:
    print("⚠️  Your virtual environment is OFF. Switch it on (step 6 in the README), then run this again.")
