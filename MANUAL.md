# MANUAL.md — Running GoogleFindMyTools via Docker

Docker wrapper around [GoogleFindMyTools](https://github.com/leonboe1/GoogleFindMyTools). Handles Chrome + Python deps inside a container; exposes the one-time Google login through a browser-based VNC viewer since the tool needs a real Chrome GUI session to authenticate (not a simple token/link flow).

**Status:** verified end-to-end — real Google login through noVNC, `oauth_token` captured, `main.py` lists devices.

## Prerequisites

- Docker + Docker Compose installed on host.
- Nothing else — no local Python, no local Chrome needed.

## First run (Google login required)

1. From the repo directory:
   ```bash
   cd /home/sandor/claude/googlefindmy/GoogleFindMyTools
   docker compose up
   ```
   Run in the **foreground** (no `-d`) — the script asks for keyboard input.

2. Wait for this line in the terminal:
   ```
   [AuthFlow] Press Enter to continue...
   ```
   Press **Enter**.

3. Open **http://localhost:7900** in your normal browser. Password: `secret`.
   You'll see a live view of Chrome running inside the container.

4. In that noVNC window, log into your Google account as you normally would (2FA etc. all work same as any browser).

5. Once login completes, the terminal will print `[AuthFlow] Retrieved Account Token successfully.` and continue — `main.py` proceeds to list your Find My Device trackers/Android devices.

6. Your session is cached to `data/secrets.json` on the host. You will not need to repeat the browser login on future runs unless that file is deleted or Google invalidates the session.

## Normal (already authenticated) runs

```bash
docker compose up
```
Same command — if `data/secrets.json` already has valid tokens, it skips straight to listing devices; no browser step needed. You can ignore the noVNC link at that point.

## Using the tool once it's running

`main.py` is interactive:
- Type a device number + Enter → prints/decrypts that device's last known location.
- Type `r` + Enter → register a new ESP32/Zephyr-based tracker (follow on-screen instructions).
- `Ctrl+C` to quit.

## Stopping

```bash
docker compose down
```
Stops and removes the container. `data/secrets.json` (your login) survives since it's a host-mounted file, not inside the container.

## Rebuilding after a repo/code update

```bash
git pull
docker compose build
docker compose up
```

## Files in this setup

| File | Purpose |
|---|---|
| `Dockerfile` | Builds the app image on top of `selenium/standalone-chrome` (bundles Chrome + virtual display + noVNC). |
| `docker-entrypoint.sh` | Starts the virtual display stack, then runs `python3 main.py` in the foreground. |
| `docker-compose.yml` | One-command build+run: opens stdin/tty, publishes noVNC port 7900, mounts `data/secrets.json`. |
| `data/secrets.json` | Your cached Google auth tokens. Gitignored — never commit this file. Delete it to force a fresh login. |

## Troubleshooting

- **Stuck with no prompt / can't type anything:** you probably ran with `docker compose up -d` (detached). Run it in the foreground instead.
- **noVNC page won't load:** give the container a few seconds to boot; check `docker compose logs` for `[entrypoint] Display ready.`
- **Forgot the noVNC password:** it's `secret` — a fixed default from the base image, not something this setup configures.
- **Want a completely fresh login:** stop the container, delete `data/secrets.json`, recreate it as an empty JSON file (`echo '{}' > data/secrets.json`), then `docker compose up` again.
- **Permission errors writing `secrets.json`:** make sure `data/secrets.json` exists on the host *before* starting the container and is writable (`chmod 666 data/secrets.json`) — Docker will otherwise create it as a directory or with mismatched ownership.

## Known limitation

The Google login step itself must be done by a human through the noVNC browser window — there's no way to script or automate that part (nor should there be, since it's your real Google account credentials).

## Fixes baked into this image

- **Home dir ownership:** the base `selenium/standalone-chrome` image leaves `/home/seluser/.local` owned by `root`, which broke `undetected_chromedriver`'s cache dir (`PermissionError`). `Dockerfile` chowns `/home/seluser` to `seluser` at build time.
- **ChromeDriver/Chrome version mismatch:** `undetected_chromedriver`'s `version_main=None` auto-detection didn't reliably match the image's bundled Chrome, so it fetched the latest chromedriver instead of the one matching the installed Chrome (`SessionNotCreatedException`). `chrome_driver.py` now reads the installed Chrome's version via `google-chrome --version` and pins `version_main` explicitly.
