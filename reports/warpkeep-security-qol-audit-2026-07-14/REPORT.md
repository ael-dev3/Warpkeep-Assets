# Warpkeep Security and Quality-of-Life Audit

**Audit date:** 14 July 2026  
**Mode:** Read-only and non-destructive  
**Status:** Complete  

## Executive verdict

No Critical or High security vulnerability was confirmed. No evidence was found of compromise, exposed production secrets, unauthorized database access, authentication bypass, account takeover, vulnerable installed dependencies, or corrupted release assets.

The audit confirmed:

- one Moderate browser-security defect: the production frontend is cross-origin frameable;
- two Moderate operational risks: incomplete deployment provenance and absent repository-defined production monitoring/synthetics;
- one Low supply-chain weakness: the asset archive's default branch is unprotected;
- a substantial mobile entry-performance problem and several responsive-layout/entry-discoverability issues.

No production state, authentication challenge, player, FID, castle, allowlist, deployment, repository, or account setting was changed.

## Exact audited scope

- Production frontend: `https://warpkeep.com`
- Production auth bridge: `https://auth.warpkeep.com`
- Production SpacetimeDB schema and privacy-safe protected aggregate
- Runtime repository: `ael-dev3/Warpkeep`
- Provenance/source-asset repository: `ael-dev3/Warpkeep-Assets`
- GitHub Pages, Actions, branch protection, CodeQL, releases, dependencies, SBOM, DNS/TLS, public assets and deployment records

### Frozen coordinates

- Warpkeep repository and live Pages SHA: `f3fb6ed031a84c6a1703bd438d9553bd00bacd33`
- Auth Worker v21: `856862c0-6700-4310-bb98-61567ebc69ef`
- Auth Worker source SHA: `e56d74768da3e47a3d56cbfb5e0f2e2ed51032cf`
- Warpkeep-Assets SHA: `23795ce671fa2c7c98e188887b7a444a194a8a1e`
- Backend protocol: `2`
- Protected aggregate: 61 world tiles; 0 legacy/v2 players; 0 ownerships/orphans; 0 castles; 0 allowed/enabled FIDs; 2 administrative audit entries

## Security findings

### S1 — Moderate: frontend permits cross-origin framing

The production root lacks response-level CSP `frame-ancestors`, `X-Frame-Options`, and HSTS. The complete live Warpkeep UI was reproduced inside an unrelated cross-origin iframe. This enables clickjacking/UI redress around the menu and realm-entry flow.

No session theft, authentication bypass, credential disclosure, or unauthorized realm action was demonstrated. The auth Worker itself correctly returns deny-all framing controls and strict credential protections.

**Remediation:** move or proxy the frontend through an edge capable of response headers. Add `frame-ancestors 'none'`, HSTS, a tested application CSP, `X-Content-Type-Options: nosniff`, Referrer-Policy and a restrictive Permissions-Policy. Keep legal-page meta CSP as defense in depth, but do not treat meta CSP as a framing control.

### S2 — Moderate: production components lack one end-to-end deployment attestation

Pages is bound to its Git SHA, but Worker and SpacetimeDB production changes remain manual. There is no protected Worker deployment workflow, SpacetimeDB publish workflow, unified deployment manifest, Worker Version Metadata binding or scheduled post-deploy gate.

The checked-in Worker intentionally defaults `PUBLIC_AUTH_ENABLED=false`, while the audited production version uses an explicit `true` deployment override. That default is fail-closed, but it makes exact release provenance important. Current live configuration and behavior passed verification; this is a future drift/recovery risk, not evidence of current drift.

Maincloud exposes live schema and behavior but no documented runtime module hash, so byte-for-byte module equivalence cannot be independently proven after publication.

**Remediation:** generate one immutable deployment manifest binding frontend SHA, Worker source/version/config fingerprint, dependency locks, module artifact receipt/schema/protocol, protected aggregate, timestamp and rollback coordinates. Require it in a protected environment and run privacy-safe post-deploy synthetics before promotion.

