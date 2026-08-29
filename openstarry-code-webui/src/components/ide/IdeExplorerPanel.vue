<template>
  <section
    class="ide-panel"
    :class="{ 'is-collapsed': collapsed, 'is-resizing': resizing }"
    :style="collapsed ? undefined : { width: `${width}px` }"
    data-testid="ide-panel"
  >
    <!-- Collapsed strip: a slim vertical rail with an expand button. -->
    <div v-if="collapsed" class="ide-panel__strip">
      <button
        type="button"
        class="ide-panel__toggle"
        :title="t('ide.expand')"
        :aria-label="t('ide.expand')"
        @click="expand"
      >
        <Icon name="panel-right-open" :size="16" />
      </button>
    </div>

    <template v-else>
      <!-- Left-edge resizer: dragging left grows the panel. -->
      <div
        class="ide-panel__resizer"
        role="separator"
        aria-orientation="vertical"
        :title="t('ide.resize')"
        @pointerdown="onResizeStart"
        @dblclick="resetWidth"
      />

      <header class="ide-panel__header">
        <div class="ide-panel__title">
          <Icon name="fileCode" :size="14" />
          <span>{{ t('ide.title') }}</span>
        </div>
        <div class="ide-panel__actions">
          <button
            type="button"
            class="ide-panel__action"
            :title="t('ide.refresh')"
            :aria-label="t('ide.refresh')"
            @click="refreshActive"
          >
            <Icon name="refresh" :size="14" />
          </button>
          <button
            type="button"
            class="ide-panel__action"
            :title="t('ide.collapse')"
            :aria-label="t('ide.collapse')"
            @click="collapse"
          >
            <Icon name="panel-right-close" :size="14" />
          </button>
        </div>
      </header>

      <div class="ide-panel__tabsbar">
        <div class="ide-panel__tabs" role="tablist" :aria-label="t('ide.title')">
          <button
            type="button"
            role="tab"
            class="ide-panel__tab"
            :class="{ 'is-active': activeTab === 'docs' }"
            :aria-selected="activeTab === 'docs'"
            @click="setTab('docs')"
          >
            <Icon name="fileText" :size="13" />
            <span>{{ t('ide.tabDocs') }}</span>
          </button>
          <button
            type="button"
            role="tab"
            class="ide-panel__tab"
            :class="{ 'is-active': activeTab === 'code' }"
            :aria-selected="activeTab === 'code'"
            @click="setTab('code')"
          >
            <Icon name="fileCode" :size="13" />
            <span>{{ t('ide.tabCode') }}</span>
          </button>
          <button
            type="button"
            role="tab"
            class="ide-panel__tab"
            :class="{ 'is-active': activeTab === 'remote' }"
            :aria-selected="activeTab === 'remote'"
            @click="setTab('remote')"
          >
            <Icon name="cloud" :size="13" />
            <span>{{ t('ide.tabRemote') }}</span>
          </button>
          <button
            ref="changesBtnRef"
            type="button"
            class="ide-panel__changes-btn"
            :class="{ 'is-active': changesOpen }"
            :title="t('ide.changes.title')"
            :aria-label="t('ide.changes.title')"
            :aria-expanded="changesOpen"
            @click="toggleChanges"
          >
            <Icon name="clock" :size="13" />
            <span v-if="recentChanges.length > 0" class="ide-panel__changes-badge">{{ changesBadgeLabel }}</span>
          </button>
        </div>

        <!-- Recent AI changes popover -->
        <Transition name="ide-fade">
          <div
            v-if="changesOpen"
            ref="changesRef"
            class="ide-changes"
            role="dialog"
            :aria-label="t('ide.changes.title')"
          >
            <div class="ide-changes__head">
              <span class="ide-changes__title">{{ t('ide.changes.title') }}</span>
              <button
                type="button"
                class="ide-changes__close"
                :title="t('ide.changes.close')"
                :aria-label="t('ide.changes.close')"
                @click="changesOpen = false"
              >
                <Icon name="x" :size="12" />
              </button>
            </div>
            <div v-if="recentChanges.length === 0" class="ide-changes__empty">{{ t('ide.changes.empty') }}</div>
            <ul v-else class="ide-changes__list">
              <li v-for="item in recentChanges" :key="item.path">
                <button
                  type="button"
                  class="ide-changes__item"
                  :title="item.path"
                  @click="openChangedFile(item)"
                >
                  <span class="ide-changes__icon" aria-hidden="true"><Icon :name="changeIcon(item.path)" :size="14" /></span>
                  <span class="ide-changes__meta">
                    <span class="ide-changes__name">{{ fileNameOf(item.path) }}</span>
                    <span class="ide-changes__path">{{ item.path }}</span>
                  </span>
                  <span class="ide-changes__time">{{ relativeTime(item.mtime) }}</span>
                </button>
              </li>
            </ul>
          </div>
        </Transition>
      </div>

      <div class="ide-panel__body">
        <!-- Docs tab: rendered handoff Markdown -->
        <div v-show="activeTab === 'docs'" class="ide-panel__doc">
          <div v-if="docLoading" class="ide-panel__empty">{{ t('ide.loading') }}</div>
          <div v-else-if="docError" class="ide-panel__empty">
            <p>{{ docError }}</p>
            <button type="button" class="btn btn--ghost" @click="loadDoc">
              {{ t('ide.retry') }}
            </button>
          </div>
          <div v-else-if="docHtml" class="ide-markdown" v-html="docHtml" />
          <div v-else class="ide-panel__empty">{{ t('ide.noHandoff') }}</div>
        </div>

        <!-- Code tab: source tree + file viewer -->
        <div v-show="activeTab === 'code'" class="ide-panel__code">
          <div class="ide-tree" @scroll="closeMenu">
            <div class="ide-tree__root">
              <Icon name="folder" :size="14" />
              <span class="ide-tree__root-name">{{ rootName || '…' }}</span>
            </div>
            <div v-if="treeLoading" class="ide-panel__empty">{{ t('ide.loading') }}</div>
            <div v-else-if="treeError" class="ide-panel__empty">
              <p>{{ treeError }}</p>
              <button type="button" class="btn btn--ghost" @click="loadTree">
                {{ t('ide.retry') }}
              </button>
            </div>
            <ul v-else class="ide-tree__list" role="tree">
              <li
                v-for="row in rows"
                :key="row.editing ? 'row-editing' : row.entry.path"
                role="treeitem"
              >
                <!-- Inline editor for create / rename (one at a time) -->
                <div
                  v-if="row.editing || isRenaming(row.entry)"
                  class="ide-tree__row ide-tree__row--editing"
                  :style="{ paddingInlineStart: `${12 + row.depth * 14}px` }"
                >
                  <Icon :name="editingIcon" :size="13" class="ide-tree__file-icon" />
                  <input
                    :ref="setEditingInput"
                    v-model="editingValue"
                    class="ide-tree__input"
                    type="text"
                    :placeholder="t('ide.namePlaceholder')"
                    spellcheck="false"
                    @keydown.enter.prevent="commitEditing"
                    @keydown.esc.prevent="cancelEditing"
                    @blur="commitEditing"
                  >
                </div>
                <button
                  v-else
                  type="button"
                  class="ide-tree__row"
                  :class="{ 'is-selected': selectedPath === row.entry.path }"
                  :style="{ paddingInlineStart: `${12 + row.depth * 14}px` }"
                  :title="row.entry.path"
                  @click="onRowClick(row.entry)"
                  @contextmenu.prevent="openMenu(row.entry, $event)"
                >
                  <Icon
                    v-if="row.entry.type === 'dir'"
                    :name="isDirExpanded(row.entry.path) ? 'chevronDown' : 'chevronRight'"
                    :size="12"
                    class="ide-tree__chevron"
                  />
                  <Icon
                    v-else
                    :name="row.entry.language ? 'fileCode' : 'fileText'"
                    :size="13"
                    class="ide-tree__file-icon"
                  />
                  <span class="ide-tree__label">{{ row.entry.name }}</span>
                  <span
                    v-if="row.entry.type === 'file' && isChangedPath(row.entry.path)"
                    class="ide-tree__dot"
                    aria-hidden="true"
                  />
                </button>
              </li>
              <li v-if="rows.length === 0" class="ide-panel__empty">{{ t('ide.emptyTree') }}</li>
            </ul>
          </div>

          <div class="ide-viewer">
            <div v-if="fileLoading" class="ide-panel__empty">{{ t('ide.loading') }}</div>
            <div v-else-if="fileError" class="ide-panel__empty">
              <p>{{ fileError }}</p>
            </div>
            <template v-else-if="file">
                <div class="ide-viewer__bar">
                  <span class="ide-viewer__name">{{ file.name }}</span>
                  <span v-if="file.truncated" class="ide-viewer__truncated">{{ t('ide.fileTooLarge') }}</span>
                  <span
                    v-if="diffChanged"
                    class="ide-viewer__diff"
                    role="img"
                    :title="t('ide.diff.legend')"
                  >
                    <span class="ide-viewer__diff-chip ide-viewer__diff-chip--add">+{{ diffSummary?.added ?? 0 }}</span>
                    <span class="ide-viewer__diff-chip ide-viewer__diff-chip--mod">±{{ diffSummary?.modified ?? 0 }}</span>
                    <span class="ide-viewer__diff-chip ide-viewer__diff-chip--del">−{{ diffSummary?.removed ?? 0 }}</span>
                  </span>
                </div>
                <div v-if="file.binary" class="ide-panel__empty">{{ t('ide.binaryFile') }}</div>
                <pre v-else-if="file.content !== undefined" class="ide-viewer__pre"><code class="hljs" v-html="fileHtmlWithDiffs" /></pre>
              </template>
            <div v-else class="ide-panel__empty">{{ t('ide.noSelection') }}</div>
          </div>
        </div>

        <!-- Remote tab: browse SSH / FTP / WSL / MCP / Git clone file systems -->
        <div v-show="activeTab === 'remote'" class="ide-panel__remote">
          <div class="ide-remote__bar">
            <div class="ide-remote__transports" role="tablist" :aria-label="t('ide.tabRemote')">
              <button
                v-for="tp in REMOTE_TRANSPORTS"
                :key="tp"
                type="button"
                role="tab"
                class="ide-remote__transport"
                :class="{ 'is-active': remoteType === tp }"
                :aria-selected="remoteType === tp"
                @click="setRemoteType(tp)"
              >
                {{ t('ide.remote.' + tp) }}
              </button>
            </div>
            <select
              v-if="remoteServerOptions.length > 0"
              v-model="remoteSourceId"
              class="ide-remote__source"
              :aria-label="t('ide.remote.selectServer')"
              @change="onRemoteSourceChange"
            >
              <option v-for="s in remoteServerOptions" :key="s.id" :value="s.id">{{ s.name }}</option>
            </select>
          </div>

          <div v-if="remoteServerOptions.length === 0" class="ide-remote__empty">
            <p>
              {{
                remoteType === 'git'
                  ? t('ide.remote.noGitRepos')
                  : t('ide.remote.noServers', { transport: t('ide.remote.' + remoteType) })
              }}
            </p>
            <button
              v-if="remoteSettingsPath"
              type="button"
              class="btn btn--ghost"
              @click="openRemoteSettings"
            >
              {{ t('ide.remote.openSettings') }}
            </button>
          </div>

          <template v-else>
            <div v-if="remoteLoading" class="ide-panel__empty">{{ t('ide.loading') }}</div>
            <div v-else-if="remoteError" class="ide-panel__empty">
              <p>{{ remoteError }}</p>
              <button type="button" class="btn btn--ghost" @click="loadRemoteSources">
                {{ t('ide.retry') }}
              </button>
            </div>
            <div v-else class="ide-tree ide-tree--remote" @scroll="closeMenu">
              <div class="ide-tree__root">
                <Icon name="cloud" :size="14" />
                <span class="ide-tree__root-name">{{ remoteSourceName || '…' }}</span>
              </div>
              <ul v-if="remoteRows.length > 0" class="ide-tree__list" role="tree">
                <li v-for="row in remoteRows" :key="row.entry.path" role="treeitem">
                  <button
                    type="button"
                    class="ide-tree__row"
                    :class="{ 'is-selected': remoteSelected === row.entry.path }"
                    :style="{ paddingInlineStart: `${12 + row.depth * 14}px` }"
                    :title="row.entry.path"
                    @click="onRemoteRowClick(row.entry)"
                  >
                    <Icon
                      v-if="row.entry.type === 'dir'"
                      :name="isRemoteDirExpanded(row.entry.path) ? 'chevronDown' : 'chevronRight'"
                      :size="12"
                      class="ide-tree__chevron"
                    />
                    <Icon
                      v-else
                      :name="row.entry.language ? 'fileCode' : 'fileText'"
                      :size="13"
                      class="ide-tree__file-icon"
                    />
                    <span class="ide-tree__label">{{ row.entry.name }}</span>
                  </button>
                </li>
              </ul>
              <div v-else class="ide-panel__empty">{{ t('ide.emptyTree') }}</div>
            </div>

            <div class="ide-viewer">
              <div v-if="remoteFileLoading" class="ide-panel__empty">{{ t('ide.loading') }}</div>
              <div v-else-if="remoteFileError" class="ide-panel__empty">
                <p>{{ remoteFileError }}</p>
              </div>
              <template v-else-if="remoteFile">
                <div class="ide-viewer__bar">
                  <span class="ide-viewer__name">{{ remoteFile.name }}</span>
                  <span v-if="remoteFile.truncated" class="ide-viewer__truncated">{{ t('ide.fileTooLarge') }}</span>
                </div>
                <div v-if="remoteFile.binary" class="ide-panel__empty">{{ t('ide.binaryFile') }}</div>
                <pre v-else-if="remoteFile.content !== undefined" class="ide-viewer__pre"><code class="hljs" v-html="remoteFileHtml" /></pre>
              </template>
              <div v-else class="ide-panel__empty">{{ t('ide.noSelection') }}</div>
            </div>
          </template>
        </div>
      </div>
    </template>
  </section>

  <!-- Explorer row context menu (fixed-position, teleported out of the panel) -->
  <Teleport to="body">
    <div
      v-if="menu"
      ref="menuRef"
      class="ide-context-menu"
      role="menu"
      :aria-label="t('ide.title')"
      :style="{ left: `${menu.x}px`, top: `${menu.y}px` }"
      @contextmenu.prevent
    >
      <button type="button" class="ide-context-menu__item" role="menuitem" @click="startCreate('create-file')">
        <span class="ide-context-menu__icon" aria-hidden="true"><Icon name="fileText" :size="15" /></span>
        <span class="ide-context-menu__label">{{ t('ide.newFile') }}</span>
      </button>
      <button type="button" class="ide-context-menu__item" role="menuitem" @click="startCreate('create-dir')">
        <span class="ide-context-menu__icon" aria-hidden="true"><Icon name="folder" :size="15" /></span>
        <span class="ide-context-menu__label">{{ t('ide.newFolder') }}</span>
      </button>
      <button type="button" class="ide-context-menu__item" role="menuitem" @click="startRename">
        <span class="ide-context-menu__icon" aria-hidden="true"><Icon name="pencil" :size="15" /></span>
        <span class="ide-context-menu__label">{{ t('ide.rename') }}</span>
      </button>
      <button type="button" class="ide-context-menu__item ide-context-menu__item--danger" role="menuitem" @click="deleteFromMenu">
        <span class="ide-context-menu__icon" aria-hidden="true"><Icon name="trash" :size="15" /></span>
        <span class="ide-context-menu__label">{{ t('ide.delete') }}</span>
      </button>
      <div class="ide-context-menu__divider" role="separator" />
      <button type="button" class="ide-context-menu__item" role="menuitem" @click="copyAbsolutePathFromMenu">
        <span class="ide-context-menu__icon" aria-hidden="true"><Icon name="copy" :size="15" /></span>
        <span class="ide-context-menu__label">{{ t('ide.copyPath') }}</span>
      </button>
      <button type="button" class="ide-context-menu__item" role="menuitem" @click="copyRelativePathFromMenu">
        <span class="ide-context-menu__icon" aria-hidden="true"><Icon name="copy" :size="15" /></span>
        <span class="ide-context-menu__label">{{ t('ide.copyRelativePath') }}</span>
      </button>
      <button type="button" class="ide-context-menu__item" role="menuitem" @click="openAddToChat">
        <span class="ide-context-menu__icon" aria-hidden="true"><Icon name="chat" :size="15" /></span>
        <span class="ide-context-menu__label">{{ t('ide.addToChat') }}</span>
      </button>
    </div>
  </Teleport>

  <!-- "Add to conversation" chooser: insert the path or a content reference -->
  <Teleport to="body">
    <Transition name="ide-fade">
      <div v-if="addToChatOpen" class="ide-modal-overlay" @click="closeAddToChat">
        <div
          class="ide-modal"
          role="dialog"
          aria-modal="true"
          :aria-label="t('ide.addToChat')"
          @click.stop
        >
          <h3 class="ide-modal__title">{{ t('ide.addToChat') }}</h3>
          <p class="ide-modal__name">{{ addChatTarget?.name }}</p>
          <button type="button" class="ide-context-menu__item" role="menuitem" @click="insertEntryPath">
            <span class="ide-context-menu__icon" aria-hidden="true"><Icon name="fileText" :size="15" /></span>
            <span class="ide-context-menu__label">{{ t('ide.insertPath') }}</span>
          </button>
          <button
            v-if="addChatTarget?.type === 'file'"
            type="button"
            class="ide-context-menu__item"
            role="menuitem"
            @click="insertEntryContent"
          >
            <span class="ide-context-menu__icon" aria-hidden="true"><Icon name="fileCode" :size="15" /></span>
            <span class="ide-context-menu__label">{{ t('ide.insertContent') }}</span>
          </button>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import type { ComponentPublicInstance } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import hljs from 'highlight.js/lib/common'
