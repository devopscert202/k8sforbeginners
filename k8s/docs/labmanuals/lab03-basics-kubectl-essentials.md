# Lab 03: Essential kubectl Commands

## Overview
In this lab, you will master the essential kubectl commands used for day-to-day Kubernetes operations. You'll learn to create, inspect, modify, and delete Kubernetes resources using the command line.

## Prerequisites
- A running Kubernetes cluster
- `kubectl` CLI tool installed and configured
- Completion of Lab 01 and Lab 02 (recommended)
- Basic understanding of Kubernetes objects (Pods, Deployments, Services)

## Learning Objectives
By the end of this lab, you will be able to:
- Create deployments using kubectl imperative commands
- Inspect and describe Kubernetes resources
- Expose deployments as services
- Work with namespaces for resource isolation
- Scale deployments dynamically
- Delete and clean up resources
- Troubleshoot using events and logs

---

## Exercise 1: Creating and Managing Deployments

### Step 1: Create Your First Deployment

Create a deployment named 'myapp1' with the hello-openshift image:

```bash
kubectl create deployment myapp1 --image=docker.io/openshift/hello-openshift
```

Expected output:
```
deployment.apps/myapp1 created
```

**Understanding the command:**
- `create deployment` - Creates a new Deployment resource
- `myapp1` - Name of the deployment
- `--image` - Specifies the container image to use

### Step 2: View Pods

List all pods in the current namespace:

```bash
kubectl get pods
```

Expected output:
```
NAME                      READY   STATUS    RESTARTS   AGE
myapp1-57bb57dd79-dz8dg   1/1     Running   0          30s
```

**Understanding the pod name:**
- `myapp1` - Deployment name
- `57bb57dd79` - ReplicaSet hash
- `dz8dg` - Random pod identifier

### Step 3: Describe a Pod

Get detailed information about a specific pod:

```bash
kubectl describe pod myapp1-57bb57dd79-dz8dg
```

(Replace with your actual pod name from the previous step)

**Key information in describe output:**
- **Name**: Pod identifier
- **Namespace**: Resource isolation boundary
- **Node**: Which node the pod is running on
- **Status**: Current pod lifecycle state
- **IP**: Pod's internal IP address
- **Containers**: Container details including image, ports, state
- **Events**: Recent activities and state changes

### Step 4: View Deployments

List all deployments:

```bash
kubectl get deployment
```

Expected output:
```
NAME     READY   UP-TO-DATE   AVAILABLE   AGE
myapp1   1/1     1            1           2m
```

**Understanding the columns:**
- **READY**: Number of pods ready / desired replicas
- **UP-TO-DATE**: Pods updated with the latest configuration
- **AVAILABLE**: Pods available for at least minReadySeconds
- **AGE**: Time since deployment creation

### Step 5: Describe a Deployment

Get detailed deployment information:

```bash
kubectl describe deployment myapp1
```

**Important fields to review:**
- **Replicas**: Desired, current, ready replicas
- **StrategyType**: RollingUpdate or Recreate
- **Pod Template**: Container specifications
- **Conditions**: Deployment status conditions
- **Events**: Deployment-related events

---

## Exercise 2: Generating and Using YAML Manifests

### Step 1: Generate Deployment YAML

Create a deployment YAML without applying it to the cluster:

```bash
kubectl create deployment myhttpd --image=docker.io/httpd --dry-run=client -o yaml > myapp1.yaml
```

**Understanding the flags:**
- `--dry-run=client` - Simulates resource creation without actually creating it
- `-o yaml` - Outputs in YAML format
- `> myapp1.yaml` - Redirects output to a file

### Step 2: Review the Generated YAML

```bash
cat myapp1.yaml
```

You should see a complete Deployment manifest:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myhttpd
  labels:
    app: myhttpd
spec:
  replicas: 1
  selector:
    matchLabels:
      app: myhttpd
  template:
    metadata:
      labels:
        app: myhttpd
    spec:
      containers:
      - image: docker.io/httpd
        name: httpd
