<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'
import ControlSwitch from '@/components/ControlSwitch.vue'
import Icon from '@/components/Icon.vue'
import { usePlatform } from '@/platform'
import { useProjectWorkspaces } from '@/composables/useProjectWorkspaces'

const props = defineProps<{ mode: 'computerControl' | 'browser' | 'coding' }>()
const STORAGE_KEY = 'openstarry.settings.integrations.v1'

const computer = reactive({ enabled: true, chromeInstalled: false, edgeEnabled: true, excelEnabled: true })
const browser = reactive({ enabled: true, urlTarget: 'default', localTarget: 'chatgpt' })

type CodingPage = 'hooks' | 'connection' | 'git' | 'environment' | 'worktrees'
const codingPages = [
  { id: 'hooks', label: '钩子', icon: 'target' },
  { id: 'connection', label: '连接', icon: 'cloud' },
  { id: 'git', label: 'Git', icon: 'fork' },
  { id: 'environment', label: '环境', icon: 'gauge' },
  { id: 'worktrees', label: 'Worktrees', icon: 'folder' },
] as const

interface SshProfile { name: string; host: string; user: string; port: number; keyPath: string }
interface CodingSettings {
  hooksEnabled: boolean
  beforeTurnHook: boolean
  afterTurnHook: boolean
  hooksPath: string
  sshHost: string
  sshUser: string
  sshPort: number
  sshKeyPath: string
  sshProfiles: SshProfile[]
  branchPrefix: string
  mergeMethod: 'merge' | 'squash'
  forcePush: boolean
  draftPullRequests: boolean
  reviewMode: 'current' | 'separate'
  environment: Array<{ key: string; value: string }>
  worktreeRoot: string
  autoClean: boolean
  retention: number
}

const coding = reactive<CodingSettings>({
  hooksEnabled: true, beforeTurnHook: true, afterTurnHook: false,
  hooksPath: '~/.openstarry-code/hooks', sshHost: '', sshUser: '', sshPort: 22,
  sshKeyPath: '~/.ssh/id_ed25519', sshProfiles: [], branchPrefix: 'openstarry/',
  mergeMethod: 'merge', forcePush: false, draftPullRequests: true, reviewMode: 'current',
  environment: [{ key: 'OPENSTARRY_CODE_HOME', value: '~/.openstarry-code' }],
  worktreeRoot: '~/.openstarry-code/worktrees', autoClean: true, retention: 15,
})

const activeCodingPage = ref<CodingPage>('hooks')
const feedback = ref('')
const browserDataCleared = ref(false)
const platform = usePlatform()
const projectWorkspaces = useProjectWorkspaces()
const projects = projectWorkspaces.workspaces

function readBoolean(key: string, fallback: boolean): boolean {
  try {
    const value = localStorage.getItem(key)
    return value === null ? fallback : value === '1'
  } catch { return fallback }
}

function loadPreferences() {
  try {
    const parsed = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}') as {
      computer?: Partial<typeof computer>
      browser?: Partial<typeof browser>
      coding?: Partial<CodingSettings>
    }
    if (parsed.computer) Object.assign(computer, parsed.computer)
    if (parsed.browser) Object.assign(browser, parsed.browser)
    if (parsed.coding) {
      Object.assign(coding, parsed.coding)
      coding.sshProfiles = Array.isArray(parsed.coding.sshProfiles)
        ? parsed.coding.sshProfiles.filter(profile => profile && typeof profile.host === 'string') as SshProfile[]
        : []
      coding.environment = Array.isArray(parsed.coding.environment)
        ? parsed.coding.environment.filter(entry => entry && typeof entry.key === 'string') as Array<{ key: string; value: string }>
        : [{ key: 'OPENSTARRY_CODE_HOME', value: '~/.openstarry-code' }]
    }
  } catch { /* use defaults */ }
  computer.enabled = readBoolean('openstarry.desktop.enabled', computer.enabled)
  computer.chromeInstalled = readBoolean('openstarry.desktop.chromeInstalled', computer.chromeInstalled)
  computer.edgeEnabled = readBoolean('openstarry.desktop.edgeEnabled', computer.edgeEnabled)
  computer.excelEnabled = readBoolean('openstarry.desktop.excelEnabled', computer.excelEnabled)
  browser.enabled = readBoolean('openstarry.browser.enabled', browser.enabled)
}

