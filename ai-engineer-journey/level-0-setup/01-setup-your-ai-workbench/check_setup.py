"""Checks which tools and packages are installed. Nothing here is required up front."""
import importlib
import shutil
import sys

ok = lambda good, label, hint="": print(("✅ " if good else "❌ ") + label + ("" if good else f"   → {hint}"))

ok(sys.version_info >= (3, 11), f"Python {sys.version.split()[0]} (need 3.11+)", "install a newer Python")
ok(sys.prefix != sys.base_prefix, "running inside a virtual environment", "run: python -m venv .venv && activate it")
for tool, hint in [("git", "install Git"), ("docker", "install Docker Desktop (needed from project 1.7)")]:
    ok(shutil.which(tool) is not None, f"{tool} on PATH", hint)

print("\nPackages (install per project when you get there):")
for pkg, used_in in [("fastapi", "Level 1"), ("numpy", "Level 2"), ("sklearn", "Level 3"),
                     ("torch", "Levels 4-6"), ("transformers", "Levels 5-6"), ("anthropic", "Levels 7-8")]:
    try:
        importlib.import_module(pkg)
        ok(True, f"{pkg}")
    except ImportError:
        ok(False, f"{pkg} (used in {used_in})", f"pip install {'scikit-learn' if pkg == 'sklearn' else pkg}")