import Icon from '../Icon.vue'
import type { IconName } from '@/utils/icons'
import { useChatTextRendering } from '@/composables/chat/useChatTextRendering'
import { useConfirm } from '@/composables/useConfirm'
import { useToasts } from '@/composables/useToasts'
import { requestComposerInsert } from '@/utils/chat/composerInsert'
import {
  createIdeEntry,
  deleteIdeEntry,
  fetchIdeChanges,
  fetchIdeDiff,
  fetchIdeFile,
  fetchIdeHandoff,
  fetchIdeRoot,
  fetchIdeTree,
  renameIdeEntry,
  type IdeChangeFile,
  type IdeDiffEntry,
  type IdeDiffResponse,
  type IdeFileResponse,
  type IdeTreeEntry,
} from '@/utils/ideApi'
import {
  fetchRemoteFile,
  fetchRemoteSources,
  fetchRemoteTree,
  type RemoteFileResponse,
  type RemoteSourcesResponse,
  type RemoteTreeEntry,
  type RemoteType,
} from '@/utils/remoteApi'

const { t } = useI18n()
const { renderMarkdown } = useChatTextRendering()
const { confirm } = useConfirm()
const { pushToast } = useToasts()
const router = useRouter()

// ---------------------------------------------------------------------------
// Persisted panel state
// ---------------------------------------------------------------------------

