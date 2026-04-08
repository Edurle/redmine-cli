---
name: redmine-cli
description: |
  Manage Redmine project management tasks via the redmine CLI tool.
  Use when the user asks to: create/view/update/delete issues, list projects
  or project members, check user info, log time entries, view time reports,
  or perform any Redmine-related task.
  Trigger words: redmine, issue, task, project, time entry, log time,
  bug tracker, ticket, assignee, sprint, workload.
---

# Redmine CLI Tool Guide

## Installation

The CLI can be installed via **conda** or **pip**. Choose one:

### Method A: Conda (Recommended)

```bash
git clone git@github.com:Edurle/redmine-cli.git
cd redmine-cli
conda create -n redmine-cli python=3.12 -y
conda run -n redmine-cli pip install -e .
```

All commands must be prefixed with `conda run -n redmine-cli`:

```bash
conda run -n redmine-cli redmine --help
conda run -n redmine-cli redmine config test
conda run -n redmine-cli redmine my-issues
```

Or activate the environment first to use `redmine` directly:

```bash
conda activate redmine-cli
redmine --help
redmine my-issues
```

### Method B: pip (system Python)

```bash
cd redmine-cli
pip install -e .          # or: pip3 install -e .
# or with dev dependencies:
pip install -e ".[dev]"
```

After pip install, use `redmine` directly:

```bash
redmine --help
redmine config test
redmine my-issues
```

If `redmine` is not on PATH, run as a Python module:

```bash
python -m redmine_cli.main --help       # or: python3 -m redmine_cli.main --help
python -m redmine_cli.main config test
python -m redmine_cli.main my-issues
```

### How to Detect the Installation Method

Run these checks in order:

```bash
# Check conda environment
conda env list 2>/dev/null | grep redmine-cli

# Check if redmine command is available
which redmine 2>/dev/null

# Check if the package is installed
python -c "import redmine_cli; print(redmine_cli.__version__)"
```

**Decision logic:**
1. If conda env `redmine-cli` exists → use `conda run -n redmine-cli redmine <args>`
2. Else if `redmine` is on PATH → use `redmine <args>` directly
3. Else → use `python -m redmine_cli.main <args>`

## Prerequisites

Before using the CLI, verify it is installed and configured:

```bash
redmine --help                    # Verify CLI is installed
redmine config test               # Verify connection is working
```

## Configuration Guide

If `redmine config test` fails or returns an error, the CLI needs to be configured.
There are two ways to configure the connection:

### Method 1: Config File (Recommended)

1. Initialize a config template:
```bash
redmine config init
```

2. Edit the config file at `~/.redmine-cli/config.toml`:
```toml
# Optional: set default profile name
default_profile = "work"

[profiles.work]
url = "http://your-redmine-server.example.com"
api_key = "your-api-key-here"
default_project = "project-identifier"   # optional, used as default -p value

# You can add multiple profiles
[profiles.personal]
url = "http://another-redmine.example.com"
api_key = "another-api-key"
```

3. Verify the connection:
```bash
redmine config test
```

### Method 2: Environment Variables

Set environment variables (useful for CI/CD or temporary sessions):
```bash
export REDMINE_URL="http://your-redmine-server.example.com"
export REDMINE_API_KEY="your-api-key-here"
redmine config test
```

Environment variables take **priority** over the config file.

### How to Get Your API Key

1. Log in to your Redmine web interface
2. Go to **My account** (top-right corner, `/my/account`)
3. In the right sidebar, find **API access key**
4. Click **Show** to reveal the key, then copy it
5. Make sure **Enable REST API** is checked in Administration > Settings > API

### How to Find Project Identifier

When creating issues or filtering by project, you need the project identifier (not the display name):

```bash
redmine projects list                        # List all projects with identifiers
redmine projects show PROJECT_IDENTIFIER     # View a specific project
```

The `identifier` column shows the value to use with `-p` options.

### Multi-Profile Usage

If you have multiple Redmine servers, use the `--profile` option:
```bash
redmine --profile work my-issues
redmine --profile personal projects list
```

## Quick Reference

### Check my tasks
```bash
redmine my-issues
redmine my-issues --status closed --format json
redmine issues list --assignee me --status open --format json
```

### View issue detail
```bash
redmine issues show ISSUE_ID
redmine issues show ISSUE_ID --format json
redmine issues show ISSUE_ID --include journals,children,attachments
```

