## **Kubernetes Cordon, Drain, and Uncordon Lab Tutorial**

This lab tutorial explores how to use the Kubernetes commands `cordon`, `drain`, and `uncordon` to manage node scheduling during maintenance or upgrades. It includes an overview, concepts, benefits, real-world use cases, and step-by-step implementation.

---

### **Table of Contents**

1. [Overview](#overview)  
2. [Concepts](#concepts)  
3. [Benefits](#benefits)  
4. [Use Cases](#use-cases)  
5. [Real-World Scenarios](#real-world-scenarios)  
6. [Lab Implementation](#lab-implementation)  
    - [Step 1: Preparing the Cluster](#step-1-preparing-the-cluster)  
    - [Step 2: Cordon a Node](#step-2-cordon-a-node)  
    - [Step 3: Drain a Node](#step-3-drain-a-node)  
    - [Step 4: Uncordon a Node](#step-4-uncordon-a-node)  
7. [Verification Steps](#verification-steps)  
8. [Summary Table](#summary-table)  

---

### **Overview**

Cordon, drain, and uncordon are critical node lifecycle management commands in Kubernetes. These commands allow cluster administrators to manage scheduling on nodes during maintenance or updates without disrupting application availability.

---

### **Concepts**

- **Cordon**: Marks a node as unschedulable, preventing new pods from being scheduled there while leaving existing pods unaffected.  
- **Drain**: Evicts all running pods from a node and marks it as unschedulable, making it ready for maintenance or decommissioning.  
- **Uncordon**: Marks a node as schedulable again, allowing pods to be scheduled.  

---

### **Benefits**

1. **Controlled Maintenance**: Perform node upgrades or hardware fixes without risking application downtime.  
2. **Pod Rescheduling**: Automatically migrate workloads to other nodes, ensuring high availability.  
3. **Cluster Health Management**: Temporarily isolate problematic nodes without disrupting running workloads.  
4. **Zero-Downtime Updates**: Enable rolling updates and seamless node lifecycle management.  

---

### **Use Cases**

1. **Node Maintenance**: Upgrade the OS or Kubernetes version on a node.  
2. **Scaling Down Clusters**: Drain workloads from nodes before removing them from a cluster.  
3. **Hardware Replacement**: Replace faulty hardware while keeping services operational.  
4. **Load Balancing**: Temporarily shift workloads from an overloaded node to others.  

---

### **Real-World Scenarios**

- **Cloud Node Lifecycle**: Drain nodes during automatic scaling events in managed Kubernetes clusters.  
- **On-Premises Clusters**: Isolate nodes for hardware diagnostics or RAID configuration updates.  
- **Rolling Updates**: Upgrade or patch nodes sequentially in a production environment.  

---

### **Lab Implementation**

#### **Step 1: Preparing the Cluster**

1. **Ensure you have a running Kubernetes cluster** with at least 3 nodes:
   - `master`: Control plane node.
   - `worker-node-1`: First worker node.
   - `worker-node-2`: Second worker node.  
2. Install `kubectl` on your local machine.

#### **Step 2: Cordon a Node**

1. Mark `worker-node-1` as unschedulable:  
   ```bash
   kubectl cordon worker-node-1
   ```

2. Verify the node status:  
   ```bash
   kubectl get nodes
   ```
   Output:
   ```
   NAME             STATUS                     ROLES    AGE    VERSION
   master           Ready                      control   10d    v1.27.4
   worker-node-1    Ready,SchedulingDisabled   <none>   10d    v1.27.4
   worker-node-2    Ready                      <none>   10d    v1.27.4
   ```

---

#### **Step 3: Drain a Node**

1. Evict pods from `worker-node-1`:  
   ```bash
   kubectl drain worker-node-1 --ignore-daemonsets --force
   ```

   - `--ignore-daemonsets`: Ensures daemonsets are not evicted.
   - `--force`: Forces eviction for pods that lack a disruption budget.

2. Verify pod rescheduling:
   ```bash
   kubectl get pods -o wide
   ```
   The pods should now be running on `worker-node-2`.

---

#### **Step 4: Uncordon a Node**

1. Mark `worker-node-1` as schedulable:  
   ```bash
   kubectl uncordon worker-node-1
   ```

2. Verify the node status:  
   ```bash
   kubectl get nodes
   ```
   Output:
   ```
   NAME             STATUS    ROLES    AGE    VERSION
   master           Ready     control   10d    v1.27.4
   worker-node-1    Ready     <none>   10d    v1.27.4
   worker-node-2    Ready     <none>   10d    v1.27.4
   ```

---

### **Verification Steps**

1. **Confirm Node Status**:
   - Ensure nodes correctly reflect their schedulable or unschedulable states.  
   - Use `kubectl describe node <node-name>` to check the `Conditions` and `Taints`.

2. **Validate Pod Rescheduling**:
   - Verify that pods from drained nodes are rescheduled to other available nodes.

3. **Check Node Workloads**:
   - After uncordoning, deploy a new pod to verify it can schedule on the previously unschedulable node.

---

### **Example YAML for Pod Deployment**

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

- Deploy the pod:  
  ```bash
  kubectl apply -f sample-pod.yaml
  ```

- Confirm the pod's node placement after draining and uncordoning:
  ```bash
  kubectl get pods -o wide
  ```

---

### **Summary Table**

| **Command**       | **Purpose**                                         | **Effect on Pods**                                   | **Usage**                        |  
|--------------------|-----------------------------------------------------|-----------------------------------------------------|----------------------------------|  
| `kubectl cordon`   | Mark a node as unschedulable                        | Existing pods are unaffected; new pods aren't scheduled | Preparing a node for maintenance |  
| `kubectl drain`    | Evict pods and mark a node as unschedulable         | Running pods are rescheduled to other nodes         | Node decommissioning/upgrades    |  
| `kubectl uncordon` | Mark a node as schedulable again                    | Allows new pods to be scheduled                     | Post-maintenance actions         |  

This tutorial provides a structured, practical way to understand and apply cordon, drain, and uncordon operations in a Kubernetes cluster.