const WIDTH_KEY = 'opensquilla.idePanel.width'
const COLLAPSED_KEY = 'opensquilla.idePanel.collapsed'
const TAB_KEY = 'opensquilla.idePanel.tab'

const DEFAULT_WIDTH = 360
const MIN_WIDTH = 240
const MAX_WIDTH = 720

function readStoredNumber(key: string, fallback: number): number {
  try {
    const parsed = Number.parseInt(localStorage.getItem(key) || '', 10)
    return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback
  } catch {
    return fallback
  }
}

function readStoredBoolean(key: string, fallback: boolean): boolean {
  try {
    const stored = localStorage.getItem(key)
    return stored === null ? fallback : stored === '1'
  } catch {
    return fallback
  }
}

const width = ref(Math.min(MAX_WIDTH, Math.max(MIN_WIDTH, readStoredNumber(WIDTH_KEY, DEFAULT_WIDTH))))
const collapsed = ref(readStoredBoolean(COLLAPSED_KEY, false))
const activeTab = ref<'docs' | 'code' | 'remote'>(readStoredTab())
const resizing = ref(false)

function persistWidth() {
  try { localStorage.setItem(WIDTH_KEY, String(Math.round(width.value))) } catch {}
}
function persistCollapsed() {
  try { localStorage.setItem(COLLAPSED_KEY, collapsed.value ? '1' : '0') } catch {}
}

function readStoredTab(): 'docs' | 'code' | 'remote' {
  try {
    const stored = localStorage.getItem(TAB_KEY)
    if (stored === '1') return 'docs' // legacy docs flag
    if (stored === '0') return 'code' // legacy code flag
    if (stored === 'docs' || stored === 'code' || stored === 'remote') return stored
  } catch { /* storage unavailable */ }
  return 'docs'
}

function persistTab() {
  try { localStorage.setItem(TAB_KEY, activeTab.value) } catch {}
}

function collapse() {
  collapsed.value = true
  persistCollapsed()
}

function expand() {
  collapsed.value = false
  persistCollapsed()
}

function setTab(next: 'docs' | 'code' | 'remote') {
  activeTab.value = next
  persistTab()
  if (next === 'remote') void ensureRemoteSources()
}

// ---------------------------------------------------------------------------
// Resize (left edge)
// ---------------------------------------------------------------------------

function onResizeStart(event: PointerEvent) {
  if (event.button !== 0) return
  resizing.value = true
  const startX = event.clientX
  const startWidth = width.value
  const onMove = (move: PointerEvent) => {
    const delta = startX - move.clientX // moving left grows the panel
    width.value = Math.min(MAX_WIDTH, Math.max(MIN_WIDTH, startWidth + delta))
  }
  const onUp = () => {
    window.removeEventListener('pointermove', onMove)
    window.removeEventListener('pointerup', onUp)
    resizing.value = false
    persistWidth()
  }
  window.addEventListener('pointermove', onMove)
  window.addEventListener('pointerup', onUp)
  event.preventDefault()
}

function resetWidth() {
  width.value = DEFAULT_WIDTH
  persistWidth()
}

// ---------------------------------------------------------------------------
// Docs tab — newest handoff document rendered as Markdown
// ---------------------------------------------------------------------------

const docLoading = ref(false)
const docError = ref('')
const docHtml = ref('')

async function loadDoc() {
  docLoading.value = true
  docError.value = ''
  try {
    const handoff = await fetchIdeHandoff()
    docHtml.value = renderMarkdown(handoff.content, { highlight: true, math: 'defer' })
  } catch (err) {
    docError.value = err instanceof Error ? err.message : String(err)
    docHtml.value = ''
  } finally {
    docLoading.value = false
  }
}

// ---------------------------------------------------------------------------
// Code tab — lazy project source tree + highlighted file viewer
// ---------------------------------------------------------------------------

const rootName = ref('')
const rootPath = ref('')
const treeLoading = ref(false)
const treeError = ref('')
// parent dir path ('') -> entries. Expanded dirs stay cached so revisits are instant.
const treeEntries = ref(new Map<string, IdeTreeEntry[]>())
const expanded = ref(new Set<string>())
const selectedPath = ref('')
const file = ref<IdeFileResponse | null>(null)
const fileLoading = ref(false)
const fileError = ref('')
// AI-change marks: per-line classification (context / add / mod) vs the
// backend's project snapshot, plus the added/modified/removed counts.
const diffEntries = ref<IdeDiffEntry[] | null>(null)
const diffSummary = ref<IdeDiffResponse['summary'] | null>(null)
const diffError = ref('')

// ---------------------------------------------------------------------------
// Context menu + inline editing state (declared before `rows`, which reads it)
// ---------------------------------------------------------------------------

interface ContextMenuState {
  x: number
  y: number
  entry: IdeTreeEntry
}

interface EditingState {
  mode: 'create-file' | 'create-dir' | 'rename'
  parentPath: string
  targetPath: string
  origName: string
  value: string
  icon: IconName
}

const menu = ref<ContextMenuState | null>(null)
const menuRef = ref<HTMLElement | null>(null)
const editing = ref<EditingState | null>(null)
const editingInputEl = ref<HTMLInputElement | null>(null)
const busy = ref(false)
const addChatTarget = ref<IdeTreeEntry | null>(null)
const addToChatOpen = ref(false)

interface TreeRow {
  entry: IdeTreeEntry
  depth: number
  editing?: boolean
}

// Sentinel row for the inline "new file / new folder" editor. Its path is
// \0-prefixed so it can never collide with a real backend entry.
const EDITING_ROW_ENTRY: IdeTreeEntry = { name: '', path: '\u0000editing\u0000', type: 'file' }

