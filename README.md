# Socialia (<code>socialia</code>)

<p align="center">
  <a href="https://scitex.ai">
    <img src="docs/scitex-logo-blue-cropped.png" alt="SciTeX" width="400">
  </a>
</p>

<p align="center"><b>Unified social media management — posting, analytics, and insights</b></p>

<p align="center">
  <a href="https://socialia.readthedocs.io/">Full Documentation</a> · <code>uv pip install socialia[all]</code>
</p>

<!-- scitex-badges:start -->
<p align="center">
  <a href="https://pypi.org/project/socialia/"><img src="https://img.shields.io/pypi/v/socialia?label=pypi" alt="pypi"></a>
  <a href="https://pypi.org/project/socialia/"><img src="https://img.shields.io/pypi/pyversions/socialia?label=python" alt="python"></a>
  <a href="https://github.com/ywatanabe1989/socialia/actions/workflows/rtd-sphinx-build-on-ubuntu-latest.yml"><img src="https://img.shields.io/github/actions/workflow/status/ywatanabe1989/socialia/rtd-sphinx-build-on-ubuntu-latest.yml?branch=develop&label=docs" alt="docs"></a>
  <a href="https://socialia.readthedocs.io/en/latest/"><img src="https://img.shields.io/readthedocs/socialia?label=docs" alt="docs"></a>
</p>
<p align="center">
  <a href="https://github.com/ywatanabe1989/socialia/actions/workflows/pytest-matrix-on-ubuntu-py3-11-3-12-3-13.yml"><img src="https://img.shields.io/github/actions/workflow/status/ywatanabe1989/socialia/pytest-matrix-on-ubuntu-py3-11-3-12-3-13.yml?branch=develop&label=tests" alt="tests"></a>
  <a href="https://github.com/ywatanabe1989/socialia/actions/workflows/import-smoke-on-ubuntu-py3-12.yml"><img src="https://img.shields.io/github/actions/workflow/status/ywatanabe1989/socialia/import-smoke-on-ubuntu-py3-12.yml?branch=develop&label=install-check" alt="install-check"></a>
  <a href="https://github.com/ywatanabe1989/socialia/actions/workflows/quality-audit-on-ubuntu-latest.yml"><img src="https://img.shields.io/github/actions/workflow/status/ywatanabe1989/socialia/quality-audit-on-ubuntu-latest.yml?branch=develop&label=quality" alt="quality"></a>
  <a href="https://codecov.io/gh/ywatanabe1989/socialia"><img src="https://img.shields.io/codecov/c/github/ywatanabe1989/socialia/develop?label=cov" alt="cov"></a>
</p>
<!-- scitex-badges:end -->

---

## Problem and Solution


| # | Problem | Solution |
|---|---------|----------|
| 1 | **Each social platform has a different API** -- tweepy + LinkedIn UGC + PRAW + slack-sdk + YouTube Data API + GA4 — 6 different auth stories | **Unified `socialia post <platform>`** -- one CLI + MCP interface across Twitter / LinkedIn / Reddit / Slack / YouTube; auth handled behind the scenes |
| 2 | Agents need to **post and retract** without clicking, but every platform's Python SDK is a different shape | MCP tools `social_post` / `social_delete` / `social_status` give agents **one call per action** with a structured response |

## Quick Start

```python
from socialia import Twitter, LinkedIn, Reddit, YouTube, GoogleAnalytics

# Post to Twitter
twitter = Twitter()
twitter.post("Hello World!")

# Post to LinkedIn
linkedin = LinkedIn()
linkedin.post("Professional update!")

# Track analytics
ga = GoogleAnalytics()
ga.track_event("page_view", {"page": "/docs"})
```


## Demo

```bash
# One-shot post across platforms (uses ~/.scitex/socialia/config.yaml creds)
socialia post twitter "Hello World!"
socialia post linkedin --file drafts/announce.md

# Schedule + analytics
socialia schedule list
socialia analytics show-pageviews --days 7
```

![socialia CLI demo](docs/cli-demo.svg)

## Installation

```bash
uv pip install "socialia[all]"
```

> **Recommended**: `uv pip install socialia[all]` —
> uv's Rust resolver handles the SciTeX dep set in 1-3 min where
> pip's serial backtracker can take 30+ min on the full extras.
> Plain `pip install` still works; the extras matrix below shows both.

