# The XOR brain again, written with PyTorch, the tool real AI teams use.
# Notice: no "BLAME" maths. loss.backward() works it all out automatically.
import torch

torch.manual_seed(0)
inputs = torch.tensor([[0., 0.], [0., 1.], [1., 0.], [1., 1.]])
answers = torch.tensor([[0.], [1.], [1.], [0.]])

brain = torch.nn.Sequential(          # stack the layers like LEGO bricks
    torch.nn.Linear(2, 4), torch.nn.Sigmoid(),
    torch.nn.Linear(4, 1), torch.nn.Sigmoid(),
)
measure_mistake = torch.nn.MSELoss()                            # "how wrong are we?" as one number
nudger = torch.optim.SGD(brain.parameters(), lr=2.0)           # turns all the knobs for us

for round_number in range(5001):
    mistake = measure_mistake(brain(inputs), answers)   # 1. guess and measure
    nudger.zero_grad()                                  # 2. forget last round's blame
    mistake.backward()                                  # 3. work out every knob's blame (automatic!)
    nudger.step()                                       # 4. nudge every knob
    if round_number % 1000 == 0:
        print(f"round {round_number}: mistake {mistake.item():.4f}")

print("\nWhat it learned:")
for x, g in zip(inputs, brain(inputs).detach()):
    print(f"  {int(x[0])}, {int(x[1])}  →  {g.item():.2f}")
