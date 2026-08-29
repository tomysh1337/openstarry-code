<template>
  <section class="ftp-settings" aria-labelledby="ftp-settings-title">
    <header class="ftp-settings__header">
      <div>
        <h3 id="ftp-settings-title">{{ t('settings.ftp.title') }}</h3>
        <p>{{ t('settings.ftp.subtitle') }}</p>
      </div>
      <button
        v-if="!editorOpen"
        type="button"
        class="btn btn--primary"
        data-testid="ftp-add"
        @click="openAdd"
      >
        <Icon name="plus" :size="14" aria-hidden="true" />
        {{ t('settings.ftp.add') }}
      </button>
    </header>

    <div v-if="loading" class="ftp-settings__state" role="status">
      {{ t('shared.loading') }}
    </div>
    <div v-else-if="loadError" class="ftp-settings__state" role="alert">
      <span>{{ t('settings.ftp.loadFailed') }}</span>
      <button type="button" class="btn" data-testid="ftp-retry" @click="void load()">
        {{ t('settings.ftp.retry') }}
      </button>
    </div>

    <template v-else>
      <ul v-if="hosts.length" class="ftp-list" data-testid="ftp-host-list">
        <li v-for="host in hosts" :key="host.id || host.name" class="ftp-list__row">
          <div class="ftp-list__info">
            <div class="ftp-list__name">
              <strong>{{ host.name }}</strong>
              <span class="ftp-list__badge">{{ host.port }}</span>
              <span v-if="host.tls" class="ftp-list__badge ftp-list__badge--tls">FTPS</span>
            </div>
            <code class="ftp-list__target">{{ targetText(host) }}</code>
          </div>
          <div class="ftp-list__actions">
            <ControlSwitch
              :checked="host.enabled"
              :aria-label="t('settings.ftp.fieldEnabled')"
              data-testid="ftp-enabled-toggle"
              @change="value => void toggleEnabled(host, value)"
            />
            <button
              type="button"
              class="btn btn--icon btn--ghost"
              :aria-label="t('settings.ftp.edit')"
              :title="t('settings.ftp.edit')"
              @click="openEdit(host)"
            >
              <Icon name="edit" :size="14" />
            </button>
            <button
              type="button"
              class="btn btn--icon btn--ghost ftp-list__delete"
              :aria-label="t('settings.ftp.delete')"
              :title="t('settings.ftp.delete')"
              @click="void remove(host)"
            >
              <Icon name="trash" :size="14" />
            </button>
          </div>
        </li>
      </ul>
      <div v-else class="ftp-settings__state ftp-settings__state--empty">
        <span>{{ t('settings.ftp.empty') }}</span>
        <small>{{ t('settings.ftp.emptyHint') }}</small>
      </div>
    </template>

    <form v-if="editorOpen" class="ftp-editor" data-testid="ftp-editor" @submit.prevent="void save()">
      <h4>{{ editingId ? t('settings.ftp.editTitle') : t('settings.ftp.newTitle') }}</h4>

      <label class="ftp-editor__field">
        <span>{{ t('settings.ftp.fieldName') }}</span>
        <input
          v-model="draft.name"
          type="text"
          :placeholder="t('settings.ftp.namePlaceholder')"
          data-testid="ftp-name"
        />
      </label>

      <label class="ftp-editor__field">
        <span>{{ t('settings.ftp.fieldHost') }}</span>
        <input
          v-model="draft.host"
          type="text"
          :placeholder="t('settings.ftp.hostPlaceholder')"
          data-testid="ftp-host"
        />
      </label>

      <div class="ftp-editor__pair">
        <label class="ftp-editor__field">
          <span>{{ t('settings.ftp.fieldPort') }}</span>
          <input
            v-model="draft.port"
            type="number"
            min="1"
            max="65535"
            :placeholder="t('settings.ftp.portPlaceholder')"
            data-testid="ftp-port"
          />
        </label>
        <label class="ftp-editor__field">
          <span>{{ t('settings.ftp.fieldUsername') }}</span>
          <input
            v-model="draft.username"
            type="text"
            :placeholder="t('settings.ftp.usernamePlaceholder')"
            data-testid="ftp-username"
          />
        </label>
      </div>

      <label class="ftp-editor__field">
        <span>{{ t('settings.ftp.fieldPassword') }}</span>
        <input
          v-model="draft.password"
          type="password"
          autocomplete="new-password"
          :placeholder="t('settings.ftp.passwordPlaceholder')"
          data-testid="ftp-password"
        />
        <small class="ftp-editor__hint">{{ t('settings.ftp.passwordHint') }}</small>
      </label>

      <label class="ftp-editor__switch">
        <span>{{ t('settings.ftp.fieldTls') }}</span>
        <ControlSwitch v-model:checked="draft.tls" name="ftp_host_tls" />
      </label>

      <label class="ftp-editor__switch">
        <span>{{ t('settings.ftp.fieldEnabled') }}</span>
        <ControlSwitch v-model:checked="draft.enabled" name="ftp_host_enabled" />
      </label>

      <p v-if="formError" class="ftp-editor__error" role="alert">{{ formError }}</p>

      <div class="ftp-editor__actions">
        <button type="button" class="btn" :disabled="saving" @click="closeEditor">
          {{ t('settings.ftp.cancel') }}
        </button>
        <button type="submit" class="btn btn--primary" :disabled="saving" data-testid="ftp-save">
          {{ t('settings.ftp.save') }}
        </button>
      </div>
    </form>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import ControlSwitch from '@/components/ControlSwitch.vue'
