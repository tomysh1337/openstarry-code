import type { RouteRecordRaw } from 'vue-router'

// Desktop and web now share the same Settings overlay (webRoutes' `/settings`,
// gated on capabilities.hasWebConfig which is true on both platforms). The
// desktop-only concerns (owned gateway status/log/restart, reset) live inside
// that dialog as a Runtime section rather than a separate full-page view, so
// there are currently no desktop-exclusive routes. Kept as an explicit empty
// set so the router/nav wiring (router/index.ts, router/nav.ts) stays stable.
export const desktopRoutes: RouteRecordRaw[] = []
