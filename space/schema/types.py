"""Response shapes for the Bonfire API (see docs/hermes/API_REFERENCE.md).

All are `total=False`: the server may omit or add fields, and these annotations must never
turn an upstream change into a runtime failure.
"""

from typing import TypedDict


class Project(TypedDict, total=False):
    id: int
    name: str
    slug: str
    path: str
    description: str | None
    private: bool
    short_code: str | None
    current_phase: str | None
    progress_percent: int
    roadmap: str | None
    recently_completed: str | None
    budget_total: str
    budget_spent: str
    created_at: str
    updated_at: str


class Room(TypedDict, total=False):
    id: int
    name: str
    type: str
    description: str | None
    private: bool
    parent_id: int | None
    project_id: int
    creator_id: int
    archived_at: str | None
    created_at: str
    updated_at: str


class Message(TypedDict, total=False):
    id: int
    room_id: int
    creator_id: int
    creator_type: str
    system: bool
    system_type: str | None
    body: str
    has_attachment: bool
    attachment_filename: str | None
    attachment_content_type: str | None
    attachment_url: str | None
    created_at: str
    updated_at: str


class MessageList(TypedDict, total=False):
    count: int
    page: int
    per_page: int
    messages: list[Message]


class ActionAck(TypedDict, total=False):
    status: str
    action: str


class ApprovalRequest(TypedDict, total=False):
    id: int
    room_id: int
    message_id: int | None
    agent_id: int | None
    request_type: str
    status: str
    requested_at: str
    resolved_at: str | None
    resolved_by_id: int | None


class ApprovalRequestList(TypedDict, total=False):
    count: int
    page: int
    per_page: int
    approval_requests: list[ApprovalRequest]


class AttentionItem(TypedDict, total=False):
    id: int
    category: str
    title: str
    meta_text: str | None
    due_at: str | None
    overdue: bool
    status: str
    project_id: int | None
    room_id: int | None
    user_id: int | None
    source_id: int | None
    source_type: str | None
    target_id: int | None
    target_type: str | None
    action_label: str | None
    ai_confirm: bool
    created_at: str
    updated_at: str
    resolved_at: str | None
    resolved_by_id: int | None


class AttentionItemList(TypedDict, total=False):
    count: int
    page: int
    per_page: int
    attention_items: list[AttentionItem]


class CompanyStatusPeriod(TypedDict, total=False):
    id: int
    account_id: int
    name: str
    slug: str
    current: bool
    starts_on: str | None
    ends_on: str | None
    position: int
    created_at: str
    updated_at: str


class CompanyStatusPeriodList(TypedDict, total=False):
    count: int
    company_status_periods: list[CompanyStatusPeriod]


class CompanyStatusItem(TypedDict, total=False):
    id: int
    company_status_period_id: int
    project_id: int | None
    title: str
    category: str
    status: str | None
    health: str | None
    badge: str | None
    summary: str | None
    details: str | None
    owner_name: str | None
    source_type: str | None
    position: int
    created_at: str
    updated_at: str


class CompanyStatusItemList(TypedDict, total=False):
    count: int
    page: int
    per_page: int
    company_status_items: list[CompanyStatusItem]


class ProjectUser(TypedDict, total=False):
    id: int
    name: str
    display_name: str
    email_address: str
    job_title: str | None
    status: str
    created_at: str
    updated_at: str


class ProjectUserList(TypedDict, total=False):
    count: int
    page: int
    per_page: int
    project_users: list[ProjectUser]


class AllHandsTakeaway(TypedDict, total=False):
    id: int
    project_id: int
    category: str
    content: str
    active: bool
    position: int
    created_at: str
    updated_at: str


class AllHandsTakeawayList(TypedDict, total=False):
    count: int
    page: int
    per_page: int
    project_all_hands_takeaways: list[AllHandsTakeaway]


class AllHandsDecision(TypedDict, total=False):
    id: int
    project_id: int
    title: str
    basis: str | None
    impact: str | None
    badge: str | None
    active: bool
    position: int
    created_at: str
    updated_at: str


