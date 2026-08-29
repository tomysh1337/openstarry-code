<template>
  <section class="mcp-settings" aria-labelledby="mcp-settings-title">
    <header class="mcp-settings__header">
      <div>
        <h3 id="mcp-settings-title">{{ t('settings.mcp.title') }}</h3>
        <p>{{ t('settings.mcp.subtitle') }}</p>
      </div>
      <button
        v-if="!editorOpen"
        type="button"
        class="btn btn--primary"
        data-testid="mcp-add"
        @click="openAdd"
      >
        <Icon name="plus" :size="14" aria-hidden="true" />
        {{ t('settings.mcp.add') }}
      </button>
    </header>

    <div v-if="loading" class="mcp-settings__state" role="status">
      {{ t('shared.loading') }}
    </div>
    <div v-else-if="loadError" class="mcp-settings__state" role="alert">
      <span>{{ t('settings.mcp.loadFailed') }}</span>
      <button type="button" class="btn" data-testid="mcp-retry" @click="void load()">
        {{ t('settings.mcp.retry') }}
      </button>
    </div>

    <template v-else>
      <section class="mcp-builtin" data-testid="mcp-builtin">
        <header class="mcp-builtin__header">
          <h4>{{ t('settings.mcp.builtin.title') }}</h4>
          <p>{{ t('settings.mcp.builtin.subtitle') }}</p>
        </header>
        <div class="mcp-builtin__item">
          <div class="mcp-builtin__info">
            <span class="mcp-builtin__icon" aria-hidden="true">
              <Icon name="target" :size="18" />
            </span>
            <div class="mcp-builtin__text">
              <strong>{{ t('settings.mcp.builtin.computerUseName') }}</strong>
              <p>{{ t('settings.mcp.builtin.computerUseDesc') }}</p>
            </div>
          </div>
          <div class="mcp-builtin__actions">
            <button
              type="button"
              class="btn"
              data-testid="mcp-builtin-computer-use-preview"
              @click="previewOpen = true"
            >
              <Icon name="monitor" :size="14" aria-hidden="true" />
              {{ t('settings.mcp.preview.open') }}
            </button>
            <button
              type="button"
              class="btn"
              :class="{ 'btn--primary': !computerUseEnabled }"
              data-testid="mcp-builtin-computer-use"
              :disabled="enablingBuiltin"
              @click="void enableBuiltinComputerUse()"
            >
              <Icon :name="computerUseEnabled ? 'check' : 'plus'" :size="14" aria-hidden="true" />
              {{
                computerUseEnabled
                  ? t('settings.mcp.builtin.enabled')
                  : t('settings.mcp.builtin.enable')
              }}
            </button>
          </div>
        </div>
      </section>

      <ul v-if="servers.length" class="mcp-list" data-testid="mcp-server-list">
        <li v-for="server in servers" :key="server.id || server.name" class="mcp-list__row">
          <div class="mcp-list__info">
            <div class="mcp-list__name">
              <strong>{{ server.name }}</strong>
              <span class="mcp-list__badge">{{ server.transport }}</span>
            </div>
            <code class="mcp-list__target">{{ targetText(server) }}</code>
          </div>
          <div class="mcp-list__actions">
            <ControlSwitch
              :checked="server.enabled"
              :aria-label="t('settings.mcp.fieldEnabled')"
              data-testid="mcp-enabled-toggle"
              @change="value => void toggleEnabled(server, value)"
            />
            <button
              type="button"
              class="btn btn--icon btn--ghost"
              :aria-label="t('settings.mcp.edit')"
              :title="t('settings.mcp.edit')"
              @click="openEdit(server)"
            >
              <Icon name="edit" :size="14" />
            </button>
            <button
              type="button"
              class="btn btn--icon btn--ghost mcp-list__delete"
              :aria-label="t('settings.mcp.delete')"
              :title="t('settings.mcp.delete')"
              @click="void remove(server)"
            >
              <Icon name="trash" :size="14" />
            </button>
          </div>
        </li>
      </ul>
      <div v-else class="mcp-settings__state mcp-settings__state--empty">
        <span>{{ t('settings.mcp.empty') }}</span>
        <small>{{ t('settings.mcp.emptyHint') }}</small>
      </div>
    </template>

    <form v-if="editorOpen" class="mcp-editor" data-testid="mcp-editor" @submit.prevent="void save()">
      <h4>{{ editingId ? t('settings.mcp.editTitle') : t('settings.mcp.newTitle') }}</h4>

      <label class="mcp-editor__field">
        <span>{{ t('settings.mcp.fieldName') }}</span>
        <input
          v-model="draft.name"
          type="text"
          :placeholder="t('settings.mcp.namePlaceholder')"
          data-testid="mcp-name"
        />
      </label>

      <div class="mcp-editor__field">
        <span id="mcp-transport-label">{{ t('settings.mcp.fieldTransport') }}</span>
        <div class="mcp-editor__segmented" role="group" aria-labelledby="mcp-transport-label">
          <button
            type="button"
            :class="{ 'is-selected': draft.transport === 'stdio' }"
            data-testid="mcp-transport-stdio"
            @click="draft.transport = 'stdio'"
          >
            {{ t('settings.mcp.transportStdio') }}
          </button>
          <button
            type="button"
            :class="{ 'is-selected': draft.transport === 'http' }"
            data-testid="mcp-transport-http"
            @click="draft.transport = 'http'"
          >
            {{ t('settings.mcp.transportHttp') }}
          </button>
        </div>
      </div>

      <template v-if="draft.transport === 'stdio'">
        <label class="mcp-editor__field">
          <span>{{ t('settings.mcp.fieldCommand') }}</span>
          <input
            v-model="draft.command"
            type="text"
            :placeholder="t('settings.mcp.commandPlaceholder')"
            data-testid="mcp-command"
          />
        </label>
        <label class="mcp-editor__field">
          <span>{{ t('settings.mcp.fieldArgs') }}</span>
          <input
            v-model="draft.args"
            type="text"
            :placeholder="t('settings.mcp.argsPlaceholder')"
            data-testid="mcp-args"
          />
        </label>
      </template>
      <label v-else class="mcp-editor__field">
        <span>{{ t('settings.mcp.fieldUrl') }}</span>
        <input
          v-model="draft.url"
          type="url"
          :placeholder="t('settings.mcp.urlPlaceholder')"
          data-testid="mcp-url"
        />
      </label>

      <label class="mcp-editor__field">
        <span>{{ t('settings.mcp.fieldEnv') }}</span>
        <textarea
          v-model="draft.envText"
          rows="3"
          :placeholder="t('settings.mcp.envPlaceholder')"
          data-testid="mcp-env"
        ></textarea>
        <small>{{ t('settings.mcp.envHint') }}</small>
      </label>

      <label class="mcp-editor__switch">
        <span>{{ t('settings.mcp.fieldEnabled') }}</span>
        <ControlSwitch v-model:checked="draft.enabled" name="mcp_server_enabled" />
      </label>

      <p v-if="formError" class="mcp-editor__error" role="alert">{{ formError }}</p>

      <div class="mcp-editor__actions">
        <button type="button" class="btn" :disabled="saving" @click="closeEditor">
          {{ t('settings.mcp.cancel') }}
        </button>
        <button type="submit" class="btn btn--primary" :disabled="saving" data-testid="mcp-save">
          {{ t('settings.mcp.save') }}
        </button>
      </div>
    </form>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import ControlSwitch from '@/components/ControlSwitch.vue'
