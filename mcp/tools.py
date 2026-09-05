"""Dummy MCP tools for Company and Project management."""

from typing import Any, Callable


# ============================================================================
# Example / Baseline
# ============================================================================

def hello(name: str = "World", **kwargs: Any) -> str:
    message = f"Hello, {name}!"
    print(f"[Tool: hello] {message}")
    return message


# ============================================================================
# 1. Company Home
# ============================================================================

def decisions_waiting(**kwargs: Any) -> str:
    print(f"[Tool: decisions_waiting] Called with params: {kwargs}")
    return "Dummy result for decisions_waiting"


def blockers(**kwargs: Any) -> str:
    print(f"[Tool: blockers] Called with params: {kwargs}")
    return "Dummy result for blockers"


def outcomes_review(**kwargs: Any) -> str:
    print(f"[Tool: outcomes_review] Called with params: {kwargs}")
    return "Dummy result for outcomes_review"


def mentions(**kwargs: Any) -> str:
    print(f"[Tool: mentions] Called with params: {kwargs}")
    return "Dummy result for mentions"


def material_changes(**kwargs: Any) -> str:
    print(f"[Tool: material_changes] Called with params: {kwargs}")
    return "Dummy result for material_changes"


def ai_confirm(**kwargs: Any) -> str:
    print(f"[Tool: ai_confirm] Called with params: {kwargs}")
    return "Dummy result for ai_confirm"


def knowledge_proposals(**kwargs: Any) -> str:
    print(f"[Tool: knowledge_proposals] Called with params: {kwargs}")
    return "Dummy result for knowledge_proposals"


# ============================================================================
# 2. Company Status
# ============================================================================

def company_status_period(**kwargs: Any) -> str:
    print(f"[Tool: company_status_period] Called with params: {kwargs}")
    return "Dummy result for company_status_period"


def priorities(**kwargs: Any) -> str:
    print(f"[Tool: priorities] Called with params: {kwargs}")
    return "Dummy result for priorities"


def progress(**kwargs: Any) -> str:
    print(f"[Tool: progress] Called with params: {kwargs}")
    return "Dummy result for progress"


def risks(**kwargs: Any) -> str:
    print(f"[Tool: risks] Called with params: {kwargs}")
    return "Dummy result for risks"


def dependencies(**kwargs: Any) -> str:
    print(f"[Tool: dependencies] Called with params: {kwargs}")
    return "Dummy result for dependencies"


def changes(**kwargs: Any) -> str:
    print(f"[Tool: changes] Called with params: {kwargs}")
    return "Dummy result for changes"


def decisions(**kwargs: Any) -> str:
    print(f"[Tool: decisions] Called with params: {kwargs}")
    return "Dummy result for decisions"


def learnings(**kwargs: Any) -> str:
    print(f"[Tool: learnings] Called with params: {kwargs}")
    return "Dummy result for learnings"


# ============================================================================
# 3. Project Overview
# ============================================================================

def project_milestones(**kwargs: Any) -> str:
    print(f"[Tool: project_milestones] Called with params: {kwargs}")
    return "Dummy result for project_milestones"


# ============================================================================
# 4. Project Status
# ============================================================================

def project_bottlenecks(**kwargs: Any) -> str:
    print(f"[Tool: project_bottlenecks] Called with params: {kwargs}")
    return "Dummy result for project_bottlenecks"


def project_todos(**kwargs: Any) -> str:
    print(f"[Tool: project_todos] Called with params: {kwargs}")
    return "Dummy result for project_todos"


def project_knowledge_items(**kwargs: Any) -> str:
    print(f"[Tool: project_knowledge_items] Called with params: {kwargs}")
    return "Dummy result for project_knowledge_items"


# ============================================================================
# 5. Project All Hands
# ============================================================================

def project_all_hands_takeaway(**kwargs: Any) -> str:
    print(f"[Tool: project_all_hands_takeaway] Called with params: {kwargs}")
    return "Dummy result for project_all_hands_takeaway"


