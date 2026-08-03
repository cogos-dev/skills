---
name: openclaw-expert
description: Expert guide for OpenClaw's gateway hub-and-spoke architecture, 20+ messaging platform integrations, session management, agent execution, and multi-agent routing.
version: 1.0.0
author: myrgic
tags: [openclaw, gateway, messaging-platforms, multi-agent, architecture]
canonical_source: "~/workspaces/cog/.claude/skills/openclaw-expert/SKILL.md"
projection_note: >
  This is the public marketplace projection. The canonical source additionally
  cites a set of private internal architecture-decision-record notes and a
  private local vendoring path for the OpenClaw source tree; those pointers
  are replaced here with OpenClaw's own public repository and docs. Update
  canonical first; project here after.
---

# OpenClaw Expert

You are an expert in the OpenClaw architecture, implementation, and ecosystem. You have comprehensive knowledge of how OpenClaw works, its design decisions, and how to extend it.

## Core Competencies

### 1. Architecture Understanding
- **Gateway hub-and-spoke model**: Single Gateway coordinates all channels, sessions, clients, and nodes
- **WebSocket + HTTP multiplexing**: Single port (18789) handles control plane and API
- **Session management**: JSONL transcripts, reset policies, identity linking across platforms, compaction (summarization)
- **Agent execution**: Streaming responses, tool orchestration, model failover, subagent spawning
- **Device nodes**: iOS/Android/macOS companions with camera, voice, screen, canvas capabilities
- **Multi-agent routing**: Multiple named agents with per-agent config, workspace, and model selection

### 2. Messaging Integration
- **20+ platforms**: WhatsApp (Baileys), Telegram (grammY), Discord, Slack, iMessage, Signal, Google Chat, Microsoft Teams, Matrix, Line, BlueBubbles, Zalo, Nostr, Twitch, Nextcloud Talk, Tlon, Mattermost, and more
- **Channel adapters**: Normalize platform messages to common format (core + extension channels)
- **Session scoping**: main, per-sender, per-channel-peer, per-account-channel-peer
- **Identity linking**: Map provider IDs to canonical identities
- **Activation modes**: Mention, reply, always-on, never
- **Voice calls**: Twilio/Telnyx/Plivo integration via voice-call extension

### 3. Tool Ecosystem
- **30+ built-in tools**: Filesystem, execution, web, browser, messaging, nodes, sessions, memory, automation
- **Security model**: Allowlist/denylist, tool groups, approval gates, sandboxing
- **Browser automation**: CDP + Playwright, AI snapshots with numeric refs
- **Node capabilities**: camera.*, canvas.*, screen.record, location.get, sms.send
- **Tool execution**: Host, Docker sandbox, or device node
- **Subagent tools**: `sessions_spawn` for parallel/background agent work with announcement

### 4. Memory & Knowledge
- **Workspace files**: AGENTS.md, SOUL.md, TOOLS.md, IDENTITY.md, USER.md, HEARTBEAT.md, BOOTSTRAP.md
- **Daily memory**: `memory/YYYY-MM-DD.md` files in workspace
- **Long-term memory**: `memory.md` in workspace
- **QMD backend**: Opt-in vector memory with SQLite + embeddings (OpenAI, Gemini, or local LLaMA)
- **Session transcripts**: JSONL files at `~/.openclaw/agents/<agentId>/sessions/`
- **Memory search**: `openclaw memory search "topic"`

### 5. Extension Mechanisms
- **Skills**: SKILL.md format with YAML frontmatter, three-tier loading (workspace → managed → bundled)
- **Plugins**: Node.js plugins with SDK, CLI/tools/handlers registration (32+ extensions)
- **Channels**: Custom platform adapters implementing Channel interface
- **Tools**: Custom tool definitions with execute/executeStream
- **Hooks**: Lifecycle hooks (pre/post/error) for gateway/session/agent/channel events

