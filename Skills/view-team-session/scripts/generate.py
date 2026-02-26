#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Generate a self-contained HTML viewer for Claude Code session logs.

Usage:
    uv run {SKILL_DIR}/scripts/generate.py SESSION_ID [--output path] [--no-open]

Discovers JSONL files in ~/.claude/projects/*, parses conversation events,
handles agent team sessions with inter-agent DM deduplication, and embeds
the data into a self-contained HTML template.
"""

import argparse
import json
import sys
import webbrowser
from datetime import datetime
from glob import glob
from pathlib import Path

AGENT_COLORS = [
    "#58a6ff", "#3fb950", "#bc8cff", "#f0883e",
    "#f778ba", "#ff7b72", "#79c0ff", "#56d364",
]

TOOL_RESULT_MAX_CHARS = 10_000


def find_session_files(session_id: str) -> list[Path]:
    """Find all JSONL files matching this session ID across all projects."""
    base = Path.home() / ".claude" / "projects"
    pattern = str(base / "*" / f"{session_id}.jsonl")
    return [Path(p) for p in glob(pattern)]


def read_first_metadata(path: Path) -> dict:
    """Read the first non-snapshot line to get session metadata."""
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            if entry.get("type") == "file-history-snapshot":
                continue
            return entry
    return {}


def discover_team_files(lead_path: Path) -> tuple[str | None, str | None, list[tuple[Path, str, str]]]:
    """Given the lead's JSONL, find all teammate files with same teamName.

    Returns: (team_name, project_name, [(path, session_id, agent_name), ...])
    """
    project_dir = lead_path.parent
    project_name = project_dir.name

    # Find teamName from the lead file
    team_name = None
    with open(lead_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            tn = entry.get("teamName")
            if tn:
                team_name = tn
                break

    if not team_name:
        return None, project_name, []

    # Scan all JSONL files in the same project dir for matching teamName
    teammates = []
    for jsonl_path in sorted(project_dir.glob("*.jsonl")):
        if jsonl_path == lead_path:
            continue
        meta = read_first_metadata(jsonl_path)
        if meta.get("teamName") == team_name:
            agent_name = meta.get("agentName", jsonl_path.stem)
            session_id = meta.get("sessionId", jsonl_path.stem)
            teammates.append((jsonl_path, session_id, agent_name))

    return team_name, project_name, teammates


def parse_jsonl(path: Path, agent_id: str, agent_name: str) -> list[dict]:
    """Parse a JSONL file into structured events."""
    events = []

    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            entry_type = entry.get("type")
            timestamp = entry.get("timestamp", "")
            message = entry.get("message", {})

            if entry_type == "file-history-snapshot":
                continue

            if entry_type == "progress":
                continue

            if entry_type == "system":
                # Drop JSON system events (idle notifications, etc.)
                data = entry.get("data", {})
                if isinstance(data, dict) and data.get("type") in (
                    "idle_notification", "shutdown_approved",
                    "teammate_terminated", "shutdown_request",
                ):
                    continue
                content = str(data) if data else ""
                if content:
                    events.append({
                        "timestamp": timestamp,
                        "agentId": agent_id,
                        "agentName": agent_name,
                        "type": "system_event",
                        "content": content,
                        "metadata": {},
                    })
                continue

            if not isinstance(message, dict):
                continue

            role = message.get("role")
            content = message.get("content", "")

            # --- ASSISTANT messages ---
            if role == "assistant" and entry_type == "assistant":
                if isinstance(content, list):
                    for block in content:
                        btype = block.get("type")

                        if btype == "thinking":
                            thinking_text = block.get("thinking", "")
                            if thinking_text:
                                events.append({
                                    "timestamp": timestamp,
                                    "agentId": agent_id,
                                    "agentName": agent_name,
                                    "type": "agent_thinking",
                                    "content": thinking_text,
                                    "metadata": {},
                                })

                        elif btype == "text":
                            text = block.get("text", "").strip()
                            if text:
                                events.append({
                                    "timestamp": timestamp,
                                    "agentId": agent_id,
                                    "agentName": agent_name,
                                    "type": "agent_text",
                                    "content": text,
                                    "metadata": {},
                                })

                        elif btype == "tool_use":
                            tool_name = block.get("name", "")
                            tool_input = block.get("input", {})
                            tool_id = block.get("id", "")

                            if tool_name == "SendMessage":
                                msg_type = tool_input.get("type", "message")
                                recipient = tool_input.get("recipient", "")
                                msg_content = tool_input.get("content", "")
                                summary = tool_input.get("summary", "")

                                # shutdown_response goes to whoever requested
                                # it (the team lead). Fill in defaults.
                                if msg_type == "shutdown_response":
                                    if not recipient:
                                        recipient = "team-lead"
                                    approve = tool_input.get("approve", True)
                                    if not msg_content:
                                        msg_content = (
                                            "Shutdown approved"
                                            if approve
                                            else "Shutdown declined"
                                        )
                                    if not summary:
                                        summary = (
                                            "Approved shutdown"
                                            if approve
                                            else "Declined shutdown"
                                        )

                                events.append({
                                    "timestamp": timestamp,
                                    "agentId": agent_id,
                                    "agentName": agent_name,
                                    "type": "send_message",
                                    "content": msg_content,
                                    "metadata": {
                                        "messageType": msg_type,
                                        "recipient": recipient,
                                        "summary": summary,
                                        "toolId": tool_id,
                                    },
                                })
                            else:
                                input_str = json.dumps(tool_input, indent=2)
                                events.append({
                                    "timestamp": timestamp,
                                    "agentId": agent_id,
                                    "agentName": agent_name,
                                    "type": "tool_call",
                                    "content": input_str,
                                    "metadata": {
                                        "toolName": tool_name,
                                        "toolId": tool_id,
                                    },
                                })

            # --- USER messages ---
            elif role == "user" and entry_type == "user":
                if isinstance(content, str):
                    # Check for teammate-message (receive_message) — drop these
                    if "<teammate-message" in content:
                        continue
                    # Plain human input
                    text = content.strip()
                    if text and not text.startswith("<"):
                        events.append({
                            "timestamp": timestamp,
                            "agentId": agent_id,
                            "agentName": agent_name,
                            "type": "human_input",
                            "content": text,
                            "metadata": {},
                        })

                elif isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict):
                            if block.get("type") == "tool_result":
                                tool_id = block.get("tool_use_id", "")
                                result_content = block.get("content", "")

                                # Normalise result content to string
                                if isinstance(result_content, list):
                                    parts = []
                                    for part in result_content:
                                        if isinstance(part, dict):
                                            parts.append(part.get("text", str(part)))
                                        else:
                                            parts.append(str(part))
                                    result_str = "\n".join(parts)
                                elif isinstance(result_content, str):
                                    result_str = result_content
                                else:
                                    result_str = str(result_content)

                                # Truncate large results
                                if len(result_str) > TOOL_RESULT_MAX_CHARS:
                                    result_str = result_str[:TOOL_RESULT_MAX_CHARS] + "\n... [truncated]"

                                events.append({
                                    "timestamp": timestamp,
                                    "agentId": agent_id,
                                    "agentName": agent_name,
                                    "type": "tool_result",
                                    "content": result_str,
                                    "metadata": {"toolId": tool_id},
                                })

                            elif block.get("type") == "text":
                                text = block.get("text", "").strip()
                                if "<teammate-message" in text:
                                    continue
                                if text and not text.startswith("<"):
                                    events.append({
                                        "timestamp": timestamp,
                                        "agentId": agent_id,
                                        "agentName": agent_name,
                                        "type": "human_input",
                                        "content": text,
                                        "metadata": {},
                                    })

    return events


def consolidate_agent_text(events: list[dict]) -> list[dict]:
    """Merge consecutive agent_text events from the same agent."""
    if not events:
        return events

    consolidated = []
    i = 0
    while i < len(events):
        event = events[i]
        if event["type"] == "agent_text":
            # Collect consecutive agent_text from same agent
            texts = [event["content"]]
            j = i + 1
            while (j < len(events)
                   and events[j]["type"] == "agent_text"
                   and events[j]["agentId"] == event["agentId"]
                   and events[j]["timestamp"] == event["timestamp"]):
                texts.append(events[j]["content"])
                j += 1
            merged = {**event, "content": "\n\n".join(texts)}
            consolidated.append(merged)
            i = j
        else:
            consolidated.append(event)
            i += 1
    return consolidated


def build_session_data(session_id: str) -> dict:
    """Build the complete session data structure."""
    lead_files = find_session_files(session_id)
    if not lead_files:
        print(f"Error: No JSONL file found for session {session_id}", file=sys.stderr)
        print("Searched: ~/.claude/projects/*/", file=sys.stderr)
        sys.exit(1)

    lead_path = lead_files[0]
    team_name, project_name, teammates = discover_team_files(lead_path)

    agents = [{"id": "lead", "name": "team-lead", "color": AGENT_COLORS[0]}]
    all_events = parse_jsonl(lead_path, "lead", "team-lead")

    for idx, (tm_path, tm_session_id, tm_agent_name) in enumerate(teammates):
        color = AGENT_COLORS[(idx + 1) % len(AGENT_COLORS)]
        agents.append({
            "id": tm_session_id,
            "name": tm_agent_name,
            "color": color,
        })
        tm_events = parse_jsonl(tm_path, tm_session_id, tm_agent_name)
        all_events.extend(tm_events)

    all_events.sort(key=lambda e: e.get("timestamp", ""))
    all_events = consolidate_agent_text(all_events)

    timestamps = [e["timestamp"] for e in all_events if e["timestamp"]]
    if len(timestamps) >= 2:
        try:
            t0 = datetime.fromisoformat(timestamps[0].replace("Z", "+00:00"))
            t1 = datetime.fromisoformat(timestamps[-1].replace("Z", "+00:00"))
            duration_seconds = int((t1 - t0).total_seconds())
        except (ValueError, TypeError):
            duration_seconds = 0
    else:
        duration_seconds = 0

    session_type = "team" if team_name else "solo"

    return {
        "sessionId": session_id,
        "sessionType": session_type,
        "teamName": team_name,
        "project": project_name,
        "leadJsonlPath": str(lead_path),
        "agents": agents,
        "events": all_events,
        "stats": {
            "totalEvents": len(all_events),
            "durationSeconds": duration_seconds,
            "agentCount": len(agents),
        },
    }