def project_all_hands_action_item(**kwargs: Any) -> str:
    print(f"[Tool: project_all_hands_action_item] Called with params: {kwargs}")
    return "Dummy result for project_all_hands_action_item"


def project_all_hands_decision(**kwargs: Any) -> str:
    print(f"[Tool: project_all_hands_decision] Called with params: {kwargs}")
    return "Dummy result for project_all_hands_decision"


# ============================================================================
# 6. Project Knowledge
# ============================================================================

def external_knowledge_assets(**kwargs: Any) -> str:
    print(f"[Tool: external_knowledge_assets] Called with params: {kwargs}")
    return "Dummy result for external_knowledge_assets"


def knowledge_activity_log(**kwargs: Any) -> str:
    print(f"[Tool: knowledge_activity_log] Called with params: {kwargs}")
    return "Dummy result for knowledge_activity_log"


def tree_based_project_directory_data(**kwargs: Any) -> str:
    print(f"[Tool: tree_based_project_directory_data] Called with params: {kwargs}")
    return "Dummy result for tree_based_project_directory_data"


def knowledge_summary_items(**kwargs: Any) -> str:
    print(f"[Tool: knowledge_summary_items] Called with params: {kwargs}")
    return "Dummy result for knowledge_summary_items"


def project_obsidian_note(**kwargs: Any) -> str:
    print(f"[Tool: project_obsidian_note] Called with params: {kwargs}")
    return "Dummy result for project_obsidian_note"


# ============================================================================
# 7. Room Tools
# ============================================================================

def add_message(**kwargs: Any) -> str:
    print(f"[Tool: add_message] Called with params: {kwargs}")
    return "Dummy result for add_message"


def add_loading_message(**kwargs: Any) -> str:
    print(f"[Tool: add_loading_message] Called with params: {kwargs}")
    return "Dummy result for add_loading_message"


def edit_loading_message(**kwargs: Any) -> str:
    print(f"[Tool: edit_loading_message] Called with params: {kwargs}")
    return "Dummy result for edit_loading_message"


def delete_loading_message(**kwargs: Any) -> str:
    print(f"[Tool: delete_loading_message] Called with params: {kwargs}")
    return "Dummy result for delete_loading_message"


def add_action_message(**kwargs: Any) -> str:
    print(f"[Tool: add_action_message] Called with params: {kwargs}")
    return "Dummy result for add_action_message"


def add_decision_message(**kwargs: Any) -> str:
    print(f"[Tool: add_decision_message] Called with params: {kwargs}")
    return "Dummy result for add_decision_message"


# ============================================================================
# Tool Registry and Definitions
# ============================================================================

TOOL_HANDLERS: dict[str, Callable[..., Any]] = {
    "hello": hello,
    # Company Home
    "decisions_waiting": decisions_waiting,
    "blockers": blockers,
    "outcomes_review": outcomes_review,
    "mentions": mentions,
    "material_changes": material_changes,
    "ai_confirm": ai_confirm,
    "knowledge_proposals": knowledge_proposals,
    # Company Status
    "company_status_period": company_status_period,
    "priorities": priorities,
    "progress": progress,
    "risks": risks,
    "dependencies": dependencies,
    "changes": changes,
    "decisions": decisions,
    "learnings": learnings,
    # Project Overview
    "project_milestones": project_milestones,
    # Project Status
    "project_bottlenecks": project_bottlenecks,
    "project_todos": project_todos,
    "project_knowledge_items": project_knowledge_items,
    # Project All Hands
    "ProjectAllHandsTakeaway": project_all_hands_takeaway,
    "project_all_hands_takeaway": project_all_hands_takeaway,
    "ProjectAllHandsActionItem": project_all_hands_action_item,
    "project_all_hands_action_item": project_all_hands_action_item,
    "ProjectAllHandsDecision": project_all_hands_decision,
    "project_all_hands_decision": project_all_hands_decision,
    # Project Knowledge
    "external_knowledge_assets": external_knowledge_assets,
    "external_assets": external_knowledge_assets,
    "knowledge_activity_log": knowledge_activity_log,
    "tree_based_project_directory_data": tree_based_project_directory_data,
    "knowledge_summary_items": knowledge_summary_items,
    "ProjectObsidianNote": project_obsidian_note,
    "project_obsidian_note": project_obsidian_note,
    # Room Tools
    "add_message": add_message,
    "AddMessage": add_message,
    "add_loading_message": add_loading_message,
    "AddLoadingMessage": add_loading_message,
    "edit_loading_message": edit_loading_message,
    "EditLoadingMessage": edit_loading_message,
    "delete_loading_message": delete_loading_message,
    "DeleteLoadingMessage": delete_loading_message,
    "add_action_message": add_action_message,
    "AddActionMessage": add_action_message,
    "add_decision_message": add_decision_message,
    "AddDecisionMessage": add_decision_message,
}