import Icon from '@/components/Icon.vue'
import { useConfirm } from '@/composables/useConfirm'
import { useToasts } from '@/composables/useToasts'
import {
  createMcpServer,
  deleteMcpServer,
  fetchMcpServers,
  updateMcpServer,
  type McpServer,
  type McpServerInput,
  type McpTransport,
} from '@/utils/mcpApi'

const { t } = useI18n()
const { confirm } = useConfirm()
const { pushToast } = useToasts()

const servers = ref<McpServer[]>([])
const loading = ref(true)
const loadError = ref(false)

const editorOpen = ref(false)
const editingId = ref('')
const saving = ref(false)
const formError = ref('')

interface McpDraft {
  name: string
  transport: McpTransport
  command: string
  args: string
  url: string
  envText: string
  enabled: boolean
}

function emptyDraft(): McpDraft {
  return { name: '', transport: 'stdio', command: '', args: '', url: '', envText: '', enabled: true }
}
const draft = ref<McpDraft>(emptyDraft())

// Built-in servers: one-click enablement of servers bundled with the gateway.
const BUILTIN_COMPUTER_USE_NAME = 'openstarry-computer-use'
const enablingBuiltin = ref(false)
// Live computer-use preview modal (screenshot + virtual cursor + state).
const previewOpen = ref(false)

