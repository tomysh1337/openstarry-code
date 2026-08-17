---
name: go-style-conventions
description: >
  Apply Effective Go, gofmt/goimports, idiomatic error handling, package and
  exported-API comments, naming, and module-local style when writing or reviewing
  Go code. Use when Go style, gofmt, goimports, Effective Go, package comments,
  error wrapping, Go 风格, or Go formatting and idioms are in scope.
---

# Go Style Conventions

Language-level style for Go. Prefer repository config over generic defaults.
Pair with `code-quality-standards` for boundaries, tests, security, and lifecycle.
This skill does not replace project-specific linters or architecture rules.

## Use When

- Writing, refactoring, or reviewing Go (`.go`) sources or modules.
- User mentions **Go style**, **gofmt**, **goimports**, **golint**/`staticcheck`, **Effective Go**, or **Go 风格**.
- Diff fails format checks, `go vet`, or team Go style CI.
- Errors lack context, packages miss doc comments, or APIs fight Go naming idioms.
- Choosing between generic “clean code” advice and idiomatic Go.

**Do not use as primary when:** the task is pure algorithm design with no Go surface, non-Go languages, or deep security/exploit work (use the matching domain skill).

## Repo Config First

Read and obey the repo before applying generic rules. Conflicts with correctness or security: surface them; do not invent a second style.

| Source | What to take |
| --- | --- |
| `go.mod` / `go.work` | Module path, Go version, workspace layout |
| Nearby packages | Naming, error patterns, context usage, interface size |
| `//go:generate`, embed, build tags | Generated and constrained files — do not hand-format away |
| `.golangci.yml` / `.golangci.yaml` | Enabled linters, exclusions, severity |
| `Makefile` / CI / `pre-commit` | Exact `gofmt`/`goimports`/`gofumpt`/`staticcheck` commands |
| `README` / `CONTRIBUTING` / `AGENTS.md` / `STYLE.md` | Team Go conventions |
| `EditorConfig` / VS Code/`gopls` settings | Tab width expectations (Go is tabs for indent) |

**Defaults only when the repo is silent:**

1. Format with `gofmt` (or repo-mandated `gofumpt`).
2. Fix imports with `goimports` (or `gofmt -s` + local import grouping as the repo does).
3. `go vet` + tests for touched packages.
4. Effective Go + Go Code Review Comments as style baseline.
5. Package comment on every non-`main`/non-test package that is part of a public or internal library surface.

## Workflow

### 1. Align tooling

```text
gofmt -w .
goimports -w .
go vet ./...
# if present:
golangci-lint run
staticcheck ./...
go test ./...
```

- Never commit files `gofmt` would change.
- Match import grouping: stdlib, blank line, third party, blank line, module-local (as `goimports` does with `-local` when configured).
- Do not reformat generated code unless the generator is updated.

### 2. Package and file layout

- One package purpose per directory; directory name usually matches package name.
- Prefer short, lowercase package names (`http`, `json`, `user`) — no underscores, no stutter with import path last element when avoidable.
- Avoid `util`/`common` catch-alls; name by domain.
- `internal/` for non-exportable library code; do not expand public API by accident.
- Keep `main` thin: flags, wiring, `os.Exit` / signal handling; logic in importable packages when tests matter.

### 3. Naming (Effective Go)

| Kind | Convention |
| --- | --- |
| Packages | short, lowercase, singular where natural |
| Exported | `CamelCase`; unexported `camelCase` |
| Acronyms | `URL`, `ID`, `HTTP` consistent (`ServeHTTP`, not `ServeHttp`) |
| Getters | `Name()` not `GetName()` for field-like access |
| Interfaces | often verb/`-er` when one method (`Reader`, `Stringer`); name by behavior |
| Receivers | short (1–2 letters from type name), consistent on the type |

Avoid stutter: `http.Server` not `http.HTTPServer` when the package already says HTTP.

### 4. Comments and godoc

- Every exported name needs a comment starting with the name: `// Client connects to ...`.
- Package comment: immediately preceding `package foo` in one file (often `doc.go`): `// Package foo provides ...`.
- Document **why**, invariants, units, concurrency, and closer responsibilities — not restatements of the signature.
- Use complete sentences; keep examples in comments runnable when they claim to be.

### 5. Errors

- Return `error` as the last result; do not use panics for routine failure.
- Check every error; do not assign to `_` without a deliberate, local reason.
- Wrap with `%w` when callers may use `errors.Is` / `errors.As`:

```go
if err != nil {
    return fmt.Errorf("load config %s: %w", path, err)
}
```

- Add context that names the operation and key inputs (paths, IDs) — not noise.
- Sentinel errors: `var ErrNotFound = errors.New("not found")` or custom types when matching needs structure.
- Prefer `fmt.Errorf("...: %w", err)` / `errors.Join` over string-only loss of the chain.
- Log **or** return at a layer, not both, unless the boundary is documented (e.g. top-level handler logs and returns status).