function persist() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ computer, browser, coding }))
  } catch { /* preferences are best effort in private mode */ }
}

function setFeedback(message: string) {
  feedback.value = message
  window.setTimeout(() => { if (feedback.value === message) feedback.value = '' }, 2600)
}

function updateComputer(key: keyof typeof computer, value: boolean) {
  computer[key] = value
  try { localStorage.setItem(`openstarry.desktop.${key}`, value ? '1' : '0') } catch { /* best effort */ }
  persist(); setFeedback('电脑操控设置已保存')
}

function updateBrowser(value: boolean) {
  browser.enabled = value
  try { localStorage.setItem('openstarry.browser.enabled', value ? '1' : '0') } catch { /* best effort */ }
  persist(); setFeedback('浏览器设置已保存')
}

function clearBrowserData() {
  try {
    for (const key of Object.keys(localStorage)) if (key.startsWith('openstarry.browser.')) localStorage.removeItem(key)
  } catch { /* private mode */ }
  browser.enabled = true; browserDataCleared.value = true; persist(); setFeedback('浏览数据已清除')
}

function saveCoding(message = '编码设置已保存') {
  coding.retention = Math.max(0, Math.min(999, Math.floor(Number(coding.retention) || 0)))
  coding.sshPort = Math.max(1, Math.min(65535, Math.floor(Number(coding.sshPort) || 22)))
  persist(); setFeedback(message)
}

function addSshProfile() {
  const host = coding.sshHost.trim()
  if (!host) { setFeedback('请先填写 SSH 主机'); return }
  coding.sshProfiles.push({
    name: `${coding.sshUser || 'user'}@${host}`, host, user: coding.sshUser.trim() || 'root',
    port: coding.sshPort, keyPath: coding.sshKeyPath.trim(),
  })
  coding.sshHost = ''; saveCoding('SSH 连接已添加')
}

function removeSshProfile(index: number) { coding.sshProfiles.splice(index, 1); saveCoding('SSH 连接已移除') }

async function copySshCommand(profile: SshProfile) {
  const command = `ssh ${profile.user}@${profile.host} -p ${profile.port}`
  try { await navigator.clipboard.writeText(command) } catch { /* clipboard may be unavailable */ }
  setFeedback(`已复制：${command}`)
}

function addEnvironmentEntry() { coding.environment.push({ key: '', value: '' }) }
function removeEnvironmentEntry(index: number) { coding.environment.splice(index, 1); saveCoding('环境变量已更新') }

async function chooseWorktreeDirectory() {
  const choose = platform.files.chooseProjectDirectory
  if (!choose) { setFeedback('当前浏览器不支持目录选择，请直接输入路径'); return }
  const result = await choose({ initialPath: coding.worktreeRoot })
  if (result?.path) { coding.worktreeRoot = result.path; saveCoding('Worktrees 目录已更新') }
}

async function refreshProjects() {
  try { await projectWorkspaces.loadWorkspaces(); setFeedback('项目列表已刷新') }
  catch { setFeedback('项目列表暂不可用') }
}

async function addProject() {
  const choose = platform.files.chooseProjectDirectory
  if (!choose) { setFeedback('当前浏览器不支持添加项目'); return }
  const result = await choose(); if (!result?.path) return
  try { await projectWorkspaces.openWorkspace(result.path); setFeedback('项目已添加') }
  catch { setFeedback('项目添加失败，请确认网关已连接') }
}

watch([computer, browser, coding], persist, { deep: true })
onMounted(() => { loadPreferences(); if (props.mode === 'coding') void refreshProjects() })
</script>

