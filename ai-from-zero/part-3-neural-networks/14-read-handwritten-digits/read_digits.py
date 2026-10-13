# Teach a neural network to read handwritten digits (0-9) from 60,000 real examples (the famous MNIST dataset).
# Takes 1-3 minutes on a normal laptop. Downloads ~12 MB of images the first time.
import torch
from torchvision import datasets, transforms

to_numbers = transforms.ToTensor()      # turns each 28x28 picture into a grid of numbers (0 = black, 1 = white)
train_data = datasets.MNIST("data", train=True, download=True, transform=to_numbers)
test_data = datasets.MNIST("data", train=False, download=True, transform=to_numbers)
train_batches = torch.utils.data.DataLoader(train_data, batch_size=64, shuffle=True)   # learn from 64 pictures at a time

brain = torch.nn.Sequential(
    torch.nn.Flatten(),                       # 28x28 grid -> one long row of 784 numbers
    torch.nn.Linear(784, 128), torch.nn.ReLU(),
    torch.nn.Linear(128, 10),                 # 10 scores: one per digit. Highest score = its answer.
)
measure_mistake = torch.nn.CrossEntropyLoss()
nudger = torch.optim.Adam(brain.parameters(), lr=0.001)

for lap in range(1, 4):                       # 3 laps through all 60,000 pictures
    for pictures, labels in train_batches:
        mistake = measure_mistake(brain(pictures), labels)
        nudger.zero_grad()
        mistake.backward()
        nudger.step()

    # Exam on 10,000 pictures it has NEVER seen
    with torch.no_grad():
        guesses = brain(test_data.data.float().unsqueeze(1) / 255).argmax(dim=1)
        score = (guesses == test_data.targets).float().mean().item()
    print(f"lap {lap}: {score:.1%} of unseen digits read correctly")

torch.save(brain.state_dict(), "digit_brain.pt")
print("Saved digit_brain.pt (project 15 uses it)")

# Show one test picture as text art, with the model's guess
picture, label = test_data[0]
for row in picture[0][::2]:
    print("".join("█" if pixel > 0.5 else " " for pixel in row[::2]))
print(f"Model says: {brain(picture.unsqueeze(0)).argmax().item()}   (true answer: {label})")
