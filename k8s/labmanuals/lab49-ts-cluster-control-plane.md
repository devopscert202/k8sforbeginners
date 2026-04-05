# Lab 49: Cluster and Control Plane Troubleshooting

## Overview

This lab gives you hands-on practice diagnosing issues that affect the Kubernetes control plane: the API server, scheduler, controller manager, and etcd. You will use `kubectl`, health endpoints, component logs, and `etcdctl` in scenarios aligned with the CKA troubleshooting domain. Exercises progress from quick health checks to log analysis and a guided break-fix with `ResourceQuota`.

## Prerequisites

- Running Kubernetes cluster (kubeadm-based preferred for full control plane and static pod access)
- `kubectl` configured; SSH access to a control plane node (for `journalctl`, `crictl`, certificate paths, and etcd)
- Basic understanding of Kubernetes architecture (Lab 01)
- Optional: `etcdctl` installed on the control plane node (see Lab 07 for install steps)

## Learning Objectives

- Check cluster health with `kubectl` and API server healthz-style endpoints
- Diagnose API server connectivity and certificate-related failure modes (read-only scenarios)
- Troubleshoot scheduler behavior when pods remain `Pending`
- Identify controller manager involvement using ReplicaSets, events, and logs
- Use `etcdctl` for endpoint health, status, alarms, and snapshot verification
- Read control plane and node logs systematically with `kubectl logs`, `journalctl`, and `/var/log/pods`

---

## Exercise 1: Checking Cluster Health

### Step 1: Confirm the cluster control plane endpoint

```bash
kubectl cluster-info
```

You should see the Kubernetes control plane address and (if installed) the CoreDNS service URL.

```bash
kubectl get nodes -o wide
```

Verify all intended nodes are `Ready`. Any `NotReady` node affects scheduling and may surface as control-plane symptoms if it hosts control plane pods.

### Step 2: Legacy component status (know the deprecation)

```bash
kubectl get componentstatuses
```

On clusters **before Kubernetes 1.27**, this command reported `Healthy` or `Unhealthy` for `scheduler`, `controller-manager`, and `etcd`.

```text
NAME                 STATUS    MESSAGE   ERROR
scheduler            Healthy   ok
controller-manager   Healthy   ok
etcd-0               Healthy   ok
```

On **Kubernetes 1.27 and newer**, `ComponentStatus` is removed; the command may error or be unavailable. Treat that as expected and rely on `kube-system` pods, logs, and health endpoints instead.

### Step 3: API server probes via the aggregated API

These requests go through `kubectl` to the API server’s own health checks:

```bash
kubectl get --raw /healthz
kubectl get --raw /livez
kubectl get --raw /readyz
```

Typical successful body:

```text
ok
```

**What the paths mean (high level):**

- `/healthz` — legacy liveness-style check; often returns `ok` when the process is up.
- `/livez` — indicates the process should not be restarted (live).
- `/readyz` — indicates the API server is ready to accept traffic; failures here often correlate with admission plugins, storage, or etcd connectivity.

If `/readyz` fails, fetch verbose detail (output varies by version):

```bash
kubectl get --raw /readyz?verbose
```

Interpretation guide:

- **Healthy / ok** — the check passed; the API server (for that probe) considers itself operational.
- **Unhealthy / failing checks listed** — use the verbose output and API server logs (Exercise 2) to see which dependency failed (for example etcd, authentication, or admission).

### Step 4: Control plane pods in `kube-system`

```bash
kubectl get pods -n kube-system -o wide
```

Look for static-pod style names (typical on kubeadm):

```text
kube-apiserver-<control-plane-hostname>
kube-controller-manager-<control-plane-hostname>
kube-scheduler-<control-plane-hostname>
etcd-<control-plane-hostname>
```

All should be `Running` with low restart counts. Repeated restarts often point to configuration, certificates, or resource pressure.

### Step 5: Quick sanity on cluster objects

```bash
kubectl get ns
kubectl get pods -A --field-selector=status.phase!=Running --no-headers | head
```

This surfaces obvious cluster-wide issues (many stuck pods) that may be control-plane or workload related.

---

## Exercise 2: API Server Health and Logs

### Step 1: Locate the API server pod

```bash
kubectl get pods -n kube-system | grep apiserver
```

Note the exact pod name (it includes the node name suffix).

### Step 2: Stream recent API server logs

Replace `<apiserver-pod>` with your pod name from Step 1.

```bash
kubectl logs -n kube-system <apiserver-pod> --tail=100
```

For previous container instance after a crash loop:

```bash
kubectl logs -n kube-system <apiserver-pod> --previous --tail=100
```

### Step 3: On the control plane node — systemd unit (if used)