```

### Step 3: Edit the YAML (Optional)

Modify the generated YAML file:

```bash
nano myapp1.yaml
```

You can change:
- Number of `replicas`
- Container `image` version
- Add `resources` (CPU/memory limits)
- Add `ports` configuration

### Step 4: Apply the Modified YAML

```bash
kubectl apply -f myapp1.yaml
```

Expected output:
```
deployment.apps/myhttpd created
```

---

## Exercise 3: Exposing Deployments as Services

### Step 1: Expose a Deployment

Expose the myapp1 deployment on port 8080:

```bash
kubectl expose deployment myapp1 --port=8080
```

Expected output:
```
service/myapp1 exposed
```

**What this does:**
- Creates a ClusterIP Service
- Maps service port 8080 to container port 8080
- Uses deployment's label selector

### Step 2: List Services

View all services in the current namespace:

```bash
kubectl get svc
```

Alternative (same command):
```bash
kubectl get services
```

Expected output:
```
NAME         TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)    AGE
kubernetes   ClusterIP   10.96.0.1       <none>        443/TCP    5d
myapp1       ClusterIP   10.96.100.200   <none>        8080/TCP   10s
```

### Step 3: Describe a Service

Get detailed service information:

```bash
kubectl describe svc myapp1
```

**Key information:**
- **Type**: ClusterIP, NodePort, or LoadBalancer
- **IP**: Cluster-internal IP address
- **Port**: Service port configuration
- **TargetPort**: Container port
- **Endpoints**: Pod IPs that match the selector
- **Session Affinity**: Client IP session stickiness

### Step 4: View Endpoints

Services route traffic to endpoints (pod IPs):

```bash
kubectl get endpoints
```

Expected output:
```
NAME         ENDPOINTS           AGE
myapp1       172.17.0.5:8080     2m
```

Describe endpoints for more details:

```bash
kubectl describe endpoints myapp1
```

---

## Exercise 4: Working with Namespaces

### Step 1: Create a Namespace

Namespaces provide logical isolation for resources:

```bash
kubectl create namespace mynamespace
```

Expected output:
```
namespace/mynamespace created
```

**Common namespace uses:**
- **Environment separation**: dev, staging, prod
- **Team isolation**: team-a, team-b
- **Application grouping**: app1, app2

### Step 2: List All Namespaces

```bash
kubectl get namespace
```

Alternative (shorter):
```bash
kubectl get ns
```

Expected output:
```
NAME              STATUS   AGE
default           Active   5d
kube-system       Active   5d
kube-public       Active   5d
kube-node-lease   Active   5d
mynamespace       Active   10s
```

**Default namespaces:**
- `default` - Default namespace for resources without a specified namespace
- `kube-system` - Kubernetes system components
- `kube-public` - Publicly readable resources
- `kube-node-lease` - Node heartbeat objects

### Step 3: Create Resources in a Namespace

Deploy an application to the new namespace:

```bash
kubectl create deployment myapp1 --image=docker.io/httpd -n mynamespace
```

**The `-n` flag specifies the namespace!**

### Step 4: View Resources in a Namespace

List deployments in the specific namespace:

```bash
kubectl get deployment -n mynamespace
```

List pods in the namespace:

```bash
kubectl get pods -n mynamespace
```

**Pro tip**: View resources in ALL namespaces:
```bash
kubectl get pods --all-namespaces
```

Or shorter:
```bash
kubectl get pods -A
```

---

## Exercise 5: Scaling Deployments

### Step 1: Scale a Deployment

Increase replicas to 3 in your custom namespace:

```bash
kubectl scale --replicas=3 deployment myapp1 -n mynamespace
```

Expected output:
```
deployment.apps/myapp1 scaled
```

### Step 2: Verify Scaling

Check deployment status:

```bash
kubectl get deployment -n mynamespace
```

Expected output:
```
NAME     READY   UP-TO-DATE   AVAILABLE   AGE
myapp1   3/3     3            3           2m
```

List the pods:

```bash
kubectl get pods -n mynamespace
```

Expected output:
```
NAME                      READY   STATUS    RESTARTS   AGE
myapp1-7d5c8f9b8c-abc12   1/1     Running   0          2m
myapp1-7d5c8f9b8c-def34   1/1     Running   0          30s
myapp1-7d5c8f9b8c-ghi56   1/1     Running   0          30s
```

### Step 3: Watch Live Changes

Monitor pods in real-time as they scale:

```bash
kubectl get pods -n mynamespace -w
```

(Press Ctrl+C to exit)

---

## Exercise 6: Cleaning Up Resources

### Step 1: Delete a Deployment

Remove the deployment in the default namespace:

```bash
kubectl delete deployment myapp1
```

Expected output:
```
deployment.apps "myapp1" deleted
```

**Note**: This also deletes all pods managed by the deployment.

### Step 2: Delete a Service

Remove the service:

```bash
kubectl delete svc myapp1
```

Expected output:
```
service "myapp1" deleted
```

### Step 3: Verify Deletion

Confirm the service no longer exists:

```bash
kubectl get svc
```

You should only see the default `kubernetes` service.

### Step 4: Delete a Namespace

Remove the entire namespace and all resources within it:

```bash
kubectl delete namespace mynamespace
```

Expected output:
```
namespace "mynamespace" deleted
```

**⚠️ Warning**: This deletes ALL resources in the namespace!

---

## Exercise 7: Monitoring and Troubleshooting

### Step 1: View Cluster Events

List recent events sorted by time:

```bash
kubectl get events
```

Sort events by timestamp:

```bash
kubectl get events --sort-by=.metadata.creationTimestamp
```

Filter events for a specific namespace:

```bash
kubectl get events -n kube-system
```

**Event types:**
- `Normal` - Routine operations
- `Warning` - Potential issues
- `Error` - Problems requiring attention

### Step 2: List All Nodes

View cluster nodes:

```bash
kubectl get nodes
```

Expected output:
```
NAME                        STATUS   ROLES           AGE   VERSION
master.example.com          Ready    control-plane   5d    v1.29.x
worker-node-1.example.com   Ready    <none>          5d    v1.29.x
worker-node-2.example.com   Ready    <none>          5d    v1.29.x
```

Show additional information:

```bash
kubectl get nodes -o wide
```

### Step 3: Describe a Node

Get detailed node information:

```bash
kubectl describe node worker-node-1.example.com
```

**Important node details:**
- **Conditions**: Node health status
- **Capacity**: Total CPU, memory, pods
- **Allocatable**: Resources available for pods
- **System Info**: OS, kernel version, container runtime
- **Non-terminated Pods**: Pods running on the node
- **Allocated resources**: CPU and memory usage

---

## Lab Cleanup

Remove all resources created during this lab:

```bash
# Delete deployments
kubectl delete deployment myapp1 myhttpd --ignore-not-found=true

