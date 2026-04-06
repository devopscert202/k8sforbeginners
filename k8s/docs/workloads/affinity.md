# **Practical Guide to Affinity and Anti-Affinity in Kubernetes Scheduling**

In Kubernetes, **affinity** and **anti-affinity** are powerful features used to control the scheduling of pods based on node labels or other pod characteristics. They help ensure that your pods are scheduled on appropriate nodes or are placed in specific patterns, such as ensuring that certain pods don’t share the same node or that they are co-located for performance reasons.

This guide explains the concepts, syntax, and typical scheduling patterns—often illustrated with two worker nodes (`worker-node-1` and `worker-node-2`) so you can reason about placement and failure domains.

---

## **1. Understanding Affinity and Anti-Affinity**

### **Node Affinity**
Node affinity allows you to control where a pod is scheduled based on the labels assigned to the nodes in your cluster. This is equivalent to `nodeSelector` but more flexible and expressive.

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

## **3. Example Scenario: Node and Pod Anti-Affinity**

Consider nodes labeled by environment—for example, `worker-node-1` with `env=production` and `worker-node-2` with `env=staging`. You might pin a workload to production nodes using **node affinity**, while using **pod anti-affinity** so another workload does not land on the same host as an existing production pod (spreading replicas for availability).

**Node affinity (production node only):**

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

**Pod anti-affinity (avoid same node as pods matching a label, using hostname topology):**

After the first pod exists, a second pod can declare anti-affinity against pods labeled `env=production` so the scheduler prefers a different node:

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

To make pod-to-pod rules meaningful, pods need labels the selector can match (for example `env=production` on the first pod). In real clusters you verify placement with `kubectl get pods -o wide`, describe events on unschedulable pods, and inspect node labels—those operational checks belong in hands-on labs.

---

## **4. Summary of Affinity and Anti-Affinity Use Cases**

| **Scenario**                            | **Affinity Type**                       | **Example**                                                               |
|-----------------------------------------|-----------------------------------------|---------------------------------------------------------------------------|
| **Schedule pods on a specific node**    | Node Affinity                           | Use node labels (e.g., `env=production`) to schedule pods on a specific node. |
| **Ensure pods run together**            | Pod Affinity                            | Use pod affinity to co-locate pods for faster communication (e.g., front-end and back-end). |
| **Ensure pods don’t run together**      | Pod Anti-Affinity                       | Use pod anti-affinity to avoid running multiple replicas of a service on the same node. |
| **Prevent resource contention**         | Pod Anti-Affinity (with `topologyKey`)  | Use pod anti-affinity to spread replicas across different zones or nodes for high availability. |

---

### **Conclusion**

**Affinity** and **anti-affinity** control where pods are scheduled relative to nodes and to each other. **Node affinity** targets node labels; **pod affinity** and **pod anti-affinity** express co-location or separation across a **topology** (such as hostname or zone). Used together, they help you balance performance, isolation, and high availability.

---

## Hands-On Labs

Practice these concepts with guided lab exercises:

| Lab | Description |
|-----|-------------|
| [Lab 18: Pod Scheduling with Node and Pod Affinity](../../labmanuals/lab18-sched-affinity-antiaffinity.md) | Node affinity, pod affinity/anti-affinity, and scheduling verification on a multi-node cluster. |
