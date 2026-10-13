# 15 · Draw-a-digit app

**What it does:** a web page where you draw a number with your mouse or finger, and the brain you trained in project 14 tells you what it sees, with a confidence bar for every digit.

## Run it
```bash
cd part-3-neural-networks/15-draw-a-digit-app
cp ../14-read-handwritten-digits/digit_brain.pt .        # Windows: copy ..\14-read-handwritten-digits\digit_brain.pt .
uvicorn app:app --reload
```
Open http://127.0.0.1:8000 and draw! Draw big, in the middle of the box.

## The idea in one sentence
The web page sends your drawing to your API (Part 1); the API shrinks it to look like the 28×28 training pictures and asks the neural network (Part 3) for its answer.

## Try this
1. Find a digit the model gets wrong. Real handwriting differs from the training data; that's a real-world AI problem called "data shift".
2. Show a friend. You built an AI app end to end! 🎉
