# Albert Plugin: Todoist

Manage your Todoist tasks directly from Albert launcher.

## Features

- Add new tasks with natural language support (dates, projects, labels, priorities)
- Search existing tasks
- View today's tasks
- Complete tasks directly from Albert
- Project-specific task management
- Quick access to Todoist web interface

## Setup

1. Get your API token from Todoist Settings → Integrations → API token
2. Configure the token in Albert plugin settings
3. Use `td` trigger to access Todoist functionality

## Usage

- `td` - Show today's tasks and main options
- `td add <content>` - Add new task
- `td project <name>` - Show project tasks
- `td <search>` - Search tasks

### Adding Tasks with Natural Language

When adding tasks, you can use Todoist's natural language features:

- **Dates**: `td add clean the room today`, `td add meeting tomorrow at 3pm`
- **Projects**: `td add Buy book #Books` (use `#` followed by project name without spaces)
- **Labels**: `td add urgent task @work @important`
- **Priority**: `td add important task p1` (p1 is highest, p4 is lowest)
- **Deadlines**: `td add finish report {next friday}`
- **Description**: `td add task title // this is the description`

### Task Actions (Keyboard Shortcuts)

When viewing tasks:

- **Enter** - Open task details in Todoist web
- **Alt + ↓** then **Enter** - Opens the action menu where you can:
  - Show details (open in web)
  - ✓ Set as done (complete the task)

## Installation

1. Clone or copy this plugin to your Albert Python plugins directory
    - MacOS: `git clone git@github.com/okb1100/albert-plugin-todoist ~/Library/Application\ Support/albert/python/plugins`
    - Linux: `git clone git@github.com/okb1100/albert-plugin-todoist ~/.local/share/albert/python/plugins`
2. Restart Albert and enable the plugin in Albert settings
3. Configure your Todoist API token in the plugin settings

## Requirements

- Python 3.6+
- requests library
- Todoist account with API access

## License

MIT License

## Disclaimer

Albert Todoist Plugin is not created by, affiliated with, or supported by Doist
Albert Todoist Plugin is not created by, affiliated with, or supported by Albert Launcher Development Team

