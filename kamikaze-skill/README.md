# Kamikaze

A clean-slate button for a Claude chat. Run it, and Claude drops every skill instruction it was following. Then Kamikaze retires itself too.

## Why

Skills are helpful, but several active at once can pull in different directions: one wants short answers, another wants long structured reports, a third insists on its own process. Kamikaze puts the chat back to plain Claude without opening a new one and losing the history.

Use it when:

- Skills are clashing and the answers feel confused
- A specialized task is finished and you want normal conversation back
- A skill that says it is "always active" will not let go

## Install

Copy the skill into your Claude Code skills folder under the name `kamikaze`:

```bash
mkdir -p ~/.claude/skills/kamikaze
cp SKILL.md ~/.claude/skills/kamikaze/SKILL.md
```

## Use

Type `/kamikaze` in a chat. Claude lists the skills it dropped and confirms in one line:

```
Kamikaze: dropped ponytail, brainstorming. Back to plain Claude.
```

## What it does not do

- **It does not delete anything.** Skill text already loaded into a conversation cannot be removed. Kamikaze makes Claude stop acting on it. No files on disk are touched, so every skill is available again in the next chat.
- **It does not stop hooks.** A skill that a hook re-injects on every message will keep reappearing. Claude ignores it for the rest of the chat, but the hook has to be disabled in settings to stop it for good.
- **It does not override you.** Your CLAUDE.md, your direct requests, and the system prompt stay in force. Skills you invoke after Kamikaze work normally.
