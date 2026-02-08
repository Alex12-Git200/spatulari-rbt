# Spatulari_RBT

A modular, self-managed Discord bot built with **discord.py**, designed for **stability**, **hot-reloading**, and **real backend control** — not restart spam.

Built by **Spatulari**

---

## Features

### Music System

- Local audio playback
- YouTube audio streaming
- Queue system with loop support
- Per-session volume control
- Auto-disconnect when channel empties

### Fun Commands

- Coin flip, dice roll
- Magic 8-ball
- Rate anything
- Slap users
- Touch grass (mandatory)
- Message relay (`!say`) for trusted/staff

### Leveling System

- XP gained from chatting
- Level progression
- Leaderboard
- Auto role reward at **Level 15** (Trusted Member)

### ℹ️ Info & Utility

- Bot uptime
- Server info
- User info (`!whois`)
- Bot diagnostics (`!botinfo`)
- Ping / latency checks
- Loaded cogs & extensions overview

### Moderation

- Kick, ban, timeout
- Permission-safe role handling
- Auto role assignment on join
- Welcome messages + DM greeting

### Core System (Owner)

- Manual cog loading / unloading
- Safe hot-reload system
- Load all / unload all
- Protected core to prevent soft-locks
- Controlled restart & shutdown

---

## Architecture Overview

The bot uses a **modular cog-based architecture** with a protected core system.

```text
src/
├── main.py               # Bot entry point
├── cogs/
│   ├── core.py           # System loader (protected)
│   ├── utils.py          # Info & utility commands
│   ├── fun.py            # Fun commands
│   └── moderation.py     # Moderation commands
├── utils/
│   └── checks.py         # Custom command checks
├── audio/                # Local audio files
├── levels.json           # XP & leveling data
├── config.py             # Bot configuration
└── bot_token.py          # Bot token (ignored)
```

---

This still needs a lot of organazation, ```main.py``` is a monster with over 700 lines, which will be resolved soon.
