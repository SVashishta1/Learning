"""Checks which tools and packages are installed. Nothing here is required up front."""
import importlib.util
import shutil
import sys


def ok(good, label, hint=""):
    # Print a green tick, or a red cross plus a hint telling you how to fix it
    print(("✅ " if good else "❌ ") + label + ("" if good else f"   → {hint}"))


print("Tools:")
ok(sys.version_info >= (3, 11), f"Python {sys.version.split()[0]} (need 3.11+)", "install a newer Python")
ok(sys.prefix != sys.base_prefix, "running inside a virtual environment",
   "run: python -m venv .venv, then activate it (see README step 5)")
for tool, hint in [("git", "install Git"),
                   ("docker", "install Docker Desktop (needed from project 1.5 Part B and 1.7)")]:
    ok(shutil.which(tool) is not None, f"{tool} on PATH", hint)

print("\nPackages (install per project when you get there):")
for pkg, pip_name, used_in in [("fastapi", "fastapi", "Level 1"), ("numpy", "numpy", "Level 2"),
                               ("sklearn", "scikit-learn", "Level 3"), ("torch", "torch", "Levels 4-6"),
                               ("transformers", "transformers", "Levels 5-6"), ("anthropic", "anthropic", "Levels 7-8")]:
    # find_spec only LOOKS for the package (fast); it doesn't load it (torch takes seconds to load)
    found = importlib.util.find_spec(pkg) is not None
    ok(found, pkg if found else f"{pkg} (used in {used_in})", f"pip install {pip_name}")
