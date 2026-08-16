<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import ControlSwitch from '@/components/ControlSwitch.vue'
import MemoryLearningGroup from '@/components/settings/MemoryLearningGroup.vue'
import { getPlatform, type CodexXStatus } from '@/platform'

const { t } = useI18n()
const platform = getPlatform()
const emit = defineEmits<{
  'open-agent-configuration': []
  'open-data-maintenance': []
}>()

// Client-only "Labs" preferences. Each row reads/writes ONE localStorage key
// directly. The chat composables that consume these read the value once at
// construction and live behind an architecture import-fence, so writing the raw
// key here is the safe, decoupled way to surface them (no chat imports). Applies
// instantly; the reload-gated ones are labelled. Never enters the dirty bar.

// --- boolean '1'/'0' flags (absent => off) ---
const APPROVAL_KEY = 'opensquilla.chat.approvalPoll'
const RUNTRACE_KEY = 'opensquilla.logs.runTrace'

function readBool(key: string): boolean {
  try { return localStorage.getItem(key) === '1' } catch { return false }
}
function writeBool(key: string, on: boolean) {
  try { localStorage.setItem(key, on ? '1' : '0') } catch { /* private mode */ }
}

const approvalPoll = ref(readBool(APPROVAL_KEY))
const runTrace = ref(readBool(RUNTRACE_KEY))
function setApprovalPoll(on: boolean) { approvalPoll.value = on; writeBool(APPROVAL_KEY, on) }
function setRunTrace(on: boolean) { runTrace.value = on; writeBool(RUNTRACE_KEY, on) }

// --- foldLiveTurn: default ON; '0' is the only OFF value ---
const FOLD_KEY = 'opensquilla.chat.foldLiveTurn'
const foldOn = ref(localStorageGet(FOLD_KEY) !== '0')
function setFold(on: boolean) {
  foldOn.value = on
  try { localStorage.setItem(FOLD_KEY, on ? '1' : '0') } catch { /* private mode */ }
}

// --- answerReveal: "min,max" milliseconds, min >= 0 and max >= min ---
const REVEAL_KEY = 'opensquilla.chat.answerReveal'
const REVEAL_DEFAULT: [number, number] = [1800, 4000]
function readReveal(): [number, number] {
  const raw = localStorageGet(REVEAL_KEY)
  if (raw) {
    const parts = raw.split(',').map(Number)
    if (parts.length === 2 && parts.every(Number.isFinite) && parts[0] >= 0 && parts[1] >= parts[0]) {
      return [parts[0], parts[1]]
    }
  }
  return [...REVEAL_DEFAULT]
}
const initialReveal = readReveal()
const revealMin = ref(initialReveal[0])
const revealMax = ref(initialReveal[1])
const revealValid = computed(() =>
  Number.isFinite(revealMin.value) && Number.isFinite(revealMax.value) &&
  revealMin.value >= 0 && revealMax.value >= revealMin.value,
)
function commitReveal() {
  if (!revealValid.value) return
  try {
    localStorage.setItem(REVEAL_KEY, `${Math.round(revealMin.value)},${Math.round(revealMax.value)}`)
  } catch { /* private mode */ }
}

function localStorageGet(key: string): string | null {
  try { return localStorage.getItem(key) } catch { return null }
}

const INVESTIGATION_PROMPT_KEY = 'openstarry.prompts.investigation'
const DEFAULT_INVESTIGATION_PROMPT = '调查当前 OpenStarry Code 问题：先读取项目状态、相关配置、运行日志和实际请求链路，基于可复现证据定位根因；列出影响范围和最小修复方案，只修改必要文件；完成后运行针对性测试或构建验证，并报告变更、验证命令、结果和仍需关注的风险。缺少信息时使用明确占位符，不要凭空假设运行结果。'
const investigationPrompt = ref(localStorageGet(INVESTIGATION_PROMPT_KEY) || DEFAULT_INVESTIGATION_PROMPT)

function saveInvestigationPrompt() {
  try { localStorage.setItem(INVESTIGATION_PROMPT_KEY, investigationPrompt.value.trim() || DEFAULT_INVESTIGATION_PROMPT) } catch { /* private mode */ }
}

function resetInvestigationPrompt() {
  investigationPrompt.value = DEFAULT_INVESTIGATION_PROMPT
  saveInvestigationPrompt()
}

async function copyInvestigationPrompt() {
  try { await navigator.clipboard.writeText(investigationPrompt.value) } catch { /* clipboard may be unavailable */ }
}

const codexX = platform.codexX
const codexXStatus = ref<CodexXStatus | null>(null)
const codexXLoading = ref(false)
const codexXOpening = ref(false)
const codexXError = ref('')
const codexXHome = computed(() => codexXStatus.value?.sharedCodexHomePath || '~/.openstarry-code')
const codexXStateLabel = computed(() => {
  if (!codexX) return t('setup.advanced.codexXUnsupported')
  if (codexXLoading.value) return t('setup.advanced.codexXChecking')
  if (codexXStatus.value?.available) return t('setup.advanced.codexXReady')
  return t('setup.advanced.codexXUnavailable')
})