class AllHandsDecisionList(TypedDict, total=False):
    count: int
    page: int
    per_page: int
    project_all_hands_decisions: list[AllHandsDecision]


class AllHandsActionItem(TypedDict, total=False):
    id: int
    project_id: int
    title: str
    assignee_name: str | None
    due_date: str | None
    completed: bool
    completed_at: str | None
    active: bool
    position: int
    created_at: str
    updated_at: str


class AllHandsActionItemList(TypedDict, total=False):
    count: int
    page: int
    per_page: int
    project_all_hands_action_items: list[AllHandsActionItem]


class KnowledgeItem(TypedDict, total=False):
    id: int
    project_id: int
    title: str
    description: str
    badge: str | None
    active: bool
    position: int
    created_at: str
    updated_at: str


class KnowledgeItemList(TypedDict, total=False):
    count: int
    page: int
    per_page: int
    knowledge_items: list[KnowledgeItem]


class ExternalAsset(TypedDict, total=False):
    id: int
    project_id: int
    title: str
    url: str
    doc_type: str | None
    icon: str | None
    source_type: str | None
    meta_text: str | None
    active: bool
    position: int
    created_at: str
    updated_at: str


class ExternalAssetList(TypedDict, total=False):
    count: int
    page: int
    per_page: int
    external_assets: list[ExternalAsset]


class Adr(TypedDict, total=False):
    id: int
    project_id: int
    identifier: str
    title: str
    decision_date: str | None
    status: str
    file_path: str | None
    active: bool
    position: int
    created_at: str
    updated_at: str


class AdrList(TypedDict, total=False):
    count: int
    page: int
    per_page: int
    adrs: list[Adr]


class KnowledgeActivity(TypedDict, total=False):
    id: int
    project_id: int
    actor_name: str
    actor_color: str | None
    action_text: str
    target_path: str | None
    target_url: str | None
    active: bool
    position: int
    created_at: str
    updated_at: str


class KnowledgeActivityList(TypedDict, total=False):
    count: int
    page: int
    per_page: int
    knowledge_activities: list[KnowledgeActivity]


class DirectoryItem(TypedDict, total=False):
    id: int
    project_id: int
    parent_id: int | None
    name: str
    item_type: str
    file_path: str | None
    content: str | None
    active: bool
    position: int
    created_at: str
    updated_at: str


class DirectoryItemList(TypedDict, total=False):
    count: int
    page: int
    per_page: int
    directory_items: list[DirectoryItem]


class ObsidianNote(TypedDict, total=False):
    id: int
    project_id: int
    title: str
    tags: str | None
    content: str | None
    html_source_type: str | None
    html_source_path: str | None
    active: bool
    position: int
    created_at: str
    updated_at: str


class ObsidianNoteList(TypedDict, total=False):
    count: int
    page: int
    per_page: int
    obsidian_notes: list[ObsidianNote]


class ProjectBottleneck(TypedDict, total=False):
    id: int
    project_id: int
    title: str
    description: str | None
    severity: str
    resolved_at: str | None
    position: int
    created_at: str
    updated_at: str


class ProjectBottleneckList(TypedDict, total=False):
    count: int
    page: int
    per_page: int
    project_bottlenecks: list[ProjectBottleneck]


class ProjectTodo(TypedDict, total=False):
    id: int
    project_id: int
    title: str
    meta_text: str | None
    completed: bool
    completed_at: str | None
    position: int
    created_at: str
    updated_at: str


class ProjectTodoList(TypedDict, total=False):
    count: int
    page: int
    per_page: int
    project_todos: list[ProjectTodo]


class ProjectMilestone(TypedDict, total=False):
    id: int
    project_id: int
    title: str
    description: str | None
    icon: str | None
    active: bool
    position: int
    created_at: str
    updated_at: str


class ProjectMilestoneList(TypedDict, total=False):
    count: int
    page: int
    per_page: int
    project_milestones: list[ProjectMilestone]


