# Lab 31: Kubernetes Metrics Server

## Overview
In this lab, you will learn about the Kubernetes Metrics Server, a cluster-wide aggregator of resource usage data. The Metrics Server collects resource metrics from Kubelets and exposes them through the Kubernetes API server for use by Horizontal Pod Autoscaler (HPA), Vertical Pod Autoscaler (VPA), and kubectl top commands. You'll install the Metrics Server, configure it for different environments, and use it to monitor cluster resource usage.

## Prerequisites
- A running Kubernetes cluster (Minikube, Kind, or any K8s cluster)
- `kubectl` CLI tool installed and configured
- Cluster admin access
- Basic understanding of Pods and Deployments (Lab 01)
- Understanding of Kubernetes architecture

## Learning Objectives
By the end of this lab, you will be able to:
- Understand the Metrics Server architecture and purpose
- Install and configure Metrics Server
- Use kubectl top commands to monitor resources
- Troubleshoot Metrics Server issues
- Configure Metrics Server for different environments
- Understand resource metrics collection
- Enable resource monitoring for autoscaling

---

## What is Kubernetes Metrics Server?

**Metrics Server** is a scalable, efficient source of container resource metrics for Kubernetes built-in autoscaling pipelines. It collects resource metrics from Kubelets and exposes them in Kubernetes API server through Metrics API.

### Key Characteristics

- **Cluster-Wide Aggregator**: Collects metrics from all nodes
- **Resource Metrics**: Focuses on CPU and memory usage
- **Short-Term Storage**: Stores metrics in memory (not persistent)
- **Metrics API**: Exposes metrics through standard Kubernetes API
- **Autoscaling Foundation**: Required for HPA and VPA
- **Lightweight**: Low resource overhead

### Architecture

```
┌─────────────────────────────────────────────────┐
│           Kubernetes API Server                 │
│  ┌──────────────────────────────────────────┐  │
│  │        Metrics API Extension             │  │
│  └──────────────────────────────────────────┘  │
└─────────────────┬───────────────────────────────┘
                  │
         ┌────────▼────────┐
         │  Metrics Server │
         │  - Aggregates   │
         │  - Processes    │
         │  - Exposes      │
         └────────┬────────┘
                  │
     ┌────────────┼────────────┐
     │            │            │
┌────▼────┐  ┌───▼─────┐  ┌──▼──────┐
│ Kubelet │  │ Kubelet │  │ Kubelet │
│ (Node1) │  │ (Node2) │  │ (Node3) │
└─────────┘  └─────────┘  └─────────┘
```

### Metrics Server vs Monitoring Solutions

| Feature | Metrics Server | Prometheus | Full Monitoring |
|---------|----------------|------------|-----------------|
| **Purpose** | Resource metrics | Time-series DB | Complete observability |
| **Storage** | In-memory | Persistent | Long-term storage |
| **Metrics** | CPU, Memory | Custom metrics | All metrics |
| **Retention** | Few minutes | Configurable | Days/Months |
| **Use Case** | Autoscaling | Monitoring | Analytics |
| **Resource Usage** | Low | Medium | High |

### Common Use Cases

1. **Horizontal Pod Autoscaling**: Scale Pods based on CPU/memory
2. **Vertical Pod Autoscaling**: Right-size container resources
3. **kubectl top Commands**: View resource usage
4. **Capacity Planning**: Monitor cluster resource utilization
5. **Resource Monitoring**: Track Pod and node metrics

---

## Exercise 1: Check Existing Metrics Server Installation

### Step 1: Check if Metrics Server Exists

```bash
kubectl get deployment metrics-server -n kube-system
```

If installed, you'll see:
```
NAME             READY   UP-TO-DATE   AVAILABLE   AGE
metrics-server   1/1     1            1           5d
```

If not installed:
```
Error from server (NotFound): deployments.apps "metrics-server" not found
```

### Step 2: Check Metrics API Availability

```bash
kubectl get apiservice v1beta1.metrics.k8s.io -o yaml
```

Look for the status:
```yaml
status:
  conditions:
  - lastTransitionTime: "2026-03-16T10:00:00Z"
    message: all checks passed
    reason: Passed
    status: "True"
    type: Available
```

### Step 3: Test kubectl top Commands

