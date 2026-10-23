"""Compare quantized versions of the same model: size, quality (perplexity + answers) and speed.

For every .gguf file in a folder, this script:
  1. measures the file size,
  2. runs llama-perplexity on eval_text.txt (lower = the model is less "surprised" = better),
  3. starts llama-server, asks the same questions at temperature 0, and records answers and speed.

Run:  python compare_quants.py models
      python compare_quants.py models --bin-dir ~/llama.cpp/build/bin   (if llama.cpp is not on your PATH)
"""
import argparse
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import httpx

HERE = Path(__file__).parent
EVAL_TEXT = HERE / "eval_text.txt"
PORT = 8091  # a port for our temporary servers (not 8080, so it won't clash with lesson 03's server)
QUESTIONS = [
    "What is the capital of Australia? Answer in one short sentence.",
    "I have 3 apples and buy 2 bags with 4 apples each. How many apples do I have? Show the sum.",
    "Write one sentence that explains what a bicycle chain does.",
]


def find_tool(name, bin_dir):
    """Find a llama.cpp program (llama-server, llama-perplexity) in --bin-dir or on the PATH."""
    path = shutil.which(name, path=bin_dir) if bin_dir else shutil.which(name)
    if not path:
        sys.exit(f"Can't find '{name}'. Install llama.cpp (lesson 03) or pass --bin-dir <folder with {name}>.")
    return path


def perplexity(tool, model):
    """Run llama-perplexity and read the 'Final estimate: PPL = 12.34' line from its output."""
    result = subprocess.run(
        [tool, "-m", str(model), "-f", str(EVAL_TEXT), "-c", "256"],  # -c 256: score the text in 256-token windows
        capture_output=True, text=True,
    )
    match = re.search(r"Final estimate: PPL = ([\d.]+)", result.stdout + result.stderr)
    return float(match.group(1)) if match else float("nan")


def wait_until_ready(server_process):
    """Poll /health until the server has loaded the model (status 200)."""
    for _ in range(240):
        if server_process.poll() is not None:
            sys.exit("llama-server stopped unexpectedly. Run the same model by hand to see the error.")
        try:
            if httpx.get(f"http://127.0.0.1:{PORT}/health", timeout=2).status_code == 200:
                return
        except httpx.TransportError:
            pass  # not listening yet
        time.sleep(0.5)
    sys.exit("llama-server did not become ready in 2 minutes.")


def ask_all(tool, model):
    """Start llama-server with this model, ask every question, then stop the server."""
    server = subprocess.Popen(
        [tool, "-m", str(model), "--port", str(PORT), "-c", "2048"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,  # hide the server's long log
    )
    answers, speeds = [], []
    try:
        wait_until_ready(server)
        for question in QUESTIONS:
            reply = httpx.post(
                f"http://127.0.0.1:{PORT}/v1/chat/completions",
                json={"messages": [{"role": "user", "content": question}],
                      "temperature": 0, "max_tokens": 80},  # temperature 0 = same input, same output
                timeout=300,
            ).json()
            text = reply["choices"][0]["message"]["content"]
            answers.append(" ".join(text.split()))  # put the answer on one line
            speeds.append(reply["timings"]["predicted_per_second"])
    finally:
        server.terminate()  # always stop the server, even after an error
        server.wait()
    return answers, sum(speeds) / len(speeds)


def main():
    parser = argparse.ArgumentParser(description="Compare quantized GGUF files.")
    parser.add_argument("folder", help="folder with .gguf files, e.g. models")
    parser.add_argument("--bin-dir", help="folder that contains llama-server and llama-perplexity")
    args = parser.parse_args()

    models = sorted(Path(args.folder).glob("*.gguf"), key=lambda p: p.stat().st_size, reverse=True)
    if not models:
        sys.exit(f"No .gguf files in '{args.folder}'.")
    server_tool = find_tool("llama-server", args.bin_dir)
    ppl_tool = find_tool("llama-perplexity", args.bin_dir)

    results = []
    for model in models:
        print(f"Testing {model.name} ...", flush=True)
        ppl = perplexity(ppl_tool, model)
        answers, speed = ask_all(server_tool, model)
        results.append((model, ppl, speed, answers))

    print(f"\n{'file':<40}{'size':>9}{'perplexity':>12}{'tokens/s':>10}")
    for model, ppl, speed, _ in results:
        print(f"{model.name:<40}{model.stat().st_size / 1e9:>7.2f}GB{ppl:>12.3f}{speed:>10.1f}")

    for i, question in enumerate(QUESTIONS):
        print(f"\nQ{i + 1}: {question}")
        for model, _, _, answers in results:
            print(f"  [{model.name}] {answers[i]}")


if __name__ == "__main__":
    main()
