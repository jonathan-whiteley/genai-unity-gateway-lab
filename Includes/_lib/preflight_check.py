# _lib/preflight_check.py
#
# Optional, non-fatal prerequisite check for the Unity AI Gateway lab.
#
# Run this BEFORE the classroom setup to fail fast with clear guidance instead
# of hitting a cryptic error mid-setup. It never raises: it prints a PASS / WARN
# / FAIL checklist and points at the README's "Known gotchas" section. The real
# hard gates still live in the setup itself (serverless version, catalog create).
#
# Added in this hardened copy of the lab (not in the original); see the README
# changelog.

import os
from typing import Optional

_PASS = "[PASS]"
_WARN = "[WARN]"
_FAIL = "[FAIL]"
_INFO = "[INFO]"


def _line(marker: str, title: str, detail: str = "") -> None:
    print(f"  {marker} {title}")
    if detail:
        for ln in detail.splitlines():
            print(f"         {ln}")


def _check_serverless(serverless_version: str) -> bool:
    is_serverless = os.environ.get("IS_SERVERLESS", "") == "TRUE"
    runtime = os.environ.get("DATABRICKS_RUNTIME_VERSION", "")
    ok = is_serverless and runtime.startswith(f"client.{serverless_version}.")
    if ok:
        _line(_PASS, f"Serverless environment version {serverless_version}",
              f"detected runtime '{runtime}'")
    else:
        detected = f"serverless '{runtime}'" if is_serverless else "classic (non-serverless) compute"
        _line(_FAIL, f"Serverless environment version {serverless_version} required",
              f"running on {detected}.\n"
              f"Open the Environment side panel, set version to {serverless_version}, Apply, re-run.")
    return ok


def _check_catalog(catalog_override: str) -> bool:
    """Report the catalog the lab will use and whether it's ready."""
    try:
        from .catalog_utils import (
            _current_user_email, _safe_uc_name, _get_workspace_catalogs, _catalog_exists,
        )
        catalogs = _get_workspace_catalogs()
        if catalog_override:
            if _catalog_exists(catalog_override, catalogs):
                _line(_PASS, f"Catalog override '{catalog_override}' exists",
                      "you need CREATE SCHEMA on it (setup will create the lab schema there).")
                return True
            _line(_FAIL, f"Catalog override '{catalog_override}' does not exist",
                  "create it first, or fix the $catalog_override value.")
            return False
        user = _current_user_email()
        target = f"labuser_{_safe_uc_name(user.split('@')[0])[:19]}"
        if _catalog_exists(target, catalogs):
            _line(_PASS, f"Catalog '{target}' already exists", "setup will reuse it.")
            return True
        _line(_WARN, f"Catalog '{target}' will be created by setup",
              "On accounts with UC Default Storage (no metastore storage root) a bare\n"
              "CREATE CATALOG fails. If so: pass $catalog_override=\"<existing_catalog>\",\n"
              "or set catalog.managed_location in config-1.yaml. See README 'Known gotchas'.")
        return True
    except Exception as e:  # never let the check itself break the notebook
        _line(_INFO, "Could not evaluate catalog readiness", str(e))
        return True


def _check_foundation_models() -> bool:
    """At least one Claude/GPT pay-per-token endpoint must exist for gateway routing."""
    try:
        from databricks.sdk import WorkspaceClient
        names = [e.name or "" for e in WorkspaceClient().serving_endpoints.list()]
        fm = [n for n in names if "claude" in n.lower() or "gpt" in n.lower()]
        if fm:
            _line(_PASS, f"Foundation Model endpoints available ({len(fm)} found)",
                  "e.g. " + ", ".join(sorted(fm)[:4]))
            return True
        _line(_FAIL, "No Foundation Model (Claude/GPT) serving endpoints found",
              "The gateway steps route to system.ai model services backed by these.\n"
              "Confirm Foundation Model APIs are available in this workspace/region.")
        return False
    except Exception as e:
        _line(_WARN, "Could not list serving endpoints", str(e))
        return True


def _check_apps() -> bool:
    try:
        from databricks.sdk import WorkspaceClient
        # Touch the Apps API; consume one item at most.
        it = iter(WorkspaceClient().apps.list())
        next(it, None)
        _line(_PASS, "Databricks Apps API reachable", "you also need permission to create apps.")
        return True
    except Exception as e:
        _line(_WARN, "Could not reach the Databricks Apps API", str(e) +
              "\nApps may be disabled in this workspace/region, or you may lack permission.")
        return True


def _check_previews() -> None:
    """Best-effort note on the two Beta previews. These are account-admin toggles
    under Previews and can't be reliably probed via API, so we advise verifying."""
    _line(_INFO, "Beta previews (enable under Previews, needs an account admin)",
          "- Service policies: required for the hallucination guardrail step.\n"
          "- Managed MLflow Prompt Registry: powers the 'My Agent' prompt panel\n"
          "  (setup degrades gracefully if it's off). Verify both are ON.")


def preflight_check(catalog_override: str = "", serverless_version: str = "5") -> bool:
    """Print a prerequisite checklist for the lab. Returns True if no hard FAIL.

    Non-fatal by design: it never raises and never blocks setup. Pass the same
    ``$catalog_override`` you plan to use so the catalog check is accurate.
    """
    print("=" * 60)
    print("Unity AI Gateway lab - preflight prerequisite check")
    print("=" * 60)
    results = {
        "serverless": _check_serverless(serverless_version),
        "catalog": _check_catalog(catalog_override),
        "foundation_models": _check_foundation_models(),
        "apps": _check_apps(),
    }
    _check_previews()
    hard_fail = not (results["serverless"] and results["foundation_models"])
    print("-" * 60)
    if hard_fail:
        print("  Result: resolve the [FAIL] item(s) above before running setup.")
    else:
        print("  Result: prerequisites look OK. Review any [WARN]/[INFO] notes, then run setup.")
    print("=" * 60)
    return not hard_fail
