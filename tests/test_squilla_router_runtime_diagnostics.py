from __future__ import annotations

from openstarry_code.router_runtime_diagnostics import (
    MACOS_LIBOMP_MISSING,
    ROUTER_ASSETS_MISSING,
    ROUTER_NATIVE_DEPENDENCY_MISSING,
    ROUTER_PYTHON_DEPENDENCY_MISSING,
    WINDOWS_VC_RUNTIME_MISSING,
    classify_router_runtime_error,
    router_runtime_operator_message,
)


def test_router_runtime_classifier_detects_macos_libomp_failure() -> None:
    error = RuntimeError(
        "dlopen(.../lightgbm/lib/lib_lightgbm.dylib, 0x0006): Library not loaded: "
        "@rpath/libomp.dylib Referenced from: .../lib_lightgbm.dylib Reason: tried"
    )

    assert classify_router_runtime_error(error) == MACOS_LIBOMP_MISSING
    assert "brew install libomp" in router_runtime_operator_message(error)


def test_router_runtime_classifier_detects_windows_vc_failure() -> None:
    error = RuntimeError(
        "DLL load failed while importing onnxruntime_pybind11_state: "
        "The specified module could not be found."
    )

    assert classify_router_runtime_error(error) == WINDOWS_VC_RUNTIME_MISSING
    assert "vc_redist.x64.exe" in router_runtime_operator_message(error)


def test_router_runtime_classifier_detects_assets_and_generic_native_failures() -> None:
    assert (
        classify_router_runtime_error("missing V4 bundle files in /tmp/router: ['runtime_src']")
        == ROUTER_ASSETS_MISSING
    )
    assert (
        classify_router_runtime_error("lib_lightgbm.so: cannot open shared object file")
        == ROUTER_NATIVE_DEPENDENCY_MISSING
    )


def test_router_runtime_classifier_detects_wrapped_python_dependency_failure() -> None:
    error = RuntimeError("failed to initialize V4 Phase 3 router")
    error.__cause__ = ImportError("No module named 'lightgbm'")

    assert classify_router_runtime_error(error) == ROUTER_PYTHON_DEPENDENCY_MISSING
