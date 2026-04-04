# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [2.0.0] - 2026-04-04

### Changed

- Migrated to Albert Python plugin API v5.0 (required for Albert v34+)
- Replaced `TriggerQueryHandler` with `GeneratorQueryHandler` (coroutine-based query handling)
- Adopted new `Icon` API with `icon_factory` pattern
- Updated query interface from `Query` to `QueryContext`
- Bumped minimum Albert version to v34.0.0

### Fixed

- Plugin not appearing in Albert v34.x due to outdated interface version

## [1.2.0] - 2026-01-19

### Changed

- Refactored task management and API integration
- Improved task completion with background syncing

## [1.1.0] - 2025-12-15

### Added

- Natural language task creation (dates, projects, labels, priorities, descriptions)
- Project-specific task browsing and filtering
- Fuzzy search support

## [1.0.0] - 2025-12-01

### Added

- Initial release
- View today's tasks
- Add tasks via Quick Add API
- Complete tasks from Albert
- Search tasks
- Configurable API token, max tasks, project filter, and today-only mode
