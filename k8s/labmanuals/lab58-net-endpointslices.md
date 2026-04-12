# Lab 58: EndpointSlices — Scalable Endpoint Management

## Overview

When you create a **Service** in Kubernetes, something has to keep track of which Pods are healthy and ready to receive traffic for that Service. That "something" is an **EndpointSlice** — a Kubernetes API object that lists the real IP addresses and ports of every matching Pod behind the Service.

Think of it this way: the Service is a **published phone number**, and EndpointSlices are the **directory of actual phones** that ring when someone dials that number. Components like **kube-proxy** read EndpointSlices to build iptables/IPVS rules so traffic to the Service ClusterIP gets forwarded to a healthy Pod.

EndpointSlices are created and updated **automatically** by the EndpointSlice controller for any Service that has a `selector`. You can also author **custom** EndpointSlices to route cluster traffic to backends **outside** the cluster (an on-premises database, a legacy API, etc.) via a headless Service without a selector.

In this lab you will inspect auto-created slices, create custom ones, and learn how EndpointSlices replaced the older monolithic Endpoints object to scale to thousands of Pods efficiently.

## Prerequisites

- A running Kubernetes cluster (Minikube, Kind, or any K8s cluster)
- `kubectl` CLI tool installed and configured
- Completion of [Lab 02: Creating Services](lab02-basics-creating-services.md)
- Recommended: [Lab 35: Ingress](lab35-net-ingress.md)

## Learning Objectives

By the end of this lab, you will be able to:

- Explain how **EndpointSlices** differ from legacy **Endpoints** and why slices matter at scale
- List and inspect **auto-created** EndpointSlices for normal selector-based Services
- Create **custom** EndpointSlices for external or manually managed backends
- Interpret **topology** fields (for example `zone`, `nodeName`) and relate them to topology-aware routing
- Troubleshoot common **endpoint** and EndpointSlice association problems

---

## Repository YAML Files

Manifests used in this lab are versioned in the repository. From the repo root, you can open or apply:

- [endpointslices.yaml](../../labs/networking/endpointslices.yaml) — custom EndpointSlice example referenced in Exercise 2

---

## Concepts

### What is an EndpointSlice?

When you create a **Service** in Kubernetes, the cluster needs a way to keep track of **which Pods** are currently healthy and ready to receive traffic for that Service. That tracking is the job of **EndpointSlices**.

An **EndpointSlice** is a Kubernetes API object (API group `discovery.k8s.io/v1`) that stores a list of **backend addresses** — the IP addresses and ports of Pods that match a Service's label selector. Think of it as a directory or phone book: the Service is the published name, and the EndpointSlice is the list of actual addresses behind that name.

```
Service "my-app"  ──selector: app=my-app──►  EndpointSlice
                                              ├─ 10.244.1.5:8080  (Pod A, Ready)
                                              ├─ 10.244.2.9:8080  (Pod B, Ready)
                                              └─ 10.244.3.3:8080  (Pod C, Ready)
```

**Who uses EndpointSlices?**

- **kube-proxy** reads EndpointSlices to program iptables/IPVS rules on every node, so traffic to the Service ClusterIP gets forwarded to a healthy Pod.
- **Ingress controllers** and **service meshes** also consume EndpointSlices to build their routing tables.
- **You** can inspect EndpointSlices to answer the question: "Which Pods is this Service actually sending traffic to right now?"

**Key facts at a glance:**

| Property | Detail |
|----------|--------|
| **API group** | `discovery.k8s.io/v1` |
| **Created by** | EndpointSlice controller (part of kube-controller-manager) |
| **Linked to Service via** | Label `kubernetes.io/service-name: <svc-name>` |
| **Max endpoints per slice** | 100 (additional slices are created automatically) |
| **Address types** | IPv4, IPv6, or FQDN |
| **Stored per endpoint** | IP, port, protocol, ready/serving/terminating conditions, node name, zone |

**Automatic management:** For any Service that has a `selector`, Kubernetes creates and maintains EndpointSlices automatically. You do not need to create them yourself. As Pods are added, removed, or fail readiness probes, the EndpointSlice controller updates the slices within seconds.

**Custom EndpointSlices:** For a Service **without** a selector (a "headless external" Service), you can manually create EndpointSlices to route cluster traffic to IPs outside the cluster — for example, an on-premises database or a legacy API.

---

### Why EndpointSlices replaced legacy Endpoints

Before EndpointSlices (Kubernetes < 1.17 GA), the cluster used a single **Endpoints** object per Service. This worked fine for small Services, but had serious problems at scale:

| Problem with legacy Endpoints | How EndpointSlices solve it |
|-------------------------------|---------------------------|
| **One huge object** — A Service with 500 Pods produces a single Endpoints object with 500 entries | **Chunked into slices** — Split into 5 slices of 100 each; updates touch only the changed slice |
| **Full replacement on every change** — Adding or removing one Pod transmits the entire object | **Partial updates** — Only the affected slice is sent over the wire |
| **Watch storm** — Every kube-proxy on every node receives the full object on every Pod change | **Reduced bandwidth** — Smaller payloads mean less network churn and faster convergence |
| **No topology data** — No zone, node, or hint fields | **Topology-aware routing** — Each endpoint carries `zone`, `nodeName`, and optional `hints` for same-zone preference |
| **IPv4 only** — Dual-stack required workarounds | **Dual-stack native** — Separate slices per address family (IPv4, IPv6) |

### EndpointSlices vs Endpoints — quick comparison

| Feature | Endpoints (legacy) | EndpointSlices (current) |
|---------|-----------|----------------|
| **API** | `v1` | `discovery.k8s.io/v1` |
| **Max size** | Unlimited (one object) | 100 endpoints per slice |
| **Scalability** | Poor (>100 Pods) | Excellent (1000+ Pods) |
| **Update efficiency** | Full object replacement | Partial updates |
| **Dual-stack** | No | Yes (IPv4 + IPv6) |
| **Topology fields** | No | Yes (zone, nodeName, hints) |
| **Default since** | Always | Kubernetes 1.21+ (default for kube-proxy) |

> **Note:** Legacy `Endpoints` objects still exist for backward compatibility and are still populated by the Endpoints controller. However, kube-proxy and most modern controllers prefer EndpointSlices.

---

## Exercise 1: Understanding EndpointSlices

### Step 1: Create sample workloads and view EndpointSlices

Create two small Deployments and ClusterIP Services so the cluster generates EndpointSlices for you:

```bash
kubectl create deployment ep-demo-web --image=nginx --replicas=2
kubectl expose deployment ep-demo-web --port=80 --target-port=80 --name=ep-demo-web

kubectl create deployment ep-demo-api --image=hashicorp/http-echo --replicas=2 -- -text="ep-demo-api"
kubectl expose deployment ep-demo-api --port=5678 --target-port=5678 --name=ep-demo-api
```

Verify the workloads:

```bash
kubectl get deployments ep-demo-web ep-demo-api
kubectl get services ep-demo-web ep-demo-api
```

List EndpointSlices:

```bash
kubectl get endpointslices
```

Expected output (names and IPs will differ):

```
NAME                        ADDRESSTYPE   PORTS   ENDPOINTS                AGE
ep-demo-api-xxxxx           IPv4          5678    10.244.0.5,10.244.0.6  1m
ep-demo-web-xxxxx           IPv4          80      10.244.0.7,10.244.0.8  1m
```

**Notice**: Kubernetes automatically created EndpointSlices for your Services!

### Step 2: Compare with Traditional Endpoints

```bash
# View old-style Endpoints
kubectl get endpoints

# Compare with EndpointSlices
kubectl get endpointslices
```

Both show the same Pod IPs, but EndpointSlices provide additional metadata.

### Step 3: Examine EndpointSlice Details

```bash
kubectl describe endpointslice <endpointslice-name>
```

Tip — list slices for one Service first:

```bash
kubectl get endpointslices -l kubernetes.io/service-name=ep-demo-web
```

Look for:

- **Address Type**: IPv4 or IPv6
- **Endpoints**: List of Pod IPs with ready status
- **Ports**: Port configuration
- **Topology**: Zone/region information (cloud environments)

### Step 4: View EndpointSlice YAML

```bash
kubectl get endpointslice <endpointslice-name> -o yaml
```

Key fields:

```yaml
addressType: IPv4
endpoints:
- addresses:
  - "10.244.0.5"
  conditions:
    ready: true
    serving: true
    terminating: false
  nodeName: minikube
  targetRef:
    kind: Pod
    name: ep-demo-web-xxxxx
ports:
- name: ""
  port: 80
  protocol: TCP
```

---

## Exercise 2: Create Custom EndpointSlice

### What are Custom EndpointSlices?

Custom EndpointSlices allow you to:

- Route traffic to external services (outside cluster)
- Integrate legacy systems
- Create hybrid cloud/on-prem setups
- Implement custom load balancing

### Step 1: Navigate to Lab Directory

```bash
cd k8s/labs/networking
```

### Step 2: Review the EndpointSlice Manifest

Let's examine `endpointslices.yaml`:

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

**Understanding the manifest:**

