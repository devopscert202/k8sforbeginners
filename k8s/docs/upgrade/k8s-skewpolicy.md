# Kubernetes Version Skew Policy: An Easy-to-Understand Guide

## Introduction
When upgrading or maintaining a Kubernetes cluster, understanding the **version skew policy** is crucial to ensure compatibility between the control plane and worker nodes, as well as between Kubernetes components. This guide simplifies the concepts, explains key rules, and provides examples to help you plan upgrades effectively.

For more details from Oficial documentation, refer https://kubernetes.io/releases/version-skew-policy/

---

## What Is Version Skew?
Version skew refers to differences in versions between:
- **Control Plane** components (e.g., API Server, Controller Manager, Scheduler).
- **Kubelet** (the agent running on each node).
- **Kubectl** (the CLI tool used by administrators).

Kubernetes enforces specific compatibility rules to prevent issues caused by version mismatches.

---

## Key Rules of Version Skew Policy
Here’s a summary of the compatibility rules:

| **Component**               | **Supported Version Skew**                                                                                     |
|-----------------------------|----------------------------------------------------------------------------------------------------------------|
| **Control Plane to Kubelet** | Kubelet versions can be **one minor version behind** the control plane version.                                |
| **Kubectl to Control Plane** | Kubectl supports the control plane version it interacts with, as well as **one minor version older or newer**. |

---

## Rule Breakdown with Examples
### 1. **Control Plane to Kubelet**
The kubelet on worker nodes can be **one minor version behind** the control plane. This ensures compatibility while allowing flexibility in upgrading.

#### Example:
- Control Plane version: `1.28`
- Supported Kubelet versions: `1.27`, `1.28`

#### What happens if the kubelet is two versions behind?
- Example: Control Plane is `1.28`, but Kubelet is `1.26`.
- Result: The node may not register or function properly.

#### Recommendation:
- Always upgrade the control plane first.
- Upgrade worker nodes (kubelet) immediately after.

#### Scenarios for Kubelet Version Skew:
- **Scenario 1: All nodes upgraded gradually**
  - Example: Start upgrading one node at a time to minimize disruptions.
  - Tip: Use `kubectl cordon` and `kubectl drain` to safely prepare a node for upgrade.
- **Scenario 2: Large cluster with node pools**
  - Example: If you have separate node pools, upgrade one pool at a time.
  - Tip: Ensure workloads are rescheduled properly.

---

### 2. **Kubectl to Control Plane**
Kubectl can interact with a control plane that is:
- One minor version **older**.
- The **same** version.
- One minor version **newer**.

#### Example:
| **Kubectl Version** | **Compatible Control Plane Versions** |
|---------------------|---------------------------------------|
| `1.27`              | `1.26`, `1.27`, `1.28`               |
| `1.28`              | `1.27`, `1.28`, `1.29`               |

#### What happens if kubectl is two versions behind?
- Example: Kubectl is `1.26`, but the control plane is `1.29`.
- Result: Kubectl commands may fail or behave unpredictably.

#### Recommendation:
- Keep kubectl updated alongside your cluster.

---

# Control Plane and Worker Node Version Compatibility: Important Tips and Notes


## Key Compatibility Rules

1. **Control Plane Version ≥ Worker Node Version**
   - The control plane must always be the same version or newer than the worker nodes.
   - Worker nodes cannot run a version higher than the control plane.

   **Example**:
   - **Allowed**: Control Plane `v1.28.x`, Worker Node `v1.27.x`
   - **Not Allowed**: Control Plane `v1.28.x`, Worker Node `v1.29.x`

2. **Kubelet Version Compatibility**
   - Kubelet on worker nodes must be the same version as the control plane or at most one minor version behind.
   - **Rule**:  
     `Control Plane ≤ Kubelet ≤ Control Plane + 1 minor version`

   **Example**:
   - If the control plane is `v1.28.x`:  
     Allowed kubelet versions: `v1.27.x` (lagging) or `v1.28.x` (matching).

3. **kubectl Version Compatibility**
   - `kubectl` can communicate with the control plane within ±1 minor version.
   - **Rule**:  
     `Control Plane - 1 ≤ kubectl ≤ Control Plane + 1 minor version`

   **Example**:
   - If the control plane is `v1.28.x`:  
     Allowed kubectl versions: `v1.27.x`, `v1.28.x`, or `v1.29.x`.

