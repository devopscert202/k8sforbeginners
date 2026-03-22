# Lab 03: ETCD Backup and Restore

## Overview
In this lab, you will learn how to backup and restore etcd, the distributed key-value store that serves as Kubernetes' brain. You'll understand why backups are critical, how to automate them, and practice disaster recovery procedures.

## Prerequisites
- A running Kubernetes cluster with control-plane access
- SSH access to the master/control-plane node
- Basic understanding of Kubernetes architecture
- Completion of Lab 01 and Lab 02 (recommended)

## Learning Objectives
By the end of this lab, you will be able to:
- Understand the role of etcd in Kubernetes
- Discover etcd endpoints using multiple methods
- Take manual backups of etcd data
- Verify backup integrity
- Restore etcd from a backup snapshot
- Automate backups with cron jobs
- Troubleshoot common etcd issues

---

## What is ETCD?

### Introduction
[`etcd`](https://etcd.io) is a distributed, consistent key-value store used by **Kubernetes** to persist all cluster state, including:

- Pods, deployments, services, and config maps
- Cluster metadata and control-plane coordination
- Role-based access control (RBAC) and secrets
- Custom resources and their definitions

### Why Backup ETCD?

Because Kubernetes depends on `etcd` as its **source of truth**, corruption or loss of `etcd` data can render the cluster unusable.

**Critical reasons for backing up etcd:**
- **Prevent data loss** after node crashes or disk failures
- **Enable disaster recovery** and cluster migration
- **Support forensic analysis** by restoring historical state
- **Practice resilience** with restore testing in staging

> 🛠️ **Best practice:** Back up `etcd` regularly (daily or more often), store backups off-cluster, and test restores.

---

## Exercise 1: Environment Setup

### Step 1: Install ETCD Client Tools

On your control-plane node:

```bash
sudo apt-get update
sudo apt-get install -y etcd-client
```

Verify installation:
```bash
etcdctl version
```

Expected output:
```
etcdctl version: 3.5.x
API version: 3.5
```

### Step 2: Verify Cluster Access

Check you have access to the control-plane node:
```bash
kubectl get nodes
```

Verify etcd pod is running:
```bash
kubectl -n kube-system get pods -l component=etcd
```

Expected output:
```
NAME                        READY   STATUS    RESTARTS   AGE
etcd-master.example.com     1/1     Running   0          5d
```

---

## Exercise 2: Discovering ETCD Endpoint

You need the etcd endpoint URL and certificates to connect. Try these methods in order.

### Method 1: Read from etcd.yaml Manifest (Quickest)

If you're on the control-plane node, the static pod manifest contains the endpoint:

```bash
cat /etc/kubernetes/manifests/etcd.yaml | grep advertise-client-urls
```

Extract it directly:
```bash
export ETCD_ENDPOINTS=$(grep -oP '(?<=--advertise-client-urls=)\S+' /etc/kubernetes/manifests/etcd.yaml)
echo $ETCD_ENDPOINTS
```

Expected output:
```
https://172.31.28.251:2379
```

**Understanding the URL:**
- `https://` - Secure connection with TLS
- `172.31.28.251` - Control-plane node IP
- `2379` - etcd client port (NOT 2380 which is for peer communication)

### Method 2: Using etcdctl member list

Run from the control-plane node:

```bash
sudo ETCDCTL_API=3 /usr/bin/etcdctl \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  member list
```

Expected output:
```
a0b86504f30e9756, started, master.example.com, https://172.31.28.251:2380, https://172.31.28.251:2379, false
```

Copy the **client URL** (the one ending in `:2379`):
```bash
export ETCD_ENDPOINTS="https://172.31.28.251:2379"
```

### Method 3: From Inside ETCD Pod (Fallback)

If the above methods fail:

```bash
# Get etcd pod name
ETCD_POD=$(kubectl -n kube-system get pods -l component=etcd -o jsonpath='{.items[0].metadata.name}')

# Execute inside the pod
kubectl -n kube-system exec -it $ETCD_POD -- sh -c '
ETCDCTL_API=3 etcdctl \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  member list
'
```

---

## Exercise 3: Taking a Manual Backup

### Step 1: Create Backup Directory

```bash
sudo mkdir -p /var/backups/etcd
```

### Step 2: Take a Snapshot

```bash
sudo ETCDCTL_API=3 /usr/bin/etcdctl \
  --endpoints="$ETCD_ENDPOINTS" \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  snapshot save /var/backups/etcd/etcd_backup_$(date +%Y%m%d_%H%M%S).db
```

Expected output:
```
{"level":"info","ts":1710612345.1234,"caller":"snapshot/v3_snapshot.go:68","msg":"created temporary db file","path":"/var/backups/etcd/etcd_backup_20260316_143000.db.part"}
{"level":"info","ts":1710612345.5678,"caller":"snapshot/v3_snapshot.go:119","msg":"fetching snapshot","endpoint":"https://172.31.28.251:2379"}
{"level":"info","ts":1710612346.1234,"caller":"snapshot/v3_snapshot.go:132","msg":"fetched snapshot","endpoint":"https://172.31.28.251:2379","size":"5.1 MB","took":"now"}
Snapshot saved at /var/backups/etcd/etcd_backup_20260316_143000.db
```

### Step 3: Verify File Created

```bash
ls -lh /var/backups/etcd/
```

Expected output:
```
-rw------- 1 root root 5.1M Mar 16 14:30 etcd_backup_20260316_143000.db
```

---

## Exercise 4: Verifying Backup Integrity

### Step 1: Check Snapshot Status

```bash
sudo ETCDCTL_API=3 /usr/bin/etcdctl \
  snapshot status /var/backups/etcd/etcd_backup_*.db \
  --write-out=table
```

Expected output:
```
+----------+----------+------------+------------+
|   HASH   | REVISION | TOTAL KEYS | TOTAL SIZE |
+----------+----------+------------+------------+
| 123abcd  |   45678  |    3500    |   5.1 MB   |
+----------+----------+------------+------------+
```

**Understanding the output:**
- **HASH**: Checksum to verify data integrity
- **REVISION**: etcd revision number
- **TOTAL KEYS**: Number of keys in the database
- **TOTAL SIZE**: Size of the snapshot

### Step 2: Document Cluster State

Before any restore operation, document current state:

```bash
kubectl get all --all-namespaces > /tmp/cluster_state_before_restore.txt
```

---

## Exercise 5: Restore from Backup (Disaster Recovery)

> ⚠️ **WARNING**: Restoration overwrites current etcd data. Only perform in emergencies or test environments!

### Step 1: Stop API Server (Optional but Recommended)

On the control-plane node:
```bash
sudo mv /etc/kubernetes/manifests/kube-apiserver.yaml /tmp/
```

Wait for API server to stop:
```bash
kubectl get nodes  # This should fail
```

### Step 2: Restore the Snapshot

> **Note**: `snapshot restore` is **local** and doesn't contact etcd. No cert flags required.

```bash
sudo ETCDCTL_API=3 /usr/bin/etcdctl snapshot restore \
  /var/backups/etcd/etcd_backup_*.db \
  --data-dir=/var/lib/etcd-restored \
  --name=master-restored \
  --initial-cluster=master-restored=https://172.31.28.251:2380 \
  --initial-cluster-token=etcd-cluster-restored \
  --initial-advertise-peer-urls=https://172.31.28.251:2380
```

Expected output:
```
{"level":"info","ts":1710612400.1234,"caller":"snapshot/v3_snapshot.go:296","msg":"restoring snapshot","path":"/var/backups/etcd/etcd_backup_20260316_143000.db","wal-dir":"/var/lib/etcd-restored/member/wal","data-dir":"/var/lib/etcd-restored","snap-dir":"/var/lib/etcd-restored/member/snap"}
```

### Step 3: Update ETCD Configuration

Edit the etcd manifest:
```bash
sudo nano /etc/kubernetes/manifests/etcd.yaml
```

Find and update these fields:
```yaml
spec:
  containers:
  - command:
    - etcd
    - --data-dir=/var/lib/etcd-restored     # Changed
    - --name=master-restored                 # Changed
    - --initial-cluster=master-restored=https://172.31.28.251:2380  # Changed
    - --initial-cluster-state=new           # Changed from 'existing'
```

Also update the volume mount path:
```yaml
  volumes:
  - hostPath:
      path: /var/lib/etcd-restored          # Changed
      type: DirectoryOrCreate
    name: etcd-data
```

### Step 4: Restart ETCD

Move the API server manifest back:
```bash
sudo mv /tmp/kube-apiserver.yaml /etc/kubernetes/manifests/
```

Delete the etcd pod to force restart:
```bash
kubectl -n kube-system delete pod etcd-master.example.com
```

### Step 5: Verify Restoration

Wait for cluster to stabilize (30-60 seconds), then check:

```bash
kubectl get nodes
kubectl get pods --all-namespaces
```

Compare with documented state:
```bash
kubectl get all --all-namespaces > /tmp/cluster_state_after_restore.txt
diff /tmp/cluster_state_before_restore.txt /tmp/cluster_state_after_restore.txt
```

---

## Exercise 6: Automating Backups

### Step 1: Create Backup Script

```bash
sudo nano /opt/etcd-backup.sh
```

Add the following content:

```bash
#!/bin/bash
#
# ETCD Automated Backup Script
# Purpose: Creates timestamped snapshots of etcd data
# Author: K8s Learning Team
# Date: March 2026
#

set -euo pipefail

# Configuration
export ETCDCTL_API=3
export ETCDCTL_CACERT=/etc/kubernetes/pki/etcd/ca.crt
export ETCDCTL_CERT=/etc/kubernetes/pki/etcd/server.crt
export ETCDCTL_KEY=/etc/kubernetes/pki/etcd/server.key

# Get etcd endpoint dynamically
ETCD_ENDPOINTS=$(grep -oP '(?<=--advertise-client-urls=)\S+' /etc/kubernetes/manifests/etcd.yaml)
BACKUP_DIR="/var/backups/etcd"
LOG_FILE="/var/log/etcd-backup.log"
RETENTION_DAYS=7

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Generate filename with timestamp
TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
SNAPSHOT="${BACKUP_DIR}/etcd-snapshot-${TIMESTAMP}.db"

# Log function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Take snapshot
log "Starting ETCD backup..."

if sudo ETCDCTL_API=3 /usr/bin/etcdctl \
  --endpoints="$ETCD_ENDPOINTS" \
  --cacert="$ETCDCTL_CACERT" \
  --cert="$ETCDCTL_CERT" \
  --key="$ETCDCTL_KEY" \
  snapshot save "$SNAPSHOT"; then

    log "✅ ETCD backup completed: $SNAPSHOT"

    # Verify snapshot
    sudo ETCDCTL_API=3 /usr/bin/etcdctl snapshot status "$SNAPSHOT" --write-out=table >> "$LOG_FILE" 2>&1

    # Calculate size
    SIZE=$(du -h "$SNAPSHOT" | cut -f1)
    log "Backup size: $SIZE"

else
    log "❌ ETCD backup FAILED!"
    exit 1
fi

# Remove old backups
log "Removing backups older than $RETENTION_DAYS days..."
find "$BACKUP_DIR" -type f -name "etcd-snapshot-*.db" -mtime +$RETENTION_DAYS -exec rm -f {} \; -print | tee -a "$LOG_FILE"

log "Backup process completed successfully"
exit 0
```

### Step 2: Make Script Executable

```bash
sudo chmod +x /opt/etcd-backup.sh
```

### Step 3: Test the Script

```bash
sudo /opt/etcd-backup.sh
```

Check logs:
```bash
tail -f /var/log/etcd-backup.log
```

### Step 4: Schedule with Cron

Edit root's crontab:
```bash
sudo crontab -e
```

Add daily backup at midnight:
```cron
# ETCD Daily Backup - Runs at midnight
0 0 * * * /opt/etcd-backup.sh >> /var/log/etcd-backup.log 2>&1
```

For more frequent backups (every 6 hours):
```cron
# ETCD Backup every 6 hours
0 */6 * * * /opt/etcd-backup.sh >> /var/log/etcd-backup.log 2>&1
```

Verify cron job:
```bash
sudo crontab -l
```

---

## Lab Cleanup

If you created test resources during restore practice:

```bash
# Remove test backup directory (keep production backups!)
# sudo rm -rf /var/backups/etcd/test/

# If you modified etcd data-dir for testing, revert to original:
# 1. Edit /etc/kubernetes/manifests/etcd.yaml
# 2. Change --data-dir back to /var/lib/etcd
# 3. Change --name back to original
# 4. Restart etcd pod
```

---

## Key Takeaways

1. **ETCD is critical** - It stores all Kubernetes cluster state
2. **Three methods** to discover etcd endpoint (manifest, etcdctl, pod exec)
3. **Backup command**: `etcdctl snapshot save`
4. **Verify command**: `etcdctl snapshot status`
5. **Restore command**: `etcdctl snapshot restore`
6. **Automation is essential** - Use cron for regular backups
7. **Test restores** - Verify backups work before disaster strikes
8. **Off-cluster storage** - Store backups remotely for true disaster recovery

---

## Troubleshooting Guide

### Issue: `context deadline exceeded`

**Symptoms**: etcdctl commands timeout

**Solutions**:
```bash
# Check endpoint is correct (port 2379, not 2380)
echo $ETCD_ENDPOINTS

# Test connectivity
nc -vz 172.31.28.251 2379

# Increase timeout
sudo ETCDCTL_API=3 /usr/bin/etcdctl --command-timeout=10s ...

# Verify certificates exist
ls -l /etc/kubernetes/pki/etcd/
```

### Issue: `snapshot file corrupt`

**Symptoms**: Restore fails with corruption error

**Solutions**:
```bash
# Verify backup integrity
sudo ETCDCTL_API=3 /usr/bin/etcdctl snapshot status /path/to/backup.db

# Take a fresh backup
sudo /opt/etcd-backup.sh

# Check disk space
df -h /var/backups/etcd
```

### Issue: Pod doesn't restart after restore

**Symptoms**: etcd pod stays in Pending/Error state

**Solutions**:
```bash
# Check etcd pod logs
kubectl -n kube-system logs etcd-master.example.com

# Verify manifest syntax
sudo cat /etc/kubernetes/manifests/etcd.yaml

# Check data directory permissions
sudo ls -ld /var/lib/etcd-restored

# Verify all required flags are set:
# --data-dir, --name, --initial-cluster, --initial-cluster-state
```

### Issue: Backup script fails in cron

**Symptoms**: Manual runs work, cron runs fail

**Solutions**:
```bash
# Check cron logs
sudo grep CRON /var/log/syslog

# Verify script has full paths
# Use /usr/bin/etcdctl not just etcdctl

# Test script with minimal environment
sudo env -i /opt/etcd-backup.sh

# Check file permissions
ls -l /opt/etcd-backup.sh
```

---

## Additional Commands Reference

```bash
# View etcd cluster health
sudo ETCDCTL_API=3 etcdctl \
  --endpoints="$ETCD_ENDPOINTS" \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  endpoint health

# Check etcd cluster status
sudo ETCDCTL_API=3 etcdctl \
  --endpoints="$ETCD_ENDPOINTS" \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  endpoint status --write-out=table

# List all etcd keys (be careful, can be large!)
sudo ETCDCTL_API=3 etcdctl \
  --endpoints="$ETCD_ENDPOINTS" \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  get / --prefix --keys-only

# Check backup size and age
ls -lh /var/backups/etcd/

# View backup logs
tail -50 /var/log/etcd-backup.log
```

---

## Next Steps

Proceed to [Lab 04: Essential kubectl Commands](lab04-kubectl-commands.md) to master Kubernetes command-line operations.

## Additional Reading

- [ETCD Official Documentation](https://etcd.io/docs/)
- [Kubernetes etcd Backup Best Practices](https://kubernetes.io/docs/tasks/administer-cluster/configure-upgrade-etcd/#backing-up-an-etcd-cluster)
- [Disaster Recovery for Kubernetes](https://kubernetes.io/docs/tasks/administer-cluster/configure-upgrade-etcd/#restoring-an-etcd-cluster)

---

**Lab Created**: March 2026
**Compatible with**: Kubernetes 1.24+
**Based on**: labs/administration/etcd-backup.md
**Tested on**: kubeadm clusters, AWS EKS, GCP GKE
