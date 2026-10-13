# 1.6 · Login API: hashed passwords + JWT tokens

**What you build:** sign up, log in, receive a **token**, and use it to reach your **private** to-do list. Other users can't see your todos.
**Like you're 10:**
- **Hashing** is a one-way blender. You can turn a strawberry into a smoothie but never back. We store the smoothie (hash), never the strawberry (password). At login we blend what you typed and compare smoothies.
- **A JWT token** is a wristband at a theme park. You show your ticket once at the gate (login) and get a wristband. Rides (protected routes) check the wristband, not your ticket. Wristbands expire (30 minutes here).

## Run it
```bash
cd level-1-apis/06-login-api-hashed-passwords-and-jwt
pip install -r requirements.txt
uvicorn main:app --reload
```
In http://127.0.0.1:8000/docs:
1. `POST /signup` with `{"username": "sam", "password": "mypassword1"}`
2. Click the green **Authorize 🔒** button, type `sam` / `mypassword1`, click Authorize. (It calls `/login` for you.)
3. `GET /me` now works. `POST /todos`, then `GET /todos`.
4. Sign up a second user, authorize as them, and notice they can't see sam's todos.

With curl:
```bash
curl -X POST localhost:8000/signup -H "Content-Type: application/json" -d '{"username":"sam","password":"mypassword1"}'
TOKEN=$(curl -s -X POST localhost:8000/login -d "username=sam&password=mypassword1" | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")
curl localhost:8000/me -H "Authorization: Bearer $TOKEN"
```
Paste your token into https://jwt.io to see what's inside. It's readable but can't be forged.

Test: `pytest -v`

## Key ideas
- **401 Unauthorized** = "who are you?" (no or bad token). **403 Forbidden** = "I know you, but you're not allowed".
- `Depends(current_user)` is a **guard**: add it to any route to make it require login.
- Never log or return passwords. Never commit `SECRET_KEY`. Use environment variables.
- The same "Bearer token" pattern is how you'll send your **LLM API key** in Level 7.

## Your turn
1. Add `PATCH /todos/{id}` that only works if the todo belongs to you (else 404).
2. Add a `role` column (`user`/`admin`) and an admin-only route that lists all users (return 403 for non-admins).
3. Change `TOKEN_MINUTES` to 1, log in, wait a minute, and watch the token expire.

## Watch
- Hashing vs encryption: https://www.youtube.com/results?search_query=hashing+vs+encryption+explained
- JWT explained: https://www.youtube.com/results?search_query=JWT+json+web+token+explained
- FastAPI security tutorial: https://fastapi.tiangolo.com/tutorial/security/
