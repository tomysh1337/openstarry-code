<template>
  <Teleport to="body">
    <Transition name="cu-preview-modal">
      <div v-if="open" class="cu-preview-overlay" @click="onClose">
        <div
          ref="modalRef"
          class="cu-preview"
          role="dialog"
          aria-modal="true"
          aria-labelledby="cu-preview-title"
          @click.stop
        >
          <header class="cu-preview__header">
            <div class="cu-preview__heading">
              <h3 id="cu-preview-title">{{ t('settings.mcp.preview.title') }}</h3>
              <span class="cu-preview__badge" :class="`cu-preview__badge--${state.status}`">
                <span class="cu-preview__badge-dot" aria-hidden="true"></span>
                {{ statusLabel }}
              </span>
            </div>
            <button
              ref="closeBtn"
              type="button"
              class="btn btn--icon btn--ghost"
              :aria-label="t('settings.mcp.preview.close')"
              :title="t('settings.mcp.preview.close')"
              data-testid="cu-preview-close"
              @click="onClose"
            >
              <Icon name="x" :size="16" />
            </button>
          </header>

          <div class="cu-preview__stage" data-testid="cu-preview-stage">
            <div v-if="loading && !state.screenshot" class="cu-preview__state" role="status">
              {{ t('shared.loading') }}
            </div>
            <div v-else-if="error && !state.screenshot" class="cu-preview__state" role="alert">
              <span>{{ t('settings.mcp.preview.loadFailed') }}</span>
              <button type="button" class="btn" @click="void poll()">
                {{ t('settings.mcp.retry') }}
              </button>
            </div>
            <div v-else-if="!state.screenshot" class="cu-preview__state cu-preview__state--empty">
              <Icon name="monitor" :size="28" aria-hidden="true" />
              <span>{{ t('settings.mcp.preview.noScreenshot') }}</span>
            </div>
            <template v-else>
              <img
                :src="dataUri ?? undefined"
                class="cu-preview__screenshot"
                :alt="t('settings.mcp.preview.title')"
                data-testid="cu-preview-screenshot"
                @load="onScreenshotLoad"
              />
              <span
                v-if="cursorStyle"
                class="cu-preview__cursor"
                :style="cursorStyle"
                :title="cursorTitle"
                aria-hidden="true"
              ></span>
            </template>
          </div>

          <footer class="cu-preview__meta">
            <div class="cu-preview__meta-row">
              <span class="cu-preview__meta-label">{{ t('settings.mcp.preview.lastAction') }}</span>
              <span class="cu-preview__meta-value" data-testid="cu-preview-last-action">
                {{ state.lastAction || t('settings.mcp.preview.noAction') }}
              </span>
            </div>
            <div v-if="cursorTitle" class="cu-preview__meta-row">
              <span class="cu-preview__meta-label">{{ t('settings.mcp.preview.cursor') }}</span>
              <span class="cu-preview__meta-value">{{ cursorTitle }}</span>
            </div>
          </footer>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import Icon from '@/components/Icon.vue'
import { useDialogA11y } from '@/composables/useDialogA11y'
import {
  fetchComputerUseState,
  screenshotDataUri,
  type ComputerUseState,
} from '@/utils/computerUseApi'

const props = defineProps<{ open: boolean }>()
const emit = defineEmits<{ (e: 'close'): void }>()

const { t } = useI18n()

const POLL_INTERVAL_MS = 2000

const state = ref<ComputerUseState>({
  status: 'idle',
  screenshot: null,
  screenshotWidth: null,
  screenshotHeight: null,
  cursor: null,
  lastAction: null,
  updatedAt: null,
})
const loading = ref(false)
const error = ref(false)

const modalRef = ref<HTMLElement | null>(null)
const closeBtn = ref<HTMLElement | null>(null)

const isOpen = computed(() => props.open)

function onClose(): void {
  emit('close')
}

useDialogA11y(modalRef, isOpen, onClose, { initialFocus: closeBtn })

const dataUri = computed(() => screenshotDataUri(state.value))

const statusLabel = computed(() => {
  if (state.value.status === 'active') return t('settings.mcp.preview.statusActive')
  if (state.value.status === 'aborted') return t('settings.mcp.preview.statusAborted')
  return t('settings.mcp.preview.statusIdle')
})

// Screenshot pixel size: prefer the state-provided resolution, fall back to
// the decoded image's intrinsic size once it loads.
const naturalSize = ref<{ width: number; height: number } | null>(null)

function onScreenshotLoad(event: Event): void {
  const img = event.target as HTMLImageElement | null
  if (img && img.naturalWidth > 0 && img.naturalHeight > 0) {
    naturalSize.value = { width: img.naturalWidth, height: img.naturalHeight }
  }
}

const screenshotSize = computed(() => {
  if (state.value.screenshotWidth && state.value.screenshotHeight) {
    return {
      width: state.value.screenshotWidth,
      height: state.value.screenshotHeight,
    }
  }
  return naturalSize.value
})

