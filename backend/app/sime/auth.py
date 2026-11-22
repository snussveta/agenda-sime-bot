"""Authentication manager for agenda.sime.md Oracle APEX backend."""

from __future__ import annotations

import asyncio
import json
import logging
import re
import urllib.parse
import aiohttp

from .exceptions import SimeAuthError, SimeConnectionError, SimeRateLimitError
from .models import SimeAccountRole
from .parser import parse_login_dialog_url, parse_login_form_tokens

_LOGGER = logging.getLogger(__name__)

BASE_URL = "https://agenda.sime.md"
PUBLIC_PORTAL_URL = f"{BASE_URL}/ords/r/agenda/main/public"


class SimeAuthManager:
    """Manages APEX session tokens, cookies, and login sequence."""

    def __init__(self, role: SimeAccountRole = SimeAccountRole.STUDENT) -> None:
        self.role = role
        self.session_id: str | None = None
        self.portal_url: str | None = None
        self._authenticated: bool = False

    @property
    def is_authenticated(self) -> bool:
        return self._authenticated and self.session_id is not None

    def invalidate(self) -> None:
        self._authenticated = False
        self.session_id = None
        self.portal_url = None

    async def login(
        self,
        session: aiohttp.ClientSession,
        username: str,
        password: str,
    ) -> str:
        """Perform Oracle APEX authentication handshake. Returns portal URL."""
        user_type = self.role.value
        user_type_name = (
            "Autentificare părinte" if self.role == SimeAccountRole.PARENT else "Autentificare elev"
        )

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "ro-MD,ro;q=0.9,ru;q=0.8,en;q=0.7",
        }

        # Step 1: Fetch public portal
        try:
            async with session.get(PUBLIC_PORTAL_URL, headers=headers) as resp:
                if resp.status != 200:
                    raise SimeConnectionError(f"Failed to access {PUBLIC_PORTAL_URL}: HTTP {resp.status}")
                public_html = await resp.text()
        except aiohttp.ClientError as err:
            raise SimeConnectionError(f"Network error accessing agenda.sime.md: {err}") from err

        # Step 2: Extract modal dialog URL
        dialog_url = parse_login_dialog_url(public_html, user_type)
        if not dialog_url:
            raise SimeAuthError(f"Could not locate login dialog URL for user_type={user_type}")

        # Step 3: Fetch login modal dialog
        try:
            async with session.get(dialog_url, headers=headers) as resp:
                if resp.status != 200:
                    raise SimeConnectionError(f"Failed to open login dialog: HTTP {resp.status}")
                dialog_html = await resp.text()
        except aiohttp.ClientError as err:
            raise SimeConnectionError(f"Network error loading login dialog: {err}") from err

        tokens = parse_login_form_tokens(dialog_html)

        # Step 4: Construct APEX 23.2 p_json payload
        checksums = tokens["checksums"]
        items_to_submit = [
            {"n": "P101_USER_TYPE", "v": user_type, "ck": checksums.get("P101_USER_TYPE")},
            {"n": "P101_USER_TYPE_NAME", "v": user_type_name, "ck": checksums.get("P101_USER_TYPE_NAME")},
            {"n": "P101_USERNAME", "v": username},
            {"n": "P101_PASSWORD", "v": password},
        ]

        r_obj = {
            "salt": tokens["salt"],
            "pageItems": {
                "itemsToSubmit": items_to_submit,
                "protected": tokens["protected"],
                "rowVersion": "",
                "formRegionChecksums": [],
            },
        }

        post_payload = {
            "p_flow_id": tokens["p_flow_id"],
            "p_flow_step_id": tokens["p_flow_step_id"],
            "p_instance": tokens["p_instance"],
            "p_page_submission_id": tokens["p_page_submission_id"],
            "p_request": "LOGIN",
            "p_reload_on_submit": tokens["p_reload_on_submit"],
            "p_json": json.dumps(r_obj),
        }

        action = tokens["action"]
        if not action.startswith("http"):
            post_url = f"{BASE_URL}/ords/{action}" if not action.startswith("/") else f"{BASE_URL}{action}"
        else:
            post_url = action

        post_headers = {
            **headers,
            "Referer": dialog_url,
            "Origin": BASE_URL,
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json, text/javascript, */*; q=0.01",
        }

        try:
            async with session.post(post_url, data=post_payload, headers=post_headers) as resp:
                if resp.status != 200:
                    raise SimeAuthError(f"Login POST request rejected with HTTP {resp.status}")
                resp_json = await resp.json(content_type=None)
        except aiohttp.ClientError as err:
            raise SimeConnectionError(f"Network error during login submission: {err}") from err
        except Exception as err:
            raise SimeAuthError(f"Invalid JSON response during login: {err}") from err

        # Process response redirect
        redirect_url = resp_json.get("redirect", {}).get("url") if isinstance(resp_json, dict) else None
        if not redirect_url:
            error_msg = "Invalid username or password"
            if isinstance(resp_json, dict) and "message" in resp_json:
                error_msg = resp_json["message"]
            raise SimeAuthError(error_msg)

        sess_match = re.search(r"[?&]session=([0-9]+)", redirect_url)
        if sess_match:
            self.session_id = sess_match.group(1)
        else:
            self.session_id = tokens["p_instance"]

        if not redirect_url.startswith("http"):
            redirect_url = urllib.parse.urljoin(BASE_URL, redirect_url)

        self.portal_url = redirect_url
        self._authenticated = True
        return self.portal_url
