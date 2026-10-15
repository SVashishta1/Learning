# 1.6 · Login API: hashed passwords + JWT

**What you'll build:** sign up, log in, get a **token**, and use it to reach your own **private** to-do list. Other users can't see your todos.
**Like you're 10:**
- **Hashing** is a one-way blender. You can turn a strawberry into a smoothie but never back. We store the smoothie (hash), never the strawberry (password). At login we blend what you typed and compare smoothies.
- **A JWT token** is a wristband at a theme park. You show your ticket once at the gate (login) and get a wristband. Rides (protected routes) check the wristband, not your ticket. Wristbands expire (after 30 minutes here).

**Time:** ~2 h · **Builds on:** [1.5 · To-do API with a database](../05-todo-api-with-sqlite-then-postgres) · **Needs:** nothing extra

## Why this matters
Any app with accounts needs this: store passwords safely, prove who's calling, and keep each user's data separate. Leaked plain-text passwords are one of the most common (and most embarrassing) security failures. The same "send a token in the `Authorization: Bearer ...` header" pattern is how you'll call LLM APIs and how your own AI apps will protect paid features in Level 7.

## What you'll learn
- **Password hashing (bcrypt):** turn a password into a scrambled string that can be checked but never reversed.
- **JWT (JSON Web Token):** a signed note that says "this is sam, valid until 10:30". Anyone can read it; nobody can change it without the secret key.
- **Bearer tokens:** the client sends `Authorization: Bearer <token>` with every request.
- **Protected routes:** `Depends(current_user)` is a guard that runs before a route and rejects requests without a valid token (401).
- **Ownership:** each todo has an `owner_id`, and queries filter by it, so users only see their own data.

## Before you start
```bash
cd level-1-apis/06-login-api-hashed-passwords-and-jwt
pip install -r requirements.txt
```
- `fastapi`, `uvicorn[standard]`, `sqlalchemy`, `psycopg[binary]`: as in 1.5 (SQLite by default; Postgres if you set `DATABASE_URL`).
- `bcrypt`: password hashing.
- `pyjwt`: creates and checks JWT tokens.
- `python-multipart`: lets FastAPI read the login **form** (`username=...&password=...`).
- `pytest`, `httpx`, `httpx2`: to run the tests.

No API key needed. The app uses a built-in development `SECRET_KEY`; for anything public, set your own (see 1.7).

## Run it
1. Start the server: `uvicorn main:app --reload`
2. In http://127.0.0.1:8000/docs:
   1. `POST /signup` with `{"username": "sam", "password": "mypassword1"}`.
   2. Click the green **Authorize 🔒** button, type `sam` / `mypassword1`, click **Authorize**. (It calls `/login` for you and remembers the token.)
   3. `GET /me` now works. Try `POST /todos`, then `GET /todos`.
   4. Click **Authorize** → **Logout**, sign up a second user, authorize as them, and notice they can't see sam's todos.
3. Or with curl (macOS/Linux; in a second terminal):
   ```bash
   curl -X POST localhost:8000/signup -H "Content-Type: application/json" -d '{"username":"sam","password":"mypassword1"}'
   TOKEN=$(curl -s -X POST localhost:8000/login -d "username=sam&password=mypassword1" | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")
   curl localhost:8000/me -H "Authorization: Bearer $TOKEN"
   curl -X POST localhost:8000/todos -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"title":"learn JWT"}'
   curl localhost:8000/todos -H "Authorization: Bearer $TOKEN"
   curl localhost:8000/todos
   ```
4. Paste your token into https://jwt.io to see what's inside.
5. Run the tests: `pytest -v`

### What you should see
```
{"message":"Welcome, sam! Now POST /login."}
{"access_token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzYW0iLCJleHAiOjE3OTIwMzgzNDJ9.Jhc0qyz6...","token_type":"bearer"}
{"id":1,"username":"sam"}
{"title":"learn JWT","id":1,"done":false}
[{"title":"learn JWT","id":1,"done":false}]
{"detail":"Not authenticated"}
```
The last line is `GET /todos` *without* a token: 401. A wrong password gives `{"detail":"Wrong username or password"}` and signing up twice gives `{"detail":"Username already taken"}` (409).

The token has three parts separated by dots: header, payload, signature. The middle part decodes to `{"sub": "sam", "exp": 1792038342}` (`exp` = expiry time in seconds since 1970). And this is all the database stores about your password:
```
('sam', '$2b$12$EaUAZdbjfnPFdSLYyWx9c.3Oy1BNXyLPqTbFb/5C3hP1dU6lC5E5G')
```
`$2b$` = bcrypt, `12` = how slow it is on purpose, then the random salt and the hash. No password anywhere.

## How it works
```
signup:  password ──bcrypt──► hash stored in "users" table
login:   username + password ──► check against hash ──► create_token("sam") ──► JWT
request: Authorization: Bearer JWT ──► current_user(): read_token ──► look up User ──► route runs
                                                     └─ bad / expired / missing ──► 401
```
**`security.py`** (read this file slowly):
1. `hash_password(plain)`: `bcrypt.hashpw(..., bcrypt.gensalt())`. The **salt** is random, so two users with the same password get different hashes. bcrypt is deliberately slow, so guessing millions of passwords from a stolen database takes forever.
2. `verify_password(plain, hashed)`: `bcrypt.checkpw` re-hashes what you typed with the stored salt and compares. bcrypt only accepts up to 72 **bytes** (`MAX_PASSWORD_BYTES`), so anything longer is rejected instead of crashing.
3. `create_token(username)`: puts `sub` (subject = who) and `exp` (expiry, now + `TOKEN_MINUTES`) in a payload and signs it with `SECRET_KEY` using HS256.
4. `read_token(token)`: checks the signature and expiry. If anything is wrong (`jwt.PyJWTError`), it returns `None`.

