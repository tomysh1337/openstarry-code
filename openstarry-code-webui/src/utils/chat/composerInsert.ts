/** Cross-component bridge for inserting text into the chat composer.
 *
 * The composer draft lives in ChatView/ChatComposer (no pinia store), so
 * external surfaces — e.g. the IDE explorer's "add to conversation" —
 * publish a window CustomEvent that the mounted composer appends to its
 * draft. Mirrors the requestBrowserWorkbenchOpen pattern in
 * workbench/browserItems.ts.
 */

export const COMPOSER_INSERT_EVENT = 'opensquilla:composer-insert'

export interface ComposerInsertEventDetail {
  text: string
}

export function requestComposerInsert(text: string): boolean {
  if (!text.trim() || typeof window === 'undefined') return false
  window.dispatchEvent(new CustomEvent<ComposerInsertEventDetail>(
    COMPOSER_INSERT_EVENT,
    { detail: { text } },
  ))
  return true
}
