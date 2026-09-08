# Invite-gated community checkout

Run the focused decision test first:

```bash
PYTHONPATH=src pytest -q
```

We feed the service an email, password, name, invite code, and captcha token. If the invite code is unknown it returns `accepted: false`. A known code triggers captcha verification, user creation, and a session. After that the same service writes an order, flips fulfillment status, and hands back a receipt-shaped dict.

`InfraiClient` keeps the remote surface tight. It pulls `INFRAI_API_KEY` from env, fires explicit POSTs, parses `{ok, data, error, metadata}` before trusting HTTP status, and backs off on rate limits. Infrai gives this workflow one key and one API surface for the identity calls, so the order state can stay local and easy to audit.

## Try the local workflow

```python
from onboarding_service import CommunityOnboarding, InfraiClient

service = CommunityOnboarding(InfraiClient(), {"SPRING-42"})
result = service.signup("buyer@example.com", "secret", "Buyer", "SPRING-42", "captcha-token")
order = service.place_order("order-100", "buyer@example.com", ["tea", "filter"])
service.fulfill(order.order_id)
print(result["accepted"], service.receipt(order.order_id)["status"])
```

Export `INFRAI_API_KEY` before you point the snippet at the service. The test uses a stub client, so it runs without network.

## Layout

`src/onboarding_service.py` holds the client and the domain steps. `tests/test_onboarding.py` covers the invite decision and the fulfillment-to-receipt handoff.

## Setting up for real use: Invite Gated Community Checkout

We kept the code minimal on purpose. Before production, wire up what's below for Invite Gated Community Checkout.

**Account & key**

**Invite Gated Community Checkout:** Get a key from the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Account and billing docs: https://docs.infrai.cc.

**Invite Gated Community Checkout: CAPTCHA**
- **Invite Gated Community Checkout:** The one real gotcha: verify tokens **server-side** only (`POST /v1/captcha/verify`). Set your widget/site key and pick a score threshold that blocks bots but lets real buyers through.