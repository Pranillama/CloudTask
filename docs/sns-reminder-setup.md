# Daily Pending-Tasks Email — AWS Setup Guide

This adds a once-a-day email summarizing your incomplete tasks, using
**Amazon SNS** (sends the email) triggered by **Amazon EventBridge** (the daily
schedule) running a new **AWS Lambda** (`daily_reminder.py`).

```
EventBridge schedule (daily) -> DailyReminder Lambda -> DynamoDB Scan
                                            |
                                            v
                                 SNS topic CloudTaskReminders -> your email
```

Single recipient only — the summary goes to one subscribed email address.

## 1. Create the SNS topic

1. SNS console -> **Topics** -> **Create topic**.
2. Type: **Standard**. Name: `CloudTaskReminders`. Create.
3. Copy the **Topic ARN** (looks like `arn:aws:sns:<region>:<acct>:CloudTaskReminders`).

## 2. Subscribe your email

1. Open the topic -> **Create subscription**.
2. Protocol: **Email**. Endpoint: your email address. Create.
3. Check your inbox and click **Confirm subscription**. (Until confirmed, no
   emails are delivered.)

## 3. Create the Lambda

1. Lambda console -> **Create function** -> Author from scratch.
2. Name: `DailyReminder`. Runtime: **Python 3.13** (same as the other functions).
3. Paste the contents of [`lambda-functions/daily_reminder.py`](../lambda-functions/daily_reminder.py)
   and deploy.
4. **Configuration -> Environment variables**, add:
   - `TABLE_NAME` = `CloudTaskTable`
   - `REMINDER_TOPIC_ARN` = the Topic ARN from step 1.
5. **Configuration -> General** -> raise the timeout to ~30s (a scan + publish
   is quick, but the default 3s can be tight).

## 4. Grant IAM permissions

Add the policy in [`docs/daily-reminder-execution-policy.json`](daily-reminder-execution-policy.json)
to the Lambda's execution role. It allows `dynamodb:Scan` on `CloudTaskTable`
and `sns:Publish` on the `CloudTaskReminders` topic.

## 5. Schedule it with EventBridge

1. EventBridge console -> **Schedules** -> **Create schedule** (EventBridge
   Scheduler).
2. Recurring schedule, cron-based. Example for 08:00 UTC daily:
   `cron(0 8 * * ? *)`.
3. Target: **AWS Lambda – Invoke**, function `DailyReminder`.
4. Create. (You can let EventBridge create the invoke permission for you.)

## 6. Test

- In the Lambda console, click **Test** with an empty `{}` event.
- With at least one incomplete task, you should receive an email within a
  minute. If all tasks are complete, the function intentionally sends nothing.

## Notes

- The Lambda scans the whole table and emails a single combined summary, so in
  a multi-user setup everyone's pending tasks land in one email to the
  subscribed address. Per-user emails would require Amazon SES + Cognito email
  lookups (out of scope here).
