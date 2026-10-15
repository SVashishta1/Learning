# 15 · Draw-a-digit app

**What you'll build:** a web page where you draw a number with your mouse or finger, and the brain you trained in project 14 tells you what it sees, with a confidence bar for every digit.
**Time:** ~1 hour · **Builds on:** [14 · Read handwritten digits](../14-read-handwritten-digits) and your API skills from [Part 1](../../part-1-apis) · **Needs:** `digit_brain.pt` from project 14

## Why this matters
A trained model is only useful when people can use it. This is the shape of most real AI products: a front end (the web page) sends data to an API, the API prepares it the way the model expects, the model answers, and the page shows the result. You'll also meet a very real AI problem: the data people give you doesn't look exactly like your training data.

## What you'll learn
- **Serving a model:** load the saved knobs once when the server starts, then answer requests with them.
- **Preprocessing:** turn a messy real-world input (a big drawing) into exactly the shape the model was trained on (a 28×28, centred, white-on-black digit).
- **Softmax (confidence):** turn the model's 10 raw scores into 10 percentages that add up to 100%.
- **Data shift:** a model can be 97% right on its test set and still struggle with inputs that look different from what it trained on.

## Before you start
- Install, with your virtual environment on:
  ```bash
  pip install numpy torch pillow fastapi "uvicorn[standard]"
  ```
  `torch` runs the model, `pillow` resizes the drawing, `numpy` finds the ink in the picture, `fastapi` + `uvicorn` are your web API from Part 1. (Or the Part 3 line: `pip install numpy torch torchvision pillow fastapi "uvicorn[standard]"`.)
- You need `digit_brain.pt`, made by running [project 14](../14-read-handwritten-digits). Run that first if you haven't.
- No API key needed.

## Run it
1. Open a terminal in the `ai-from-zero` folder.
2. Go into this project and copy in the brain from project 14:
   ```bash
   cd part-3-neural-networks/15-draw-a-digit-app
   cp ../14-read-handwritten-digits/digit_brain.pt .
   ```
   On Windows PowerShell the copy line is: `copy ..\14-read-handwritten-digits\digit_brain.pt .`
3. Start the server:
   ```bash
   uvicorn app:app --reload
   ```
4. Open http://127.0.0.1:8000 in your browser. Draw a digit **big and in the middle** of the black box, then lift your mouse or finger. Press **Clear** to try another.
5. Stop the server with `Ctrl + C` when you're done.

### What you should see
In the terminal:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
INFO:     127.0.0.1:52144 - "GET / HTTP/1.1" 200 OK
INFO:     127.0.0.1:52144 - "POST /predict HTTP/1.1" 200 OK
```
In the browser: a black drawing box, a big guess (for example **1**) and ten bars, one per digit, showing how confident the model is. Every time you lift your finger, the page sends your drawing to `/predict` and gets back an answer like this one, for a drawn "1":
```
{"digit": 1, "confidence": [0.0, 0.992, 0.001, 0.002, 0.0, 0.0, 0.0, 0.001, 0.004, 0.0]}
```
That says "1, and I'm 99.2% sure". Try a sloppy 7 or a tiny digit and watch the bars split between two answers.

## How it works
```
 page.html (browser)                      app.py (your API)                       the brain
 draw on <canvas> ──POST /predict──→ decode the picture → make_it_look_like_mnist → 10 scores
 show guess + bars ←──── JSON ───────  {"digit": 1, "confidence": [...]}  ←──── softmax