async function refreshCodexX() {
  if (!codexX || codexXLoading.value) return
  codexXLoading.value = true
  codexXError.value = ''
  try { codexXStatus.value = await codexX.getStatus() }
  catch (error) { codexXError.value = error instanceof Error ? error.message : String(error) }
  finally { codexXLoading.value = false }
}

async function openCodexX() {
  if (!codexX || codexXOpening.value) return
  codexXOpening.value = true
  codexXError.value = ''
  try {
    const status = await codexX.open()
    codexXStatus.value = status
    if (!status.launched) codexXError.value = t('setup.advanced.codexXUnavailable')
  } catch (error) {
    codexXError.value = error instanceof Error ? error.message : String(error)
  } finally { codexXOpening.value = false }
}

const agentConfigAriaLabel = computed(() =>
  `${t('setup.advanced.agentConfigAction')}: ${t('setup.advanced.agentConfigLabel')}`,
)

onMounted(() => { void refreshCodexX() })
</script>

<template>
  <section class="control-section">
    <div class="control-section__head">
      <h3 class="control-section__title">{{ t('setup.advanced.title') }}</h3>
      <p class="control-section__desc">{{ t('setup.advanced.desc') }} <em>{{ t('setup.advanced.reload') }}</em> {{ t('setup.advanced.descReloadSuffix') }}</p>
    </div>

    <label class="control-row">
      <div class="control-row__label-block">
        <span class="control-row__label">{{ t('setup.advanced.foldLabel') }}</span>
        <span class="control-row__desc">{{ t('setup.advanced.foldDesc') }}</span>
      </div>
      <div class="control-row__control">
        <span class="labs-hint">{{ t('setup.advanced.reload') }}</span>
        <ControlSwitch name="labs_fold_live_turn" :checked="foldOn" :aria-label="t('setup.advanced.foldAria')" @change="setFold" />
      </div>
    </label>

    <div class="control-row control-row--stack">
      <div class="control-row__label-block">
        <span id="labs-reveal-label" class="control-row__label">{{ t('setup.advanced.revealLabel') }}</span>
        <span class="control-row__desc">{{ t('setup.advanced.revealDesc') }}</span>
      </div>
      <div class="control-row__control labs-range" role="group" aria-labelledby="labs-reveal-label">
        <input
          class="control-input control-input--narrow"
          name="labs_reveal_min"
          type="number" min="0" step="100" inputmode="numeric"
          v-model.number="revealMin"
          :aria-label="t('setup.advanced.revealMinAria')"
          :aria-invalid="!revealValid ? 'true' : 'false'"
          aria-describedby="labs-reveal-error"
          @change="commitReveal"
        >
        <span class="labs-range__sep" aria-hidden="true">&ndash;</span>
        <input
          class="control-input control-input--narrow"
          name="labs_reveal_max"
          type="number" min="0" step="100" inputmode="numeric"
          v-model.number="revealMax"
          :aria-label="t('setup.advanced.revealMaxAria')"
          :aria-invalid="!revealValid ? 'true' : 'false'"
          aria-describedby="labs-reveal-error"
          @change="commitReveal"
        >
        <span v-if="!revealValid" id="labs-reveal-error" class="labs-invalid" role="alert">{{ t('setup.advanced.revealInvalid') }}</span>
      </div>
    </div>

    <label class="control-row">
      <div class="control-row__label-block">
        <span class="control-row__label">{{ t('setup.advanced.approvalPollLabel') }}</span>
        <span class="control-row__desc">{{ t('setup.advanced.approvalPollDesc') }}</span>
      </div>
      <div class="control-row__control">
        <ControlSwitch name="labs_approval_poll" :checked="approvalPoll" :aria-label="t('setup.advanced.approvalPollLabel')" @change="setApprovalPoll" />
      </div>
    </label>

    <MemoryLearningGroup />

    <div class="control-row control-row--stack" data-testid="advanced-investigation-prompt">
      <div class="control-row__label-block">
        <span class="control-row__label">{{ t('setup.advanced.investigationPromptLabel') }}</span>
        <span class="control-row__desc">{{ t('setup.advanced.investigationPromptDesc') }}</span>
      </div>
      <div class="control-row__control prompt-template-control">
        <textarea
          v-model="investigationPrompt"
          class="control-input prompt-template"
          rows="4"
          :aria-label="t('setup.advanced.investigationPromptLabel')"
          @change="saveInvestigationPrompt"
        ></textarea>
        <div class="prompt-template__actions">
          <button type="button" class="btn btn--ghost" @click="copyInvestigationPrompt">{{ t('setup.advanced.investigationPromptCopy') }}</button>
          <button type="button" class="btn btn--ghost" @click="resetInvestigationPrompt">{{ t('setup.advanced.investigationPromptReset') }}</button>
        </div>
      </div>
    </div>

    <div class="control-row control-row--stack" data-testid="advanced-codex-x">
      <div class="control-row__label-block">
        <span class="control-row__label">{{ t('setup.advanced.codexXLabel') }}</span>
        <span class="control-row__desc">{{ t('setup.advanced.codexXDesc') }}</span>
      </div>
      <div class="control-row__control codex-x-control">
        <span class="codex-x-status" :class="{ 'is-ready': codexXStatus?.available }">{{ codexXStateLabel }}</span>
        <span v-if="codexXStatus?.version" class="codex-x-version">v{{ codexXStatus.version }}</span>
        <code class="codex-x-home" :title="codexXHome">{{ codexXHome }}</code>
        <div class="codex-x-actions">
          <button type="button" class="btn btn--ghost" :disabled="codexXLoading" @click="refreshCodexX">{{ t('setup.advanced.codexXRefresh') }}</button>
          <button type="button" class="btn btn--primary" :disabled="!codexXStatus?.available || codexXOpening" :aria-busy="codexXOpening ? 'true' : undefined" @click="openCodexX">{{ codexXOpening ? t('setup.advanced.codexXOpening') : t('setup.advanced.codexXOpen') }}</button>
        </div>
        <span v-if="codexXError" class="codex-x-error" role="alert">{{ codexXError }}</span>
      </div>
    </div>

    <label class="control-row">
      <div class="control-row__label-block">
        <span class="control-row__label">{{ t('setup.advanced.runTraceLabel') }}</span>
        <span class="control-row__desc">{{ t('setup.advanced.runTraceDesc') }}</span>
      </div>
      <div class="control-row__control">
        <span class="labs-hint">{{ t('setup.advanced.reload') }}</span>
        <ControlSwitch name="labs_run_trace" :checked="runTrace" :aria-label="t('setup.advanced.runTraceAria')" @change="setRunTrace" />
      </div>
    </label>

    <div class="control-row">
      <div class="control-row__label-block">
        <span class="control-row__label">{{ t('setup.advanced.agentConfigLabel') }}</span>
        <span class="control-row__desc">{{ t('setup.advanced.agentConfigDesc') }}</span>
      </div>
      <div class="control-row__control">
        <button
          type="button"
          class="btn btn--ghost"
          :aria-label="agentConfigAriaLabel"
          @click="emit('open-agent-configuration')"
        >
          {{ t('setup.advanced.agentConfigAction') }}
        </button>
      </div>
    </div>

    <div class="control-row advanced-maintenance" data-testid="advanced-data-maintenance">
      <div class="control-row__label-block">
        <span class="control-row__label">{{ t('setup.advanced.dataMaintenanceLabel') }}</span>
        <span class="control-row__desc">{{ t('setup.advanced.dataMaintenanceDesc') }}</span>
      </div>
      <div class="control-row__control">
        <button
          type="button"
          class="btn btn--ghost"
          :aria-label="t('setup.advanced.dataMaintenanceAria')"
          @click="emit('open-data-maintenance')"
        >
          {{ t('setup.advanced.dataMaintenanceAction') }}
        </button>
      </div>
    </div>
  </section>
