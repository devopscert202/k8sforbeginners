# Lab 29: Kubernetes CronJobs

## Overview
In this lab, you will learn about CronJobs, a Kubernetes workload type for running scheduled tasks. You'll create and manage CronJobs, understand the cron schedule syntax, monitor job execution, and learn best practices for scheduled workloads in Kubernetes.

## Prerequisites
- A running Kubernetes cluster (Minikube, Kind, or any K8s cluster)
- `kubectl` CLI tool installed and configured
- Basic understanding of Pods and Deployments (Lab 01)
- Familiarity with Unix cron syntax (helpful but not required)

## Learning Objectives
By the end of this lab, you will be able to:
- Understand what CronJobs are and their use cases
- Create and manage CronJobs with cron schedules
- Monitor CronJob execution and history
- Understand the difference between Jobs and CronJobs
- Configure job retention policies
- Use timezone support for CronJobs (K8s 1.25+)
- Troubleshoot failed CronJobs
- Implement best practices for scheduled tasks

## Repository YAML Files

Under `k8s/labs/workloads/`:

| File | Description |
|------|-------------|
| `cronjob.yaml` | CronJob `hello-cronjob` (every 5 minutes, busybox). |
| `cronjob-timezone.yaml` | Timezone-aware CronJob `timezone-cronjob` (`America/New_York`). |
| `one-time-job.yaml` | Single-run Job `one-time-job` for comparison with CronJobs. |
| `backup-cronjob.yaml` | CronJob `daily-backup` (2 AM UTC). |
| `cleanup-cronjob.yaml` | CronJob `hourly-cleanup`. |
| `report-cronjob.yaml` | CronJob `weekday-report`. |
| `failing-cronjob.yaml` | CronJob `failing-job` (intentional failure + backoff). |
| `sequential-cronjob.yaml` | CronJob `sequential-job` with `concurrencyPolicy: Forbid`. |
| `configured-cronjob.yaml` | CronJob `configured-job` (requires ConfigMap `cronjob-config` and Secret `cronjob-secret` as in the lab). |
| `london-cronjob.yaml` / `tokyo-cronjob.yaml` | Same schedule, different `timeZone`. |
| `test-timezone.yaml` | Frequent test CronJob (`America/Los_Angeles`). |

---

## What is a CronJob?

A **CronJob** creates Jobs on a repeating schedule. It is ideal for periodic and recurring tasks like backups, report generation, and sending emails.

### Key Characteristics

- **Scheduled Execution**: Runs Jobs at specified times using cron format
- **Job Management**: Automatically creates Job objects on schedule
- **History Management**: Controls how many completed/failed Jobs to retain
- **Idempotency**: Jobs should be designed to handle overlapping executions
- **Time Zone**: By default uses the kube-controller-manager's time zone

### Cron Schedule Format

```
┌───────────── minute (0 - 59)
│ ┌───────────── hour (0 - 23)
│ │ ┌───────────── day of the month (1 - 31)
│ │ │ ┌───────────── month (1 - 12)
│ │ │ │ ┌───────────── day of the week (0 - 6) (Sunday to Saturday)
│ │ │ │ │
│ │ │ │ │
* * * * *
```

**Common Schedule Examples:**

| Schedule | Description |
|----------|-------------|
| `*/5 * * * *` | Every 5 minutes |
| `0 * * * *` | Every hour at minute 0 |
| `0 0 * * *` | Daily at midnight |
| `0 0 * * 0` | Every Sunday at midnight |
| `0 2 * * 1-5` | Weekdays at 2 AM |
| `30 3 1 * *` | First day of month at 3:30 AM |
| `0 */6 * * *` | Every 6 hours |

### Common Use Cases

1. **Database Backups**: Scheduled database dumps
2. **Data Processing**: ETL jobs, report generation
3. **Cache Warming**: Periodic cache refresh
4. **Cleanup Tasks**: Delete old files, logs, or data
5. **Health Checks**: Periodic system health monitoring
6. **Email Reports**: Scheduled email notifications
7. **Data Synchronization**: Periodic sync between systems

---

## Exercise 1: Deploy Your First CronJob

