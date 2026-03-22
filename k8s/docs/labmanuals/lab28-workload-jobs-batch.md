# Lab 28: Jobs and Batch Processing in Kubernetes

## Overview
In this lab, you will learn how to run batch workloads and scheduled tasks in Kubernetes using Jobs and CronJobs. Unlike Deployments that run continuously, Jobs are designed for tasks that run to completion.

## Prerequisites
- A running Kubernetes cluster (Minikube, Kind, or any K8s cluster)
- `kubectl` CLI tool installed and configured
- Completion of Lab 01 (Creating Pods) is recommended
- Basic understanding of cron expressions (for CronJob section)

## Learning Objectives
By the end of this lab, you will be able to:
- Create and manage Kubernetes Jobs
- Understand Job completion and failure handling
- Configure Job parallelism and completion counts
- Create scheduled tasks using CronJobs
- Monitor and troubleshoot batch workloads
- Clean up completed Jobs automatically

---

## What is a Job?

A **Job** creates one or more Pods and ensures that a specified number of them successfully complete. Jobs are ideal for:
- Batch processing tasks
- Data processing pipelines
- Database migrations
- Backup operations
- One-time initialization tasks

**Key Characteristics:**
- Runs to completion (not continuously)
- Tracks successful completions
- Handles Pod failures with retry logic
- Cleans up Pods after completion
- Supports parallel execution

### Jobs vs Deployments

| Feature | Job | Deployment |
|---------|-----|------------|
| **Purpose** | Run to completion | Run continuously |
| **Lifecycle** | Terminates when done | Runs indefinitely |
| **Restart Policy** | Never or OnFailure | Always |
| **Use Case** | Batch processing, migrations | Web servers, APIs |
| **Success Criteria** | Completion count reached | Pods stay running |

---

## Exercise 1: Creating a Basic Job

### Step 1: Review the Job Manifest

Let's look at `jobs.yaml`:

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: pi
spec:
  template:
    spec:
      containers:
      - name: pi
        image: perl
        command: ["perl", "-Mbignum=bpi", "-wle", "print bpi(2000)"]
      restartPolicy: Never
  backoffLimit: 4
```

**Understanding the manifest:**
- `apiVersion: batch/v1` - Uses the batch API group
- `kind: Job` - Defines this as a Job resource
- `metadata.name: pi` - Names the Job "pi"
- `spec.template` - Pod template for the Job
- `command` - Calculates Pi to 2000 digits using Perl
- `restartPolicy: Never` - Don't restart container on failure
- `backoffLimit: 4` - Maximum retry attempts before marking as failed

### Step 2: Deploy the Job

Navigate to the workloads directory:
```bash
cd k8s/labs/workloads
```

Create the Job:
```bash
kubectl apply -f jobs.yaml
```

Expected output:
```
job.batch/pi created
```

### Step 3: Monitor Job Progress

Check Job status:
```bash
kubectl get jobs
```

Expected output:
```
NAME   COMPLETIONS   DURATION   AGE
pi     0/1           5s         5s
```

Watch the Job in real-time:
```bash
kubectl get jobs -w
```

After completion:
```
NAME   COMPLETIONS   DURATION   AGE
pi     1/1           12s        30s
```

Press Ctrl+C to exit watch mode.

### Step 4: View Job Details

Get detailed Job information:
```bash
kubectl describe job pi
```

Expected output shows:
- Pod creation events
- Completion status
- Duration
- Parallelism settings

View the Pods created by the Job:
```bash
kubectl get pods -l job-name=pi
```

Expected output:
```
NAME       READY   STATUS      RESTARTS   AGE
pi-xxxxx   0/1     Completed   0          1m
```

Notice the `STATUS: Completed` - the Pod finished successfully.

### Step 5: View Job Output

Check the Pod logs to see the calculated Pi value:
```bash
kubectl logs -l job-name=pi
```

You should see Pi calculated to 2000 digits!

Alternatively, get the Pod name and view logs:
```bash
POD_NAME=$(kubectl get pods -l job-name=pi -o jsonpath='{.items[0].metadata.name}')
kubectl logs $POD_NAME
```

---

## Exercise 2: Understanding Job Behavior

### Step 1: Create a Simple Job

Let's look at `onemin-job.yaml`:

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: one-minute-job
spec:
  template:
    spec:
      containers:
      - name: one-minute-container
        image: busybox
        command: ["sh", "-c", "echo 'Job is running'; sleep 60; echo 'Job is done'"]
      restartPolicy: Never
  backoffLimit: 2
```