const cursorStyle = computed(() => {
  const cursor = state.value.cursor
  const size = screenshotSize.value
  if (!cursor || !size) return null
  if (size.width <= 0 || size.height <= 0) return null
  const left = Math.min(Math.max((cursor.x / size.width) * 100, 0), 100)
  const top = Math.min(Math.max((cursor.y / size.height) * 100, 0), 100)
  return { left: `${left}%`, top: `${top}%` }
})

const cursorTitle = computed(() => {
  if (!state.value.cursor) return ''
  return `(${state.value.cursor.x}, ${state.value.cursor.y})`
})

async function poll(): Promise<void> {
  loading.value = true
  error.value = false
  try {
    state.value = await fetchComputerUseState()
  } catch {
    // Keep the last snapshot on a failed poll; only surface the error when
    // there is nothing to show yet.
    error.value = true
  } finally {
    loading.value = false
  }
}

let pollTimer: ReturnType<typeof setInterval> | null = null

function stopPolling(): void {
  if (pollTimer !== null) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

watch(isOpen, (open) => {
  stopPolling()
  if (open) {
    naturalSize.value = null
    void poll()
    pollTimer = setInterval(() => void poll(), POLL_INTERVAL_MS)
  }
}, { immediate: true })

onUnmounted(stopPolling)
</script>

<style scoped>
.cu-preview-overlay {
  align-items: center;
  background: var(--scrim);
  bottom: 0;
  display: flex;
  justify-content: center;
  left: 0;
  position: fixed;
  right: 0;
  top: 0;
  z-index: 1100;
}

.cu-preview {
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-modal);
  display: grid;
  gap: var(--sp-3);
  max-width: min(920px, 92vw);
  padding: var(--sp-5);
  width: 90%;
}

.cu-preview__header {
  align-items: center;
  display: flex;
  gap: var(--sp-3);
  justify-content: space-between;
}

.cu-preview__heading {
  align-items: center;
  display: flex;
  gap: var(--sp-3);
  min-width: 0;
}

.cu-preview__heading h3 {
  color: var(--text);
  font-size: var(--fs-md);
  margin: 0;
}

.cu-preview__badge {
  align-items: center;
  border: 1px solid var(--border);
  border-radius: var(--radius-pill);
  color: var(--text-muted);
  display: inline-flex;
  flex-shrink: 0;
  font-size: var(--fs-xs);
  gap: var(--sp-1);
  padding: 0.1rem 0.6rem;
}

.cu-preview__badge-dot {
  background: var(--text-dim);
  border-radius: var(--radius-full);
  height: 7px;
  width: 7px;
}

.cu-preview__badge--active {
  color: var(--ok);
}

.cu-preview__badge--active .cu-preview__badge-dot {
  background: var(--ok);
}

.cu-preview__badge--aborted {
  color: var(--danger);
}

.cu-preview__badge--aborted .cu-preview__badge-dot {
  background: var(--danger);
}

.cu-preview__stage {
  align-items: center;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  display: flex;
  justify-content: center;
  max-height: 60vh;
  min-height: 240px;
  overflow: hidden;
  position: relative;
  width: 100%;
}

.cu-preview__state {
  align-items: center;
  color: var(--text-muted);
  display: flex;
  flex-direction: column;
  font-size: var(--fs-sm);
  gap: var(--sp-3);
  justify-content: center;
  padding: var(--sp-6);
  text-align: center;
}

.cu-preview__state--empty {
  color: var(--text-dim);
}

.cu-preview__screenshot {
  display: block;
  height: auto;
  max-height: 60vh;
  max-width: 100%;
  object-fit: contain;
  width: auto;
}

.cu-preview__cursor {
  background: var(--accent);
  border: 2px solid var(--bg-surface);
  border-radius: var(--radius-full);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--accent) 45%, transparent);
  height: 12px;
  position: absolute;
  transform: translate(-50%, -50%);
  transition: left var(--dur-fast) var(--ease-standard),
              top var(--dur-fast) var(--ease-standard);
  width: 12px;
}

.cu-preview__meta {
  display: grid;
  gap: var(--sp-1);
}

.cu-preview__meta-row {
  display: flex;
  gap: var(--sp-2);
  min-width: 0;
}

.cu-preview__meta-label {
  color: var(--text-muted);
  flex-shrink: 0;
  font-size: var(--fs-xs);
  font-weight: 600;
}

.cu-preview__meta-value {
  color: var(--text);
  font-family: var(--font-mono);
  font-size: var(--fs-xs);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cu-preview-modal-enter-active,
.cu-preview-modal-leave-active {
  transition: opacity var(--dur-base) var(--ease-standard);
}

.cu-preview-modal-enter-from,
.cu-preview-modal-leave-to {
  opacity: 0;
}
</style>