const computerUseEnabled = computed(() =>
  servers.value.some((server) => server.name === BUILTIN_COMPUTER_USE_NAME),
)

/**
 * Create the built-in computer-use MCP server entry. The command stays the
 * portable "python" placeholder — never hardcode an interpreter path; the
 * gateway environment decides which python resolves at spawn time.
 */
async function enableBuiltinComputerUse(): Promise<void> {
  if (enablingBuiltin.value) return
  if (computerUseEnabled.value) {
    pushToast(t('settings.mcp.builtin.alreadyEnabled'), { tone: 'ok' })
    return
  }
  enablingBuiltin.value = true
  try {
    await createMcpServer({
      name: BUILTIN_COMPUTER_USE_NAME,
      transport: 'stdio',
      command: 'python',
      args: ['-m', 'openstarry_code.computer_use.mcp_server'],
      enabled: true,
    })
    pushToast(t('settings.mcp.builtin.enabled'), { tone: 'ok' })
    await load()
  } catch {
    pushToast(t('settings.mcp.builtin.enableFailed'), { tone: 'danger' })
  } finally {
    enablingBuiltin.value = false
  }
}

async function load(): Promise<void> {
  loading.value = true
  loadError.value = false
  try {
    const data = await fetchMcpServers()
    servers.value = data.servers
  } catch {
    loadError.value = true
  } finally {
    loading.value = false
  }
}

function targetText(server: McpServer): string {
  if (server.transport === 'stdio') {
    return [server.command, ...server.args].filter(Boolean).join(' ')
  }
  return server.url ?? ''
}

function envToText(env: Record<string, string>): string {
  return Object.entries(env).map(([key, value]) => `${key}=${value}`).join('\n')
}

/** One KEY=VALUE per line; null when a line is malformed. */
function parseEnvText(text: string): Record<string, string> | null {
  const env: Record<string, string> = {}
  for (const raw of text.split('\n')) {
    const line = raw.trim()
    if (!line) continue
    const eq = line.indexOf('=')
    if (eq <= 0) return null
    const key = line.slice(0, eq).trim()
    if (!key) return null
    env[key] = line.slice(eq + 1).trim()
  }
  return env
}

function isHttpUrl(value: string): boolean {
  try {
    const parsed = new URL(value)
    return (parsed.protocol === 'http:' || parsed.protocol === 'https:') && !!parsed.hostname
  } catch {
    return false
  }
}

function openAdd(): void {
  editingId.value = ''
  draft.value = emptyDraft()
  formError.value = ''
  editorOpen.value = true
}

function openEdit(server: McpServer): void {
  editingId.value = server.id || server.name
  draft.value = {
    name: server.name,
    transport: server.transport,
    command: server.command ?? '',
    args: server.args.join(' '),
    url: server.url ?? '',
    envText: envToText(server.env),
    enabled: server.enabled,
  }
  formError.value = ''
  editorOpen.value = true
}

function closeEditor(): void {
  editorOpen.value = false
  formError.value = ''
}

function buildInput(): McpServerInput | null {
  const name = draft.value.name.trim()
  if (!name) {
    formError.value = t('settings.mcp.errNameRequired')
    return null
  }
  const env = parseEnvText(draft.value.envText)
  if (env === null) {
    formError.value = t('settings.mcp.errEnvInvalid')
    return null
  }
  if (draft.value.transport === 'stdio') {
    const command = draft.value.command.trim()
    if (!command) {
      formError.value = t('settings.mcp.errCommandRequired')
      return null
    }
    return {
      name,
      transport: 'stdio',
      command,
      args: draft.value.args.trim().split(/\s+/).filter(Boolean),
      env,
      enabled: draft.value.enabled,
    }
  }
  const url = draft.value.url.trim()
  if (!isHttpUrl(url)) {
    formError.value = t('settings.mcp.errUrlRequired')
    return null
  }
  return { name, transport: 'http', url, env, enabled: draft.value.enabled }
}

