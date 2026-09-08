from onboarding_service import CommunityOnboarding


class StubClient:
    def verify_captcha(self, token):
        return {"ok": True, "data": {}}

    def create_user(self, email, password, name, invite_code):
        return {"ok": True, "data": {"user_id": "user-1"}}

    def create_session(self, user_id):
        return {"ok": True, "data": {"session_id": "session-1"}}


def test_invite_gate_and_order_update():
    service = CommunityOnboarding(StubClient(), {"SPRING-42"})
    rejected = service.signup("a@example.com", "pw", "A", "NOPE", "captcha")
    assert rejected == {"accepted": False, "reason": "invite_code_required"}
    accepted = service.signup("a@example.com", "pw", "A", "SPRING-42", "captcha")
    assert accepted["accepted"] is True
    service.place_order("order-1", "a@example.com", ["tea"])
    assert service.fulfill("order-1").status == "fulfilled"
    assert service.receipt("order-1")["status"] == "fulfilled"
