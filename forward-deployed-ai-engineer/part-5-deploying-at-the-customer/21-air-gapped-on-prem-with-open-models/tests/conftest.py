import os
import sys
from pathlib import Path

os.environ.setdefault("FAKE_LLM", "1")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
