<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import Icon from '@/components/Icon.vue'

interface FieldSpec {
  name: string
  label?: string
  description?: string
  required?: boolean
}

interface HeaderRow {
  id: number
  name: string
  value: string
}

const props = defineProps<{
  field: FieldSpec
  value: unknown
}>()

const emit = defineEmits<{
  update: [name: string, value: Record<string, string>]
  validity: [valid: boolean]
}>()

const { t } = useI18n()
const rows = ref<HeaderRow[]>([])
const rowInputs = ref<HTMLInputElement[]>([])
const lastEmittedSignature = ref('')
let nextRowId = 1

const RESTRICTED_HEADER_NAMES = new Set([
  'authorization',
  'x-api-key',
  'host',
  'content-length',
  'connection',
  'proxy-authorization',
  'transfer-encoding',
  'upgrade',
])
const HEADER_NAME_PATTERN = /^[!#$%&'*+.^_`|~0-9A-Za-z-]+$/

function normalizeHeaders(value: unknown): Record<string, string> {
  let candidate = value
  if (typeof candidate === 'string') {
    const trimmed = candidate.trim()
    if (!trimmed) return {}
    try {
      candidate = JSON.parse(trimmed)
    } catch {
      return {}
    }
  }
  if (!candidate || typeof candidate !== 'object' || Array.isArray(candidate)) return {}
  return Object.fromEntries(
    Object.entries(candidate as Record<string, unknown>)
      .filter(([name]) => name.trim())
      .map(([name, headerValue]) => [name, String(headerValue ?? '')]),
  )
}

function headerSignature(headers: Record<string, string>): string {
  return JSON.stringify(headers)
}

function normalizedHeaderName(name: string): string {
  return name.trim().toLowerCase()
}

function isRestricted(name: string): boolean {
  return RESTRICTED_HEADER_NAMES.has(normalizedHeaderName(name))
}

function isDuplicate(index: number): boolean {
  const name = normalizedHeaderName(rows.value[index]?.name || '')
  if (!name) return false
  return rows.value.some((row, rowIndex) => (
    rowIndex !== index && normalizedHeaderName(row.name) === name
  ))
}

function rowError(row: HeaderRow, index: number): string {
  const name = row.name.trim()
  if (!name && row.value) return t('setup.provider.customHeaderNameRequired')
  if (name && !HEADER_NAME_PATTERN.test(name)) {
    return t('setup.provider.customHeaderInvalidName', { name })
  }
  if (isRestricted(name)) return t('setup.provider.customHeaderRestricted', { name })
  if (isDuplicate(index)) return t('setup.provider.customHeaderDuplicate', { name })
  return ''
}

const valid = computed(() => rows.value.every((row, index) => !rowError(row, index)))

function outputHeaders(): Record<string, string> {
  const headers: Record<string, string> = {}
  for (const row of rows.value) {
    const name = row.name.trim()
    if (!name || isRestricted(name)) continue
    headers[name] = row.value
  }
  return headers
}

function commit() {
  const headers = outputHeaders()
  lastEmittedSignature.value = headerSignature(headers)
  emit('update', props.field.name, headers)
  emit('validity', valid.value)
}

function addHeader() {
  rows.value.push({ id: nextRowId++, name: '', value: '' })
  void nextTick(() => rowInputs.value[rowInputs.value.length - 1]?.focus())
}

function removeHeader(index: number) {
  rows.value.splice(index, 1)
  commit()
}

function updateHeader(index: number, key: 'name' | 'value', value: string) {
  const row = rows.value[index]
  if (!row) return
  row[key] = value
  commit()
}

watch(
  () => props.value,
  value => {
    const headers = normalizeHeaders(value)
    const signature = headerSignature(headers)
    if (signature === lastEmittedSignature.value) return
    rows.value = Object.entries(headers).map(([name, headerValue]) => ({
      id: nextRowId++,
      name,
      value: headerValue,
    }))
    emit('validity', valid.value)
  },
  { immediate: true, deep: true },
)
</script>

<template>
  <section class="custom-headers" :data-name="field.name" data-scope="provider">
    <div class="custom-headers__head">
      <div>
        <h5>{{ field.label || t('setup.provider.customHeadersTitle') }}{{ field.required ? ' *' : '' }}</h5>
        <p>{{ field.description || t('setup.provider.customHeadersDesc') }}</p>
      </div>
      <button type="button" class="btn btn--ghost custom-headers__add" @click="addHeader">
        <Icon name="plus" :size="14" aria-hidden="true" />
        {{ t('setup.provider.customHeaderAdd') }}
      </button>
    </div>

    <div v-if="rows.length" class="custom-headers__list">
      <div class="custom-headers__columns" aria-hidden="true">
        <span>{{ t('setup.provider.customHeaderName') }}</span>
        <span>{{ t('setup.provider.customHeaderValue') }}</span>
        <span></span>
      </div>
      <div v-for="(row, index) in rows" :key="row.id" class="custom-headers__row">
        <input
          :ref="element => { if (element) rowInputs[index] = element as HTMLInputElement }"
          class="control-input"
          :class="{ 'is-invalid': rowError(row, index) }"
          :name="`setup_provider_custom_headers_${index}_name`"
          :value="row.name"
          :placeholder="t('setup.provider.customHeaderNamePlaceholder')"
          :aria-label="t('setup.provider.customHeaderName')"
          :aria-invalid="rowError(row, index) ? 'true' : undefined"
          :aria-describedby="rowError(row, index) ? `custom-header-error-${row.id}` : undefined"
          autocomplete="off"
          @input="updateHeader(index, 'name', ($event.target as HTMLInputElement).value)"
        >
        <input
          class="control-input"
          :name="`setup_provider_custom_headers_${index}_value`"
          :value="row.value"
          :placeholder="t('setup.provider.customHeaderValuePlaceholder')"
          :aria-label="t('setup.provider.customHeaderValue')"
          autocomplete="off"
          @input="updateHeader(index, 'value', ($event.target as HTMLInputElement).value)"
        >
        <button
          type="button"
          class="btn btn--icon btn--ghost custom-headers__remove"
          :aria-label="t('setup.provider.customHeaderRemove', { name: row.name || index + 1 })"
          :title="t('setup.provider.customHeaderRemove', { name: row.name || index + 1 })"
          @click="removeHeader(index)"
        >
          <Icon name="trash" :size="14" aria-hidden="true" />
        </button>
        <p
          v-if="rowError(row, index)"
          :id="`custom-header-error-${row.id}`"
          class="custom-headers__error"
          role="alert"
        >{{ rowError(row, index) }}</p>
      </div>
    </div>
    <p v-else class="custom-headers__empty">{{ t('setup.provider.customHeadersEmpty') }}</p>
  </section>
</template>

<style scoped>
.custom-headers {
  display: grid;
  gap: var(--sp-3);
}

.custom-headers__head {
  align-items: flex-start;
  display: flex;
  gap: var(--sp-3);
  justify-content: space-between;
}

.custom-headers__head h5,
.custom-headers__head p,
.custom-headers__empty,
.custom-headers__error {
  margin: 0;
}

.custom-headers__head p,
.custom-headers__empty {
  color: var(--text-muted);
  font-size: var(--fs-sm);
  margin-top: 2px;
}

.custom-headers__add {
  flex: 0 0 auto;
}

.custom-headers__list {
  display: grid;
  gap: var(--sp-2);
}

.custom-headers__columns,
.custom-headers__row {
  display: grid;
  gap: var(--sp-2);
  grid-template-columns: minmax(8rem, 0.85fr) minmax(10rem, 1.15fr) 36px;
}

.custom-headers__columns {
  color: var(--text-muted);
  font-size: var(--fs-xs);
  font-weight: 600;
  padding: 0 2px;
}

.custom-headers__row {
  align-items: start;
}

.custom-headers__row .control-input {
  min-width: 0;
  width: 100%;
}

.custom-headers__row .control-input.is-invalid {
  border-color: var(--danger);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--danger) 14%, transparent);
}

.custom-headers__remove {
  height: 36px;
  width: 36px;
}

.custom-headers__error {
  color: var(--danger);
  font-size: var(--fs-xs);
  grid-column: 1 / -1;
}

@container provider-panel (max-width: 560px) {
  .custom-headers__head {
    align-items: stretch;
    flex-direction: column;
  }

  .custom-headers__add {
    align-self: flex-start;
  }

  .custom-headers__columns {
    display: none;
  }

  .custom-headers__row {
    grid-template-columns: minmax(0, 1fr) 36px;
  }

  .custom-headers__row .control-input:first-child,
  .custom-headers__error {
    grid-column: 1 / -1;
  }
}
</style>