**Understanding the manifest:**
- Uses `busybox` image for lightweight container
- Runs for exactly 60 seconds
- Prints messages at start and end
- `backoffLimit: 2` - Only 2 retry attempts

### Step 2: Deploy and Monitor

Create the Job:
```bash
kubectl apply -f onemin-job.yaml
```

Immediately start monitoring:
```bash
kubectl get jobs one-minute-job -w
```

You'll see:
1. `0/1` - Job started, not completed
2. After 60 seconds: `1/1` - Job completed

In another terminal, watch the Pod:
```bash
kubectl get pods -l job-name=one-minute-job -w
```

You'll see:
1. `Pending` - Pod is being created
2. `ContainerCreating` - Container is starting
3. `Running` - Job is executing
4. `Completed` - Job finished successfully

### Step 3: View Job Logs

Check the output:
```bash
kubectl logs -l job-name=one-minute-job
```

Expected output:
```
Job is running
Job is done
```

---

## Exercise 3: Job Failure and Retry Behavior

### Understanding backoffLimit

The `backoffLimit` controls how many times Kubernetes retries a failed Job. The backoff delay increases exponentially: 10s, 20s, 40s, etc.

### Step 1: Create a Failing Job

Create a Job that always fails:
```bash
cat > failing-job.yaml <<EOF
apiVersion: batch/v1
kind: Job
metadata:
  name: failing-job
spec:
  template:
    spec:
      containers:
      - name: fail-container
        image: busybox
        command: ["sh", "-c", "echo 'This will fail'; exit 1"]
      restartPolicy: Never
  backoffLimit: 3
EOF
```

### Step 2: Apply and Monitor

Create the Job:
```bash
kubectl apply -f failing-job.yaml
```

Watch the Pods:
```bash
kubectl get pods -l job-name=failing-job -w
```

You'll see multiple Pods being created (up to 4 total: initial + 3 retries):
```
failing-job-xxxxx   0/1     Error       0          10s
failing-job-yyyyy   0/1     Error       0          20s
failing-job-zzzzz   0/1     Error       0          40s
failing-job-wwwww   0/1     Error       0          80s
```

Check Job status:
```bash
kubectl get job failing-job
```

Expected output:
```
NAME          COMPLETIONS   DURATION   AGE
failing-job   0/1           2m         2m
```

Describe the Job to see failure details:
```bash
kubectl describe job failing-job
```

Look for events showing:
- Multiple Pod creations
- Backoff messages
- Final failure status

### Step 3: Clean Up Failed Job

Delete the failed Job and its Pods:
```bash
kubectl delete job failing-job
```

---

## Exercise 4: Job Parallelism and Completions

### Understanding Parallel Jobs

Jobs can run multiple Pods in parallel to speed up processing:
- `completions`: Total number of successful completions needed
- `parallelism`: Maximum number of Pods running simultaneously

### Step 1: Create a Parallel Job

Create a Job that runs 5 completions with 2 parallel workers:
```bash
cat > parallel-job.yaml <<EOF
apiVersion: batch/v1
kind: Job
metadata:
  name: parallel-job
spec:
  completions: 5
  parallelism: 2
  template:
    spec:
      containers:
      - name: worker
        image: busybox
        command: ["sh", "-c", "echo 'Processing task'; sleep 10; echo 'Task complete'"]
      restartPolicy: Never
  backoffLimit: 3
EOF
```

### Step 2: Deploy and Monitor

Create the Job:
```bash
kubectl apply -f parallel-job.yaml
```

Watch the Pods:
```bash
kubectl get pods -l job-name=parallel-job -w
```

Observations:
- Initially, 2 Pods start (parallelism=2)
- When one completes, another starts
- Continues until 5 completions achieved
- Total time: ~30 seconds (vs 50 seconds if sequential)

Check Job progress:
```bash
kubectl get job parallel-job
```

Expected output:
```
NAME           COMPLETIONS   DURATION   AGE
parallel-job   5/5           35s        40s
```

### Step 3: Verify All Completions

List all Pods created by the Job:
```bash
kubectl get pods -l job-name=parallel-job
```

Expected output shows 5 completed Pods:
```
NAME                 READY   STATUS      RESTARTS   AGE
parallel-job-xxxxx   0/1     Completed   0          1m
parallel-job-yyyyy   0/1     Completed   0          1m
parallel-job-zzzzz   0/1     Completed   0          50s
parallel-job-wwwww   0/1     Completed   0          40s
parallel-job-vvvvv   0/1     Completed   0          30s
```

---

## Exercise 5: CronJobs for Scheduled Tasks

### What is a CronJob?

