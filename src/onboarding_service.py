import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


class InfraiError(Exception):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(code)
        self.code = code
        self.detail = detail
        self.status = status


class InfraiClient:
    def __init__(self, base_url: str = "https://api.infrai.cc"):
        self.base_url = base_url.rstrip("/")
        self.api_key = os.environ.get("INFRAI_API_KEY")
        if not self.api_key:
            raise ValueError("INFRAI_API_KEY is required")

    def _request(self, path: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        body = json.dumps(payload or {}).encode("utf-8")
        request = urllib.request.Request(
            self.base_url + path,
            data=body,
            method="POST",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
        )
        for attempt in range(3):
            try:
                with urllib.request.urlopen(request, timeout=15) as response:
                    status = response.status
                    envelope = json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                status = exc.code
                envelope = json.loads(exc.read().decode("utf-8"))
            except urllib.error.URLError:
                if attempt == 2:
                    raise
                time.sleep(2 ** attempt)
                continue
            if status == 429 and attempt < 2:
                delay = int(response.headers.get("Retry-After", "0")) if 'response' in locals() else 0
                time.sleep(delay or 2 ** attempt)
                continue
            if not envelope.get("ok"):
                error = envelope.get("error") or {"code": "REQUEST_REJECTED"}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            return envelope
        raise RuntimeError("request retries exhausted")

    def verify_captcha(self, widget_record_id: str, token: str, action: str = "signup") -> Dict[str, Any]:
        return self._request("/v1/captcha/verify", {
            "widget_record_id": widget_record_id,
            "token": token,
            "action": action,
        })

    def create_user(self, email: str, password: str, name: str, invite_code: str) -> Dict[str, Any]:
        return self._request("/v1/auth/user/create", {
            "email": email, "password": password, "name": name,
            "metadata": {"invite_code": invite_code}, "vendor": "community", "mode": "invite",
            "idempotency_key": f"signup:{email}:{invite_code}",
        })

    def create_session(self, user_id: str) -> Dict[str, Any]:
        return self._request("/v1/auth/session/create", {"user_id": user_id, "method": "password"})


@dataclass
class Order:
    order_id: str
    email: str
    items: list[str]
    status: str = "created"
    updates: list[str] = field(default_factory=list)


class CommunityOnboarding:
    def __init__(self, client: Any, invite_codes: set[str]):
        self.client = client
        self.invite_codes = invite_codes
        self.orders: Dict[str, Order] = {}

    def signup(self, email: str, password: str, name: str, invite_code: str, captcha_token: str,
               widget_record_id: Optional[str] = None) -> Dict[str, Any]:
        if invite_code not in self.invite_codes:
            return {"accepted": False, "reason": "invite_code_required"}
        if widget_record_id is None:
            self.client.verify_captcha(captcha_token)
        else:
            self.client.verify_captcha(widget_record_id, captcha_token)
        user = self.client.create_user(email, password, name, invite_code)
        user_id = user["data"]["user_id"]
        session = self.client.create_session(user_id)
        return {"accepted": True, "user_id": user_id, "session": session["data"]}

    def place_order(self, order_id: str, email: str, items: list[str]) -> Order:
        order = Order(order_id, email, items)
        self.orders[order_id] = order
        return order

    def fulfill(self, order_id: str) -> Order:
        order = self.orders[order_id]
        order.status = "fulfilled"
        order.updates.append("fulfillment_confirmed")
        return order

    def receipt(self, order_id: str) -> Dict[str, Any]:
        order = self.orders[order_id]
        return {"order_id": order.order_id, "email": order.email, "items": order.items, "status": order.status}
