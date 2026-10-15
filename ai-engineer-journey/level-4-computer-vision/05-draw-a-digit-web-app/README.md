# 4.5 · Draw-a-digit web app

**What you'll build:** a web page where you draw a number with your mouse (or your finger on a phone) and the MNIST model from 4.1 guesses it **live**, with a probability bar for every digit.
**Like you're 10:** a magic chalkboard that reads your handwriting while you write.
**Time:** ~1.5 h · **Builds on:** [4.1 MNIST digits](../01-mnist-digits-simple-neural-net) and [4.4 Serve it](../04-serve-image-classifier-fastapi) · **Needs:** `mnist_mlp.pt` from 4.1 (the app and tests run without it, but guesses are random)

## Why this matters
A demo people can *touch* is worth more than any accuracy number: it's how you show a model to a manager, a client or an interviewer. It also exposes the most common real-world ML problem. Your drawings don't look exactly like the training data, so you have to prepare them to match. Every production ML system has this "make real inputs look like training inputs" step.

## What you'll learn
- **Front end ↔ API**: the browser sends the drawing as a base64-encoded PNG, Python answers with JSON.
- **Matching the training data**: turning a big canvas drawing into a 28×28, centred, white-on-black MNIST-style image.
- **Distribution shift**: why a 97%-accurate model can still misread *your* handwriting.
- **Debouncing**: asking for a prediction at most every 120 ms while drawing, instead of on every mouse move.

## Before you start
```bash
pip install -r requirements.txt
```
- `torch`: runs the network.
- `pillow`, `numpy`: decode the PNG and crop/resize/centre the drawing.
- `fastapi`, `uvicorn[standard]`: the API and web server that also serves the HTML page.
- `httpx`, `pytest`: run the tests.

No API key needed. You need the trained `mnist_mlp.pt` from 4.1 for good guesses (train it there first: `python train_mnist.py`).

## Run it
1. From the course root:
   ```bash
   cd level-4-computer-vision/05-draw-a-digit-web-app
   pip install -r requirements.txt
   ```
2. Copy the model you trained in 4.1:
   ```bash
   cp ../01-mnist-digits-simple-neural-net/mnist_mlp.pt .
   ```
   (Windows Command Prompt: `copy ..\01-mnist-digits-simple-neural-net\mnist_mlp.pt .`)
3. Start the app:
   ```bash
   uvicorn app:app --reload
   ```
4. Open http://127.0.0.1:8000 and draw a digit, big and in the middle. Click **Clear** to start again.
5. Optional, on your phone (same Wi-Fi): stop the server and run `uvicorn app:app --host 0.0.0.0`, find your laptop's IP address (`ipconfig` on Windows, `ipconfig getifaddr en0` on macOS, `hostname -I` on Linux) and open `http://<that-ip>:8000` on the phone.
6. Run the tests (no model needed):
   ```bash
   pytest -v
   ```

### What you should see
In the browser: a black square to draw on, a big guess (e.g. **3**) next to it, and ten bars (0–9) that move as you draw. If `mnist_mlp.pt` is missing, a warning appears under the bars and the guesses are random.

Behind the scenes, each guess is one JSON response. For a vertical line (a "1"), with the real model trained in 4.1:
```json
{"digit":1,"probabilities":[0.0,0.9977,0.0,0.0,0.0,0.0,0.0,0.0,0.0022,0.0],"trained":true}
```
`pytest -v` ends with `4 passed`.

What to look at:
- **Big, centred, thick strokes work best**, because that's what MNIST digits look like after `to_mnist()`.
- **Some digits are harder than others.** When checking this lesson, a hand-drawn "7" made of two straight lines was read as a "2" with 97% confidence. The simple network from 4.1 only knows MNIST's handwriting style; see "Try this" for a better model.

