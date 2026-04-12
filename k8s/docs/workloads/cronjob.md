# **Kubernetes CronJob Tutorial**

## **Introduction to CronJobs**

A **CronJob** in Kubernetes is used to schedule jobs that run periodically, similar to the cron utility in Linux. It is well suited to automating repetitive tasks like backups, data cleanup, or sending periodic reports.

### **Use Cases for CronJobs**
- Database backups on a schedule.
- Sending periodic reports (for example, usage statistics).
- Cleaning up temporary files or logs.
- Rotating secrets and certificates.

---

## **What is a Kubernetes CronJob?**
A CronJob creates **Jobs** at specified times based on a cron schedule. Each **Job** runs one or more Pods to complete a specific task.

### **Key Features**
1. **Time-based scheduling**: Uses cron format (`minute hour day month weekday`).
2. **Retries**: Job and Pod restart policies control retries for failed runs.
3. **Concurrency policies**:
   - `Allow`: Multiple Jobs may run simultaneously.
   - `Forbid`: Only one Job runs at a time; if a new schedule fires while one is running, that run may be skipped.
   - `Replace`: The current running Job may be replaced by a newly scheduled one.
4. **Retention policy**: `successfulJobsHistoryLimit` and `failedJobsHistoryLimit` control how many completed Job objects are kept for debugging and auditing.

---

## **Example: CronJob manifest**

This example runs a simple task on a schedule and retains a small history of Job objects:

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
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 1
```

### **Explanation of the manifest**
- **`schedule`**: Cron expression; `*/5 * * * *` means every five minutes.
- **`jobTemplate`**: Template for each Job the CronJob creates (Pod spec, restart policy, and so on).
- **`restartPolicy`**: For Jobs, commonly `OnFailure` or `Never` (not `Always`).
- **`successfulJobsHistoryLimit`** / **`failedJobsHistoryLimit`**: How many finished Jobs to retain.

### **Cron schedule fields**

Standard five-field cron syntax:

```
┌───────────── minute (0 - 59)
│ ┌───────────── hour (0 - 23)
│ │ ┌───────────── day of month (1 - 31)
│ │ │ ┌───────────── month (1 - 12)
│ │ │ │ ┌───────────── day of week (0 - 6, Sunday = 0)
│ │ │ │ │
* * * * *
```

---

## **Advantages of CronJobs**
1. **Automation**: Encapsulates recurring tasks in cluster-native objects.
2. **Reliability**: Failed runs can be retried according to Job and container policies.
3. **Integration**: Scheduled work is visible alongside other workloads (`kubectl get cronjobs`, `kubectl get jobs`).
4. **Auditability**: History limits preserve recent successes and failures for troubleshooting.

---

## **Summary Table**

| **Feature**               | **Description**                                                   |
|---------------------------|-------------------------------------------------------------------|
| **Scheduling**            | Time-based Jobs using cron syntax.                                |
| **Retries**               | Influenced by `restartPolicy` and Job backoff behavior.             |
| **Concurrency policies**  | Control overlap between scheduled Job runs.                       |
| **History limits**        | Retain a bounded number of successful and failed Job records.       |

---

## **Use Cases (recap)**
1. Scheduled backups of databases or volumes.
2. Cleaning up old logs or temporary files.
3. Sending periodic alerts or metrics.
4. Automating certificate renewals.

---

## Hands-On Labs

Practice these concepts with guided lab exercises:

| Lab | Description |
|-----|-------------|
| [Lab 29: CronJobs](../../labmanuals/lab29-workload-cronjobs.md) | Create CronJobs, observe Job creation, and explore schedules and history limits. |
