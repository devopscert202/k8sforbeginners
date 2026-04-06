## Kubernetes on AWS EC2 (conceptual overview)

This document describes **what** you need for a kubeadm-style cluster on **EC2** (e.g. one control plane and multiple workers), **why** each layer matters, and **how** the pieces fit together. Step-by-step install commands belong in [Lab 06](../../labmanuals/lab06-install-kubernetes-kubeadm.md).

### Role of each node

- **Control plane node:** Runs the Kubernetes API, scheduler, controller-manager, and (for stacked etcd) etcd. Workloads are usually not scheduled here unless you remove the control-plane taint (not typical for production learning clusters).
- **Worker nodes:** Run **kubelet**, the **container runtime** (e.g. containerd), and your Pods. They register with the API server and receive Pod assignments.

### Network and security on AWS

- **Security groups** should allow **SSH** from admin sources, **6443** (API) from workers (and admins), **10250** (kubelet) between control plane and workers as required by your topology, and **NodePort** range (e.g. **30000–32767**) if you use NodePort Services. Tighten sources to known CIDRs rather than `0.0.0.0/0` where possible.
- **Network ACLs** must not block the same ports between subnets if you use them.
- After the cluster is up, a **CNI plugin** (Calico, Cilium, etc.) provides Pod networking and network policies; the `kubeadm init` **pod network CIDR** must match the CNI’s documented range.

### Software layers (all nodes)

- **OS updates** and consistent OS version across nodes reduce kernel/runtime drift.
- **containerd** (or another supported runtime) with **systemd cgroup** driver aligned to kubelet expectations.
- **Kernel modules and sysctl:** `br_netfilter`, `overlay`, and `ip_forward` / bridge iptables settings are commonly required for Kubernetes networking.
- **kubeadm, kubelet, kubectl** at compatible versions per the [version skew policy](https://kubernetes.io/releases/version-skew-policy/).

### Bootstrapping (high level)

- On the first control plane: **`kubeadm init`** with the chosen **service CIDR** and **pod CIDR** (the latter must match the CNI).
- Copy **admin kubeconfig** to the operator user for `kubectl`.
- Apply the **CNI manifest**; confirm nodes reach `Ready`.
- On workers: run **`kubeadm join`** with the token and CA hash emitted by `kubeadm init` (or use config files for production).

### Validation (conceptual)

- **Nodes:** `kubectl get nodes` should show `Ready`.
- **System workloads:** `kube-system` Pods should be running.
- **Smoke test:** A simple Deployment + Service (ClusterIP or NodePort) confirms scheduling, DNS, and routing.

### Troubleshooting themes

- **Join failures:** Clock skew, firewall, wrong API advertise address, expired bootstrap token.
- **NotReady nodes:** Kubelet logs, runtime status, CNI pods, disk/memory pressure.
- **Pod stuck ContainerCreating:** Image pull, volume mount, or CNI errors visible in `kubectl describe pod`.

---

## Hands-On Labs

Practice these concepts with guided lab exercises:

| Lab | Description |
|-----|-------------|
| [Lab 06: Kubernetes Cluster Installation](../../labmanuals/lab06-install-kubernetes-kubeadm.md) | Full kubeadm install, CNI, join workers, and cluster validation |
