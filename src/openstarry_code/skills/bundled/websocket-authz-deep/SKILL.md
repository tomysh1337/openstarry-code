---
name: websocket-authz-deep
description: >-
  Deep WebSocket authorization after the HTTP upgrade: re-bind identity per
  message, subscribe/channel ACL, token refresh, privilege changes mid-session,
  and cross-account action IDs. Use when sockets stay open long after 101 and
  message-layer authZ is unclear. Authorized assessments only.
---

# WebSocket Authorization After Upgrade

## Scope And Authorization

- Use only on owned apps, labs, CTFs, or written engagements that list the `ws://` / `wss://` endpoints and test accounts.
- Prefer dual sessions (User A / User B). Do not hijack real-user sockets or plant CSWSH pages against third parties outside scope.
- Limit send rates; avoid flood/DoS proofs on shared production. Destructive actions (force-logout all, wipe rooms, billing opcodes) need explicit approval.
- Redact cookies, bearer tickets, `Sec-WebSocket-Key`, channel names tied to people, and message payloads with PII in reports.
- Handshake Origin/CSWSH surveys remain in `websocket-security`; this skill goes **deeper after** a successful authorized upgrade.

## Use When

- App opens a long-lived socket; many sensitive actions are messages, not REST.
- Auth appears only on upgrade (cookie/`Authorization`/query ticket) and later opcodes trust the connection principal blindly.
- Subscribe/join/room/channel IDs look like object references (IDOR on the wire).
- Tokens refresh on HTTP but the socket never re-validates; or role/tenant changes while the socket stays open.
- After `websocket-security` confirms connect rules but message-layer **object ACL** is unproven.
- Binary envelopes need codecs first → `websocket-binary-reverse-engineering`, then return here for authZ mutations.
- Not primary for pure GraphQL HTTP node IDOR (`idor-graphql-nodes`) unless the transport is a GraphQL subscription over WS.

## Workflow

1. **Capture the authorized baseline**  
   With a legitimate client and test user A, record:

   | Item | Capture |
   | --- | --- |
   | Upgrade URL / query | Path, tickets in query (leak risk) |
   | Auth material | Cookie, `Authorization`, first-message login, mTLS |
   | Principal bind time | Upgrade only vs every message vs subscribe |
   | Message catalog | Join, subscribe, publish, RPC, ack, error shapes |
   | Object keys | `channelId`, `roomId`, `userId`, `orgId`, `stream`, topic |

   Use DevTools, Burp/ZAP WS history, or `websocat` in lab. Keep A and B jars isolated.

2. **Map when identity is evaluated**  
   Build a timeline:

   ```text
   HTTP 101 → (optional auth frame) → subscribe/join → data/events → ...
   ```

   Probe with authorized clients only:

   | Check | Action | Weak outcome |
   | --- | --- | --- |
   | Anonymous upgrade | Omit credentials | 101 + data |
   | Connect OK, skip auth frame | Open then never send login | Subscribes work |
   | Expired session | Kill server session / expire cookie; keep socket | Frames still authorized |
   | Logout elsewhere | Log out via HTTP; reuse socket | Privileges remain |
   | Role change | Demote A mid-session | Old admin opcodes still work |

3. **Per-message and per-channel ACL (core deep authZ)**  
   Authentication on connect ≠ authorization on each action. With B’s socket:

   - Subscribe to A’s `channelId` / `orderId` / `userId` room.  
   - Publish or RPC with foreign resource IDs.  
   - Replay A’s honest messages with a single ID field swapped (one mutation at a time).  
   - Request history/replay/catch-up for foreign streams.

   ```text
   # Conceptual — adjust to observed schema
   {"op":"subscribe","channel":"<A_channel>"}
   {"op":"get","resourceType":"order","id":"<A_id>"}
   {"op":"update","id":"<A_id>","fields":{...}}
   ```

   Success criteria for a finding: B receives A’s private events or mutates A’s object without a grant. Document server errors vs silent drop vs partial fan-out.

4. **Subscription fan-out and presence**  
   Join a shared room legitimately, then probe whether presence lists, typing events, or server pushes include **out-of-scope** user metadata. Test private DMs vs public topics. Confirm unsubscribe actually removes server-side ACL grants (resubscribe with stale capability tokens).

5. **Capability tokens and first-message tickets**  
   If upgrade uses a short-lived ticket:

   - Replay ticket on a second connection after use.  
   - Use ticket issued for A on a connection that later sends B’s identity frame (bind mismatch).  
   - Strip or swap tenant claims inside signed tickets only if analysis is authorized and keys/claims are already visible — do not attack third-party IdPs.

6. **Cross-protocol consistency**  
   Compare the same object access over REST/GraphQL vs WS. Gaps where HTTP denies but WS allows (or the reverse) are high-value. For GraphQL subscriptions, apply node/edge ID swaps with `idor-graphql-nodes` patterns on subscription payloads.

7. **Privilege boundary matrix**  
   | Principal | Target | Ops to try |
   | --- | --- | --- |
   | B same role | A private channel | subscribe, read backlog, write |
   | Low-priv | Admin opcode / topic | elevate via message type rename |
   | Tenant A token | Tenant B room id | cross-tenant IDOR |
   | Stale elevated socket | After demote/logout | sensitive op still accepted |

8. **Session lifecycle hardening checks**  
   - Server must invalidate WS principal on logout, password change, MFA revoke, and ban.  
   - Prefer re-auth or ticket refresh for sensitive opcodes (payments, export).  
   - Do not put long-lived session tokens in upgrade query strings.  
   - Origin/CSWSH preconditions: if cookie auth on upgrade is weak, note handoff to `websocket-security` rather than re-running full CSWSH here.

9. **Evidence and remediation**  
   Save: redacted upgrade, message sequence, A/B account ids, and one minimal PoC frame pair. Remediation: bind principal at connect **and** enforce object/channel ACL on every subscribe/publish/RPC; drop sockets on session revoke; align WS checks with HTTP authZ (`code-quality-standards`).

## Routing

| Need | Skill |
| --- | --- |
| Handshake, Origin, CSWSH survey | `websocket-security` |
| Binary frame codecs / state machines | `websocket-binary-reverse-engineering` |
| Object IDOR patterns (HTTP/API) | `idor-broken-object-authorization` |
| GraphQL node/edge ACL (incl. subscription data) | `idor-graphql-nodes`, `graphql-and-hidden-parameters` |
| Implement server-side session revoke + per-action ACL | `code-quality-standards` |

## Checklist

- [ ] Scope, endpoint(s), and A/B (tenant) accounts recorded
- [ ] Auth mechanism and principal bind time documented
- [ ] Message catalog with object-key fields listed
- [ ] Expired/logout/role-change mid-session results
- [ ] Cross-account subscribe/publish/RPC IDOR tests
- [ ] Fan-out / backlog / capability-ticket replay notes
- [ ] REST/GraphQL vs WS authZ consistency sample
- [ ] Proof sequence redacted; remediation: per-message object ACL + revoke-on-logout