Try to view node metrics:

```bash
kubectl top nodes
```

If Metrics Server is working:
```
NAME           CPU(cores)   CPU%   MEMORY(bytes)   MEMORY%
controlplane   150m         7%     1200Mi          30%
node01         100m         5%     800Mi           20%
```

If not working:
```
error: Metrics API not available
```

Try to view Pod metrics:

```bash
kubectl top pods -A
```

---

## Exercise 2: Install Metrics Server

### Step 1: Download the Official Manifest

For production clusters with valid TLS certificates:

```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

Expected output:
```
serviceaccount/metrics-server created
clusterrole.rbac.authorization.k8s.io/system:aggregated-metrics-reader created
clusterrole.rbac.authorization.k8s.io/system:metrics-server created
rolebinding.rbac.authorization.k8s.io/metrics-server-auth-reader created
clusterrolebinding.rbac.authorization.k8s.io/metrics-server:system:auth-delegator created
clusterrolebinding.rbac.authorization.k8s.io/system:metrics-server created
service/metrics-server created
deployment.apps/metrics-server created
apiservice.apiregistration.k8s.io/v1beta1.metrics.k8s.io created
```

### Step 2: Verify Installation

Check the deployment:

```bash
kubectl get deployment metrics-server -n kube-system
```

Check the Pods:

```bash
kubectl get pods -n kube-system -l k8s-app=metrics-server
```

Expected output:
```
NAME                              READY   STATUS    RESTARTS   AGE
metrics-server-7b4f8b595f-xxxxx   1/1     Running   0          1m
```

### Step 3: Check Logs

View Metrics Server logs:

```bash
kubectl logs -n kube-system -l k8s-app=metrics-server
```

Successful logs should show:
```
I0316 10:00:00.000000       1 serving.go:342] Generated self-signed cert
I0316 10:00:00.000000       1 secure_serving.go:266] Serving securely on [::]:4443
```

---

## Exercise 3: Configure Metrics Server for Local Development

For local Kubernetes clusters (Minikube, Kind, Docker Desktop) that use self-signed certificates, you need to configure Metrics Server to skip TLS verification.

### Step 1: Review the Patch Configuration

Navigate to the workloads directory:
```bash
cd k8s/labs/workloads
```

View `k8s-metrics-server.patch.yaml`:

```yaml
spec:
  template:
    spec:
      containers:
      - name: metrics-server
        command:
        - /metrics-server
        - --kubelet-insecure-tls
        - --kubelet-preferred-address-types=InternalIP
