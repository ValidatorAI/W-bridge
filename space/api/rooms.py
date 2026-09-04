from ..schema import Room
from ._client import request


async def list_rooms(project_id: int | str) -> list[Room]:
    return await request("GET", f"/projects/{project_id}/rooms")


async def get_room(project_id: int | str, room_id: int | str) -> Room:
    return await request("GET", f"/projects/{project_id}/rooms/{room_id}")


async def list_room_threads(project_id: int | str, room_id: int | str) -> list[Room]:
    return await request("GET", f"/projects/{project_id}/rooms/{room_id}/threads")


async def search_rooms(project_id: int | str, q: str) -> list[Room]:
    return await request("GET", f"/projects/{project_id}/rooms/search", params={"q": q})
