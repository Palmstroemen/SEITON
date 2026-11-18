from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, Optional, Union

from core.acl import ACLAuthorizer, find_acl_project_root
from core.brand import META_DIR, getenv

AuditSink = Callable[[Dict[str, object]], None]

MODES = ("off", "monitor", "enforce")


def configured_mode() -> str:
    """The ACL mode set for this run (MYOS_ACL_MODE): off (default), monitor or enforce.
    Scope's checks and the suggested folders both follow it."""
    mode = str(getenv("ACL_MODE") or "off").strip().lower()
    return mode if mode in MODES else "off"


def allowed_at(path: Union[str, Path], action: str, user: Optional[str] = None) -> bool:
    """Whether user (default: the person at path, core.identity) may do action ("read",
    "write", "delete", ...) at path, by the ACLs.md that governs path: its own project's, or
    the parent's it inherits - whatever program asks and wherever it stands otherwise.
    True when the mode is not enforce, and where no ACLs.md governs."""
    mode = configured_mode()
    if mode != "enforce":
        return True
    target = Path(path).expanduser().resolve()
    root = find_acl_project_root(target)
    if root is None:
        return True
    from core.identity import acl_user_for  # here: core.identity reads ACLs itself

    project = next((c for c in [target, *target.parents] if (c / META_DIR / "Project.md").is_file()), None)
    backend = str(getenv("ACL_BACKEND") or "auto").strip().lower()
    try:
        # The folder rules apply again to the template folders of the path's own subproject.
        authorizer = ACLAuthorizer.from_project(root, backend=backend if backend in {"auto", "legacy", "casbin"}
                                                else "auto", context=project)
    except Exception:
        return False  # Security: rules that cannot be read allow nothing
    rel = str(target.relative_to(root)).replace("\\", "/") if target != root else ""
    resource = "/" + rel if rel and rel != "." else "/"
    who = user if user is not None else acl_user_for(target)
    check = ACLEnforcementService(authorizer, mode=mode).check(ACLCheckRequest(user=who, action=action, resource=resource))
    return check.allowed


@dataclass(frozen=True)
class ACLCheckRequest:
    user: str
    action: str
    resource: str


@dataclass(frozen=True)
class ACLCheckResult:
    allowed: bool
    enforced: bool
    reason: str
    mode: str


class ACLEnforcementService:
    """Feature-flagged ACL enforcement wrapper with audit events."""

    def __init__(
        self,
        authorizer: ACLAuthorizer,
        mode: str = "off",
        audit_sink: Optional[AuditSink] = None,
    ) -> None:
        self.authorizer = authorizer
        self.mode = self._normalize_mode(mode)
        self._audit_sink = audit_sink

    @staticmethod
    def _normalize_mode(raw_mode: str) -> str:
        mode = str(raw_mode or "").strip().lower()
        if mode in {"off", "monitor", "enforce"}:
            return mode
        # // Security: unknown modes fail closed to strict enforcement.
        return "enforce"

    def check(self, request: ACLCheckRequest) -> ACLCheckResult:
        user = str(request.user or "").strip().lower()
        action = str(request.action or "").strip().lower() or "read"
        resource = str(request.resource or "").strip() or "/"

        policy_allowed = self.authorizer.can_user_access(user, resource, action)
        if self.mode == "off":
            result = ACLCheckResult(allowed=True, enforced=False, reason="acl_off", mode=self.mode)
        elif self.mode == "monitor":
            reason = "policy_allowed" if policy_allowed else "monitor_override"
            result = ACLCheckResult(allowed=True, enforced=False, reason=reason, mode=self.mode)
        else:
            reason = "policy_allowed" if policy_allowed else "policy_denied"
            result = ACLCheckResult(allowed=policy_allowed, enforced=True, reason=reason, mode=self.mode)

        self._emit_audit_event(
            user=user,
            action=action,
            resource=resource,
            policy_allowed=policy_allowed,
            result=result,
        )
        return result

    def _emit_audit_event(
        self,
        *,
        user: str,
        action: str,
        resource: str,
        policy_allowed: bool,
        result: ACLCheckResult,
    ) -> None:
        if self._audit_sink is None:
            return
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user": user,
            "action": action,
            "resource": resource,
            "mode": result.mode,
            "policy_allowed": bool(policy_allowed),
            "allowed": bool(result.allowed),
            "enforced": bool(result.enforced),
            "reason": result.reason,
            "backend": self.authorizer.backend,
        }
        self._audit_sink(event)