### S3 — Moderate reliability/security-operations risk: monitoring is not encoded

No repository-configured Worker observability, Version Metadata binding, scheduled authentication/resolver synthetic, alert threshold or deployment-health workflow was found. Existing application events are privacy-safe and allowlisted, but regressions may require manual discovery.

**Remediation:** add sanitized availability/error/latency buckets, deployed-version identity, bounded non-mutating synthetics, alert ownership, retention limits and rollback runbooks. Never retain FIDs, proof material, tokens, cookies, QR payloads, signatures or raw upstream responses.

### S4 — Low: Warpkeep-Assets default branch is unprotected

The runtime repository enforces strict required checks, up-to-date branch checks, admin enforcement, linear history and conversation resolution. Warpkeep-Assets has no branch protection or ruleset.

Fresh public release downloads still passed manifest and checksum verification, so no corruption was found.

**Remediation:** protect `main`, require pull requests and archive-verifier checks, block force pushes/deletion, and require resolved review conversations.

### S5 — Low/accepted structural privacy risk: frozen public v1 identity schema

The legacy public `player` schema retains an opaque identity field for wire compatibility. It has zero rows; protocol v2 does not read, write or subscribe to it, and the production aggregate verifies the zero-row invariant. Active v2 uses a public FID/game projection plus a private ownership binding.

**Remediation:** continue enforcing the zero-row hard stop until a separately reviewed breaking migration can remove the legacy structure.

### Governance hardening

- GitHub private vulnerability reporting is disabled.
- `/.well-known/security.txt` is absent.
- No dedicated privacy/security contact is published; the privacy notice accurately identifies this limitation.
- CAA records were not observed for the apex.

These are disclosure/governance gaps, not demonstrated exploits.

## QoL findings

### Q1 — High-impact mobile entry performance

Mobile Lighthouse recorded:

- performance score: 42;
- approximately 11.8 MiB transferred;
- approximately 2.23 seconds total blocking time.

Desktop performance was also constrained by a large JavaScript entry bundle and delayed LCP. Major assets include a roughly 1.12 MB JavaScript bundle, 5.35 MB title track, 9.63 MB menu track and 1.71/3.84 MB compact/high title models. The menu audio is prepared with `preload='auto'` while the user is still on the title. Large unversioned media receives only `max-age=600`.

**Remediation:** defer menu audio/video until entry, preserve the realm track's existing deferred behavior, split non-title UI and backend code, further compress/stream audio, prefer compact assets on constrained devices, provide a lightweight HTML/SVG LCP placeholder, and use long-lived immutable caching for versioned media.

### Q2 — Responsive layout defects

- At `360×800`, the menu wordmark/command area is crowded and can visibly overlap/collide.
- At `740×360`, Settings and Terms extend below the fold with weak scroll discovery.
- Keyboard Escape works, but short-landscape touch users lack an equally obvious persistent close control.

**Remediation:** add dedicated narrow/short viewport breakpoints, reduce vertical chrome, make dialog actions sticky, preserve a visible close button and test 320–390 px portrait plus 640–844 px short landscape.

### Q3 — Entry discoverability

The galactic-core entry target has a semantic label and adequate activation size, but recognition depends heavily on animation and a delayed hint. A first-time or reduced-attention user can miss the path forward.

**Remediation:** add a restrained persistent `ENTER WARPKEEP` affordance while retaining the core as the primary visual interaction.

### Q4 — Dead-end `EXIT` command

`EXIT` only reports that the feature is under construction and redirects users mentally to Return to Title/Escape.

**Remediation:** implement a meaningful web action or remove/rename the command until one exists.

### Q5 — No root render error boundary

Media, WebGL/model and backend reconnection paths have targeted fallbacks. No application-level React error boundary was found, so an unexpected render exception can still blank the UI.

**Remediation:** add a root recovery screen with reload, return-to-title and privacy-safe failure reporting.

### Q6 — Developer QoL

