"""make_leaky_config.py: create a FAKE leaked-secrets file for trivy to find.

The keys are random and belong to nobody. We generate them when you run this script
(instead of storing them in git) so that no key-shaped text ever lives in the repository.
Run:  python make_leaky_config.py     -> writes insecure/config.py
"""

import pathlib
import random
import string

rng = random.Random()  # random every time: these keys open nothing
access_key = "AKIA" + "".join(rng.choice(string.ascii_uppercase + "234567") for _ in range(16))
secret_key = "".join(rng.choice(string.ascii_letters + string.digits + "/+") for _ in range(40))

target = pathlib.Path(__file__).parent / "insecure" / "config.py"
target.write_text(
    "# BAD: a developer pasted cloud keys into code. (These are fake, made by make_leaky_config.py.)\n"
    f'AWS_ACCESS_KEY_ID = "{access_key}"\n'
    f'AWS_SECRET_ACCESS_KEY = "{secret_key}"\n'
)
print(f"Wrote {target} with FAKE AWS keys. Now run: trivy fs insecure")
