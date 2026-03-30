# **Practical Guide to Affinity and Anti-Affinity in Kubernetes Scheduling**

In Kubernetes, **affinity** and **anti-affinity** are powerful features used to control the scheduling of pods based on node labels or other pod characteristics. They help ensure that your pods are scheduled on appropriate nodes or are placed in specific patterns, such as ensuring that certain pods don’t share the same node or that they are co-located for performance reasons.

This guide will walk through the concepts, usage, and a practical example involving **node affinity** and **pod affinity/anti-affinity**, using two worker nodes (`worker-node-1` and `worker-node-2`) to demonstrate their effectiveness.

---

## **1. Understanding Affinity and Anti-Affinity**

### **Node Affinity**
Node affinity allows you to control where a pod is scheduled based on the labels assigned to the nodes in your cluster. This is equivalent to "nodeSelector" but more flexible and expressive.

#### **Types of Node Affinity**:
1. **RequiredDuringSchedulingIgnoredDuringExecution**: The pod will only be scheduled on nodes that match the specified criteria. If no matching nodes are found, the pod won’t be scheduled.
2. **PreferredDuringSchedulingIgnoredDuringExecution**: Kubernetes will attempt to schedule the pod on nodes that match the specified criteria, but it is not mandatory. If no matching nodes are found, the pod will still be scheduled on other available nodes.

### **Pod Affinity**
Pod affinity allows you to specify that a pod should be scheduled on the same node or in the same topology domain as another pod, based on labels.

### **Pod Anti-Affinity**
Pod anti-affinity allows you to specify that a pod should **not** be scheduled on the same node or in the same topology domain as other specific pods.

### **Why are Affinity and Anti-Affinity Important?**
- **Affinity** can be used to ensure that pods that need to communicate with each other frequently are scheduled on the same node or in close proximity (e.g., for low-latency communication).
- **Anti-affinity** helps avoid scheduling pods that should not share the same node or failover domain (e.g., avoiding two replicas of a critical application being scheduled on the same node).

### **When to Use Them?**
- **Node Affinity**: When you need to target specific nodes based on their hardware, OS, or any other labeling criteria.
- **Pod Affinity**: When certain pods need to run together, such as a front-end and back-end application that require fast communication.
- **Pod Anti-Affinity**: When you want to spread replicas of a service across nodes to improve availability, or ensure that certain pods don’t share a node.

---

## **2. Syntax for Affinity and Anti-Affinity**

### **Node Affinity Example Syntax**

```yaml
affinity:
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
      - matchExpressions:
        - key: <key>
          operator: In
          values:
          - <value>
```

### **Pod Affinity Example Syntax**

```yaml
affinity:
  podAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      labelSelector:
        matchExpressions:
        - key: <key>
          operator: In
          values:
          - <value>
    topologyKey: <topologyKey>
```

### **Pod Anti-Affinity Example Syntax**

```yaml
affinity:
  podAntiAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      labelSelector:
        matchExpressions:
        - key: <key>
          operator: In
          values:
          - <value>
    topologyKey: <topologyKey>
```

---

## **3. Practical Example: Scheduling with Affinity and Anti-Affinity**

Let’s set up a scenario with two nodes (`worker-node-1` and `worker-node-2`) and show how affinity and anti-affinity can be applied to control where pods are scheduled.

### **Scenario**:
- **Node Labels**: `worker-node-1` has the label `env=production`, and `worker-node-2` has the label `env=staging`.
- **Pod Affinity**: We will ensure that a certain pod can only be scheduled on `worker-node-1` because it’s for production.
- **Pod Anti-Affinity**: We will ensure that another pod does not get scheduled on `worker-node-1`, as it is critical to avoid putting too many replicas of the same application on that node.

### **Step 1: Label the Nodes**

Label the nodes so we can apply affinity based on these labels.

```bash
kubectl label nodes worker-node-1 env=production
kubectl label nodes worker-node-2 env=staging
```

### **Step 2: Create Pod with Node Affinity (Production)**

We will create a pod that will only be scheduled on `worker-node-1`, where the `env=production` label is applied.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: production-pod
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: env
            operator: In
            values:
            - production
  containers:
  - name: nginx
    image: nginx
```

### **Step 3: Create Pod with Pod Anti-Affinity (Avoiding Same Node)**

Label the pods so we can apply anti-affinity based on these labels.

```bash
kubectl label pods production-pod env=production
```

Next, we will create another pod that should not be scheduled on the same node as the `production-pod`. This is achieved using pod anti-affinity.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: anti-affinity-pod
spec:
  affinity:
    podAntiAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchExpressions:
          - key: "env"
            operator: In
            values:
            - production
        topologyKey: kubernetes.io/hostname
  containers:
  - name: nginx
    image: nginx
```

In this example, we are specifying that the pod with the label `env=production` (from the first pod) should not be scheduled on the same node as the new pod, which is enforcing **anti-affinity**.

### **Step 4: Apply the Pods**

```bash
kubectl apply -f production-pod.yaml
kubectl apply -f anti-affinity-pod.yaml
```

### **Step 5: Verify Pod Scheduling**

To verify that the affinity and anti-affinity have been applied correctly, check where the pods are running.

```bash
kubectl get pods -o wide
```

The `production-pod` should be scheduled on `worker-node-1` because of the node affinity rule. The `anti-affinity-pod` should be scheduled on `worker-node-2` because of the pod anti-affinity rule, ensuring it does not run on the same node as the `production-pod`.

---

## **4. Verifying Affinity and Anti-Affinity in Effect**

After deploying the pods, use the following commands to verify that everything is working as expected:

1. **Check the Nodes**:
   Verify the node labels to ensure they are correctly applied:
   ```bash
   kubectl get nodes --show-labels
   ```

2. **Check Pod Scheduling**:
   Verify the pods’ scheduling:
   ```bash
   kubectl get pods -o wide
   ```

   The pods should be scheduled on different nodes based on the affinity and anti-affinity rules.

3. **Check Pod Events**:
   If the pods are not scheduled as expected, you can check events to see why:
   ```bash
   kubectl describe pod <pod-name>
   ```

   This will show if there were issues with the scheduling due to affinity or anti-affinity constraints.

---

## **5. Summary of Affinity and Anti-Affinity Use Cases**

| **Scenario**                            | **Affinity Type**                       | **Example**                                                               |
|-----------------------------------------|-----------------------------------------|---------------------------------------------------------------------------|
| **Schedule pods on a specific node**    | Node Affinity                           | Use node labels (e.g., `env=production`) to schedule pods on a specific node. |
| **Ensure pods run together**            | Pod Affinity                            | Use pod affinity to co-locate pods for faster communication (e.g., front-end and back-end). |
| **Ensure pods don’t run together**      | Pod Anti-Affinity                       | Use pod anti-affinity to avoid running multiple replicas of a service on the same node. |
| **Prevent resource contention**         | Pod Anti-Affinity (with `topologyKey`)  | Use pod anti-affinity to spread replicas across different zones or nodes for high availability. |

---

### **Conclusion**

This practical guide provides a detailed explanation of **affinity** and **anti-affinity** in Kubernetes scheduling. These features help control where pods are scheduled, ensuring your workloads are distributed efficiently based on your specific needs. Through the examples with **node affinity**, **pod affinity**, and **pod anti-affinity**, you can now understand how to manage pod placement effectively in a Kubernetes cluster.