### 6. Implementation Patterns
- **Entry point**: Process respawn for Node.js flags, lazy CLI loading
- **Gateway**: TypeBox schemas, AJV validation, client sessions, event broadcasting
- **Sessions**: JSONL storage, reset policies, transcript archival, compaction
- **Agents**: Prompt building, tool execution, streaming, failover, subagent spawning
- **Channels**: Platform SDK wrapping, message normalization, presence handling
- **Build**: tsdown bundling, Oxlint/Oxfmt for linting/formatting, Vitest for testing

## When to Use This Skill

### Analyzing OpenClaw Codebase
- Understanding how Gateway coordinates sessions and channels
- Tracing message flow from platform → agent → response
- Identifying extension points for new features
- Debugging session lifecycle or tool execution issues

### Extending OpenClaw Functionality
- Creating custom skills for agent capabilities
- Building plugins to add CLI commands or tools
- Implementing channel adapters for new platforms
- Developing custom tools with proper security

### Comparing Architectures
- Contrasting OpenClaw's hub-and-spoke vs. other patterns
- Evaluating local-first vs. cloud-first trade-offs
- Understanding centralized Gateway vs. distributed systems
- Analyzing messaging integration approaches

### Debugging OpenClaw Issues
- Gateway connection problems
- Session reset policy behavior
- Tool execution failures
- Channel integration issues
- Node pairing and capability invocation
- Memory/QMD indexing problems

## Key Knowledge

### Architecture Reference

For deep architectural detail beyond this summary (data flow diagrams, protocol trade-offs, full feature inventory, source organization), read the OpenClaw project's own documentation and source directly:

- **Docs**: https://docs.openclaw.ai
- **Source**: https://github.com/openclaw/openclaw
- **Website**: https://openclaw.ai
- **Discord**: https://discord.gg/clawd

If you have a local checkout of the OpenClaw repository, its `src/` tree (see "Key Files & Locations" below) is generally the fastest way to confirm current behavior — treat this skill's summary as an orientation map, not a substitute for reading the actual implementation when precision matters.

### Core Concepts

**Gateway**: Always-on process (systemd/launchd/macOS app) that owns:
- Single connections to messaging platforms (Baileys, grammY, etc.)
- Session state (transcripts, metadata, identity links)
- Connected clients (WebSocket) and nodes
- Tool execution orchestration
- Event broadcasting
- Agents dashboard (web UI)

**Sessions**: Conversation threads with unique IDs:
- DM: `agent:<agentId>:main` (or per-sender variants)
- Group: `agent:<agentId>:<channel>:group:<groupId>`
- Subagent: `agent:<agentId>:subagent:<uuid>`
- Cron: `cron:<jobId>`
- Webhook: `hook:<uuid>`
- Node: `node-<nodeId>`
- Compaction: summarize old context when window fills

**Agents**: Isolated execution contexts per session:
- Load conversation history
- Build system prompt (identity + skills + tools)
- Call LLM provider (Anthropic Claude, OpenAI, etc.)
- Stream responses with typing indicators
- Execute tools with approval gates
- Append to JSONL transcript
- Spawn subagents for parallel/background work

**Channels**: Messaging platform integrations:
- Connect via platform SDK (Baileys, grammY, Discord.js, Bolt, etc.)
- Normalize messages to common format
- Forward to Gateway router
- Receive agent responses
- Send via platform API
- 32+ extensions covering all major platforms

**Nodes**: Device companions (macOS, iOS, Android):
- Connect with `role: "node"` and capability list
- Require pairing approval
- Expose camera, voice, screen, location, SMS
- Execute via `node.invoke` tool
- Canvas rendering via WebView (A2UI)

**Tools**: First-class agent capabilities:
- 30+ built-in (read, write, exec, browser, message, etc.)
- Allowlist/denylist per agent
- Approval gates for sensitive operations
- Docker sandboxing option
- Plugin-extensible

**Skills**: Knowledge injection via SKILL.md:
- YAML frontmatter (name, description, requires, envVars, tools)
- Markdown content (when to use, guidelines, examples)
- Three-tier loading (workspace → managed → bundled)
- 55+ built-in skills

**Browser**: Web automation via CDP + Playwright:
- Managed browser launch
- AI snapshots with numeric element refs
- Screenshots, navigation, interaction
- JavaScript evaluation
- Per-agent profiles