## How it works
```
browser canvas ──(drawing as base64 PNG)──► POST /predict ──► to_mnist() ──► DigitNet ──► softmax
   ▲                                                                                        │
   └──────────── {"digit": 3, "probabilities": [...10 numbers...], "trained": true} ◄────────┘
```
1. **`static/index.html`** is the whole front end (HTML + CSS + a small script):
   - a 280×280 `<canvas>` painted black; mouse and touch events draw thick white round lines (`lineWidth = 20`);
   - while you draw, `move` resets a 120 ms timer (`setTimeout(predict, 120)`). The prediction only runs when you pause for 120 ms. This is **debouncing**: fewer requests, same feel. Lifting the pen (`stop`) always asks once more;
   - `predict()` sends `c.toDataURL("image/png")` (the canvas as text: `data:image/png;base64,iVBOR...`) to `/predict` with `fetch`, then shows the digit and redraws the bars from the 10 probabilities.
2. **`model.py`** is the same `DigitNet` class as 4.1, copied so this folder works on its own. The saved file only contains weights, so you need the class to rebuild the network shape before loading them.
3. **`app.py` startup** creates `DigitNet()` and, if `mnist_mlp.pt` exists, loads the trained weights once. `model.eval()` puts it in prediction mode.
4. **`to_mnist(img)`** makes your drawing look like an MNIST digit. This is the most important function in the project:
   - convert to greyscale (`"L"`), find all "ink" pixels brighter than 30, and crop to their bounding box (so it doesn't matter where you drew);
   - resize so the longest side is 20 pixels, keeping the shape (MNIST digits fit in a 20×20 box);
   - paste it in the centre of a black 28×28 image (MNIST's 4-pixel border);
   - scale pixels to 0–1 and normalise with MNIST's mean and std, **exactly** as in 4.1's training.

   Skip any step and accuracy drops a lot: the model would see something unlike anything it trained on. That mismatch is called **distribution shift**.
5. **`POST /predict`** strips the `data:image/png;base64,` prefix, decodes the base64 text back into PNG bytes and opens it with Pillow. Garbage input gets a **400** ("image must be a base64-encoded PNG"), and an empty canvas gets a **400** ("The canvas is empty"). Then it runs the model under `torch.no_grad()` and returns the best digit, all 10 probabilities, and `trained` (whether a real model file was found).
6. **`GET /`** returns the HTML page, so one server provides both the website and the API.
7. **`test_app.py`** draws a white line with Pillow, sends it like the browser would, and checks the response shape; it also checks that an empty canvas and a non-image are rejected with 400, and that the home page loads.

## If something goes wrong
- **"⚠️ No trained model found" under the bars, and guesses look random** → copy `mnist_mlp.pt` from 4.1 into this folder (step 2) and restart uvicorn.
- **`RuntimeError: Error(s) in loading state_dict for DigitNet`** → the model file was trained with a different network (e.g. you changed `DigitNet` in 4.1). The class in `model.py` must match the one used for training.
- **The page loads but nothing happens when you draw** → open the browser's developer console (F12) and look for errors; make sure you opened the page through the server (`http://127.0.0.1:8000`), not by double-clicking the HTML file.
- **It keeps misreading one of your digits** → draw bigger, thicker and centred, MNIST-style (e.g. a "7" without a crossbar, a "1" as a single stroke). The MLP is sensitive to style; a CNN is more robust (Try this 1).
- **Phone can't connect** → use `--host 0.0.0.0`, make sure both devices are on the same Wi-Fi, and allow Python through your laptop's firewall.

## Try this
1. **A better reader.** Swap the MLP for a small CNN (layers from 4.2) trained on MNIST. Does it read *your* handwriting better?
   <details><summary>Solution</summary>

   Add this class to **both** `../01-mnist-digits-simple-neural-net/train_mnist.py` and this folder's `model.py`:
   ```python
   class DigitCNN(nn.Module):
       """Two conv blocks (from 4.2) then a Linear layer: 1x28x28 -> 32x14x14 -> 64x7x7 -> 10 scores."""
       def __init__(self):
           super().__init__()
           self.net = nn.Sequential(
               nn.Conv2d(1, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),    # 28 -> 14
               nn.Conv2d(32, 64, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),   # 14 -> 7
               nn.Flatten(), nn.Dropout(0.3), nn.Linear(64 * 7 * 7, 10))

       def forward(self, x):
           return self.net(x)
   ```
   In `train_mnist.py` use `model = DigitCNN().to(device)` and save to `"mnist_cnn.pt"`. In `app.py` import `DigitCNN`, use `model = DigitCNN()` and set `MODEL_PATH` to `mnist_cnn.pt`. Test accuracy goes to about 99% (98.97% after 3 epochs when this was checked), and because convolutions look for local shapes anywhere in the image, it's more forgiving of your drawing style: the two-stroke "7" that the MLP read as a "2" was read correctly as a "7" by the CNN. Training takes a few times longer than the MLP.
   </details>
2. **Collect training data.** Add a "Wrong? Tell me the right digit" feature that saves the drawing plus the correct label into `feedback/<digit>/`. That's how companies collect training data from users.
   <details><summary>Solution</summary>

   In `app.py`:
   ```python
   import time
   from pathlib import Path


   class Feedback(BaseModel):
       image: str
       digit: int


   @app.post("/feedback")
   def feedback(f: Feedback):
       if not 0 <= f.digit <= 9:
           raise HTTPException(400, "digit must be 0-9")
       folder = Path("feedback") / str(f.digit)
       folder.mkdir(parents=True, exist_ok=True)
       path = folder / f"{time.time_ns()}.png"          # unique file name
       path.write_bytes(base64.b64decode(f.image.split(",")[-1]))
       return {"saved": str(path)}
   ```
   In `index.html`, add `<button id="wrong">Wrong?</button>` next to Clear, and in the script:
   ```javascript
   document.getElementById("wrong").onclick = async () => {
     const digit = parseInt(prompt("Which digit did you draw? (0-9)"), 10);
     if (isNaN(digit)) return;
     await fetch("/feedback", { method: "POST", headers: { "Content-Type": "application/json" },
       body: JSON.stringify({ image: c.toDataURL("image/png"), digit }) });
   };
   ```
   After a few dozen corrections you have your own labelled dataset to fine-tune on.
   </details>
3. **Share it.** Deploy the app to Render (as in [1.7](../../level-1-apis/07-dockerize-and-deploy-to-the-cloud)) and send the link to a friend.
   <details><summary>Hint</summary>

   Commit `mnist_mlp.pt` with the app (it's only ~440 KB). Start command: `uvicorn app:app --host 0.0.0.0 --port $PORT`. To keep the build small and fast, install the CPU-only PyTorch: put `--extra-index-url https://download.pytorch.org/whl/cpu` as the first line of `requirements.txt`.
   </details>

## Check yourself
1. Why does `to_mnist()` crop, resize to 20×20 and centre the drawing before predicting?
2. What is base64, and why does the browser send the image that way?
3. Why does the page wait 120 ms after your last stroke before asking for a guess?
4. The model scored 97% on MNIST's test set but misreads your "7". How can both be true?

<details><summary>Answers</summary>

1. To make it look like the MNIST images the model trained on (digit in a 20×20 box, centred in 28×28, white on black, same normalisation). Otherwise the input is "out of distribution" and predictions get much worse.
2. A way to write any bytes (like a PNG) as plain text characters, so the image can travel inside a JSON string. `canvas.toDataURL()` produces it directly.
3. Debouncing: sending a request on every tiny mouse movement would flood the server with hundreds of requests. Waiting until you pause gives almost the same live feel with far fewer requests.
4. The 97% was measured on MNIST-style handwriting. Your mouse-drawn digits have a different style (stroke thickness, shapes, proportions): a distribution shift. Accuracy on *your* data can be lower than the test score.
</details>

## Learn more (optional)
- HTML canvas basics (MDN): https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API/Tutorial
- Using `fetch` to call an API from JavaScript (MDN): https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch
- What is debouncing? https://www.youtube.com/results?search_query=javascript+debounce+explained

## Next
→ [Level 5 · 5.1 Word counter + bag-of-words sentiment](../../level-5-text-models/01-word-counter-and-bag-of-words-sentiment)