</template>

<style scoped>
.labs-hint {
  border: 1px solid color-mix(in srgb, var(--warn) 35%, var(--border));
  border-radius: var(--radius-full);
  color: var(--warn);
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.03em;
  padding: 1px 7px;
  text-transform: uppercase;
}

.labs-range {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-2);
}

.labs-range__sep {
  color: var(--text-dim);
}

.labs-invalid {
  color: var(--danger);
  font-size: var(--fs-xs);
  width: 100%;
}

.advanced-maintenance {
  margin-top: var(--sp-3);
  opacity: 0.82;
}

.advanced-maintenance:focus-within,
.advanced-maintenance:hover {
  opacity: 1;
}

.prompt-template-control,
.codex-x-control {
  align-items: stretch;
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
  min-width: min(100%, 420px);
}

.prompt-template {
  min-height: 96px;
  resize: vertical;
  width: min(100%, 560px);
}

.prompt-template__actions,
.codex-x-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-2);
  justify-content: flex-end;
}

.codex-x-status,
.codex-x-version {
  color: var(--text-dim);
  font-size: var(--fs-xs);
}

.codex-x-status.is-ready {
  color: var(--ok);
}

.codex-x-home {
  max-width: 100%;
  overflow-wrap: anywhere;
  white-space: normal;
}

.codex-x-error {
  color: var(--danger);
  font-size: var(--fs-xs);
}
</style>