**Canvas (A2UI)**: Interactive HTML rendering:
- Canvas Host Server (HTTP, port 18793)
- Node Bridge (TCP, port 18790)
- Present/hide/navigate/eval/snapshot actions
- Live reload on file changes
- Binding: loopback, LAN, Tailscale, or auto

**Heartbeats**: Proactive background agent:
- Configurable interval (default: 30 minutes, 0 to disable)
- HEARTBEAT.md defines tasks
- Suppresses delivery on HEARTBEAT_OK response
- Full agent turns (tool execution, streaming)

**QMD Memory**: Opt-in vector search backend:
- SQLite-based with embeddings (OpenAI, Gemini, local LLaMA)
- Indexes workspace files + session transcripts
- Semantic + keyword hybrid search
- State at `~/.openclaw/state/memory/qmd/`

### Key Files & Locations

```
src/
├── entry.ts                    # Application bootstrap
├── cli/run-main.ts             # CLI command dispatch
├── commands/                   # CLI commands (dashboard, etc.)
├── gateway/index.ts            # Gateway server
├── agents/run-agent.ts         # Agent execution
├── agents/openclaw-tools.ts    # Tool implementations
├── agents/subagent-registry.ts # Subagent system
├── agents/compaction.ts        # Session compaction
├── sessions/                   # Session management
├── channels/                   # Platform adapters
│   ├── whatsapp/
│   ├── telegram/
│   ├── discord/
│   └── ...
├── browser/                    # Browser automation
├── canvas-host/                # Canvas/A2UI server
├── memory/qmd-manager.ts       # QMD memory backend
├── tools/                      # Tool implementations
├── plugins/                    # Plugin system
└── plugin-sdk/                 # Plugin SDK
extensions/                     # 32+ platform/feature extensions
skills/                         # 55+ built-in skills
```

### Config & State Paths

```
~/.openclaw/
├── openclaw.json               # Main config (JSON5)
├── credentials/                # Auth credentials
├── workspace/                  # Default agent workspace
│   ├── AGENTS.md               # Agent instructions
│   ├── SOUL.md                 # Identity/personality
│   ├── TOOLS.md                # Environment notes
│   ├── IDENTITY.md             # Name, emoji, avatar
│   ├── USER.md                 # About the human
│   ├── HEARTBEAT.md            # Periodic tasks
│   └── memory/                 # Daily + long-term memory
├── agents/<agentId>/sessions/  # Session transcripts
├── state/memory/qmd/           # QMD vector store
└── logs/                       # Application logs
```

### CLI Commands

```bash
# Core
openclaw gateway [run] [--port 18789]  # Start gateway
openclaw onboard                        # Onboarding wizard
openclaw setup                          # Workspace setup
openclaw doctor                         # Migration/repair

# Agents
openclaw agents list|add|delete|set-identity
openclaw agent --message "..." [--thinking low|high]

# Channels
openclaw channels status [--probe] [--deep]
openclaw send --to <target> --message <text>

# Memory
openclaw memory search "topic"
openclaw memory write <path> "Title"

# Models & Auth
openclaw models list|set-default
openclaw login

# Skills
openclaw skills list|install|enable|disable

# Cron / Heartbeats
openclaw cron list|add|edit|delete|run

# System
openclaw status [--all] [--deep]
openclaw health [--json]
openclaw security audit [--deep] [--fix]
openclaw update [status|--channel stable|beta|dev]
openclaw dashboard
openclaw config get|set|validate
openclaw nodes list|canvas [present|hide|navigate|eval|snapshot]
```

### Design Principles

1. **Single-user by design**: Gateway assumes one owner, simplifies auth
2. **Gateway as authority**: All state owned by Gateway, clients query it
3. **Device-based trust**: Pairing per device, not per user
4. **Protocol-first**: TypeBox schemas generate JSON Schema + Swift models
5. **Idempotent operations**: Side effects require idempotency keys
6. **Lazy command loading**: Only load invoked subcommand for fast startup
7. **Validation-first**: AJV validates all Gateway frames before processing
8. **Multi-agent safety**: Multiple agents can run concurrently with session isolation

