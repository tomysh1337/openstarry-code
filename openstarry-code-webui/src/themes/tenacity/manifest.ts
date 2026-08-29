import type { ThemeManifest } from '../types'

// Value theme "tenacity" — the Tenacity Glass look: a pastel light-blue→pink
// gradient ground with white 75% glass surfaces (backdrop blur), soft glow and
// slide/hover motion. Palette + glass recipe in ./tokens.css (contract +
// contrast guards); the world layer — gradient ground, glass chrome, accent
// glow — is ./world.css, loaded lazily on activation so other-theme users
// download none of it.
const tenacity: ThemeManifest = {
  id: 'tenacity',
  name: 'Tenacity',
  kind: 'value',
  icon: 'cloud',
  capabilities: { colorScheme: 'light', userSelectable: true, respectsReducedMotion: true },
  world: { styles: () => import('./world.css') },
}

export default tenacity