# Delete services
kubectl delete svc myapp1 --ignore-not-found=true

# Delete namespace (if still exists)
kubectl delete namespace mynamespace --ignore-not-found=true

# Verify cleanup
kubectl get all
```

---

## Key Takeaways

1. **Imperative commands** - Fast way to create resources (`kubectl create`)
2. **Declarative approach** - Use YAML files for version control (`kubectl apply`)
3. **Dry-run** - Preview changes without applying (`--dry-run=client`)
4. **Namespaces** - Logical isolation for resources
5. **Scaling** - Easily adjust replica count
6. **Describe** - Detailed resource information
7. **Events** - Cluster activity logs
8. **Delete** - Clean up resources when done

---

## Essential kubectl Cheat Sheet

### Resource Management
```bash
# Create
kubectl create deployment <name> --image=<image>
kubectl create namespace <name>

# Get/List
kubectl get pods
kubectl get deployments
kubectl get services
kubectl get all

# Describe
kubectl describe pod <pod-name>
kubectl describe deployment <deployment-name>

# Delete
kubectl delete pod <pod-name>
kubectl delete deployment <deployment-name>
kubectl delete namespace <namespace-name>
```

### Working with Namespaces
```bash
# Specify namespace
kubectl get pods -n <namespace>
kubectl get all -n <namespace>

# All namespaces
kubectl get pods --all-namespaces
kubectl get pods -A
```

### Scaling and Updates
```bash
# Scale
kubectl scale deployment <name> --replicas=<count>

# Update image
kubectl set image deployment/<name> <container>=<new-image>

# Edit resource
kubectl edit deployment <name>
```

### Troubleshooting
```bash
# Logs
kubectl logs <pod-name>
kubectl logs <pod-name> -f  # Follow
kubectl logs <pod-name> --previous  # Previous container

# Events
kubectl get events
kubectl get events --sort-by=.metadata.creationTimestamp

# Shell access
kubectl exec -it <pod-name> -- /bin/bash
kubectl exec -it <pod-name> -- sh
```

### YAML Management
```bash
# Generate YAML
kubectl create deployment <name> --image=<image> --dry-run=client -o yaml > file.yaml

# Apply YAML
kubectl apply -f file.yaml

# Delete from YAML
kubectl delete -f file.yaml
```

---

## Troubleshooting Guide

### Issue: `Error from server (NotFound)`

**Solution**: Resource doesn't exist or wrong namespace
```bash
kubectl get <resource> --all-namespaces
```

### Issue: Pod stuck in `Pending`

**Solution**: Check events and node resources
```bash
kubectl describe pod <pod-name>
kubectl get events
kubectl describe nodes
```

### Issue: `Unable to connect to the server`

**Solution**: Verify cluster connection
```bash
kubectl cluster-info
kubectl config view
kubectl config current-context
```

### Issue: `Forbidden` errors

**Solution**: Check RBAC permissions
```bash
kubectl auth can-i <verb> <resource>
kubectl auth can-i create pods
```

---

## Next Steps

Proceed to [Lab 08: Cluster Administration](lab08-cluster-administration.md) to learn advanced kubeadm and cluster management commands.

## Additional Reading

- [kubectl Official Documentation](https://kubernetes.io/docs/reference/kubectl/)
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)
- [kubectl Book](https://kubectl.docs.kubernetes.io/)

---

**Lab Created**: March 2026
**Compatible with**: Kubernetes 1.24+
**Based on**: labs/administration/k8scommands.txt
**Tested on**: kubeadm clusters, Minikube, Kind