A **CronJob** creates Jobs on a repeating schedule using cron expressions. Perfect for:
- Scheduled backups
- Report generation
- Data cleanup tasks
- Health checks
- Periodic data synchronization

### Understanding Cron Expressions

Cron format: `minute hour day month weekday`

Common examples:
- `*/5 * * * *` - Every 5 minutes
- `0 * * * *` - Every hour
- `0 0 * * *` - Daily at midnight
- `0 0 * * 0` - Weekly on Sunday
- `30 2 * * 1-5` - Weekdays at 2:30 AM

### Step 1: Review the CronJob Manifest

Let's look at `cronjob.yaml`:

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

**Understanding the manifest:**
- `apiVersion: batch/v1` - Uses the batch API
- `kind: CronJob` - Defines this as a CronJob resource
- `schedule: "*/5 * * * *"` - Runs every 5 minutes
- `jobTemplate` - Template for Jobs created by CronJob
- `successfulJobsHistoryLimit: 3` - Keeps last 3 successful Jobs
- `failedJobsHistoryLimit: 1` - Keeps last 1 failed Job

### Step 2: Deploy the CronJob

Create the CronJob:
```bash
kubectl apply -f cronjob.yaml
```

Expected output:
```
cronjob.batch/hello-cronjob created
```

### Step 3: Monitor CronJob

View CronJobs:
```bash
kubectl get cronjobs
```

Expected output:
```
NAME            SCHEDULE      SUSPEND   ACTIVE   LAST SCHEDULE   AGE
hello-cronjob   */5 * * * *   False     0        <none>          20s
```

Wait for the first Job to be created (up to 5 minutes):
```bash
kubectl get cronjobs hello-cronjob -w
```

After the schedule triggers:
```
NAME            SCHEDULE      SUSPEND   ACTIVE   LAST SCHEDULE   AGE
hello-cronjob   */5 * * * *   False     1        10s             5m
```

### Step 4: View CronJob Executions

List Jobs created by the CronJob:
```bash
kubectl get jobs -l job-name
```

Or more specifically:
```bash
kubectl get jobs | grep hello-cronjob
```

Expected output:
```
NAME                     COMPLETIONS   DURATION   AGE
hello-cronjob-28012345   1/1           5s         2m
hello-cronjob-28012350   1/1           4s         7m
```

View Pods created by CronJob:
```bash
kubectl get pods | grep hello-cronjob
```

### Step 5: Check CronJob Output

View logs from the most recent execution:
```bash
kubectl logs -l job-name --tail=20
```

Or get logs from a specific Job:
```bash
JOB_NAME=$(kubectl get jobs -l job-name -o jsonpath='{.items[-1].metadata.name}' | grep hello-cronjob)
kubectl logs job/$JOB_NAME
```

Expected output:
```
Mon Jan 15 14:35:00 UTC 2026
Hello from Kubernetes CronJob!
```

---

## Exercise 6: CronJob Management

### Suspend a CronJob

Temporarily stop the CronJob from running:
```bash
kubectl patch cronjob hello-cronjob -p '{"spec":{"suspend":true}}'
```

Verify:
```bash
kubectl get cronjob hello-cronjob
```

Expected output:
```
NAME            SCHEDULE      SUSPEND   ACTIVE   LAST SCHEDULE   AGE
hello-cronjob   */5 * * * *   True      0        2m              15m
```

### Resume a CronJob

Re-enable the CronJob:
```bash
kubectl patch cronjob hello-cronjob -p '{"spec":{"suspend":false}}'
```

### Trigger a Manual Run

Create a Job from the CronJob template:
```bash
kubectl create job manual-run --from=cronjob/hello-cronjob
```

View the manual Job:
```bash
kubectl get job manual-run
```

Check logs:
```bash
kubectl logs job/manual-run
```

### View CronJob History

Get detailed CronJob information:
```bash
kubectl describe cronjob hello-cronjob
```

Look for:
- Last scheduled time
- Active Jobs
- Events showing Job creation

---

## Exercise 7: Advanced CronJob Configuration

### Step 1: Create a CronJob with Concurrency Policy

Create a CronJob that prevents overlapping executions:
```bash
cat > backup-cronjob.yaml <<EOF
apiVersion: batch/v1
kind: CronJob
metadata:
  name: backup-job
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  concurrencyPolicy: Forbid  # Prevent concurrent runs
  startingDeadlineSeconds: 300  # Start within 5 minutes
  successfulJobsHistoryLimit: 7  # Keep 7 days of backups
  failedJobsHistoryLimit: 3
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: busybox
            command:
            - /bin/sh
            - -c
            - |
              echo "Starting backup at \$(date)"
              echo "Backing up database..."
              sleep 30
              echo "Backup completed at \$(date)"
          restartPolicy: OnFailure
      backoffLimit: 3
EOF
```