### Step 1: Review the CronJob Manifest

Navigate to the workloads directory:
```bash
cd k8s/labs/workloads
```

Let's examine the `cronjob.yaml` file:

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: hello-cronjob
  namespace: default
spec:
  schedule: "*/5 * * * *" # Every 5 minutes
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: hello
            image: busybox
            args:
            - /bin/sh
            - -c
            - date; echo "Hello from Kubernetes CronJob!"
          restartPolicy: OnFailure
  successfulJobsHistoryLimit: 3 # Retain 3 successful Jobs
  failedJobsHistoryLimit: 1     # Retain 1 failed Job
```

**Understanding the Manifest:**

- `kind: CronJob` - Defines this as a CronJob resource
- `schedule: "*/5 * * * *"` - Runs every 5 minutes
- `jobTemplate` - Template for Jobs that will be created
- `template.spec` - Pod specification (same as in Pods/Deployments)
- `image: busybox` - Lightweight container for simple tasks
- `args` - Commands to run: print date and hello message
- `restartPolicy: OnFailure` - Retry on failure, not on success
- `successfulJobsHistoryLimit: 3` - Keep last 3 successful Jobs
- `failedJobsHistoryLimit: 1` - Keep last 1 failed Job

### Step 2: Deploy the CronJob

Apply the manifest:

```bash
kubectl apply -f cronjob.yaml
```

Expected output:
```
cronjob.batch/hello-cronjob created
```

### Step 3: Verify CronJob Creation

Check the CronJob:

```bash
kubectl get cronjob
```

Expected output:
```
NAME            SCHEDULE      SUSPEND   ACTIVE   LAST SCHEDULE   AGE
hello-cronjob   */5 * * * *   False     0        <none>          10s
```

**Understanding the output:**
- `SCHEDULE`: The cron schedule expression
- `SUSPEND`: Whether the CronJob is suspended (not running)
- `ACTIVE`: Number of currently running Jobs
- `LAST SCHEDULE`: Time since last Job execution
- `AGE`: Time since CronJob creation

Get detailed information:

```bash
kubectl describe cronjob hello-cronjob
```

---

## Exercise 2: Monitoring CronJob Execution

### Step 1: Wait for Job Execution

Wait for 5 minutes for the first Job to be created, or watch in real-time:

```bash
kubectl get jobs -w
```

After the scheduled time, you should see:
```
NAME                      COMPLETIONS   DURATION   AGE
hello-cronjob-28503720    1/1           5s         30s
```

### Step 2: View Created Jobs

List all Jobs created by the CronJob:

```bash
kubectl get jobs -l job-name
```

Or more specifically:

```bash
kubectl get jobs | grep hello-cronjob
```

Expected output:
```
NAME                      COMPLETIONS   DURATION   AGE
hello-cronjob-28503720    1/1           5s         2m
hello-cronjob-28503725    1/1           4s         1m
```

### Step 3: View Pod Logs

List Pods created by the Jobs:

```bash
kubectl get pods | grep hello-cronjob
```

Expected output:
```
NAME                            READY   STATUS      RESTARTS   AGE
hello-cronjob-28503720-abcd1    0/1     Completed   0          2m
hello-cronjob-28503725-abcd2    0/1     Completed   0          1m
```

View logs from a completed Pod:

```bash
POD_NAME=$(kubectl get pods -l job-name --sort-by=.metadata.creationTimestamp | grep hello-cronjob | tail -1 | awk '{print $1}')
kubectl logs $POD_NAME
```

Expected output:
```
Mon Mar 16 10:35:00 UTC 2026
Hello from Kubernetes CronJob!
```

### Step 4: Monitor CronJob Status

Check CronJob status continuously:

```bash
kubectl get cronjob hello-cronjob -w
```

View events:

```bash
kubectl describe cronjob hello-cronjob | grep -A 10 Events
```

---

## Exercise 3: Understanding Job vs CronJob

### Jobs vs CronJobs

| Feature | Job | CronJob |
|---------|-----|---------|
| **Execution** | Runs once | Runs on schedule |
| **Schedule** | Immediate | Cron-based |
| **Use Case** | One-time tasks | Recurring tasks |
| **Management** | Manual creation | Automatic creation |
| **Lifecycle** | User-managed | Auto-managed with history limits |

### Create a One-Time Job (For Comparison)

Create `one-time-job.yaml`:

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: one-time-job
spec:
  template:
    spec:
      containers:
      - name: hello
        image: busybox
        args:
        - /bin/sh
        - -c
        - date; echo "This is a one-time Job!"
      restartPolicy: OnFailure
  backoffLimit: 4
```