import Icon from '@/components/Icon.vue'
import { useConfirm } from '@/composables/useConfirm'
import { useToasts } from '@/composables/useToasts'
import {
  createFtpHost,
  deleteFtpHost,
  fetchFtpHosts,
  updateFtpHost,
  type FtpHost,
  type FtpHostInput,
} from '@/utils/ftpApi'

const { t } = useI18n()
const { confirm } = useConfirm()
const { pushToast } = useToasts()

const hosts = ref<FtpHost[]>([])
const loading = ref(true)
const loadError = ref(false)

const editorOpen = ref(false)
const editingId = ref('')
const saving = ref(false)
const formError = ref('')

interface FtpDraft {
  name: string
  host: string
  port: string
  username: string
  password: string
  tls: boolean
  enabled: boolean
}

function emptyDraft(): FtpDraft {
  return { name: '', host: '', port: '21', username: '', password: '', tls: false, enabled: true }
}
const draft = ref<FtpDraft>(emptyDraft())

async function load(): Promise<void> {
  loading.value = true
  loadError.value = false
  try {
    const data = await fetchFtpHosts()
    hosts.value = data.hosts
  } catch {
    loadError.value = true
  } finally {
    loading.value = false
  }
}

function targetText(host: FtpHost): string {
  const user = host.username ? `${host.username}@` : ''
  return `${user}${host.host}:${host.port}${host.tls ? ' (FTPS)' : ''}`
}

function openAdd(): void {
  editingId.value = ''
  draft.value = emptyDraft()
  formError.value = ''
  editorOpen.value = true
}

function openEdit(host: FtpHost): void {
  editingId.value = host.id || host.name
  draft.value = {
    name: host.name,
    host: host.host,
    port: String(host.port),
    username: host.username,
    password: host.password,
    tls: host.tls,
    enabled: host.enabled,
  }
  formError.value = ''
  editorOpen.value = true
}

function closeEditor(): void {
  editorOpen.value = false
  formError.value = ''
}

function buildInput(): FtpHostInput | null {
  const name = draft.value.name.trim()
  if (!name) {
    formError.value = t('settings.ftp.errNameRequired')
    return null
  }
  const host = draft.value.host.trim()
  if (!host) {
    formError.value = t('settings.ftp.errHostRequired')
    return null
  }
  const port = Number.parseInt(draft.value.port.trim() || '21', 10)
  if (!Number.isFinite(port) || port < 1 || port > 65535) {
    formError.value = t('settings.ftp.errPortInvalid')
    return null
  }
  return {
    name,
    host,
    port,
    username: draft.value.username.trim(),
    password: draft.value.password,
    tls: draft.value.tls,
    enabled: draft.value.enabled,
  }
}

async function save(): Promise<void> {
  const input = buildInput()
  if (!input || saving.value) return
  saving.value = true
  try {
    if (editingId.value) {
      await updateFtpHost(editingId.value, input)
    } else {
      await createFtpHost(input)
    }
    pushToast(t('settings.ftp.saved'), { tone: 'ok' })
    closeEditor()
    await load()
  } catch {
    pushToast(t('settings.ftp.saveFailed'), { tone: 'danger' })
  } finally {
    saving.value = false
  }
}

// PUT replaces the entry, so the toggle sends the full payload with `enabled`
// flipped and reloads to stay in sync with what the gateway persisted.
async function toggleEnabled(host: FtpHost, enabled: boolean): Promise<void> {
  const input: FtpHostInput = {
    name: host.name,
    host: host.host,
    port: host.port,
    username: host.username || undefined,
    password: host.password,
    tls: host.tls,
    enabled,
  }
  try {
    await updateFtpHost(host.id || host.name, input)
  } catch {
    pushToast(t('settings.ftp.saveFailed'), { tone: 'danger' })
  } finally {
    await load()
  }
}

