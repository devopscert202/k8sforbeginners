# Lab 51: Kubelet and Node Troubleshooting

## Overview

This lab focuses on **node-level** reliability: how the **kubelet** reports health to the control plane, how **container runtimes** (commonly **containerd**) interact with the kubelet, and how **resource pressure** triggers **evictions** and **NotReady** conditions. You will practice read-only inspection commands from `kubectl`, then correlate them with **SSH** checks on a worker node—`systemd` units, `journalctl`, and `crictl`. You will also walk through a safe mental model for **node join** issues using `kubeadm` tokens and connectivity tests.

**Level:** beginner to intermediate.  
**Companion:** interactive HTML walkthrough — [`../html/ts-kubelet-node.html`](../html/ts-kubelet-node.html).

---

## Exercise index

| # | Topic | Jump |
|---|--------|------|
| 1 | Node health check basics | [Exercise 1](#ex1) |
| 2 | Investigating Node `NotReady` | [Exercise 2](#ex2) |
| 3 | Kubelet log analysis | [Exercise 3](#ex3) |
| 4 | Container runtime troubleshooting | [Exercise 4](#ex4) |
| 5 | Resource pressure scenarios | [Exercise 5](#ex5) |
| 6 | Node join / rejoin | [Exercise 6](#ex6) |

---

## Prerequisites

- A running Kubernetes cluster; **kubeadm**-style nodes are ideal so you can SSH to a worker and use `systemctl`, `journalctl`, and `/var/lib/kubelet/`.
- `kubectl` configured with permission to **describe nodes** and (for metrics) read **Metrics API** objects.
- **SSH** access to at least one **worker node** (or a single-node cluster where you have shell access).
- **Metrics Server** installed if you want `kubectl top node` to work (see [Lab 36: Metrics Server](lab36-observe-metrics-server.md)).
- Prior context from [Lab 49: Cluster and Control Plane Troubleshooting](lab49-ts-cluster-control-plane.md) helps you separate **control-plane** symptoms from **node/kubelet** symptoms.
- Optional: `sudo` on nodes for service restarts and reading protected paths.

## Learning Objectives

By the end of this lab, you will be able to:

- Interpret **node conditions** (`Ready`, `MemoryPressure`, `DiskPressure`, `PIDPressure`) from `kubectl describe node`.
- Correlate **API-reported heartbeats** with **kubelet** and **container runtime** health on the node.
- Use **`journalctl`** to tail and filter kubelet logs; locate **kubelet configuration** on disk.
- Inspect workloads with **`crictl`** against **containerd** (or a CRI-compatible runtime).
- Explain **eviction order** by **QoS class** under pressure and use basic **disk/memory/PID** checks.
- Diagnose **join** failures with **tokens**, **port connectivity**, and (when appropriate) **`kubeadm reset`** plus a fresh join.

---

<a id="ex1"></a>

## Exercise 1: Node Health Check Basics

The control plane learns node health primarily from the **kubelet**, which updates **Node** status conditions on a regular cadence. Start every node investigation from **`kubectl`**, then drill into the node OS only when conditions or events point there.

### Step 1: List nodes with extra columns

```bash
kubectl get nodes -o wide
```

**What to notice:**

- **`STATUS`** — should be `Ready` for schedulable, healthy nodes.
- **`INTERNAL-IP` / `EXTERNAL-IP`** — how control plane and other nodes reach this kubelet.
- **`VERSION`** — kubelet/API reporting version (useful during upgrades).

Example (illustrative):

```text
NAME           STATUS   ROLES           AGE   VERSION   INTERNAL-IP    OS-IMAGE
worker-1       Ready    <none>          10d   v1.30.2   10.0.0.21      Ubuntu 22.04.4 LTS
```

### Step 2: Describe one node — Conditions and capacity

Pick a node name from the previous output and run:

```bash
kubectl describe node <node-name>
```

Scroll to **Conditions**. Typical rows:

| Type | Meaning (short) |
|------|------------------|
| **Ready** | `True` means kubelet is healthy enough to run pods; `False` often means kubelet/runtime/network problems. |
| **MemoryPressure** | `True` — kubelet sees memory pressure; may evict pods. |
| **DiskPressure** | `True` — filesystem pressure on key paths; may evict pods. |
| **PIDPressure** | `True` — too many processes; scheduling/evictions may follow. |
| **NetworkUnavailable** | Some network plugins set this during setup; persistent `True` can block readiness. |

Also read **LastHeartbeatTime** and **LastTransitionTime**:

- A **stale** heartbeat (long gap versus peers) suggests the kubelet stopped updating status—often process down, network partition, or kubelet unable to reach API.

### Step 3: Capacity, allocatable, and allocated resources

In the same `describe` output, find:

- **Capacity** — physical/logical resources the node advertises.
- **Allocatable** — what is left for user pods after **system reserved** and **kube reserved** carve-outs.
- **Allocated resources** — sum of **requests** on that node (not the same as actual usage).

Quick numeric view of requests/limits per node:

```bash
kubectl describe node <node-name> | sed -n '/Allocated resources:/,/Events:/p'
```

**Key idea:** `Allocated resources` shows **scheduling pressure** (requests), while **actual** usage needs metrics (next step) or node-level tools.

### Step 4: Node resource usage with Metrics Server

If Metrics Server is healthy:

```bash
kubectl top node
```

Example:

```text
NAME       CPU(cores)   CPU%   MEMORY(bytes)   MEMORY%
worker-1   120m         6%     1800Mi          23%
```

Compare **`kubectl top`** to **requests** from `describe`. A node can look “fine” on CPU **requests** yet run hot on **actual** CPU, or vice versa.

### Step 5: Optional — JSON path for condition sanity check

```bash
kubectl get node <node-name> -o jsonpath='{range .status.conditions[*]}{.type}{"\t"}{.status}{"\t"}{.lastHeartbeatTime}{"\n"}{end}'
```

Use this in scripts or when sharing a concise status snapshot in tickets.

---

<a id="ex2"></a>

## Exercise 2: Investigating Node NotReady

`NotReady` is a **symptom**, not a single root cause. The kubelet sets **Ready=False** when it cannot satisfy node health rules—commonly:

1. **Kubelet not running** or crash-looping.
2. **Container runtime** (e.g. **containerd**) down or not reachable via the CRI socket.
3. **Network** path from node to API server broken (firewall, wrong VIP, bad routes, clock skew).
4. **CNI** not fully wiring node network; some installs surface this as readiness issues.

### Part A — From the control plane: `describe node`

```bash
kubectl get nodes
kubectl describe node <not-ready-node-name>
```

Focus on:

- **Conditions** — `Ready` reason/message (Kubernetes version-dependent wording).
- **Events** at the bottom — registration, PLEG errors, eviction, etc.

If **LastHeartbeatTime** for `Ready` or `NodeReady` is old while the machine is up, suspect kubelet ↔ API connectivity or a stopped kubelet.

### Part B — SSH to the node: systemd and runtime

```bash
ssh <user>@<node-ip>
```

Check kubelet:

```bash
sudo systemctl status kubelet
```

Healthy units usually show **active (running)**. Note **Main PID**, **since**, and whether **restart counters** climb.

Check containerd (typical kubeadm + containerd stack):

```bash
sudo systemctl status containerd
```

If either service is **failed** or **inactive**, the API will often eventually mark the node **NotReady**.

### Part C — Kubelet logs (last 10 minutes)

```bash
sudo journalctl -u kubelet --since "10 min ago" --no-pager
```

Look for recurring errors such as:

- CRI / **dial unix** socket errors (runtime not listening).
- **certificate** or **authorization** errors talking to API.
- **PLEG** (Pod Lifecycle Event Generator) issues—sometimes tied to runtime slowness.

### Part D — Controlled recovery (lab only)

> **Warning:** Restarting kubelet **disrupts** pod housekeeping momentarily. Do this during a maintenance window on production systems.

If policy allows:

```bash
sudo systemctl restart kubelet
sudo systemctl status kubelet
```

Back on your workstation:

```bash
kubectl get node <node-name> -w
```

The node should return to **Ready** if the underlying issue was a stuck kubelet process and the runtime is healthy.

---

<a id="ex3"></a>

## Exercise 3: Kubelet Log Analysis

Logs are the fastest path from “NotReady” to a specific misconfiguration—once you know how to **filter** without drowning in noise.

### Step 1: Follow kubelet logs live

On the node:

```bash
sudo journalctl -u kubelet -f
```

Press **Ctrl+C** to stop following.

### Step 2: Pull recent errors only

```bash
sudo journalctl -u kubelet --since "1 hour ago" --no-pager | grep -i error
```

**Tip:** Some distributions log at **info** level with few literal “error” strings. If this returns nothing, widen the filter:

```bash
sudo journalctl -u kubelet --since "1 hour ago" --no-pager | grep -iE 'fail|unhealthy|unable|forbidden|denied'
```

### Step 3: Inspect kubelet configuration

Default data directory on many kubeadm installs:

```bash
sudo ls -la /var/lib/kubelet/
sudo sed -n '1,200p' /var/lib/kubelet/config.yaml
```

You will commonly see fields such as **`cgroupDriver`**, **`clusterDNS`**, eviction thresholds, and **`authentication`/`authorization`** webhook modes. Line numbers and keys vary by Kubernetes version—compare against official docs for your minor release.

Also check the **kubelet drop-in** or service flags (paths vary):

```bash
systemctl cat kubelet
```

### Step 4: Recognize frequent log patterns

| Log theme | Often means |
|-----------|-------------|
| **unable to load bootstrap kubeconfig** | join/bootstrap token flow misconfigured; wrong path; expired token. |
| **node "..." not found** | kubelet **--hostname-override** / cloud name mismatch vs Node object name. |
| **x509: certificate** errors | wrong CA, expired kubelet client cert, or skewed clock. |
| **CNI plugin not initialized** | pod networking not ready; node may flap Ready depending on install. |

### Step 5: Confirm kubelet binary version

```bash
kubelet --version
```

Align this with `kubectl get node <name> -o wide` **VERSION** column and your **cluster upgrade** plan ([Lab 40: Cluster Upgrades](lab40-upgrade-cluster-upgrades.md)).

---

<a id="ex4"></a>

## Exercise 4: Container Runtime Troubleshooting

The kubelet talks to the runtime through the **Container Runtime Interface (CRI)**. On containerd clusters, **`crictl`** is the CLI mirror of what the kubelet drives.

### Step 1: Runtime daemon status

```bash
sudo systemctl status containerd
```

### Step 2: CRI diagnostics

```bash
sudo crictl info
```

You want a coherent JSON report: **cgroup driver** alignment with kubelet, **runtime name**, and **sandbox/image** endpoints.

If `crictl` errors immediately, check **socket** path and **CONTAINER_RUNTIME_ENDPOINT** environment (if customized).

### Step 3: List running and stopped containers

```bash
sudo crictl ps
sudo crictl ps -a
```

**Mapping to Kubernetes:**

- Use **`crictl pods`** to list **podsandbox** objects.
- Pair **pod** IDs with **`kubectl get pod -o wide`** on workloads you know are scheduled on this node.

### Step 4: Inspect one container

Pick a **`CONTAINER ID`** from `crictl ps`:

```bash
sudo crictl inspect <container-id>
```

Focus on:

- **State** (`running`, `exited`, OOM, etc.).
- **LogPath** — where stdout/stderr files may be mirrored on disk.
- **Labels** — Kubernetes metadata annotations/labels are often mirrored here.

### Step 5: Manual image pull

Test registry reachability and auth from the node:

```bash
sudo crictl pull docker.io/library/nginx:latest
```

Failure here often correlates with **`ImagePullBackOff`** at the Pod level—even when the kubelet looks healthy.

### Step 6: Verify containerd socket

```bash
ls -la /run/containerd/containerd.sock
```

Expect a **socket** file owned by **`root`** with group readable by the runtime/kubelet users per your distribution’s packaging.

---

<a id="ex5"></a>

## Exercise 5: Resource Pressure Scenarios

The kubelet enforces **evictions** when it detects pressure signals (configured via **eviction thresholds** in `kubelet` config and hard/soft signals). Understanding **QoS classes** tells you **who gets evicted first** when the kubelet must free resources.

### Step 1: Disk pressure signals on the node

```bash
df -h
```

Pay attention to mounts hosting **`/var/lib/kubelet`**, **`/var/lib/containerd`**, **image layers**, and **logs**.

In `kubectl describe node`, correlate real disk usage with **`DiskPressure`**.

### Step 2: Memory pressure signals

```bash
free -m
```

Also useful:

```bash
grep -iE 'MemAvailable|MemTotal' /proc/meminfo
```

### Step 3: Eviction order (QoS)

Kubernetes classifies pods into **QoS classes** based on **requests** and **limits**:

| QoS class | Typical eviction vulnerability |
|-----------|---------------------------------|
| **BestEffort** | No CPU/memory requests/limits — **first** candidate under resource pressure. |
| **Burstable** | At least one container has a request (or limits without full alignment) — **after** BestEffort in many scenarios. |
| **Guaranteed** | Every container has equal requests and limits for CPU/memory — **last** resort for memory eviction. |

This ordering is a **mental model** for planning; exact behavior also depends on **priority**, **grace periods**, and **thresholds**.

### Step 4: Reclaim disk — prune unused images

> **Caution:** Pruning images removes **unused** layers. On dev clusters this is usually fine; on nodes running many dormant Jobs, verify impact.

```bash
sudo crictl rmi --prune
```

Re-check disk:

```bash
df -h /var/lib/containerd
```

### Step 5: PID pressure awareness

Rough process count:

```bash
ps aux | wc -l
```

Compare with **`PIDPressure`** in `kubectl describe node`. **Runaway forks** or **zombie storms** can starve PID space even when CPU/memory look OK.

### Step 6: Tie pressure back to the API

```bash
kubectl describe node <node-name> | sed -n '/Conditions:/,/Addresses:/p'
kubectl get events --field-selector involvedObject.name=<node-name> --all-namespaces
```

Events may mention **evicted** pods or **FreeDiskSpaceFailed**-style reasons (wording varies by version).

---

<a id="ex6"></a>

## Exercise 6: Node Join / Rejoin

New nodes fail to join for a handful of repeatable reasons: **expired bootstrap tokens**, **wrong API endpoint**, **firewall blocks on 6443**, **swap still on**, or **leftover state** from a previous cluster on the disk.

### Step 1: List bootstrap tokens (on a control plane node)

```bash
sudo kubeadm token list
```

Tokens show **TTL**. Expired tokens cannot authenticate new nodes.

### Step 2: Create a fresh token and print join command

```bash
sudo kubeadm token create --print-join-command
```

Copy the output exactly; it includes **`kubeadm join`**, **token**, **discovery hash**, and **API endpoint**.

### Step 3: Network check from the joining node

Replace `<master-ip>` with your control plane endpoint IP or DNS:

```bash
nc -zv <master-ip> 6443
```

Success implies **TCP reachability**—not full TLS trust (that comes next during `kubeadm join`).

### Step 4: When a node was previously joined — reset and rejoin

> **Destructive:** `kubeadm reset` tears down local Kubernetes state on that machine. **Do not** run this on a production node unless you intend to remove it from service.

On the **worker** (after draining and deleting the Node object from the cluster in real operations):

```bash
sudo kubeadm reset -f
```

Then re-run the **`kubeadm join`** command you generated.

### Step 5: Verify registration

On a workstation with `kubectl`:

```bash
kubectl get nodes -o wide
```

The node should appear **Ready** after the kubelet registers and CNI is ready.

### Step 6: If join still fails — quick checklist

- **Time sync** (`chrony`/`systemd-timesyncd`) — TLS validation fails with skewed clocks.
- **Swap** — kubeadm expects swap **off** unless explicitly configured for newer flows.
- **Hostname/DNS** — stable name resolvable from control plane if your install requires it.
- **Firewall rules** — 6443 from node to API; plus **10250** and other paths for logs/exec depending on architecture.

---

## Key Takeaways

- **Learning path:** Pair this lab with [Lab 49: Cluster and Control Plane Troubleshooting](lab49-ts-cluster-control-plane.md) for API/etcd issues, and with [Lab 52: Networking and Connectivity Troubleshooting](lab52-ts-network-connectivity.md) when the node is `Ready` but workload traffic still fails across the cluster.
- **Node health** is an **API projection** of kubelet heartbeats and conditions—start with **`kubectl describe node`**, then SSH when signals are stale or contradictory.
- **`NotReady`** usually reduces to **kubelet process**, **container runtime**, **network to API**, or **CNI**—use **`systemctl`** + **`journalctl`** to distinguish them quickly.
- **`crictl`** is the operator’s window into **CRI** state: images, sandboxes, and containers **as the kubelet sees them**.
- **Pressure conditions** tie **OS metrics** (`df`, `free`, PID counts) to **scheduling and evictions**; **QoS class** predicts **who is at risk**.
- **Join issues** are often **expired tokens** or **connectivity**—regenerate tokens and verify **6443** before deep debugging.

## Troubleshooting Tips

- If **`kubectl top node`** fails, fix **Metrics Server** first—absence of metrics does **not** imply the node is unhealthy.
- **`grep` on logs** can miss structured JSON lines; fall back to **`journalctl -u kubelet --since ...`** without grep when results look empty.
- **`crictl`** requires matching **socket** configuration; if commands fail, compare with **`systemctl cat containerd`** and kubelet flags.
- After **`kubeadm reset`**, ensure the old **Node** object is removed from etcd if you reuse the same name—otherwise objects can conflict with expectations.
- For **control-plane** symptoms (API flakes, `etcd` alarms), pivot to [Lab 49: Cluster and Control Plane Troubleshooting](lab49-ts-cluster-control-plane.md) instead of tuning kubelet indefinitely.
- When **nodes are healthy** but **Pods** misbehave (probes, image pulls, `CrashLoopBackOff`), use [Lab 50: Pod Failures](lab50-ts-pod-failures.md) first, then [Lab 52: Networking and Connectivity Troubleshooting](lab52-ts-network-connectivity.md) for Service, Endpoint, and DNS paths.

## Cleanup

This lab is mostly **observational** and does not require a dedicated namespace. If you need to undo **control-plane** experiments from the same study session, follow the cleanup section in [Lab 49](lab49-ts-cluster-control-plane.md).

If you restarted services or pruned images:

- No cluster objects are required for cleanup.
- If you created temporary files on nodes, remove them manually.
- If you ran **`kubeadm reset`** on a machine you still need in the cluster, **re-join** it before closing the lab.

```bash
# Example: confirm nodes are still Ready after exercises
kubectl get nodes
```

## Next Steps

- **Previous in series:** [Lab 49: Cluster and Control Plane Troubleshooting](lab49-ts-cluster-control-plane.md) — separates API, scheduler, controller-manager, and etcd issues from kubelet symptoms.
- **Related workload layer:** [Lab 50: Pod Failures](lab50-ts-pod-failures.md) — `describe pod`, events, image pull, and probe failures before you assume the node is at fault.
- **Continue troubleshooting:** [Lab 52: Networking and Connectivity Troubleshooting](lab52-ts-network-connectivity.md) — when pods and Services fail across nodes (add this manual to the repo when published; filename may vary).
- **Interactive review:** [Kubelet & Node Troubleshooting (HTML)](../html/ts-kubelet-node.html).
- **Related:** [Lab 36: Metrics Server](lab36-observe-metrics-server.md) for **`kubectl top`**, [Lab 27: Static Pods](lab27-workload-static-pods.md) for kubelet-managed manifests, [Lab 06: kubeadm install](lab06-install-kubernetes-kubeadm.md) for baseline cluster wiring.

---

*Lab 51 — Kubelet and Node Troubleshooting — hands-on diagnostics for node conditions, kubelet logs, containerd/CRI, resource pressure, and kubeadm join flows.*
