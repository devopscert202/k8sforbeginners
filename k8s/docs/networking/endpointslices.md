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

#### **Illustrative Service-backed workload**

A Deployment (or other workload) labeled to match the Service selector is what populates slices automatically. The exact image and replica count are arbitrary; the important part is consistent labels between Pods and the Service `selector`.

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

#### **Custom EndpointSlice (external backends)**

For a Service **without** a selector, you can author EndpointSlices that point at **external** IPs or FQDNs. The slice must carry the `kubernetes.io/service-name` label matching the Service name.

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
      - "203.0.113.10"
    conditions:
      ready: true
    hostname: external-backend-1
    nodeName: node-1
    zone: us-west2-a
```

*(Replace addresses and topology fields with values valid in your environment.)*

#### **Troubleshooting (conceptual)**

- **No EndpointSlice for a Service with a selector**: Confirm the EndpointSlice controller is running, the Service type is supported, and the API group `discovery.k8s.io` is available.
- **Backends missing from slices**: Check Pod labels against the Service selector, readiness probes, and Pod phase; only ready endpoints should appear as serving traffic.
- **Custom slice not associated**: Validate the `kubernetes.io/service-name` label, `addressType`, and that the parent Service exists and matches the intended routing pattern.

---

## Hands-On Labs

Practice these concepts with guided lab exercises:

| Lab | Description |
|-----|-------------|
| [Lab 58: EndpointSlices — Scalable Endpoint Management](../../labmanuals/lab58-net-endpointslices.md) | Inspect auto-generated slices, custom EndpointSlices, and troubleshooting. |
