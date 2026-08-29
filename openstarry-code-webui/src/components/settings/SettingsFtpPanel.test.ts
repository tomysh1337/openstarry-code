// @vitest-environment happy-dom
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { App } from 'vue'

const mounted: Array<{ app: App; el: HTMLElement }> = []

async function settle(): Promise<void> {
  for (let i = 0; i < 8; i++) await Promise.resolve()
  await new Promise(resolve => setTimeout(resolve, 10))
}

async function waitForText(el: HTMLElement, text: string): Promise<void> {
  await vi.waitFor(() => {
    expect(el.textContent).toContain(text)
  }, { timeout: 1000, interval: 10 })
}

function host(overrides: Record<string, unknown> = {}) {
  return {
    id: 'h1',
    name: 'web-server',
    host: 'ftp.example.com',
    port: 21,
    username: 'deploy',
    password: '',
    tls: false,
    enabled: true,
    ...overrides,
  }
}

async function mountPanel(options: {
  hosts?: Array<Record<string, unknown>>
  confirm?: boolean
} = {}) {
  vi.resetModules()
  document.body.innerHTML = ''
  // Stateful fake server so create/delete round-trips show up after reload.
  const state: Array<Record<string, unknown>> = [...(options.hosts ?? [host()])]
  const confirmResult = options.confirm ?? true

  const fetchFtpHosts = vi.fn(async () => ({ hosts: [...state] }))
  const createFtpHost = vi.fn(async (input: unknown) => {
    const entry = { id: 'new-id', ...(input as object) }
    state.push(entry)
    return entry
  })
  const updateFtpHost = vi.fn(async (_id: string, input: unknown) => ({ id: 'h1', ...(input as object) }))
  const deleteFtpHost = vi.fn(async () => {
    state.length = 0
    return { id: 'h1', deleted: true }
  })

  vi.doMock('@/utils/ftpApi', () => ({ fetchFtpHosts, createFtpHost, updateFtpHost, deleteFtpHost }))
  vi.doMock('@/composables/useConfirm', () => ({
    useConfirm: () => ({ confirm: vi.fn(async () => confirmResult) }),
  }))
  vi.doMock('@/composables/useToasts', () => ({ useToasts: () => ({ pushToast: vi.fn() }) }))

  const { createApp, nextTick } = await import('vue')
  const i18n = (await import('@/i18n')).default
  i18n.global.locale.value = 'en'
  const Component = (await import('./SettingsFtpPanel.vue')).default
  const el = document.createElement('div')
  document.body.appendChild(el)
  const app = createApp(Component)
  app.use(i18n)
  app.mount(el)
  mounted.push({ app, el })
  await settle()
  await nextTick()
  return { el, api: { fetchFtpHosts, createFtpHost, updateFtpHost, deleteFtpHost } }
}

afterEach(() => {
  while (mounted.length) mounted.pop()!.app.unmount()
  vi.doUnmock('@/utils/ftpApi')
  vi.doUnmock('@/composables/useConfirm')
  vi.doUnmock('@/composables/useToasts')
  vi.restoreAllMocks()
  document.body.innerHTML = ''
})

describe('SettingsFtpPanel', () => {
  it('loads and renders configured FTP hosts', async () => {
    const { el, api } = await mountPanel()

    expect(api.fetchFtpHosts).toHaveBeenCalledTimes(1)
    await waitForText(el, 'web-server')
    expect(el.textContent).toContain('ftp.example.com:21')
  })

  it('renders the FTPS badge for TLS hosts', async () => {
    const { el } = await mountPanel({ hosts: [host({ tls: true })] })

    await waitForText(el, 'FTPS')
  })

  it('creates a new FTP host from the editor', async () => {
    const { el, api } = await mountPanel({ hosts: [] })
    await waitForText(el, 'No FTP servers configured')

    el.querySelector<HTMLButtonElement>('[data-testid="ftp-add"]')!.click()
    await settle()
    const name = el.querySelector<HTMLInputElement>('[data-testid="ftp-name"]')!
    name.value = 'staging'
    name.dispatchEvent(new Event('input', { bubbles: true }))
    const hostInput = el.querySelector<HTMLInputElement>('[data-testid="ftp-host"]')!
    hostInput.value = 'ftp.example.org'
    hostInput.dispatchEvent(new Event('input', { bubbles: true }))

    el.querySelector<HTMLButtonElement>('[data-testid="ftp-save"]')!.click()
    await waitForText(el, 'staging')

    expect(api.createFtpHost).toHaveBeenCalledWith(
      expect.objectContaining({ name: 'staging', host: 'ftp.example.org', port: 21, enabled: true }),
    )
  })

  it('blocks save when the name is empty', async () => {
    const { el, api } = await mountPanel({ hosts: [] })
    await waitForText(el, 'No FTP servers configured')

    el.querySelector<HTMLButtonElement>('[data-testid="ftp-add"]')!.click()
    await settle()
    const hostInput = el.querySelector<HTMLInputElement>('[data-testid="ftp-host"]')!
    hostInput.value = 'ftp.example.org'
    hostInput.dispatchEvent(new Event('input', { bubbles: true }))

    el.querySelector<HTMLButtonElement>('[data-testid="ftp-save"]')!.click()
    await settle()

    expect(api.createFtpHost).not.toHaveBeenCalled()
    expect(el.textContent).toContain('Name is required')
  })

  it('deletes a host after confirmation', async () => {
    const { el, api } = await mountPanel()
    await waitForText(el, 'web-server')

    el.querySelector<HTMLButtonElement>('.ftp-list__delete')!.click()
    await settle()

    expect(api.deleteFtpHost).toHaveBeenCalledWith('h1', 'web-server')
  })
})
