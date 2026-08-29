<template>
  <section class="ssh-settings" aria-labelledby="ssh-settings-title">
    <header class="ssh-settings__header">
      <div>
        <h3 id="ssh-settings-title">{{ t('settings.ssh.title') }}</h3>
        <p>{{ t('settings.ssh.subtitle') }}</p>
      </div>
      <button
        v-if="!editorOpen"
        type="button"
        class="btn btn--primary"
        data-testid="ssh-add"
        @click="openAdd"
      >
        <Icon name="plus" :size="14" aria-hidden="true" />
        {{ t('settings.ssh.add') }}
      </button>
    </header>

    <div v-if="loading" class="ssh-settings__state" role="status">
      {{ t('shared.loading') }}
    </div>
    <div v-else-if="loadError" class="ssh-settings__state" role="alert">
      <span>{{ t('settings.ssh.loadFailed') }}</span>
      <button type="button" class="btn" data-testid="ssh-retry" @click="void load()">
        {{ t('settings.ssh.retry') }}
      </button>
    </div>

    <template v-else>
      <ul v-if="hosts.length" class="ssh-list" data-testid="ssh-host-list">
        <li v-for="host in hosts" :key="host.id || host.name" class="ssh-list__row">
          <div class="ssh-list__info">
            <div class="ssh-list__name">
              <strong>{{ host.name }}</strong>
              <span class="ssh-list__badge">{{ host.port }}</span>
            </div>
            <code class="ssh-list__target">{{ targetText(host) }}</code>
          </div>
          <div class="ssh-list__actions">
            <ControlSwitch
              :checked="host.enabled"
              :aria-label="t('settings.ssh.fieldEnabled')"
              data-testid="ssh-enabled-toggle"
              @change="value => void toggleEnabled(host, value)"
            />
            <button
              type="button"
              class="btn btn--icon btn--ghost"
              :aria-label="t('settings.ssh.edit')"
              :title="t('settings.ssh.edit')"
              @click="openEdit(host)"
            >
              <Icon name="edit" :size="14" />
            </button>
            <button
              type="button"
              class="btn btn--icon btn--ghost ssh-list__delete"
              :aria-label="t('settings.ssh.delete')"
              :title="t('settings.ssh.delete')"
              @click="void remove(host)"
            >
              <Icon name="trash" :size="14" />
            </button>
          </div>
        </li>
      </ul>
      <div v-else class="ssh-settings__state ssh-settings__state--empty">
        <span>{{ t('settings.ssh.empty') }}</span>
        <small>{{ t('settings.ssh.emptyHint') }}</small>
      </div>
    </template>

    <form v-if="editorOpen" class="ssh-editor" data-testid="ssh-editor" @submit.prevent="void save()">
      <h4>{{ editingId ? t('settings.ssh.editTitle') : t('settings.ssh.newTitle') }}</h4>

      <label class="ssh-editor__field">
        <span>{{ t('settings.ssh.fieldName') }}</span>
        <input
          v-model="draft.name"
          type="text"
          :placeholder="t('settings.ssh.namePlaceholder')"
          data-testid="ssh-name"
        />
      </label>

      <label class="ssh-editor__field">
        <span>{{ t('settings.ssh.fieldHost') }}</span>
        <input
          v-model="draft.host"
          type="text"
          :placeholder="t('settings.ssh.hostPlaceholder')"
          data-testid="ssh-host"
        />
      </label>

      <div class="ssh-editor__pair">
        <label class="ssh-editor__field">
          <span>{{ t('settings.ssh.fieldPort') }}</span>
          <input
            v-model="draft.port"
            type="number"
            min="1"
            max="65535"
            :placeholder="t('settings.ssh.portPlaceholder')"
            data-testid="ssh-port"
          />
        </label>
        <label class="ssh-editor__field">
          <span>{{ t('settings.ssh.fieldUsername') }}</span>
          <input
            v-model="draft.username"
            type="text"
            :placeholder="t('settings.ssh.usernamePlaceholder')"
            data-testid="ssh-username"
          />
        </label>
      </div>

      <label class="ssh-editor__switch">
        <span>{{ t('settings.ssh.fieldEnabled') }}</span>
        <ControlSwitch v-model:checked="draft.enabled" name="ssh_host_enabled" />
      </label>

      <p v-if="formError" class="ssh-editor__error" role="alert">{{ formError }}</p>

      <div class="ssh-editor__actions">
        <button type="button" class="btn" :disabled="saving" @click="closeEditor">
          {{ t('settings.ssh.cancel') }}
        </button>
        <button type="submit" class="btn btn--primary" :disabled="saving" data-testid="ssh-save">
          {{ t('settings.ssh.save') }}
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
  createSshHost,
  deleteSshHost,
  fetchSshHosts,
  updateSshHost,
  type SshHost,
  type SshHostInput,
} from '@/utils/sshApi'

