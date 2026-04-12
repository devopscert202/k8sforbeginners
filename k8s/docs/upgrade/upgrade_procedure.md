# Kubernetes upgrade procedure (general)

This document is the **shared reference** for kubeadm-style upgrades: why and how to prepare, back up, order work across control plane and workers, respect version skew, validate, and roll back. Exact package versions, repository URLs, and release-specific API notes live in the other Markdown guides in this folder (for example [`v1.27 → v1.28`](./v1.27_to_v1.28.md)). For a guided exercise, see [Lab 40](../../labmanuals/lab40-upgrade-cluster-upgrades.md).

---

## Introduction to Kubernetes upgrades

Upgrading a cluster keeps the platform patched, unlocks features, and reduces known defects. These steps target **self-managed** clusters (typically **kubeadm** on Linux). Managed offerings (**EKS**, **AKS**, **GKE**, and similar) use provider workflows for the control plane and often for node images—use their documentation for authoritative steps.

### Considerations for version selection

- **Compatibility:** Follow the official Kubernetes [version skew policy](https://kubernetes.io/releases/version-skew-policy/) (also summarized below).
- **Minor versions:** Upgrade **one minor at a time** (for example 1.27 → 1.28 → 1.29). Do not skip minors.
- **Major versions:** Plan for API deprecations and breaking changes; read release notes.
- **Release notes:** Review [Kubernetes releases](https://kubernetes.io/releases/) / changelog for your target minor.
- **Staging:** Run through the full upgrade on a non-production cluster before production.

---

## Version skew policy (summary)

Rules evolve slightly by release; always confirm against the [official skew documentation](https://kubernetes.io/releases/version-skew-policy/).

| Area | Typical rule |
|------|----------------|
| **Upgrade path** | **One minor** per upgrade (kubeadm does not support skipping minors). |
| **kubelet vs API server** | Kubelets must **not** be newer than `kube-apiserver` and may be up to **two** minor versions **older** (often summarized as kubelet at **N, N-1, N-2** when the API server is at **N**). |
| **Control plane components** | `kube-controller-manager`, `kube-scheduler`, and `cloud-controller-manager` should match `kube-apiserver` within **one** minor (prefer **same** minor as the API server). |
| **kubectl** | Supported within **±1 minor** of the API server. |
| **Rolling workers** | While you roll workers, some nodes may temporarily lag the new API server by one minor; keep that window short and within skew. |

During an upgrade, **upgrade the control plane first**, then bring workers (and kubelets) up toward the target minor in a controlled order.

---

## Prerequisites

- **Cluster:** Running cluster at the **current** minor you are upgrading **from** (already healthy).
- **Binaries:** `kubeadm`, `kubectl`, and `kubelet` present on nodes you touch; `etcdctl` where you take etcd snapshots (often control plane nodes).
- **Access:** `sudo` on nodes; `kubectl` configured from an admin machine or control plane; SSH or equivalent as you normally use.
- **Network:** Reachable package repositories (or offline packages prepared in advance).
- **Naming:** Replace placeholder node names (for example `master.example.com`, `<control-plane-node>`, `<worker-node>`) with your real names.
- **Capacity:** Enough spare capacity to **drain** nodes without violating **PodDisruptionBudgets**; upgrade **one node or a small batch** at a time to limit blast radius.
- **HA control plane:** Upgrade **each** control plane node in sequence. On the **first** node run `kubeadm upgrade plan` and `kubeadm upgrade apply`; on **additional** control plane nodes use **`kubeadm upgrade node`** (not `apply`).

---

## Backup before the upgrade

### etcd

**etcd** holds cluster state. Take a **verified** snapshot before changing control plane components.

On a control plane node (paths assume default kubeadm layout):

1. **Confirm etcdctl (API v3):**
   ```bash
   ETCDCTL_API=3 etcdctl version
   ```
2. **Set connection variables** (member on localhost is typical for stacked etcd):
   ```bash
   export ETCDCTL_API=3
   export ETCDCTL_ENDPOINTS=https://127.0.0.1:2379
   export ETCDCTL_CACERT=/etc/kubernetes/pki/etcd/ca.crt
   export ETCDCTL_CERT=/etc/kubernetes/pki/etcd/server.crt
   export ETCDCTL_KEY=/etc/kubernetes/pki/etcd/server.key
   ```
3. **Save a snapshot** (use a path you persist off-node if possible):
   ```bash
   sudo etcdctl snapshot save /path/to/backup/etcd-snapshot.db
   ```
4. **Verify the file:**
   ```bash
   sudo etcdctl snapshot status /path/to/backup/etcd-snapshot.db
   ```

For external etcd or HA topologies, endpoints and certificates differ—see [Backing up an etcd cluster](https://kubernetes.io/docs/tasks/administer-cluster/configure-upgrade-etcd/#backing-up-an-etcd-cluster).

### Configuration and manifests

- Preserve **`/etc/kubernetes`**, static pod manifests, kubeadm config you applied, and any custom **kubelet** config for audit and disaster recovery.

---

## Drain, cordon, and upgrade order (kubeadm)

- **Cordon** (optional but common): `kubectl cordon <node>` prevents new workload scheduling before you drain.
- **Drain** evicts workloads (respects PDBs unless you override). Typical flags: `--ignore-daemonsets`, and for workers often `--delete-emptydir-data`. Use `--force` only when you understand the impact.
- **Uncordon** when the node is healthy again: `kubectl uncordon <node>`.

**Control plane node (single or per HA member):**

1. Point packages at the **target** minor and install the target **`kubeadm`**; run **`kubeadm upgrade plan`** then **`kubeadm upgrade apply <version>`** (first CP only) or **`kubeadm upgrade node`** (additional CP members).
2. **Drain** the control plane node **when upgrading its kubelet** on that node (some topologies treat the control plane differently; match your organization’s practice).
3. Install matching **`kubelet`** and **`kubectl`**; **`systemctl daemon-reload`** and **restart kubelet**.
4. **Uncordon** and confirm **`Ready`**.

**Worker nodes:**

1. Install target **`kubeadm`** on the worker; run **`kubeadm upgrade node`**.
2. **Drain** the worker from a machine with **`kubectl`** access.
3. Install matching **`kubelet`** and **`kubectl`**; restart kubelet; **uncordon**; confirm **Ready** before the next node.

Pin versions with your packaging tool where appropriate (for example **`apt-mark hold`** on Debian/Ubuntu) so components do not drift unintentionally after the upgrade.

---

## Upgrade the control plane (summary)

- Refresh packages to the **target minor only**.
- Upgrade **kubeadm** first; **`kubeadm upgrade plan`**, then **`kubeadm upgrade apply`** with the exact target version string.
- Then upgrade **kubelet** and **kubectl** on that node to match (after drain if you drain for kubelet upgrades).
- Repeat for additional control plane nodes using **`kubeadm upgrade node`** as appropriate.

---

## Upgrade worker nodes (summary)

- For each node: matching **kubeadm** → **`kubeadm upgrade node`** → **drain** → **kubelet** + **kubectl** → restart kubelet → **uncordon** → validate.
- Roll **one node at a time** or in small batches; watch PDBs and cluster capacity.

---

## Validate the upgrade

- **`kubectl get nodes`** (versions and **Ready**).
- Core addons (**CNI**, **DNS**, **kube-proxy**) and **`kube-system`** pods healthy.
- Optional smoke test: run a short-lived pod or your standard validation workload.
- **`kubectl get events -A`** (or equivalent) for errors during the window.

---

## Rollback if the upgrade fails

Rollback is **destructive** and **environment-specific**; rehearse in staging.

- **etcd:** Restoring a **known-good snapshot** is the primary path for catastrophic control plane failure. That usually means stopping members safely per your topology, restoring data to the configured etcd data directory, then bringing etcd and the API server back in an order consistent with your install guide.
- **Packages:** **Downgrade** `kubeadm`, `kubelet`, and `kubectl` to the **previous** minor may be required; **align APT/YUM repositories** with that minor and use vendor-supported downgrade flags (for example **`--allow-downgrades`** on apt where appropriate).
- **kubeadm:** Re-applying the previous cluster version may require **`kubeadm upgrade apply <previous-version> --force`** only when documented for your situation—read kubeadm’s output and logs carefully.

---

## Additional considerations

- **Observability:** Watch metrics and logs through the upgrade window.
- **Managed clouds:** Control plane upgrades are provider-driven; node upgrades follow vendor workflows.

---

## Hands-on labs

| Lab | Description |
|-----|-------------|
| [Lab 40: Kubernetes Cluster Upgrades with kubeadm](../../labmanuals/lab40-upgrade-cluster-upgrades.md) | Hands-on kubeadm upgrade, drain/cordon, etcd backup concepts, and validation |

---

## Final summary

Successful upgrades combine **verified backups**, **ordered component upgrades** (control plane first, one minor at a time), **incremental node rollout** within **version skew**, **post-upgrade validation**, and a **documented rollback** path. Use the version-specific files in this directory for exact package versions and repository lines.
