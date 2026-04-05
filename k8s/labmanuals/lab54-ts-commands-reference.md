# Lab 54: Troubleshooting Commands Practice (Reference Lab)

## Exercise index

| # | Topic | Jump |
|---|--------|------|
| 1 | [Cluster health](#ex1) | `cluster-info`, nodes, healthz, metrics, events |
| 2 | [Pod debugging](#ex2) | `describe`, `logs`, `exec`, `port-forward`, `cp`, `debug` |
| 3 | [Node debugging](#ex3) | `describe node`, cordon/drain, kubelet, `crictl` |
| 4 | [Networking](#ex4) | Services, Endpoints, DNS, NetworkPolicy, Ingress, CoreDNS |
| 5 | [Storage](#ex5) | PV, PVC, StorageClass, mount checks |
| 6 | [RBAC](#ex6) | `auth can-i`, ClusterRoles, bindings |
| 7 | [etcd](#ex7) | `etcdctl` health, status, snapshots, alarms |
| 8 | [Logs and events](#ex8) | Pod logs, node journals, events, log paths |

---

## Overview

This lab is a **guided practice sheet** for the Kubernetes troubleshooting command set you will use daily and on exams. You will run commands in eight categories—cluster health, pod debugging, node inspection, networking, storage, RBAC, etcd, and logs/events—and learn what “good” output looks like versus signals that warrant deeper investigation.

Work through the exercises in order the first time; afterward, keep this manual as a **checklist** when incidents strike.

**Level:** beginner to intermediate.

**Companion (interactive):** [Troubleshooting commands reference — HTML](../html/ts-commands-reference.html)

---

## Prerequisites

- A running Kubernetes cluster (Kind, Minikube, kubeadm, or a managed control plane).
- `kubectl` configured and able to run read-only commands against the cluster.
- **Metrics Server** installed if you want `kubectl top` to return data (see [Lab 36: Metrics Server](lab36-observe-metrics-server.md)); without it, `top` may show “Metrics API not available.”
- For **node SSH** and **crictl** sections: SSH to a worker or control plane node with sufficient privileges (lab exercises use read-only commands where possible).
- For **etcd** commands: access to a control plane node with `etcdctl` and the cluster’s etcd TLS assets (typical on kubeadm clusters). On managed Kubernetes you may not have etcd access; skip or use a self-managed lab cluster.
- Optional prior reading: [Lab 03: kubectl essentials](lab03-basics-kubectl-essentials.md), [Lab 49: Control plane troubleshooting](lab49-ts-cluster-control-plane.md).

---

## Learning Objectives

By the end of this lab, you should be able to:

- Run core **cluster health** probes and interpret node and API signals.
- Use **pod-level** tools (`describe`, `logs`, `exec`, `port-forward`, `cp`, `debug`) in a safe, methodical order.
- Inspect **nodes** with kubectl and, where permitted, kubelet/container runtime tools.
- Trace **Service → Endpoints → DNS** problems and spot NetworkPolicy/Ingress gaps.
- Verify **PV/PVC/StorageClass** binding and in-pod mounts.
- Check **RBAC** with `kubectl auth can-i` and inspect high-privilege bindings.
- Use **etcdctl** (v3 API) for endpoint health, status, snapshots, and alarms.
- Correlate **logs and Events** across kubectl, kubelet, and node filesystem paths.

---

<a id="ex1"></a>
## Exercise 1: Cluster Health Commands

Run each command below. For every one, note **what “healthy” looks like** and **what should trigger follow-up**.

### `kubectl cluster-info`

```bash
kubectl cluster-info
```

**Expected:** Lines showing the Kubernetes control plane URL and (usually) CoreDNS via the API proxy. Failures here point to kubeconfig, network, or API reachability—not app YAML.

### `kubectl get nodes -o wide`

```bash
kubectl get nodes -o wide
```

**Expected:** `STATUS` `Ready`, valid `INTERNAL-IP`, and a `CONTAINER-RUNTIME` string. `NotReady` or missing IP suggests kubelet, CNI, or node-level failure.

### `kubectl get componentstatuses` (legacy)

```bash
kubectl get componentstatuses
# short alias (same resource):
kubectl get cs
```

**Historical (pre-1.27):** rows for `scheduler`, `controller-manager`, `etcd-*` with `STATUS Healthy`. **`ComponentStatus` was removed in Kubernetes 1.27**—errors or empty results on newer clusters are expected; use `kube-system` pods, `/readyz`, and logs ([Lab 49](lab49-ts-cluster-control-plane.md)).

### API server health: `/healthz`, `/livez`, `/readyz`

```bash
kubectl get --raw /healthz
kubectl get --raw /livez
kubectl get --raw /readyz
```

**Expected:** Body `ok` for each path. If `/readyz` fails, add verbose output (shape varies by version):

```bash
kubectl get --raw '/readyz?verbose'
```

| Path | Meaning |
|------|---------|
| `/healthz` | Legacy liveness-style check. |
| `/livez` | Process should stay up (not restarted). |
| `/readyz` | API ready for traffic; failures often involve etcd, admission, or auth. |

### `kubectl top nodes`

```bash
kubectl top nodes
```

**Expected (with Metrics Server):** per-node CPU/memory columns. Hot nodes or missing metrics API → capacity issues or install/repair Metrics Server ([Lab 36](lab36-observe-metrics-server.md)).

### Cluster-wide events (sorted)

```bash
kubectl get events -A --sort-by='.lastTimestamp' | tail -n 30
```

**What to look for:** Recent `Warning` events, `FailedScheduling`, `FailedMount`, `Unhealthy`, image pull failures. The tail keeps the noise manageable; widen the window when chasing an incident.

---

<a id="ex2"></a>
## Exercise 2: Pod Debugging Commands

### Step 0: Deploy a small test workload

Use a predictable namespace (default is fine for a lab).

```bash
kubectl create deployment ts-debug --image=nginx:1.25-alpine --replicas=1
kubectl rollout status deployment/ts-debug
kubectl get pods -l app=ts-debug -o wide
```

Record the pod name as `POD` for the rest of this exercise:

```bash
POD=$(kubectl get pod -l app=ts-debug -o jsonpath='{.items[0].metadata.name}')
echo "$POD"
```

### `kubectl get pods -o wide`

```bash
kubectl get pods -o wide
kubectl get pods -l app=ts-debug -o wide
```

**What to look for:** `READY` matches containers, `STATUS` is `Running` (or intentional phases for Jobs), `NODE` assigned for scheduled pods, correct `IP`.

### `kubectl describe pod`

```bash
kubectl describe pod "$POD"
```

**What to look for (sections):**

- **Events** at the bottom—often the fastest answer for image pulls, mounts, probes, and scheduling.
- **Conditions**—`PodReadyToStartContainers`, `Initialized`, `Ready`, `ContainersReady`.
- **Limits/requests** if you suspect CPU/memory pressure.

### `kubectl logs`

```bash
# Current container stdout/stderr
kubectl logs "$POD"

# Follow (Ctrl+C to stop)
kubectl logs -f "$POD"

# Last N lines
kubectl logs "$POD" --tail=50

# Since a duration
kubectl logs "$POD" --since=10m

# Previous instance (after crash/restart)
kubectl logs "$POD" --previous
```

**What to look for:** Crash loops (`Exit Code`), stack traces, “connection refused” to dependencies. `--previous` is essential when the pod restarted and the current container has little log history.

### Multi-container pods: `-c`

If you add a sidecar later, target the container name explicitly:

```bash
kubectl logs "$POD" -c <container-name>
```

### `kubectl exec` (shell and environment)

```bash
# Interactive shell (image must have a shell; nginx alpine has /bin/sh)
kubectl exec -it "$POD" -- /bin/sh

# Non-interactive: dump environment inside the container
kubectl exec "$POD" -- env | sort | head
```

**What to look for:** Wrong env vars, missing files, DNS resolution behavior from *inside* the network namespace.

### `kubectl port-forward`

```bash
# Terminal A
kubectl port-forward "pod/$POD" 8080:80
# Terminal B (or browser)
curl -sS http://127.0.0.1:8080/ | head
```

**Purpose:** Reach the container directly—separates app bugs from Service/Ingress/DNS.

### `kubectl cp`

```bash
kubectl cp "$POD":/etc/hostname ./hostname-from-pod.txt
cat ./hostname-from-pod.txt
```

**What to look for:** File appears locally; confirms readable filesystem paths and permissions for debugging.

### `kubectl debug` (ephemeral debug container)

Requires **ephemeral containers** (Kubernetes 1.23+; some distros need feature enablement). Single-container pod:

```bash
kubectl debug "$POD" -it --image=busybox:1.36
```

Multi-container pod: add `--target=<container-name>`. If the API rejects the call, use the debug pod pattern in Exercise 4.

---

<a id="ex3"></a>
## Exercise 3: Node Debugging Commands

Pick a node name from `kubectl get nodes`:

```bash
NODE=$(kubectl get nodes -o jsonpath='{.items[0].metadata.name}')
echo "$NODE"
```

### `kubectl describe node`

```bash
kubectl describe node "$NODE"
```

**What to look for:**

- **Conditions:** `Ready`, `MemoryPressure`, `DiskPressure`, `PIDPressure`, `NetworkUnavailable`.
- **Allocated resources** vs capacity.
- **Events** at the bottom (often kubelet or runtime messages).

### `kubectl top node`

```bash
kubectl top node
```

Same metrics story as Exercise 1—requires Metrics Server.

### Cordon and uncordon

**Cordon** prevents *new* pods from scheduling onto the node (existing pods keep running):

```bash
kubectl cordon "$NODE"
kubectl get node "$NODE"
```

Expect `SchedulingDisabled` in the `STATUS` column or a `spec.unschedulable` taint depending on version/output.

**Uncordon** restores scheduling:

```bash
kubectl uncordon "$NODE"
kubectl get node "$NODE"
```

### `kubectl drain` (explain before you run)

Drain evicts workloads from the node so you can maintain or decommission it.

```bash
# Example only — do NOT run on your only node in a single-node lab without planning
# kubectl drain "$NODE" --ignore-daemonsets --delete-emptydir-data
```

**Flags (conceptual):**

| Flag | Why it matters |
|------|----------------|
| `--ignore-daemonsets` | DaemonSet pods are not evicted; required on most clusters because DS pods exist on every node. |
| `--delete-emptydir-data` | Allows eviction of pods using `emptyDir` (data loss warning). |

**When to use:** Node upgrades, hardware repair, shrinking a node pool. Always ensure capacity elsewhere before draining production nodes.

### On the node: kubelet and journal

SSH to the node (paths and units may vary slightly by OS):

```bash
sudo systemctl status kubelet
sudo journalctl -u kubelet -n 100 --no-pager
```

**What to look for:** Crash loops, certificate errors, cgroup/driver errors, PLEG issues, repeated sync failures.

### `crictl` (containerd/CRI)

```bash
sudo crictl ps
sudo crictl pods
```

Pick a running container ID from `crictl ps`:

```bash
CID=<container-id-from-crictl-ps>
sudo crictl logs "$CID" | tail -n 50
sudo crictl inspect "$CID" | head -n 40
sudo crictl images | head
```

**What to look for:** Image pull errors, OOM kills, sandbox issues—often the ground truth below kubectl.

---

<a id="ex4"></a>
## Exercise 4: Networking Commands

### Services and Endpoints

```bash
kubectl get svc -A -o wide
kubectl get svc -n default -o wide
```

Pick a Service that should have backends (replace names as needed):

```bash
kubectl get endpoints <svc-name> -n <namespace>
# modern alias (Kubernetes 1.22+): EndpointSlices
kubectl get endpointslices -n <namespace>
```

**What to look for:** Endpoints (or slices) list **pod IPs and ports**. Empty endpoints + `Running` pods usually means **selector mismatch** or **readiness** failing.

### DNS test from a debug pod

Create a long-lived debug pod if you do not already have one:

```bash
kubectl run net-debug --image=busybox:1.36 --restart=Never --command -- sleep 3600
kubectl wait --for=condition=Ready pod/net-debug --timeout=60s
```

Test DNS (adjust the name and namespace to match a real Service):

```bash
kubectl exec -it net-debug -- nslookup kubernetes.default.svc.cluster.local
kubectl exec -it net-debug -- nslookup <svc-name>.<namespace>.svc.cluster.local
```

**What to look for:** `Name:` and `Address:` lines. `NXDOMAIN` or timeouts point to CoreDNS, upstream DNS, or NetworkPolicy blocks.

### Policies and Ingress

```bash
kubectl get networkpolicy -A
kubectl get ingress -A
```

**What to look for:** Unexpected default-deny policies, missing ingress class, wrong host/rules.

### CoreDNS logs

```bash
kubectl logs -n kube-system -l k8s-app=kube-dns --tail=50
# If the label differs: kubectl get pods -n kube-system | grep -i dns
# then: kubectl logs -n kube-system <coredns-pod-name> --tail=50
```

**What to look for:** Loop detection, upstream timeouts, OOM, plugin errors.

---

<a id="ex5"></a>
## Exercise 5: Storage Commands

### Create a simple PV and PVC (hostPath for lab clusters)

> **Warning:** `hostPath` binds data to a node—OK for Kind/Minikube-style learning, not for production.

```bash
cat <<'EOF' | kubectl apply -f -
apiVersion: v1
kind: PersistentVolume
metadata:
  name: ts-pv-lab54
spec:
  capacity: { storage: 1Gi }
  accessModes: [ReadWriteOnce]
  persistentVolumeReclaimPolicy: Retain
  storageClassName: manual-lab54
  hostPath: { path: /tmp/k8s-lab54-pv, type: DirectoryOrCreate }
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: ts-pvc-lab54
spec:
  accessModes: [ReadWriteOnce]
  storageClassName: manual-lab54
  resources: { requests: { storage: 1Gi } }
---
apiVersion: v1
kind: Pod
metadata:
  name: ts-vol-debug
spec:
  containers:
    - name: app
      image: busybox:1.36
      command: ["sleep", "3600"]
      volumeMounts: [{ name: data, mountPath: /data }]
  volumes:
    - name: data
      persistentVolumeClaim: { claimName: ts-pvc-lab54 }
EOF
kubectl wait --for=condition=Ready pod/ts-vol-debug --timeout=120s
```

### List and describe storage objects

```bash
kubectl get pv
kubectl get pvc
kubectl describe pv ts-pv-lab54
kubectl describe pvc ts-pvc-lab54
kubectl get storageclass
```

**What to look for:** PVC `STATUS` is `Bound`; PV `STATUS` is `Bound`; `CLAIM` shows the PVC; events on describe explain provisioning failures.

### Mount debugging inside the pod

```bash
kubectl exec -it ts-vol-debug -- df -h
kubectl exec -it ts-vol-debug -- ls -la /data
```

**What to look for:** Expected filesystem size, mount at `/data`, permission errors.

---

<a id="ex6"></a>
## Exercise 6: RBAC Commands

### Check permissions for the current context

```bash
kubectl auth can-i create pods
kubectl auth can-i create pods --namespace=default
```

**Expected:** `yes` or `no` on stdout.

### Impersonate a ServiceAccount

```bash
kubectl auth can-i create pods --as=system:serviceaccount:default:default
kubectl auth can-i list secrets --as=system:serviceaccount:default:default -n default
```

**What to look for:** Principle of least privilege—unexpected `yes` on sensitive verbs is a risk.

### List all permissions for the current user

```bash
kubectl auth can-i --list
kubectl auth can-i --list --namespace=kube-system
```

**What to look for:** Broad wildcard rules (`*`) or `cluster-admin`-like coverage for non-admin users.

### Inspect cluster roles and bindings (sample)

```bash
kubectl get clusterroles | head -20
kubectl get clusterrolebindings | head -20
kubectl describe clusterrolebinding cluster-admin
```

**What to look for:** Who is bound to `cluster-admin`, and whether bindings are justified.

---

<a id="ex7"></a>
## Exercise 7: etcd Commands

On a **kubeadm** control plane node, etcd uses TLS. Verify paths on your node (often under `/etc/kubernetes/pki/etcd/`). **Managed clusters** usually hide etcd—use the provider’s backup story instead.

```bash
export ETCDCTL_API=3
EP=https://127.0.0.1:2379
CA=/etc/kubernetes/pki/etcd/ca.crt
CERT=/etc/kubernetes/pki/etcd/server.crt
KEY=/etc/kubernetes/pki/etcd/server.key

# Read-only: member health (expect "healthy" / committed proposal latency)
sudo etcdctl endpoint health --endpoints="$EP" --cacert="$CA" --cert="$CERT" --key="$KEY"

# Table: leader, db size, version (compare members in HA)
sudo etcdctl endpoint status -w table --endpoints="$EP" --cacert="$CA" --cert="$CERT" --key="$KEY"

# Backup drill + integrity (non-zero size / revision in status output)
sudo etcdctl snapshot save /tmp/etcd-practice.db \
  --endpoints="$EP" --cacert="$CA" --cert="$CERT" --key="$KEY"
sudo etcdctl snapshot status /tmp/etcd-practice.db -w table

# Alarms (e.g. NOSPACE → disk / defrag / ops)
sudo etcdctl alarm list --endpoints="$EP" --cacert="$CA" --cert="$CERT" --key="$KEY"
```

---

<a id="ex8"></a>
## Exercise 8: Logs and Events Commands

If `$POD` from Exercise 2 is unset, pick any Running pod:  
`POD=$(kubectl get pod -o jsonpath='{.items[0].metadata.name}')`

### Pod logs (tail)

```bash
kubectl logs "$POD" --tail=50
```

### Control plane or add-on component logs

Replace with a real pod name from `kube-system`:

```bash
kubectl get pods -n kube-system
kubectl logs -n kube-system <component-pod-name> --tail=80
```

**Examples of what you might inspect:** `kube-apiserver-*`, `kube-scheduler-*`, `etcd-*`, CNI pods, CSI pods—match the symptom.

### Node journals (SSH)

```bash
sudo journalctl -u kubelet -n 100 --no-pager
sudo journalctl -u containerd -n 100 --no-pager
# if your node uses docker instead of containerd:
# sudo journalctl -u docker -n 100 --no-pager
```

### Events via kubectl

```bash
kubectl get events -A --sort-by='.metadata.creationTimestamp' | tail -n 40
kubectl get events -A --field-selector type=Warning --sort-by='.metadata.creationTimestamp' | tail -n 40
```

**What to look for:** Warnings concentrated in one namespace, repeated `Backoff`, `FailedMount`, `Unhealthy`.

### Log file locations (node filesystem)

On the node, kubelet keeps pod logs under well-known paths:

```bash
sudo ls /var/log/pods | head
sudo ls /var/log/containers | head
```

**What to look for:** Missing log files can indicate log rotation misconfiguration or pods that never started.

---

## Quick reference table

| Command | Purpose | When to use |
|---------|---------|-------------|
| `kubectl cluster-info` | Show API and CoreDNS proxy endpoints | First connectivity check |
| `kubectl get nodes -o wide` | Node readiness, IPs, runtime | Scheduling / node incidents |
| `kubectl get cs` | Legacy component status | Only on older clusters; know deprecation |
| `kubectl get --raw /readyz` | API server readiness | API latency/errors |
| `kubectl top nodes` | CPU/memory usage | Capacity, hot nodes (needs metrics) |
| `kubectl get events -A` | Recent warnings | Fast incident triage |
| `kubectl describe pod` | Pod spec + **Events** | Image pull, mount, probe failures |
| `kubectl logs` / `--previous` | Container logs | Crash loops, app errors |
| `kubectl exec` | Run commands in container | In-container DNS, files, binaries |
| `kubectl port-forward` | Local tunnel to Pod/Service | Isolate app vs Service mesh/Ingress |
| `kubectl cp` | Copy files to/from container | Grab configs, heap dumps, small artifacts |
| `kubectl debug` | Ephemeral debug container | Deep inspection without new image |
| `kubectl describe node` | Capacity, conditions, taints | Node NotReady, pressure |
| `kubectl cordon` / `uncordon` | Stop/start scheduling | Maintenance windows |
| `kubectl drain` | Evict workloads safely | Node drain before upgrade |
| `systemctl` / `journalctl` (kubelet) | Node-level service health | Below-kubectl failures |
| `crictl ps/logs/inspect` | CRI-level truth | Runtime/Image/Sandbox issues |
| `kubectl get svc` / `get endpoints` | Service routing chain | “Service has no endpoints” |
| `kubectl exec … nslookup` | Cluster DNS from pod | CoreDNS/policy/DNS issues |
| `kubectl get networkpolicy` | Policy inventory | Unexpected traffic blocks |
| `kubectl get pv,pvc,sc` | Storage chain | Bound vs Pending claims |
| `kubectl auth can-i` | RBAC check | Access denied mysteries |
| `etcdctl endpoint health/status` | etcd cluster health | API/etcd correlation |
| `etcdctl snapshot save/status` | Backup verification | DR drills |
| `etcdctl alarm list` | etcd alarms | Quota/disk emergencies |

---

## Key Takeaways

- **Order matters:** cluster → node → workload → network → storage → auth → data plane logs; skipping steps creates red herrings.
- **`describe` Events** and **`kubectl get events`** often beat log tailing for the first five minutes of triage.
- **`endpoints` empty** is a structural routing problem before you blame the app.
- **`kubectl auth can-i --list`** is the fastest way to understand “what this credential can do.”
- **etcd** tools are powerful and sensitive—treat snapshots and certificates as production-grade secrets.

---

## Troubleshooting Tips

- **`kubectl top` errors:** Install/repair Metrics Server; wait a few minutes after install for first metrics.
- **`componentstatuses` fails:** Expected on Kubernetes 1.27+; pivot to `kube-system` pods and `/readyz`.
- **`kubectl debug` fails:** Check version, feature gates, and whether the pod’s namespace allows ephemeral containers.
- **`crictl` permission errors:** Use `sudo` or join the right group per your Linux image.
- **DNS works from cluster but not from host:** Normal—test from a pod, not your laptop.
- **etcd TLS errors:** Wrong cert/key pair or wrong `endpoints`—compare with static pod manifest under `/etc/kubernetes/manifests/etcd.yaml`.

---

## Cleanup

Remove lab objects created in this manual (ignore errors if you skipped an exercise):

```bash
kubectl delete deployment ts-debug --ignore-not-found
kubectl delete pod net-debug ts-vol-debug --ignore-not-found
kubectl delete pvc ts-pvc-lab54 --ignore-not-found
kubectl delete pv ts-pv-lab54 --ignore-not-found
rm -f ./hostname-from-pod.txt
sudo rm -f /tmp/etcd-practice.db
```

If you cordoned a node for practice, **uncordon** it:

```bash
kubectl uncordon "$NODE" 2>/dev/null || true
```

---

## Next Steps

- **Other troubleshooting labs (markdown):** [Lab 49 — Control plane](lab49-ts-cluster-control-plane.md) · [Lab 50 — Pod failures](lab50-ts-pod-failures.md)
- **Interactive HTML:** [ts-control-plane](../html/ts-control-plane.html) · [ts-pod-failures](../html/ts-pod-failures.html) · [ts-kubelet-node](../html/ts-kubelet-node.html) · [ts-networking](../html/ts-networking.html) · [ts-application-debugging](../html/ts-application-debugging.html) · [ts-cka-scenarios](../html/ts-cka-scenarios.html) · [ts-commands-reference](../html/ts-commands-reference.html) (this lab)
- **Related depth:** [Lab 03 — kubectl](lab03-basics-kubectl-essentials.md) · [Lab 07 — etcd backup](lab07-cluster-etcd-backup-restore.md) · [Lab 11 — RBAC](lab11-sec-rbac-security.md) · [Lab 39 — Storage](lab39-storage-persistent-storage.md) · [Lab 45 — DNS](lab45-net-dns-configuration.md)
