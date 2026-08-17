# OpenStarry Code Releases

The OpenStarry Code fork publishes the `openstarry-code` distribution and CLI
with the `openstarry_code` Python import from
[`tomysh1337/openstarry-code`](https://github.com/tomysh1337/openstarry-code).
The fork's first source-first release publishes the verified Python wheel,
source archive, and `SHA256SUMS`. Desktop source uses the new identity, while
Windows releases include the packaged gateway and pinned Python, Node.js, and
Git Bash runtimes in NSIS EXE and WiX MSI installers.
0.5.x releases (previews and the stable) publish Electron desktop installers;
0.5.4 added WiX MSI beside the existing NSIS EXE target.
GitHub Releases do not publish Windows portable zips, portable latest aliases,
public wheelhouse zips, or separately branded macOS or Linux portable bundles.

| Version | Tag | Date | Notes |
|---|---|---|---|
| 0.5.9 | v0.5.9 | 2026-08-17 | Mixed-provider fusion fixes, real-time channel progress, QQ rich-media delivery, automatic subagent collaboration, and expanded bundled Skills |
| 0.5.8 | v0.5.8 | 2026-08-16 | Remote custom-provider context budgeting, live Luna/Sol/Terra discovery, and desktop integration settings |
| 0.5.7 | v0.5.7 | 2026-08-16 | Resilient custom-provider model discovery, configured-model fallback, clearer transport diagnostics, and independent Zen API profiles |
| 0.5.6 | v0.5.6 | 2026-08-15 | Codex-X companion, shared Codex Skills/prompts/conversations, sandbox status tool, third-party API catalog, custom request headers, and credential redaction |
| 0.5.5 | v0.5.5 | 2026-08-14 | Custom Chat/Responses/Anthropic endpoints, Bing China/Baidu/Sogou search, complete OpenStarry branding, and correlation-header fixes |
| 0.5.4 | v0.5.4 | 2026-08-14 | Windows desktop release: NSIS EXE, WiX MSI, bundled application-build skill, and portable tar extraction compatibility |
| 0.5.3 | v0.5.3 | 2026-08-14 | OpenStarry Code: four custom API slots, automatic model discovery, B5 stacking, rebranded documentation, dependency fixes, and the inherited 0.5.3 runtime improvements |
| 0.5.2 | v0.5.2 | 2026-07-30 | Maintenance: same-turn steering, responsive startup and session history, safer recovery and usage accounting, and Desktop/provider/UI fixes |
| 0.5.1 | v0.5.1 | 2026-07-29 | Maintenance: Full host/Cron reliability, Plan mode and project workspaces, artifact previews, desktop recovery, and provider/UI improvements |
| 0.5.0 | v0.5.0 | 2026-07-23 | Stable: Model Ensemble and multi-provider routing, safer upgrades and profile protection, signed macOS desktop updates, usage reporting, and the OSS download mirror |
| 0.5.0rc4 | v0.5.0rc4 | 2026-07-13 | Preview: safe profile recovery, explicit Windows Portable transfer, Desktop data retention, update reliability, and OSS downloads |
| 0.5.0rc3 | v0.5.0rc3 | 2026-07-10 | Preview: legacy-home migration, provider and routing expansion, desktop/Web UI improvements, runtime hardening, and container images |
| 0.5.0rc2 | v0.5.0rc2 | 2026-07-06 | Preview: provider/router recovery, Web UI upload refresh, desktop/session fixes, and CI contract repair |
| 0.5.0rc1 | v0.5.0rc1 | 2026-07-04 | Preview: Model Ensemble routing, Control UI, managed execution, OpenTUI, and portable retirement |
| 0.4.1 | v0.4.1 | 2026-06-30 | Desktop reliability, six-language client support, telemetry accuracy, router packaging, and mainline governance |
| 0.4.0 | v0.4.0 | 2026-06-27 | Control UI refresh, manual MetaSkills, coding mode, search expansion, and runtime hardening |
| 0.3.0 | v0.3.0 | 2026-05-31 | MetaSkills, Health Doctor, tool compression, and docs release |
| 0.2.1 | v0.2.1 | 2026-05-21 | 0.2 maintenance release |
| 0.2.0 | v0.2.0 | 2026-05-20 | 0.2 release |
| 0.2.0rc1 | v0.2.0rc1 | 2026-05-19 | Second public preview |
| 0.1.0rc1 | v0.1.0rc1 | 2026-05-12 | First public preview |

OpenStarry Code v0.5.9 publishes these verified artifacts:

- `OpenStarry-Code-0.5.9-win-x64.exe`
- `OpenStarry-Code-0.5.9-win-x64.msi`
- `openstarry_code-0.5.9-py3-none-any.whl`
- `openstarry_code-0.5.9.tar.gz`
- `SHA256SUMS`

The release is marked stable after the wheel contents, compiled Web UI,
entry points, source archive, Windows package layout, bundled runtime, and
checksums pass verification. The Windows installers are currently unsigned.

For Windows Desktop upgrades from RC3 to RC4 or later, users must install the
new version directly over the existing installation and must not uninstall RC3
first. The RC3 uninstaller may remove `%APPDATA%\OpenSquilla`; release guidance
must tell users to back up that directory. RC4 and later NSIS packages set
`deleteAppDataOnUninstall=false`.

Container tags follow a separate policy: each release publishes
`ghcr.io/tomysh1337/openstarry-code:<git-tag>`, and Docker `:latest`
tracks the most recently pushed release tag, including previews and backports.
If a backport moves `:latest`, rerun the container workflow from the newest tag
to restore the intended ordering. The fixed release tag is the rollback and
reproducibility contract.

The Windows desktop installer is currently unsigned; release notes and download
sections must link to `docs/code-signing-policy.md` until a signing workflow is
approved and enabled. Windows browser downloads may carry Mark-of-the-Web, and
SmartScreen, Smart App Control, enterprise policy, and unsigned binary
reputation must be checked on a real Windows machine before broad promotion.

GitHub source archives remain available for code review and developer
reference; source installs should use `git clone` plus Git LFS. Python wheel
filenames must remain versioned because installers validate the version segment
inside the wheel filename.

Release wheels, Electron Desktop installers, and container images include the
CI-built Vue control console; installing those artifacts does not require
Node.js or npm. Git checkouts do not track the generated console. Source
installers and contributors producing Web UI or wheel artifacts require Node.js
22.12+ with npm, run `npm ci` plus `npm run build`, and therefore pay the
frontend dependency download, build-time, and cache-space cost. Backend-only
editable installs remain available without that build. Release notes should
call this out whenever the source build contract changes.

Release docs must describe the unified non-user-initiated network observability
switch. `OPENSTARRY_CODE_PRIVACY_DISABLE_NETWORK_OBSERVABILITY=true` or:

```toml
[privacy]
disable_network_observability = true
```

disables automatic install telemetry, passive update checks, and automatic
desktop update checks at startup and, while the app remains open, at most once
per day. The current environment variables
`OPENSTARRY_CODE_TELEMETRY_DISABLED=true` and
`OPENSTARRY_CODE_UPDATE_CHECK_DISABLED=true` remain honored. Manual user-initiated
update-availability checks do not bypass these controls. Opening a release page
or downloading an asset is a separate user-initiated action and may still
contact GitHub.

Update discovery follows the installed release channel. Stable builds only
offer newer stable releases. Preview builds offer the highest published release
on the same version base — a later RC or the final stable release — and never
jump to a preview on a different base. Supported macOS desktop builds check
after startup and at most once per day while the app remains open; surfaces
without native update support refresh the passive Control UI notice through the
local gateway. These long-running checks are included starting with RC4, so an
already-installed Windows RC3 still requires a manual, in-place RC4 upgrade.

README install commands must use tag-pinned URLs such as:

- `https://github.com/opensquilla/opensquilla/releases/download/v0.5.3/OpenSquilla-0.5.3-mac-arm64.dmg`
- `https://github.com/opensquilla/opensquilla/releases/download/v0.5.3/OpenSquilla-0.5.3-win-x64.exe`
- `https://github.com/opensquilla/opensquilla/releases/download/v0.5.3/opensquilla-0.5.3-py3-none-any.whl`

## Release SOP

1. Verify `git status` is clean before starting release prep.
2. Confirm the latest `origin/main` SHA is the intended release baseline and
   that its required CI run completed successfully.
3. Prepare a release PR from `origin/main`: update version metadata,
   `CHANGELOG.md`, `RELEASES.md`, `CONTRIBUTORS.md`, release notes, README
   download sections, install scripts, workflow asset contracts, and release
   tests.
4. Confirm release notes and README download sections link to `PRIVACY.md`,
   `THIRD_PARTY_NOTICES.md`, and `docs/code-signing-policy.md`; do not claim
   Windows code signing before it is enabled. Confirm privacy wording documents
   the unified network observability switch and legacy opt-out environment
   variables.
5. Bump `pyproject.toml`, `uv.lock`, `desktop/electron/package.json`,
   `desktop/electron/package-lock.json`, `install.sh`, and `install.ps1` to the
   release version.
6. Run the focused release contract tests locally, then open and merge the
   release PR only after review and CI pass.
7. Fetch `origin main --tags`, verify the merged `origin/main` SHA and CI one
   more time, then create the annotated tag on that exact SHA:

   ```sh
   git tag -a v0.5.3 <verified-sha> -m "OpenSquilla 0.5.3"
   git push origin v0.5.3
   ```

8. Wait for both `.github/workflows/wheelhouse-release.yml` and
   `.github/workflows/docker-image.yml`. Review the draft GitHub Release. For
   the `v0.5.3` stable, confirm it is not marked Pre-release, leave Latest
   unset until the maintainer explicitly confirms it at publish time, and
   confirm it contains only the Electron installers, updater metadata,
   versioned wheel, `SHA256SUMS`, plus GitHub's generated source archives. It
   must not contain `OpenSquilla-*-portable.zip` or
   `OpenSquilla-windows-x64-portable.zip`.
9. Verify GHCR before publishing broadly. For the first container release, make
   the newly created `ghcr.io/opensquilla/opensquilla` package public, then
   confirm both `v0.5.3` and `latest` resolve to an amd64/arm64 manifest and
   pass a gateway health smoke test.
10. Publish the GitHub Release only after maintainer confirmation, then run the
   post-publish tag URL checks:

   ```sh
   curl --fail --head --location https://github.com/opensquilla/opensquilla/releases/download/v0.5.3/OpenSquilla-0.5.3-mac-arm64.dmg
   curl --fail --head --location https://github.com/opensquilla/opensquilla/releases/download/v0.5.3/OpenSquilla-0.5.3-win-x64.exe
   curl --fail --head --location https://github.com/opensquilla/opensquilla/releases/download/v0.5.3/opensquilla-0.5.3-py3-none-any.whl
   curl --fail --head --location https://github.com/opensquilla/opensquilla/releases/download/v0.5.3/SHA256SUMS
   ```

11. If a release tag is wrong before publication, stop and report its peeled
    SHA, the intended SHA, CI result, tag message, and protected-tag ruleset.
    Move it only through the protected-tag repair procedure, restore protection,
    and verify both workflows and the remote peeled tag before continuing.
12. For subsequent previews: bump the package version, docs, workflow
    contracts, and tag to the next preview version, for example `0.5.0rc5` /
    `v0.5.0rc5`. Preview GitHub Releases must remain pre-releases and use
    tag-pinned README URLs until a later stable release is intentionally
    promoted.

## GitHub-only release checks

These checks cannot be fully proven by local artifact generation:

- The tag exists on GitHub and matches `pyproject.toml`.
- The release workflow can fetch hydrated Git LFS router assets.
- The draft GitHub Release title is `OpenSquilla 0.5.3`.
- Preview drafts are marked Pre-release and must not be marked as Latest; the `v0.5.3`
  stable draft is not marked Pre-release, and Latest is applied only at
  publish after explicit maintainer confirmation.
- Preview GitHub Releases contain the Electron installers, updater metadata,
  versioned wheel, and `SHA256SUMS` after `gh release upload --clobber`.
- Preview GitHub Releases do not contain Windows portable zips or portable
  latest aliases.
- The GHCR package is public, and `v0.5.3` plus `latest` expose both amd64
  and arm64 images that pass the gateway health smoke test.
- After a preview GitHub Release is published, the tag-pinned release asset URLs
  resolve.
- Windows browser downloads may carry Mark-of-the-Web; SmartScreen,
  Smart App Control, enterprise policy, and unsigned binary reputation must be
  checked on a real Windows machine.

## Why preview package versions use rc

Release assets are distributed as built artifacts, so the package filename,
installer name, wheel name, and tag should describe the same preview build.
PEP 440 accepts `0.5.0rc4`, while the public GitHub Release title can use the
friendlier name "OpenSquilla 0.5.0 Preview 4".