const rows = computed<TreeRow[]>(() => {
  const out: TreeRow[] = []
  const state = editing.value
  const walk = (dirPath: string, depth: number) => {
    if (state && state.mode !== 'rename' && state.parentPath === dirPath) {
      out.push({ entry: EDITING_ROW_ENTRY, depth, editing: true })
    }
    const entries = treeEntries.value.get(dirPath) || []
    for (const entry of entries) {
      out.push({ entry, depth })
      if (entry.type === 'dir' && expanded.value.has(entry.path)) {
        walk(entry.path, depth + 1)
      }
    }
  }
  walk('', 0)
  return out
})

function isDirExpanded(path: string): boolean {
  return expanded.value.has(path)
}

async function loadTree() {
  treeLoading.value = true
  treeError.value = ''
  try {
    const [root, tree] = await Promise.all([fetchIdeRoot(), fetchIdeTree('')])
    rootName.value = root.name
    rootPath.value = root.path
    treeEntries.value = new Map([['', tree.entries]])
    expanded.value = new Set()
  } catch (err) {
    treeError.value = err instanceof Error ? err.message : String(err)
  } finally {
    treeLoading.value = false
  }
}

async function openFileByPath(path: string) {
  selectedPath.value = path
  fileLoading.value = true
  fileError.value = ''
  diffEntries.value = null
  diffSummary.value = null
  diffError.value = ''
  try {
    file.value = await fetchIdeFile(path)
    await refreshDiff(path)
  } catch (err) {
    fileError.value = errorMessage(err)
    file.value = null
  } finally {
    fileLoading.value = false
  }
}

// Refetch the AI-change marks for `path` (silently when the viewer already has
// a file open — used by both openFileByPath and the recent-changes poll).
async function refreshDiff(path: string) {
  try {
    const diff = await fetchIdeDiff(path)
    if (selectedPath.value === path) {
      diffEntries.value = diff.entries
      diffSummary.value = diff.summary
      diffError.value = ''
    }
  } catch (err) {
    if (selectedPath.value === path) {
      diffError.value = errorMessage(err)
      diffEntries.value = null
      diffSummary.value = null
    }
  }
}

async function onRowClick(entry: IdeTreeEntry) {
  if (entry.type === 'dir') {
    if (expanded.value.has(entry.path)) {
      expanded.value.delete(entry.path)
      return
    }
    expanded.value.add(entry.path)
    if (!treeEntries.value.has(entry.path)) {
      try {
        const tree = await fetchIdeTree(entry.path)
        treeEntries.value = new Map(treeEntries.value).set(entry.path, tree.entries)
      } catch (err) {
        treeError.value = errorMessage(err)
        expanded.value.delete(entry.path)
      }
    }
    return
  }
  await openFileByPath(entry.path)
}

// ---------------------------------------------------------------------------
// Remote tab — SSH / FTP / WSL / MCP / Git clone file browsing (read-only)
// ---------------------------------------------------------------------------

const REMOTE_TRANSPORTS: readonly RemoteType[] = ['ssh', 'ftp', 'wsl', 'mcp', 'git']

const remoteType = ref<RemoteType>('ssh')
const remoteSources = ref<RemoteSourcesResponse | null>(null)
const remoteSourceId = ref('')
const remoteDirEntries = ref(new Map<string, RemoteTreeEntry[]>())
const remoteExpanded = ref(new Set<string>())
const remoteSelected = ref('')
const remoteFile = ref<RemoteFileResponse | null>(null)
const remoteLoading = ref(false)
const remoteError = ref('')
const remoteFileLoading = ref(false)
const remoteFileError = ref('')

const remoteServerOptions = computed<Array<{ id: string; name: string }>>(() => {
  const sources = remoteSources.value
  if (!sources) return []
  const list = sources[remoteType.value]
  return Array.isArray(list) ? list : []
})

const remoteSettingsPath = computed(() => {
  if (remoteType.value === 'ssh') return '/settings/ssh'
  if (remoteType.value === 'ftp') return '/settings/ftp'
  if (remoteType.value === 'mcp') return '/settings/mcp'
  return '' // WSL needs no configuration
})

const remoteSourceName = computed(() => {
  const id = remoteSourceId.value
  if (!id) return ''
  return remoteServerOptions.value.find(s => s.id === id)?.name || ''
})

const remoteRows = computed<Array<{ entry: RemoteTreeEntry; depth: number }>>(() => {
  const out: Array<{ entry: RemoteTreeEntry; depth: number }> = []
  const walk = (dirPath: string, depth: number) => {
    const entries = remoteDirEntries.value.get(dirPath) || []
    for (const entry of entries) {
      out.push({ entry, depth })
      if (entry.type === 'dir' && remoteExpanded.value.has(entry.path)) {
        walk(entry.path, depth + 1)
      }
    }
  }
  walk('', 0)
  return out
})

function isRemoteDirExpanded(path: string): boolean {
  return remoteExpanded.value.has(path)
}

function clearRemoteTree() {
  remoteDirEntries.value = new Map()
  remoteExpanded.value = new Set()
  remoteSelected.value = ''
  remoteFile.value = null
  remoteFileError.value = ''
  remoteError.value = ''
}

async function ensureRemoteSources() {
  // The git source is auto-discovered on the gateway; re-scan whenever the
  // git transport is opened so clones made since the last visit show up.
  if (!remoteSources.value || remoteType.value === 'git') {
    await loadRemoteSources()
  }
}

async function loadRemoteSources() {
  remoteLoading.value = true
  remoteError.value = ''
  try {
    remoteSources.value = await fetchRemoteSources()
    const options = remoteServerOptions.value
    remoteSourceId.value = options[0]?.id || ''
    clearRemoteTree()
    if (options.length > 0) await loadRemoteRoot()
  } catch (err) {
    remoteError.value = errorMessage(err)
  } finally {
    remoteLoading.value = false
  }
}

async function setRemoteType(next: RemoteType) {
  if (next === remoteType.value) return
  remoteType.value = next
  await ensureRemoteSources()
  const options = remoteServerOptions.value
  remoteSourceId.value = options[0]?.id || ''
  clearRemoteTree()
  if (options.length > 0) await loadRemoteRoot()
}

async function onRemoteSourceChange() {
  clearRemoteTree()
  if (remoteSourceId.value) await loadRemoteRoot()
}

async function loadRemoteRoot() {
  if (!remoteSourceId.value) return
  remoteLoading.value = true
  remoteError.value = ''
  try {
    const tree = await fetchRemoteTree(remoteType.value, remoteSourceId.value, '')
    remoteDirEntries.value = new Map([['', tree.entries]])
  } catch (err) {
    remoteError.value = errorMessage(err)
  } finally {
    remoteLoading.value = false
  }
}

async function onRemoteRowClick(entry: RemoteTreeEntry) {
  if (entry.type === 'dir') {
    if (remoteExpanded.value.has(entry.path)) {
      remoteExpanded.value.delete(entry.path)
      return
    }
    remoteExpanded.value.add(entry.path)
    if (!remoteDirEntries.value.has(entry.path)) {
      try {
        const tree = await fetchRemoteTree(remoteType.value, remoteSourceId.value, entry.path)
        remoteDirEntries.value = new Map(remoteDirEntries.value).set(entry.path, tree.entries)
      } catch (err) {
        remoteError.value = errorMessage(err)
        remoteExpanded.value.delete(entry.path)
      }
    }
    return
  }
  remoteSelected.value = entry.path
  remoteFileLoading.value = true
  remoteFileError.value = ''
  try {
    remoteFile.value = await fetchRemoteFile(remoteType.value, remoteSourceId.value, entry.path)
  } catch (err) {
    remoteFileError.value = errorMessage(err)
    remoteFile.value = null
  } finally {
    remoteFileLoading.value = false
  }
}

function openRemoteSettings() {
  const path = remoteSettingsPath.value
  if (path) void router.push(path)
}

const remoteFileHtml = computed(() => {
  const content = remoteFile.value?.content
  if (content === undefined) return ''
  const language = remoteFile.value?.language || ''
  if (language && hljs.getLanguage(language)) {
    try {
      return hljs.highlight(content, { language, ignoreIllegals: true }).value
    } catch { /* fall through to plain */ }
  }
  return escapeHtml(content)
})

// ---------------------------------------------------------------------------
// Recent AI changes — polled file activity (badge + popover + tree dots)
// ---------------------------------------------------------------------------

const CHANGES_POLL_MS = 5000
const CHANGES_KEEP_MAX = 100

