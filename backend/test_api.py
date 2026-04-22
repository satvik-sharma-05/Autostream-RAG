"""
Quick smoke-test for the AutoStream API.
Run locally:  python test_api.py
Run against Render:  BASE_URL=https://autostream-agent.onrender.com python test_api.py
"""
import sys
import os
import requests

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
PASS = "\033[92m✓\033[0m"
FAIL = "\033[91m✗\033[0m"


def check(label: str, condition: bool, detail: str = ""):
    icon = PASS if condition else FAIL
    print(f"  {icon} {label}" + (f" — {detail}" if detail else ""))
    if not condition:
        sys.exit(1)


print(f"\n🔍 Testing AutoStream API at {BASE_URL}\n")

# ── Health ────────────────────────────────────────────────────────────────────
print("1. Health check")
r = requests.get(f"{BASE_URL}/health", timeout=30)
check("status 200", r.status_code == 200)
check("status=ok", r.json().get("status") == "ok", r.text)

# ── Chat: greeting ────────────────────────────────────────────────────────────
print("\n2. Chat — greeting")
r = requests.post(f"{BASE_URL}/api/v1/chat",
                  json={"message": "hi", "session_id": "smoke-1"}, timeout=30)
check("status 200", r.status_code == 200)
data = r.json()
check("has response", bool(data.get("response")))
check("intent=greeting", data.get("intent") == "greeting", data.get("intent"))
check("lead_captured=false", data.get("lead_captured") is False)

# ── Chat: pricing inquiry ─────────────────────────────────────────────────────
print("\n3. Chat — pricing inquiry (should NOT trigger lead collection)")
r = requests.post(f"{BASE_URL}/api/v1/chat",
                  json={"message": "what are your plans?", "session_id": "smoke-2"}, timeout=30)
check("status 200", r.status_code == 200)
data = r.json()
check("intent=pricing_inquiry", data.get("intent") == "pricing_inquiry", data.get("intent"))
check("lead_captured=false", data.get("lead_captured") is False)
check("mentions pricing", any(w in data.get("response", "").lower() for w in ["pro", "free", "$29", "$0", "plan"]), data["response"][:80])

# ── Chat: high intent → lead collection ──────────────────────────────────────
print("\n4. Chat — high purchase intent → lead collection flow")
sid = "smoke-lead"
r = requests.post(f"{BASE_URL}/api/v1/chat",
                  json={"message": "I want to sign up for Pro", "session_id": sid}, timeout=30)
check("status 200", r.status_code == 200)
data = r.json()
check("intent=high_purchase_intent", data.get("intent") == "high_purchase_intent", data.get("intent"))
check("asks for name", any(w in data["response"].lower() for w in ["name", "call you"]))

r = requests.post(f"{BASE_URL}/api/v1/chat",
                  json={"message": "Satvik Sharma", "session_id": sid}, timeout=30)
check("asks for email", "email" in r.json()["response"].lower())

r = requests.post(f"{BASE_URL}/api/v1/chat",
                  json={"message": "satvik@autostream.ai", "session_id": sid}, timeout=30)
check("asks for platform", "platform" in r.json()["response"].lower())

r = requests.post(f"{BASE_URL}/api/v1/chat",
                  json={"message": "YouTube", "session_id": sid}, timeout=30)
data = r.json()
check("lead_captured=true", data.get("lead_captured") is True, str(data.get("lead_captured")))
check("success message", "captured" in data["response"].lower())

# ── Leads endpoint ────────────────────────────────────────────────────────────
print("\n5. Leads endpoint")
r = requests.get(f"{BASE_URL}/api/v1/leads", timeout=10)
check("status 200", r.status_code == 200)
leads = r.json()
check("at least 1 lead", len(leads) >= 1, f"got {len(leads)}")
check("lead has email", leads[-1].get("email") == "satvik@autostream.ai")

# ── CSV export ────────────────────────────────────────────────────────────────
print("\n6. CSV export")
r = requests.get(f"{BASE_URL}/api/v1/leads/export", timeout=10)
check("status 200", r.status_code == 200)
check("csv content-type", "text/csv" in r.headers.get("content-type", ""))
check("has header row", "name,email" in r.text.lower())

print(f"\n{'='*40}")
print("  All tests passed! 🎉")
print(f"{'='*40}\n")
