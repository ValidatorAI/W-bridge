# W-bridge MCP Tools Reference

This document explains each MCP tool exposed through the `tools/list` and `tools/call` JSON-RPC methods.

- Total tools in registry: `171`
- Canonical tools: `112`
- Alias tools: `59`

## How MCP Tools Are Called

Use method `tools/call` on `POST /mcp` with a tool name and an arguments object:

```json
{
  "jsonrpc": "2.0",
  "id": 10,
  "method": "tools/call",
  "params": {
    "name": "add_message",
    "arguments": {
      "room_id": 123,
      "user_id": 456,
      "body": "Hello from MCP"
    }
  }
}
```

Tool outputs are returned as text content in `result.content`, and failures set `result.isError` to `true`.

## Canonical Tools (Preferred Names)

### Core

| Tool | Purpose |
|---|---|
| `hello` | Say hello to a given name or the world |

### Company Home

| Tool | Purpose |
|---|---|
| `add_ai_confirm` | Create a company-home AI-confirm attention item |
| `add_blockers` | Create a company-home blocker attention item |
| `add_decisions_waiting` | Create a company-home decisions-waiting attention item |
| `add_knowledge_proposals` | Create a company-home knowledge-proposal attention item |
| `add_material_changes` | Create a company-home material-change attention item |
| `add_mentions` | Create a company-home mention attention item |
| `add_outcomes_review` | Create a company-home outcomes-review attention item |
| `ai_confirm` | List company-home AI-confirm attention items |
| `blockers` | List company-home blocker attention items |
| `decisions_waiting` | List company-home decisions-waiting attention items |
| `edit_ai_confirm` | Update a company-home AI-confirm attention item |
| `edit_blockers` | Update a company-home blocker attention item |
| `edit_decisions_waiting` | Update a company-home decisions-waiting attention item |
| `edit_knowledge_proposals` | Update a company-home knowledge-proposal attention item |
| `edit_material_changes` | Update a company-home material-change attention item |
| `edit_mentions` | Update a company-home mention attention item |
| `edit_outcomes_review` | Update a company-home outcomes-review attention item |
| `knowledge_proposals` | List company-home knowledge-proposal attention items |
| `material_changes` | List company-home material-change attention items |
| `mentions` | List company-home mention attention items |
| `outcomes_review` | List company-home outcomes-review attention items |

### Company Status

| Tool | Purpose |
|---|---|
| `add_company_status_period` | Create a company status period |
| `changes` | List or manage company status change items |
| `company_status_period` | List, get, create, update, or delete company status periods |
| `decisions` | List or manage company status decision items |
| `dependencies` | List or manage company status dependency items |
| `edit_company_status_period` | Update a company status period |
| `learnings` | List or manage company status learning items |
| `priorities` | List or manage company status priority items |
| `progress` | List or manage company status progress items |
| `risks` | List or manage company status risk items |

### Project Milestones

| Tool | Purpose |
|---|---|
| `add_project_milestone` | Create a project milestone |
| `delete_project_milestone` | Delete a project milestone |
| `edit_project_milestone` | Update a project milestone |
| `project_milestones` | List, get, or delete project milestones |

### Project Bottlenecks

| Tool | Purpose |
|---|---|
| `add_project_bottleneck` | Create a project bottleneck |
| `delete_project_bottleneck` | Delete a project bottleneck |
| `edit_project_bottleneck` | Update a project bottleneck |
| `project_bottlenecks` | List, get, or delete project bottlenecks |

### Project Todos

| Tool | Purpose |
|---|---|
| `add_project_todo` | Create a project todo |
| `delete_project_todo` | Delete a project todo |
| `edit_project_todo` | Update a project todo |
| `project_todos` | List, get, or delete project todos |

### Project Knowledge Items

| Tool | Purpose |
|---|---|
| `add_project_knowledge_item` | Create a project knowledge item |
| `delete_project_knowledge_item` | Delete a project knowledge item |
| `edit_project_knowledge_item` | Update a project knowledge item |
| `project_knowledge_items` | List, get, or delete project knowledge items |

### Project All Hands

| Tool | Purpose |
|---|---|
| `add_project_all_hands_action_item` | Create a project all-hands action item |
| `add_project_all_hands_decision` | Create a project all-hands decision |
| `add_project_all_hands_takeaway` | Create a project all-hands takeaway |
| `delete_project_all_hands_action_item` | Delete a project all-hands action item |
| `delete_project_all_hands_decision` | Delete a project all-hands decision |
| `delete_project_all_hands_takeaway` | Delete a project all-hands takeaway |
| `edit_project_all_hands_action_item` | Update a project all-hands action item |
| `edit_project_all_hands_decision` | Update a project all-hands decision |
| `edit_project_all_hands_takeaway` | Update a project all-hands takeaway |
| `project_all_hands_action_item` | List, get, or delete project all-hands action items |
| `project_all_hands_decision` | List, get, or delete project all-hands decisions |
| `project_all_hands_takeaway` | List, get, or delete project all-hands takeaways |