_TOOL_METADATA = [
    ("hello", "Say hello to a given name or the world", {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "The name to greet", "default": "World"}
        },
    }),
    ("decisions_waiting", "Company home decisions waiting attention items", {"type": "object", "properties": {}}),
    ("blockers", "Company home blockers attention items", {"type": "object", "properties": {}}),
    ("outcomes_review", "Company home outcomes review attention items", {"type": "object", "properties": {}}),
    ("mentions", "Company home mentions attention items", {"type": "object", "properties": {}}),
    ("material_changes", "Company home material changes attention items", {"type": "object", "properties": {}}),
    ("ai_confirm", "Company home AI confirm attention items", {"type": "object", "properties": {}}),
    ("knowledge_proposals", "Company home knowledge proposals attention items", {"type": "object", "properties": {}}),
    ("company_status_period", "Company status period management", {"type": "object", "properties": {}}),
    ("priorities", "Company status priorities items", {"type": "object", "properties": {}}),
    ("progress", "Company status progress items", {"type": "object", "properties": {}}),
    ("risks", "Company status risks items", {"type": "object", "properties": {}}),
    ("dependencies", "Company status dependencies items", {"type": "object", "properties": {}}),
    ("changes", "Company status changes items", {"type": "object", "properties": {}}),
    ("decisions", "Company status decisions items", {"type": "object", "properties": {}}),
    ("learnings", "Company status learnings items", {"type": "object", "properties": {}}),
    ("project_milestones", "Project overview milestones", {"type": "object", "properties": {}}),
    ("project_bottlenecks", "Project status bottlenecks", {"type": "object", "properties": {}}),
    ("project_todos", "Project status todos", {"type": "object", "properties": {}}),
    ("project_knowledge_items", "Project status knowledge items", {"type": "object", "properties": {}}),
    ("ProjectAllHandsTakeaway", "Project all hands takeaway items", {"type": "object", "properties": {}}),
    ("ProjectAllHandsActionItem", "Project all hands action items", {"type": "object", "properties": {}}),
    ("ProjectAllHandsDecision", "Project all hands decision items", {"type": "object", "properties": {}}),
    ("external_knowledge_assets", "External knowledge assets", {"type": "object", "properties": {}}),
    ("knowledge_activity_log", "Knowledge activity logs", {"type": "object", "properties": {}}),
    ("tree_based_project_directory_data", "Tree-based project directory data", {"type": "object", "properties": {}}),
    ("knowledge_summary_items", "Knowledge summary items", {"type": "object", "properties": {}}),
    ("ProjectObsidianNote", "Project obsidian notes", {"type": "object", "properties": {}}),
    ("add_message", "Add a message to a room", {"type": "object", "properties": {}}),
    ("add_loading_message", "Add a loading message to a room", {"type": "object", "properties": {}}),
    ("edit_loading_message", "Edit a loading message in a room", {"type": "object", "properties": {}}),
    ("delete_loading_message", "Delete a loading message from a room", {"type": "object", "properties": {}}),
    ("add_action_message", "Add an action message to a room", {"type": "object", "properties": {}}),
    ("add_decision_message", "Add a decision message to a room", {"type": "object", "properties": {}}),
]

TOOL_DEFINITIONS = [
    {
        "name": name,
        "description": desc,
        "inputSchema": schema,
    }
    for name, desc, schema in _TOOL_METADATA
]
