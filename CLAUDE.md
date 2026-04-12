# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

An Albert launcher plugin (v34+) that integrates with Todoist via the Sync API v1. Single-file Python plugin (`__init__.py`) using Albert Python API v5.0.

## Architecture

The entire plugin lives in `__init__.py`. The `Plugin` class inherits from `PluginInstance` and `GeneratorQueryHandler` (Albert API v5.0). Key patterns:

- **Query routing**: `items()` dispatches on query prefix — empty (default view), `today`, `add <content>`, `project <name>`, or freeform search
- **Background sync**: `_refresh_tasks()` spawns a daemon thread calling the Todoist Sync API (`/api/v1/sync`), storing projects/tasks/user in memory (no local persistence)
- **Config**: Uses Albert's `readConfig`/`writeConfig` for settings (api_token, max_tasks, project, show_today_only), exposed as properties with a `configWidget()` for the settings UI
- **Task creation**: Uses Todoist Quick Add API (`/api/v1/tasks/quick`) which supports natural language parsing

## API Details

- Base URL: `https://api.todoist.com/api/v1`
- Auth: Bearer token from user config
- Endpoints used: `/sync` (full sync), `/tasks/quick` (quick add), `/tasks/{id}/close` (complete)

## Dependencies

- `requests` (only external dependency)
- Albert Python API (`from albert import *`) — provides `PluginInstance`, `GeneratorQueryHandler`, `StandardItem`, `Action`, `Matcher`, `MatchConfig`, `Icon`, `Notification`, `openUrl`, logging functions

## Development

No build step or tests. To develop, edit `__init__.py` and restart Albert (or reload the plugin). The plugin is loaded from this directory by Albert's plugin system via `metadata.json`.

Trigger keyword: `td ` (with trailing space).
