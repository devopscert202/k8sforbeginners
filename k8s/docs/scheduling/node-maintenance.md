## **Kubernetes cordon, drain, and uncordon**

**Cordon**, **drain**, and **uncordon** are node lifecycle operations used during maintenance, upgrades, or node removal. They adjust whether the scheduler may place new Pods on a node and whether existing workloads should be evicted.

---

### **Table of Contents**

1. [Overview](#overview)  
2. [Concepts](#concepts)  
3. [Benefits](#benefits)  
4. [Use cases](#use-cases)  
5. [Real-world scenarios](#real-world-scenarios)  
6. [Behavior summary](#behavior-summary)  
7. [Summary table](#summary-table)  

---

### **Overview**

These commands let administrators **prepare** a node (stop new scheduling), **empty** it safely (evict Pods subject to disruption budgets and policies), and **return** it to service. They complement **taints** and workload controllers that recreate evicted Pods elsewhere.

---

### **Concepts**

- **Cordon**: Marks a node **unschedulable** (`SchedulingDisabled`). Running Pods stay; no new Pods are assigned except in unusual cases (static Pods, some DaemonSets).
- **Drain**: Evicts Pods from the node (respecting **PodDisruptionBudgets** when possible) and leaves the node unschedulable—typical before maintenance or decommission.
- **Uncordon**: Clears the unschedulable state so normal scheduling resumes.

Common flags on **drain** include `--ignore-daemonsets` (DaemonSet Pods are not evicted by default behavior expectations) and `--force` for Pods with no controller (use with care). Always review cluster-specific runbooks: managed offerings may integrate node replacement with these patterns.

---

### **Benefits**

1. **Controlled maintenance**: Reduce risk during OS patches, kubelet upgrades, or hardware work.  
2. **Rescheduling**: ReplicaSets, Deployments, and StatefulSets recreate Pods on healthy nodes.  
3. **Isolation**: Temporarily steer traffic away from a suspect node without immediate eviction (cordon-only).  
4. **Rolling node operations**: Combine with cluster autoscaler or manual scale-in after drains.

---

### **Use cases**

1. **Node maintenance**: Kernel, container runtime, or kubelet updates.  
2. **Scale-down**: Drain before removing a node from the pool.  
3. **Hardware replacement**: Evict workloads before power or disk work.  
4. **Load relief**: Cordon an overloaded node so new Pods land elsewhere while you investigate.

---

### **Real-world scenarios**

- **Managed cloud**: Node repair or image rollouts may cordon/drain automatically; understanding the semantics helps interpret node conditions.  
- **On-premises**: Sequential drain across workers while keeping the control plane available.  
- **Upgrades**: One node at a time, verifying cluster capacity for displaced Pods.

---

### **Behavior summary**

After **cordon**, `kubectl get nodes` shows `SchedulingDisabled` while the node can still be `Ready`. After **drain**, workloads should appear on other nodes unless constraints (taints, resources, PDBs) block eviction—then the command reports errors and may require policy or capacity fixes. **Uncordon** only affects scheduling; it does not move Pods back.

---

### **Example Pod spec (context only)**

Any standard Pod or Deployment can be used to observe rescheduling when nodes are drained; the scheduling outcome depends on labels, affinity, resources, and PDBs—not on a special Pod shape:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: sample-pod
spec:
  containers:
  - name: nginx
    image: nginx:1.23
    ports:
    - containerPort: 80
```

---

### **Summary Table**

| **Command**       | **Purpose**                                         | **Effect on Pods**                                   | **Typical use**                        |  
|--------------------|-----------------------------------------------------|-----------------------------------------------------|----------------------------------|  
| `kubectl cordon`   | Mark a node unschedulable                           | Existing pods usually stay; new pods are not scheduled | Prepare for maintenance           |  
| `kubectl drain`    | Evict pods and leave node unschedulable             | Running pods are terminated/evicted and recreated elsewhere | Maintenance or node removal       |  
| `kubectl uncordon` | Mark node schedulable again                         | Allows new pods to be scheduled                     | After maintenance completes       |  

---

## Hands-On Labs

Practice these concepts with guided lab exercises:

| Lab | Description |
|-----|-------------|
| [Lab 08: Cluster Administration with kubeadm](../../labmanuals/lab08-cluster-administration.md) | Node operations, cluster admin tasks, and related kubectl practice |
