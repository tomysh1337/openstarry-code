// @vitest-environment happy-dom
import { afterEach, describe, expect, it, vi } from 'vitest'

import { createDesktopPlatform } from './desktop'

function installDesktopApi(api: Record<string, unknown>) {
  ;(window as unknown as { opensquillaDesktop?: unknown }).opensquillaDesktop = api
}

afterEach(() => {
  delete (window as unknown as { opensquillaDesktop?: unknown }).opensquillaDesktop
})

describe('Codex-X desktop companion bridge', () => {
  it('stays absent for an older desktop preload', () => {
    installDesktopApi({ getOsLocale: vi.fn() })

    expect(createDesktopPlatform().codexX).toBeUndefined()
  })

  it('normalizes status and launch responses from Electron', async () => {
    const getCodexXStatus = vi.fn(async () => ({
      supported: true,
      available: true,
      version: '0.3.12',
      sharedCodexHome: true,
    }))
    const openCodexX = vi.fn(async () => ({
      supported: true,
      available: true,
      version: '0.3.12',
      sharedCodexHome: true,
      launched: true,
      ignored: 'private host field',
    }))
    installDesktopApi({ getOsLocale: vi.fn(), getCodexXStatus, openCodexX })

    const companion = createDesktopPlatform().codexX
    expect(await companion?.getStatus()).toEqual({
      supported: true,
      available: true,
      version: '0.3.12',
      sharedCodexHome: true,
    })
    expect(await companion?.open()).toEqual({
      supported: true,
      available: true,
      version: '0.3.12',
      sharedCodexHome: true,
      launched: true,
    })
  })
})
