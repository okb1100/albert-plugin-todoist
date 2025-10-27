"""Todoist plugin for Albert launcher."""

from albert import *
import json
import requests
from pathlib import Path
from typing import List, Optional
from datetime import datetime

md_iid = "3.1"
md_version = "1.0"
md_name = "Todoist"
md_description = "Manage Todoist tasks"

md_license = "MIT"
md_url = "https://github.com/okb1100/albert-plugin-todoist"
md_authors = ["@okb1100"]
md_maintainers = ["@okb1100"]
md_lib_dependencies = ["requests"]


class Plugin(PluginInstance, TriggerQueryHandler):
    def __init__(self):
        PluginInstance.__init__(self)
        TriggerQueryHandler.__init__(self)
        self.api_token = self.readConfig("api_token", str) or ""
        self.max_tasks = int(self.readConfig("max_tasks", int) or 10)
        self.project = self.readConfig("project", str) or "inbox"
        self.show_today_only = bool(self.readConfig("show_today_only", bool) if self.readConfig("show_today_only", bool) is not None else True)
        self.projects = []
        self.tasks = []
        self.user = {}
        self.fuzzy = False
        if not self.api_token:
            info("No Todoist API token configured")

    def id(self) -> str:
        return __name__

    def name(self) -> str:
        return md_name

    def description(self) -> str:
        return md_description

    def defaultTrigger(self) -> str:
        return "td "

    def synopsis(self, query: str) -> str:
        return "td <query> - Search and manage Todoist tasks"

    def supportsFuzzyMatching(self) -> bool:
        return True

    def setFuzzyMatching(self, enabled: bool):
        self.fuzzy = enabled

    def configWidget(self) -> List[dict]:
        return [
            {
                'type': 'label',
                'text': '<b>Todoist Configuration</b>'
            },
            {
                'type': 'lineedit',
                'property': 'api_token',
                'label': 'API Token',
                'widget_properties': {
                    'echoMode': 2,
                    'placeholderText': 'Enter your Todoist API token'
                }
            },
            {
                'type': 'spinbox',
                'property': 'max_tasks',
                'label': 'Max tasks to show',
                'widget_properties': {
                    'minimum': 1,
                    'maximum': 50
                }
            },
            {
                'type': 'lineedit',
                'property': 'project',
                'label': 'Project (name or "inbox")',
                'widget_properties': {
                    'placeholderText': 'Inbox or project name'
                }
            },
            {
                'type': 'checkbox',
                'property': 'show_today_only',
                'label': 'Show today only',
                'checked': True
            },
            {
                'type': 'label',
                'text': 'Get your API token from <a href="https://app.todoist.com/app/settings/integrations/developer">Todoist Settings → Integrations → API token</a>'
            }
        ]

    def __getattr__(self, name):
        if name == 'api_token':
            return self.readConfig('api_token', str) or ""
        if name == 'max_tasks':
            return int(self.readConfig('max_tasks', int) or 10)
        if name == 'project':
            return self.readConfig('project', str) or "inbox"
        if name == 'show_today_only':
            val = self.readConfig('show_today_only', bool)
            return True if val is None else bool(val)
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        if name in ('api_token', 'max_tasks', 'project', 'show_today_only', 'sync_token'):
            try:
                self.writeConfig(name, value)
            except Exception:
                super().__setattr__(name, value)
        else:
            super().__setattr__(name, value)

    def handleTriggerQuery(self, query: Query):
        current_token = self.readConfig("api_token", str) or ""
        if not current_token:
            query.add(StandardItem(
                id="no-token",
                text="No API token configured",
                subtext="Go to plugin settings to configure your Todoist API token",
                iconUrls=[],
                actions=[
                    Action("config", "Open settings", lambda: openUrl("albert://settings"))
                ]
            ))
            return
        query_string = query.string.strip()
        if not query_string:
            self._show_default_options(query)
        elif query_string == "today":
            self._show_today_tasks(query)
        elif query_string.startswith("add "):
            self._handle_add_task(query, query_string[4:])
        elif query_string.startswith("project "):
            self._handle_project_query(query, query_string[8:])
        else:
            self._search_tasks(query, query_string)

    def _show_default_options(self, query: Query):
        items = [
            StandardItem(
                id="add-task",
                text="Add new task",
                subtext="td add <task content>",
                iconUrls=[],
                actions=[
                    Action("add", "Add task", lambda: self._quick_add_task())
                ]
            ),
            # StandardItem(
            #     id="today-tasks",
            #     text="Today's tasks",
            #     subtext="Show tasks due today",
            #     iconUrls=[],
            #     actions=[
            #         Action("today", "Show today's tasks", lambda: self.handleTriggerQuery(Query('today')))
            #     ]
            # ),
            StandardItem(
                id="refresh",
                text="Refresh tasks",
                subtext="Sync with Todoist",
                iconUrls=[],
                actions=[
                    Action("refresh", "Refresh", lambda: self._refresh_tasks())
                ]
            )
        ]
        query.add(items)
        self._show_today_tasks(query)

    def _handle_add_task(self, query: Query, content: str):
        if content.strip():
            query.add(StandardItem(
                id="add-task-action",
                text=f"Add task: {content}",
                subtext="Press Enter to add this task to Todoist",
                iconUrls=[],
                actions=[
                    Action("add", "Add task", lambda: self._add_task(content))
                ]
            ))

    def _handle_project_query(self, query: Query, project_name: str):
        matcher = Matcher(project_name, MatchConfig(fuzzy=self.fuzzy))
        items = []
        for p in self.projects:
            if matcher.match(p.get('name', '')):
                items.append(StandardItem(
                    id=p.get('id'),
                    text=p.get('name'),
                    subtext=f"Project id: {p.get('id')}",
                    iconUrls=[],
                    actions=[Action('open', 'Open Project', lambda pid=p.get('id'): openUrl(f"https://todoist.com/app/project/{pid}"))]
                ))
        if not items:
            query.add(StandardItem(id='no-project', text='No matching projects', subtext='Try a different name', iconUrls=[]))
        else:
            query.add(items)

    def _search_tasks(self, query: Query, search_term: str):
        matcher = Matcher(search_term, MatchConfig(fuzzy=self.fuzzy))
        items = []
        for t in self.tasks:
            if matcher.match(t.get('content', '')):
                due = t.get('due')
                due_str = due.get('date') if due and due.get('date') else (due.get('datetime') if due else '')
                items.append(StandardItem(
                    id=t.get('id'),
                    text=t.get('content', ''),
                    subtext=f"Due: {due_str}",
                    iconUrls=[],
                    actions=[Action('open', 'Open Task', lambda tid=t.get('id'): openUrl(f"https://todoist.com/app/task/{tid}"))]
                ))
        if not items:
            query.add(StandardItem(id='no-results', text='No matching tasks', subtext='Try a different query', iconUrls=[]))
        else:
            query.add(items)

    def _add_task(self, content: str):
        current_token = self.readConfig("api_token", str) or ""
        if not current_token:
            return
        try:
            headers = {
                'Authorization': f'Bearer {current_token}',
                'Content-Type': 'application/json'
            }
            data = {
                'content': content
            }
            response = requests.post(
                'https://api.todoist.com/rest/v2/tasks',
                headers=headers,
                json=data
            )
            if response.status_code == 200:
                info(f"Task added successfully: {content}")
                notification = Notification("Todoist", f"Task added: {content}")
                notification.send()
            else:
                try:
                    err = response.json()
                    warning(f"Failed to add task: {response.status_code} {err}")
                except Exception:
                    warning(f"Failed to add task: {response.status_code}")
        except Exception as e:
            critical(f"Error adding task: {str(e)}")

    def _refresh_tasks(self):
        current_token = self.readConfig("api_token", str) or ""
        if not current_token:
            warning("No API token configured")
            return
        sync_token = self.readConfig('sync_token', str) or '*'
        headers = {
            'Authorization': f'Bearer {current_token}'
        }
        payload = {
            'sync_token': "*",
            'resource_types': json.dumps(["items", "projects", "user"])
        }
        info("Syncing with Todoist...")
        try:
            resp = requests.post('https://api.todoist.com/api/v1/sync', headers=headers, data=payload, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                new_token = data.get('sync_token')
                if new_token:
                    try:
                        self.writeConfig('sync_token', new_token)
                    except Exception:
                        pass
                self.projects = data.get('projects', []) or []
                self.tasks = data.get('items', []) or []
                self.user = data.get('user', {}) or {}
                info(f"Synced {len(self.projects)} projects and {len(self.tasks)} tasks")
                Notification('Todoist', f'Synced {len(self.tasks)} tasks').send()
            else:
                try:
                    err = resp.json()
                    warning(f"Sync failed: {resp.status_code} {err}")
                except Exception:
                    warning(f"Sync failed: {resp.status_code}")
        except Exception as e:
            critical(f"Error during sync: {str(e)}")

    def _quick_add_task(self):
        openUrl("https://todoist.com/app/today")

    def _show_today_tasks(self, query: Query):
        # self._refresh_tasks()
        cfg_max = int(self.readConfig('max_tasks', int) or 10)
        cfg_project = self.readConfig('project', str) or 'inbox'
        cfg_show_today = bool(self.readConfig('show_today_only', bool) if self.readConfig('show_today_only', bool) is not None else True)
        project_id = None
        if cfg_project.lower() in ('inbox', 'inbox_project'):
            project_id = self.user.get('inbox_project_id')
        else:
            for p in self.projects:
                if p.get('name', '').lower() == cfg_project.lower():
                    project_id = p.get('id')
                    break
            if not project_id:
                project_id = cfg_project

        def due_is_today(due):
            if not due:
                return False
            date_str = due.get('date') or due.get('datetime')
            if not date_str:
                return False
            try:
                if 'T' in date_str:
                    dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    d = dt.date()
                else:
                    d = datetime.strptime(date_str, '%Y-%m-%d').date()
                return d == datetime.utcnow().date()
            except Exception:
                return False

        filtered = []
        for t in self.tasks:
            # if project_id and str(t.get('project_id')) != str(project_id):
                # continue
            if t.get('checked'):
                continue
            if t.get('is_deleted'):
                continue
            if cfg_show_today:
                if not due_is_today(t.get('due')):
                    continue
            filtered.append(t)

        filtered.sort(key=lambda x: x.get('day_order', 0) if x.get('day_order') is not None else 0)
        items = []
        for t in filtered[:cfg_max]:
            due = t.get('due')
            due_str = ''
            if due:
                due_str = due.get('date') or due.get('datetime') or ''
            items.append(StandardItem(
                id=t.get('id'),
                text=t.get('content', ''),
                subtext=f"{due_str}",
                iconUrls=[],
                actions=[Action('open', 'Open Task', lambda tid=t.get('id'): openUrl(f"https://todoist.com/app/task/{tid}"))]
            ))

        if not items:
            query.add(StandardItem(id='no-tasks', text='No tasks', subtext='No tasks matched the filters', iconUrls=[]))
        else:
            query.add(items)