async function save(): Promise<void> {
  const input = buildInput()
  if (!input || saving.value) return
  saving.value = true
  try {
    if (editingId.value) {
      await updateMcpServer(editingId.value, input)
    } else {
      await createMcpServer(input)
    }
    pushToast(t('settings.mcp.saved'), { tone: 'ok' })
    closeEditor()
    await load()
  } catch {
    pushToast(t('settings.mcp.saveFailed'), { tone: 'danger' })
  } finally {
    saving.value = false
  }
}

// PUT replaces the entry, so the toggle sends the full payload with `enabled`
// flipped and reloads to stay in sync with what the gateway persisted.
async function toggleEnabled(server: McpServer, enabled: boolean): Promise<void> {
  const input: McpServerInput = {
    name: server.name,
    transport: server.transport,
    command: server.command ?? undefined,
    args: server.args,
    env: server.env,
    url: server.url ?? undefined,
    enabled,
  }
  try {
    await updateMcpServer(server.id || server.name, input)
  } catch {
    pushToast(t('settings.mcp.saveFailed'), { tone: 'danger' })
  } finally {
    await load()
  }
}

async function remove(server: McpServer): Promise<void> {
  const ok = await confirm({
    title: t('settings.mcp.deleteTitle'),
    body: t('settings.mcp.deleteBody', { name: server.name }),
    primaryLabel: t('settings.mcp.delete'),
    primaryClass: 'btn--danger',
  })
  if (!ok) return
  try {
    await deleteMcpServer(server.id, server.name)
    pushToast(t('settings.mcp.deleted'), { tone: 'ok' })
    await load()
  } catch {
    pushToast(t('settings.mcp.deleteFailed'), { tone: 'danger' })
  }
}

onMounted(() => void load())
</script>

<style scoped>
.mcp-settings {
  display: grid;
  gap: var(--sp-4);
  max-width: 840px;
  margin: 0 auto;
  padding: 0.25rem 0 2rem;
}

.mcp-settings__header {
  align-items: center;
  display: flex;
  gap: var(--sp-4);
  justify-content: space-between;
  min-height: 52px;
}

.mcp-settings h3,
.mcp-settings h4,
.mcp-settings p {
  margin: 0;
}

.mcp-settings__header p {
  color: var(--text-muted);
  font-size: var(--fs-sm);
  line-height: 1.45;
}

.mcp-settings__header button {
  align-items: center;
  display: inline-flex;
  flex-shrink: 0;
  gap: var(--sp-1);
}

.mcp-settings__state {
  align-items: center;
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  background: var(--bg-surface);
  color: var(--text-muted);
  display: flex;
  font-size: var(--fs-sm);
  gap: var(--sp-3);
  justify-content: center;
  padding: var(--sp-5);
  text-align: center;
}

.mcp-settings__state--empty {
  flex-direction: column;
  gap: var(--sp-1);
}

.mcp-settings__state--empty small {
  color: var(--text-dim);
  font-size: var(--fs-xs);
}

/* Built-in servers card */
.mcp-builtin {
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  background: var(--bg-surface);
  display: grid;
  gap: var(--sp-3);
  padding: var(--sp-4);
}

.mcp-builtin__header {
  display: grid;
  gap: var(--sp-1);
}

.mcp-builtin__header h4 {
  color: var(--text);
  font-size: var(--fs-md);
}

.mcp-builtin__header p {
  color: var(--text-muted);
  font-size: var(--fs-xs);
  line-height: 1.45;
}

.mcp-builtin__item {
  align-items: center;
  display: flex;
  gap: var(--sp-3);
  justify-content: space-between;
}

.mcp-builtin__info {
  align-items: center;
  display: flex;
  gap: var(--sp-3);
  min-width: 0;
}

.mcp-builtin__icon {
  align-items: center;
  background: var(--bg-hover);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  color: var(--accent);
  display: inline-flex;
  flex-shrink: 0;
  height: 36px;
  justify-content: center;
  width: 36px;
}

.mcp-builtin__text {
  display: grid;
  gap: 2px;
  min-width: 0;
}

.mcp-builtin__text strong {
  color: var(--text);
  font-size: var(--fs-sm);
}

.mcp-builtin__text p {
  color: var(--text-muted);
  font-size: var(--fs-xs);
  line-height: 1.45;
}