Some environments run the API server as a systemd service instead of only as a static pod. On the control plane node:

```bash
sudo systemctl status kube-apiserver --no-pager
sudo journalctl -u kube-apiserver --since "10 min ago" --no-pager
```

If the unit does not exist, rely on the static pod logs from Step 2.

### Step 4: Map the running container with crictl

On the control plane node:

```bash
sudo crictl ps | grep kube-apiserver
```

Use this to confirm the container ID, image, and that only one healthy instance is running per control plane node.

### Step 5: Read-only scenario — certificate expiry

**Do not intentionally break production clusters.** In exams and real incidents, expired or mismatched TLS material is a common API failure mode.

When client or server certificates for the API server are invalid or expired, typical symptoms include:

- `kubectl` commands fail with TLS or connection errors
- Kubelet on nodes cannot reach the API server; nodes may go `NotReady`
- API server logs mention `x509`, `certificate`, `unknown authority`, or handshake failures

**What you would check (without breaking the lab):**

```bash
# On control plane node — inspect apiserver manifest for cert flags (paths vary)
sudo grep -E 'tls-cert-file|tls-private-key-file|client-ca-file' /etc/kubernetes/manifests/kube-apiserver.yaml
```

```bash
# Example — inspect a certificate's end date (adjust path to your cluster)
sudo openssl x509 -in /etc/kubernetes/pki/apiserver.crt -noout -dates
```

**Recovery pattern (conceptual):** renew control plane certificates with your distribution’s tooling (for example `kubeadm certs renew ...` on kubeadm clusters), restart affected static pods or services, and verify `kubectl get nodes` again.

---

## Exercise 3: Scheduler Troubleshooting

### Step 1: Create a pod that requests impossible CPU

This manifest asks for far more CPU than any single node can satisfy, so the pod stays `Pending`.

```bash
cat <<'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: lab49-too-much-cpu
  labels:
    lab: lab49
spec:
  containers:
  - name: pause
    image: registry.k8s.io/pause:3.9
    resources:
      requests:
        cpu: "999"
EOF
```

```bash
kubectl get pod lab49-too-much-cpu -o wide
```

Expect `Pending` in the `STATUS` column.

### Step 2: Read scheduling events

```bash
kubectl describe pod lab49-too-much-cpu
```

In the **Events** section, look for `FailedScheduling` messages mentioning insufficient CPU or memory.

Example (wording varies by version):

```text
Warning  FailedScheduling  default-scheduler  0/3 nodes are available: 3 Insufficient cpu.
```

### Step 3: Scheduler logs

```bash
kubectl get pods -n kube-system | grep scheduler
```

```bash
# Replace with your scheduler pod name
kubectl logs -n kube-system kube-scheduler-<your-control-plane-node> --tail=80
```

You should see log lines correlating with scheduling attempts and filters.

### Step 4: Pending due to `nodeSelector`

```bash
cat <<'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: lab49-wrong-nodeselector
  labels:
    lab: lab49
spec:
  nodeSelector:
    disktype: ssd
  containers:
  - name: pause
    image: registry.k8s.io/pause:3.9
EOF
```

```bash
kubectl describe pod lab49-wrong-nodeselector
```

Events often state that no nodes match the selector.

### Step 5: Fix by labeling a node

Pick a node name from `kubectl get nodes`:

```bash
kubectl label node <node-name> disktype=ssd
```

```bash
kubectl get pod lab49-wrong-nodeselector -o wide
```

After labels match, the pod should transition to `Running`.

### Step 6: Clean up scheduling exercise pods

```bash
kubectl delete pod lab49-too-much-cpu lab49-wrong-nodeselector --ignore-not-found
kubectl label node <node-name> disktype-
```

---

## Exercise 4: Controller Manager Investigation

### Step 1: Deploy a sample Deployment

```bash
kubectl create deployment lab49-cm-demo --image=registry.k8s.io/nginx-slim:0.21 --replicas=3
```

```bash
kubectl get deploy lab49-cm-demo
kubectl get rs -l app=lab49-cm-demo
kubectl get pods -l app=lab49-cm-demo -o wide
```

### Step 2: Inspect ReplicaSet events

```bash
RS_NAME=$(kubectl get rs -l app=lab49-cm-demo -o jsonpath='{.items[0].metadata.name}')
kubectl describe rs "$RS_NAME"
```

Look for successful replica adoption and pod creation messages.

### Step 3: Scale and watch the controller loop

```bash
kubectl scale deployment lab49-cm-demo --replicas=5
kubectl get rs -l app=lab49-cm-demo
kubectl get pods -l app=lab49-cm-demo
```

ReplicaSets and Pods should converge to five running replicas (assuming cluster capacity).

