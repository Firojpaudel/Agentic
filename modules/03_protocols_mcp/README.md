# Module 03: Protocol Layer and FastMCP

> "Tool access and agent-to-agent calls are standardized. Production agents get capabilities through these."

---

## 1. Objectives
- Understand the Model Context Protocol (MCP) specification: Tools, Resources, Prompts, Transports (stdio, SSE).
- Build production-ready MCP servers using FastMCP.
- Decouple capability providers from agent orchestrators.

---

## 2. Key Repositories to Read Line-by-Line
- **modelcontextprotocol/modelcontextprotocol** (https://github.com/modelcontextprotocol/modelcontextprotocol): Read the JSON-RPC wire format spec.
- **jlowin/fastmcp** (https://github.com/jlowin/fastmcp): High-level server framework with auth, lifecycle, and composition.
- **anthropics/skills** (https://github.com/anthropics/skills): How agent skills are loaded on demand without context bloat.

---

## 3. Hands-On Exercises
1. Build a custom MCP server with `FastMCP` that exposes 3 internal system resources (e.g., local database query, git repo analyzer, translation).
2. Connect your MCP server to an external agent client (Claude Code, Cursor, or your Module 01 Raw Agent).
3. Implement an Agent-to-Agent (A2A) handoff protocol over HTTP/SSE.

---

## 4. Acceptance Criteria
- Your server passes MCP inspector validation.
- Your tools can be plugged into any MCP-compliant host without code changes.
