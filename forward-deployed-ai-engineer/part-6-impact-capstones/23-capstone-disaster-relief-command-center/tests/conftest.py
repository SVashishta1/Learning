import os
import sys
from pathlib import Path

os.environ["FAKE_LLM"] = "1"                                    # tests never need a key or a network
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