<template>
  <section v-if="props.mode === 'computerControl'" class="control-section desktop-integrations" aria-labelledby="computer-control-title">
    <div class="control-section__head"><h3 id="computer-control-title" class="control-section__title">电脑操控</h3><p class="control-section__desc">管理 OpenStarry Code 对浏览器和桌面应用的连接权限。</p></div>
    <div class="desktop-integrations__card">
      <ControlSwitch :checked="computer.enabled" label="任意应用" caption="允许 OpenStarry Code 控制电脑上的应用" aria-label="允许 OpenStarry Code 控制电脑上的应用" name="desktop-control-enabled" @change="updateComputer('enabled', $event)" />
      <div class="desktop-integrations__rule"><Icon name="monitor" :size="28" aria-hidden="true" /><div><strong>Google Chrome</strong><small :class="computer.chromeInstalled ? 'is-ready' : 'is-missing'">{{ computer.chromeInstalled ? '已安装浏览器扩展程序' : '未安装浏览器扩展程序' }}</small></div><button type="button" class="btn" @click="updateComputer('chromeInstalled', true)">{{ computer.chromeInstalled ? '已安装' : '安装' }}</button></div>
      <div class="desktop-integrations__rule"><Icon name="monitor" :size="28" aria-hidden="true" /><div><strong>Microsoft Edge</strong><small class="is-ready">已安装浏览器扩展程序</small></div><ControlSwitch :checked="computer.edgeEnabled" aria-label="启用 Microsoft Edge" @change="updateComputer('edgeEnabled', $event)" /></div>
      <div class="desktop-integrations__rule"><Icon name="table" :size="28" aria-hidden="true" /><div><strong>Microsoft Excel</strong><small>允许 OpenStarry Code 使用 Excel 加载项以获得更多控制权限</small></div><ControlSwitch :checked="computer.excelEnabled" aria-label="启用 Microsoft Excel" @change="updateComputer('excelEnabled', $event)" /></div>
    </div>
    <p v-if="feedback" class="desktop-integrations__feedback" role="status">{{ feedback }}</p>
  </section>

  <section v-else-if="props.mode === 'browser'" class="control-section desktop-integrations" aria-labelledby="browser-settings-title">
    <div class="control-section__head"><h3 id="browser-settings-title" class="control-section__title">浏览器</h3><p class="control-section__desc">管理内置浏览器，让 OpenStarry Code 在需要时打开网页和本地预览。</p></div>
    <div class="desktop-integrations__card">
      <ControlSwitch :checked="browser.enabled" label="浏览器" caption="让 OpenStarry Code 控制内置浏览器" aria-label="启用内置浏览器" @change="updateBrowser" />
      <label class="desktop-integrations__select-row"><span><strong>网页 URL 和链接打开目标</strong><small>链接默认打开位置</small></span><select v-model="browser.urlTarget" @change="saveCoding('浏览器打开目标已保存')"><option value="default">默认浏览器</option><option value="embedded">内置浏览器</option></select></label>
      <label class="desktop-integrations__select-row"><span><strong>本地 URL 打开目标位置</strong><small>本地开发站点默认打开位置</small></span><select v-model="browser.localTarget" @change="saveCoding('本地 URL 打开目标已保存')"><option value="chatgpt">OpenStarry Code</option><option value="embedded">内置浏览器</option></select></label>
      <div class="desktop-integrations__select-row"><span><strong>浏览数据</strong><small>清除内置浏览器中的历史记录、网站数据、缓存和下载历史记录</small></span><button type="button" class="btn" @click="clearBrowserData">{{ browserDataCleared ? '已清除' : '清除所有浏览数据' }}</button></div>
    </div>
    <p v-if="feedback" class="desktop-integrations__feedback" role="status">{{ feedback }}</p>
  </section>

  <section v-else class="control-section desktop-integrations desktop-integrations--coding" aria-labelledby="coding-settings-title">
    <div class="control-section__head"><h3 id="coding-settings-title" class="control-section__title">编码</h3><p class="control-section__desc">配置 OpenStarry Code 的开发工具和项目工作流。</p></div>
    <nav class="desktop-integrations__coding-list" aria-label="编码工具" role="tablist">
      <button v-for="item in codingPages" :key="item.id" type="button" role="tab" class="desktop-integrations__coding-item" :class="{ 'is-active': activeCodingPage === item.id }" :aria-selected="activeCodingPage === item.id" @click="activeCodingPage = item.id"><Icon :name="item.icon as any" :size="18" /><span>{{ item.label }}</span><Icon name="chevronRight" :size="15" aria-hidden="true" /></button>
    </nav>

    <div class="desktop-integrations__coding-panel">
      <section v-if="activeCodingPage === 'hooks'" aria-labelledby="hooks-title"><h4 id="hooks-title">钩子</h4><p class="desktop-integrations__hint">在任务开始和结束时运行 OpenStarry Code 的本地钩子。</p><ControlSwitch :checked="coding.hooksEnabled" label="启用钩子" caption="允许工作流调用 ~/.openstarry-code/hooks 中的脚本" aria-label="启用钩子" @change="coding.hooksEnabled = $event; saveCoding()" /><label class="desktop-integrations__field"><span>钩子目录</span><input v-model="coding.hooksPath" type="text" spellcheck="false" @change="saveCoding()"></label><ControlSwitch :checked="coding.beforeTurnHook" label="任务开始前" caption="运行 pre-turn 钩子" aria-label="启用任务开始前钩子" @change="coding.beforeTurnHook = $event; saveCoding()" /><ControlSwitch :checked="coding.afterTurnHook" label="任务完成后" caption="运行 post-turn 钩子" aria-label="启用任务完成后钩子" @change="coding.afterTurnHook = $event; saveCoding()" /></section>
      <section v-else-if="activeCodingPage === 'connection'" aria-labelledby="ssh-title"><h4 id="ssh-title">连接</h4><p class="desktop-integrations__hint">保存常用 SSH 主机，连接命令会使用 OpenStarry Code 的终端执行。</p><div class="desktop-integrations__form-grid"><label><span>主机</span><input v-model="coding.sshHost" type="text" placeholder="example.com"></label><label><span>用户</span><input v-model="coding.sshUser" type="text" placeholder="root"></label><label><span>端口</span><input v-model.number="coding.sshPort" type="number" min="1" max="65535"></label><label><span>密钥路径</span><input v-model="coding.sshKeyPath" type="text" spellcheck="false"></label></div><button type="button" class="btn btn--primary" @click="addSshProfile">添加 SSH 连接</button><div v-if="coding.sshProfiles.length" class="desktop-integrations__saved-list"><div v-for="(profile, index) in coding.sshProfiles" :key="`${profile.host}-${index}`" class="desktop-integrations__saved-row"><span><strong>{{ profile.name }}</strong><small>{{ profile.host }}:{{ profile.port }} · {{ profile.keyPath || '默认密钥' }}</small></span><button type="button" class="btn" @click="copySshCommand(profile)">复制命令</button><button type="button" class="btn btn--ghost" @click="removeSshProfile(index)">移除</button></div></div></section>
      <section v-else-if="activeCodingPage === 'git'" aria-labelledby="git-title"><h4 id="git-title">Git</h4><p class="desktop-integrations__hint">设置 OpenStarry Code 创建分支和提交审查请求时使用的默认行为。</p><label class="desktop-integrations__field"><span>分支前缀</span><input v-model="coding.branchPrefix" type="text" spellcheck="false"></label><label class="desktop-integrations__select-row"><span><strong>拉取请求合并方法</strong><small>选择默认的合并方式</small></span><select v-model="coding.mergeMethod"><option value="merge">合并</option><option value="squash">压缩合并</option></select></label><ControlSwitch :checked="coding.forcePush" label="始终强制推送" caption="使用 --force-with-lease 推送工作分支" aria-label="始终强制推送" @change="coding.forcePush = $event; saveCoding()" /><ControlSwitch :checked="coding.draftPullRequests" label="创建草稿拉取请求" caption="创建 PR 时默认使用草稿状态" aria-label="创建草稿拉取请求" @change="coding.draftPullRequests = $event; saveCoding()" /><label class="desktop-integrations__select-row"><span><strong>代码审查发送方式</strong><small>选择在当前聊天中审查，或创建独立审查聊天</small></span><select v-model="coding.reviewMode"><option value="current">在此聊天中进行</option><option value="separate">独立审查聊天</option></select></label><button type="button" class="btn btn--primary" @click="saveCoding('Git 设置已保存')">保存 Git 设置</button></section>
      <section v-else-if="activeCodingPage === 'environment'" aria-labelledby="environment-title"><h4 id="environment-title">环境</h4><p class="desktop-integrations__hint">为项目保存 OpenStarry Code 使用的环境变量。敏感值只保存在当前浏览器配置中。</p><div class="desktop-integrations__saved-list"><div v-for="(entry, index) in coding.environment" :key="index" class="desktop-integrations__env-row"><input v-model="entry.key" type="text" placeholder="变量名"><input v-model="entry.value" type="text" placeholder="值"><button type="button" class="btn btn--ghost" aria-label="移除环境变量" @click="removeEnvironmentEntry(index)">移除</button></div></div><div class="desktop-integrations__button-row"><button type="button" class="btn" @click="addEnvironmentEntry">添加变量</button><button type="button" class="btn btn--primary" @click="saveCoding('环境变量已保存')">保存环境变量</button></div><div class="desktop-integrations__projects-head"><strong>项目</strong><button type="button" class="btn" @click="addProject">添加项目</button></div><div v-if="projects.length" class="desktop-integrations__saved-list"><div v-for="project in projects" :key="project.id" class="desktop-integrations__saved-row"><span><strong>{{ project.name }}</strong><small>{{ project.path }}</small></span><span class="desktop-integrations__project-count">{{ project.taskCount }} 个任务</span></div></div><p v-else class="desktop-integrations__empty">尚未添加项目</p></section>
      <section v-else aria-labelledby="worktrees-title"><h4 id="worktrees-title">Worktrees</h4><p class="desktop-integrations__hint">OpenStarry Code 创建的托管工作树会放在此目录，不再使用 Codex 目录。</p><label class="desktop-integrations__field"><span>工作树根目录</span><div class="desktop-integrations__input-action"><input v-model="coding.worktreeRoot" type="text" spellcheck="false"><button type="button" class="btn" @click="chooseWorktreeDirectory">选择目录</button></div></label><ControlSwitch :checked="coding.autoClean" label="自动删除旧工作树" caption="超过保留数量后自动清理闲置工作树" aria-label="自动删除旧工作树" @change="coding.autoClean = $event; saveCoding()" /><label class="desktop-integrations__field"><span>自动删除限制</span><input v-model.number="coding.retention" type="number" min="0" max="999"></label><div class="desktop-integrations__button-row"><button type="button" class="btn" @click="refreshProjects">刷新项目列表</button><span class="desktop-integrations__muted">{{ projects.length }} 个已登记项目</span></div></section>
    </div>
    <p v-if="feedback" class="desktop-integrations__feedback" role="status">{{ feedback }}</p>
  </section>