**New parameters explained:**
- `concurrencyPolicy: Forbid` - Skip new run if previous is still running
  - `Allow` - Allow concurrent Jobs (default)
  - `Replace` - Cancel current Job and start new one
- `startingDeadlineSeconds: 300` - Job must start within 5 minutes of scheduled time

Apply the CronJob:
```bash
kubectl apply -f backup-cronjob.yaml
```

### Step 2: Test Concurrency Policy

Manually trigger overlapping Jobs:
```bash
kubectl create job backup-test-1 --from=cronjob/backup-job
kubectl create job backup-test-2 --from=cronjob/backup-job
```

Check Job status:
```bash
kubectl get jobs | grep backup
```

---

## Exercise 8: Job TTL and Cleanup

### Automatic Cleanup with TTL

Jobs can automatically clean up after completion using TTL (Time To Live):

Create a self-cleaning Job:
```bash
cat > ttl-job.yaml <<EOF
apiVersion: batch/v1
kind: Job
metadata:
  name: ttl-example
spec:
  ttlSecondsAfterFinished: 100  # Delete 100 seconds after completion
  template:
    spec:
      containers:
      - name: cleanup-test
        image: busybox
        command: ["sh", "-c", "echo 'This Job will auto-delete'; sleep 10"]
      restartPolicy: Never
EOF
```

Apply and monitor:
```bash
kubectl apply -f ttl-job.yaml
kubectl get jobs ttl-example -w
```

After completion, the Job will be deleted automatically after 100 seconds.

### Manual Cleanup

Delete completed Jobs manually:
```bash
# Delete specific Job
kubectl delete job parallel-job

# Delete all Jobs
kubectl delete jobs --all

# Delete Jobs older than 1 hour
kubectl delete jobs --field-selector status.successful=1
```

---

## Lab Cleanup

Remove all resources created in this lab:

```bash
# Delete Jobs
kubectl delete job pi
kubectl delete job one-minute-job
kubectl delete job parallel-job
kubectl delete job manual-run

# Delete CronJobs (also deletes associated Jobs)
kubectl delete cronjob hello-cronjob
kubectl delete cronjob backup-job

# Delete any remaining resources
kubectl delete -f jobs.yaml
kubectl delete -f onemin-job.yaml
kubectl delete -f cronjob.yaml

# Verify cleanup
kubectl get jobs
kubectl get cronjobs
kubectl get pods
```

Clean up local files:
```bash
rm -f failing-job.yaml parallel-job.yaml backup-cronjob.yaml ttl-job.yaml
```

---

## Key Takeaways

1. **Jobs** run Pods to completion, ideal for batch processing
2. **CronJobs** schedule Jobs using cron expressions
3. `backoffLimit` controls retry behavior for failed Jobs
4. `completions` and `parallelism` enable parallel processing
5. CronJobs maintain history of successful and failed Jobs
6. Use `concurrencyPolicy` to control overlapping Job executions
7. `restartPolicy` must be `Never` or `OnFailure` for Jobs
8. Jobs don't auto-delete by default - use TTL or manual cleanup
9. CronJobs are perfect for scheduled maintenance tasks
10. Monitor Job logs to debug failures

---

## Additional Commands Reference

```bash
# List all Jobs
kubectl get jobs

# List all CronJobs
kubectl get cronjobs

# View Job details
kubectl describe job <job-name>

# View CronJob details
kubectl describe cronjob <cronjob-name>

# View Job logs
kubectl logs job/<job-name>

# Delete completed Jobs
kubectl delete jobs --field-selector status.successful=1

# Suspend CronJob
kubectl patch cronjob <name> -p '{"spec":{"suspend":true}}'

# Resume CronJob
kubectl patch cronjob <name> -p '{"spec":{"suspend":false}}'

# Create manual Job from CronJob
kubectl create job <job-name> --from=cronjob/<cronjob-name>

# View CronJob schedule
kubectl get cronjob <name> -o jsonpath='{.spec.schedule}'

# List Pods for a specific Job
kubectl get pods -l job-name=<job-name>

# Delete all Jobs in namespace
kubectl delete jobs --all

# Watch Job progress
kubectl get jobs -w
```

---

## Best Practices

### For Jobs

