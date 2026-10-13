"""One-off live E2E test: login, pick a notebook, hit every AI endpoint with timing."""
import sys
import time

import httpx

BASE = "http://localhost:8000/api"

client = httpx.Client(timeout=200)

# 1. Login
r = client.post(f"{BASE}/auth/login", json={"email": "test@example.com", "password": "password123"})
assert r.status_code == 200, r.text
token = r.json()["data"]["access_token"]
H = {"Authorization": f"Bearer {token}"}
print("login OK")

# 2. Pick first notebook
r = client.get(f"{BASE}/notebooks", headers=H)
assert r.status_code == 200, r.text
notebooks = r.json()["data"]["notebooks"]
if not notebooks:
    sys.exit("no notebooks available - create one in the UI first")
nb = notebooks[0]
nb_id = nb["id"]
print(f"notebook: {nb['title']} ({nb_id})")

# 3. List resources
r = client.get(f"{BASE}/notebooks/{nb_id}/resources", headers=H)
assert r.status_code == 200, r.text
resources = r.json()["data"]["resources"]
if not resources:
    sys.exit("notebook has no resources")
ids = [x["id"] for x in resources]
print(f"resources: {[x['name'] for x in resources]}")

results = []


def timed(name, fn):
    t0 = time.time()
    try:
        status, detail = fn()
    except Exception as exc:  # noqa: BLE001
        status, detail = "EXC", f"{type(exc).__name__}: {exc}"
    dt = time.time() - t0
    ok = status == 200
    results.append((name, ok, dt, detail))
    print(f"{'PASS' if ok else 'FAIL':4s} {name:12s} {dt:7.1f}s  {detail}")


def post(path, payload):
    def run():
        resp = client.post(path, json=payload, headers=H)
        body = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
        detail = body.get("message") or str(body)[:150]
        if resp.status_code == 200:
            data = body.get("data") or {}
            gc = data.get("generated_content")
            if gc:
                detail = f"{gc.get('type')} saved, keys={list((gc.get('content') or {}).keys())[:4]}"
        return resp.status_code, detail
    return run


# 4. Chat
timed("chat", post(f"{BASE}/chat", {
    "notebook_id": nb_id,
    "message": "In 2-3 sentences, what is the main topic of my sources?",
    "resource_ids": ids,
}))

# 5. All five generators
timed("summary", post(f"{BASE}/ai/summary", {"notebook_id": nb_id, "resource_ids": ids}))
timed("quiz", post(f"{BASE}/ai/quiz", {"notebook_id": nb_id, "resource_ids": ids, "number_of_questions": 5}))
timed("flashcards", post(f"{BASE}/ai/flashcards", {"notebook_id": nb_id, "resource_ids": ids, "number_of_cards": 5}))
timed("faq", post(f"{BASE}/ai/faq", {"notebook_id": nb_id, "resource_ids": ids}))
timed("study-notes", post(f"{BASE}/ai/study-notes", {"notebook_id": nb_id, "resource_ids": ids}))

# 6. Prompt studio execute
def prompt_flow():
    r1 = client.post(f"{BASE}/prompts", headers=H, json={
        "title": "live-test", "prompt": "Explain photosynthesis in one sentence.",
        "model": "fast", "temperature": 0.7, "max_output_tokens": 200,
    })
    assert r1.status_code == 200, r1.text
    pid = r1.json()["data"]["prompt"]["id"]
    r2 = client.post(f"{BASE}/prompts/{pid}/execute", headers=H, json={})
    assert r2.status_code == 200, r2.text
    resp_text = r2.json()["data"]["prompt"]["response"]
    client.delete(f"{BASE}/prompts/{pid}", headers=H)
    return 200, f"prompt response: {resp_text[:60]!r}"


timed("prompt-exec", prompt_flow)

print("\n=== SUMMARY ===")
fails = [x for x in results if not x[1]]
for name, ok, dt, _ in results:
    print(f"{name:12s} {'OK  ' if ok else 'FAIL'} {dt:6.1f}s")
print(f"\n{len(results) - len(fails)}/{len(results)} passed")
sys.exit(1 if fails else 0)