```

**Understanding the configuration:**

- `--kubelet-insecure-tls`: Skip TLS certificate verification (development only)
- `--kubelet-preferred-address-types=InternalIP`: Use internal IP to communicate with Kubelets

**Security Note**: Never use `--kubelet-insecure-tls` in production environments!

### Step 2: Apply the Patch

Using kubectl patch command:

```bash
kubectl patch deployment metrics-server -n kube-system --type='json' -p='[
  {
    "op": "add",
    "path": "/spec/template/spec/containers/0/args/-",
    "value": "--kubelet-insecure-tls"
  },
  {
    "op": "add",
    "path": "/spec/template/spec/containers/0/args/-",
    "value": "--kubelet-preferred-address-types=InternalIP"
  }
]'
```

Expected output:
```
deployment.apps/metrics-server patched
```

Alternative method using the patch file:

```bash
kubectl patch deployment metrics-server -n kube-system --patch-file k8s-metrics-server.patch.yaml
```

### Step 3: Verify Patch Applied

Check the deployment configuration:

```bash
kubectl get deployment metrics-server -n kube-system -o yaml | grep -A 5 args
```

You should see:
```yaml
args:
- --cert-dir=/tmp
- --secure-port=4443
- --kubelet-preferred-address-types=InternalIP,ExternalIP,Hostname
- --kubelet-use-node-status-port
- --metric-resolution=15s
- --kubelet-insecure-tls
- --kubelet-preferred-address-types=InternalIP
```

### Step 4: Wait for Rollout

Wait for the new Pod to be ready:

```bash
kubectl rollout status deployment metrics-server -n kube-system
```

Expected output:
```
deployment "metrics-server" successfully rolled out
```

---

## Exercise 4: Using kubectl top Commands

### Step 1: View Node Metrics

Wait 30-60 seconds after Metrics Server starts, then:

```bash
kubectl top nodes
```

Expected output:
```
NAME           CPU(cores)   CPU%   MEMORY(bytes)   MEMORY%
controlplane   150m         7%     1200Mi          30%
node01         100m         5%     800Mi           20%
```

**Understanding the output:**
- `CPU(cores)`: Actual CPU usage in millicores
- `CPU%`: Percentage of allocatable CPU
- `MEMORY(bytes)`: Actual memory usage
- `MEMORY%`: Percentage of allocatable memory

View with additional details:

```bash
kubectl top nodes --sort-by=memory
kubectl top nodes --sort-by=cpu
```

### Step 2: View Pod Metrics

View all Pods across namespaces:

```bash
kubectl top pods -A
```

View Pods in specific namespace:

```bash
kubectl top pods -n kube-system
```

Expected output:
```
NAME                              CPU(cores)   MEMORY(bytes)
coredns-5d78c9869d-xxxxx          3m           12Mi
etcd-controlplane                 25m          50Mi
kube-apiserver-controlplane       60m          250Mi
kube-controller-manager           40m          45Mi
kube-scheduler-controlplane       5m           20Mi
metrics-server-7b4f8b595f-xxxxx   4m           15Mi
```

Sort by resource usage:

```bash
kubectl top pods -A --sort-by=cpu
kubectl top pods -A --sort-by=memory
```

### Step 3: View Container Metrics

View metrics for containers within Pods:

```bash
kubectl top pods -n kube-system --containers
```

Expected output:
```
POD                               NAME                      CPU(cores)   MEMORY(bytes)
coredns-5d78c9869d-xxxxx          coredns                   3m           12Mi
etcd-controlplane                 etcd                      25m          50Mi
kube-apiserver-controlplane       kube-apiserver            60m          250Mi
```

### Step 4: Filter Pods with Labels

View metrics for specific application:

```bash
kubectl top pods -l app=nginx
kubectl top pods -l tier=frontend
```

---

## Exercise 5: Deploy Sample Application and Monitor

### Step 1: Review the Application Manifest

View `metricsserver.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  labels:
    app: guestbook
    tier: frontend
spec:
  replicas: 3
  selector:
    matchLabels:
      tier: frontend
  template:
    metadata:
      labels:
        tier: frontend
    spec:
      containers:
        - name: php-redis
          image: gcr.io/google_samples/gb-frontend:v3
```

### Step 2: Deploy the Application

```bash
kubectl apply -f metricsserver.yaml
```

Expected output:
```
deployment.apps/frontend created
```

### Step 3: Wait for Pods to Start

```bash
kubectl get pods -l tier=frontend -w
```

Wait until all Pods are Running:
```
NAME                       READY   STATUS    RESTARTS   AGE
frontend-85595f5bf9-xxxxx  1/1     Running   0          1m
frontend-85595f5bf9-yyyyy  1/1     Running   0          1m
frontend-85595f5bf9-zzzzz  1/1     Running   0          1m
```

Press `Ctrl+C` to stop watching.

### Step 4: Monitor Application Metrics

View metrics for the frontend Pods:

```bash
kubectl top pods -l tier=frontend
```

Expected output:
```
NAME                       CPU(cores)   MEMORY(bytes)
frontend-85595f5bf9-xxxxx  1m           10Mi
frontend-85595f5bf9-yyyyy  1m           10Mi
frontend-85595f5bf9-zzzzz  1m           10Mi
```

### Step 5: Generate Load and Monitor

Create a load generator:

```bash
kubectl run load-generator --image=busybox --restart=Never -- /bin/sh -c "while true; do sleep 1; done"
```

Monitor in real-time:

```bash
watch kubectl top pods -l tier=frontend
```

You'll see the CPU and memory values update every 15 seconds (default scrape interval).

Press `Ctrl+C` to stop watching.

---

## Exercise 6: Understanding Metrics Server Configuration

### Step 1: View Metrics Server Deployment

```bash
kubectl get deployment metrics-server -n kube-system -o yaml > metrics-server-config.yaml
```

### Step 2: Examine Key Configuration Options

Common command-line arguments:

```yaml
args:
- --cert-dir=/tmp
  # Directory for TLS certificates

