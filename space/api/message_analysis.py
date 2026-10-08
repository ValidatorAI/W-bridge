from ..schema import MessageAnalysis, MessageAnalysisList
from ._client import prune, request


async def list_message_analysis(
    *,
    message_id: int | str | None = None,
    importance_level: int | None = None,
    is_a_response: bool | None = None,
    page: int | None = None,
    per_page: int | None = None,
) -> MessageAnalysisList:
    return await request(
        "GET",
        "/message_analysis",
        params=prune(
            {
                "message_id": message_id,
                "importance_level": importance_level,
                "is_a_response": is_a_response,
                "page": page,
                "per_page": per_page,
            }
        ),
    )


async def get_message_analysis(message_analysis_id: int | str) -> MessageAnalysis:
    return await request("GET", f"/message_analysis/{message_analysis_id}")


async def create_message_analysis(
    message_id: int | str,
    importance_level: int,
    message_content_summary: str,
    message_type: str,
    *,
    tags: str | None = None,
    is_a_response: bool | None = None,
) -> MessageAnalysis:
    return await request(
        "POST",
        "/message_analysis",
        json=prune(
            {
                "message_id": message_id,
                "importance_level": importance_level,
                "message_content_summary": message_content_summary,
                "message_type": message_type,
                "tags": tags,
                "is_a_response": is_a_response,
            }
        ),
    )


async def update_message_analysis(
    message_analysis_id: int | str,
    *,
    message_id: int | str | None = None,
    importance_level: int | None = None,
    message_content_summary: str | None = None,
    message_type: str | None = None,
    tags: str | None = None,
    is_a_response: bool | None = None,
) -> MessageAnalysis:
    return await request(
        "PATCH",
        f"/message_analysis/{message_analysis_id}",
        json=prune(
            {
                "message_id": message_id,
                "importance_level": importance_level,
                "message_content_summary": message_content_summary,
                "message_type": message_type,
                "tags": tags,
                "is_a_response": is_a_response,
            }
        ),
    )


async def delete_message_analysis(message_analysis_id: int | str) -> None:
    return await request("DELETE", f"/message_analysis/{message_analysis_id}")
