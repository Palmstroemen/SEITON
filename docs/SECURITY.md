# SEITON Security Overview

**⚠️ PROTOTYPE — Not for production use**

## Current Protections

- **Path traversal:** Blocked in embryo paths and API entry points
- **ACL system:** Three modes — `off` (default), `monitor`, `enforce`, set with `SEITON_ACL_MODE` (the former `MYOS_ACL_MODE` is still read; see [ACL_ROLLOUT.md](../core/Dokumentation/ACL_ROLLOUT.md))
- **Audit logging:** ACL decisions logged in monitor/enforce modes (the project's `.seiton/audit.log`)
- **Sandbox:** the time tracking's clock runs in bubblewrap with a drive of its own role (`core/sandbox.py`, `core/role_drive.py`; [Designdocument Time](../core/Dokumentation/Designdocument%20Time.md), 7)
- **Security tests:** Scope API, PostFix, importer, Desk and the sandbox have dedicated security tests (e.g. `core/tests/unit/test_scope_api_security.py`, `PostFix/tests/test_postfix_security.py`, `core/tests/unit/test_importer_security.py`, `core/tests/unit/test_sandbox.py`)

## ACL Rollout

See [core/Dokumentation/ACL_ROLLOUT.md](../core/Dokumentation/ACL_ROLLOUT.md) for the safe rollout path and operational checklist.

## Design Documents

- [Designdocument BlueprintLayer](../core/Dokumentation/Designdocument%20BlueprintLayer.md) — Path traversal, embryo handling
- [Designdocument ACLs](../core/Dokumentation/Designdocument%20ACLs.md) — ACL design
- [Designdocument Export-Import](../core/Dokumentation/Designdocument%20Export-Import.md) — Import/export security
- [Desk Security Test Index](../core/Dokumentation/Desk%20Security%20Test%20Index.md) — what the desktop profiles' tests cover

## Reporting Issues

Please report security issues via GitHub issues. Do not disclose critical vulnerabilities in public issues.
