# Space event dedupe (one user action = one dispatch)

Status: implemented in `bus/dedupe.py` + ingest (`main.py`) and drain (`bus/executors.py`),
schema in `alembic/versions/20260916_0018_add_space_event_dedupe.py`.
Reason: one user question produced two routing cards and two room replies (room 10,
message 31: space_events 29 `message_created` + 30 `ai_question_asked`, same group).

## Why the duplicate happens

Rails emits one user action as a *group* of space events and delivers every member of the
group to the bridge as an independent webhook (`OutputEvents::DeliverJob`):

| event type                   | when                                     |
| ---------------------------- | ---------------------------------------- |
| `message_created`            | always                                   |
| `message_attachment_uploaded`| message carries a file                   |
| `ai_question_asked`          | message addresses bot users (`bot_user_ids`) |

All members share `group_id` and `event_id` (the Rails message id). Delivery order and
timing are not guaranteed, so nothing may assume "the pair arrives together".

Non-message groups reuse `(group_id, event_id)` for several **distinct** facts
(`account_settings_updated` + `account_bot_access_updated`; `room_created` +
`room_member_added`), so a key on `(group_id, event_id)` alone would silently drop real
events.

## Dedupe key

```
message:<group_id>:<room_id>:<message_id>     # message_created / attachment / ai_question_asked
event:<event_type>:<rails_event_id>:<sha256(event_data)[:16]>   # anything else: exact redelivery only
```

The family literal is the first segment, so a key is self-describing.

## Mechanics

1. **Ingest** (`main.py`): the row is stored with its `dedupe_key`; the key is claimed by
   inserting into `space_event_dispatch_groups`, whose `dedupe_key` is UNIQUE. The first
   member wins and is queued; every later member fails the insert, is recorded on its own
   row as `result.status = "duplicate_merged"` and is never queued.
2. **Merge window** (`SPACE_EVENT_MERGE_SETTLE_SECONDS`, default 3s): a message group
   waits out the window, then all member rows are merged into ONE payload
   (`ai_question_asked` wins, lists unioned) so `bot_user_ids` survives the collapse. The
   item is re-queued until the window closes; single events never wait.
3. **Dispatch**: exactly one Hermes call per key. Every member row gets `sent_date` and a
   result in the same commit (`record_group_dispatch`), the group row goes `dispatched`.
4. **Exactly-once guard**: at drain time a member whose unit already has a dispatched
   sibling is skipped (`duplicate_merged`, no Hermes call).

## Restart recovery (`bus/cron.py::_requeue_lost_work`)

The queue is in memory while the events are in the DB, so a restart used to drop queued
work. On start the bridge re-queues:

* rows with `sent_date IS NULL` **and no result** from the last
  `SPACE_EVENT_RECOVERY_MAX_AGE_SECONDS` (default 900s) — errors and merged duplicates are
  never re-queued, which is what previously re-routed the same twin on every start;
* rows stored before this feature get their `dedupe_key` backfilled first, so a legacy
  pair recovers as ONE dispatch, and a legacy member whose unit was dispatched inside
  `SPACE_EVENT_LEGACY_DISPATCH_LOOKBACK_SECONDS` is only marked as merged.

## Naming / audit

| column | meaning |
| ------ | ------- |
| `space_events.dedupe_key` | routing unit of the event (NULL = pre-feature or unkeyable) |
| `space_events.result` | Hermes response for the unit's owner row, `{"status": "duplicate_merged", ...}` for merged members |
| `space_events.sent_date` | set on every member of a dispatched unit |
| `space_event_dispatch_groups.status` | `pending` → `dispatched` / `failed` |

## Tests

`tests/test_space_event_dedupe.py` (68 tests total in the suite): key construction,
payload merging, ingest dedupe, distinct-message regression, drain single-call + failure
path, merge window, restart recovery, legacy backfill, replay row resolution.
