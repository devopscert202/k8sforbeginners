### **What is an EndpointSlice?**

When you create a **Service** in Kubernetes, the cluster needs to know **which Pods** are healthy and ready to receive traffic for that Service. That tracking is the job of **EndpointSlices**.

An **EndpointSlice** is a Kubernetes API object (`discovery.k8s.io/v1`) that stores a list of **backend addresses** — the IP addresses and ports of Pods that match a Service's label selector. Think of it as a directory or phone book: the Service is the published name, and the EndpointSlice is the list of actual addresses behind that name.

```
Service "my-app"  ──selector: app=my-app──►  EndpointSlice
                                              ├─ 10.244.1.5:8080  (Pod A, Ready)
                                              ├─ 10.244.2.9:8080  (Pod B, Ready)
                                              └─ 10.244.3.3:8080  (Pod C, Ready)
```

**Who creates them?** For any Service that has a `selector`, the **EndpointSlice controller** (part of kube-controller-manager) creates and maintains slices automatically. As Pods are added, removed, or fail readiness probes, the controller updates the slices within seconds.

**Who reads them?** **kube-proxy** reads EndpointSlices to program iptables/IPVS rules on every node, so traffic to the Service ClusterIP gets forwarded to a healthy Pod. Ingress controllers and service meshes also consume EndpointSlices.

**Why not just Endpoints?** Before EndpointSlices (Kubernetes < 1.17 GA), a single monolithic **Endpoints** object per Service stored all backend IPs. This worked for small Services, but a Service with 500 Pods produced one huge object — every Pod change retransmitted the entire list to every kube-proxy. EndpointSlices solve this by splitting backends into **chunks of up to 100**, supporting **partial updates**, and carrying **topology metadata** (zone, node) for smarter routing.

#### **Key facts at a glance**

| Property | Detail |
|----------|--------|
| **API group** | `discovery.k8s.io/v1` |
| **Created by** | EndpointSlice controller (kube-controller-manager) |
| **Linked to Service via** | Label `kubernetes.io/service-name: <svc-name>` |
| **Max endpoints per slice** | 100 (additional slices are created automatically) |
| **Address types** | IPv4, IPv6, or FQDN |
| **Stored per endpoint** | IP, port, protocol, ready/serving/terminating conditions, nodeName, zone |
| **Default since** | Kubernetes 1.21+ (kube-proxy default) |

#### **When to Use EndpointSlice?**
- EndpointSlices are used **automatically** by every modern Kubernetes cluster — you don't opt in.
- **Custom EndpointSlices** are useful when routing cluster traffic to external backends (on-premises databases, legacy APIs) via a headless Service without a selector.
- Understanding EndpointSlices helps debug "Service has no endpoints" problems and reason about topology-aware routing.

---

### **Lab Setup**

#### **Prerequisites**
- A Kubernetes cluster running (e.g., GKE, kubeadm-based, etc.).
- Tools: `kubectl`, `kubeadm`, `kubelet`, and `containerd`.
- Basic understanding of Kubernetes YAML files.

---

### **Steps**

#### **1. Create a Deployment and Identify its EndpointSlice**

1.1 **Create the Deployment YAML File**  
Save the following content to `frontend-app.yaml`:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend-app
spec:
  replicas: 3
  selector:
    matchLabels:
      run: frontend-app
  template:
    metadata:
      labels:
        run: frontend-app
    spec:
      containers:
      - name: frontend-app
        image: nginx:1.16.1
        ports:
        - containerPort: 80
```

1.2 **Apply the Deployment YAML**:
```bash
kubectl apply -f frontend-app.yaml
```

1.3 **Check Deployment Status**:
```bash
kubectl get deploy frontend-app
kubectl get pods -l run=frontend-app
```

1.4 **Expose the Deployment as a Service**:
```bash
kubectl expose deploy frontend-app --port 80 --target-port 80
```

1.5 **Identify the Service Endpoints**:
```bash
kubectl get svc frontend-app
kubectl get endpointslices
```
You’ll notice an EndpointSlice (e.g., `frontend-app-xyz12`) created for the service.

1.6 **Inspect EndpointSlice Details**:
```bash
kubectl get endpointslices <endpoint-slice-name> -o yaml
```

---

#### **2. Create a Custom EndpointSlice**

2.1 **Create a YAML File for Custom EndpointSlice Configuration**  
Save the following content to `endpoint-slice.yaml`:
```yaml
apiVersion: discovery.k8s.io/v1
kind: EndpointSlice
metadata:
  name: custom-endpoint-slice
  labels:
    kubernetes.io/service-name: endpoint-slice-example
addressType: IPv4
ports:
  - name: http
    protocol: TCP
    port: 80
endpoints:
  - addresses:
      - "172.31.2.237"
    conditions:
      ready: true
    hostname: pod-1
    nodeName: node-1
    zone: us-west2-a
```

2.2 **Apply the EndpointSlice YAML**:
```bash
kubectl apply -f endpoint-slice.yaml
```

2.3 **Verify the Resource**:
```bash
kubectl get endpointslices
kubectl describe endpointslices custom-endpoint-slice
```

---

#### **3. Troubleshooting**

- **Issue: EndpointSlice Not Created Automatically**
  - Ensure your cluster has EndpointSlice feature gate enabled.
  - Check service configuration; ensure it references `ClusterIP` or `LoadBalancer`.

- **Issue: Pods Not Listed in EndpointSlice**
  - Confirm pods are labeled correctly (`run: frontend-app`).
  - Check if the pods are healthy (`kubectl get pods`).
  
- **Issue: Custom EndpointSlice Not Applied**
  - Check YAML for errors (`kubectl describe` will provide details).
  - Ensure IP and node values are correct.

---

By following the steps above, you’ll learn how to configure EndpointSlice effectively, verify its creation, and troubleshoot common issues. Would you like to dive deeper into any part of this tutorial?