- --secure-port=4443
  # HTTPS port for serving

- --kubelet-preferred-address-types=InternalIP,ExternalIP,Hostname
  # Order of address types to use for connecting to Kubelet

- --kubelet-use-node-status-port
  # Use the port in node status

- --metric-resolution=15s
  # Interval for scraping metrics (default: 60s, recommended: 15s)

- --kubelet-insecure-tls
  # Skip Kubelet TLS verification (dev only)

- --requestheader-client-ca-file=/etc/ca.crt
  # Client CA for request header authentication
```

### Step 3: Customize Metric Resolution

For more frequent updates (production):

```bash
kubectl patch deployment metrics-server -n kube-system --type='json' -p='[
  {
    "op": "add",
    "path": "/spec/template/spec/containers/0/args/-",
    "value": "--metric-resolution=15s"
  }
]'
```

---

## Exercise 7: Metrics API Deep Dive

### Step 1: Query Metrics API Directly

Get node metrics via API:

```bash
kubectl get --raw "/apis/metrics.k8s.io/v1beta1/nodes" | jq .
```

Expected output:
```json
{
  "kind": "NodeMetricsList",
  "apiVersion": "metrics.k8s.io/v1beta1",
  "metadata": {},
  "items": [
    {
      "metadata": {
        "name": "controlplane",
        "creationTimestamp": "2026-03-16T10:00:00Z"
      },
      "timestamp": "2026-03-16T10:00:00Z",
      "window": "30s",
      "usage": {
        "cpu": "150m",
        "memory": "1200Mi"
      }
    }
  ]
}
```

Get Pod metrics via API:

```bash
kubectl get --raw "/apis/metrics.k8s.io/v1beta1/namespaces/default/pods" | jq .
```

Get specific Pod metrics:

```bash
kubectl get --raw "/apis/metrics.k8s.io/v1beta1/namespaces/default/pods/frontend-85595f5bf9-xxxxx" | jq .
```

### Step 2: Understanding Metric Values

- **cpu**: Measured in cores (1000m = 1 core)
- **memory**: Measured in bytes (Ki, Mi, Gi)
- **window**: Time window for metric collection (typically 30s)
- **timestamp**: When metrics were collected

---

## Lab Cleanup

Remove the sample application:

```bash
# Delete deployment
kubectl delete deployment frontend

# Delete load generator
kubectl delete pod load-generator --ignore-not-found

# Verify cleanup
kubectl get pods -l tier=frontend
kubectl get deployments
```

**Note**: Keep Metrics Server installed as it's needed for future labs (HPA, VPA).

To uninstall Metrics Server (if needed):

```bash
kubectl delete -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

---

## Key Takeaways

1. **Metrics Server is Essential** - Required for autoscaling and resource monitoring
2. **In-Memory Storage** - Metrics are not persisted; use Prometheus for long-term storage
3. **Resource Metrics Only** - Focuses on CPU and memory, not custom metrics
4. **Low Overhead** - Lightweight solution with minimal resource usage
5. **API Integration** - Exposes metrics through standard Kubernetes API
6. **kubectl top Commands** - Quick way to view resource usage
7. **Development vs Production** - Never use insecure TLS in production
8. **Metric Lag** - Metrics update every 15-60 seconds, not real-time

---

## Best Practices

### 1. Production Configuration

```yaml
args:
- --cert-dir=/tmp
- --secure-port=4443
- --kubelet-preferred-address-types=InternalIP
- --metric-resolution=15s
- --kubelet-use-node-status-port
# DO NOT use --kubelet-insecure-tls in production
```

### 2. Resource Requests and Limits

```yaml
resources:
  requests:
    cpu: 100m
    memory: 200Mi
  limits:
    cpu: 1000m
    memory: 1000Mi
```

### 3. High Availability

```yaml
spec:
  replicas: 2
  strategy:
    rollingUpdate:
      maxUnavailable: 0
```

### 4. Monitoring Metrics Server

```bash
# Check Metrics Server health
kubectl get pods -n kube-system -l k8s-app=metrics-server

# View logs
kubectl logs -n kube-system -l k8s-app=metrics-server --tail=50

# Check API availability
kubectl get apiservice v1beta1.metrics.k8s.io
```