const { t } = useI18n()
const { confirm } = useConfirm()
const { pushToast } = useToasts()

const hosts = ref<SshHost[]>([])
const loading = ref(true)
const loadError = ref(false)

const editorOpen = ref(false)
const editingId = ref('')
const saving = ref(false)
const formError = ref('')

interface SshDraft {
  name: string
  host: string
  port: string
  username: string
  enabled: boolean
}

function emptyDraft(): SshDraft {
  return { name: '', host: '', port: '22', username: '', enabled: true }
}
const draft = ref<SshDraft>(emptyDraft())

async function load(): Promise<void> {
  loading.value = true
  loadError.value = false
  try {
    const data = await fetchSshHosts()
    hosts.value = data.hosts
  } catch {
    loadError.value = true
  } finally {
    loading.value = false
  }
}

function targetText(host: SshHost): string {
  const user = host.username ? `${host.username}@` : ''
  return `${user}${host.host}:${host.port}`
}

function openAdd(): void {
  editingId.value = ''
  draft.value = emptyDraft()
  formError.value = ''
  editorOpen.value = true
}

function openEdit(host: SshHost): void {
  editingId.value = host.id || host.name
  draft.value = {
    name: host.name,
    host: host.host,
    port: String(host.port),
    username: host.username,
    enabled: host.enabled,
  }
  formError.value = ''
  editorOpen.value = true
}

function closeEditor(): void {
  editorOpen.value = false
  formError.value = ''
}

function buildInput(): SshHostInput | null {
  const name = draft.value.name.trim()
  if (!name) {
    formError.value = t('settings.ssh.errNameRequired')
    return null
  }
  const host = draft.value.host.trim()
  if (!host) {
    formError.value = t('settings.ssh.errHostRequired')
    return null
  }
  const port = Number.parseInt(draft.value.port.trim() || '22', 10)
  if (!Number.isFinite(port) || port < 1 || port > 65535) {
    formError.value = t('settings.ssh.errPortInvalid')
    return null
  }
  return {
    name,
    host,
    port,
    username: draft.value.username.trim(),
    enabled: draft.value.enabled,
  }
}

async function save(): Promise<void> {
  const input = buildInput()
  if (!input || saving.value) return
  saving.value = true
  try {
    if (editingId.value) {
      await updateSshHost(editingId.value, input)
    } else {
      await createSshHost(input)
    }
    pushToast(t('settings.ssh.saved'), { tone: 'ok' })
    closeEditor()
    await load()
  } catch {
    pushToast(t('settings.ssh.saveFailed'), { tone: 'danger' })
  } finally {
    saving.value = false
  }
}

// PUT replaces the entry, so the toggle sends the full payload with `enabled`
// flipped and reloads to stay in sync with what the gateway persisted.
async function toggleEnabled(host: SshHost, enabled: boolean): Promise<void> {
  const input: SshHostInput = {
    name: host.name,
    host: host.host,
    port: host.port,
    username: host.username || undefined,
    enabled,
  }
  try {
    await updateSshHost(host.id || host.name, input)
  } catch {
    pushToast(t('settings.ssh.saveFailed'), { tone: 'danger' })
  } finally {
    await load()
  }
}

async function remove(host: SshHost): Promise<void> {
  const ok = await confirm({
    title: t('settings.ssh.deleteTitle'),
    body: t('settings.ssh.deleteBody', { name: host.name }),
    primaryLabel: t('settings.ssh.delete'),
    primaryClass: 'btn--danger',
  })
  if (!ok) return
  try {
    await deleteSshHost(host.id, host.name)
    pushToast(t('settings.ssh.deleted'), { tone: 'ok' })
    await load()
  } catch {
    pushToast(t('settings.ssh.deleteFailed'), { tone: 'danger' })
  }
}