<details>
<summary><b>Extras matrix</b></summary>

| Extra | Install | Enables |
|-------|---------|---------|
| (core) | `pip install socialia` | Twitter/X, LinkedIn, Slack posting, scheduling, org drafts |
| reddit | `pip install socialia[reddit]` | Reddit via PRAW |
| youtube | `pip install socialia[youtube]` | YouTube Data API upload |
| analytics | `pip install socialia[analytics]` | Google Analytics Data API |
| mcp | `pip install socialia[mcp]` | MCP server tools |
| docs | `pip install socialia[docs]` | Sphinx documentation build |
| all | `pip install socialia[all]` | Everything |

</details>

## Architecture

```mermaid
flowchart LR
    drafts[drafts content<br/>*.org / *.md] --> core
    projects[campaign defs<br/>projects/*.yaml] --> core
    creds[credentials + scheduler<br/>~/.scitex/socialia/] --> core
    core[socialia core<br/>post · schedule · analytics · grow · feed] --> adapters
    adapters[per-platform adapters<br/>twitter · linkedin · reddit<br/>youtube · slack · analytics] --> platforms[platform APIs]
```

<p align="center"><sub><b>Figure 1.</b> Drafts, campaign files, and stored credentials flow through one Python core to per-platform adapters.</sub></p>

A single Python core dispatches to per-platform adapters; CLI / MCP
share the same Python API surface.

## Four Interfaces

### MCP ⭐⭐⭐ (primary)

Agent-friendly tools (`social_post`, `social_delete`, `social_status`,
analytics helpers) served over one MCP server — see the
<details><summary><b>MCP Server</b></summary> section below.

### Python API ⭐⭐

One client per platform (`Twitter`, `LinkedIn`, `Reddit`, `YouTube`,
`GoogleAnalytics`) sharing a common base — see
<details><summary><b>Python API</b></summary> below.

### CLI ⭐⭐

`socialia post / schedule / analytics / grow / feed` on one command tree —
see <details><summary><b>CLI Usage</b></summary> below.

### Skills ⭐

Packaged agent skills under `src/socialia/_skills` with their own
quality gate (`tests/develop/test_skills_quality.py`).


<details>
<summary><b>CLI Usage</b></summary>

```bash
# Check all platform connections at once
socialia check

# Get recent posts from all platforms
socialia feed
socialia feed --detail        # Full text with URLs
socialia feed --mentions      # Get mentions/notifications
socialia feed --replies       # Get replies to your posts (Twitter)

# Optional Xquik read backend
SOCIALIA_X_READ_BACKEND=xquik
SOCIALIA_X_READ_USERNAME=your_handle
XQUIK_API_KEY=xq_...

# Get user profile info
socialia me twitter

# Post to Twitter
socialia post twitter "Hello World!"

# Schedule a post for later
socialia post twitter "Hello!" --schedule "10:00"
socialia post twitter "Hello!" --schedule "2026-01-23 10:00"
socialia post twitter "Hello!" --schedule "+1h"

# Manage scheduled posts
socialia schedule list        # View pending posts
socialia schedule cancel ID   # Cancel a scheduled post
socialia schedule daemon      # Run scheduler in background

# Post to LinkedIn
socialia post linkedin "Professional update!"

# Post to Reddit
socialia post reddit "Post body" --subreddit python --title "Post Title"

# Post to YouTube (video upload)
socialia post youtube "Description" --video video.mp4 --title "My Video"

# Analytics tracking
socialia analytics track page_view --param page /docs

# Get realtime users
socialia analytics realtime

# Post from file
socialia post twitter --file tweet.txt

# Delete a post
socialia delete twitter 1234567890

# Post a thread (separate posts with ---)
socialia thread twitter --file thread.txt

# Dry run (preview without posting)
socialia post twitter "Test" --dry-run

# Show all commands
socialia --help-recursive

# JSON output
socialia feed --json

# Shell completion
socialia completion bash      # Print bash completion script
socialia completion zsh       # Print zsh completion script
socialia completion install   # Auto-install to shell config
socialia completion status    # Check installation status

# Org mode draft management (Emacs integration)
socialia org init drafts.org              # Create template
socialia org status drafts.org            # Show draft status
socialia org list drafts.org              # List all drafts
socialia org schedule drafts.org          # Schedule future posts
socialia org post drafts.org              # Post due drafts
socialia org post drafts.org --dry-run    # Preview without posting
```

