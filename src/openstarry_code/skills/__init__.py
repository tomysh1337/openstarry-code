"""Skills system for OpenStarry Code.

Six-layer architecture (low→high precedence):
- Extra: config-specified additional directories
- Bundled: Ship with OpenStarry Code in src/openstarry_code/skills/bundled/
- Managed: Local installs in $OPENSTARRY_CODE_STATE_DIR/skills/ (default ~/.openstarry-code/skills/)
- Personal: Local user installs in ~/.agents/skills/
- Project: {workspace}/.agents/skills/
- Workspace: {workspace}/skills/

Only Bundled skills are shipped with OpenStarry Code. Managed, Personal, Project,
Workspace, and Extra layers are local directories discovered at runtime.
"""

from __future__ import annotations

from openstarry_code.skills.eligibility import (
    EligibilityContext,
    EligibilityReport,
    InstallHint,
    check_eligibility,
    diagnose_eligibility,
)
from openstarry_code.skills.injector import SkillInjector
from openstarry_code.skills.loader import SkillLoader
from openstarry_code.skills.resources import SkillResources
from openstarry_code.skills.types import (
    SkillInstallSpec,
    SkillLayer,
    SkillPlatformMeta,
    SkillRequires,
    SkillSpec,
)

__all__ = [
    "EligibilityContext",
    "EligibilityReport",
    "InstallHint",
    "SkillInjector",
    "SkillInstallSpec",
    "SkillLayer",
    "SkillLoader",
    "SkillPlatformMeta",
    "SkillRequires",
    "SkillResources",
    "SkillSpec",
    "check_eligibility",
    "diagnose_eligibility",
]
