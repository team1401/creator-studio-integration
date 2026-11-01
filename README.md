# Creator Studio → Agent Zero adapter contract

## Verified outcome (2026-10-22 UTC)

One real authenticated job on **agent-zero-1**, context `OzIMaV93`, created:

`/a0/usr/workdir/creator-studio-integration-3bc3bbfd92064f469a9fa132798e52b6/integration-verified.txt`

Independent read-only SSH/container filesystem verification found **21 bytes**, exactly `integration verified\n`, SHA-256 `199dbe21722d2212d545a289a97402a81ec993f2e28e8f16c4d7fe9037e63fef`. The agent trace contains one code-execution tool action and a final response returning the same path. Completion is established by the file check plus `running=false`, not by that response alone. The dedicated context ended idle/unpaused. Five preexisting contexts' IDs, running/paused flags and creation times matched before/after. Instance2 received no authenticated API calls or jobs.

Initial polling suffered a 20-second transport timeout; cleanup paused only our context. A bounded continuation resumed the **same** job, without duplicate dispatch. The first filesystem probe used unavailable `python`; corrected to installed `python3`. Both failed attempts are retained. This is a successful recovered integration test, **not a clean uninterrupted run or production reliability proof**.

## Server-side contract

`a0_client.py` uses installed v2.14's supported Web UI API handlers (not secret-prefix A2A URLs):

| Operation | Request | Meaning |
|---|---|---|
| Authenticate | `POST /login`, form username/password | Obtain a new application session from vault credentials; no browser-cookie extraction |
| CSRF | `GET /api/csrf_token` | Keep `token` only in memory; send `X-CSRF-Token` and matching Origin |
| Create | `POST /api/chat_create`, `{"project_name":""}` | Fresh dedicated context; no project inheritance |
| Send | `POST /api/message_async`, context/text/message_id | Acknowledgement only; never mark completed here |
| Poll | `POST /api/poll`, context/log_from/notifications_from | Inspect selected context running/paused, logs; do not forward unrelated contexts/tasks/notifications to clients |
| Pause | `POST /api/pause`, context, paused=true | Only contexts owned by this adapter |
| Resume | Same endpoint, paused=false | Only contexts owned by this adapter |

The adapter permits only worker1's exact URL, disables ambient proxy configuration, prohibits automatic redirects, uses connect/read timeouts, and logs only route/method/status/timing. API budget defaults to 70 requests. Each test continuation has its own explicit budget and 180-second poll deadline. Model prompt requested at most two tool actions; the trace shows one code action. **The prompt's action limit and isolated path are not a security sandbox or enforced tool quota.** Agent Zero retains container-level tool capabilities and automatic memory persistence; do not claim all framework writes were confined to the task directory.

`owned` is deliberately process-local. Production recovery must reconstruct ownership from a separate Creator Studio SQLite job mapping, not accept a browser-supplied context ID or arbitrary reassignment. The continuation harness loads only this test's exact recorded context; it is not an app endpoint. No app-child files or databases were modified. No global task-board migration, Helix/Argus/Discord task dispatch, or peer request occurred.

Do not automatically retry `message_async` after a timeout: acknowledgement uncertainty can duplicate work. `message_id` is correlation, **not proven idempotency**. Poll first and require operator review when delivery is uncertain. Pause is a cooperative context flag; it is not proof an in-flight subprocess has stopped. No global pause exists in this adapter.

## UI and desktop readiness

- **Open worker:** `http://100.108.186.69:50080/` verified authenticated HTTP200; anonymous302 to login.
- Worker2 `http://100.108.186.69:50081/` responds anonymous302; its authentication was not tested in this task.
- Desktop software status says healthy, but actual read-only desktop state says **Can't open display :120**, zero windows/geometry. Existing desktop route returns authenticated307, anonymous401. No desktop was started or changed. **There is no currently verified usable direct desktop link.** Do not display a green “desktop connected” indicator or invent an iframe URL. Prior pilot desktop success is historical, not current availability.

Recommend **Open worker** plus **Copy task / manual handoff** now. An “Open worker desktop” control should currently open the worker UI with an explicit manual Desktop/start instruction, not promise a connected desktop. Supervised Send/Poll/Pause/Resume is prototype-proven; keep unattended automatic dispatch off until durable ownership, authorization, per-job budgets, artifact policies, uncertain-delivery recovery, and tool isolation are implemented. Argus = **not connected**; no readable live proof was established.

## Secrets and deployment

Credentials retrieved from the existing shared Bitwarden item through the established authorized Mac Keychain flow; master password, vault session, app credentials, cookies, and CSRF stayed in subprocess/process memory. No new credentials/SSO, browser auth extraction, secret-prefix links, environment changes, model/settings changes, restart, or cloud operations. The credential helper is an operator verification harness, not a production secret service; do not ship its historical session lookup inside the child app. Inject an approved server-only vault resolver at deployment. Tailnet HTTP relies on Tailscale transport, not application HTTPS. Keep endpoint access tailnet-scoped.

Live Strix v2.14 matches the reviewed API semantics. Current model preset is Halogen via lm_studio, vision=true, temperature=0, enable_thinking=false; local embeddings remain configured. Both A0 containers are native Docker Manager-managed, unprivileged, with separate usr/browser bind mounts and Tailscale-only50080/50081 bindings. `.env` on worker1 is mode600. Current start times are **2026-10-21 21:49:26 UTC**, newer than the historical tuning report—do not repeat its no-restart-since15:56 claim as current truth. Native templates exist. Docker filesystem reports80G total,31G used,50G available. Candidate TCP50082 was not listening at observation time; **not reserved**, recheck before deployment. Use a new native editable Unraid template and a separate persistent child-app SQLite/appdata path; no deployment was performed here.

## Evidence and tests

- `integration-capabilities.json`: consumable capability flags/verified links.
- `live-verification.json`: original attempt and failure, secret-free API audit.
- `continuation-first-failure.json`: first filesystem probe failure.
- `continuation-verification.json`: independent artifact result and preserved-context comparison.
- `dedicated-trace.json`: only this new job's trace; never full unrelated poll payload.
- `desktop-status.json`, `desktop-state.json`, `link-verification.json`: distinguish installed desktop from usable desktop.
- `deployment-facts.json`: allowlisted Docker/native/ports/source evidence, no environment credentials.
- `test_client.py`: six passing local safety tests; live test is separate, not mocked.

Run safety tests with `python -m unittest discover -s creator-studio-integration -p test_client.py -v` from the workspace. **Do not casually rerun `verify_live.py`: it creates another live job.**

Canonical Obsidian was not edited. This report is the pending project note for the parent to apply through the authorized canonical-vault workflow.
