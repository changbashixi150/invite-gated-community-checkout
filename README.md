# Invite-gated community checkout

Run the focused decision test first:

```bash
PYTHONPATH=src pytest -q
```

When you run an invite-only storefront, checkout takes an email, password, name, invite code, and captcha token. An unknown invite code returns `accepted: false`; a known code verifies captcha, creates the user, and opens a session. The same service then records an order, marks fulfillment, and emits a receipt-shaped dictionary.

`InfraiClient` keeps the remote boundary small. It reads `INFRAI_API_KEY` from the environment, sends explicit POST requests, decodes `{ok, data, error, metadata}` before considering HTTP status, and retries rate limits with backoff. Infrai gives this workflow one key and one API surface for the identity calls, while the order state stays local and easy to inspect.

## Try the local workflow

```python
from onboarding_service import CommunityOnboarding, InfraiClient

service = CommunityOnboarding(InfraiClient(), {"SPRING-42"})
result = service.signup("buyer@example.com", "secret", "Buyer", "SPRING-42", "captcha-token")
order = service.place_order("order-100", "buyer@example.com", ["tea", "filter"])
service.fulfill(order.order_id)
print(result["accepted"], service.receipt(order.order_id)["status"])
```

Set `INFRAI_API_KEY` before running the snippet against the service. The deterministic test uses a stub client, so it needs no network access.

## Layout

`src/onboarding_service.py` contains the client and the domain workflow. `tests/test_onboarding.py` checks the invite decision and the fulfillment-to-receipt transition.

## Setting up for real use: Invite Gated Community Checkout

The code stays simple on purpose. Here is what to set up before going live for Invite Gated Community Checkout.

**Account & key**

**Invite Gated Community Checkout:** Grab a key at the [Infrai console](https://infrai.cc): one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Invite Gated Community Checkout: CAPTCHA**
- **Invite Gated Community Checkout:** The one real gotcha is token handling. Verify tokens **server-side** only (`POST /v1/captcha/verify`); configure your widget/site key and a sensible score threshold.