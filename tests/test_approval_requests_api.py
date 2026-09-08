import unittest
from unittest.mock import AsyncMock, patch

from space.api import approval_requests as approval_requests_module
from space.api import (
    create_approval_request,
    delete_approval_request,
    get_approval_request,
    list_approval_requests,
    update_approval_request,
)


class TestApprovalRequestsAPI(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_request_patcher = patch(
            "space.api.approval_requests.request", new_callable=AsyncMock
        )
        self.mock_request = self.mock_request_patcher.start()

    async def asyncTearDown(self):
        self.mock_request_patcher.stop()

    async def test_list_approval_requests(self):
        await list_approval_requests(1, 2, page=1, per_page=10)
        self.mock_request.assert_awaited_once_with(
            "GET",
            "/projects/1/rooms/2/approval_requests",
            params={"page": 1, "per_page": 10},
        )

    async def test_list_approval_requests_without_project(self):
        await list_approval_requests(None, 2)
        self.mock_request.assert_awaited_once_with(
            "GET",
            "/rooms/2/approval_requests",
            params=None,
        )

    async def test_get_approval_request(self):
        await get_approval_request(1, 2, 5)
        self.mock_request.assert_awaited_once_with(
            "GET",
            "/projects/1/rooms/2/approval_requests/5",
        )

    async def test_create_approval_request(self):
        await create_approval_request(
            1,
            2,
            request_type="decision",
            status="pending",
            message_id=3,
            agent_id=4,
            payload={"note": "please review"},
        )
        self.mock_request.assert_awaited_once_with(
            "POST",
            "/projects/1/rooms/2/approval_requests",
            json={
                "request_type": "decision",
                "status": "pending",
                "message_id": 3,
                "agent_id": 4,
                "payload": {"note": "please review"},
            },
        )

    async def test_create_approval_request_omits_none(self):
        await create_approval_request(1, 2, request_type="decision")
        self.mock_request.assert_awaited_once_with(
            "POST",
            "/projects/1/rooms/2/approval_requests",
            json={"request_type": "decision"},
        )

    async def test_update_approval_request(self):
        await update_approval_request(
            1,
            2,
            5,
            status="approved",
            resolved_at="2026-09-08T12:00:00Z",
            resolved_by_id=3,
        )
        self.mock_request.assert_awaited_once_with(
            "PATCH",
            "/projects/1/rooms/2/approval_requests/5",
            json={
                "status": "approved",
                "resolved_at": "2026-09-08T12:00:00Z",
                "resolved_by_id": 3,
            },
        )

    async def test_delete_approval_request(self):
        await delete_approval_request(1, 2, 5)
        self.mock_request.assert_awaited_once_with(
            "DELETE",
            "/projects/1/rooms/2/approval_requests/5",
        )


class TestApprovalRequestPath(unittest.TestCase):
    def test_room_scoped_path(self):
        self.assertEqual(
            approval_requests_module._approval_request_path(2),
            "/rooms/2/approval_requests",
        )

    def test_project_scoped_path(self):
        self.assertEqual(
            approval_requests_module._approval_request_path(2, project_id=1),
            "/projects/1/rooms/2/approval_requests",
        )

    def test_with_approval_request_id(self):
        self.assertEqual(
            approval_requests_module._approval_request_path(2, approval_request_id=5),
            "/rooms/2/approval_requests/5",
        )

    def test_full_path(self):
        self.assertEqual(
            approval_requests_module._approval_request_path(2, project_id=1, approval_request_id=5),
            "/projects/1/rooms/2/approval_requests/5",
        )


if __name__ == "__main__":
    unittest.main()