Apply and observe:

```bash
kubectl apply -f one-time-job.yaml
kubectl get jobs
kubectl logs job/one-time-job
```

The Job runs once and completes. The CronJob creates new Jobs on schedule.

---

## Exercise 4: Creating Different CronJob Schedules

### Example 1: Daily Backup Job

Create `backup-cronjob.yaml`:

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: daily-backup
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: busybox
            args:
            - /bin/sh
            - -c
            - echo "Running backup at $(date)"
          restartPolicy: OnFailure
  successfulJobsHistoryLimit: 7  # Keep one week of backups
  failedJobsHistoryLimit: 3
```

Apply it:

```bash
kubectl apply -f backup-cronjob.yaml
```

### Example 2: Hourly Cleanup Job

Create `cleanup-cronjob.yaml`:

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: hourly-cleanup
spec:
  schedule: "0 * * * *"  # Every hour
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: cleanup
            image: busybox
            args:
            - /bin/sh
            - -c
            - echo "Cleaning up old files at $(date)"
          restartPolicy: OnFailure
  successfulJobsHistoryLimit: 5
  failedJobsHistoryLimit: 2
```

Apply it:

```bash
kubectl apply -f cleanup-cronjob.yaml
```

### Example 3: Weekday Report Job

Create `report-cronjob.yaml`:

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: weekday-report
spec:
  schedule: "0 9 * * 1-5"  # Weekdays at 9 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: report
            image: busybox
            args:
            - /bin/sh
            - -c
            - echo "Generating report at $(date)"
          restartPolicy: OnFailure
  successfulJobsHistoryLimit: 10
  failedJobsHistoryLimit: 3
```

Apply it:

```bash
kubectl apply -f report-cronjob.yaml
```

View all CronJobs:

```bash
kubectl get cronjobs
```

---

## Exercise 5: Managing CronJob History

### Step 1: Understanding History Limits

CronJobs automatically clean up old Jobs based on history limits:

- `successfulJobsHistoryLimit`: Number of successful Jobs to retain
- `failedJobsHistoryLimit`: Number of failed Jobs to retain

### Step 2: View Job History

Check current Jobs:

```bash
kubectl get jobs | grep hello-cronjob
```

After several executions, you'll see only the most recent Jobs (up to the history limit).

### Step 3: Update History Limits

Edit the CronJob to change history limits:

```bash
kubectl edit cronjob hello-cronjob
```

Change:
```yaml
successfulJobsHistoryLimit: 5
failedJobsHistoryLimit: 2
```

Or use patch:

```bash
kubectl patch cronjob hello-cronjob -p '{"spec":{"successfulJobsHistoryLimit":5,"failedJobsHistoryLimit":2}}'
```

### Step 4: Manual Cleanup

Manually delete old Jobs:

```bash
# Delete all completed Jobs for a CronJob
kubectl delete jobs -l job-name | grep hello-cronjob | grep Completed

# Delete all Jobs older than 1 hour
kubectl get jobs --field-selector status.successful=1 -o json | \
  jq -r '.items[] | select(.status.completionTime | fromdateiso8601 < (now - 3600)) | .metadata.name' | \
  xargs kubectl delete job