### Project Decision Records

| Tool | Purpose |
|---|---|
| `add_project_decision_record` | Create a project decision record (ADR) |
| `delete_project_decision_record` | Delete a project decision record (ADR) |
| `edit_project_decision_record` | Update a project decision record (ADR) |
| `project_decision_records` | List, get, or delete project decision records (ADRs) |

### External Knowledge Assets

| Tool | Purpose |
|---|---|
| `add_external_knowledge_asset` | Create an external knowledge asset |
| `delete_external_knowledge_asset` | Delete an external knowledge asset |
| `edit_external_knowledge_asset` | Update an external knowledge asset |
| `external_knowledge_assets` | List, get, or delete external knowledge assets |

### Knowledge Activity Log

| Tool | Purpose |
|---|---|
| `add_knowledge_activity_log` | Create a knowledge activity log entry |
| `delete_knowledge_activity_log` | Delete a knowledge activity log entry |
| `edit_knowledge_activity_log` | Update a knowledge activity log entry |
| `knowledge_activity_log` | List, get, or delete knowledge activity log entries |

### Tree Directory

| Tool | Purpose |
|---|---|
| `add_tree_based_project_directory_item` | Create a tree-based project directory item |
| `delete_tree_based_project_directory_item` | Delete a tree-based project directory item |
| `edit_tree_based_project_directory_item` | Update a tree-based project directory item |
| `tree_based_project_directory_data` | List, get, delete, or upload a file to tree-based project directory items |

### Knowledge Summary Items

| Tool | Purpose |
|---|---|
| `add_knowledge_summary_item` | Create a knowledge summary item |
| `delete_knowledge_summary_item` | Delete a knowledge summary item |
| `edit_knowledge_summary_item` | Update a knowledge summary item |
| `knowledge_summary_items` | List, get, or delete knowledge summary items |

### Project Obsidian Notes

| Tool | Purpose |
|---|---|
| `add_project_obsidian_note` | Create a project obsidian note |
| `delete_project_obsidian_note` | Delete a project obsidian note |
| `edit_project_obsidian_note` | Update a project obsidian note |
| `project_obsidian_note` | List, get, or delete project obsidian notes |

### Room Interaction

| Tool | Purpose |
|---|---|
| `add_action_message` | Send a real-time action (e.g. typing indicator) to a room |
| `add_decision_message` | Respond to an approval request (decision) in a room |
| `add_loading_message` | Add a loading message to a room (prefixed with :spin:) |
| `add_message` | Add a message to a room |
| `delete_loading_message` | Delete a loading message from a room |
| `edit_loading_message` | Edit a loading message in a room (prefixed with :spin:) |

### Approval Requests

| Tool | Purpose |
|---|---|
| `add_approval_request` | Create an approval request in a room |
| `add_approve_request_with_message` | Create a message in a room and attach an approval request to it |
| `approval_requests` | List approval requests in a room |
| `delete_approval_request` | Delete an approval request from a room |
| `edit_approval_request` | Update an approval request in a room |
| `get_approval_request` | Get a single approval request in a room |

### AI Config

| Tool | Purpose |
|---|---|
| `list_ai_profiles` | List AI profiles |
| `get_ai_profile` | Get a single AI profile |
| `list_ai_settings` | List AI settings |
| `get_ai_setting` | Get a single AI setting |
| `list_mcps` | List MCP servers |
| `get_mcp` | Get a single MCP server |
| `list_tools` | List AI tools |
| `get_tool` | Get a single AI tool |
| `list_skills` | List AI skills |
| `get_skill` | Get a single AI skill |
| `list_ai_profile_tools` | List AI profile-tool assignments (optional `ai_profile_id`, `tool_id` filters) |
| `get_ai_profile_tool` | Get a single AI profile-tool assignment |
| `list_ai_profile_skills` | List AI profile-skill assignments (optional `ai_profile_id`, `skill_id` filters) |
| `get_ai_profile_skill` | Get a single AI profile-skill assignment |
| `list_ai_profile_mcps` | List AI profile-MCP assignments (optional `ai_profile_id`, `mcp_id` filters) |
| `get_ai_profile_mcp` | Get a single AI profile-MCP assignment |

## Alias Tools (Compatibility Names)

Aliases resolve to canonical tools and use the same input schema and behavior.