---

## Do’s

1. **Upgrade Control Plane First**
   - Always start with upgrading the control plane before worker nodes. This ensures the cluster's stability and avoids breaking compatibility.
   - Use `kubeadm` to apply the upgrade to the control plane:
     ```bash
     kubeadm upgrade apply <version>
     ```

2. **Upgrade Worker Nodes Gradually**
   - Upgrade worker nodes one at a time to minimize downtime and reduce the risk of errors impacting the entire cluster.
   - Drain and cordon each node before upgrading:
     ```bash
     kubectl cordon <node-name>
     kubectl drain <node-name> --ignore-daemonsets
     ```

3. **Keep kubeadm, kubelet, and kubectl Aligned**
   - Use the same minor version for `kubeadm`, `kubelet`, and `kubectl` where possible. Update `kubeadm` first, then `kubelet`, and final


---

## Key Compatibility Rules

1. **Control Plane Version ≥ Worker Node Version**
   - The control plane must always be the same version or newer than the worker nodes.
   - Worker nodes cannot run a version higher than the control plane.

   **Example**:
   - **Allowed**: Control Plane `v1.28.x`, Worker Node `v1.27.x`
   - **Not Allowed**: Control Plane `v1.28.x`, Worker Node `v1.29.x`

2. **Kubelet Version Compatibility**
   - Kubelet on worker nodes must be the same version as the control plane or at most one minor version behind.
   - **Rule**:  
     `Control Plane ≤ Kubelet ≤ Control Plane + 1 minor version`

   **Example**:
   - If the control plane is `v1.28.x`:  
     Allowed kubelet versions: `v1.27.x` (lagging) or `v1.28.x` (matching).

3. **kubectl Version Compatibility**
   - `kubectl` can communicate with the control plane within ±1 minor version.
   - **Rule**:  
     `Control Plane - 1 ≤ kubectl ≤ Control Plane + 1 minor version`

   **Example**:
   - If the control plane is `v1.28.x`:  
     Allowed kubectl versions: `v1.27.x`, `v1.28.x`, or `v1.29.x`.

---

## Do’s

1. **Upgrade Control Plane First**
   - Always start with upgrading the control plane before worker nodes. This ensures the cluster's stability and avoids breaking compatibility.
   - Use `kubeadm` to apply the upgrade to the control plane:
     ```bash
     kubeadm upgrade apply <version>
     ```

2. **Upgrade Worker Nodes Gradually**
   - Upgrade worker nodes one at a time to minimize downtime and reduce the risk of errors impacting the entire cluster.
   - Drain and cordon each node before upgrading:
     ```bash
     kubectl cordon <node-name>
     kubectl drain <node-name> --ignore-daemonsets
     ```

3. **Keep kubeadm, kubelet, and kubectl Aligned**
   - Use the same minor version for `kubeadm`, `kubelet`, and `kubectl` where possible. Update `kubeadm` first, then `kubelet`, and finally `kubectl`.

4. **Validate Node Upgrades**
   - Verify node versions after each upgrade:
     ```bash
     kubectl get nodes
     ```

5. **Monitor Logs During Upgrades**
   - Use `kubectl logs` to monitor pods for errors during and after the upgrade to detect issues early.

---

## Don’ts

1. **Don’t Skip Minor Versions**
   - Kubernetes only supports sequential upgrades (e.g., from `v1.27` to `v1.28`, and then `v1.28` to `v1.29`). Skipping versions is not supported.

2. **Don’t Upgrade Worker Nodes Before the Control Plane**
   - Worker nodes cannot run a higher version than the control plane. Doing so will result in version mismatches and potential API communication issues.

3. **Don’t Forget About Add-ons**
   - After upgrading the control plane, ensure you update cluster add-ons (e.g., CNI plugins, CoreDNS, kube-proxy) to maintain compatibility.
   - Use `kubeadm upgrade` to handle core add-ons:
     ```bash
     kubeadm upgrade apply <version>
     ```

4. **Don’t Perform a Mass Node Upgrade**
   - Avoid upgrading all worker nodes simultaneously. Perform upgrades incrementally to avoid cluster-wide disruptions.

