#!/usr/bin/env python3
"""Select a declared route and evaluate versioned evidence without side effects."""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


INTENTS = ("format", "explain", "review", "repair", "revise", "create",
           "research", "maintain", "publish")
METHODS = {
    "format": ("preserve-content", ("content-preserved", "format-matches-request")),
    "explain": ("explain-with-evidence", ("answer-supported", "scope-respected")),
    "review": ("review-against-criteria", ("findings-supported", "coverage-stated")),
    "repair": ("reproduce-and-repair", ("problem-resolved", "regressions-checked")),
    "revise": ("revise-within-scope", ("requested-change-achieved", "locked-facts-preserved")),
    "create": ("create-against-criteria", ("requirements-met", "deliverable-usable")),
    "research": ("verify-sources", ("claims-supported", "uncertainty-disclosed")),
    "maintain": ("compare-with-baseline", ("baseline-fixed", "differences-supported")),
    "publish": ("verify-before-delivery", ("artifact-ready", "delivery-target-confirmed")),
}
DOMAIN_CHECKS = {
    "software": {
        "explain": ("failure-condition-verified",),
        "repair": ("normal-entry-point-verified",),
        "create": ("normal-entry-point-verified",),
        "review": ("behavior-and-regressions-reviewed",),
    },
    "creative": {
        "create": ("established-context-respected", "reader-effect-reviewed"),
        "revise": ("continuity-preserved", "reader-effect-reviewed"),
        "review": ("continuity-and-craft-reviewed",),
    },
    "research": {
        "explain": ("source-scope-stated",),
        "research": ("source-versions-recorded",),
        "review": ("claims-checked-against-sources",),
    },
    "documents": {
        "create": ("structure-and-readability-reviewed",),
        "revise": ("meaning-preserved",),
        "review": ("structure-and-meaning-reviewed",),
    },
    "data": {
        "create": ("data-validated", "calculations-reconciled"),
        "revise": ("data-integrity-checked",),
        "review": ("units-and-calculations-checked",),
    },
    "operations": {
        "create": ("inputs-outputs-and-handoffs-defined",),
        "repair": ("process-recovery-verified",),
        "publish": ("execution-scope-verified",),
    },
}
SOFTWARE_MODULES = {
    "explain": ("debugging-and-error-recovery",),
    "review": ("code-review-and-quality",),
    "repair": ("debugging-and-error-recovery", "test-driven-development"),
    "revise": ("incremental-implementation",),
    "create": ("incremental-implementation",),
    "research": ("source-driven-development",),
    "publish": ("shipping-and-launch",),
}
CHECK_KINDS = ("test", "mechanical", "review")
RESULTS = ("PASS", "FAIL", "NOT_APPLICABLE")