### Step 4: Controller manager logs

```bash
kubectl get pods -n kube-system | grep controller-manager
```

```bash
kubectl logs -n kube-system kube-controller-manager-<your-control-plane-node> --tail=100
```

**What to expect conceptually:** log lines referencing deployment/replicaset reconciliation, namespace, and sync intervals. When misconfigured, you might see permission errors, client timeouts, or leader-election messages if highly available components conflict.

### Step 5: Remove the demo Deployment

```bash
kubectl delete deployment lab49-cm-demo --ignore-not-found
```

---

## Exercise 5: etcd Health Checks

Perform these steps **on a control plane node** with `etcdctl` available and paths adjusted to your cluster. Kubeadm commonly stores certificates under `/etc/kubernetes/pki/etcd/`.

### Step 1: Point etcdctl at the cluster

```bash
export ETCDCTL_API=3
export ETCDCTL_ENDPOINTS=https://127.0.0.1:2379
export ETCDCTL_CACERT=/etc/kubernetes/pki/etcd/ca.crt
export ETCDCTL_CERT=/etc/kubernetes/pki/etcd/server.crt
export ETCDCTL_KEY=/etc/kubernetes/pki/etcd/server.key
```

If your manifest uses different client cert paths, copy the `--cert-file`, `--key-file`, and `--trusted-ca-file` values from `/etc/kubernetes/manifests/etcd.yaml`.

### Step 2: Endpoint health

```bash
etcdctl endpoint health --cluster
```

Healthy members report `is healthy: true`.

### Step 3: Endpoint status table

```bash
etcdctl endpoint status --cluster -w table
```

Review `RAFT TERM`, `RAFT INDEX`, `DB SIZE`, and whether the leader is elected.

### Step 4: Alarm list

```bash
etcdctl alarm list
```

No output usually means no active alarms. `NOSPACE` alarms occur when the database is full — a classic control-plane outage risk.

### Step 5: Snapshot save and verify

```bash
sudo etcdctl snapshot save /tmp/etcd-test-backup.db
sudo etcdctl snapshot status /tmp/etcd-test-backup.db -w table
```

Example status fields:

```text
Hash      Revision  Total Keys  ...
abcdef01  12345     6789        ...
```

### Step 6: Remove test snapshot (optional)

```bash
sudo rm -f /tmp/etcd-test-backup.db
```

---

## Exercise 6: Component Log Analysis

### Step 1: Collect control plane pod logs

Replace pod names with those from your cluster.

```bash
APISERVER=$(kubectl get pod -n kube-system -l component=kube-apiserver -o jsonpath='{.items[0].metadata.name}')
SCHEDULER=$(kubectl get pod -n kube-system -l component=kube-scheduler -o jsonpath='{.items[0].metadata.name}')
CONTROLLER=$(kubectl get pod -n kube-system -l component=kube-controller-manager -o jsonpath='{.items[0].metadata.name}')
ETCD=$(kubectl get pod -n kube-system -l component=etcd -o jsonpath='{.items[0].metadata.name}')

kubectl logs -n kube-system "$APISERVER" --tail=50
kubectl logs -n kube-system "$SCHEDULER" --tail=50
kubectl logs -n kube-system "$CONTROLLER" --tail=50
kubectl logs -n kube-system "$ETCD" --tail=50
```

If a label selector returns empty, fall back to `grep` from Exercise 2.

### Step 2: Search for error patterns in logs

```bash
kubectl logs -n kube-system "$APISERVER" --tail=500 | grep -i error
kubectl logs -n kube-system "$ETCD" --tail=500 | grep -i error
```

Treat benign startup lines carefully; focus on repeating errors, stack traces, and etcd timeouts.

### Step 3: Kubelet journal on the node

On the node where workloads fail or control plane pods run:

```bash
sudo journalctl -u kubelet --since "30 min ago" | grep -i error
```

Kubelet errors often explain sandbox, CNI, image pull, or API connectivity issues that look like control plane problems from a user’s perspective.

### Step 4: Files under `/var/log/pods`

On a node:

```bash
sudo ls -la /var/log/pods/ | head
sudo find /var/log/pods -maxdepth 3 -type d | head
```

Each pod UID directory contains per-container log files mirrored from the container runtime. This is useful when `kubectl logs` is unavailable (for example API down) but node disk access remains.

### Step 5: Ordered events in `kube-system`

```bash
kubectl get events -n kube-system --sort-by='.lastTimestamp' | tail -n 30
```

Use this timeline to correlate static pod restarts, image pulls, and mount failures.

---

## Exercise 7: Simulated Break-Fix (Intermediate)