</template>

<style scoped>
.desktop-integrations { max-width: 820px; }
.desktop-integrations__card { border: 1px solid var(--border); border-radius: var(--radius-md); overflow: hidden; background: var(--bg-elevated); }
.desktop-integrations__card > * { margin: 0 1rem; }
.desktop-integrations__card > :first-child { margin-top: 1rem; }
.desktop-integrations__card > :last-child { margin-bottom: 1rem; }
.desktop-integrations__rule, .desktop-integrations__select-row { align-items: center; border-top: 1px solid var(--border); display: flex; gap: .85rem; min-height: 76px; padding: .8rem 0; }
.desktop-integrations__rule > div, .desktop-integrations__select-row > span { display: grid; gap: .25rem; min-width: 0; flex: 1; }
.desktop-integrations strong { font-size: .9rem; }
.desktop-integrations small, .desktop-integrations__hint { color: var(--text-muted); font-size: .78rem; }
.desktop-integrations small.is-ready { color: var(--ok); }
.desktop-integrations small.is-missing { color: var(--danger); }
.desktop-integrations select { min-width: 170px; }
.desktop-integrations__coding-list { display: grid; gap: .35rem; max-width: 360px; margin-bottom: 1rem; }
.desktop-integrations__coding-item { align-items: center; background: transparent; border: 0; border-radius: var(--radius-sm); color: var(--text); display: flex; gap: .8rem; padding: .7rem .8rem; text-align: left; }
.desktop-integrations__coding-item:hover, .desktop-integrations__coding-item.is-active { background: var(--bg-hover); }
.desktop-integrations__coding-item.is-active { box-shadow: inset 2px 0 0 var(--accent); }
.desktop-integrations__coding-item span { flex: 1; }
.desktop-integrations__coding-panel { border: 1px solid var(--border); border-radius: var(--radius-md); padding: 1rem; max-width: 720px; }
.desktop-integrations__coding-panel h4 { font-size: 1.2rem; margin: 0; }
.desktop-integrations__hint { margin: .35rem 0 1rem; }
.desktop-integrations__field { align-items: center; display: grid; gap: .6rem; grid-template-columns: minmax(120px, .7fr) minmax(0, 1.3fr); margin: .75rem 0; }
.desktop-integrations__field > span, .desktop-integrations__form-grid span { color: var(--text-muted); font-size: .82rem; }
.desktop-integrations__field input, .desktop-integrations__form-grid input, .desktop-integrations__env-row input { min-width: 0; }
.desktop-integrations__form-grid { display: grid; gap: .7rem; grid-template-columns: repeat(2, minmax(0, 1fr)); margin-bottom: 1rem; }
.desktop-integrations__form-grid label { display: grid; gap: .35rem; }
.desktop-integrations__saved-list { display: grid; gap: .45rem; margin: 1rem 0; }
.desktop-integrations__saved-row, .desktop-integrations__env-row { align-items: center; border-top: 1px solid var(--border); display: flex; gap: .65rem; min-height: 58px; padding: .55rem 0; }
.desktop-integrations__saved-row > span:first-child { display: grid; gap: .25rem; min-width: 0; flex: 1; }
.desktop-integrations__saved-row small { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.desktop-integrations__env-row input:first-child { flex: .8; }
.desktop-integrations__env-row input:nth-child(2) { flex: 1.2; }
.desktop-integrations__button-row, .desktop-integrations__projects-head, .desktop-integrations__input-action { align-items: center; display: flex; gap: .6rem; }
.desktop-integrations__projects-head { border-top: 1px solid var(--border); justify-content: space-between; margin-top: 1rem; padding-top: 1rem; }
.desktop-integrations__input-action input { flex: 1; min-width: 0; }
.desktop-integrations__project-count, .desktop-integrations__muted, .desktop-integrations__empty { color: var(--text-muted); font-size: .78rem; }
.desktop-integrations__feedback { color: var(--ok); font-size: .8rem; margin-top: .7rem; }
@media (max-width: 640px) { .desktop-integrations__select-row, .desktop-integrations__field { align-items: flex-start; flex-direction: column; grid-template-columns: 1fr; } .desktop-integrations select, .desktop-integrations__select-row .btn { width: 100%; } .desktop-integrations__form-grid { grid-template-columns: 1fr; } .desktop-integrations__env-row { align-items: stretch; flex-wrap: wrap; } .desktop-integrations__env-row input { flex: 1 1 40%; } }
</style>