### Common Patterns

**Message flow**:
```
Platform SDK → Channel Adapter → Gateway Router → Session Manager
  → Agent Executor → Tool Executor → Session Manager → Gateway Router
  → Channel Adapter → Platform SDK
```

**Tool execution**:
```
LLM tool_use → Validator (allowlist) → Approval Gate → Context Selection
  (host/Docker/node) → Tool Implementation → Result Streaming
  → Agent Continuation
```

**Subagent spawning**:
```
Agent A → sessions_spawn(task, label) → Gateway → New Session
  → Subagent runs (isolated, no sub-sub-agents)
  → Result announced back to Agent A's channel
```

**Cross-agent communication**:
```
Agent A → sessions_send(B, msg) → Gateway → Inject to Session B
  → Agent B runs → Result → Agent A receives
```

**Session compaction**:
```
Context window filling → Compaction agent summarizes old messages
  → Summary replaces old context → Session continues with budget
```

### Performance Characteristics
- **Message latency**: 100-500ms (channel → agent → response)
- **Concurrent sessions**: 50-100 realistic limit
- **Tool execution**: 1-60s (exec), 2-10s (browser), 100-1000ms (node)
- **WebSocket clients**: 10-20 simultaneous connections
- **Vertical scaling**: Single Gateway, all state in one process

### Security Model
- **Device pairing**: Challenge-response, approval required
- **Channel allowlists**: Per-platform user/group filtering
- **Tool profiles**: minimal, coding, messaging, full
- **Approval gates**: exec, bash, process, node.invoke, elevated
- **Sandbox isolation**: Docker containers, read-only workspace, resource limits
- **Session isolation**: Separate transcripts, explicit cross-session communication
- **Security audit**: `openclaw security audit [--deep]` built-in
- **Healthcheck skill**: Periodic security hardening checks

### Integration Points
- **OpenAI API**: `/v1/chat/completions` endpoint for LangChain, LlamaIndex
- **Webhooks**: `/webhook/<path>` for GitHub, CI, external triggers
- **Tailscale**: Serve/Funnel for remote access
- **Docker**: Tool sandboxing with custom images
- **OAuth**: Anthropic (Claude Pro/Max) and OpenAI (ChatGPT/Codex) subscriptions
- **Auth profiles**: Multiple credential rotation with cooldowns/chutes
- **OpenRouter**: Model sync via `openclaw models sync openrouter`

### Comparison with OpenCode

| Dimension | OpenClaw | OpenCode |
|-----------|----------|----------|
| **Architecture** | Gateway hub | Client/server (Hono) |
| **Focus** | Multi-channel assistant | Code editing |
| **State** | Gateway-owned persistent | Database/JSON |
| **Execution** | Distributed (nodes) | Server-local |
| **Tools** | 30+ built-in | ~21 + MCP |
| **Device** | Deep (camera, voice, screen, canvas) | Limited (filesystem) |
| **Multi-client** | Many (CLI, UI, mobile, macOS) | TUI/Desktop/Web |
| **Messaging** | 20+ platforms | None |
| **Browser** | First-class (CDP + Playwright) | Via MCP |
| **Persistence** | JSONL transcripts | Sessions in DB |
| **Voice** | Always-on wake + voice calls | None |
| **Memory** | Workspace files + QMD vectors | None |
| **Deployment** | Daemon (systemd/launchd) | Interactive CLI/server |

**Key insight**: OpenClaw optimizes for **always-on personal assistant** across devices/channels. OpenCode optimizes for **focused coding workflow** in terminal. Complementary, not competing.

## Example Usage Scenarios

### Scenario 1: Understanding Gateway Architecture
When asked "How does the Gateway work?", explain:
- Single-port WebSocket + HTTP multiplexer (18789)
- Handshake: connect frame → validation → connect_ack with snapshot
- Request-response pattern with JSON Schema validation (AJV)
- Event broadcasting to all connected clients
- State ownership: sessions, presence, paired devices
- Channel integration: dedicated adapters forward messages to Gateway
- Agents dashboard for web-based management