```

---

## Exercise 6: Suspending and Resuming CronJobs

### Step 1: Suspend a CronJob

Temporarily stop a CronJob from creating new Jobs:

```bash
kubectl patch cronjob hello-cronjob -p '{"spec":{"suspend":true}}'
```

Verify suspension:

```bash
kubectl get cronjob hello-cronjob
```

Output:
```
NAME            SCHEDULE      SUSPEND   ACTIVE   LAST SCHEDULE   AGE
hello-cronjob   */5 * * * *   True      0        2m              10m
```

Notice `SUSPEND` is now `True`.

### Step 2: Resume a CronJob

Resume the CronJob:

```bash
kubectl patch cronjob hello-cronjob -p '{"spec":{"suspend":false}}'
```

Verify:

```bash
kubectl get cronjob hello-cronjob
```

---

## Exercise 7: Handling Failed Jobs

### Step 1: Create a Failing CronJob

Create `failing-cronjob.yaml`:

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: failing-job
spec:
  schedule: "*/2 * * * *"  # Every 2 minutes
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: fail
            image: busybox
            args:
            - /bin/sh
            - -c
            - exit 1  # Always fail
          restartPolicy: OnFailure
      backoffLimit: 2  # Retry only 2 times
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 3
```

Apply it:

```bash
kubectl apply -f failing-cronjob.yaml
```

### Step 2: Monitor Failures

Wait a few minutes and check the status:

```bash
kubectl get cronjob failing-job
kubectl get jobs | grep failing-job
```

View a failed Job:

```bash
kubectl describe job <failing-job-name>
```

Look for:
- Number of retries
- Failure reason
- Backoff limit reached

### Step 3: View Failed Pod Logs

```bash
kubectl get pods | grep failing-job | grep Error
POD_NAME=$(kubectl get pods | grep failing-job | grep Error | tail -1 | awk '{print $1}')
kubectl logs $POD_NAME
```

### Step 4: Fix and Update

Fix the CronJob by updating the command:

```bash
kubectl patch cronjob failing-job --type='json' -p='[
  {
    "op": "replace",
    "path": "/spec/jobTemplate/spec/template/spec/containers/0/args",
    "value": ["/bin/sh", "-c", "echo Success; exit 0"]
  }
]'
```

---

## Exercise 8: CronJob Concurrency Policies

### Understanding Concurrency Policies

Control what happens when a Job is still running when the next scheduled time arrives:

- `Allow` (default): Multiple Jobs can run concurrently
- `Forbid`: Skip new Job if previous is still running
- `Replace`: Cancel running Job and start new one

### Example: Forbid Concurrent Jobs

Create `sequential-cronjob.yaml`:

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: sequential-job
spec:
  schedule: "*/2 * * * *"
  concurrencyPolicy: Forbid
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: long-task
            image: busybox
            args:
            - /bin/sh
            - -c
            - echo "Starting long task"; sleep 180; echo "Task completed"
          restartPolicy: OnFailure
```

This Job takes 3 minutes but runs every 2 minutes. With `Forbid`, the second execution will be skipped.

Apply and observe:

```bash
kubectl apply -f sequential-cronjob.yaml
kubectl get jobs -w | grep sequential-job
```

---

## Exercise 9: CronJob with Environment Variables and Secrets

### Step 1: Create a ConfigMap

```bash
kubectl create configmap cronjob-config --from-literal=ENVIRONMENT=production
```

### Step 2: Create a Secret

```bash
kubectl create secret generic cronjob-secret --from-literal=API_KEY=super-secret-key
```

### Step 3: Create CronJob Using Config

Create `configured-cronjob.yaml`:

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: configured-job
spec:
  schedule: "*/10 * * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: app
            image: busybox
            args:
            - /bin/sh
            - -c
            - echo "Environment: $ENVIRONMENT, API Key: $API_KEY"
            env:
            - name: ENVIRONMENT
              valueFrom:
                configMapKeyRef:
                  name: cronjob-config
                  key: ENVIRONMENT
            - name: API_KEY
              valueFrom:
                secretKeyRef:
                  name: cronjob-secret
                  key: API_KEY
          restartPolicy: OnFailure
```

Apply and verify:

```bash
kubectl apply -f configured-cronjob.yaml

# Wait for execution, then check logs
sleep 600  # Wait 10 minutes
POD_NAME=$(kubectl get pods | grep configured-job | tail -1 | awk '{print $1}')
kubectl logs $POD_NAME
```

---