</details>

<details>
<summary><b>Org Mode Integration</b></summary>

Manage social media drafts in Emacs org mode files:

```org
* Twitter Drafts [0/2]

** TODO [#A] My First Post
   SCHEDULED: <2026-01-24 Fri 10:00>
   :PROPERTIES:
   :PLATFORM: twitter
   :END:

Post content goes here.
Multiple lines supported.

** TODO [#B] Second Post
   SCHEDULED: <2026-01-25 Sat 10:00>
   :PROPERTIES:
   :PLATFORM: linkedin
   :END:

Another draft for LinkedIn.
```

**Features:**
- Parse org files with TODO/DONE status
- Support SCHEDULED timestamps
- Platform selection via :PLATFORM: property
- Automatic status update after posting
- Dry-run mode for previewing

```bash
# Create a new drafts file
socialia org init ~/drafts/january.org --platform twitter

# Check status of all drafts
socialia org status ~/drafts/january.org

# Schedule all future posts
socialia org schedule ~/drafts/january.org

# Post all due drafts (scheduled time passed)
socialia org post ~/drafts/january.org

# Run scheduler daemon to auto-post
socialia schedule daemon
```

```python
from socialia.org import OrgDraftManager

manager = OrgDraftManager("drafts.org")
manager.status_report()      # Get overview
manager.get_pending()        # List TODO drafts
manager.get_due()            # Get drafts ready to post
manager.schedule_all()       # Schedule future posts
manager.post_draft(draft, dry_run=True)  # Post with preview
```

</details>

<details>
<summary><b>Python API</b></summary>

```python
from socialia import Twitter, LinkedIn, Reddit, YouTube, GoogleAnalytics

# Check connection and get user info
twitter = Twitter()
twitter.check()      # Verify connection
twitter.me()         # Get user profile
twitter.feed()       # Get recent tweets
twitter.mentions()   # Get mentions
twitter.replies()    # Get replies to your posts

# Post content
twitter.post("Hello World!")
twitter.post_thread(["First", "Second", "Third"])
twitter.delete("1234567890")

# LinkedIn
linkedin = LinkedIn()
linkedin.post("Professional update!")
linkedin.me()        # Get user info

# Reddit (requires: pip install socialia[reddit])
reddit = Reddit()
reddit.post("Post body", subreddit="test", title="Title")
reddit.feed()        # Get recent posts
reddit.mentions()    # Get inbox mentions
reddit.update("post_id", "Updated text")  # Edit post

# YouTube (requires: pip install socialia[youtube])
youtube = YouTube()
youtube.post("Description", video_path="video.mp4", title="My Video")
youtube.feed()       # Get recent videos
youtube.update("video_id", title="New Title")

# Google Analytics (requires: pip install socialia[analytics])
ga = GoogleAnalytics()
ga.track_event("social_post", {"platform": "twitter", "post_id": "123"})
ga.get_page_views(start_date="7daysAgo", end_date="today")
```

</details>

<details>
<summary><b>MCP Server</b></summary>

```bash
# Check server health and credentials
socialia mcp doctor

# List available MCP tools
socialia mcp list-tools

# Show Claude Desktop configuration
socialia mcp installation

# Start the MCP server
socialia mcp start
```

Add to Claude Code settings:

```json
{
  "mcpServers": {
    "socialia": {
      "command": "socialia",
      "args": ["mcp", "start"],
      "env": {
        "SOCIALIA_X_CONSUMER_KEY": "...",
        "SOCIALIA_X_CONSUMER_KEY_SECRET": "...",
        "SOCIALIA_X_ACCESSTOKEN": "...",
        "SOCIALIA_X_ACCESSTOKEN_SECRET": "..."
      }
    }
  }
}
```

</details>

<details>
<summary><b>Environment Variables</b></summary>

