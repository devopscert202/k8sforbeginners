# 🧩 Kubernetes DaemonSet Tutorial

## Introduction

A **DaemonSet** in Kubernetes ensures that **a specific Pod runs on every (or selected) node** in the cluster.
As new nodes are added, the DaemonSet automatically schedules Pods on them. When nodes are removed, the corresponding Pods are cleaned up.

DaemonSets are essential for **node-level workloads** where each node needs its own agent, service, or helper process.

---

## Common use cases

* **Monitoring agents**  
  Run a metrics collector (for example, Prometheus Node Exporter or a vendor agent) on each node.

* **Log collection**  
  Collect node and container logs with tools like Fluent Bit, Fluentd, or similar.

* **Networking**  
  Run node-level networking components (CNI plugins, kube-proxy, or mesh node agents).

* **Storage drivers**  
  Deploy CSI node plugins or other per-node storage helpers.

---

## Key features

* **One Pod per node** (or a subset of nodes when constrained with `nodeSelector`, affinity, or taints/tolerations).
* **Cluster lifecycle awareness**: new nodes receive Pods automatically.
* **Rolling updates**: update the DaemonSet Pod template with controlled rollouts.
* **Operational simplicity**: one declared object represents “this workload on every targeted node.”

---

## Example: minimal DaemonSet

A minimal DaemonSet runs one Pod per schedulable node that matches its placement rules:

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: node-nginx-simple
  namespace: default
  labels:
    app: node-nginx-simple
spec:
  selector:
    matchLabels:
      app: node-nginx-simple
  template:
    metadata:
      labels:
        app: node-nginx-simple
    spec:
      containers:
      - name: nginx
        image: nginx:1.25
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 80
          name: http
```

In practice you verify a DaemonSet by checking that Pod count matches the number of (eligible) nodes and that each Pod is assigned to a different node; hands-on labs cover `kubectl` inspection, updates, and cleanup.

---

## Summary

* **DaemonSets** run a Pod on **every targeted node**.
* They fit **cluster-wide agents** (monitoring, logging, networking, storage).
* They adapt automatically when nodes join or leave the cluster.
* Updates use the same controller patterns as other workloads (for example, rolling update of the Pod template).

Use a DaemonSet when you need **consistent per-node execution** rather than a fixed replica count independent of node count.

---

## Hands-On Labs

Practice these concepts with guided lab exercises:

| Lab | Description |
|-----|-------------|
| [Lab 26: DaemonSets](../../labmanuals/lab26-workload-daemonsets.md) | Deploy and inspect DaemonSets, relate Pods to nodes, and practice updates on a multi-node cluster. |