1. **Always set backoffLimit**: Prevent infinite retries
2. **Use appropriate restart policies**: Never or OnFailure
3. **Set resource limits**: Prevent resource exhaustion
4. **Add TTL for cleanup**: Auto-delete completed Jobs
5. **Use labels**: Organize and select Jobs easily
6. **Monitor completion**: Set up alerts for failed Jobs
7. **Test before production**: Verify Job behavior in dev environment

### For CronJobs

1. **Choose appropriate schedule**: Consider timezone (CronJobs use UTC)
2. **Set concurrency policy**: Prevent resource conflicts
3. **Configure history limits**: Balance between history and resource usage
4. **Use startingDeadlineSeconds**: Handle missed schedules
5. **Monitor failures**: Set up alerts for failed CronJobs
6. **Test manually first**: Use `kubectl create job --from=cronjob`
7. **Document schedule**: Comment cron expressions for clarity
8. **Plan for maintenance**: Suspend CronJobs during cluster maintenance

### Resource Management

```yaml
# Example with resource limits
apiVersion: batch/v1
kind: Job
metadata:
  name: resource-limited-job
spec:
  template:
    spec:
      containers:
      - name: worker
        image: busybox
        resources:
          requests:
            memory: "64Mi"
            cpu: "250m"
          limits:
            memory: "128Mi"
            cpu: "500m"
        command: ["sh", "-c", "echo 'Processing'; sleep 30"]
      restartPolicy: Never
  backoffLimit: 3
```

---

## Real-World Use Cases

### Use Case 1: Database Backup

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: db-backup
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  concurrencyPolicy: Forbid
  successfulJobsHistoryLimit: 7
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: postgres:13
            env:
            - name: PGPASSWORD
              valueFrom:
                secretKeyRef:
                  name: db-secret
                  key: password
            command:
            - /bin/sh
            - -c
            - |
              pg_dump -h db-service -U admin mydb > /backup/db-$(date +%Y%m%d).sql
              echo "Backup completed"
            volumeMounts:
            - name: backup-volume
              mountPath: /backup
          volumes:
          - name: backup-volume
            persistentVolumeClaim:
              claimName: backup-pvc
          restartPolicy: OnFailure
```

### Use Case 2: Data Processing Pipeline

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: data-pipeline
spec:
  completions: 10
  parallelism: 3
  template:
    spec:
      containers:
      - name: processor
        image: python:3.9
        command:
        - python
        - -c
        - |
          import os
          import time
          job_id = os.environ.get('JOB_COMPLETION_INDEX', '0')
          print(f"Processing batch {job_id}")
          time.sleep(20)
          print(f"Batch {job_id} completed")
      restartPolicy: Never
  backoffLimit: 3
```

### Use Case 3: Report Generation

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: weekly-report
spec:
  schedule: "0 9 * * 1"  # Monday at 9 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: report-generator
            image: mycompany/report-generator:latest
            env:
            - name: REPORT_TYPE
              value: "weekly"
            - name: EMAIL_RECIPIENTS
              value: "team@example.com"
          restartPolicy: OnFailure
  successfulJobsHistoryLimit: 4
```

---

## Troubleshooting

**Job stuck in Active state?**
- Check Pod status: `kubectl get pods -l job-name=<name>`
- View Pod logs: `kubectl logs <pod-name>`
- Check resource availability: `kubectl describe node`

**CronJob not running?**
- Verify schedule syntax: Check cron expression
- Check if suspended: `kubectl get cronjob <name>`
- View events: `kubectl describe cronjob <name>`

**Job fails repeatedly?**
- Check Pod logs: `kubectl logs job/<name>`
- Increase backoffLimit if transient failures
- Verify image and command are correct
- Check resource limits

**CronJob creates too many Jobs?**
- Lower successfulJobsHistoryLimit
- Set TTL on Job template
- Increase cleanup frequency

**Pods not deleted after Job completion?**
- Set ttlSecondsAfterFinished in Job spec
- Manually delete: `kubectl delete job <name>`
- Check if Job has finalizers

---

## Next Steps

You've completed the Jobs and Batch Processing lab! Consider exploring:
- [Lab 25: ConfigMaps](lab25-workload-configmaps.md) for configuration management
- StatefulSets for stateful applications
- Init Containers for setup tasks
- Pod presets and priorities

## Additional Resources

- [Kubernetes Jobs Documentation](https://kubernetes.io/docs/concepts/workloads/controllers/job/)
- [CronJob Documentation](https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/)
- [Crontab Guru](https://crontab.guru/) - Cron expression helper
- [Parallel Processing with Jobs](https://kubernetes.io/docs/tasks/job/parallel-processing-expansion/)

---

**Lab Created**: March 2026
**Compatible with**: Kubernetes 1.24+