def route(intent, domain, complex=False):
    """Choose a procedure after the caller determines intent from the user request."""
    if (not isinstance(intent, str) or intent not in METHODS
            or not isinstance(domain, str)
            or not re.fullmatch(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*", domain)
            or len(domain) > 64 or type(complex) is not bool):
        raise ValueError("invalid intent, domain, or complexity")
    method, checks = METHODS[intent]
    if intent == "explain" and domain == "software":
        method = "diagnose"
    checks += DOMAIN_CHECKS.get(domain, {}).get(intent, ())
    modules = SOFTWARE_MODULES.get(intent, ()) if domain == "software" else ()
    if complex and domain == "software" and intent == "create":
        modules = ("spec-driven-development", "planning-and-task-breakdown") + modules
    return {
        "route": intent,
        "domain": domain,
        "complex": complex,
        "depth": "structured" if complex else "quick",
        "method": method,
        "checks": list(checks),
        "modules": list(modules),
    }


def _mapping(value, field):
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object")
    return value


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _nonnegative(value, field):
    if type(value) is not int or value < 0:
        raise ValueError(f"{field} must be a nonnegative integer")
    return value


def _check_outcome(check, receipt, versions):
    if not receipt or not _text(receipt.get("reference")):
        return "UNTESTED"
    bound_versions = _mapping(receipt.get("versions", {}), "evidence versions")
    dependencies = check["depends_on"]
    if any(not _text(versions.get(ref)) or not _text(bound_versions.get(ref))
           for ref in dependencies):
        return "UNTESTED"
    if any(bound_versions[ref] != versions[ref] for ref in dependencies):
        return "STALE"
    result = receipt.get("result")
    if result not in RESULTS:
        raise ValueError("evidence result must be PASS, FAIL, or NOT_APPLICABLE")
    if result == "NOT_APPLICABLE":
        if check.get("allow_not_applicable") and _text(receipt.get("reason")):
            return result
        return "UNTESTED"
    if check["kind"] == "test":
        exit_code, executed = receipt.get("exit_code"), receipt.get("executed")
        if type(exit_code) is not int or type(executed) is not int or executed <= 0:
            return "UNTESTED"
        if exit_code != 0:
            return "FAIL"
    if check.get("requires_isolation") and receipt.get("context_isolation") != "isolated":
        return "UNTESTED"
    return result


def _approved(action, versions, required_refs):
    approval = _mapping(action.get("approval", {}), "external_action.approval")
    ref = action.get("artifact_ref")
    if (not _text(ref) or ref not in required_refs
            or versions.get(ref) != action.get("artifact_version")):
        return False
    return _text(approval.get("reference")) and all(
        _text(action.get(key)) and approval.get(key) == action[key]
        for key in ("action", "target", "artifact_version")
    )


def evaluate(state):
    """Evaluate recorded facts. The caller is responsible for authentic receipts."""
    state = _mapping(state, "state")
    versions = _mapping(state.get("versions"), "versions")
    evidence = _mapping(state.get("evidence", {}), "evidence")
    if any(not _text(ref) or not _text(version) for ref, version in versions.items()):
        raise ValueError("version names and values must be nonempty strings")
    revisions = _nonnegative(state.get("revision_count", 0), "revision_count")
    maximum = _nonnegative(state.get("max_revisions", 3), "max_revisions")
    retries = _nonnegative(state.get("retry_count", 0), "retry_count")
    if revisions > maximum:
        raise ValueError("revision_count exceeds max_revisions")
    checks = state.get("checks")
    if not isinstance(checks, list):
        raise ValueError("checks must be an array")

    outcomes = {}
    required = []
    required_refs = set()
    for check in checks:
        check = _mapping(check, "check")
        check_id = check.get("id")
        if not _text(check_id) or check_id in outcomes:
            raise ValueError("check ids must be nonempty and unique")
        if check.get("kind") not in CHECK_KINDS:
            raise ValueError("check kind must be test, mechanical, or review")
        dependencies = check.get("depends_on")
        if (not isinstance(dependencies, list) or not dependencies
                or not all(_text(ref) for ref in dependencies)
                or len(set(dependencies)) != len(dependencies)):
            raise ValueError("depends_on must contain unique, nonempty version names")
        is_required = check.get("required", True)
        isolation = check.get("requires_isolation", False)
        may_skip = check.get("allow_not_applicable", False)
        if any(type(value) is not bool for value in (is_required, isolation, may_skip)):
            raise ValueError("required, requires_isolation, and allow_not_applicable must be boolean")
        if isolation and check["kind"] != "review":
            raise ValueError("requires_isolation is supported for review checks only")
        if is_required:
            required.append(check_id)
            required_refs.update(dependencies)
        receipt = _mapping(evidence.get(check_id, {}), f"evidence for {check_id}")
        outcomes[check_id] = _check_outcome(check, receipt, versions)

    if not required:
        raise ValueError("at least one required check is needed")
    missing = required_refs.difference(versions)
    recheck = [key for key in required if outcomes[key] in {"STALE", "UNTESTED"}]
    failures = [key for key in required if outcomes[key] == "FAIL"]
    stop_reason, blocked_reason = state.get("stop_reason"), state.get("blocked_reason")
    external_action = state.get("external_action")

    if _text(stop_reason):
        status, reason = "STOPPED", stop_reason
    elif _text(blocked_reason):
        status, reason = "BLOCKED", blocked_reason
    elif missing:
        status, reason = "BLOCKED", "missing versions: " + ", ".join(sorted(missing))
    elif external_action is not None and not _approved(
            _mapping(external_action, "external_action"), versions, required_refs):
        status, reason = "BLOCKED", "missing or mismatched action approval"
    elif recheck:
        status, reason = "RECHECK", "required evidence is stale or untested"
    elif failures and revisions >= maximum:
        status, reason = "STOPPED", "required checks failed and revision budget is exhausted"
    elif failures:
        status, reason = "REVISE", "required checks failed"
    else:
        status, reason = "READY", "all required checks are current and satisfied"

    return {
        "status": status, "reason": reason, "checks": outcomes, "recheck": recheck,
        "failures": failures, "revision_count": revisions, "max_revisions": maximum,
        "retry_count": retries,
    }


def fingerprint(paths):
    """Return content fingerprints using caller-provided path strings as names."""
    result = {}
    for path in paths:
        digest = hashlib.sha256()
        with Path(path).open("rb") as stream:
            for chunk in iter(lambda: stream.read(65536), b""):
                digest.update(chunk)
        result[path] = digest.hexdigest()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    selector = commands.add_parser("route")
    selector.add_argument("--intent", required=True, choices=INTENTS)
    selector.add_argument("--domain", required=True, help="a built-in or custom domain slug")
    selector.add_argument("--complex", action="store_true")
    gate = commands.add_parser("evaluate")
    gate.add_argument("state", type=Path)
    hashes = commands.add_parser("fingerprint")
    hashes.add_argument("files", nargs="+")
    args = parser.parse_args()

    try:
        if args.command == "route":
            result = route(args.intent, args.domain, args.complex)
        elif args.command == "evaluate":
            result = evaluate(json.loads(args.state.read_text(encoding="utf-8")))
        else:
            result = fingerprint(args.files)
    except (OSError, TypeError, ValueError) as error:
        parser.exit(2, f"workflow: {error}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
