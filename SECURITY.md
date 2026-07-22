# Warpkeep-Assets Security Policy

Warpkeep-Assets is the public provenance and release archive for Warpkeep media.
Its manifests and checksums verify exact bytes; they do not turn an untrusted
manifest into an authenticated one or grant rights that provenance does not
record.

## Supported material

The current `main` verifier, committed release manifests, and public release
attachments receive best-effort security fixes. Superseded scripts, local source
deposits, and material outside the repository's recorded release boundaries are
unsupported.

## Reporting a vulnerability

Use **Report a vulnerability** on this repository's Security page. Do not put a
vulnerability, reproduction, private source asset, or sensitive evidence in a
public issue, pull request, discussion, cast, or direct message.

If private vulnerability reporting is unavailable, open a content-free issue
titled `Security contact request` and wait for a private channel. Never attach
access tokens, private keys, credentials, unpublished source packages, private
communication metadata, identities, browser traces, or raw private logs.

Reports should use synthetic local fixtures and include only the affected
commit or release, impact, required attacker access, and minimal non-destructive
reproduction steps. There is no bug-bounty or response-time guarantee.
