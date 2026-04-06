# Summary of Steps for Kubernetes Upgrade

This page is a **high-level reference** for kubeadm-style upgrades: what to do in each phase and why. Exact package names, versions, and node names depend on your OS and cluster—follow [Lab 40](../../labmanuals/lab40-upgrade-cluster-upgrades.md) or the version-specific guides in this folder for command-level detail.

## Backup before the upgrade

- **etcd** holds cluster state; take a verified snapshot before changing control plane components. Typical flow: set `ETCDCTL_API=3`, point `etcdctl` at the member endpoints and TLS assets under `/etc/kubernetes/pki/etcd/`, run `etcdctl snapshot save`, then `snapshot status` on the file.
- **Configuration:** Preserve `/etc/kubernetes`, static pod manifests, and any custom kubeadm or kubelet config you rely on for restore or audit.

## Upgrade the control plane

- Refresh packages to the **target minor version only** (Kubernetes does not support skipping minors).
- Upgrade **kubeadm** first; run `kubeadm upgrade plan`, then `kubeadm upgrade apply` for the desired version.
- **Drain** the control plane node when upgrading its kubelet (unless your topology treats it differently); upgrade **kubelet** and **kubectl** to match; restart kubelet; **uncordon** when healthy.

## Upgrade worker nodes

- For each node (or pool): install matching **kubeadm**, run **`kubeadm upgrade node`** on the worker, **drain** from a machine with `kubectl` access, upgrade **kubelet** and **kubectl**, restart kubelet, **uncordon**, and confirm `Ready` before continuing.
- Rolling one node at a time (or small batches) limits blast radius; respect **PodDisruptionBudgets** and workload capacity.

## Validate the upgrade

- Confirm **node versions** and `Ready` state, system namespaces (e.g. `kube-system`) healthy, and a **smoke workload** if appropriate.
- Watch **events** and core addons (CNI, DNS, kube-proxy) for regressions.

## Rollback if the upgrade fails

- Restoring **etcd** from a known-good snapshot is the primary path for catastrophic failure; that usually implies stopping kubelet, restoring data to the configured etcd data directory, and bringing components back in a documented order consistent with your install guide.
- **Downgrading** binaries (kubeadm, kubelet, kubectl) to the previous minor may be required; align package repositories with that minor and verify skew rules.

## Version skew policy considerations

- **kubeadm** upgrades are **one minor version at a time** (e.g. 1.27 → 1.28 → 1.29).
- **Worker kubelets** may lag the API server by **at most one minor** version.
- **kubectl** is generally supported within **±1 minor** of the API server.

| Component               | Supported skew (typical) |
|-------------------------|---------------------------|
| Control plane → nodes   | Nodes may lag by 1 minor  |
| API server → kubelet    | Kubelet may lag by 1 minor |
| Client → API server     | kubectl within ±1 minor   |

## Additional considerations

- **Staging:** Exercise the full path on a non-production cluster first.
- **Observability:** Watch metrics and logs through the upgrade window.
- **Managed clouds (EKS, AKS, GKE):** Control plane upgrades are provider-driven; worker/node image upgrades follow vendor workflows.

---

## Hands-On Labs

Practice these concepts with guided lab exercises:

| Lab | Description |
|-----|-------------|
| [Lab 40: Kubernetes Cluster Upgrades with kubeadm](../../labmanuals/lab40-upgrade-cluster-upgrades.md) | Hands-on kubeadm upgrade, drain/cordon, etcd backup concepts, and validation |

---

## Final summary

Successful upgrades combine **verified backups**, **ordered component upgrades** (control plane before workers, one minor at a time), **incremental node rollout**, **post-upgrade validation**, and a **documented rollback** path. Use the lab manual and version-specific docs in `k8s/docs/upgrade/` when you need exact commands.
