---
name: cross-channel-context-management
description: Manage persistent context across multiple messaging channels (Telegram, WhatsApp) using a centralized state file and CLI script.
category: koba-infra
---

# Cross-Channel Context Management

## When to Use
Maintain conversation continuity when switching between messaging channels. Use when:
- User switches from WhatsApp to Telegram or vice versa
- Need to preserve conversation state across channel boundaries
- Multi-channel workflows with shared context

## Architecture
1. Central state file: `/root/koba/vault/Inbox/cross-channel-state.json`
2. CLI script: `/root/koba/scripts/cross_channel.py`
3. Memory instruction: Always check state file at session start

## The Script
```bash
# Inject context for a channel
python3 /root/koba/scripts/cross_channel.py --channel telegram_presupuestos "User is working on budget estimates"

# Read current state
python3 /root/koba/scripts/cross_channel.py --channel whatsapp --read

# Clear channel state
python3 /root/koba/scripts/cross_channel.py --channel telegram_presupuestos --clear
```

## Implementation Flow
1. Daemon receives message
2. Calls `cross_channel.py --channel <name> "<context>"`
3. Gets cross-channel context from other channels
4. Injects into prompt system
5. On task completion, updates state with new context

## State File Structure
```json
{
  "channels": {
    "telegram_presupuestos": {
      "last_context": "...",
      "previous_context": "...",
      "updated_at": "ISO timestamp"
    },
    "whatsapp": {}
  },
  "global_threads": [],
  "last_updated": "ISO timestamp"
}
```

## Memory Integration
Must add to memory: `CROSS-CHANNEL: siempre leer /root/koba/vault/Inbox/cross-channel-state.json al inicio, actualizar al terminar.`

## Integration with Daemons
Daemons need to:
1. Before session start: Call cross_channel.py with channel context
2. Parse returned cross_channel_context
3. Inject into system prompt
4. On completion: Call again with updated context

## Limitations
- Daemons run outside sandbox, so script needs to be invoked from host
- Memory has 2,200 char limit, so context injection must be concise
- Cannot auto-read without daemon modifications
</think>