### Create issue
```bash
redmine issues create -s "Subject" -p PROJECT_ID -a ASSIGNEE_ID \
  --start-date 2026-04-07 --due-date 2026-04-10 -e 8
redmine issues create -s "Bug fix" -p myproject --tracker 12 --priority 3 \
  -d "Description of the issue" --format json
```

### Update issue status / progress
```bash
redmine issues update ISSUE_ID --status 2 --comment "Started work"
redmine issues update ISSUE_ID --status 3 --done-ratio 100
redmine issues update ISSUE_ID --assignee USER_ID --due-date 2026-04-15
```

### Add comment
```bash
redmine issues comment ISSUE_ID -c "Comment text"
```

### Delete issue
```bash
redmine issues delete ISSUE_ID -y
```

### Log time
```bash
redmine time log -i ISSUE_ID -h 2.5 -c "Description of work"
redmine time log -i ISSUE_ID -h 8 --activity 9 --date 2026-04-07
```

### View time entries
```bash
redmine time list --period this_week --format json
redmine time list --user me --from 2026-04-01 --to 2026-04-07
redmine time list --issue ISSUE_ID
```

### List time entry activities
```bash
redmine time activities
```

### Projects
```bash
redmine projects list
redmine projects show PROJECT_IDENTIFIER
redmine projects members PROJECT_IDENTIFIER
```

### Current user info
```bash
redmine users me --format json
```

## Common Workflows

### Workflow: Start working on an issue
1. List available issues: `redmine issues list --assignee me --status open`
2. View details: `redmine issues show ISSUE_ID`
3. Set to in-progress: `redmine issues update ISSUE_ID --status 2 --comment "Starting"`

### Workflow: Complete an issue
1. Log time spent: `redmine time log -i ISSUE_ID -h HOURS -c "Work done"`
2. Mark resolved: `redmine issues update ISSUE_ID --status 3 --done-ratio 100 -c "Completed"`

### Workflow: Create a sub-task
1. Find parent: `redmine issues show PARENT_ID`
2. Create sub-task: `redmine issues create -s "Subject" -p PROJECT --parent PARENT_ID -a ASSIGNEE`

### Workflow: Check team workload
1. List project members: `redmine projects members PROJECT_ID`
2. List each person's issues: `redmine issues list --assignee USER_ID --status open --format json`

### Workflow: Weekly time report
1. View this week: `redmine time list --period this_week`
2. View last week: `redmine time list --period last_week`
3. Export as JSON: `redmine time list --period this_week --format json`

## Output Format

Always use `--format json` (or `-f json`) when you need to parse or programmatically
process the output. The JSON output is the raw API response and suitable for scripting.

Table format (default) is for human-readable terminal display.

## Status IDs Reference

| ID | Status |
|----|--------|
| 1  | New |
| 2  | In Progress |
| 3  | Resolved |
| 4  | Feedback |
| 5  | Closed |
| 6  | Rejected |

## Activity IDs Reference

| ID | Activity |
|----|----------|
| 8  | Design |
| 9  | Development |
| 10 | Modification |
| 11 | Meeting |
| 15 | Learning |
| 17 | Business Trip |
| 21 | Tech Support |
| 22 | Testing |

## Tracker IDs Reference

| ID | Tracker |
|----|---------|
| 8  | Project Test |
| 12 | Program Development |
| 14 | Program Test |
| 15 | Project Meeting |
| 16 | Proposal Writing |
| 17 | Business Travel |
| 22 | Data Collection & Organization |

## Priority IDs Reference

| ID | Priority |
|----|----------|
| 1  | Low |
| 2  | Normal |
| 3  | High |
| 4  | Urgent |
| 5  | Immediate |

## Error Handling

If a command fails:
- "No configuration found" -> Run `redmine config init` to set up configuration
- 401 Unauthorized -> API key is invalid, update config file or REDMINE_API_KEY env var
- 404 Not Found -> Resource does not exist, verify the ID/identifier
- 422 Validation Error -> Required fields are missing, check the error messages in output
- Connection refused -> Redmine URL is unreachable, check network and config URL

## Tips

- Use `--format json` when piping output to other tools or when the model needs to parse results
- The `--all` flag on `issues list` fetches all pages automatically (use with caution on large datasets)
- `--assignee me` automatically resolves to the current user's ID
- Time entry `--period` shortcuts: today, yesterday, this_week, last_week, this_month
- Config supports multiple profiles; use `--profile NAME` to select one