```bash
# Twitter/X
export SOCIALIA_X_CONSUMER_KEY="your_consumer_key"
export SOCIALIA_X_CONSUMER_KEY_SECRET="your_consumer_secret"
export SOCIALIA_X_ACCESSTOKEN="your_access_token"
export SOCIALIA_X_ACCESSTOKEN_SECRET="your_access_token_secret"

# LinkedIn
export SOCIALIA_LINKEDIN_ACCESS_TOKEN="your_access_token"

# Reddit
export SOCIALIA_REDDIT_CLIENT_ID="your_client_id"
export SOCIALIA_REDDIT_CLIENT_SECRET="your_client_secret"
export SOCIALIA_REDDIT_USERNAME="your_username"
export SOCIALIA_REDDIT_PASSWORD="your_password"

# YouTube
export SOCIALIA_YOUTUBE_CLIENT_SECRETS_FILE="path/to/client_secrets.json"

# Google Analytics
export SOCIALIA_GOOGLE_ANALYTICS_MEASUREMENT_ID="G-XXXXXXXXXX"
export SOCIALIA_GOOGLE_ANALYTICS_API_SECRET="your_api_secret"
export SOCIALIA_GOOGLE_ANALYTICS_PROPERTY_ID="123456789"  # Optional, for Data API
```

**Detailed setup guide:** `socialia setup` or see [docs/SETUP.md](docs/SETUP.md)

</details>

<details>
<summary><b>Supported Platforms</b></summary>

| Platform | Status | API | Install |
|----------|--------|-----|---------|
| Twitter/X | Ready | v2 OAuth 1.0a | `pip install socialia` |
| LinkedIn | Ready | v2 OAuth 2.0 | `pip install socialia` |
| Reddit | Ready | PRAW | `pip install socialia[reddit]` |
| Slack | Ready | slack-sdk | `pip install socialia` |
| YouTube | Ready | Data API v3 | `pip install socialia[youtube]` |
| Google Analytics | Ready | GA4 + Data API | `pip install socialia[analytics]` |

</details>

<details>
<summary><b>Project Structure</b></summary>

```
socialia/
├── src/socialia/         # Python package
│   ├── cli/              # CLI with argparse
│   ├── _mcp/             # MCP tools and handlers
│   ├── twitter.py        # Twitter/X API
│   ├── linkedin.py       # LinkedIn API
│   ├── reddit.py         # Reddit API (PRAW)
│   ├── youtube.py        # YouTube API
│   ├── youtube_batch.py  # YouTube batch upload configs
│   ├── slack.py          # Slack messaging
│   ├── analytics.py      # Google Analytics
│   ├── scheduler.py      # Post scheduling system
│   ├── org.py            # Org mode draft management
│   ├── org_files.py      # File lifecycle helpers (draft/scheduled/posted)
│   ├── mcp_server.py     # MCP server (delegates to CLI)
│   ├── _server.py        # Platform-specific content strategies
│   ├── _base.py          # Base class
│   ├── _branding.py      # Branding/env prefix resolution
│   ├── _twitter/           # Twitter/X subpackage
│   │   ├── growth.py       # Follow/growth automation
│   │   ├── media.py        # Media upload
│   │   └── read_backend.py # Optional Xquik read backend
├── docs/
│   ├── platforms/        # Platform API documentation
│   ├── sphinx/           # Sphinx/ReadTheDocs sources
│   └── SETUP.md          # Step-by-step setup guide
├── examples/             # Usage examples
├── Makefile              # Command dispatcher
├── pyproject.toml
└── .env                  # Credentials (gitignored)
```

</details>

<details>
<summary><b>SciTeX Integration</b></summary>

Socialia is part of the SciTeX ecosystem:

```bash
# Install via scitex
pip install scitex[social]

# Use in research workflows
import scitex as stx
from socialia import Twitter

@stx.session
def share_results(twitter=stx.INJECTED):
    # Auto-configured from scitex settings
    twitter.post("New research results!")
```

</details>

## Part of SciTeX

`socialia` is part of [**SciTeX**](https://scitex.ai).

>Four Freedoms for Research
>
>0. The freedom to **run** your research anywhere — your machine, your terms.
>1. The freedom to **study** how every step works — from raw data to final manuscript.
>2. The freedom to **redistribute** your workflows, not just your papers.
>3. The freedom to **modify** any module and share improvements with the community.
>
>AGPL-3.0 — because we believe research infrastructure deserves the same freedoms as the software it runs on.

---

<p align="center">
  <a href="https://scitex.ai" target="_blank"><img src="docs/scitex-icon-navy-inverted.png" alt="SciTeX" width="40"/></a>
  <br>
  AGPL-3.0
</p>
