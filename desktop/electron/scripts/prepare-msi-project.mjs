import { readFile, writeFile } from 'node:fs/promises'

const PRODUCT_CODEPAGE_PATTERN = /(<Product\b[^>]*\bCodepage=")([^"]+)(")/

export function rewriteMsiCodepage(source) {
  if (!PRODUCT_CODEPAGE_PATTERN.test(source)) {
    throw new Error('generated MSI project does not declare Product/@Codepage')
  }
  return source.replace(
    PRODUCT_CODEPAGE_PATTERN,
    (_match, prefix, _current, suffix) => `${prefix}936${suffix}`,
  )
}

export default async function prepareMsiProject(projectPath) {
  const source = await readFile(projectPath, 'utf8')
  await writeFile(projectPath, rewriteMsiCodepage(source), 'utf8')
}
