# Todoist for Albert

A plugin for [Albert launcher](https://albertlauncher.github.io/) that integrates with [Todoist](https://todoist.com), bringing task management into your keyboard-driven workflow.

## Features

- **Quick Add** — Create tasks using Todoist's natural language parsing (dates, projects, labels, priorities, descriptions)
- **Today View** — See tasks due today at a glance
- **Search** — Find any task with fuzzy matching
- **Projects** — Browse and filter tasks by project
- **Complete** — Mark tasks as done without leaving Albert

## Requirements

- Albert v34.0.0 or later
- Python 3.9+
- A [Todoist](https://todoist.com) account

## Installation

Clone this repository into your Albert Python plugins directory:

**macOS**
```sh
git clone https://github.com/okb1100/albert-plugin-todoist.git \
  ~/Library/Application\ Support/albert/python/plugins/albert-plugin-todoist
```

**Linux**
```sh
git clone https://github.com/okb1100/albert-plugin-todoist.git \
  ~/.local/share/albert/python/plugins/albert-plugin-todoist
```

Then restart Albert and enable **Todoist** in Settings > Plugins.

## Setup

1. Go to [Todoist Settings > Integrations > Developer](https://app.todoist.com/app/settings/integrations/developer) and copy your API token.
2. Open Albert Settings > Plugins > Todoist and paste your token.

## Usage

All commands use the `td` trigger (with a trailing space).

| Command | Description |
|---|---|
| `td` | Show today's tasks and quick actions |
| `td add <content>` | Add a new task |
| `td today` | Show today's tasks |
| `td project` | List all projects |
| `td project <name>` | Show tasks in a project |
| `td <query>` | Search tasks |

### Natural Language

Task creation supports Todoist's full natural language syntax:

```
td add Buy groceries tomorrow at 5pm #Personal @errands p2
td add Finish report {next friday} // remember to include Q1 data
```

- **Dates** — `today`, `tomorrow`, `next monday`, `jan 15 at 3pm`
- **Projects** — `#ProjectName`
- **Labels** — `@label`
- **Priority** — `p1` (urgent) through `p4` (default)
- **Deadlines** — `{date}` for hard deadlines
- **Description** — `// text` appended after the title

### Actions

When viewing a task, press **Enter** to open it in Todoist. Use **Alt+Down** to reveal additional actions including marking the task as done.

## Configuration

Available in Albert Settings > Plugins > Todoist:

| Setting | Default | Description |
|---|---|---|
| API Token | — | Your Todoist API token |
| Max tasks | 10 | Maximum number of tasks shown (1–50) |
| Project | inbox | Default project filter |
| Show today only | On | Only show tasks due today |

---

## License

[MIT](LICENSE)

## Privacy

This plugin communicates exclusively with the official Todoist API (`api.todoist.com`). Your API token is stored locally in Albert's configuration directory. No data is collected, tracked, or sent to third parties. See [PRIVACY.md](PRIVACY.md) for details.

## Disclaimer

Albert Todoist Plugin is not created by, affiliated with, or supported by Doist

Albert Todoist Plugin is not created by, affiliated with, or supported by Albert Launcher Development Team
