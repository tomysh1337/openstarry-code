import assert from 'node:assert/strict'
import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'

import prepareMsiProject, { rewriteMsiCodepage } from './prepare-msi-project.mjs'

const fixture = '<?xml version="1.0"?><Wix><Product Name="OpenStarry Code" Codepage="65001"/></Wix>'
const expected = '<?xml version="1.0"?><Wix><Product Name="OpenStarry Code" Codepage="936"/></Wix>'

assert.equal(rewriteMsiCodepage(fixture), expected)
assert.throws(
  () => rewriteMsiCodepage('<Wix><Product Name="OpenStarry Code"/></Wix>'),
  /Product\/@Codepage/,
)

const root = await mkdtemp(join(tmpdir(), 'openstarry-msi-project-'))
try {
  const project = join(root, 'project.wxs')
  await writeFile(project, fixture, 'utf8')
  await prepareMsiProject(project)
  assert.equal(await readFile(project, 'utf8'), expected)
} finally {
  await rm(root, { recursive: true, force: true })
}

console.log('MSI project preparation tests passed.')
