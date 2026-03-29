# Lab 01: Creating Pods and Deployments in Kubernetes

## Overview
In this lab, you will learn how to create Kubernetes Pods and Deployments using YAML manifests. You'll deploy Apache HTTP Server containers and understand the difference between Pods and Deployments.

## Prerequisites
- A running Kubernetes cluster (Minikube, Kind, or any K8s cluster)
- `kubectl` CLI tool installed and configured
- Basic understanding of containers

## Learning Objectives
By the end of this lab, you will be able to:
- Create a simple Pod using YAML manifest
- Deploy multiple Pods with different names
- Create a Deployment for managing Pods
- Understand the difference between Pods and Deployments
- Use kubectl commands to manage your resources

---

## Exercise 1: Create Your First Pod (apache1)

### What is a Pod?
A **Pod** is the smallest deployable unit in Kubernetes. It represents a single instance of a running process in your cluster and can contain one or more containers.

### Step 1: Review the Pod Manifest

Let's look at the `apache1.yaml` file:

```yaml
apiVersion: v1
kind: Pod
metadata:
    name: apache1
    labels:
      mycka: k8slearning
spec:
    containers:
    - name: mycontainer
      image: docker.io/httpd
      ports:
      - containerPort: 80
```

**Understanding the manifest:**
- `apiVersion: v1` - Uses the core Kubernetes API
- `kind: Pod` - Defines this as a Pod resource
- `metadata.name: apache1` - Names the Pod "apache1"
- `metadata.labels` - Labels help identify and select resources
- `spec.containers` - Defines the container(s) in the Pod
- `image: docker.io/httpd` - Uses the official Apache HTTP Server image
- `containerPort: 80` - Exposes port 80 inside the container

### Step 2: Deploy the Pod

Navigate to the labs directory:
```bash
cd k8s/labs/basics
```

Create the Pod:
```bash
kubectl apply -f apache1.yaml
```

Expected output:
```
pod/apache1 created
```

### Step 3: Verify the Pod is Running

Check Pod status:
```bash
kubectl get pods
```

Expected output:
```
NAME      READY   STATUS    RESTARTS   AGE
apache1   1/1     Running   0          10s
```

Get detailed Pod information:
```bash
kubectl describe pod apache1
```

View Pod logs:
```bash
kubectl logs apache1
```

---

## Exercise 2: Create a Second Pod (apache2)

### Step 1: Review the apache2.yaml Manifest

The `apache2.yaml` file is similar to apache1, but with a different name:

```yaml
apiVersion: v1
kind: Pod
metadata:
    name: apache2
    labels:
      mycka: k8slearning
spec:
    containers:
    - name: mycontainer
      image: docker.io/httpd
      ports:
      - containerPort: 80
```

**Note**: Both Pods have the same label `mycka: k8slearning`. This will be important when we create Services later!

### Step 2: Deploy the Second Pod

```bash
kubectl apply -f apache2.yaml
```

Expected output:
```
pod/apache2 created
```

### Step 3: View Both Pods

List all Pods:
```bash
kubectl get pods
```

Expected output:
```
NAME      READY   STATUS    RESTARTS   AGE
apache1   1/1     Running   0          2m
apache2   1/1     Running   0          10s
```

Filter Pods by label:
```bash
kubectl get pods -l mycka=k8slearning
```

---

## Exercise 3: Create a Deployment (myapp1)

### What is a Deployment?
A **Deployment** provides declarative updates for Pods and ReplicaSets. Unlike a standalone Pod, a Deployment:
- Manages multiple Pod replicas
- Provides self-healing (recreates Pods if they fail)
- Supports rolling updates and rollbacks
- Ensures desired state is maintained

### Step 1: Review the Deployment Manifest

Let's look at `myapp1.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  creationTimestamp: null
  labels:
    app: myhttpd
  name: myhttpd
spec:
  replicas: 1
  selector:
    matchLabels:
      app: myhttpd
  strategy: {}
  template:
    metadata:
      creationTimestamp: null
      labels:
        app: myhttpd
    spec:
      containers:
      - image: docker.io/httpd
        name: httpd
        resources: {}
