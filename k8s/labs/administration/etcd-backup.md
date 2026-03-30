# 📝 Kubernetes ETCD Backup & Restore Lab

## 📌 Introduction

[`etcd`](https://etcd.io) is a distributed, consistent key-value store used by **Kubernetes** to persist all cluster state, including:

* Pods, deployments, services, and config maps.
* Cluster metadata and control-plane coordination.
* Role-based access control (RBAC) and secrets.

Because Kubernetes depends on `etcd` as its **source of truth**, corruption or loss of `etcd` data can render the cluster unusable.

👉 **Why back up `etcd`?**

* Prevent data loss after node crashes or disk failures.
* Enable disaster recovery and cluster migration.
* Support forensic analysis by restoring historical state.
* Practice resilience with restore testing in staging.

> 🛠️ **Best practice:** Back up `etcd` regularly (daily or more often), store backups off-cluster, and test restores.

---

## ⚡ Prerequisites

1. **Kubernetes cluster** (control-plane runs `etcd` as a static pod or external cluster).
2. **Access** to the control-plane node(s).
3. **Tools installed:**

   * `etcdctl`
   * `kubectl`

Install the client if missing:

```bash
sudo apt-get update
sudo apt-get install -y etcd-client
```

---

## 🔑 Step 1: Discover ETCD Endpoint

### Option A — Run from Control-Plane Node (Preferred)

Run this on the **control-plane node** where certs exist at `/etc/kubernetes/pki/etcd`:

```bash
sudo ETCDCTL_API=3 /usr/bin/etcdctl \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  member list
```

If successful, output looks like:

```
a0b86504f30e9756, started, master.example.com, https://172.31.28.251:2380, https://172.31.28.251:2379, false
```

👉 Use the **client URL** (`https://172.31.28.251:2379`):

```bash
export ETCD_ENDPOINTS="https://172.31.28.251:2379"
```

#### 🚨 If you see `context deadline exceeded`

This means the client can’t reach etcd. Common fixes:

* Ensure you use the **client port (2379)**, not peer port (2380).
* Verify connectivity:

  ```bash
  nc -vz 172.31.28.251 2379
  ```
* Test TLS handshake:

  ```bash
  openssl s_client -connect 172.31.28.251:2379 -CAfile /etc/kubernetes/pki/etcd/ca.crt </dev/null | head -20
  ```
* Increase timeout:

  ```bash
  sudo ETCDCTL_API=3 /usr/bin/etcdctl --command-timeout=10s ...
  ```

If still failing → use **Option B**.

---

### Option B — Run from Inside ETCD Pod (Fallback)

List the etcd pod:

```bash
kubectl -n kube-system get pods -l component=etcd
```

Exec into it and run `etcdctl`:

```bash
kubectl -n kube-system exec -it <etcd-pod-name> -- /bin/sh -c '
ETCDCTL_API=3 etcdctl \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  member list
'
```

Copy the **client URL** from the output (`https://<ip>:2379`) and export:

```bash
export ETCD_ENDPOINTS="https://172.31.28.251:2379"
```


---

### Option C — Quick way: Read from `etcd.yaml`

If you are on the control-plane node, the `etcd` static pod manifest is at:

```
/etc/kubernetes/manifests/etcd.yaml
```

Inside you’ll find a line like:

```yaml
- --advertise-client-urls=https://172.31.28.251:2379
```

You can extract it directly with:

```bash
grep -oP '(?<=--advertise-client-urls=)\S+' /etc/kubernetes/manifests/etcd.yaml
```

Example output:

```
https://172.31.28.251:2379
```

Then export it for later commands:

```bash
export ETCD_ENDPOINTS=$(grep -oP '(?<=--advertise-client-urls=)\S+' /etc/kubernetes/manifests/etcd.yaml)
```

---

⚡ This method avoids `etcdctl member list` and is a **quick shortcut** if you just need the client URL already defined for the running etcd pod.



## 💾 Step 2: Take a Backup

Save a snapshot of etcd:

```bash
sudo ETCDCTL_API=3 /usr/bin/etcdctl \
  --endpoints="$ETCD_ENDPOINTS" \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  snapshot save /tmp/etcd_backup.db
```

---

## 🔍 Step 3: Verify Backup

```bash
sudo ETCDCTL_API=3 /usr/bin/etcdctl \
  snapshot status /tmp/etcd_backup.db \
  --write-out=table
```

Example:

```
+----------+---------+----------+------------+
|   HASH   | VERSION |   SIZE   | TOTAL KEYS |
+----------+---------+----------+------------+
| 123abcd  |  3.5.0  |  5.1 MB  |    3500    |
+----------+---------+----------+------------+
```

---

## 🔄 Step 4: Restore from Backup

> ⚠️ `snapshot restore` is **local** (does not contact etcd). No cert flags required.

```bash
sudo ETCDCTL_API=3 /usr/bin/etcdctl snapshot restore /tmp/etcd_backup.db \
  --data-dir=/var/lib/etcd-new \
  --name=master-restored
```

### Update static pod manifest

Edit `/etc/kubernetes/manifests/etcd.yaml`:

```yaml
- --data-dir=/var/lib/etcd-new
- --name=master-restored
- --initial-cluster=master-restored=https://172.31.28.251:2380
- --initial-cluster-state=new
```

### Restart etcd pod

```bash
kubectl -n kube-system delete pod etcd-<master-node-name>
```

Kubelet will recreate it with new settings.

---

## ⚙️ Step 5: Automate Backups with Cron

### Create script `/opt/etcd-backup.sh`

```bash
#!/bin/bash
set -euo pipefail

export ETCDCTL_API=3
export ETCDCTL_CACERT=/etc/kubernetes/pki/etcd/ca.crt
export ETCDCTL_CERT=/etc/kubernetes/pki/etcd/server.crt
export ETCDCTL_KEY=/etc/kubernetes/pki/etcd/server.key

ETCD_ENDPOINTS="https://172.31.28.251:2379"
BACKUP_DIR="/var/backups/etcd"
mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
SNAPSHOT="${BACKUP_DIR}/etcd-snapshot-${TIMESTAMP}.db"

sudo ETCDCTL_API=3 /usr/bin/etcdctl \
  --endpoints="$ETCD_ENDPOINTS" \
  --cacert="$ETCDCTL_CACERT" \
  --cert="$ETCDCTL_CERT" \
  --key="$ETCDCTL_KEY" \
  snapshot save "$SNAPSHOT"

# Remove backups older than 7 days
find "$BACKUP_DIR" -type f -name "etcd-snapshot-*.db" -mtime +7 -exec rm -f {} \;

echo "✅ ETCD backup completed: $SNAPSHOT"
```

Make executable and test:

```bash
sudo chmod +x /opt/etcd-backup.sh
sudo /opt/etcd-backup.sh
```

### Schedule daily cron job

Edit crontab:

```bash
sudo crontab -e
```

Add:

```cron
0 0 * * * /opt/etcd-backup.sh >> /var/log/etcd-backup.log 2>&1
```

---

## 🧪 Step 6: Test Restore (Optional)

* Always practice restores in **staging**.
* Bring up a fresh etcd instance → `snapshot restore` → point kube-apiserver → validate cluster state.

---

## ⚠️ Common Issues

| **Issue**                         | **Fix**                                                                   |
| --------------------------------- | ------------------------------------------------------------------------- |
| `context deadline exceeded`       | Check port `2379`, certs, endpoint URL. If unresolved → use Option B.     |
| Wrong endpoint used               | Use `:2379` (client), not `:2380` (peer).                                 |
| `snapshot file corrupt`           | Backup was incomplete → re-run backup and verify status.                  |
| Pod doesn’t restart after restore | Ensure `--data-dir`, `--name`, and `--initial-cluster` flags are correct. |

---

## 📌 Summary

* **Backup:** `etcdctl snapshot save`
* **Verify:** `etcdctl snapshot status`
* **Restore:** `etcdctl snapshot restore`
* **Automate:** Cron + shell script

Regular automated etcd backups + tested restore = reliable Kubernetes disaster recovery.
