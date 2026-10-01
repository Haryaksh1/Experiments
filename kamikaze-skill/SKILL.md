---
name: kamikaze
description: Clean-slate reset for a chat. Drops every skill instruction loaded so far in this conversation, then retires itself, so Claude goes back to its plain default behavior. Use only when the user explicitly invokes /kamikaze or says "kamikaze", "kill all skills", "drop all skills", or "reset skills". Never trigger it automatically.
---

# Kamikaze

The user wants a clean slate. Take every other skill down, then go down with them.

## What to do

1. **List the casualties.** Name each skill whose instructions were loaded earlier in this conversation (by the Skill tool, a slash command, or a hook that injected a skill). If there are none, say so.
2. **Drop them.** From this point on, stop following the instructions of every one of those skills: their personas, modes, output formats, checklists, gates, and "always active" persistence rules. A skill that says it stays on until some other phrase is typed is still dropped. Kamikaze is that phrase.
3. **Drop yourself.** After the confirmation below, this skill has no further instructions. Do not mention Kamikaze again or carry any of its behavior forward.
4. **Confirm in one short message**, for example:

   > Kamikaze: dropped `ponytail`, `brainstorming`. Back to plain Claude.

Then answer whatever the user asks next the way you would with no skills loaded.

## What survives

Kamikaze only targets skills. These are untouched:

- The system prompt and safety rules
- The user's own instructions, including CLAUDE.md and anything they typed in chat
- Work already done in the conversation (files, decisions, history)
- Skills the user invokes **after** Kamikaze. Those load and run normally.

## Limits

- **This is a behavioral reset, not a deletion.** A skill's text cannot be removed from a conversation once it is loaded. Kamikaze makes Claude stop acting on it.
- **Hooks keep firing.** If a skill is re-injected every turn by a hook (for example a `UserPromptSubmit` hook), the text will reappear. Keep ignoring it for the rest of the chat, and tell the user once that the hook has to be disabled in settings to stop it for good.
- **Nothing on disk changes.** Kamikaze never deletes, edits, or uninstalls skill files. The skills are available again in the next chat.