status: {}
```

**Understanding the Deployment:**
- `apiVersion: apps/v1` - Uses the apps API group
- `kind: Deployment` - Defines this as a Deployment resource
- `replicas: 1` - Runs 1 copy of the Pod
- `selector.matchLabels` - Identifies which Pods the Deployment manages
- `template` - Defines the Pod template used to create Pods
- `template.metadata.labels` - Must match the selector labels

### Step 2: Deploy the Application

```bash
kubectl apply -f myapp1.yaml
```

Expected output:
```
deployment.apps/myhttpd created
```

### Step 3: Verify the Deployment

Check Deployment status:
```bash
kubectl get deployments
```

Expected output:
```
NAME      READY   UP-TO-DATE   AVAILABLE   AGE
myhttpd   1/1     1            1           15s
```

View the Pods created by the Deployment:
```bash
kubectl get pods
```

You'll see a Pod with a name like `myhttpd-xxxxxxxxxx-xxxxx`.

Get detailed Deployment information:
```bash
kubectl describe deployment myhttpd
```

---

## Exercise 4: Understanding the Difference

### Pods vs Deployments

| Feature | Pod | Deployment |
|---------|-----|------------|
| **Self-healing** | No - if deleted, it's gone | Yes - recreates Pods automatically |
| **Scaling** | Manual - create more Pods | Easy - change replicas count |
| **Updates** | Manual deletion and recreation | Rolling updates supported |
| **Use Case** | Testing, one-off tasks | Production workloads |

### Demonstration: Self-Healing

**Delete a standalone Pod:**
```bash
kubectl delete pod apache1
```

Check Pods:
```bash
kubectl get pods
```

Result: `apache1` is gone and won't be recreated.

**Delete a Pod managed by Deployment:**
```bash
# Get the exact Pod name
kubectl get pods -l app=myhttpd

# Delete it (replace with your actual Pod name)
kubectl delete pod myhttpd-xxxxxxxxxx-xxxxx
```

Immediately check Pods:
```bash
kubectl get pods -l app=myhttpd
```

Result: A new Pod is automatically created with a different name!

---

## Exercise 5: Scaling the Deployment

Scale the Deployment to 3 replicas:
```bash
kubectl scale deployment myhttpd --replicas=3
```

Verify scaling:
```bash
kubectl get pods -l app=myhttpd
```

Expected output:
```
NAME                      READY   STATUS    RESTARTS   AGE
myhttpd-xxxxxxxxxx-xxxxx  1/1     Running   0          2m
myhttpd-xxxxxxxxxx-yyyyy  1/1     Running   0          5s
myhttpd-xxxxxxxxxx-zzzzz  1/1     Running   0          5s
```

Scale back to 1:
```bash
kubectl scale deployment myhttpd --replicas=1
```

---

## Lab Cleanup

Remove all resources created in this lab:

```bash
# Delete individual Pods
kubectl delete pod apache2

# Delete the Deployment (this also deletes its Pods)
kubectl delete deployment myhttpd

# Verify cleanup
kubectl get pods
```

Alternative: Delete all resources using the YAML files:
```bash
kubectl delete -f apache1.yaml
kubectl delete -f apache2.yaml
kubectl delete -f myapp1.yaml
```

---

## Key Takeaways

1. **Pods** are the basic building blocks in Kubernetes
2. **Deployments** provide management features like self-healing and scaling
3. Use `kubectl apply -f <file>` to create resources from YAML
4. Use `kubectl get`, `describe`, and `logs` to inspect resources
5. **Labels** are crucial for organizing and selecting resources
6. Always use Deployments (not bare Pods) for production workloads

---

## Additional Commands Reference

```bash
# View all resources in current namespace
kubectl get all

# Watch Pods in real-time
kubectl get pods -w

# Access Pod shell
kubectl exec -it <pod-name> -- /bin/bash

# Port forward to access Pod locally
kubectl port-forward pod/<pod-name> 8080:80

# Edit a running resource
kubectl edit deployment myhttpd

# View events
kubectl get events --sort-by=.metadata.creationTimestamp
```

---

## Next Steps

Proceed to [Lab 02: Creating Services](lab02-basics-creating-services.md) to learn how to expose your Pods and Deployments to network traffic.

## Troubleshooting

**Pod stuck in Pending state?**
- Check: `kubectl describe pod <pod-name>`
- Look for: Resource constraints, image pull errors

**Pod in CrashLoopBackOff?**
- Check logs: `kubectl logs <pod-name>`
- Previous logs: `kubectl logs <pod-name> --previous`

**Can't pull image?**
- Verify image name and tag
- Check network connectivity
- Verify image exists in registry

---

**Lab Created**: March 2026
**Compatible with**: Kubernetes 1.24+
