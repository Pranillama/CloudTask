# Design: Edit Task + Daily SNS Pending-Tasks Email

Date: 2026-06-17
Status: Approved

## Goal

Add two small features to CloudTask:

1. **Edit button** — let a user rename an existing task from the UI.
2. **Daily pending-tasks email** — once a day, email a summary of incomplete
   tasks to a single recipient (the project owner), using Amazon SNS triggered
   by Amazon EventBridge.

Both are scoped as learning/portfolio add-ons. Keep changes minimal and follow
the existing vanilla-JS / boto3 patterns.

## Feature 1 — Edit task

### Frontend
- `app.js` `renderTasks()`: add an **Edit** button next to Delete.
- `handleEditTask(taskId)`: use a `prompt()` pre-filled with the current title
  (mirrors the existing `confirm()` used for delete — simplest, consistent UX).
  - Trim input. If empty or unchanged, do nothing.
  - Call `api.updateTask(taskId, { title })`, update the local task, re-render.
- `api.js` `updateTask(taskId, completed)` becomes
  `updateTask(taskId, fields)` where `fields` is an object that may contain
  `title` and/or `completed`. The toggle handler passes `{ completed }`.

### Backend
- `update_task.py`: build `UpdateExpression` dynamically from the fields present
  in the body (`title`, `completed`).
  - Use an expression-attribute-name placeholder for `completed` since it could
    be a reserved word; `title` likewise. (Build names/values maps.)
  - Reject with 400 if no updatable field is provided, or if `title` is present
    but blank.
  - Reuses existing `PUT /tasks/{taskId}` route — no API Gateway change.

## Feature 2 — Daily pending-tasks email (single recipient)

### Architecture
```
EventBridge schedule (daily) -> daily_reminder Lambda -> DynamoDB Scan
                                              |
                                              v
                                   SNS topic CloudTaskReminders -> email
```

### Components
- **SNS topic** `CloudTaskReminders` with one email subscription (owner's
  email), confirmed once via the AWS confirmation link.
- **New Lambda** `daily_reminder.py`:
  - Scans `CloudTaskTable` for items where `completed = false`.
  - Builds a plain-text summary ("You have N pending task(s): ...").
  - If zero pending tasks, exits without publishing.
  - `sns.publish(TopicArn=REMINDER_TOPIC_ARN, Subject=..., Message=...)`.
  - Topic ARN read from env var `REMINDER_TOPIC_ARN`; table name from
    `TABLE_NAME` (consistent with other Lambdas).
- **EventBridge schedule:** cron rule (default 08:00 UTC daily) targeting the
  Lambda.
- **IAM:** new execution role/policy granting `dynamodb:Scan` on the table and
  `sns:Publish` on the topic. Added as a doc under `docs/`.

### Notes / non-goals
- Single recipient only. Per-user emailing (Cognito lookups + SES) is explicitly
  out of scope.
- Scan is acceptable at this scale; a paginated query is unnecessary for a
  learning project but noted as a future improvement.

## Deliverables
- Code: `frontend/app.js`, `frontend/api.js`, `lambda-functions/update_task.py`,
  `lambda-functions/daily_reminder.py`.
- Docs: AWS setup guide (`docs/sns-reminder-setup.md`), IAM policy
  (`docs/daily-reminder-execution-policy.json`).
- README updates: services table, features, endpoints note.