### Scenario 2: Tracing Message Flow
When debugging "Why isn't my Telegram message processed?", trace:
1. Telegram SDK receives message
2. Channel adapter normalizes to InboundMessage
3. Check allowlist (user/group)
4. Build session ID based on session scope config
5. Check activation (mention, reply, always-on)
6. Forward to Gateway router
7. Session manager loads/creates session
8. Agent executor builds prompt + calls LLM
9. Stream response back through Gateway → adapter → Telegram

### Scenario 3: Creating Custom Skill
When asked "How do I teach the agent about X?", guide:
1. Create `~/.openclaw/workspace/skills/my-skill/SKILL.md` (or global `~/.openclaw/skills/`)
2. YAML frontmatter: name, description, requires, envVars, tools
3. Markdown content: when to use, guidelines, examples
4. Optional references/ directory for detailed docs
5. Restart Gateway to reload skills
6. Or manage via dashboard: `openclaw dashboard`

### Scenario 4: Building Plugin
When extending functionality, explain:
1. Create `extensions/my-plugin/` with package.json + openclaw.plugin.json
2. Implement Plugin interface: initialize(context), shutdown()
3. Register CLI commands via context.cli.addCommand()
4. Register tools via context.toolRegistry.addTool()
5. Register Gateway handlers via context.gateway.on()
6. Build and link: `npm run build && npm link`
7. Enable in openclaw.json: `"plugins": {"my-plugin": {"enabled": true}}`

### Scenario 5: Setting Up Subagents
When asked about parallel agent work:
1. Configure subagent settings in openclaw.json
2. Agent uses `sessions_spawn` tool with task description
3. Subagent runs in isolated session
4. Results announced back to originating channel
5. Transcript preserved for review
6. Safety: no sub-sub-agents, no session tools by default

### Scenario 6: Configuring QMD Memory
When asked about memory/search:
1. Set `memory.backend: "qmd"` in openclaw.json
2. Choose embedding provider (OpenAI, Gemini, local LLaMA)
3. QMD indexes workspace files + session transcripts
4. Agent uses memory_search tool for semantic lookup
5. State stored at `~/.openclaw/state/memory/qmd/`

## Best Practices

### When Analyzing OpenClaw
1. Start with the architecture overview in the project's own docs
2. Trace specific flows through the implementation directly
3. Reference feature details in the docs as needed
4. Consider extension points before proposing changes

### When Extending OpenClaw
1. Choose correct extension mechanism (skill, plugin, channel, tool)
2. Follow security best practices (validation, approval gates)
3. Test thoroughly (unit, integration, e2e with Vitest)
4. Document clearly (README, examples)

### When Debugging
1. Check Gateway logs (`openclaw daemon logs` or `~/.openclaw/logs/`)
2. Verify config (`openclaw config validate`, allowlists, tool profiles)
3. Run diagnostics (`openclaw doctor`, `openclaw status --all`)
4. Trace message flow from source to agent
5. Test tool execution in isolation
6. Verify node pairing and capabilities
7. Check QMD indexing status if memory issues

## References

- **GitHub**: https://github.com/openclaw/openclaw
- **Documentation**: https://docs.openclaw.ai
- **Website**: https://openclaw.ai
- **Discord**: https://discord.gg/clawd

## Summary

This skill provides expert-level knowledge of OpenClaw's:
- Architecture (Gateway, sessions, agents, channels, nodes, canvas)
- Implementation (TypeScript, Node.js, WebSocket, HTTP, tsdown, Vitest)
- Features (messaging, tools, browser, voice, memory, automation, heartbeats, subagents)
- Extension (skills, plugins, channels, tools, hooks — 32+ extensions, 55+ skills)
- Integration (OpenAI API, webhooks, Tailscale, Docker, OAuth, OpenRouter)
- Memory (workspace files, QMD vectors, session transcripts, compaction)
- Comparison (vs. OpenCode, Claude.ai, ChatGPT)

Use this skill when working with the OpenClaw codebase, extending functionality, debugging issues, or comparing architectural approaches.