| Alias | Canonical Tool |
|---|---|
| `AddActionMessage` | `add_action_message` |
| `AddApprovalRequest` | `add_approval_request` |
| `AddApproveRequestWithMessage` | `add_approve_request_with_message` |
| `AddCompanyStatusPeriod` | `add_company_status_period` |
| `AddDecisionMessage` | `add_decision_message` |
| `AddExternalKnowledgeAsset` | `add_external_knowledge_asset` |
| `AddKnowledgeActivityLog` | `add_knowledge_activity_log` |
| `AddKnowledgeSummaryItem` | `add_knowledge_summary_item` |
| `AddLoadingMessage` | `add_loading_message` |
| `AddMessage` | `add_message` |
| `AddProjectAllHandsActionItem` | `add_project_all_hands_action_item` |
| `AddProjectAllHandsDecision` | `add_project_all_hands_decision` |
| `AddProjectAllHandsTakeaway` | `add_project_all_hands_takeaway` |
| `AddProjectBottleneck` | `add_project_bottleneck` |
| `AddProjectDecisionRecord` | `add_project_decision_record` |
| `AddProjectKnowledgeItem` | `add_project_knowledge_item` |
| `AddProjectMilestone` | `add_project_milestone` |
| `AddProjectObsidianNote` | `add_project_obsidian_note` |
| `AddProjectTodo` | `add_project_todo` |
| `AddTreeBasedProjectDirectoryItem` | `add_tree_based_project_directory_item` |
| `ApprovalRequests` | `approval_requests` |
| `DeleteApprovalRequest` | `delete_approval_request` |
| `DeleteExternalKnowledgeAsset` | `delete_external_knowledge_asset` |
| `DeleteKnowledgeActivityLog` | `delete_knowledge_activity_log` |
| `DeleteKnowledgeSummaryItem` | `delete_knowledge_summary_item` |
| `DeleteLoadingMessage` | `delete_loading_message` |
| `DeleteProjectAllHandsActionItem` | `delete_project_all_hands_action_item` |
| `DeleteProjectAllHandsDecision` | `delete_project_all_hands_decision` |
| `DeleteProjectAllHandsTakeaway` | `delete_project_all_hands_takeaway` |
| `DeleteProjectBottleneck` | `delete_project_bottleneck` |
| `DeleteProjectDecisionRecord` | `delete_project_decision_record` |
| `DeleteProjectKnowledgeItem` | `delete_project_knowledge_item` |
| `DeleteProjectMilestone` | `delete_project_milestone` |
| `DeleteProjectObsidianNote` | `delete_project_obsidian_note` |
| `DeleteProjectTodo` | `delete_project_todo` |
| `DeleteTreeBasedProjectDirectoryItem` | `delete_tree_based_project_directory_item` |
| `EditApprovalRequest` | `edit_approval_request` |
| `EditCompanyStatusPeriod` | `edit_company_status_period` |
| `EditExternalKnowledgeAsset` | `edit_external_knowledge_asset` |
| `EditKnowledgeActivityLog` | `edit_knowledge_activity_log` |
| `EditKnowledgeSummaryItem` | `edit_knowledge_summary_item` |
| `EditLoadingMessage` | `edit_loading_message` |
| `EditProjectAllHandsActionItem` | `edit_project_all_hands_action_item` |
| `EditProjectAllHandsDecision` | `edit_project_all_hands_decision` |
| `EditProjectAllHandsTakeaway` | `edit_project_all_hands_takeaway` |
| `EditProjectBottleneck` | `edit_project_bottleneck` |
| `EditProjectDecisionRecord` | `edit_project_decision_record` |
| `EditProjectKnowledgeItem` | `edit_project_knowledge_item` |
| `EditProjectMilestone` | `edit_project_milestone` |
| `EditProjectObsidianNote` | `edit_project_obsidian_note` |
| `EditProjectTodo` | `edit_project_todo` |
| `EditTreeBasedProjectDirectoryItem` | `edit_tree_based_project_directory_item` |
| `external_assets` | `external_knowledge_assets` |
| `GetApprovalRequest` | `get_approval_request` |
| `ProjectAllHandsActionItem` | `project_all_hands_action_item` |
| `ProjectAllHandsDecision` | `project_all_hands_decision` |
| `ProjectAllHandsTakeaway` | `project_all_hands_takeaway` |
| `ProjectDecisionRecord` | `project_decision_records` |
| `ProjectObsidianNote` | `project_obsidian_note` |

## Notes

- Prefer canonical snake_case names in new clients.
- Use aliases only for backward compatibility or external client conventions.
- For exact input schemas, call `tools/list` and read each tool's `inputSchema`.