## Exercise 10: CronJobs with Timezone Support (K8s 1.25+)

### Understanding Timezone Support

Starting with Kubernetes 1.25, CronJobs support the `.spec.timeZone` field, which allows you to specify the timezone for the cron schedule. This is particularly useful when you need Jobs to run at specific local times rather than UTC.

**Key Points:**

- **Default Behavior**: Without the `timeZone` field, CronJobs use the timezone of the kube-controller-manager (typically UTC)
- **IANA Timezone Database**: The `timeZone` field accepts standard IANA timezone names (e.g., "America/New_York", "Europe/London", "Asia/Tokyo")
- **Daylight Saving Time**: Timezone-aware CronJobs automatically handle DST transitions
- **Kubernetes Version**: This feature requires Kubernetes 1.25 or later

### Step 1: Review the Timezone CronJob Manifest

Navigate to the workloads directory and examine `cronjob-timezone.yaml`:

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: timezone-cronjob
spec:
  schedule: "0 9 * * 1-5"  # 9 AM on weekdays
  timeZone: "America/New_York"  # Eastern Time
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: hello
            image: busybox
            command:
            - /bin/sh
            - -c
            - date; echo "Good morning from New York!"
          restartPolicy: OnFailure
```

**Understanding the Manifest:**

- `schedule: "0 9 * * 1-5"` - Runs at 9:00 AM on weekdays (Monday-Friday)
- `timeZone: "America/New_York"` - Schedule is interpreted in Eastern Time
- Without timezone field, 9 AM would be in UTC
- With timezone field, 9 AM is in the specified timezone

### Step 2: Deploy the Timezone-Aware CronJob

Apply the manifest:

```bash
cd k8s/labs/workloads
kubectl apply -f cronjob-timezone.yaml
```

Expected output:
```
cronjob.batch/timezone-cronjob created
```

### Step 3: Verify Timezone Configuration

Check the CronJob details:

```bash
kubectl describe cronjob timezone-cronjob
```

Look for the timezone field in the output:
```
Schedule:       0 9 * * 1-5
Time Zone:      America/New_York
```

View the full YAML:

```bash
kubectl get cronjob timezone-cronjob -o yaml | grep -A 2 schedule
```

Expected output:
```yaml
  schedule: 0 9 * * 1-5
  timeZone: America/New_York
```

### Step 4: Compare Different Timezones

Create multiple CronJobs with different timezones to understand the behavior.

**London Timezone Example** (`london-cronjob.yaml`):

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: london-cronjob
spec:
  schedule: "0 9 * * 1-5"  # 9 AM weekdays
  timeZone: "Europe/London"  # UK Time
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: hello
            image: busybox
            command:
            - /bin/sh
            - -c
            - date; echo "Good morning from London!"
          restartPolicy: OnFailure
```

**Tokyo Timezone Example** (`tokyo-cronjob.yaml`):

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: tokyo-cronjob
spec:
  schedule: "0 9 * * 1-5"  # 9 AM weekdays
  timeZone: "Asia/Tokyo"  # Japan Time
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: hello
            image: busybox
            command:
            - /bin/sh
            - -c
            - date; echo "Good morning from Tokyo!"
          restartPolicy: OnFailure
```

Apply both:

```bash
kubectl apply -f london-cronjob.yaml
kubectl apply -f tokyo-cronjob.yaml
```

### Step 5: View All Timezone CronJobs

List all CronJobs with their timezones:

```bash
kubectl get cronjobs -o custom-columns=NAME:.metadata.name,SCHEDULE:.spec.schedule,TIMEZONE:.spec.timeZone
```

Expected output:
```
NAME               SCHEDULE      TIMEZONE
timezone-cronjob   0 9 * * 1-5   America/New_York
london-cronjob     0 9 * * 1-5   Europe/London
tokyo-cronjob      0 9 * * 1-5   Asia/Tokyo
```

All three CronJobs run at "9 AM weekdays" but in different timezones, meaning they execute at different UTC times.

### Step 6: Test Timezone Conversion

Create a test CronJob that runs every 5 minutes in a specific timezone:

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: test-timezone
spec:
  schedule: "*/5 * * * *"  # Every 5 minutes
  timeZone: "America/Los_Angeles"  # Pacific Time
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: test
            image: busybox
            command:
            - /bin/sh
            - -c
            - |
              echo "Current UTC time: $(date -u)"
              echo "Scheduled timezone: America/Los_Angeles"
              echo "This job runs every 5 minutes in Pacific Time"
          restartPolicy: OnFailure
  successfulJobsHistoryLimit: 2
  failedJobsHistoryLimit: 1
```

