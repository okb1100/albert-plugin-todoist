# Albert Plugin: Todoist

Manage your Todoist tasks directly from Albert launcher.

## Features

- Add new tasks quickly
- Search existing tasks
- View today's tasks
- Project-specific task management
- Quick access to Todoist web interface

## Setup

1. Get your API token from Todoist Settings → Integrations → API token
2. Configure the token in Albert plugin settings
3. Use `td` trigger to access Todoist functionality

## Usage

- `td` - Show main options
- `td add <content>` - Add new task
- `td project <name>` - Show project tasks
- `td <search>` - Search tasks

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