const recentChanges = ref<IdeChangeFile[]>([])
const changesOpen = ref(false)
const changesBtnRef = ref<HTMLElement | null>(null)
const changesRef = ref<HTMLElement | null>(null)
let changesTimer: number | null = null
let changesInFlight = false
// Server clock of the last successful poll, fed back as the next `since` so
// client/server clock skew cannot hide or duplicate changes.
let changesSince = 0

const changedPaths = computed(() => {
  const set = new Set<string>()
  for (const item of recentChanges.value) set.add(item.path.replace(/\\/g, '/'))
  return set
})

const changesBadgeLabel = computed(() => {
  const count = recentChanges.value.length
  return count > 99 ? '99+' : String(count)
})

function isChangedPath(path: string): boolean {
  return changedPaths.value.has(path.replace(/\\/g, '/'))
}

function fileNameOf(path: string): string {
  const normalized = path.replace(/\\/g, '/')
  return normalized.slice(normalized.lastIndexOf('/') + 1) || normalized
}

function changeIcon(path: string): IconName {
  const name = fileNameOf(path)
  const ext = name.slice(name.lastIndexOf('.') + 1).toLowerCase()
  return ['md', 'markdown', 'rst', 'txt'].includes(ext) ? 'fileText' : 'fileCode'
}

function relativeTime(mtime: number): string {
  const seconds = Math.max(0, Math.round(Date.now() / 1000 - mtime))
  if (seconds < 60) return t('ide.changes.justNow')
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return t('ide.changes.minutesAgo', { n: minutes })
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return t('ide.changes.hoursAgo', { n: hours })
  return t('ide.changes.daysAgo', { n: Math.floor(hours / 24) })
}

async function pollChanges(initial = false) {
  if (changesInFlight) return
  changesInFlight = true
  try {
    const since = initial ? Date.now() / 1000 : changesSince
    const response = await fetchIdeChanges(since)
    changesSince = response.serverTime || Date.now() / 1000
    mergeChanges(response.files)
  } catch {
    // Best-effort polling: keep the last known state on transient errors.
  } finally {
    changesInFlight = false
  }
}

// Dedupe by path (keeping the newest mtime), newest first. Reassigning on
// every poll also refreshes the relative-time labels. The first (baseline)
// poll simply captures the server clock without listing history.
function mergeChanges(incoming: IdeChangeFile[]) {
  if (incoming.length === 0 && recentChanges.value.length === 0) return
  const byPath = new Map<string, IdeChangeFile>()
  for (const item of recentChanges.value) byPath.set(item.path, item)
  for (const item of incoming) {
    const existing = byPath.get(item.path)
    if (!existing || item.mtime > existing.mtime) byPath.set(item.path, item)
  }
  recentChanges.value = [...byPath.values()]
    .sort((a, b) => b.mtime - a.mtime)
    .slice(0, CHANGES_KEEP_MAX)
  if (incoming.length > 0) {
    void refreshAncestorsOf(incoming.map((item) => item.path))
    // Live-update the AI-change marks for the file currently in the viewer.
    const open = file.value?.path
    if (open && incoming.some((item) => item.path === open)) void refreshDiff(open)
  }
}

// Re-fetch cached tree listings above changed files so brand-new entries
// appear in the tree (with their dot marker) without a manual refresh.
async function refreshAncestorsOf(paths: string[]) {
  const dirs = new Set<string>()
  for (const path of paths) {
    let dir = parentDirOf(path)
    while (dir) {
      dirs.add(dir)
      dir = parentDirOf(dir)
    }
  }
  for (const dir of dirs) {
    if (treeEntries.value.has(dir)) await refreshDir(dir)
  }
}

// Expand the ancestor chain of `path` and load each dir's entries so the
// tree shows the changed file's context before it is opened.
async function revealPathInTree(path: string) {
  const sep = path.includes('\\') ? '\\' : '/'
  const parts = path.split(sep)
  let dir = ''
  for (let i = 0; i < parts.length - 1; i++) {
    dir = dir === '' ? parts[i] : `${dir}${sep}${parts[i]}`
    expanded.value.add(dir)
    await ensureDirEntries(dir)
  }
}

async function openChangedFile(item: IdeChangeFile) {
  changesOpen.value = false
  setTab('code')
  await revealPathInTree(item.path)
  await openFileByPath(item.path)
}

function toggleChanges() {
  changesOpen.value = !changesOpen.value
}

function onChangesPointerDown(event: PointerEvent) {
  const path = typeof event.composedPath === 'function' ? event.composedPath() : []
  if (changesRef.value && path.includes(changesRef.value)) return
  if (changesBtnRef.value && path.includes(changesBtnRef.value)) return
  changesOpen.value = false
}

function onChangesKeyDown(event: KeyboardEvent) {
  if (event.key === 'Escape') changesOpen.value = false
}

watch(changesOpen, (open) => {
  if (open) {
    document.addEventListener('pointerdown', onChangesPointerDown, true)
    document.addEventListener('keydown', onChangesKeyDown, true)
  } else {
    document.removeEventListener('pointerdown', onChangesPointerDown, true)
    document.removeEventListener('keydown', onChangesKeyDown, true)
  }
})

watch(collapsed, (isCollapsed) => {
  if (isCollapsed) changesOpen.value = false
})

// ---------------------------------------------------------------------------
// Context menu — create / rename / delete / copy / add-to-conversation
// ---------------------------------------------------------------------------

function errorMessage(err: unknown): string {
  return err instanceof Error ? err.message : String(err)
}

// Backend tree paths use the host OS separator, so both must be handled.
function parentDirOf(path: string): string {
  const idx = Math.max(path.lastIndexOf('/'), path.lastIndexOf('\\'))
  return idx === -1 ? '' : path.slice(0, idx)
}

function isUnderPath(path: string, root: string): boolean {
  return path !== root && [`${root}/`, `${root}\\`].some(prefix => path.startsWith(prefix))
}

function targetDirFor(entry: IdeTreeEntry): string {
  return entry.type === 'dir' ? entry.path : parentDirOf(entry.path)
}

function openMenu(entry: IdeTreeEntry, event: MouseEvent) {
  menu.value = { x: event.clientX, y: event.clientY, entry }
}

function closeMenu() {
  menu.value = null
}

function menuEventInside(event: PointerEvent): boolean {
  const root = menuRef.value
  if (!root) return false
  const path = typeof event.composedPath === 'function' ? event.composedPath() : []
  if (path.includes(root)) return true
  return event.target instanceof Node && root.contains(event.target)
}

function onDocumentPointerDown(event: PointerEvent) {
  if (!menuEventInside(event)) closeMenu()
}

function onDocumentKeyDown(event: KeyboardEvent) {
  if (event.key === 'Escape') closeMenu()
}

function onAddToChatKeyDown(event: KeyboardEvent) {
  if (event.key === 'Escape') closeAddToChat()
}

function clampMenuPosition() {
  const el = menuRef.value
  const state = menu.value
  if (!el || !state) return
  const rect = el.getBoundingClientRect()
  if (rect.width === 0 && rect.height === 0) return
  state.x = Math.max(8, Math.min(state.x, window.innerWidth - rect.width - 8))
  state.y = Math.max(8, Math.min(state.y, window.innerHeight - rect.height - 8))
}

watch(menu, (open) => {
  if (open) {
    document.addEventListener('pointerdown', onDocumentPointerDown, true)
    document.addEventListener('keydown', onDocumentKeyDown, true)
    void nextTick(clampMenuPosition)
  } else {
    document.removeEventListener('pointerdown', onDocumentPointerDown, true)
    document.removeEventListener('keydown', onDocumentKeyDown, true)
  }
})

watch(addToChatOpen, (open) => {
  if (open) {
    document.addEventListener('keydown', onAddToChatKeyDown, true)
  } else {
    document.removeEventListener('keydown', onAddToChatKeyDown, true)
  }
})

// Drop the cached listing of `path`'s own children plus every descendant cache,
// and collapse the subtree. Used after rename / delete of a file or directory.
function dropEntryCaches(path: string) {
  const prefixes = [`${path}/`, `${path}\\`]
  const nextEntries = new Map(treeEntries.value)
  nextEntries.delete(path)
  for (const key of [...nextEntries.keys()]) {
    if (prefixes.some(prefix => key.startsWith(prefix))) nextEntries.delete(key)
  }
  treeEntries.value = nextEntries
  const nextExpanded = new Set(expanded.value)
  nextExpanded.delete(path)
  for (const key of [...nextExpanded]) {
    if (prefixes.some(prefix => key.startsWith(prefix))) nextExpanded.delete(key)
  }
  expanded.value = nextExpanded
}