You will create a namespace, apply a **too-strict** `ResourceQuota`, deploy an app that exceeds the quota, diagnose with events and descriptions, then fix the quota.

### Step 1: Create namespace and restrictive quota

```bash
kubectl create namespace lab49-quota
```

```bash
cat <<'EOF' | kubectl apply -f -
apiVersion: v1
kind: ResourceQuota
metadata:
  name: lab49-restrictive
  namespace: lab49-quota
spec:
  hard:
    pods: "1"
    requests.cpu: "100m"
    requests.memory: "128Mi"
EOF
```

### Step 2: Attempt a Deployment that violates the quota

```bash
kubectl create deployment lab49-quota-demo --image=registry.k8s.io/nginx-slim:0.21 --replicas=3 -n lab49-quota
```

```bash
kubectl get pods -n lab49-quota
kubectl get rs -n lab49-quota
kubectl describe deployment lab49-quota-demo -n lab49-quota
```

Expect only one pod at most, or `ReplicaSet` / pod creation blocked with quota messages.

### Step 3: Diagnose with events

```bash
kubectl get events -n lab49-quota --sort-by='.lastTimestamp'
```

```bash
kubectl describe resourcequota lab49-restrictive -n lab49-quota
```

Example event text (paraphrased):

```text
Error creating: pods "lab49-quota-demo-..." is forbidden: exceeded quota: lab49-restrictive, requested: pods=1, used: pods=1, limited: pods=1
```

### Step 4: Correlate with controller manager (optional)

While the failure is enforced at admission, the deployment controller still tries to create pods. Controller manager and scheduler logs (Exercises 3–4) help when multiple admission plugins interact.

```bash
kubectl logs -n kube-system kube-controller-manager-<your-control-plane-node> --tail=50 | grep -i lab49-quota || true
```

### Step 5: Fix the ResourceQuota

```bash
kubectl patch resourcequota lab49-restrictive -n lab49-quota --type merge -p '
spec:
  hard:
    pods: "10"
    requests.cpu: "2"
    requests.memory: "512Mi"
'
```

```bash
kubectl get resourcequota -n lab49-quota
```

### Step 6: Verify the Deployment recovers

```bash
kubectl rollout status deployment/lab49-quota-demo -n lab49-quota
kubectl get pods -n lab49-quota -o wide
```

You should see three running pods once quota allows.

### Step 7: Cleanup namespace

```bash
kubectl delete namespace lab49-quota --wait=true
```

---

## Key Takeaways

- Cluster health starts with **nodes**, **`kube-system` pods**, and **`/readyz` / `/livez`** — not a single magic command.
- **`Pending` pods** are often scheduler or constraint issues (`resources`, `nodeSelector`, taints, PVCs); `describe pod` is the fastest narrative.
- **Deployments** converge through the **controller manager** and **ReplicaSets**; scaling issues show up in ReplicaSet events and controller logs.
- **etcd** is the data store for the API; `etcdctl endpoint health` and **snapshots** validate backup posture from Lab 07.
- **Logs live in three places**: `kubectl logs`, **`journalctl`** on the node, and **`/var/log/pods`** on disk.
- **Admission and quotas** can mimic control plane outages; always read **events** in the affected namespace.

## Troubleshooting Tips

- **Label selectors for system pods differ by install method.** If `-l component=kube-apiserver` is empty, use `kubectl get pods -n kube-system | grep apiserver`.
- **`componentstatuses` is gone on modern clusters** — do not assume it will exist in exam or production.
- **Wrong etcd certificates** produce TLS errors in `etcdctl`; copy paths exactly from the static pod manifest.
- **High restart counts** on static pods often mean manifest typos, bad mounts, or expired certs — check `describe pod` and the manifest file.
- **grep on logs** can hide JSON structured lines; increase `--tail` or use your cluster’s log stack when available.
- **ResourceQuota** failures appear at pod creation time — look for `forbidden: exceeded quota` in events.

## Cleanup

Remove lab objects if any remain:

```bash
kubectl delete pod lab49-too-much-cpu lab49-wrong-nodeselector --ignore-not-found
kubectl delete deployment lab49-cm-demo --ignore-not-found
kubectl delete namespace lab49-quota --ignore-not-found
# If you labeled a node for Exercise 3:
# kubectl label node <node-name> disktype-
```

## Next Steps

- Continue the troubleshooting series with **Lab 50: Pod Failures** and **Lab 51: Kubelet and Node** (when available in this course path).
- For interactive review, open the companion page: [`../html/ts-control-plane.html`](../html/ts-control-plane.html).
- Deepen etcd operations with **Lab 07: ETCD Backup and Restore**.
- For scheduling fundamentals, review **Lab 17: nodeSelector** and **Lab 18: Affinity**.
