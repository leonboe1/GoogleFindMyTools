#
#  GoogleFindMyTools - A set of tools to interact with the Google Find My API
#  Copyright © 2024 Leon Böttger. All rights reserved.
#
"""Fetches the account's FMDN vault keys (every version it currently holds)
via the same internal "batchexecute" RPC the real Find My Device web app
(google.com/android/find) uses, instead of the more limited
accounts.google.com/encryption/unlock/android page KeyBackup/shared_key_flow.py
otherwise talks to - which only ever hands back a single key with no version
tag at all, discovered by comparing a real browser capture of the web app
against what this tool receives. Runs entirely inside an already-authenticated
Selenium session so it rides on that session's own cookies, exactly like the
real web app does - no separate auth of our own needed.
"""

import base64
import json

from selenium.webdriver.support.ui import WebDriverWait

FIND_MY_DEVICE_URL = "https://www.google.com/android/find/?login=&device=1&rs=1"

# window.WIZ_global_data (embedded in the page's own HTML) carries everything
# needed to call its "batchexecute" RPC framework ourselves: FdrFJe is the
# session id (f.sid), cfb2h is the build label (bl), and SNlM0e is the
# anti-CSRF token (at) every POST to it must include.
_FETCH_SCRIPT = """
const callback = arguments[arguments.length - 1];
(async () => {
    try {
        const g = window.WIZ_global_data;
        const params = new URLSearchParams({
            "rpcids": "FAvFKc",
            "source-path": "/android/find/",
            "f.sid": g.FdrFJe,
            "bl": g.cfb2h,
            "hl": "en-GB",
            "_reqid": String(Math.floor(Math.random() * 900000) + 100000),
            "rt": "c",
        });
        const body = new URLSearchParams({
            "f.req": JSON.stringify([[["FAvFKc", "[]", null, "generic"]]]),
            "at": g.SNlM0e,
        });
        const resp = await fetch(
            "https://www.google.com/android/find/_/BoqWebFindMyDeviceUi/data/batchexecute?" + params.toString(),
            {
                method: "POST",
                headers: {"Content-Type": "application/x-www-form-urlencoded;charset=utf-8", "X-Same-Domain": "1"},
                body: body.toString(),
                credentials: "include",
            }
        );
        callback({ok: resp.ok, status: resp.status, text: await resp.text()});
    } catch (e) {
        callback({ok: false, error: String(e)});
    }
})();
"""


def _parse_batchexecute_response(text: str) -> list[dict]:
    """Parses Google's "batchexecute" wire format: an XSSI-protection
    )]}'  prefix, then repeated <declared-length>\\n<json chunk>\\n blocks.
    The declared length is unreliable in practice (observed off by a
    character against the real chunk boundary in a live capture - possibly a
    byte- vs char-counting quirk on Google's end) so it's used only as an
    approximate starting point; json.JSONDecoder.raw_decode() finds the real
    end of the valid JSON from there regardless, then parsing continues right
    after whatever it actually consumed."""
    if text.startswith(")]}'"):
        text = text[4:]
    text = text.lstrip("\n")

    decoder = json.JSONDecoder()
    pos, n = 0, len(text)
    while pos < n:
        newline = text.find("\n", pos)
        if newline == -1 or not text[pos:newline].isdigit():
            break
        chunk_start = newline + 1

        try:
            envelope, consumed = decoder.raw_decode(text, chunk_start)
        except ValueError:
            break
        pos = consumed
        if pos < n and text[pos] == "\n":
            pos += 1

        for item in envelope:
            if isinstance(item, list) and len(item) >= 3 and item[0] == "wrb.fr" and item[1] == "FAvFKc":
                payload = item[2]
                if not payload:
                    return []
                inner = json.loads(payload)
                entries = inner[0][5]
                return [
                    {"key": base64.b64decode(key_b64), "version": version, "domain": domain, "epoch": epoch}
                    for key_b64, version, domain, epoch, *_rest in entries
                ]
    return []


def fetch_vault_keys_via_web_app(driver) -> list[dict]:
    """Returns every {key, version, domain, epoch} entry the account's vault
    currently holds, using the browser session that just completed the
    Google sign-in. Best-effort: returns [] on any failure instead of
    raising, since this is a supplementary data source, not the primary one -
    a failure here should never fail the sign-in flow itself."""
    try:
        driver.get(FIND_MY_DEVICE_URL)
        WebDriverWait(driver, 30).until(
            lambda d: d.execute_script(
                "return !!(window.WIZ_global_data && window.WIZ_global_data.SNlM0e)"
            )
        )

        result = driver.execute_async_script(_FETCH_SCRIPT)
        if not result or not result.get("ok"):
            print(f"[VaultWebApi] Vault key fetch failed: {result}")
            return []

        entries = _parse_batchexecute_response(result["text"])
        print(f"[VaultWebApi] Fetched {len(entries)} vault key(s): "
              f"{[(e['domain'], e['version'], e['epoch']) for e in entries]}")
        return entries
    except Exception as e:
        print(f"[VaultWebApi] Vault key fetch failed (non-fatal): {e}")
        return []
