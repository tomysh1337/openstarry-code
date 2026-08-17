---
name: ansible-vault-usage
description: >
  Ansible Vault encrypt/decrypt, vault IDs, password files, rekey, and CI
  secret injection so playbooks never commit plaintext secrets. Use when
  ansible-vault, vault_id, encrypted group_vars/host_vars, vault password
  file, rekey, or CI decrypt for ansible-playbook on owned repos.
---

# Ansible Vault Usage

Use **Ansible Vault** so secrets stay encrypted in git and decrypt only at
runtime (operator, CI, controller). Owned inventories/pipelines only. Hand
org secret lifecycle, scanning, and leak IR to `secrets-management-hygiene`.

## When To Use

- Encrypting `group_vars` / `host_vars` / vars files or strings with `ansible-vault`
- Choosing **vault IDs**, password files, prompts, or client scripts
- Wiring **CI** decrypt without plaintext in artifacts or logs
- **Rekey** after rotation, offboarding, or suspected password leak
- Blocking plaintext secrets in playbooks, diffs, or PR reviews
- Keywords: ansible-vault, encrypt_string, vault_identity_list, ANSIBLE_VAULT_PASSWORD_FILE

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Org secret inventory, .env, scanners, rotation IR | `secrets-management-hygiene` |
| CI stages / OIDC / fork isolation broadly | `ci-cd-pipeline-patterns` |
| Playbook/module quality and tests | `code-quality-standards` |
| Cloud SM/Key Vault as system of record | cloud skill + secrets hygiene |

## Repo Config First

Repo and Ansible project conventions **outrank** defaults below.

1. **Vault layout:** existing `group_vars/*/vault.yml`, `host_vars`, `vars/vault.yml` — **extend**
2. **`ansible.cfg`:** `vault_password_file`, `vault_identity_list`, vault-id match flags
3. **Vault IDs:** multi-env (`dev@…`, `prod@…`) vs single default — match operators
4. **CI secrets:** platform secret names for vault passwords; prod environment protection
5. **Ignore rules:** password files, `.vault_pass`, decrypt workdirs never committed
6. **Neighbors:** AWX/Tower credentials, molecule, wrapper scripts already in-repo

**Precedence:** Follow the repo. Surface plaintext vars in git, tracked password
files, or CI logs that echo decrypted content.

## Workflow

### 1. Inventory

List `$ANSIBLE_VAULT;` files and plaintext candidates (`password:`, keys) under
inventory/`vars`. Note vault IDs and password owners (ops, CI, break-glass).
Confirm `.gitignore` covers password files and decrypt dirs.

### 2. Encrypt and edit (never commit plaintext)

```bash
ansible-vault encrypt group_vars/prod/vault.yml
ansible-vault edit group_vars/prod/vault.yml
ansible-vault encrypt_string --name 'db_password' 'REDACTED' --vault-id prod@prompt
ansible-vault decrypt --output /tmp/vault.plain group_vars/prod/vault.yml  # temp only; shred
```

Commit **ciphertext only**. Prefer `edit`/`view` over durable plaintext copies.
Never paste vault passwords or decrypted values into tickets.

### 3. Vault IDs and password files

| Pattern | Use when |
| --- | --- |
| `--ask-vault-pass` / `--vault-id prod@prompt` | Interactive ops; no password on disk |
| `--vault-password-file` / `ANSIBLE_VAULT_PASSWORD_FILE` | Local automation; mode `0600`, gitignored |
| `--vault-id prod@.vault_pass_prod` | Multiple envs; label every encrypt |
| Client script as password file | Password from keychain / CI secret API |

```bash
ansible-playbook site.yml --vault-id prod@prompt
ansible-playbook site.yml --vault-id dev@~/.vault/dev --vault-id prod@~/.vault/prod
```

Separate **prod vs non-prod** IDs so a leaked dev password cannot decrypt prod.

### 4. CI secrets injection

Store vault password(s) in the **CI secret store** (or OIDC → SM), not workflow
YAML. Write a job-scoped `0600` file or vault client script; pass
`--vault-id label@path` or `ANSIBLE_VAULT_PASSWORD_FILE`. Deny fork PR access to
prod vault secrets. Mask logs; avoid high verbosity around vaulted content.
Do not upload decrypted artifacts. Broader CI trust → `ci-cd-pipeline-patterns`;
rotation policy → `secrets-management-hygiene`.

### 5. Rekey and rotation

```bash
ansible-vault rekey --vault-id prod@old_pass_file group_vars/prod/vault.yml
```

Rekey after leak, offboarding, or schedule. Update operators, CI secrets, and
AWX credentials before retiring the old password. If plaintext hit git history:
**rotate underlying secrets first**, then re-encrypt (`secrets-management-hygiene`).

### 6. Verify

Wrong vault ID fails; intended ID `view`s. Fresh clone + CI dry-run works without
committed password files. Secret scan clean. Playbook edits use `code-quality-standards`.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| ansible-vault encrypt/decrypt, vault IDs, rekey, password files, CI decrypt | **This skill** | — |
| Org inventory, leak IR, scanning, rotation playbooks | `secrets-management-hygiene` | this for Vault ciphertext |
| Pipeline OIDC, env gates, fork isolation | `ci-cd-pipeline-patterns` | this for vault password injection |
| Playbook/plugin structure, tests | `code-quality-standards` | **always** on automation code |

- **`secrets-management-hygiene`:** **hand off** for lifecycle/scanners/IR; this skill owns Vault CLI/layout and CI decrypt wiring.
- **`ci-cd-pipeline-patterns`:** job graph/trust; this skill for how the password reaches `ansible-playbook`.
- **`code-quality-standards`:** always on playbook/wrapper changes.

Keep **this skill primary** for Vault ops; switch for org-wide secret policy.

## Output Checklist

- [ ] Encrypted files and vault IDs inventoried; owners noted (no plaintext values)
- [ ] Repo `ansible.cfg` / ignore rules / existing vault paths followed
- [ ] Ciphertext only in git; no password files or decrypted dumps committed
- [ ] Encrypt/edit via `ansible-vault`; string vs file pattern documented
- [ ] Prod vault IDs separated from non-prod where applicable
- [ ] Password via prompt, `0600` gitignored file, or CI-injected path/script
- [ ] CI: platform secrets; no fork access to prod vault; logs masked
- [ ] Rekey updates operators + CI; leaks rotate underlying secrets first
- [ ] Wrong ID fails; secret scan clean; CQS on playbook changes
- [ ] Routed: lifecycle/IR → `secrets-management-hygiene`; CI topology → `ci-cd-pipeline-patterns`

## Rules

- **Never commit plaintext** secrets or vault passwords; ciphertext only in VCS.
- Vault **passwords** are higher-tier secrets than the vars they wrap.
- Prefer `edit`/`view`; shred temps. Rekey/rotate on exposure. Private repo ≠ safe plaintext. Owned automation only.