async function remove(host: FtpHost): Promise<void> {
  const ok = await confirm({
    title: t('settings.ftp.deleteTitle'),
    body: t('settings.ftp.deleteBody', { name: host.name }),
    primaryLabel: t('settings.ftp.delete'),
    primaryClass: 'btn--danger',
  })
  if (!ok) return
  try {
    await deleteFtpHost(host.id, host.name)
    pushToast(t('settings.ftp.deleted'), { tone: 'ok' })
    await load()
  } catch {
    pushToast(t('settings.ftp.deleteFailed'), { tone: 'danger' })
  }
}

onMounted(() => void load())
</script>

<style scoped>
.ftp-settings {
  display: grid;
  gap: var(--sp-4);
  max-width: 840px;
  margin: 0 auto;
  padding: 0.25rem 0 2rem;
}

.ftp-settings__header {
  align-items: center;
  display: flex;
  gap: var(--sp-4);
  justify-content: space-between;
  min-height: 52px;
}

.ftp-settings h3,
.ftp-settings h4,
.ftp-settings p {
  margin: 0;
}

.ftp-settings__header p {
  color: var(--text-muted);
  font-size: var(--fs-sm);
  line-height: 1.45;
}

.ftp-settings__header button {
  align-items: center;
  display: inline-flex;
  flex-shrink: 0;
  gap: var(--sp-1);
}

.ftp-settings__state {
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

.ftp-settings__state--empty {
  flex-direction: column;
  gap: var(--sp-1);
}

.ftp-settings__state--empty small {
  color: var(--text-dim);
  font-size: var(--fs-xs);
}

/* Host list */
.ftp-list {
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

.ftp-list__row {
  align-items: center;
  display: flex;
  gap: var(--sp-3);
  justify-content: space-between;
  min-height: 64px;
  padding: var(--sp-2) var(--sp-3);
  transition: background var(--dur-fast) var(--ease-standard);
}

.ftp-list__row:not(:last-child) {
  border-bottom: 1px solid var(--border);
}

.ftp-list__row:hover {
  background: var(--bg-hover);
}

.ftp-list__info {
  display: grid;
  gap: var(--sp-1);
  min-width: 0;
}

.ftp-list__name {
  align-items: center;
  display: flex;
  gap: var(--sp-2);
  min-width: 0;
}

.ftp-list__name strong {
  color: var(--text);
  font-size: var(--fs-sm);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ftp-list__badge {
  border: 1px solid var(--border);
  border-radius: var(--radius-full);
  color: var(--text-muted);
  flex-shrink: 0;
  font-size: var(--fs-xs);
  padding: 0.1rem 0.5rem;
}

.ftp-list__badge--tls {
  border-color: var(--accent);
  color: var(--accent);
}

.ftp-list__target {
  color: var(--text-muted);
  font-family: var(--font-mono);
  font-size: var(--fs-xs);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ftp-list__actions {
  align-items: center;
  display: flex;
  flex-shrink: 0;
  gap: var(--sp-2);
}

.ftp-list__delete {
  color: var(--danger);
}

/* Editor form */
.ftp-editor {
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  background: var(--bg-surface);
  display: grid;
  gap: var(--sp-3);
  padding: var(--sp-4);
}

.ftp-editor h4 {
  color: var(--text);
  font-size: var(--fs-md);
  margin: 0;
}

.ftp-editor__field {
  display: grid;
  gap: var(--sp-1);
}

.ftp-editor__field > span {
  color: var(--text-muted);
  font-size: var(--fs-xs);
  font-weight: 600;
}

.ftp-editor__field input {
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  color: var(--text);
  font: inherit;
  font-size: var(--fs-sm);
  min-width: 0;
  padding: var(--sp-2) var(--sp-3);
}

.ftp-editor__hint {
  color: var(--text-dim);
  font-size: var(--fs-xs);
}

.ftp-editor__pair {
  display: grid;
  gap: var(--sp-3);
  grid-template-columns: 1fr 1fr;
}

.ftp-editor__switch {
  align-items: center;
  display: flex;
  gap: var(--sp-3);
  justify-content: space-between;
}

.ftp-editor__switch > span {
  color: var(--text-muted);
  font-size: var(--fs-xs);
  font-weight: 600;
}

.ftp-editor__error {
  border-inline-start: 3px solid var(--danger);
  color: var(--danger);
  font-size: var(--fs-xs);
  padding: var(--sp-1) var(--sp-2);
}

.ftp-editor__actions {
  display: flex;
  gap: var(--sp-2);
  justify-content: flex-end;
}

@media (max-width: 720px) {
  .ftp-settings__header {
    align-items: flex-start;
    flex-direction: column;
  }

  .ftp-list__row {
    align-items: flex-start;
    flex-direction: column;
  }

  .ftp-list__actions {
    justify-content: flex-end;
    width: 100%;
  }

  .ftp-editor__pair {
    grid-template-columns: 1fr;
  }
}
</style>