Apply and monitor:

```bash
kubectl apply -f test-timezone.yaml
kubectl get cronjob test-timezone -w
```

Wait for execution and check logs:

```bash
# After 5 minutes
POD_NAME=$(kubectl get pods -l job-name | grep test-timezone | tail -1 | awk '{print $1}')
kubectl logs $POD_NAME
```

### Common Timezone Examples

Here are some commonly used IANA timezone identifiers:

| Region | Timezone | Example Use Case |
|--------|----------|------------------|
| US East Coast | `America/New_York` | Business hours EST/EDT |
| US West Coast | `America/Los_Angeles` | Business hours PST/PDT |
| US Central | `America/Chicago` | Business hours CST/CDT |
| UK | `Europe/London` | Business hours GMT/BST |
| Central Europe | `Europe/Paris` | Business hours CET/CEST |
| India | `Asia/Kolkata` | IST operations |
| Japan | `Asia/Tokyo` | JST operations |
| Australia East | `Australia/Sydney` | AEST/AEDT operations |
| UTC | `UTC` | Explicit UTC scheduling |

### Daylight Saving Time Considerations

When using timezone-aware CronJobs:

**During DST Transition Forward (Spring)**:
- If a scheduled time falls within the "skipped" hour, the Job runs after the transition
- Example: 2:30 AM schedule when clocks jump from 2:00 AM to 3:00 AM

**During DST Transition Backward (Fall)**:
- If a scheduled time occurs twice (repeated hour), the Job runs only once
- Example: 1:30 AM schedule when clocks fall back from 2:00 AM to 1:00 AM

**Example with DST handling**:

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: dst-aware-job
spec:
  schedule: "30 2 * * *"  # 2:30 AM daily
  timeZone: "America/New_York"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: task
            image: busybox
            command:
            - /bin/sh
            - -c
            - echo "Running at 2:30 AM Eastern Time, DST handled automatically"
          restartPolicy: OnFailure
```

### Troubleshooting Timezone Issues

**Issue**: Invalid timezone value

```bash
# Check CronJob events
kubectl describe cronjob <name>

# Common error:
# Error: spec.timeZone: Invalid value: "EST": unknown time zone EST

# Solution: Use IANA timezone names, not abbreviations
# Bad:  timeZone: "EST"
# Good: timeZone: "America/New_York"
```

**Issue**: CronJob not running at expected local time

```bash
# Verify timezone is set
kubectl get cronjob <name> -o jsonpath='{.spec.timeZone}'

# Check last schedule time in UTC
kubectl get cronjob <name> -o jsonpath='{.status.lastScheduleTime}'

# Verify the timezone name is correct
# Use: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
```

**Issue**: Kubernetes version doesn't support timezone field

```bash
# Check Kubernetes version
kubectl version --short

# Timezone support requires K8s 1.25+
# If running older version, you'll see:
# error: unknown field "spec.timeZone"

