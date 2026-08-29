import { computed, ref, watch } from 'vue'

// Assist modes — client-side augmentation modes toggled from the composer's
// "+" menu, layered on top of the server's collaboration modes (plan/goal):
//
//   • Review mode — the model answers, then iteratively self-reviews its own
//     output (logic → performance → security → style → edge cases), silently
//     fixing what it finds, and finishes with a structured 审查报告 blockquote
//     that the chat renders as a glass card. Levels widen the audit surface.
//   • Thinking mode — asks for a visible step-by-step approach section before
//     the final answer (off / auto brief / high full).
//
// State is a module singleton (the modes apply to every send from any
// composer instance) and persists across reloads. AUGMENT OpenStarry note:
// this only shapes the prompt — the server stays the source of truth for
// collaboration modes and tool use.

export type ReviewLevel = 'off' | 'lenient' | 'normal' | 'strict'
export type ThinkingLevel = 'off' | 'auto' | 'high'

const REVIEW_KEY = 'opensquilla.reviewLevel'
const THINKING_KEY = 'opensquilla.thinkingLevel'

function loadLevel<T extends string>(key: string, allowed: readonly T[], fallback: T): T {
  try {
    const raw = localStorage.getItem(key)
    return allowed.includes(raw as T) ? (raw as T) : fallback
  } catch {
    return fallback
  }
}

const REVIEW_ORDER = ['off', 'lenient', 'normal', 'strict'] as const
const THINKING_ORDER = ['off', 'auto', 'high'] as const

const reviewLevel = ref<ReviewLevel>(
  loadLevel(REVIEW_KEY, REVIEW_ORDER, 'off'),
)
const thinkingLevel = ref<ThinkingLevel>(
  loadLevel(THINKING_KEY, THINKING_ORDER, 'off'),
)

watch(reviewLevel, (v) => {
  try { localStorage.setItem(REVIEW_KEY, v) } catch {}
})
watch(thinkingLevel, (v) => {
  try { localStorage.setItem(THINKING_KEY, v) } catch {}
})

/** Cycle to the next level (the add-menu item is a single toggle button). */
export function useAssistModes() {
  const reviewActive = computed(() => reviewLevel.value !== 'off')
  const thinkingActive = computed(() => thinkingLevel.value !== 'off')

  function cycleReviewLevel(): ReviewLevel {
    const idx = REVIEW_ORDER.indexOf(reviewLevel.value)
    reviewLevel.value = REVIEW_ORDER[(idx + 1) % REVIEW_ORDER.length]
    return reviewLevel.value
  }

  function cycleThinkingLevel(): ThinkingLevel {
    const idx = THINKING_ORDER.indexOf(thinkingLevel.value)
    thinkingLevel.value = THINKING_ORDER[(idx + 1) % THINKING_ORDER.length]
    return thinkingLevel.value
  }

  return {
    reviewLevel,
    thinkingLevel,
    reviewActive,
    thinkingActive,
    cycleReviewLevel,
    cycleThinkingLevel,
  }
}

const REVIEW_DIRECTIVES: Record<Exclude<ReviewLevel, 'off'>, string> = {
  lenient: [
    '[REVIEW MODE: lenient] After answering, review your own output for severe logic errors and security vulnerabilities only.',
    'Fix anything you find, then re-check until no severe issue remains.',
    'Finish with a markdown blockquote report starting with "🔍 **审查报告**", grouped by "⚠️ 严重" (severity: issue + fix).',
  ].join(' '),
  normal: [
    '[REVIEW MODE: normal] After answering, review your own output iteratively: logic correctness, performance, security, and common best practices.',
    'Fix every issue you find and re-review until nothing critical remains.',
    'Finish with a markdown blockquote report starting with "🔍 **审查报告**", grouped by "⚠️ 严重" and "⚡ 性能" (issue + fix each).',
  ].join(' '),
  strict: [
    '[REVIEW MODE: strict] After answering, review your own output exhaustively and iteratively: logic, performance, security, code style, and edge cases.',
    'Fix every issue and re-review repeatedly until you find no remaining problems.',
    'Finish with a markdown blockquote report starting with "🔍 **审查报告**", grouped by "⚠️ 严重", "⚡ 性能" and "💡 建议" (issue + fix each).',
  ].join(' '),
}

const THINKING_DIRECTIVES: Record<Exclude<ThinkingLevel, 'off'>, string> = {
  auto: '[THINKING MODE: auto] Before the final answer, include a short "🧠 思路" section: 2-3 sentences outlining your approach.',
  high: '[THINKING MODE: high] Before the final answer, include a "🧠 思路" section that reasons step by step: the problem breakdown, candidate approaches considered, trade-offs, and why you chose this path.',
}

/**
 * Augment an outgoing user message with the active assist-mode directives.
 * Returns the original text untouched when both modes are off. The directive
 * block travels inside the message (the gateway has no dedicated field for
 * these modes); it is compact and prefixed so it stays scannable in history.
 */
export function applyAssistModes(text: string): string {
  const parts: string[] = []
  if (reviewLevel.value !== 'off') parts.push(REVIEW_DIRECTIVES[reviewLevel.value])
  if (thinkingLevel.value !== 'off') parts.push(THINKING_DIRECTIVES[thinkingLevel.value])
  if (!parts.length) return text
  return `${text}\n\n${parts.join('\n')}`
}