onMounted(() => void load())
</script>

<style scoped>
.ssh-settings {
  display: grid;
  gap: var(--sp-4);
  max-width: 840px;
  margin: 0 auto;
  padding: 0.25rem 0 2rem;
}

.ssh-settings__header {
  align-items: center;
  display: flex;
  gap: var(--sp-4);
  justify-content: space-between;
  min-height: 52px;
}

.ssh-settings h3,
.ssh-settings h4,
.ssh-settings p {
  margin: 0;
}

.ssh-settings__header p {
  color: var(--text-muted);
  font-size: var(--fs-sm);
  line-height: 1.45;
}

.ssh-settings__header button {
  align-items: center;
  display: inline-flex;
  flex-shrink: 0;
  gap: var(--sp-1);
}

.ssh-settings__state {
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

.ssh-settings__state--empty {
  flex-direction: column;
  gap: var(--sp-1);
}

.ssh-settings__state--empty small {
  color: var(--text-dim);
  font-size: var(--fs-xs);
}

/* Host list */
.ssh-list {
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

.ssh-list__row {
  align-items: center;
  display: flex;
  gap: var(--sp-3);
  justify-content: space-between;
  min-height: 64px;
  padding: var(--sp-2) var(--sp-3);
  transition: background var(--dur-fast) var(--ease-standard);
}

.ssh-list__row:not(:last-child) {
  border-bottom: 1px solid var(--border);
}

.ssh-list__row:hover {
  background: var(--bg-hover);
}

.ssh-list__info {
  display: grid;
  gap: var(--sp-1);
  min-width: 0;
}

.ssh-list__name {
  align-items: center;
  display: flex;
  gap: var(--sp-2);
  min-width: 0;
}

.ssh-list__name strong {
  color: var(--text);
  font-size: var(--fs-sm);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ssh-list__badge {
  border: 1px solid var(--border);
  border-radius: var(--radius-full);
  color: var(--text-muted);
  flex-shrink: 0;
  font-size: var(--fs-xs);
  padding: 0.1rem 0.5rem;
}

.ssh-list__target {
  color: var(--text-muted);
  font-family: var(--font-mono);
  font-size: var(--fs-xs);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ssh-list__actions {
  align-items: center;
  display: flex;
  flex-shrink: 0;
  gap: var(--sp-2);
}

.ssh-list__delete {
  color: var(--danger);
}

/* Editor form */
.ssh-editor {
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  background: var(--bg-surface);
  display: grid;
  gap: var(--sp-3);
  padding: var(--sp-4);
}

.ssh-editor h4 {
  color: var(--text);
  font-size: var(--fs-md);
  margin: 0;
}

.ssh-editor__field {
  display: grid;
  gap: var(--sp-1);
}

.ssh-editor__field > span {
  color: var(--text-muted);
  font-size: var(--fs-xs);
  font-weight: 600;
}

.ssh-editor__field input {
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  color: var(--text);
  font: inherit;
  font-size: var(--fs-sm);
  min-width: 0;
  padding: var(--sp-2) var(--sp-3);
}

.ssh-editor__pair {
  display: grid;
  gap: var(--sp-3);
  grid-template-columns: 1fr 1fr;
}

.ssh-editor__switch {
  align-items: center;
  display: flex;
  gap: var(--sp-3);
  justify-content: space-between;
}

.ssh-editor__switch > span {
  color: var(--text-muted);
  font-size: var(--fs-xs);
  font-weight: 600;
}

.ssh-editor__error {
  border-inline-start: 3px solid var(--danger);
  color: var(--danger);
  font-size: var(--fs-xs);
  padding: var(--sp-1) var(--sp-2);
}

.ssh-editor__actions {
  display: flex;
  gap: var(--sp-2);
  justify-content: flex-end;
}

@media (max-width: 720px) {
  .ssh-settings__header {
    align-items: flex-start;
    flex-direction: column;
  }

  .ssh-list__row {
    align-items: flex-start;
    flex-direction: column;
  }

  .ssh-list__actions {
    justify-content: flex-end;
    width: 100%;
  }

  .ssh-editor__pair {
    grid-template-columns: 1fr;
  }
}
</style>