async function refreshDir(dirPath: string) {
  const nextEntries = new Map(treeEntries.value)
  nextEntries.delete(dirPath)
  treeEntries.value = nextEntries
  if (dirPath === '' || expanded.value.has(dirPath)) {
    try {
      const tree = await fetchIdeTree(dirPath)
      treeEntries.value = new Map(treeEntries.value).set(dirPath, tree.entries)
    } catch (err) {
      pushToast(errorMessage(err), { tone: 'danger' })
    }
  }
}

async function ensureDirEntries(dirPath: string) {
  if (treeEntries.value.has(dirPath)) return
  try {
    const tree = await fetchIdeTree(dirPath)
    treeEntries.value = new Map(treeEntries.value).set(dirPath, tree.entries)
  } catch (err) {
    pushToast(errorMessage(err), { tone: 'danger' })
  }
}

function startCreate(mode: 'create-file' | 'create-dir') {
  const entry = menu.value?.entry
  closeMenu()
  if (!entry) return
  const parentPath = targetDirFor(entry)
  if (parentPath && !expanded.value.has(parentPath)) {
    expanded.value.add(parentPath)
    void ensureDirEntries(parentPath)
  }
  editing.value = {
    mode,
    parentPath,
    targetPath: '',
    origName: '',
    value: '',
    icon: mode === 'create-dir' ? 'folder' : 'fileText',
  }
  void nextTick(() => editingInputEl.value?.focus())
}

function startRename() {
  const entry = menu.value?.entry
  closeMenu()
  if (!entry) return
  editing.value = {
    mode: 'rename',
    parentPath: parentDirOf(entry.path),
    targetPath: entry.path,
    origName: entry.name,
    value: entry.name,
    icon: entry.type === 'dir' ? 'folder' : (entry.language ? 'fileCode' : 'fileText'),
  }
  void nextTick(() => {
    editingInputEl.value?.focus()
    editingInputEl.value?.select()
  })
}

function isRenaming(entry: IdeTreeEntry): boolean {
  return editing.value?.mode === 'rename' && editing.value.targetPath === entry.path
}

const editingValue = computed({
  get: () => editing.value?.value ?? '',
  set: (next: string) => {
    if (editing.value) editing.value.value = next
  },
})

const editingIcon = computed<IconName>(() => editing.value?.icon ?? 'fileText')

function setEditingInput(el: Element | ComponentPublicInstance | null) {
  editingInputEl.value = el instanceof HTMLInputElement ? el : null
}

function cancelEditing() {
  editing.value = null
}

async function commitEditing() {
  const state = editing.value
  if (!state || busy.value) return
  const name = state.value.trim()
  if (!name) {
    editing.value = null
    return
  }
  busy.value = true
  try {
    if (state.mode === 'rename') {
      if (name !== state.origName) {
        const result = await renameIdeEntry(state.targetPath, name)
        dropEntryCaches(state.targetPath)
        await refreshDir(state.parentPath)
        if (selectedPath.value === state.targetPath) {
          await openFileByPath(result.path)
        } else if (isUnderPath(selectedPath.value, state.targetPath)) {
          selectedPath.value = ''
          file.value = null
        }
      }
    } else {
      await createIdeEntry(state.parentPath, name, state.mode === 'create-file' ? 'file' : 'dir')
      await refreshDir(state.parentPath)
    }
    editing.value = null
  } catch (err) {
    // Keep the editor open so the value can be corrected.
    pushToast(errorMessage(err), { tone: 'danger' })
  } finally {
    busy.value = false
  }
}

async function deleteFromMenu() {
  const entry = menu.value?.entry
  closeMenu()
  if (!entry) return
  const ok = await confirm({
    title: t('ide.deleteConfirmTitle'),
    body: t('ide.deleteConfirmBody', { name: entry.name }),
  })
  if (!ok) return
  busy.value = true
  try {
    await deleteIdeEntry(entry.path)
    dropEntryCaches(entry.path)
    await refreshDir(parentDirOf(entry.path))
    if (selectedPath.value === entry.path || isUnderPath(selectedPath.value, entry.path)) {
      selectedPath.value = ''
      file.value = null
    }
  } catch (err) {
    pushToast(errorMessage(err), { tone: 'danger' })
  } finally {
    busy.value = false
  }
}

function absolutePathFor(relPath: string): string {
  if (!rootPath.value) return relPath
  const sep = rootPath.value.includes('\\') ? '\\' : '/'
  return rootPath.value.endsWith(sep)
    ? `${rootPath.value}${relPath}`
    : `${rootPath.value}${sep}${relPath}`
}

async function copyText(text: string) {
  closeMenu()
  try {
    await navigator.clipboard.writeText(text)
  } catch (err) {
    pushToast(errorMessage(err), { tone: 'danger' })
  }
}

function copyAbsolutePathFromMenu() {
  const entry = menu.value?.entry
  if (!entry) return
  void copyText(absolutePathFor(entry.path))
}

function copyRelativePathFromMenu() {
  const entry = menu.value?.entry
  if (!entry) return
  void copyText(entry.path)
}

function openAddToChat() {
  const entry = menu.value?.entry
  closeMenu()
  if (!entry) return
  addChatTarget.value = entry
  addToChatOpen.value = true
}

function closeAddToChat() {
  addToChatOpen.value = false
  addChatTarget.value = null
}

function insertEntryPath() {
  const target = addChatTarget.value
  closeAddToChat()
  if (!target) return
  requestComposerInsert(absolutePathFor(target.path))
}

async function insertEntryContent() {
  const target = addChatTarget.value
  closeAddToChat()
  if (!target || target.type !== 'file') return
  busy.value = true
  try {
    const response = await fetchIdeFile(target.path)
    if (response.binary || response.content === undefined) {
      pushToast(t('ide.binaryFile'), { tone: 'warn' })
      return
    }
    const fence = response.content.includes('```') ? '````' : '```'
    const language = response.language ? `${response.language} ` : ''
    requestComposerInsert(`${fence}${language}${target.path}\n${response.content}\n${fence}`)
  } catch (err) {
    pushToast(errorMessage(err), { tone: 'danger' })
  } finally {
    busy.value = false
  }
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

const fileHtmlWithDiffs = computed(() => {
  const content = file.value?.content
  if (content === undefined) return ''
  const language = file.value?.language || ''
  let highlighted = ''
  if (language && hljs.getLanguage(language)) {
    try {
      highlighted = hljs.highlight(content, { language, ignoreIllegals: true }).value
    } catch { /* fall through to plain */ }
  }
  if (!highlighted) highlighted = escapeHtml(content)
  const diff = diffEntries.value
  if (!diff || diff.length === 0) return highlighted
  // highlight.js keeps line breaks, so split its output to wrap each line with
  // its diff mark. A trailing newline produces a final empty fragment — drop it.
  const lines = highlighted.split('\n')
  if (lines.length > 0 && lines[lines.length - 1] === '') lines.pop()
  const parts: string[] = []
  for (let i = 0; i < lines.length; i++) {
    const kind = diff[i]?.type
    const cls = kind === 'add' || kind === 'mod' ? ` ide-diff-line--${kind}` : ''
    parts.push(`<span class="ide-diff-line${cls}">${lines[i]}</span>`)
  }
  return parts.join('\n')
})

const diffChanged = computed(() => {
  const s = diffSummary.value
  return !!s && (s.added > 0 || s.modified > 0 || s.removed > 0)
})

function refreshActive() {
  if (activeTab.value === 'docs') void loadDoc()
  else if (activeTab.value === 'code') void loadTree()
  else void loadRemoteSources()
}

onMounted(() => {
  if (activeTab.value === 'docs') void loadDoc()
  else if (activeTab.value === 'code') void loadTree()
  else void ensureRemoteSources()
  // Baseline poll captures the server clock; subsequent polls are incremental.
  void pollChanges(true)
  // Paused while the panel is collapsed — the interval keeps running but skips.
  changesTimer = window.setInterval(() => {
    if (!collapsed.value) void pollChanges()
  }, CHANGES_POLL_MS)
})

onBeforeUnmount(() => {
  if (changesTimer !== null) window.clearInterval(changesTimer)
  document.removeEventListener('pointerdown', onDocumentPointerDown, true)
  document.removeEventListener('keydown', onDocumentKeyDown, true)
  document.removeEventListener('keydown', onAddToChatKeyDown, true)
  document.removeEventListener('pointerdown', onChangesPointerDown, true)
  document.removeEventListener('keydown', onChangesKeyDown, true)
})
</script>

<style scoped>
.ide-panel {
  --ide-panel-border: color-mix(in srgb, var(--border) 70%, transparent);
  position: relative;
  display: flex;
  flex-direction: column;
  flex: 0 0 auto;
  min-width: 0;
  min-height: 0;
  background: var(--bg-surface);
  border-left: 1px solid var(--ide-panel-border);
  overflow: hidden;
}

.ide-panel.is-resizing {
  cursor: col-resize;
  user-select: none;
}

/* Collapsed rail */
.ide-panel__strip {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 32px;
  flex: 1 0 auto;
  padding-top: var(--sp-2);
  border-left: 1px solid var(--ide-panel-border);
  background: var(--bg-surface);
}

.ide-panel__toggle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border: 0;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-dim);
  cursor: pointer;
}
.ide-panel__toggle:hover {
  background: var(--bg-hover);
  color: var(--text);
}