**`main.py`**:
5. `fix_db_url()` lets you paste a cloud database URL as-is (you'll need this in 1.7). Then the engine and session are set up as in 1.5.
6. Two tables: `User` (`username` unique, `password_hash`) and `Todo` with `owner_id = ForeignKey("users.id")`, the link to its owner.
7. `oauth2 = OAuth2PasswordBearer(tokenUrl="/login")` reads the `Authorization: Bearer ...` header and tells `/docs` where to log in (that's the Authorize button).
8. `current_user()` depends on `oauth2` and `get_db`: token → username → `User` row, or a 401 with the header `WWW-Authenticate: Bearer`.
9. `SignUp` validates input: username 3 to 50 letters/digits/underscores, password 8 to 72 characters, and the `fits_in_bcrypt` validator also checks the 72-**byte** limit (`é` is 2 bytes, an emoji 4).
10. `/signup` refuses a taken username with 409 Conflict and stores only the hash. `/login` reads a **form** (`OAuth2PasswordRequestForm`, the OAuth2 standard) and gives the same error for "no such user" and "wrong password", so attackers can't discover which usernames exist.
11. `/me`, `POST /todos` and `GET /todos` all have `user: User = Depends(current_user)`. `GET /todos` filters with `.where(Todo.owner_id == user.id)`: only YOUR todos.

**`test_main.py`** signs up two users and proves they can't see each other's todos, that wrong passwords and missing tokens get 401, and that bad passwords get a clean 422.

## If something goes wrong
- **`Form data requires "python-multipart" to be installed`** → `pip install -r requirements.txt` (the login form needs it).
- **`401 {"detail":"Not authenticated"}`** → no `Authorization` header was sent. In `/docs`, click **Authorize** first; with curl, check `$TOKEN` isn't empty (`echo $TOKEN`).
- **`401 {"detail":"Invalid or expired token"}`** → the token is older than 30 minutes, was copied with a missing character, or the server's `SECRET_KEY` changed since you logged in. Log in again.
- **`/login` returns 422 when you send JSON** → login takes a **form**, not JSON: `-d "username=sam&password=mypassword1"` with no JSON content type.
- **`column "owner_id" of relation "todos" does not exist`** → you pointed `DATABASE_URL` at the 1.5 Postgres database, which already has a different `todos` table (and `create_all` never changes existing tables). Use the default SQLite file (`app.db`), or a fresh database.

## Try this
1. Change `TOKEN_MINUTES` to 1 in `security.py`, log in, wait a minute, and call `/me` again.
   <details><summary>Hint</summary>

   After about a minute you get `401 Invalid or expired token`. PyJWT checks `exp` automatically in `jwt.decode`. Real apps pair short-lived access tokens with longer "refresh tokens" so users don't have to log in all the time.
   </details>
2. Add `PATCH /todos/{todo_id}` that marks a todo done, but only if it belongs to you (otherwise 404).
   <details><summary>Solution</summary>

   ```python
   @app.patch("/todos/{todo_id}", response_model=TodoOut)
   def finish_todo(todo_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
       todo = db.get(Todo, todo_id)
       if todo is None or todo.owner_id != user.id:
           raise HTTPException(404, "Todo not found")   # 404, not 403: don't reveal it exists
       todo.done = True
       db.commit()
       return TodoOut(id=todo.id, title=todo.title, done=todo.done)
   ```
   </details>
3. Add a `role` column to `User` (`"user"` or `"admin"`) and an admin-only `GET /admin/users` that lists all usernames (403 for everyone else).
   <details><summary>Solution</summary>

   In `User`: `role: Mapped[str] = mapped_column(String(10), default="user")`. Then:
   ```python
   @app.get("/admin/users")
   def list_users(user: User = Depends(current_user), db: Session = Depends(get_db)):
       if user.role != "admin":
           raise HTTPException(403, "Admins only")
       return [u.username for u in db.scalars(select(User)).all()]
   ```
   Delete `app.db` so the table is recreated with the new column. To make yourself admin, open `app.db` (VS Code SQLite Viewer, or `sqlite3 app.db "UPDATE users SET role='admin' WHERE username='sam';"`).
   </details>

## Check yourself
1. Why store a hash instead of the password, and why is bcrypt deliberately slow?
2. Anyone can decode a JWT at jwt.io. Why can't they just change `"sub": "sam"` to `"sub": "admin"`?
3. What's the difference between 401 and 403?
4. Why does `/login` give the same error for an unknown username and a wrong password?

<details><summary>Answers</summary>

1. If the database leaks, attackers get hashes, not passwords, and can't reverse them. Slowness makes guessing (trying millions of common passwords) very expensive.
2. The signature is computed from the payload and `SECRET_KEY`. Change one letter of the payload and the signature no longer matches, so `read_token` rejects it. Only someone with the secret can make a valid token.
3. 401 Unauthorized means "I don't know who you are" (no or bad token). 403 Forbidden means "I know who you are, but you're not allowed".
4. Different errors would let an attacker test which usernames exist, then focus on guessing their passwords.
</details>

## Learn more (optional)
- Hashing vs encryption: https://www.youtube.com/results?search_query=hashing+vs+encryption+explained
- JWT explained: https://www.youtube.com/results?search_query=JWT+json+web+token+explained
- FastAPI security tutorial: https://fastapi.tiangolo.com/tutorial/security/
- OWASP password storage cheat sheet: https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html

## Next
→ [1.7 · Dockerize & deploy to the cloud](../07-dockerize-and-deploy-to-the-cloud)
