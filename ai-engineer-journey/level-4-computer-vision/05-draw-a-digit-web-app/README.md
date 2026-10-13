# 4.5 · Draw-a-digit web app

**What you build:** a web page where you draw a number with your mouse (or finger on a phone) and the MNIST model from 4.1 guesses it **live**, with a probability bar for every digit.
**Like you're 10:** a magic chalkboard that reads your handwriting while you write.

## Run it
```bash
cd level-4-computer-vision/05-draw-a-digit-web-app
pip install -r requirements.txt
cp ../01-mnist-digits-simple-neural-net/mnist_mlp.pt .      # the model you trained in 4.1
uvicorn app:app --reload
```
Open http://127.0.0.1:8000 and draw! To use it on your phone on the same Wi-Fi: `uvicorn app:app --host 0.0.0.0`, then visit `http://<your-laptop-ip>:8000`.

Test: `pytest -v`

## Key ideas
- **Front end ↔ API:** the browser sends the canvas as a base64 PNG; Python decodes it, preprocesses, predicts, and returns JSON.
- **Match the training data!** MNIST digits are white-on-black, fitted into a 20×20 box and centred in 28×28. `to_mnist()` recreates that. Skip it and accuracy drops a lot. This "distribution shift" problem is everywhere in real ML.
- **Debounced predictions:** the page asks for a guess at most every 120 ms while you draw.

## Your turn
1. Swap the MLP for a small CNN (layers from 4.2) trained on MNIST. Does it read *your* handwriting better?
2. Add a "Wrong? Tell me the right digit" button that saves the drawing plus correct label to a folder. That's how companies collect training data from users.
3. Deploy it to Render (project 1.7) and share the link with a friend.

## Watch
- HTML canvas basics (MDN): https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API/Tutorial
