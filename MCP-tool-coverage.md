# MCP Tool Coverage Matrix

- Read MCP tools: 46
- Action MCP tools: 94
- Shared tools: 29

## Key findings

- Generic company-status category tools are shared across both MCPs and use one tool for CRUD behavior through `item_id`, `title`, and `delete=true` arguments: `priorities`, `progress`, `risks`, `dependencies`, `changes`, `decisions`, and `learnings`.
- The AI-config lookup tools are read-only in behavior and are intentionally excluded from the action MCP registry: `get_ai_profile`, `get_ai_profile_mcp`, `get_ai_profile_skill`, `get_ai_profile_tool`, `get_ai_setting`, `get_mcp`, `get_skill`, `get_tool`, `list_ai_profile_mcps`, `list_ai_profile_skills`, `list_ai_profile_tools`, `list_ai_profiles`, `list_ai_settings`, `list_mcps`, `list_skills`, and `list_tools`.
- `get_approval_request` is also excluded from the action MCP because it is read-only and should remain in the read MCP only.
- The dedicated write-oriented patterns remain separate tools such as `add_*`, `edit_*`, and `delete_*` for project, approval, and project-status records.

| Tool | Read MCP | Action MCP | Create/Update/Delete |
| --- | --- | --- | --- |
| add_action_message |  | ✅ | create |
| add_ai_confirm |  | ✅ | create |
| add_approval_request |  | ✅ | create |
| add_approve_request_with_message |  | ✅ | create |
| add_blockers |  | ✅ | create |
| add_company_status_period |  | ✅ | create |
| add_decision_message |  | ✅ | create |
| add_decisions_waiting |  | ✅ | create |
| add_external_knowledge_asset |  | ✅ | create |
| add_knowledge_activity_log |  | ✅ | create |
| add_knowledge_proposals |  | ✅ | create |
| add_knowledge_summary_item |  | ✅ | create |
| add_loading_message |  | ✅ | create |
| add_material_changes |  | ✅ | create |
| add_mentions |  | ✅ | create |
| add_message |  | ✅ | create |
| add_outcomes_review |  | ✅ | create |
| add_project_all_hands_action_item |  | ✅ | create |
| add_project_all_hands_decision |  | ✅ | create |
| add_project_all_hands_takeaway |  | ✅ | create |
| add_project_bottleneck |  | ✅ | create |
| add_project_decision_record |  | ✅ | create |
| add_project_knowledge_item |  | ✅ | create |
| add_project_milestone |  | ✅ | create |
| add_project_obsidian_note |  | ✅ | create |
| add_project_todo |  | ✅ | create |
| add_tree_based_project_directory_item |  | ✅ | create |
| ai_confirm | ✅ | ✅ | full crud |
| approval_requests | ✅ | ✅ | full crud |
| blockers | ✅ | ✅ | full crud |
| changes | ✅ | ✅ | full crud |
| company_status_period | ✅ | ✅ | full crud |
| decisions | ✅ | ✅ | full crud |
| decisions_waiting | ✅ | ✅ | full crud |
| delete_approval_request |  | ✅ | delete |
| delete_external_knowledge_asset |  | ✅ | delete |
| delete_knowledge_activity_log |  | ✅ | delete |
| delete_knowledge_summary_item |  | ✅ | delete |
| delete_loading_message |  | ✅ | delete |
| delete_project_all_hands_action_item |  | ✅ | delete |
| delete_project_all_hands_decision |  | ✅ | delete |
| delete_project_all_hands_takeaway |  | ✅ | delete |
| delete_project_bottleneck |  | ✅ | delete |
| delete_project_decision_record |  | ✅ | delete |
| delete_project_knowledge_item |  | ✅ | delete |
| delete_project_milestone |  | ✅ | delete |
| delete_project_obsidian_note |  | ✅ | delete |
| delete_project_todo |  | ✅ | delete |
| delete_tree_based_project_directory_item |  | ✅ | delete |
| dependencies | ✅ | ✅ | full crud |
| edit_ai_confirm |  | ✅ | update |
| edit_approval_request |  | ✅ | update |
| edit_blockers |  | ✅ | update |
| edit_company_status_period |  | ✅ | update |
| edit_decisions_waiting |  | ✅ | update |
| edit_external_knowledge_asset |  | ✅ | update |
| edit_knowledge_activity_log |  | ✅ | update |
| edit_knowledge_proposals |  | ✅ | update |
| edit_knowledge_summary_item |  | ✅ | update |
| edit_loading_message |  | ✅ | update |
| edit_material_changes |  | ✅ | update |
| edit_mentions |  | ✅ | update |
| edit_outcomes_review |  | ✅ | update |
| edit_project_all_hands_action_item |  | ✅ | update |
| edit_project_all_hands_decision |  | ✅ | update |
| edit_project_all_hands_takeaway |  | ✅ | update |
| edit_project_bottleneck |  | ✅ | update |
| edit_project_decision_record |  | ✅ | update |
| edit_project_knowledge_item |  | ✅ | update |
| edit_project_milestone |  | ✅ | update |
| edit_project_obsidian_note |  | ✅ | update |
| edit_project_todo |  | ✅ | update |
| edit_tree_based_project_directory_item |  | ✅ | update |
| external_knowledge_assets | ✅ | ✅ | full crud |
| get_ai_profile | ✅ |  |  |
| get_ai_profile_mcp | ✅ |  |  |
| get_ai_profile_skill | ✅ |  |  |
| get_ai_profile_tool | ✅ |  |  |
| get_ai_setting | ✅ |  |  |
| get_approval_request | ✅ |  |  |
| get_mcp | ✅ |  |  |
| get_skill | ✅ |  |  |
| get_tool | ✅ |  |  |
| knowledge_activity_log | ✅ | ✅ | full crud |
| knowledge_proposals | ✅ | ✅ | full crud |
| knowledge_summary_items | ✅ | ✅ | full crud |
| learnings | ✅ | ✅ | full crud |
| list_ai_profile_mcps | ✅ |  |  |
| list_ai_profile_skills | ✅ |  |  |
| list_ai_profile_tools | ✅ |  |  |
| list_ai_profiles | ✅ |  |  |
| list_ai_settings | ✅ |  |  |
| list_mcps | ✅ |  |  |
| list_skills | ✅ |  |  |
| list_tools | ✅ |  |  |
| material_changes | ✅ | ✅ | full crud |
| mentions | ✅ | ✅ | full crud |
| outcomes_review | ✅ | ✅ | full crud |
| priorities | ✅ | ✅ | full crud |
| progress | ✅ | ✅ | full crud |
| project_all_hands_action_item | ✅ | ✅ | full crud |
| project_all_hands_decision | ✅ | ✅ | full crud |
| project_all_hands_takeaway | ✅ | ✅ | full crud |
| project_bottlenecks | ✅ | ✅ | full crud |
| project_decision_records | ✅ | ✅ | full crud |
| project_knowledge_items | ✅ | ✅ | full crud |
| project_milestones | ✅ | ✅ | full crud |
| project_obsidian_note | ✅ | ✅ | full crud |
| project_todos | ✅ | ✅ | full crud |
| risks | ✅ | ✅ | full crud |
| tree_based_project_directory_data | ✅ | ✅ | full crud |
