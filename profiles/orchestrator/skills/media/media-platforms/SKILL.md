---
name: media-platforms
description: "Media and social platforms: GIF search (Tenor), email (Himalaya), Spotify music, X/Twitter (xurl), YouTube content."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [gif, email, spotify, twitter, youtube, media, social]
    category: media
---

# Media Platforms Suite

Five tools for media and social platform interaction.

---

## Mode A: GIF Search (Tenor)

**Trigger:** "gif", "animated", "reaction gif", "tenor"

Search/download GIFs from Tenor via curl + jq. No API key needed for basic search.
```bash
curl -s "https://tenor.googleapis.com/v2/search?q={query}&key={API_KEY}&limit=5&media_filter=minimal"
```

Requires a Tenor API key (free from Google Cloud Console). Returns GIF URLs, preview URLs, and metadata.

---

## Mode B: Email (Himalaya CLI)

**Trigger:** "email", "imap", "smtp", "gmail", "read mail", "send email"

Himalaya CLI: IMAP/SMTP email from terminal. Covers:
- Read inbox, search, threads, attachments
- Compose and send emails
- Folder/mailbox management
- Multiple account support

Configuration in `~/.config/himalaya/config.toml`:
```toml
[accounts.personal]
email = "user@example.com"
backend.type = "imap"
backend.host = "imap.example.com"
backend.port = 993
backend.encryption = "tls"
backend.login = "user@example.com"
backend.auth.type = "password"
backend.auth.raw = "password"
```

Send via SMTP configured similarly. Supports OAuth2 for Gmail.

---

## Mode C: Spotify

**Trigger:** "spotify", "play music", "playlist", "now playing", "search track"

Spotify: play, search, queue, manage playlists and devices. Requires Spotify Premium and OAuth setup.

Key operations:
- **Search:** `spotify search <query> --type track,artist,album,playlist`
- **Play:** `spotify play <uri>` or `spotify play --name <device>`
- **Queue:** `spotify queue <uri>`
- **Playback control:** `spotify pause`, `spotify next`, `spotify previous`, `spotify volume <0-100>`
- **Playlists:** `spotify playlist create <name>`, `spotify playlist add <uri> --playlist <id>`
- **Devices:** `spotify devices` — list available playback devices

Requires `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET` environment variables.

---

## Mode D: X/Twitter (xurl CLI)

**Trigger:** "tweet", "post to X", "twitter", "search tweets", "DM"

X/Twitter via xurl CLI: post, search, DM, media, v2 API.

Key operations:
- **Post:** `xurl post "Tweet text"`
- **Search:** `xurl search "query"` — recent tweets matching query
- **DM:** `xurl dm send <user_id> "message"`
- **Media:** `xurl media upload <file>` — upload images/video for tweets
- **Thread:** Post multiple tweets in sequence
- **Profile:** `xurl profile <username>` — get user info

Requires OAuth 1.0a credentials (consumer key/secret + access token/secret).

---

## Mode E: YouTube Content

**Trigger:** "youtube", "video transcript", "summarize video", "youtube channel"

YouTube transcripts to summaries, threads, blogs. Key operations:
- Extract transcript from video URL
- Summarize video content
- Convert transcript to blog post or thread format
- Extract chapters/timestamps

Uses YouTube's transcript API or yt-dlp for video metadata. No API key needed for transcript extraction.

Workflow: URL → transcript → analyze content → generate output (summary, blog, thread, key points).