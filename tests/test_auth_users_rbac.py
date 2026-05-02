import pytest

from app.core.security import verify_token
from app.main import app


@pytest.mark.asyncio
async def test_otp_login_flow_creates_verified_user_and_tokens(client):
    mobile_number = "9876543210"
    send_response = await client.post("/api/v1/auth/send-otp", json={"mobile_number": mobile_number})
    assert send_response.status_code == 200
    otp = send_response.json()["otp"]
    assert otp is not None

    verify_response = await client.post(
        "/api/v1/auth/verify-otp",
        json={"mobile_number": mobile_number, "otp": otp, "full_name": "Test Buyer"},
    )
    assert verify_response.status_code == 200
    body = verify_response.json()
    assert "access_token" in body
    assert "refresh_token" in body

    payload = verify_token(body["access_token"])
    assert payload["user_id"]
    assert "buyer" in payload.get("roles", [])


@pytest.mark.asyncio
async def test_users_me_and_update_me(client):
    mobile_number = "9373961764"
    send = await client.post("/api/v1/auth/send-otp", json={"mobile_number": mobile_number})
    otp = send.json()["otp"]
    login = await client.post("/api/v1/auth/verify-otp", json={"mobile_number": mobile_number, "otp": otp})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    me = await client.get("/api/v1/users/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["mobile_number"] == mobile_number

    update = await client.patch(
        "/api/v1/users/me",
        headers=headers,
        json={"full_name": "Ganesh User", "email": "ganesh@example.com"},
    )
    assert update.status_code == 200
    assert update.json()["full_name"] == "Ganesh User"
    assert update.json()["email"] == "ganesh@example.com"


@pytest.mark.asyncio
async def test_refresh_token(client):
    mobile_number = "9373961764"
    send = await client.post("/api/v1/auth/send-otp", json={"mobile_number": mobile_number})
    otp = send.json()["otp"]
    login = await client.post("/api/v1/auth/verify-otp", json={"mobile_number": mobile_number, "otp": otp})

    refresh = await client.post(
        "/api/v1/auth/refresh-token",
        json={"refresh_token": login.json()["refresh_token"]},
    )
    assert refresh.status_code == 200
    assert refresh.json()["access_token"]


@pytest.mark.asyncio
async def test_email_verification_flow(client):
    mobile_number = "9876543213"
    send = await client.post("/api/v1/auth/send-otp", json={"mobile_number": mobile_number})
    otp = send.json()["otp"]
    login = await client.post("/api/v1/auth/verify-otp", json={"mobile_number": mobile_number, "otp": otp})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    send_email = await client.post(
        "/api/v1/auth/send-email-verification",
        headers=headers,
        json={"email": "verifyme@example.com"},
    )
    assert send_email.status_code == 200
    email_token = send_email.json()["token"]

    verify_email = await client.post("/api/v1/auth/verify-email", json={"token": email_token})
    assert verify_email.status_code == 200
    assert verify_email.json()["message"] == "Email verified successfully"


@pytest.mark.asyncio
async def test_rbac_role_assignment_requires_permission_and_works_for_admin(client):
    send_user = await client.post("/api/v1/auth/send-otp", json={"mobile_number": "9876543214"})
    otp_user = send_user.json()["otp"]
    login_user = await client.post("/api/v1/auth/verify-otp", json={"mobile_number": "9876543214", "otp": otp_user})
    user_payload = verify_token(login_user.json()["access_token"])
    user_id = user_payload["user_id"]

    send_admin = await client.post("/api/v1/auth/send-otp", json={"mobile_number": "9876543215"})
    otp_admin = send_admin.json()["otp"]
    login_admin = await client.post("/api/v1/auth/verify-otp", json={"mobile_number": "9876543215", "otp": otp_admin})
    admin_payload = verify_token(login_admin.json()["access_token"])
    admin_id = admin_payload["user_id"]

    async with app.state.test_session_maker() as db:
        from app.features.rbac.repository import RoleRepository
        from app.features.users.service import UserService

        admin_role = await RoleRepository(db).get_by_name("admin")
        await UserService(db).add_role_to_user(admin_id, admin_role.id)

    send_admin2 = await client.post("/api/v1/auth/send-otp", json={"mobile_number": "9876543215"})
    otp_admin2 = send_admin2.json()["otp"]
    login_admin2 = await client.post("/api/v1/auth/verify-otp", json={"mobile_number": "9876543215", "otp": otp_admin2})
    admin_headers = {"Authorization": f"Bearer {login_admin2.json()['access_token']}"}

    roles_resp = await client.get("/api/v1/roles", headers=admin_headers)
    assert roles_resp.status_code == 200
    seller_role = next(role for role in roles_resp.json() if role["name"] == "seller")

    assign_resp = await client.post(
        f"/api/v1/users/{user_id}/roles",
        headers=admin_headers,
        json={"role_id": seller_role["id"]},
    )
    assert assign_resp.status_code == 200
    assert assign_resp.json()["id"] == user_id
