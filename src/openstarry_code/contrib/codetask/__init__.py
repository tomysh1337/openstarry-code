"""Real-repository coding tasks for OpenStarry Code (contrib).

Runs an OpenStarry Code agent against a real git repository to solve a GitHub
issue or a free-form feature request, then verifies the work with a
red→green→regression loop. Host mode only in v1: the repo is cloned to a
disposable working directory and the agent runs as a host subprocess (no
Docker). Treat the target repo as TRUSTED — host mode is not an OS
isolation boundary.

Nothing here is imported by OpenStarry Code's startup path; modules load on
demand from the ``openstarry-code code-task`` CLI subcommand.
"""