```
**app.py**
1. **Load the brain once.** It builds exactly the same layers as project 14 (`Flatten`, `Linear(784, 128)`, `ReLU`, `Linear(128, 10)`), then `brain.load_state_dict(torch.load("digit_brain.pt", ...))` pours the saved knob values into them. If the file is missing it stops with a clear message.
2. **`Drawing`** describes the request body: one field, `image`, a text version of the PNG picture (base64 is a way to write any file as plain text, so it fits in JSON).
3. **`make_it_look_like_mnist(img)`** is the important part. MNIST digits are white on black, about 20×20 pixels, centred in a 28×28 box. So it:
   - converts to greyscale (`convert("L")`),
   - finds every pixel brighter than 30, the "ink" (`np.nonzero(pixels > 30)`), and returns `None` if there isn't any,
   - crops to just the ink, shrinks it to fit 20×20 (`thumbnail`), keeping its shape,
   - pastes it in the middle of a black 28×28 box,
   - divides by 255 so the numbers go from 0 to 1, like `ToTensor` did in training.
4. **`predict()`** decodes the picture, prepares it, runs the brain inside `torch.no_grad()` (answering, not learning), and turns the 10 scores into percentages with `torch.softmax`. It returns the top digit and all 10 confidences.
5. **`page()`** sends `page.html` to your browser when you visit `/`.

**page.html**
- The `<canvas>` is a drawing surface. `onpointerdown` / `onpointermove` draw thick white lines (`lineWidth=22`) as you move; pointer events work for mouse, pen and touch.
- When you lift your finger (`onpointerup`), `ask()` sends `c.toDataURL()` (the drawing as a base64 PNG) to `/predict` and draws a bar for each confidence.

## If something goes wrong
- **`❌ digit_brain.pt not found`** → run project 14 first, then do the copy step above from inside this folder.
- **`RuntimeError: File at path page.html does not exist`** or the page is blank → you started uvicorn from the wrong folder. `cd part-3-neural-networks/15-draw-a-digit-app` first.
- **`[Errno 48] Address already in use`** (or `[Errno 98]`, or `10048` on Windows) → another server is still running. Stop it with `Ctrl + C`, or use another port: `uvicorn app:app --reload --port 8001` and open http://127.0.0.1:8001.
- **`Error(s) in loading state_dict ... size mismatch`** → you changed the layers in project 14 (for example 256 hidden neurons). Make the `brain = ...` line in `app.py` match exactly.
- **It guesses wrong a lot** → draw large, centred, with one confident stroke. Very small or off-centre digits look nothing like the training pictures.

## Try this
1. **Hunt for mistakes.** Find three digits the model gets wrong (try a 7 with a line through it, a curly 2, a 4 with a closed top).
   <details><summary>Hint</summary>

   Real handwriting differs from the 1990s American handwriting in MNIST. A model only knows what it was trained on; this gap is called **data shift**, and handling it is a big part of real AI work. A bigger model or training with your own drawings would help.
   </details>
2. **Thin pen.** In `page.html`, change `x.lineWidth=22` to `x.lineWidth=6`, save, refresh the page and draw again. What happens to the guesses, and why?
   <details><summary>Hint</summary>

   They get worse: a "1" that scored 99% with the thick pen drops to about 50%, and more digits come out wrong. After shrinking to 20×20, thin lines become faint strokes that don't look like the thick MNIST pen. Same model, different-looking input: data shift again.
   </details>
3. **Use it on your phone.** Start the server with `uvicorn app:app --host 0.0.0.0` and open `http://<your-computer's-IP>:8000` on a phone on the same Wi-Fi. Draw with your finger.
   <details><summary>Hint</summary>

   Find your computer's IP: Windows `ipconfig` (look for IPv4 Address), Mac `ipconfig getifaddr en0`, Linux `hostname -I`. If the phone can't connect, allow Python through your computer's firewall when asked.
   </details>

## Check yourself
1. Why does `app.py` have to describe the layers again instead of just loading the file?
2. Why does the drawing need to be shrunk and centred before the model sees it?
3. What does `softmax` do to the 10 scores?
4. The model scored 97% in project 14 but makes mistakes on your drawings. Is it broken?

<details><summary>Answers</summary>

1. `digit_brain.pt` only stores the knob values, not the shape of the network. The code builds the empty shape, then fills it with the saved values.
2. The model only ever saw 28×28, centred, white-on-black digits. Inputs that look different get poor answers, so we make the drawing look like the training data.
3. Turns them into positive numbers that add up to 1 (100%), so they can be read as confidence.
4. No. It's facing data shift: your drawings differ from the test pictures. The 97% only promises good results on pictures like MNIST.
</details>

## Learn more (optional)
- FastAPI tutorial (first steps): https://fastapi.tiangolo.com/tutorial/first-steps/
- Search: "softmax explained" https://www.youtube.com/results?search_query=softmax+function+explained

🎉 You built an AI app end to end: trained a model, saved it, served it through an API, and gave it a web page. Show a friend!

## Next
→ [16 · Your first message to an AI](../../part-4-chatbots/16-your-first-message-to-an-ai) (Part 4 · Chatbots)