# Solution: Upgrade cluster or use UTC-based scheduling
```

### Best Practices for Timezone-Aware CronJobs

1. **Always Use IANA Timezone Names**
   ```yaml
   # Good
   timeZone: "America/New_York"

   # Bad - abbreviations don't work
   timeZone: "EST"
   ```

2. **Consider DST for Critical Jobs**
   - Avoid scheduling critical jobs during DST transition hours (2:00-3:00 AM)
   - Use explicit UTC times for jobs that must run at exact intervals

3. **Document Timezone Expectations**
   ```yaml
   metadata:
     name: report-generator
     annotations:
       description: "Generates daily reports at 6 AM Eastern Time"
       timezone: "America/New_York (EST/EDT with DST)"
   ```

4. **Test Timezone Behavior**
   ```bash
   # Create a test job that runs every few minutes
   # Verify it runs at expected local times
   # Check logs for timing accuracy
   ```

5. **Monitor Across Timezones**
   - Set up alerts for failed Jobs in each timezone
   - Use observability tools that display job execution times in local timezone

### Cleanup Timezone CronJobs

Remove the timezone test CronJobs:

```bash
kubectl delete cronjob timezone-cronjob
kubectl delete cronjob london-cronjob
kubectl delete cronjob tokyo-cronjob
kubectl delete cronjob test-timezone
```

---

## Lab Cleanup

Remove all CronJob resources:

```bash
# Delete all CronJobs
kubectl delete cronjob hello-cronjob
kubectl delete cronjob daily-backup
kubectl delete cronjob hourly-cleanup
kubectl delete cronjob weekday-report
kubectl delete cronjob failing-job
kubectl delete cronjob sequential-job
kubectl delete cronjob configured-job
kubectl delete cronjob timezone-cronjob
kubectl delete cronjob london-cronjob
kubectl delete cronjob tokyo-cronjob
kubectl delete cronjob test-timezone

# Delete the one-time Job
kubectl delete job one-time-job

# Delete ConfigMap and Secret
kubectl delete configmap cronjob-config
kubectl delete secret cronjob-secret

# Delete any remaining Jobs
kubectl delete jobs -l job-name

# Verify cleanup
kubectl get cronjobs
kubectl get jobs
```

---

## Key Takeaways

1. **CronJobs schedule recurring tasks** using standard cron syntax
2. **Job Management** - CronJobs automatically create and clean up Job objects
3. **History Limits** - Control resource usage with retention policies
4. **Suspend Feature** - Temporarily stop CronJob execution without deletion
5. **Concurrency Policies** - Control overlapping Job execution
6. **Timezone Support** - Use `.spec.timeZone` field (K8s 1.25+) to schedule jobs in specific timezones instead of UTC
7. **Idempotency** - Design Jobs to be safe for repeated execution
8. **Monitoring** - Always monitor failed Jobs and set appropriate alerts
9. **Resource Limits** - Set CPU/memory limits to prevent resource exhaustion

---

## Best Practices

### 1. Design Idempotent Jobs

Jobs should produce the same result even if run multiple times:

```bash
# Good: Check before creating
if [ ! -f /backup/data.tar.gz ]; then
  tar -czf /backup/data.tar.gz /data
fi

# Bad: Always creates, might conflict
tar -czf /backup/data.tar.gz /data
```

### 2. Set Appropriate Timeouts

Use `activeDeadlineSeconds` to prevent stuck Jobs:

```yaml
spec:
  jobTemplate:
    spec:
      activeDeadlineSeconds: 300  # Kill after 5 minutes
      template:
        spec:
          containers:
          - name: task
            image: busybox
```

### 3. Handle Failures Gracefully

```yaml
spec:
  jobTemplate:
    spec:
      backoffLimit: 3  # Retry 3 times
      template:
        spec:
          restartPolicy: OnFailure  # Restart on failure
```

### 4. Use Resource Limits

```yaml
spec:
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: task
            resources:
              requests:
                memory: "64Mi"
                cpu: "250m"
              limits:
                memory: "128Mi"
                cpu: "500m"
```

### 5. Set Meaningful History Limits

```yaml
spec:
  successfulJobsHistoryLimit: 3  # Keep last 3 for debugging
  failedJobsHistoryLimit: 5      # Keep more failures for troubleshooting
```

---

## Additional Commands Reference

```bash
# List all CronJobs with schedule
kubectl get cronjobs -o custom-columns=NAME:.metadata.name,SCHEDULE:.spec.schedule,SUSPEND:.spec.suspend

# Get next scheduled time
kubectl get cronjob <name> -o jsonpath='{.status.lastScheduleTime}'

# Trigger a CronJob manually (create Job from CronJob)
kubectl create job --from=cronjob/<cronjob-name> <job-name>

# View CronJob in YAML
kubectl get cronjob <name> -o yaml

