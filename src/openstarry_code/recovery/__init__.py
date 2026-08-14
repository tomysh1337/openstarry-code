"""Public RC4 Desktop recovery contracts.

This package stays standard-library-only at import time so Desktop can inspect
and reconcile a profile before loading ordinary runtime/bootstrap modules.
"""

from openstarry_code.recovery.atomic import (
    PathIdentity,
    native_move_no_replace,
    no_follow_manifest,
    path_identity,
)
from openstarry_code.recovery.cleanup import (
    CleanupItem,
    CleanupReport,
    abandon_cleanup_transaction,
    cleanup_apply,
    cleanup_inspect,
)
from openstarry_code.recovery.config_recovery import recover_config
from openstarry_code.recovery.consolidate import (
    ConsolidationResult,
    acknowledge_profile_credential,
    consolidate_recovery_profiles,
)
from openstarry_code.recovery.engine import (
    choose_workspace,
    guard_desktop_profile,
    guarded_desktop_profile,
    inspect_profile,
    profile_replacement_transaction_unfinished,
    reconcile_profile,
)
from openstarry_code.recovery.errors import (
    AtomicStateUnknownError,
    ConfigChangedError,
    CrossDeviceMoveError,
    DestinationExistsError,
    InvalidWorkspaceError,
    LegacyGatewayRunningError,
    NoReplaceUnavailableError,
    ProfileLockBusyError,
    RecoveryError,
    RecoveryRequiredError,
    RestoreValidationError,
    StaleRecoveryTransactionError,
    UnsafePathError,
    WorkspaceOverrideError,
)
from openstarry_code.recovery.locking import (
    LegacyGatewayLock,
    ProfileOperationLock,
    acquire_legacy_gateway_locks,
    acquire_profile_locks,
    effective_state_roots,
    move_profile_no_replace,
    profile_lock_key,
    profile_lock_path,
)
from openstarry_code.recovery.models import RecoveryReport, WorkspaceCandidate
from openstarry_code.recovery.session_merge import (
    SessionMergeResult,
    SessionSchemaPreparer,
    merge_session_database,
    snapshot_session_database,
)
from openstarry_code.recovery.settings_transaction import (
    apply_desktop_settings,
    recover_desktop_settings,
    settings_transaction_exists,
)
from openstarry_code.recovery.transaction import recover_profile_transaction

__all__ = [
    "AtomicStateUnknownError",
    "CleanupItem",
    "CleanupReport",
    "ConsolidationResult",
    "ConfigChangedError",
    "CrossDeviceMoveError",
    "DestinationExistsError",
    "InvalidWorkspaceError",
    "LegacyGatewayLock",
    "LegacyGatewayRunningError",
    "NoReplaceUnavailableError",
    "PathIdentity",
    "ProfileLockBusyError",
    "ProfileOperationLock",
    "RecoveryError",
    "RecoveryReport",
    "RecoveryRequiredError",
    "RestoreValidationError",
    "StaleRecoveryTransactionError",
    "SessionMergeResult",
    "SessionSchemaPreparer",
    "UnsafePathError",
    "WorkspaceCandidate",
    "WorkspaceOverrideError",
    "abandon_cleanup_transaction",
    "acknowledge_profile_credential",
    "acquire_legacy_gateway_locks",
    "acquire_profile_locks",
    "apply_desktop_settings",
    "choose_workspace",
    "cleanup_apply",
    "cleanup_inspect",
    "consolidate_recovery_profiles",
    "guard_desktop_profile",
    "guarded_desktop_profile",
    "inspect_profile",
    "effective_state_roots",
    "native_move_no_replace",
    "move_profile_no_replace",
    "merge_session_database",
    "no_follow_manifest",
    "path_identity",
    "profile_replacement_transaction_unfinished",
    "profile_lock_key",
    "profile_lock_path",
    "reconcile_profile",
    "recover_config",
    "recover_desktop_settings",
    "recover_profile_transaction",
    "settings_transaction_exists",
    "snapshot_session_database",
]