def generate_html(session_data: dict, template_path: Path) -> str:
    """Replace the placeholder in template.html with session data."""
    template = template_path.read_text()
    data_json = json.dumps(session_data, ensure_ascii=False)
    return template.replace("/*__SESSION_DATA__*/null", data_json)


def main():
    parser = argparse.ArgumentParser(description="Generate Claude Code session viewer HTML")
    parser.add_argument("session_id", help="Session ID (UUID from JSONL filename)")
    parser.add_argument("--output", "-o", help="Output HTML file path")
    parser.add_argument("--no-open", action="store_true", help="Don't open in browser")
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    skill_dir = script_dir.parent
    template_path = skill_dir / "assets" / "template.html"

    if not template_path.exists():
        print(f"Error: Template not found at {template_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Building session data for {args.session_id}...")
    session_data = build_session_data(args.session_id)

    print(f"  Type: {session_data['sessionType']}")
    if session_data["teamName"]:
        print(f"  Team: {session_data['teamName']}")
    print(f"  Agents: {len(session_data['agents'])}")
    print(f"  Events: {session_data['stats']['totalEvents']}")
    duration = session_data["stats"]["durationSeconds"]
    print(f"  Duration: {duration // 60}m {duration % 60}s")

    if args.output:
        output_path = Path(args.output)
    else:
        output_path = Path(".claude/output") / f"{args.session_id}.html"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Generating HTML...")
    html = generate_html(session_data, template_path)
    output_path.write_text(html, encoding="utf-8")
    print(f"Written to {output_path}")

    if not args.no_open:
        webbrowser.open(f"file://{output_path.resolve()}")
        print("Opened in browser.")


if __name__ == "__main__":
    main()