# Edit CronJob
kubectl edit cronjob <name>

# Delete all Jobs for a CronJob
kubectl delete jobs -l job-name=<cronjob-name>

# Get all failed Pods
kubectl get pods --field-selector status.phase=Failed

# Export CronJob configuration
kubectl get cronjob <name> -o yaml > my-cronjob-backup.yaml
```

---

## Troubleshooting

**Issue**: CronJob not creating Jobs

```bash
# Check CronJob status
kubectl describe cronjob <name>

# Common causes:
# - Suspended: Check SUSPEND column
# - Invalid schedule: Verify cron syntax
# - Controller issue: Check kube-controller-manager logs
```

**Issue**: Jobs failing repeatedly

```bash
# Check Job status
kubectl describe job <job-name>

# View Pod logs
kubectl logs <pod-name>

# Check for:
# - Image pull errors
# - Application errors
# - Resource constraints
# - Permission issues
```

**Issue**: Too many old Jobs consuming resources

```bash
# Reduce history limits
kubectl patch cronjob <name> -p '{"spec":{"successfulJobsHistoryLimit":1,"failedJobsHistoryLimit":1}}'

# Manually clean up
kubectl delete jobs -l job-name=<cronjob-name>
```

**Issue**: Job not starting at expected time

```bash
# Check controller time zone
kubectl get pods -n kube-system | grep controller-manager

# Verify schedule syntax
# Use https://crontab.guru/ to validate

# For timezone-aware jobs (K8s 1.25+), check timezone field
kubectl get cronjob <name> -o jsonpath='{.spec.timeZone}'

# Use IANA timezone names, not abbreviations (e.g., "America/New_York" not "EST")
```

**Issue**: Timezone field not recognized

```bash
# Check Kubernetes version
kubectl version --short

# Timezone support requires Kubernetes 1.25 or later
# If using older version, remove timeZone field and use UTC-based scheduling
```

---

## Real-World Examples

### Example 1: Database Backup CronJob

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: postgres-backup
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: postgres:15
            env:
            - name: PGHOST
              value: "postgres-service"
            - name: PGPASSWORD
              valueFrom:
                secretKeyRef:
                  name: postgres-secret
                  key: password
            command:
            - /bin/sh
            - -c
            - |
              BACKUP_FILE="/backups/backup-$(date +%Y%m%d-%H%M%S).sql"
              pg_dump -U postgres mydatabase > $BACKUP_FILE
              echo "Backup completed: $BACKUP_FILE"
            volumeMounts:
            - name: backup-storage
              mountPath: /backups
          restartPolicy: OnFailure
          volumes:
          - name: backup-storage
            persistentVolumeClaim:
              claimName: backup-pvc
  successfulJobsHistoryLimit: 7
  failedJobsHistoryLimit: 3
```

### Example 2: Log Cleanup CronJob

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: log-cleanup
spec:
  schedule: "0 0 * * *"  # Daily at midnight
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: cleanup
            image: busybox
            command:
            - /bin/sh
            - -c
            - |
              echo "Cleaning up logs older than 30 days"
              find /logs -name "*.log" -mtime +30 -delete
              echo "Cleanup completed"
            volumeMounts:
            - name: logs
              mountPath: /logs
          restartPolicy: OnFailure
          volumes:
          - name: logs
            hostPath:
              path: /var/log/apps
```

---

## Next Steps

Now that you understand CronJobs, proceed to:
- [Lab 30: Horizontal Pod Autoscaling](lab30-workload-hpa.md) - Auto-scale workloads based on metrics
- [Lab 09: Health Checks and Probes](lab09-pod-health-probes.md) - Implement liveness and readiness probes

## Further Reading

- [Kubernetes CronJob Documentation](https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/)
- [Cron Schedule Syntax](https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/#cron-schedule-syntax)
- [Job Patterns](https://kubernetes.io/docs/concepts/workloads/controllers/job/#job-patterns)
- [Crontab Guru - Cron Expression Helper](https://crontab.guru/)

---

**Lab Created**: March 2026
**Compatible with**: Kubernetes 1.24+
