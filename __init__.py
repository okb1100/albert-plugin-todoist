"""Todoist plugin for Albert launcher."""

from albert import *
import json
import requests
import threading
from datetime import datetime, date

md_iid = "4.0"
md_version = "1.2"
md_name = "Todoist"
md_description = "Manage Todoist tasks"
md_license = "MIT"
md_url = "https://github.com/okb1100/albert-plugin-todoist"
md_authors = ["@okb1100"]
md_maintainers = ["@okb1100"]
md_lib_dependencies = ["requests"]

# API endpoints
TODOIST_API_BASE = "https://api.todoist.com/api/v1"
TODOIST_WEB_BASE = "https://todoist.com/app"


class Plugin(PluginInstance, TriggerQueryHandler):
    """Todoist integration for Albert launcher."""

    def __init__(self):
        PluginInstance.__init__(self)
        TriggerQueryHandler.__init__(self)

        # Runtime state (not persisted)
        self._projects: list = []
        self._tasks: list = []
        self._user: dict = {}
        self._fuzzy: bool = False
        self._syncing: bool = False

        # Initial sync if token is configured
        if self._get_api_token():
            self._refresh_tasks(show_notification=False)
        else:
            info("No Todoist API token configured")

    # -------------------------------------------------------------------------
    # Extension interface
    # -------------------------------------------------------------------------

    def id(self) -> str:
        return __name__

    def name(self) -> str:
        return md_name

    def description(self) -> str:
        return md_description

    def defaultTrigger(self) -> str:
        return "td "

    def synopsis(self, query: str) -> str:
        return "<query> | add <task> | project <name>"

    def supportsFuzzyMatching(self) -> bool:
        return True

    def setFuzzyMatching(self, enabled: bool):
        self._fuzzy = enabled

    # -------------------------------------------------------------------------
    # Config helpers (cached reads to avoid I/O on every keystroke)
    # -------------------------------------------------------------------------

    def _get_api_token(self) -> str:
        return self.readConfig("api_token", str) or ""

    def _get_max_tasks(self) -> int:
        return int(self.readConfig("max_tasks", int) or 10)

    def _get_project_filter(self) -> str:
        return self.readConfig("project", str) or "inbox"

    def _get_show_today_only(self) -> bool:
        val = self.readConfig("show_today_only", bool)
        return True if val is None else bool(val)

    # -------------------------------------------------------------------------
    # Config widget (for Albert settings UI)
    # -------------------------------------------------------------------------

    @property
    def api_token(self) -> str:
        return self._get_api_token()

    @api_token.setter
    def api_token(self, value: str):
        self.writeConfig("api_token", value)

    @property
    def max_tasks(self) -> int:
        return self._get_max_tasks()

    @max_tasks.setter
    def max_tasks(self, value: int):
        self.writeConfig("max_tasks", value)

    @property
    def project(self) -> str:
        return self._get_project_filter()

    @project.setter
    def project(self, value: str):
        self.writeConfig("project", value)

    @property
    def show_today_only(self) -> bool:
        return self._get_show_today_only()

    @show_today_only.setter
    def show_today_only(self, value: bool):
        self.writeConfig("show_today_only", value)

    def configWidget(self) -> list:
        return [
            {
                "type": "label",
                "text": "<b>Todoist Configuration</b>",
            },
            {
                "type": "lineedit",
                "property": "api_token",
                "label": "API Token",
                "widget_properties": {
                    "echoMode": 2,
                    "placeholderText": "Enter your Todoist API token",
                },
            },
            {
                "type": "spinbox",
                "property": "max_tasks",
                "label": "Max tasks to show",
                "widget_properties": {"minimum": 1, "maximum": 50},
            },
            {
                "type": "lineedit",
                "property": "project",
                "label": 'Project (name or "inbox")',
                "widget_properties": {"placeholderText": "Inbox or project name"},
            },
            {
                "type": "checkbox",
                "property": "show_today_only",
                "label": "Show today only",
            },
            {
                "type": "label",
                "text": 'Get your API token from <a href="https://app.todoist.com/app/settings/integrations/developer">Todoist Settings</a>',
            },
        ]

    # -------------------------------------------------------------------------
    # Query handling
    # -------------------------------------------------------------------------

    def handleTriggerQuery(self, query: Query):
        if not query.isValid:
            return

        token = self._get_api_token()
        if not token:
            query.add(self._make_no_token_item())
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
        if not query.isValid:
            return

        items = [
            StandardItem(
                id="add-task",
                text="Add new task",
                subtext="td add <task content>",
                actions=[Action("add", "Open Todoist", lambda: openUrl(f"{TODOIST_WEB_BASE}/today"))],
            ),
            StandardItem(
                id="refresh",
                text="Refresh tasks",
                subtext="Sync with Todoist",
                actions=[Action("refresh", "Refresh", lambda: self._refresh_tasks())],
            ),
        ]
        query.add(items)
        self._show_today_tasks(query)

    def _handle_add_task(self, query: Query, content: str):
        if not query.isValid:
            return

        content = content.strip()
        if not content:
            return

        query.add(
            StandardItem(
                id="add-task-action",
                text=f"Add task: {content}",
                subtext="dates, #Project, @label, p1-p4, // description",
                actions=[Action("add", "Add task", lambda c=content: self._add_task(c))],
            )
        )

    def _handle_project_query(self, query: Query, project_name: str):
        if not query.isValid:
            return

        project_name = project_name.strip()

        # No project name: show all projects
        if not project_name:
            items = [
                StandardItem(
                    id=str(p.get("id")),
                    text=p.get("name", "Unknown"),
                    subtext=f"Type 'td project {p.get('name')}' to see tasks",
                    actions=[
                        Action(
                            "open",
                            "Open Project",
                            lambda pid=p.get("id"): openUrl(f"{TODOIST_WEB_BASE}/project/{pid}"),
                        )
                    ],
                )
                for p in self._projects
            ]
            query.add(items) if items else query.add(self._make_empty_item("No projects"))
            return

        # Find matching project
        matcher = Matcher(project_name, MatchConfig(fuzzy=self._fuzzy))
        matching_project = next((p for p in self._projects if matcher.match(p.get("name", ""))), None)

        if not matching_project:
            query.add(self._make_empty_item("No matching project", "Try a different name"))
            return

        project_id = matching_project.get("id")
        project_display_name = matching_project.get("name", "Unknown")

        # Filter tasks for this project
        project_tasks = [
            t
            for t in self._tasks
            if str(t.get("project_id")) == str(project_id)
            and not t.get("checked")
            and not t.get("is_deleted")
        ]

        if not project_tasks:
            query.add(
                StandardItem(
                    id="no-tasks",
                    text=f"No tasks in {project_display_name}",
                    subtext="All tasks completed or project is empty",
                    actions=[
                        Action("open", "Open Project", lambda: openUrl(f"{TODOIST_WEB_BASE}/project/{project_id}"))
                    ],
                )
            )
            return

        items = [self._make_task_item(t, project_display_name) for t in project_tasks]
        query.add(items)

    def _search_tasks(self, query: Query, search_term: str):
        if not query.isValid:
            return

        matcher = Matcher(search_term, MatchConfig(fuzzy=self._fuzzy))
        items = []

        for t in self._tasks:
            if not query.isValid:
                return
            if t.get("checked") or t.get("is_deleted"):
                continue
            if matcher.match(t.get("content", "")):
                items.append(self._make_task_item(t))

        if items:
            query.add(items)
        else:
            query.add(self._make_empty_item("No matching tasks", "Try a different query"))

    def _show_today_tasks(self, query: Query):
        if not query.isValid:
            return

        max_tasks = self._get_max_tasks()
        show_today = self._get_show_today_only()
        today = date.today()

        # Filter tasks
        filtered = [
            t
            for t in self._tasks
            if not t.get("checked")
            and not t.get("is_deleted")
            and (not show_today or self._is_due_on_date(t.get("due"), today))
        ]

        # Sort by day_order
        filtered.sort(key=lambda x: x.get("day_order") or 0)

        if not filtered:
            query.add(self._make_empty_item("No tasks", "No tasks matched the filters"))
            return

        items = [self._make_task_item(t) for t in filtered[:max_tasks]]
        query.add(items)

    # -------------------------------------------------------------------------
    # Item factory helpers
    # -------------------------------------------------------------------------

    def _make_task_item(self, task: dict, project_name: str = None) -> StandardItem:
        task_id = task.get("id")
        task_content = task.get("content", "")
        due = task.get("due")
        due_str = self._format_due_date(due)

        if project_name:
            subtext = f"{project_name} | {due_str}" if due_str else project_name
        else:
            subtext = due_str

        return StandardItem(
            id=str(task_id),
            text=task_content,
            subtext=subtext,
            actions=[
                Action("open", "Show details", lambda tid=task_id: openUrl(f"{TODOIST_WEB_BASE}/task/{tid}")),
                Action(
                    "done",
                    "Set as done",
                    lambda tid=task_id, tc=task_content: self._complete_task(tid, tc),
                ),
            ],
        )

    def _make_empty_item(self, text: str, subtext: str = "") -> StandardItem:
        return StandardItem(id="empty", text=text, subtext=subtext)

    def _make_no_token_item(self) -> StandardItem:
        return StandardItem(
            id="no-token",
            text="No API token configured",
            subtext="Go to plugin settings to configure your Todoist API token",
            actions=[Action("config", "Open settings", lambda: openUrl("albert://settings"))],
        )

    # -------------------------------------------------------------------------
    # Date helpers
    # -------------------------------------------------------------------------

    def _format_due_date(self, due: dict) -> str:
        if not due:
            return ""
        return due.get("date") or due.get("datetime") or ""

    def _is_due_on_date(self, due: dict, target_date: date) -> bool:
        if not due:
            return False
        date_str = due.get("date") or due.get("datetime")
        if not date_str:
            return False
        try:
            if "T" in date_str:
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                return dt.date() == target_date
            else:
                return datetime.strptime(date_str, "%Y-%m-%d").date() == target_date
        except Exception:
            return False

    # -------------------------------------------------------------------------
    # Todoist API operations
    # -------------------------------------------------------------------------

    def _add_task(self, content: str):
        """Add a task using Quick Add API (supports natural language)."""
        token = self._get_api_token()
        if not token:
            return

        try:
            response = requests.post(
                f"{TODOIST_API_BASE}/tasks/quick",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json={"text": content, "auto_reminder": True},
                timeout=10,
            )

            if response.status_code == 200:
                result = response.json()
                task_content = result.get("content", content)
                info(f"Task added: {task_content}")
                Notification("Todoist", f"Task added: {task_content}").send()
                self._refresh_tasks(show_notification=False)
            else:
                self._log_api_error("add task", response)
        except Exception as e:
            critical(f"Error adding task: {e}")

    def _complete_task(self, task_id: str, task_content: str = ""):
        """Mark a task as completed."""
        token = self._get_api_token()
        if not token:
            return

        try:
            response = requests.post(
                f"{TODOIST_API_BASE}/tasks/{task_id}/close",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
            )

            if response.status_code in (200, 204):
                info(f"Task completed: {task_content}")
                Notification("Todoist", f"Completed: {task_content}").send()
                self._refresh_tasks(show_notification=False)
            else:
                self._log_api_error("complete task", response)
        except Exception as e:
            critical(f"Error completing task: {e}")

    def _refresh_tasks(self, show_notification: bool = True):
        """Start a background sync with Todoist."""
        if self._syncing:
            info("Sync already in progress")
            return

        thread = threading.Thread(target=self._do_sync, args=(show_notification,), daemon=True)
        thread.start()

    def _do_sync(self, show_notification: bool = True):
        """Perform sync in background thread."""
        self._syncing = True
        try:
            token = self._get_api_token()
            if not token:
                warning("No API token configured")
                return

            info("Syncing with Todoist...")
            response = requests.post(
                f"{TODOIST_API_BASE}/sync",
                headers={"Authorization": f"Bearer {token}"},
                data={"sync_token": "*", "resource_types": json.dumps(["items", "projects", "user"])},
                timeout=15,
            )

            if response.status_code == 200:
                data = response.json()
                self._projects = data.get("projects") or []
                self._tasks = data.get("items") or []
                self._user = data.get("user") or {}
                info(f"Synced {len(self._projects)} projects, {len(self._tasks)} tasks")
                if show_notification:
                    Notification("Todoist", f"Synced {len(self._tasks)} tasks").send()
            else:
                self._log_api_error("sync", response)
        except Exception as e:
            critical(f"Error during sync: {e}")
        finally:
            self._syncing = False

    def _log_api_error(self, action: str, response):
        """Log API error with response details."""
        try:
            err = response.json()
            warning(f"Failed to {action}: {response.status_code} {err}")
        except Exception:
            warning(f"Failed to {action}: {response.status_code}")