### 5. Regular Updates

```bash
# Update to latest version
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

---

## Additional Commands Reference

```bash
# View node metrics
kubectl top nodes
kubectl top nodes --sort-by=cpu
kubectl top nodes --sort-by=memory

# View Pod metrics
kubectl top pods
kubectl top pods -A
kubectl top pods -n <namespace>
kubectl top pods -l <label>
kubectl top pods --sort-by=cpu
kubectl top pods --sort-by=memory

# View container metrics
kubectl top pods --containers
kubectl top pods -n <namespace> --containers

# Check Metrics Server status
kubectl get deployment metrics-server -n kube-system
kubectl get pods -n kube-system -l k8s-app=metrics-server
kubectl logs -n kube-system -l k8s-app=metrics-server

# Query Metrics API
kubectl get --raw "/apis/metrics.k8s.io/v1beta1/nodes" | jq .
kubectl get --raw "/apis/metrics.k8s.io/v1beta1/namespaces/<ns>/pods" | jq .

# Check API service
kubectl get apiservice v1beta1.metrics.k8s.io
kubectl get apiservice v1beta1.metrics.k8s.io -o yaml
```

---

## Troubleshooting

**Issue**: kubectl top shows "Metrics API not available"

```bash
# Check if Metrics Server is running
kubectl get pods -n kube-system -l k8s-app=metrics-server

# Check API service status
kubectl get apiservice v1beta1.metrics.k8s.io -o yaml

# View Metrics Server logs
kubectl logs -n kube-system -l k8s-app=metrics-server

# Common causes:
# - Metrics Server not installed
# - Metrics Server pods not running
# - TLS certificate issues
# - Insufficient RBAC permissions
```

**Issue**: Metrics Server pod not starting

```bash
# Check events
kubectl describe pod -n kube-system -l k8s-app=metrics-server

# Common causes:
# - Image pull errors
# - Insufficient node resources
# - Network policies blocking traffic
```

**Issue**: "unable to fetch metrics" errors in logs

```bash
# For local clusters, apply insecure TLS patch
kubectl patch deployment metrics-server -n kube-system --type='json' -p='[
  {
    "op": "add",
    "path": "/spec/template/spec/containers/0/args/-",
    "value": "--kubelet-insecure-tls"
  }
]'

# Verify Kubelet ports are accessible
kubectl get nodes -o wide
```

**Issue**: Metrics showing as 0 or <unknown>

```bash
# Wait 30-60 seconds after Metrics Server starts
# Metrics need time to be collected and aggregated

# Check metric resolution
kubectl get deployment metrics-server -n kube-system -o yaml | grep metric-resolution
```

---

## Integration with Other Tools

### Horizontal Pod Autoscaler (HPA)

```bash
# HPA depends on Metrics Server
kubectl autoscale deployment frontend --cpu-percent=50 --min=1 --max=10
```

### Vertical Pod Autoscaler (VPA)

```bash
# VPA uses Metrics Server for recommendations
kubectl apply -f vpa.yaml
```

### Kubectl Commands

```bash
# All kubectl top commands use Metrics Server
kubectl top nodes
kubectl top pods
```

---

## Next Steps

Now that you have Metrics Server installed and configured, proceed to:
- [Lab 34: Kubernetes Dashboard](lab34-kubernetes-dashboard.md) - Install and use the Kubernetes Dashboard
- [Lab 20: Horizontal Pod Autoscaling](lab20-hpa.md) - Use Metrics Server for autoscaling
- Explore Vertical Pod Autoscaler (VPA)
- Learn about Prometheus for long-term metrics storage

## Further Reading

- [Metrics Server GitHub](https://github.com/kubernetes-sigs/metrics-server)
- [Kubernetes Metrics Server Design](https://github.com/kubernetes/design-proposals-archive/blob/main/instrumentation/metrics-server.md)
- [Resource Metrics API](https://kubernetes.io/docs/tasks/debug/debug-cluster/resource-metrics-pipeline/)
- [Monitoring Kubernetes Clusters](https://kubernetes.io/docs/tasks/debug/debug-cluster/)

---

**Lab Created**: March 2026
**Compatible with**: Kubernetes 1.24+