5. **Don’t Overlook Backup and Rollback Plans**
   - Before upgrading, back up etcd and other critical cluster data:
     ```bash
     etcdctl snapshot save <snapshot-name>
     ```
   - Plan for rollback in case of failure by ensuring you can restore the previous etcd state.

---

## Tips for Smooth Upgrades

- **Plan Upgrade Downtime**:
  Notify stakeholders of potential disruptions during the upgrade window.

- **Use Maintenance Windows for Upgrades**:
  Schedule upgrades during low-traffic periods to reduce impact on workloads.

- **Leverage Staging Environments**:
  Test upgrades in a staging or non-production environment before applying them to production clusters.

- **Enable Pod Disruption Budgets (PDBs)**:
  Protect critical workloads by configuring PDBs to prevent excessive pod terminations during upgrades:
  ```yaml
  apiVersion: policy/v1
  kind: PodDisruptionBudget
  metadata:
    name: my-app-pdb
  spec:
    minAvailable: 1
    selector:
      matchLabels:
        app: my-app

---

## Why Does `kubectl get nodes` Show a Newer Node Version?
When you run `kubectl get nodes`, it displays the kubelet version running on each worker node. If the kubelet version is newer than the control plane, it’s because the kubelet was upgraded before the API Server. This happens because:

1. **Kubelet Reports Its Version**:
   The `kubectl get nodes` command retrieves node version information directly from the kubelet, regardless of the control plane’s version.

2. **Version Skew Policy Permits It**:
   Kubernetes allows the kubelet to be one minor version ahead of the control plane. For example:
   - Control Plane version: `v1.27.2`
   - Kubelet version: `v1.28.1`

   `kubectl get nodes` will show the kubelet’s version (`v1.28.1`) even though the control plane is on `v1.27.2`.

#### Why Is This a Problem?
- It’s not ideal because the recommended order is to upgrade the control plane first.
- Upgrading the kubelet before the control plane can lead to potential issues if the version skew exceeds one minor version.

#### Recommendation:
- Always upgrade the control plane first, followed by the kubelet.
- If kubelets are upgraded first, update the control plane immediately to maintain compatibility.

---

## High Availability (HA) Cluster Upgrade Scenarios
In an HA setup, upgrading Kubernetes involves additional considerations:

### Key Points:
1. **Control Plane Upgrade Order**:
   - Upgrade one control plane node at a time to maintain availability.
   - Example: If you have three API Server nodes, upgrade one and ensure it stabilizes before proceeding to the next.

2. **Worker Node Upgrade in HA Clusters**:
   - Use a rolling upgrade approach to ensure workloads remain available.
   - Example: Drain and upgrade nodes one by one.

3. **ETCD Cluster Upgrades**:
   - If you manage etcd yourself, ensure its version is compatible with the new Kubernetes version.
   - Tip: Back up etcd before upgrading.

---

## Common Questions
### Q1. What happens if I don’t follow the version skew policy?
You may encounter:
- Nodes failing to register.
- API requests failing due to incompatible kubectl versions.
- Unpredictable behavior in workloads or cluster operations.

### Q2. Can I skip versions during an upgrade?
No. Kubernetes does not support skipping versions. For example:
- From `1.26`, you must upgrade to `1.27`, then to `1.28`.

### Q3. How do I check component versions?
- **Control Plane version:**
  ```bash
  kubectl version --short
  ```
- **Node (Kubelet) versions:**
  ```bash
  kubectl get nodes -o wide
  ```
- **Kubectl version:**
  ```bash
  kubectl version --client
  ```

---

## Summary Table
| **Component**       | **Upgrade Order**              | **Version Skew Policy**                                                     |
|---------------------|-------------------------------|----------------------------------------------------------------------------|
| Control Plane       | Upgrade first                | N/A                                                                        |
| Kubelet (Worker)    | Upgrade after Control Plane  | Can be one minor version behind the Control Plane.                        |
| Kubectl (CLI)       | Upgrade last                 | Can be one minor version older or newer than the Control Plane.           |

---

By following this guide, you can plan and execute Kubernetes upgrades confidently, ensuring compatibility and avoiding downtime.

