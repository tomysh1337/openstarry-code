"""Pre-turn pipeline steps."""

from openstarry_code.engine.pipeline import TurnContext
from openstarry_code.engine.steps.coding_mode import enforce_coding_mode
from openstarry_code.engine.steps.inject_platform_hint import inject_platform_hint
from openstarry_code.engine.steps.inject_subagent_grounding import inject_subagent_grounding
from openstarry_code.engine.steps.meta_command import meta_command_launch
from openstarry_code.engine.steps.meta_resolution import meta_resolution
from openstarry_code.engine.steps.prompt_cache import apply_prompt_cache
from openstarry_code.engine.steps.reasoning_hint_observer import observe_reasoning_hint
from openstarry_code.engine.steps.resolve_model import resolve_model
from openstarry_code.engine.steps.skills_filter import filter_skills
from openstarry_code.engine.steps.vision_followup_gate import apply_vision_followup_gate

try:
    from openstarry_code.engine.steps.squilla_router import apply_squilla_router
except ImportError:

    async def apply_squilla_router(ctx: TurnContext) -> TurnContext:
        return ctx


__all__ = [
    "apply_prompt_cache",
    "apply_squilla_router",
    "apply_vision_followup_gate",
    "enforce_coding_mode",
    "filter_skills",
    "inject_platform_hint",
    "inject_subagent_grounding",
    "meta_command_launch",
    "meta_resolution",
    "observe_reasoning_hint",
    "resolve_model",
]
