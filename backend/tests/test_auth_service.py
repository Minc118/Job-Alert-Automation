from __future__ import annotations

from dataclasses import dataclass

from api.services import auth_service


@dataclass(frozen=True)
class FakeSigningKey:
    key: str = "public-key"


def test_neon_auth_verification_keeps_unconfigured_audience_optional(monkeypatch) -> None:
    decode_calls: list[dict[str, object]] = []

    class FakeJWKClient:
        def __init__(self, jwks_url: str) -> None:
            assert jwks_url == "https://auth.example.test/jwks"

        def get_signing_key_from_jwt(self, token: str) -> FakeSigningKey:
            assert token == "signed-token"
            return FakeSigningKey()

    def fake_decode(token: str, key: str, **kwargs):
        decode_calls.append({"token": token, "key": key, **kwargs})
        return {"sub": "auth-subject", "aud": "authenticated", "email": "user@example.test"}

    monkeypatch.setattr(auth_service, "require_neon_auth_jwks_url", lambda: "https://auth.example.test/jwks")
    monkeypatch.setattr(auth_service.jwt, "get_unverified_header", lambda _token: {"alg": "RS256"})
    monkeypatch.setattr(auth_service, "PyJWKClient", FakeJWKClient)
    monkeypatch.setattr(auth_service.jwt, "decode", fake_decode)
    auth_service._jwks_client.cache_clear()

    identity = auth_service.verify_neon_auth_jwt("signed-token")

    assert identity.subject == "auth-subject"
    assert decode_calls == [
        {
            "token": "signed-token",
            "key": "public-key",
            "algorithms": ["RS256"],
            "options": {"verify_aud": False},
        }
    ]


def test_neon_auth_verification_reuses_jwks_client(monkeypatch) -> None:
    created_clients: list[str] = []

    class FakeJWKClient:
        def __init__(self, jwks_url: str) -> None:
            created_clients.append(jwks_url)

        def get_signing_key_from_jwt(self, _token: str) -> FakeSigningKey:
            return FakeSigningKey()

    monkeypatch.setattr(auth_service, "require_neon_auth_jwks_url", lambda: "https://auth.example.test/jwks")
    monkeypatch.setattr(auth_service.jwt, "get_unverified_header", lambda _token: {"alg": "RS256"})
    monkeypatch.setattr(auth_service, "PyJWKClient", FakeJWKClient)
    monkeypatch.setattr(auth_service.jwt, "decode", lambda *_args, **_kwargs: {"sub": "auth-subject"})
    auth_service._jwks_client.cache_clear()

    auth_service.verify_neon_auth_jwt("first-token")
    auth_service.verify_neon_auth_jwt("second-token")

    assert created_clients == ["https://auth.example.test/jwks"]