.mcp-builtin__actions {
  align-items: center;
  display: flex;
  flex-shrink: 0;
  flex-wrap: wrap;
  gap: var(--sp-2);
}

.mcp-builtin button {
  align-items: center;
  display: inline-flex;
  flex-shrink: 0;
  gap: var(--sp-1);
}

.mcp-builtin button:disabled {
  opacity: 0.6;
}

/* Server list */
.mcp-list {
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  background: var(--bg-surface);
  display: grid;
  gap: 0;
  list-style: none;
  margin: 0;
  overflow: hidden;
  padding: 0;
}

.mcp-list__row {
  align-items: center;
  display: flex;
  gap: var(--sp-3);
  justify-content: space-between;
  min-height: 64px;
  padding: var(--sp-2) var(--sp-3);
  transition: background var(--dur-fast) var(--ease-standard);
}

.mcp-list__row:not(:last-child) {
  border-bottom: 1px solid var(--border);
}

.mcp-list__row:hover {
  background: var(--bg-hover);
}

.mcp-list__info {
  display: grid;
  gap: var(--sp-1);
  min-width: 0;
}

.mcp-list__name {
  align-items: center;
  display: flex;
  gap: var(--sp-2);
  min-width: 0;
}

.mcp-list__name strong {
  color: var(--text);
  font-size: var(--fs-sm);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mcp-list__badge {
  border: 1px solid var(--border);
  border-radius: var(--radius-full);
  color: var(--text-muted);
  flex-shrink: 0;
  font-size: var(--fs-xs);
  padding: 0.1rem 0.5rem;
}

.mcp-list__target {
  color: var(--text-muted);
  font-family: var(--font-mono);
  font-size: var(--fs-xs);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mcp-list__actions {
  align-items: center;
  display: flex;
  flex-shrink: 0;
  gap: var(--sp-2);
}

.mcp-list__delete {
  color: var(--danger);
}

/* Editor form */
.mcp-editor {
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  background: var(--bg-surface);
  display: grid;
  gap: var(--sp-3);
  padding: var(--sp-4);
}

.mcp-editor h4 {
  color: var(--text);
  font-size: var(--fs-md);
  margin: 0;
}

.mcp-editor__field {
  display: grid;
  gap: var(--sp-1);
}

.mcp-editor__field > span {
  color: var(--text-muted);
  font-size: var(--fs-xs);
  font-weight: 600;
}

.mcp-editor__field input,
.mcp-editor__field textarea {
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  color: var(--text);
  font: inherit;
  font-size: var(--fs-sm);
  min-width: 0;
  padding: var(--sp-2) var(--sp-3);
}

.mcp-editor__field textarea {
  font-family: var(--font-mono);
  resize: vertical;
}

.mcp-editor__field small {
  color: var(--text-dim);
  font-size: var(--fs-xs);
}

.mcp-editor__segmented {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2px;
  max-width: 340px;
  padding: 3px;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  background: var(--bg-hover);
}

.mcp-editor__segmented button {
  border: 0;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  font: inherit;
  font-size: var(--fs-xs);
  font-weight: 600;
  min-height: 32px;
  padding: 0 var(--sp-3);
  transition: background var(--dur-fast) var(--ease-standard),
              color var(--dur-fast) var(--ease-standard);
}

.mcp-editor__segmented button.is-selected {
  background: var(--bg-surface);
  color: var(--text);
}

.mcp-editor__switch {
  align-items: center;
  display: flex;
  gap: var(--sp-3);
  justify-content: space-between;
}

.mcp-editor__switch > span {
  color: var(--text-muted);
  font-size: var(--fs-xs);
  font-weight: 600;
}

.mcp-editor__error {
  border-inline-start: 3px solid var(--danger);
  color: var(--danger);
  font-size: var(--fs-xs);
  padding: var(--sp-1) var(--sp-2);
}

.mcp-editor__actions {
  display: flex;
  gap: var(--sp-2);
  justify-content: flex-end;
}

@media (max-width: 720px) {
  .mcp-builtin__item {
    align-items: flex-start;
    flex-direction: column;
  }

  .mcp-settings__header {
    align-items: flex-start;
    flex-direction: column;
  }

  .mcp-list__row {
    align-items: flex-start;
    flex-direction: column;
  }

  .mcp-list__actions {
    justify-content: flex-end;
    width: 100%;
  }
}
</style>
