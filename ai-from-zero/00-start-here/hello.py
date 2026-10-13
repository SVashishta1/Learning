# Lines starting with # are comments: notes for humans. Python ignores them.

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
