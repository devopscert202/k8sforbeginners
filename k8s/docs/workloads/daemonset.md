# 🧩 Kubernetes DaemonSet Tutorial

## 📌 Introduction

A **DaemonSet** in Kubernetes ensures that **a specific pod runs on every (or selected) node** in the cluster.
As new nodes are added, the DaemonSet automatically schedules pods on them. When nodes are removed, the corresponding pods are cleaned up.

DaemonSets are essential for **node-level workloads** where each node needs its own agent, service, or helper process.

---

## 🔧 Common Use Cases

* **Monitoring agents**
  Run a metrics collector (e.g., Prometheus Node Exporter, Datadog Agent) on each node.

* **Log collection**
  Collect node and container logs with tools like Fluentd, Filebeat, or Logstash.

* **Networking**
  Run node-level networking agents (CNI plugins, kube-proxy, service mesh sidecars).

* **Storage drivers**
  Deploy CSI (Container Storage Interface) node components that manage storage volumes.

---

## ⭐ Key Features of DaemonSets

* **One pod per node** (or subset of nodes if `nodeSelector`/affinity used).
* **Auto-updates with cluster changes**: new nodes get pods automatically.
* **Rolling updates** supported (update DaemonSet image with minimal disruption).
* **Simplifies management** of cluster-wide node agents.

---

## 📝 Example: Minimal DaemonSet

Here’s a simple `DaemonSet` that deploys `nginx` on every schedulable node.

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

---

## 🚀 Step 1: Create the DaemonSet

Save the manifest as `daemonset-simple.yaml` and apply it:

```bash
kubectl apply -f daemonset-simple.yaml
```

---

## 🔍 Step 2: Verify the DaemonSet

Check the DaemonSet status:

```bash
kubectl get daemonset node-nginx-simple
```

List the pods created:

```bash
kubectl get pods -l app=node-nginx-simple -o wide
```

👉 You should see **one pod per node**.

Describe the DaemonSet for more details:

```bash
kubectl describe daemonset node-nginx-simple
```

---

## 🧪 Step 3: Test the DaemonSet

Pick any pod name:

```bash
POD=$(kubectl get pods -l app=node-nginx-simple -o jsonpath='{.items[0].metadata.name}')
```

Forward port `80` from that pod to your local machine:

```bash
kubectl port-forward "$POD" 8080:80
```

Open another terminal and test:

```bash
curl -sI http://localhost:8080 | head -n 1
# Expected: HTTP/1.1 200 OK
```

Stop the port-forward with `CTRL+C`.

---

## 🧹 Step 4: Cleanup

Delete the DaemonSet:

```bash
kubectl delete -f daemonset-simple.yaml
```

Verify pods are gone:

```bash
kubectl get pods -l app=node-nginx-simple
```

---

## 📖 Summary

* **DaemonSets** run a pod on **every node** (or selected nodes).
* Useful for **cluster-wide agents** (monitoring, logging, networking, storage).
* Automatically adapts when nodes are added or removed.
* Simple to manage and update via `kubectl set image` and rolling updates.
* The example showed how to deploy an `nginx` container as a DaemonSet, verify it, test accessibility, and clean up.

👉 Use DaemonSets whenever you need **node-level consistency** in your Kubernetes cluster.