/* Left resizer */
.ide-panel__resizer {
  position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  width: 5px;
  cursor: col-resize;
  z-index: 2;
  background: transparent;
  transition: background var(--dur-fast) var(--ease-standard);
}
.ide-panel__resizer:hover,
.ide-panel.is-resizing .ide-panel__resizer {
  background: var(--accent);
}

/* Header */
.ide-panel__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-2);
  padding: var(--sp-2) var(--sp-3);
  border-bottom: 1px solid var(--ide-panel-border);
}

.ide-panel__title {
  display: inline-flex;
  align-items: center;
  gap: var(--sp-2);
  font-size: 12px;
  font-weight: 600;
  color: var(--text);
  white-space: nowrap;
}

.ide-panel__actions {
  display: inline-flex;
  align-items: center;
  gap: var(--sp-1);
}

.ide-panel__action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border: 0;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-dim);
  cursor: pointer;
}
.ide-panel__action:hover {
  background: var(--bg-hover);
  color: var(--text);
}

/* Tabs bar (tabs + recent-changes trigger, anchor for the changes popover) */
.ide-panel__tabsbar {
  position: relative;
  border-bottom: 1px solid var(--ide-panel-border);
}

/* Tabs */
.ide-panel__tabs {
  display: flex;
  gap: var(--sp-1);
  padding: var(--sp-1) var(--sp-2);
}

.ide-panel__tab {
  display: inline-flex;
  align-items: center;
  gap: var(--sp-1);
  padding: var(--sp-1) var(--sp-2);
  border: 0;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-dim);
  font-size: 12px;
  cursor: pointer;
}
.ide-panel__tab:hover {
  background: var(--bg-hover);
  color: var(--text);
}
.ide-panel__tab.is-active {
  background: var(--accent-soft, color-mix(in srgb, var(--accent) 12%, transparent));
  color: var(--accent);
  font-weight: 600;
}

/* Recent-changes trigger + count badge */
.ide-panel__changes-btn {
  margin-inline-start: auto;
  display: inline-flex;
  align-items: center;
  gap: var(--sp-1);
  padding: var(--sp-1) var(--sp-2);
  border: 0;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-dim);
  font-size: 12px;
  cursor: pointer;
  transition: background var(--dur-fast) var(--ease-standard), color var(--dur-fast) var(--ease-standard);
}
.ide-panel__changes-btn:hover {
  background: var(--bg-hover);
  color: var(--text);
}
.ide-panel__changes-btn.is-active {
  background: var(--accent-soft, color-mix(in srgb, var(--accent) 12%, transparent));
  color: var(--accent);
}

.ide-panel__changes-badge {
  min-width: 16px;
  padding: 0 var(--sp-1);
  border-radius: var(--radius-full);
  background: var(--ok);
  color: var(--bg-surface);
  font-size: 10px;
  font-weight: 600;
  line-height: 16px;
  text-align: center;
  font-variant-numeric: tabular-nums;
}

/* Recent-changes popover (anchored below the tabs bar) */
.ide-changes {
  position: absolute;
  top: calc(100% + var(--sp-1));
  inset-inline-end: var(--sp-2);
  z-index: 30;
  display: flex;
  flex-direction: column;
  width: min(300px, calc(100% - var(--sp-4)));
  max-height: 300px;
  overflow: hidden;
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-md);
  background: var(--bg-surface);
  box-shadow: var(--shadow-xl);
  animation: ide-menu-in var(--dur-fast) var(--ease-standard);
}

.ide-changes__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-2);
  padding: var(--sp-2) var(--sp-3);
  border-bottom: 1px solid var(--ide-panel-border);
}

.ide-changes__title {
  font-size: 12px;
  font-weight: 600;
  color: var(--text);
}

.ide-changes__close {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border: 0;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-dim);
  cursor: pointer;
}
.ide-changes__close:hover {
  background: var(--bg-hover);
  color: var(--text);
}

.ide-changes__empty {
  padding: var(--sp-4);
  color: var(--text-dim);
  font-size: 12px;
  text-align: center;
}

.ide-changes__list {
  list-style: none;
  margin: 0;
  padding: var(--sp-1);
  overflow-y: auto;
}

.ide-changes__item {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  width: 100%;
  padding: var(--sp-1) var(--sp-2);
  border: 0;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text);
  cursor: pointer;
  font: inherit;
  text-align: start;
  transition: background var(--dur-fast) var(--ease-standard);
}
.ide-changes__item:hover {
  background: var(--bg-hover);
}

.ide-changes__icon {
  flex: 0 0 auto;
  display: inline-flex;
  color: var(--text-dim);
}