class AiProfile(TypedDict, total=False):
    id: int
    profile_name: str
    bot: bool
    bot_name: str | None
    editable: bool
    tool_sets_editable: bool
    max_line_sessions: int
    max_concurrent_sessions: int
    auto_decompose_per_tick: int
    max_in_progress_per_profile: int
    main_model: str | None
    fallback_model: str | None
    cloned_from: str | None
    soul_present: bool
    soul_length: int
    created_at: str
    updated_at: str


class AiProfileList(TypedDict, total=False):
    count: int
    ai_profiles: list[AiProfile]


class AiSetting(TypedDict, total=False):
    id: int
    label: str
    setting_value: int
    created_at: str
    updated_at: str


class AiSettingList(TypedDict, total=False):
    count: int
    ai_settings: list[AiSetting]


class McpServer(TypedDict, total=False):
    id: int
    name: str
    transport: str
    url: str
    authentication: str
    status: str
    command: str | None
    args: str | None
    bearer_token_present: bool
    bearer_token_length: int
    environment_present: bool
    environment_length: int
    created_at: str
    updated_at: str


class McpServerList(TypedDict, total=False):
    count: int
    mcps: list[McpServer]


class Tool(TypedDict, total=False):
    id: int
    name: str
    active: bool
    created_at: str
    updated_at: str


class ToolList(TypedDict, total=False):
    count: int
    tools: list[Tool]


class Skill(TypedDict, total=False):
    id: int
    name: str
    category: str | None
    description: str | None
    add_by_default: bool
    skill_text_present: bool
    skill_text_length: int
    created_at: str
    updated_at: str


class SkillList(TypedDict, total=False):
    count: int
    skills: list[Skill]


class AiProfileTool(TypedDict, total=False):
    id: int
    ai_profile_id: int
    tool_id: int
    enabled: bool
    created_at: str
    updated_at: str


class AiProfileToolList(TypedDict, total=False):
    count: int
    ai_profile_tools: list[AiProfileTool]


class AiProfileSkill(TypedDict, total=False):
    id: int
    ai_profile_id: int
    skill_id: int
    enabled: bool
    created_at: str
    updated_at: str


class AiProfileSkillList(TypedDict, total=False):
    count: int
    ai_profile_skills: list[AiProfileSkill]


class AiProfileMcp(TypedDict, total=False):
    id: int
    ai_profile_id: int
    mcp_id: int
    active: bool
    created_at: str
    updated_at: str


class AiProfileMcpList(TypedDict, total=False):
    count: int
    ai_profile_mcps: list[AiProfileMcp]


__all__ = [
    "ActionAck",
    "Adr",
    "AdrList",
    "AiProfile",
    "AiProfileList",
    "AiProfileMcp",
    "AiProfileMcpList",
    "AiProfileSkill",
    "AiProfileSkillList",
    "AiProfileTool",
    "AiProfileToolList",
    "AiSetting",
    "AiSettingList",
    "AllHandsActionItem",
    "AllHandsActionItemList",
    "AllHandsDecision",
    "AllHandsDecisionList",
    "AllHandsTakeaway",
    "AllHandsTakeawayList",
    "ApprovalRequest",
    "ApprovalRequestList",
    "AttentionItem",
    "AttentionItemList",
    "CompanyStatusItem",
    "CompanyStatusItemList",
    "CompanyStatusPeriod",
    "CompanyStatusPeriodList",
    "DirectoryItem",
    "DirectoryItemList",
    "ExternalAsset",
    "ExternalAssetList",
    "KnowledgeActivity",
    "KnowledgeActivityList",
    "KnowledgeItem",
    "KnowledgeItemList",
    "McpServer",
    "McpServerList",
    "Message",
    "MessageList",
    "ObsidianNote",
    "ObsidianNoteList",
    "Project",
    "ProjectBottleneck",
    "ProjectBottleneckList",
    "ProjectMilestone",
    "ProjectMilestoneList",
    "ProjectTodo",
    "ProjectTodoList",
    "ProjectUser",
    "ProjectUserList",
    "Room",
    "Skill",
    "SkillList",
    "Tool",
    "ToolList",
]