- `apiVersion: discovery.k8s.io/v1` - EndpointSlice API
- `labels.kubernetes.io/service-name` - Associates with a Service
- `addressType: IPv4` - IP version
- `ports` - Port configuration
- `endpoints` - List of endpoint addresses
  - `addresses` - IP addresses to route to
  - `conditions.ready: true` - Endpoint is ready to receive traffic
  - `hostname`, `nodeName`, `zone` - Topology information

### Step 3: Create a Service for Custom Endpoints

First, create a Service without selector (manual endpoint management):

```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Service
metadata:
  name: endpoint-slice-example
spec:
  ports:
  - port: 80
    targetPort: 80
    protocol: TCP
EOF
```

**Note**: No `selector` - this Service won't automatically discover Pods!

### Step 4: Deploy the Custom EndpointSlice

```bash
kubectl apply -f endpointslices.yaml
```

Expected output:

```
endpointslice.discovery.k8s.io/custom-endpoint-slice created
```

### Step 5: Verify the Association

```bash
# Check the Service
kubectl get service endpoint-slice-example

# Check the EndpointSlice
kubectl get endpointslice custom-endpoint-slice

# Verify the label association
kubectl get endpointslice custom-endpoint-slice -o jsonpath='{.metadata.labels.kubernetes\.io/service-name}'
```

Expected output: `endpoint-slice-example`

### Step 6: Describe the EndpointSlice

```bash
kubectl describe endpointslice custom-endpoint-slice
```

Output shows:

```
Address Type:  IPv4
Ports:
  Name     Port  Protocol
  ----     ----  --------
  http     80    TCP
Endpoints:
  - Addresses:  172.31.2.237
    Conditions:
      Ready:    true
    Hostname:   pod-1
    NodeName:   node-1
    Zone:       us-west2-a
```

### Step 7: Test the Custom EndpointSlice (Optional)

**Note**: This will only work if 172.31.2.237 is actually reachable from your cluster!

```bash
# Try to access the service
kubectl run test --image=busybox --rm -it --restart=Never -- wget -qO- http://endpoint-slice-example
```

If the IP is not reachable, you'll see a timeout (expected for this example).

### Step 8: Create a Working Example with Real Endpoints

Let's create a practical example:

```bash
# Create a deployment
kubectl create deployment web --image=nginx --replicas=2

# Get Pod IPs
kubectl get pods -l app=web -o wide

# Create Service without selector
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Service
metadata:
  name: manual-service
spec:
  ports:
  - port: 80
    targetPort: 80
EOF

# Create EndpointSlice with actual Pod IPs
POD_IP_1=$(kubectl get pod -l app=web -o jsonpath='{.items[0].status.podIP}')
POD_IP_2=$(kubectl get pod -l app=web -o jsonpath='{.items[1].status.podIP}')

cat <<EOF | kubectl apply -f -
apiVersion: discovery.k8s.io/v1
kind: EndpointSlice
metadata:
  name: manual-endpoints
  labels:
    kubernetes.io/service-name: manual-service
addressType: IPv4
ports:
- name: http
  protocol: TCP
  port: 80
endpoints:
- addresses:
  - "$POD_IP_1"
  conditions:
    ready: true
- addresses:
  - "$POD_IP_2"
  conditions:
    ready: true
EOF
```

Test it:

```bash
kubectl run test --image=busybox --rm -it --restart=Never -- wget -qO- http://manual-service
```

This should work! Traffic routes through the Service to the manually configured endpoints.

---

## Exercise 3: EndpointSlice Use Cases

### Use Case 1: External Database Service

Route traffic to external database:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: external-postgres
spec:
  ports:
  - port: 5432
    protocol: TCP
---
apiVersion: discovery.k8s.io/v1
kind: EndpointSlice
metadata:
  name: external-postgres-endpoints
  labels:
    kubernetes.io/service-name: external-postgres
addressType: IPv4
ports:
- port: 5432
  protocol: TCP
endpoints:
- addresses:
  - "192.168.1.50"  # External database IP
  conditions:
    ready: true
```

**Use case**: Legacy database that can't run in Kubernetes

### Use Case 2: Multi-Region Service

Create geo-distributed endpoints:

```yaml
apiVersion: discovery.k8s.io/v1
kind: EndpointSlice
metadata:
  name: global-api-us-west
  labels:
    kubernetes.io/service-name: global-api
addressType: IPv4
ports:
- port: 443
  protocol: TCP
endpoints:
- addresses:
  - "10.1.0.50"
  conditions:
    ready: true
  zone: us-west-1a
