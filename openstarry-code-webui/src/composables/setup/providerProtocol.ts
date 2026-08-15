export const THIRD_PARTY_PROVIDER_IDS = new Set([
  'custom',
  'custom_responses',
  'custom_anthropic',
  'custom_2',
  'custom_3',
  'custom_4',
])

export const CHAT_COMPLETIONS_CUSTOM_PROVIDER_IDS = [
  'custom',
  'custom_2',
  'custom_3',
  'custom_4',
] as const

const PROVIDER_PROTOCOL_LABELS: Record<string, string> = {
  custom: 'Chat Completions',
  custom_responses: 'Responses',
  custom_anthropic: 'Anthropic Messages',
  custom_2: 'Chat Completions',
  custom_3: 'Chat Completions',
  custom_4: 'Chat Completions',
}

export function normalizeProviderId(providerId: string): string {
  return String(providerId || '').trim().toLowerCase()
}

export function isThirdPartyProvider(providerId: string): boolean {
  return THIRD_PARTY_PROVIDER_IDS.has(normalizeProviderId(providerId))
}

export function providerProtocolLabel(providerId: string): string {
  return PROVIDER_PROTOCOL_LABELS[normalizeProviderId(providerId)] || ''
}

export function nextChatCompletionsCustomSlot(
  sourceProviderId: string,
  configuredProviderIds: Iterable<string>,
): string {
  const source = normalizeProviderId(sourceProviderId)
  if (!CHAT_COMPLETIONS_CUSTOM_PROVIDER_IDS.includes(
    source as (typeof CHAT_COMPLETIONS_CUSTOM_PROVIDER_IDS)[number],
  )) return ''
  const configured = new Set(Array.from(configuredProviderIds, normalizeProviderId))
  return CHAT_COMPLETIONS_CUSTOM_PROVIDER_IDS.find(providerId => !configured.has(providerId)) || ''
}