Strengths include extensive deterministic tests, Workerd coverage, generated-binding verification, fail-closed deployment tooling and zero TODO/FIXME debt. Gaps:

- no Playwright/Cypress browser E2E or visual-regression suite in CI;
- no ESLint/Prettier configuration or coverage gate;
- no dependency-update bot or scheduled audit;
- several large multi-responsibility files, especially the title renderer, auth provider, experience controller, main menu and audio director.

**Remediation:** add a small cross-browser release smoke suite first, then lint/format/coverage gates and gradual component/service decomposition.

### Q7 — Public-site polish

The favicon, web-app manifest, robots/sitemap and standard `security.txt` endpoint return 404. The missing favicon also causes avoidable console noise.

## Controls that passed

- Valid SAN TLS certificate; TLS 1.2/1.3 accepted and TLS 1.0/1.1 rejected.
- HTTP, `www` and legacy Pages routes converge on canonical HTTPS.
- Auth Worker returns HSTS, deny-all CSP/frame controls, no-referrer, `nosniff`, COOP/CORP and restrictive Permissions-Policy.
- Credentialed CORS is exact for `https://warpkeep.com`; hostile-origin preflight returned 403.
- `__Host-` session cookie uses Secure, HttpOnly and SameSite=Strict.
- Challenge consumption, browser binding, session-family rotation/replay controls, bounded tokens and rate limiting are implemented and tested.
- Public v1 authentication endpoints are retired; admin routes are not browser-CORS enabled.
- Anonymous SpacetimeDB data query was rejected `403 INVALID_ISSUER`.
- Private allowlist, ownership and audit tables remain inaccessible to browser subscriptions.
- Root suite: 564 tests passed.
- Auth bridge: 155 tests passed, including four real Cloudflare Workerd tests.
- SpacetimeDB module: 52 tests passed and the real module build succeeded.
- Typechecks, production build, asset/license/file-size verification passed.
- npm/pnpm vulnerability audits and package-signature verification passed.
- CodeQL passed with no open alerts at the audited SHA.
- Gitleaks found no live-bundle or asset-repository secret; two main-repository hits were inert test fixtures.
- No public source maps; common `.env`/`.git` probes returned 404.
- Automated WCAG A/AA scans found no structural violations across eight tested desktop/mobile states. Dynamic canvas/video contrast still requires manual acceptance.
- Public asset releases passed fresh download, manifest and hash verification.
- Both local repositories were clean and exactly matched their remote `main` heads after the audit.

## Priority order

1. Deny frontend framing and install the full browser-header baseline.
2. Bind Pages, Worker and SpacetimeDB releases through one protected deployment manifest and post-deploy gate.
3. Add privacy-safe monitoring and scheduled synthetics.
4. Reduce title/menu payload and improve immutable media caching.
5. Repair 360 px and short-landscape layouts; add persistent dialog-close controls.
6. Protect Warpkeep-Assets and add browser E2E/dependency automation.

## Limitations

The authenticated Farcaster exchange and admitted-player realm were intentionally not exercised because doing so would create or consume production authentication/state. Their implementation was assessed through source review, unit/Workerd/module tests, live read-only configuration and schema probes, anonymous-denial testing and the protected aggregate.

Three optional delegated reviewers timed out after ten minutes and returned no summaries. Their partial work was excluded; every conclusion above is backed by the primary audit's retained evidence.

## Evidence index

Evidence is retained in `audits/warpkeep-2026-07-14/evidence/`, including:

- `live-surface.txt`
- `cross-origin-frame.png`
- `lighthouse-mobile.json`
- `lighthouse-desktop.json`
- `interactive-viewport-audit.json`
- `axe-interactive.json`
- desktop, mobile and short-landscape screenshots
- `protected-aggregate-v2.json`
- `spacetimedb-live-schema.json`
- `gitleaks-Warpkeep.json`
- `gitleaks-Warpkeep-Assets.json`
- `gitleaks-live-bundle.json`
- `sbom-root.cdx.json`