.ide-changes__meta {
  flex: 1 1 auto;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.ide-changes__name {
  font-size: 12px;
  font-weight: 600;
  color: var(--text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ide-changes__path {
  font-size: 11px;
  color: var(--text-dim);
  font-family: var(--font-mono);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ide-changes__time {
  flex: 0 0 auto;
  font-size: 10px;
  color: var(--text-dim);
  white-space: nowrap;
}

/* Body */
.ide-panel__body {
  flex: 1 1 auto;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.ide-panel__doc {
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  padding: var(--sp-3);
}

.ide-panel__code {
  flex: 1 1 auto;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.ide-panel__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--sp-2);
  padding: var(--sp-4);
  color: var(--text-dim);
  font-size: 12px;
  text-align: center;
}
.ide-panel__empty p {
  margin: 0;
  word-break: break-word;
}

/* Tree */
.ide-tree {
  flex: 0 0 auto;
  max-height: 45%;
  min-height: 96px;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  border-bottom: 1px solid var(--ide-panel-border);
}

.ide-tree__root {
  display: inline-flex;
  align-items: center;
  gap: var(--sp-2);
  padding: var(--sp-2) var(--sp-3);
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 600;
  border-bottom: 1px solid var(--ide-panel-border);
  background: color-mix(in srgb, var(--bg-hover) 40%, transparent);
}

.ide-tree__root-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ide-tree__list {
  list-style: none;
  margin: 0;
  padding: var(--sp-1) 0;
}

.ide-tree__row {
  display: inline-flex;
  align-items: center;
  gap: var(--sp-1);
  width: 100%;
  padding: 3px var(--sp-2);
  border: 0;
  background: transparent;
  color: var(--text-secondary);
  font-size: 12px;
  font-family: inherit;
  text-align: start;
  cursor: pointer;
  overflow: hidden;
}

.ide-tree__row:hover {
  background: var(--bg-hover);
  color: var(--text);
}

.ide-tree__row.is-selected {
  background: var(--accent-soft, color-mix(in srgb, var(--accent) 12%, transparent));
  color: var(--accent);
}

.ide-tree__chevron {
  flex: 0 0 auto;
  color: var(--text-dim);
}

.ide-tree__file-icon {
  flex: 0 0 auto;
  color: var(--text-dim);
}

.ide-tree__label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Dot marker on tree rows for files the AI recently changed */
.ide-tree__dot {
  flex: 0 0 auto;
  margin-inline-start: auto;
  width: 6px;
  height: 6px;
  border-radius: var(--radius-full);
  background: var(--ok);
}

/* Inline create / rename editor */
.ide-tree__row--editing {
  cursor: text;
}

.ide-tree__input {
  flex: 1 1 auto;
  min-width: 0;
  padding: 1px var(--sp-1);
  border: 1px solid var(--accent);
  border-radius: var(--radius-xs);
  background: var(--bg-surface);
  color: var(--text);
  font-size: 12px;
  font-family: inherit;
  outline: none;
}

/* File viewer */
.ide-viewer {
  flex: 1 1 auto;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.ide-viewer__bar {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  padding: var(--sp-1) var(--sp-3);
  border-bottom: 1px solid var(--ide-panel-border);
  font-size: 11px;
  color: var(--text-dim);
}

.ide-viewer__name {
  color: var(--text-secondary);
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ide-viewer__truncated {
  flex: 0 0 auto;
  color: var(--danger);
}

.ide-viewer__pre {
  flex: 1 1 auto;
  margin: 0;
  padding: var(--sp-3);
  overflow: auto;
  font-size: 12px;
  line-height: 1.55;
  font-family: var(--font-mono);
}

/* AI-change marks: green = added, red = modified/deleted */
.ide-viewer__diff {
  flex: 0 0 auto;
  display: inline-flex;
  align-items: center;
  gap: var(--sp-1);
  margin-inline-start: auto;
}

.ide-viewer__diff-chip {
  padding: 0 var(--sp-1);
  border-radius: var(--radius-full);
  font-size: 10px;
  font-weight: 600;
  line-height: 16px;
  font-variant-numeric: tabular-nums;
}

.ide-viewer__diff-chip--add {
  background: var(--ok-soft, color-mix(in srgb, var(--ok) 16%, transparent));
  color: var(--ok);
}

.ide-viewer__diff-chip--mod {
  background: var(--danger-soft, color-mix(in srgb, var(--danger) 16%, transparent));
  color: var(--danger);
}

.ide-viewer__diff-chip--del {
  background: transparent;
  border: 1px solid var(--danger);
  color: var(--danger);
}

.ide-diff-line {
  display: block;
}

.ide-diff-line--add {
  background: var(--ok-soft, color-mix(in srgb, var(--ok) 14%, transparent));
  box-shadow: inset 3px 0 0 var(--ok);
}

.ide-diff-line--mod {
  background: var(--danger-soft, color-mix(in srgb, var(--danger) 16%, transparent));
  box-shadow: inset 3px 0 0 var(--danger);
}

/* Remote tab */
.ide-panel__remote {
  flex: 1 1 auto;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.ide-remote__bar {
  display: flex;
  flex-direction: column;
  gap: var(--sp-1);
  padding: var(--sp-2);
  border-bottom: 1px solid var(--ide-panel-border);
}

.ide-remote__transports {
  display: flex;
  gap: var(--sp-1);
}

.ide-remote__transport {
  flex: 1 1 0;
  min-width: 0;
  padding: var(--sp-1) var(--sp-2);
  border: 0;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-dim);
  font-size: 11px;
  cursor: pointer;
}
.ide-remote__transport:hover {
  background: var(--bg-hover);
  color: var(--text);
}
.ide-remote__transport.is-active {
  background: var(--accent-soft, color-mix(in srgb, var(--accent) 12%, transparent));
  color: var(--accent);
  font-weight: 600;
}

.ide-remote__source {
  width: 100%;
  min-width: 0;
  padding: var(--sp-1) var(--sp-2);
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-sm);
  background: var(--bg-surface);
  color: var(--text);
  font-size: 12px;
  font-family: inherit;
}

.ide-remote__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--sp-2);
  padding: var(--sp-4);
  color: var(--text-dim);
  font-size: 12px;
  text-align: center;
}
.ide-remote__empty p {
  margin: 0;
  word-break: break-word;
}

.ide-tree--remote {
  max-height: 45%;
}

/* Rendered handoff document */
.ide-markdown {
  font-size: 13px;
  line-height: 1.65;
  color: var(--text);
  word-break: break-word;
}

.ide-markdown :deep(h1),
.ide-markdown :deep(h2),
.ide-markdown :deep(h3),
.ide-markdown :deep(h4) {
  margin: 1.2em 0 0.5em;
  line-height: 1.3;
}

.ide-markdown :deep(h1) {
  font-size: 1.4em;
}
.ide-markdown :deep(h2) {
  font-size: 1.2em;
  padding-bottom: 0.25em;
  border-bottom: 1px solid var(--ide-panel-border);
}
.ide-markdown :deep(h3) {
  font-size: 1.05em;
}
.ide-markdown :deep(p) {
  margin: 0.6em 0;
}
.ide-markdown :deep(ul),
.ide-markdown :deep(ol) {
  margin: 0.6em 0;
  padding-inline-start: 1.4em;
}
.ide-markdown :deep(li) {
  margin: 0.25em 0;
}
.ide-markdown :deep(a) {
  color: var(--accent);
}
.ide-markdown :deep(blockquote) {
  margin: 0.8em 0;
  padding-inline-start: 1em;
  border-inline-start: 3px solid var(--ide-panel-border);
  color: var(--text-dim);
}
.ide-markdown :deep(code) {
  font-family: var(--font-mono);
  font-size: 0.92em;
  background: var(--bg-hover);
  border-radius: var(--radius-xs);
  padding: 0.1em 0.35em;
}
.ide-markdown :deep(pre) {
  margin: 0.8em 0;
  padding: var(--sp-3);
  overflow: auto;
  background: var(--bg-hover);
  border-radius: var(--radius-sm);
}
.ide-markdown :deep(pre code) {
  background: transparent;
  padding: 0;
}
.ide-markdown :deep(table) {
  border-collapse: collapse;
  margin: 0.8em 0;
  font-size: 0.95em;
}
.ide-markdown :deep(th),
.ide-markdown :deep(td) {
  border: 1px solid var(--ide-panel-border);
  padding: 0.35em 0.6em;
}
.ide-markdown :deep(th) {
  background: var(--bg-hover);
}
.ide-markdown :deep(hr) {
  border: 0;
  border-top: 1px solid var(--ide-panel-border);
  margin: 1em 0;
}

/* Context menu (teleported to body, fixed-position) */
.ide-context-menu {
  position: fixed;
  z-index: 1200;
  display: grid;
  min-width: 190px;
  padding: var(--sp-2);
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-md);
  background: var(--bg-surface);
  box-shadow: var(--shadow-xl);
  animation: ide-menu-in var(--dur-fast) var(--ease-standard);
}

@keyframes ide-menu-in {
  from {
    opacity: 0;
    transform: translateY(-2px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.ide-context-menu__item {
  display: inline-flex;
  align-items: center;
  gap: var(--sp-2);
  width: 100%;
  padding: var(--sp-2);
  border: 0;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text);
  cursor: pointer;
  font: inherit;
  font-size: var(--fs-sm);
  text-align: start;
  transition: background var(--dur-fast) var(--ease-standard);
}

.ide-context-menu__item:hover {
  background: var(--bg-hover);
}

.ide-context-menu__item--danger {
  color: var(--danger);
}

.ide-context-menu__icon {
  display: inline-flex;
  color: var(--text-muted);
}

.ide-context-menu__item--danger .ide-context-menu__icon {
  color: var(--danger);
}

.ide-context-menu__label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ide-context-menu__divider {
  height: 1px;
  margin: var(--sp-1) 0;
  background: var(--border);
}

/* "Add to conversation" chooser */
.ide-modal-overlay {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  z-index: 1200;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--scrim);
}

.ide-modal {
  display: grid;
  width: min(320px, calc(100vw - 48px));
  padding: var(--sp-4);
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-modal);
  background: var(--bg-surface);
  box-shadow: var(--shadow-xl);
}

.ide-modal__title {
  margin: 0 0 var(--sp-1);
  color: var(--text);
  font-size: var(--fs-md);
  font-weight: 600;
}

.ide-modal__name {
  margin: 0 0 var(--sp-3);
  overflow: hidden;
  color: var(--text-dim);
  font-size: var(--fs-xs);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ide-fade-enter-active,
.ide-fade-leave-active {
  transition: opacity var(--dur-base);
}

.ide-fade-enter-from,
.ide-fade-leave-to {
  opacity: 0;
}

/* Hide entirely on phones — the layout is chat-first there. */
@media (max-width: 768px) {
  .ide-panel {
    display: none;
  }
}
</style>