### 6. APIs and Effective Go patterns

- Accept interfaces, return concrete types when practical; define interfaces on the **consumer** side when small.
- Pass `context.Context` as the first parameter for cancelable / RPC / DB work; never store contexts in structs except process-lifetime cases the repo already uses.
- Prefer multiple returns over “result objects” for simple pairs `(T, error)`.
- Use defer for cleanup (`Close`, `Unlock`, cancel); check `Close` errors when they matter (write paths).
- Goroutines: ensure exit on cancel; avoid leaks; document ownership of channels.
- Concurrency: share memory by communicating when it clarifies ownership; protect shared state with clear locking rules.

### 7. Verify before finish

1. `gofmt` / `goimports` clean.
2. `go vet` (and repo linters) clean on touched packages.
3. Focused `go test` for changed behavior; `-race` when concurrency is involved and feasible.
4. Exported API comments present; package comment present for libraries.
5. Diff free of drive-by renames and unrelated formatting on generated files.

## Good And Bad Examples

### Formatting and imports

```go
// GOOD — gofmt spacing; goimports groups
import (
    "context"
    "fmt"

    "github.com/example/mod/internal/store"
)
```

```go
// BAD — hand-aligned spaces; mixed import order; unused imports
import (
  "fmt"   ; "context"
  "github.com/example/mod/internal/store"
  "os"
)
```

### Error handling

```go
// GOOD — context + wrap
func (s *Server) User(ctx context.Context, id string) (*User, error) {
    u, err := s.db.FindUser(ctx, id)
    if err != nil {
        return nil, fmt.Errorf("find user %s: %w", id, err)
    }
    return u, nil
}
```

```go
// BAD — lost cause; ignored error; panic for expected miss
func (s *Server) User(id string) *User {
    u, _ := s.db.FindUser(context.Background(), id)
    if u == nil {
        panic("not found")
    }
    return u
}
```

### Package comments and exports

```go
// GOOD — package doc + exported comment starts with name
// Package bill computes invoices for the billing service.
package bill

// Invoice is a period charge for one account.
type Invoice struct {
    AccountID string
    Cents     int64
}
```

```go
// BAD — no package doc; useless comment; stutter
package billutil

// This is the invoice struct
type BillInvoice struct{}
```

### Naming and interfaces

```go
// GOOD — small consumer-owned interface; clear names
type BlobStore interface {
    Get(ctx context.Context, key string) ([]byte, error)
}

func LoadConfig(ctx context.Context, s BlobStore, key string) ([]byte, error) {
    return s.Get(ctx, key)
}
```

```go
// BAD — huge interface invented at producer; Get- prefix noise; package stutter
type IBlobStoreService interface {
    GetGetBlob(...)
    GetListBlobs(...)
    GetDeleteBlob(...)
    // many methods forced on all implementers
}
```

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Go formatting, naming, errors, godoc, idioms | `go-style-conventions` (this) | `code-quality-standards` |
| Any production change (tests, security, boundaries) | domain skill if any | `code-quality-standards` + this for Go surface |
| Go concurrency bugs / races | `code-quality-standards` | this for style of `context`/lifecycle |
| Protobuf/gRPC Go stubs style only | this for hand-written code | `protobuf-grpc-reverse-engineering` only for wire recovery |
| Non-Go languages | matching language skill / `code-quality-standards` | — |
| Style CI config design (golangci) | this | repo DevEx docs |

## Checklist

- [ ] Repo Go version, linters, and format command identified and used
- [ ] `gofmt` / `goimports` (or repo equivalent) clean on touched files
- [ ] Import groups match repo / `goimports`
- [ ] Package names short; no needless stutter with path or types
- [ ] Exported symbols documented; package comment where required
- [ ] Errors checked, wrapped with `%w` when chain matters, context-rich
- [ ] `context.Context` first on blocking/remote APIs; cancel honored
- [ ] Interfaces small and consumer-driven when newly introduced
- [ ] Defers clean up resources; Close/cancel paths considered
- [ ] `go vet` / repo linters + relevant tests run (report what ran)
- [ ] No drive-by refactors or reformatting of generated code
- [ ] Conflicts between team config and these rules called out explicitly

## Rules

- Repository conventions outrank this skill unless they harm correctness, safety, or security.
- Do not disable linters or remove `go vet` checks to silence style debt without agreement.
- Prefer minimal diffs: style-only PRs stay style-only; behavior changes stay focused.
- Do not claim `gofmt`/`go test` passed unless those commands were actually run.
- Generated code (`*.pb.go`, wire, stringer, easyjson, etc.): change generators or inputs, not one-off hand edits, unless the repo already edits them.