---
apiVersion: discovery.k8s.io/v1
kind: EndpointSlice
metadata:
  name: global-api-us-east
  labels:
    kubernetes.io/service-name: global-api
addressType: IPv4
ports:
- port: 443
  protocol: TCP
endpoints:
- addresses:
  - "10.2.0.50"
  conditions:
    ready: true
  zone: us-east-1a
```

**Use case**: Multi-region failover, topology-aware routing

### Use Case 3: Hybrid Cloud

Mix in-cluster and external endpoints:

```yaml
apiVersion: discovery.k8s.io/v1
kind: EndpointSlice
metadata:
  name: hybrid-service
  labels:
    kubernetes.io/service-name: hybrid-app
addressType: IPv4
ports:
- port: 8080
  protocol: TCP
endpoints:
- addresses:
  - "10.244.0.10"  # In-cluster Pod
  conditions:
    ready: true
  nodeName: k8s-node-1
- addresses:
  - "192.168.1.100"  # On-prem server
  conditions:
    ready: true
```

**Use case**: Gradual migration to Kubernetes

---

## Lab Cleanup

Remove EndpointSlice lab resources:

```bash
# Sample workloads from Exercise 1
kubectl delete deployment ep-demo-web ep-demo-api web --ignore-not-found=true
kubectl delete service ep-demo-web ep-demo-api endpoint-slice-example manual-service --ignore-not-found=true

# Custom / manual EndpointSlices
kubectl delete endpointslice custom-endpoint-slice manual-endpoints --ignore-not-found=true

# Verify cleanup
kubectl get all,endpointslice
```

---

## Troubleshooting Guide

### EndpointSlice Issues

#### Issue 1: Service not routing to endpoints

**Diagnosis:**

```bash
# Check EndpointSlice exists
kubectl get endpointslice

# Check label matches service name
kubectl get endpointslice <name> -o jsonpath='{.metadata.labels.kubernetes\.io/service-name}'

# Verify endpoint IPs are reachable
kubectl run test --image=busybox --rm -it -- ping <endpoint-ip>
```

**Solutions:**

- Verify `kubernetes.io/service-name` label matches Service name exactly
- Ensure endpoint IPs are reachable from cluster
- Check `conditions.ready: true` is set

---

## Key Takeaways

1. **EndpointSlices** are the modern replacement for Endpoints
2. Scales better for large deployments (100+ Pods)
3. More efficient updates (partial vs full)
4. Supports **topology-aware routing** (zones, regions)
5. Custom EndpointSlices enable **external service integration**
6. Label `kubernetes.io/service-name` associates with Service
7. Use for **hybrid cloud**, **legacy integration**, **external services**

---

## Best Practices

### EndpointSlice Best Practices

1. **Let Kubernetes manage when possible** - Don't create custom unless needed

2. **Use for external services only**

```yaml
# Good: external database
- addresses: ["192.168.1.50"]

# Bad: in-cluster Pods (use Service selector instead)
```

3. **Set ready conditions properly**

```yaml
conditions:
  ready: true      # Endpoint can receive traffic
  serving: true    # Endpoint is serving requests
  terminating: false  # Endpoint is not shutting down
```

4. **Include topology information**

```yaml
zone: us-west-1a
nodeName: node-1
```

5. **Monitor endpoint health**

```bash
kubectl get endpointslice -w
```

---

## Additional Commands Reference

```bash
# EndpointSlice commands
kubectl get endpointslices
kubectl describe endpointslice <name>
kubectl get endpointslice <name> -o yaml

# Watch endpoint changes
kubectl get endpointslice -w

# Filter by service
kubectl get endpointslice -l kubernetes.io/service-name=myservice

# Debug tools
kubectl run netshoot --rm -it --image=nicolaka/netshoot -- bash
# Inside pod: curl, dig, nslookup, traceroute, etc.
```

---

## Next Steps

1. **HTTP routing**: Continue with [Lab 35: Ingress](lab35-net-ingress.md) for Ingress controllers and L7 routing
2. **Services**: Deepen Service patterns in [Lab 34: Multi-Port Services](lab34-net-multi-port-services.md)
3. **Modern ingress**: Explore [Lab 44: Gateway API](lab44-net-gateway-api.md) for Gateway API and HTTPRoute

---

## Additional Reading

- [EndpointSlices Documentation](https://kubernetes.io/docs/concepts/services-networking/endpoint-slices/)
- [Topology Aware Routing](https://kubernetes.io/docs/concepts/services-networking/topology-aware-routing/)

---

**Lab Created**: March 2026  
**Compatible with**: Kubernetes 1.24+  
**Tested on**: Minikube, Kind, AWS EKS, GCP GKE
