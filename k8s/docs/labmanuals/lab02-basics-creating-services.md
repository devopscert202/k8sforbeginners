# Lab 02: Creating Kubernetes Services

## Overview
In this lab, you will learn how to expose your Pods and Deployments using Kubernetes Services. You'll create both NodePort and LoadBalancer type Services to understand different ways to make your applications accessible.

## Prerequisites
- Completion of [Lab 01: Creating Pods and Deployments](lab01-basics-creating-pods.md)
- A running Kubernetes cluster
- `kubectl` CLI tool installed and configured
- Pods from Lab 01 running (apache1, apache2) or ability to recreate them

## Learning Objectives
By the end of this lab, you will be able to:
- Understand what Kubernetes Services are and why they're needed
- Create a NodePort Service
- Create a LoadBalancer Service
- Access your applications through Services
- Understand Service selectors and labels
- Troubleshoot Service connectivity

---

## What is a Kubernetes Service?

### The Problem
- Pods have dynamic IP addresses that change when they restart
- Pods are ephemeral and can be replaced at any time
- Multiple Pods may serve the same application
- External clients need a stable endpoint to access applications

### The Solution: Services
A **Service** is an abstract way to expose an application running on a set of Pods as a network service. It provides:
- **Stable IP address** - doesn't change even if Pods restart
- **DNS name** - accessible via service name
- **Load balancing** - distributes traffic across multiple Pods
- **Service discovery** - Pods can find each other by name

### Service Types

| Type | Description | Use Case |
|------|-------------|----------|
| **ClusterIP** | Internal-only, default type | Communication between Pods within cluster |
| **NodePort** | Exposes service on each Node's IP at a static port | Development, testing, or when you have external load balancer |
| **LoadBalancer** | Creates external load balancer (cloud providers) | Production external access on cloud |
| **ExternalName** | Maps service to DNS name | Integration with external services |

---

## Exercise 1: Prepare the Environment

### Step 1: Ensure Lab 01 Pods are Running

First, let's create the Pods from Lab 01 if they're not already running:

```bash
cd k8s/labs/basics
```

Create the apache Pods:
```bash
kubectl apply -f apache1.yaml
kubectl apply -f apache2.yaml
```

Verify Pods are running:
```bash
kubectl get pods
```

Expected output:
```
NAME      READY   STATUS    RESTARTS   AGE
apache1   1/1     Running   0          10s
apache2   1/1     Running   0          10s
```

### Step 2: Verify Pod Labels

Remember, Services use **label selectors** to find Pods. Let's check our Pod labels:

```bash
kubectl get pods --show-labels
```

Expected output:
```
NAME      READY   STATUS    RESTARTS   AGE   LABELS
apache1   1/1     Running   0          30s   mycka=k8slearning
apache2   1/1     Running   0          30s   mycka=k8slearning
```

Both Pods have the label `mycka=k8slearning` - this is crucial for our Service to find them!

---

## Exercise 2: Create a NodePort Service

### What is a NodePort Service?
A **NodePort** Service exposes your application on a static port on each Node's IP address. It makes your service accessible from outside the cluster at `<NodeIP>:<NodePort>`.

### Step 1: Review the Service Manifest

Let's look at `apache_service.yaml`:

```yaml
kind: Service
apiVersion: v1
metadata:
  name: myservice
spec:
  selector:
    mycka: k8slearning
  ports:
  - protocol: TCP
    port: 8081
    targetPort: 80
  type: NodePort
```

**Understanding the manifest:**
- `kind: Service` - Defines this as a Service resource
- `metadata.name: myservice` - Service name (also becomes DNS name)
- `selector.mycka: k8slearning` - Selects Pods with this label
- `ports`:
  - `port: 8081` - Service port (how other Pods access it)
  - `targetPort: 80` - Container port (where traffic is forwarded)
  - `protocol: TCP` - Transport protocol
- `type: NodePort` - Makes service accessible externally

### Step 2: Create the NodePort Service

```bash
kubectl apply -f apache_service.yaml
```

Expected output:
```
service/myservice created
```

### Step 3: Verify the Service

Check Service details:
```bash
kubectl get service myservice
```

Expected output:
```
NAME        TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)          AGE
myservice   NodePort   10.96.100.200   <none>        8081:30123/TCP   10s
```

**Understanding the output:**
- `CLUSTER-IP`: Internal IP (10.96.100.200) - accessible within cluster
- `PORT(S)`: 8081:30123 means:
  - `8081` - Service port (internal)
  - `30123` - NodePort (external, randomly assigned between 30000-32767)

Get more details:
```bash
kubectl describe service myservice
```

Look for the **Endpoints** section - it should list both Pod IPs!

### Step 4: Test the Service

**Option A: From within the cluster**
```bash
# Create a test Pod
kubectl run test-pod --image=busybox --rm -it --restart=Never -- /bin/sh

# Inside the Pod, test the service
wget -qO- http://myservice:8081
# OR
wget -qO- http://10.96.100.200:8081

# Exit the Pod
exit
```

**Option B: From your local machine (Minikube)**
```bash
# Get Minikube IP
minikube ip

# Access the service (replace <minikube-ip> and <nodeport>)
curl http://<minikube-ip>:30123
```

**Option C: Using Minikube service command**
```bash
minikube service myservice
```

This will automatically open the service in your browser!

### Step 5: Verify Load Balancing

The Service distributes traffic between apache1 and apache2. Let's verify:

```bash
kubectl get endpoints myservice
```

Expected output shows both Pod IPs:
```
NAME        ENDPOINTS                     AGE
myservice   172.17.0.3:80,172.17.0.4:80   2m
```

---

## Exercise 3: Create a LoadBalancer Service

### What is a LoadBalancer Service?
A **LoadBalancer** Service creates an external load balancer (in cloud environments like AWS, GCP, Azure) and assigns a fixed external IP to your service.

### Step 1: Review the LoadBalancer Manifest

Let's look at `apache_lb_service.yaml`:

```yaml
kind: Service
apiVersion: v1
metadata:
  name: myservice
spec:
  selector:
    mycka: k8slearning
  ports:
  - protocol: TCP
    port: 80
    targetPort: 80
  type: LoadBalancer
```

**Key differences from NodePort:**
- `type: LoadBalancer` - Creates external load balancer
- `port: 80` - Standard HTTP port (both service and target)
- Same selector, so it targets the same Pods

### Step 2: Clean Up the NodePort Service

First, delete the existing service:
```bash
kubectl delete service myservice
```

Verify it's deleted:
```bash
kubectl get service
```

### Step 3: Create the LoadBalancer Service

```bash
kubectl apply -f apache_lb_service.yaml
```

Expected output:
```
service/myservice created
```

### Step 4: Verify the LoadBalancer Service

Check Service status:
```bash
kubectl get service myservice
```

**On cloud providers (AWS, GCP, Azure):**
```
NAME        TYPE           CLUSTER-IP      EXTERNAL-IP       PORT(S)        AGE
myservice   LoadBalancer   10.96.100.200   35.123.45.67      80:31234/TCP   30s
```

**On Minikube or local clusters:**
```
NAME        TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
myservice   LoadBalancer   10.96.100.200   <pending>     80:31234/TCP   30s
```

**Note**: `<pending>` is normal on Minikube/local clusters - they don't have external load balancers.

### Step 5: Access the LoadBalancer Service

**On cloud providers:**
```bash
# Use the EXTERNAL-IP
curl http://35.123.45.67
```

**On Minikube:**
```bash
# Minikube provides a tunnel for LoadBalancer services
minikube tunnel
```

In another terminal:
```bash
kubectl get service myservice
# Now you should see an EXTERNAL-IP (likely 127.0.0.1)

# Access the service
curl http://<external-ip>
```

**Alternative for Minikube:**
```bash
minikube service myservice
```

---

## Exercise 4: Understanding Service Selectors

### How Services Find Pods

Services use **label selectors** to dynamically discover and route traffic to Pods.

### Experiment: Add a New Pod

Create a new Pod with the matching label:

```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: apache3
  labels:
    mycka: k8slearning
spec:
  containers:
  - name: mycontainer
    image: docker.io/httpd
    ports:
    - containerPort: 80
EOF
```

Check the Service endpoints:
```bash
kubectl get endpoints myservice
```

Now you should see **three** endpoints (apache1, apache2, apache3)!

The Service automatically discovered the new Pod because it has the matching label.

### Experiment: Remove a Pod from Service

Remove the label from apache3:
```bash
kubectl label pod apache3 mycka-
```

Check endpoints again:
```bash
kubectl get endpoints myservice
```

Now apache3 is gone from the endpoints! The Service stopped routing traffic to it.

Cleanup:
```bash
kubectl delete pod apache3
```

---

## Exercise 5: Service Discovery

### DNS-Based Service Discovery

Kubernetes creates DNS records for Services automatically.

### Test Service DNS

Create a test Pod:
```bash
kubectl run dns-test --image=busybox --rm -it --restart=Never -- /bin/sh
```

Inside the Pod:
```bash
# Test service name resolution
nslookup myservice

# Test HTTP access using DNS name
wget -qO- http://myservice
```

**DNS Naming:**
- `myservice` - Short name (same namespace)
- `myservice.default` - Full name in default namespace
- `myservice.default.svc.cluster.local` - Fully qualified domain name (FQDN)

Exit the Pod:
```bash
exit
```

---

## Exercise 6: Port Mapping Deep Dive

### Understanding Port Types

```yaml
ports:
- protocol: TCP
  port: 8081        # Service Port
  targetPort: 80    # Container Port
  nodePort: 30123   # Node Port (optional, auto-assigned if not specified)
```

| Port Type | Description | Example |
|-----------|-------------|---------|
| **targetPort** | Port on the Pod/container | 80 (Apache listens here) |
| **port** | Port on the Service (ClusterIP) | 8081 (Pods access service here) |
| **nodePort** | Port on the Node (external access) | 30123 (External access) |

### Traffic Flow

```
External User → NodePort (30123)
                    ↓
              Service (8081)
                    ↓
          targetPort (80 on Pod)
                    ↓
          Container Application
```

---

## Lab Cleanup

Remove all resources created in this lab:

```bash
# Delete the Service
kubectl delete service myservice

# Delete the Pods
kubectl delete pod apache1 apache2

# Verify cleanup
kubectl get all
```

Alternative: Use the YAML files:
```bash
kubectl delete -f apache_service.yaml
kubectl delete -f apache_lb_service.yaml
kubectl delete -f apache1.yaml
kubectl delete -f apache2.yaml
```

---

## Key Takeaways

1. **Services** provide stable network endpoints for dynamic Pods
2. **Label selectors** connect Services to Pods
3. **NodePort** exposes services on Node IPs (port 30000-32767)
4. **LoadBalancer** creates external load balancers (cloud only)
5. Services provide automatic **load balancing** across multiple Pods
6. **DNS-based service discovery** allows Pods to find services by name
7. **Port mapping**: targetPort → port → nodePort

---

## Common Service Patterns

### Pattern 1: Frontend Service (LoadBalancer)
```yaml
type: LoadBalancer
port: 80
targetPort: 8080
```
Use for: Web applications that need external access

### Pattern 2: Backend Service (ClusterIP)
```yaml
type: ClusterIP
port: 3306
targetPort: 3306
```
Use for: Databases, internal APIs (not exposed externally)

### Pattern 3: Development Service (NodePort)
```yaml
type: NodePort
port: 8080
targetPort: 8080
nodePort: 30080
```
Use for: Testing, development, debugging

---

## Troubleshooting Guide

### Issue: Service has no endpoints

**Check 1**: Verify Pod labels match Service selector
```bash
kubectl get pods --show-labels
kubectl describe service myservice | grep Selector
```

**Check 2**: Ensure Pods are running and ready
```bash
kubectl get pods
```

### Issue: Can't access service externally

**Check 1**: Verify service type and ports
```bash
kubectl get service myservice
```

**Check 2**: For NodePort, ensure firewall allows the port
```bash
# Check NodePort value
kubectl describe service myservice | grep NodePort
```

**Check 3**: For LoadBalancer, ensure cloud provider supports it
```bash
# Minikube requires 'minikube tunnel'
minikube tunnel
```

### Issue: Service exists but traffic doesn't reach Pods

**Check 1**: Test Pod directly
```bash
kubectl port-forward pod/apache1 8080:80
curl http://localhost:8080
```

**Check 2**: Check Pod logs
```bash
kubectl logs apache1
```

**Check 3**: Verify targetPort matches container port
```bash
kubectl describe pod apache1 | grep Port
kubectl describe service myservice | grep TargetPort
```

---

## Additional Commands Reference

```bash
# Create a service from command line
kubectl expose pod apache1 --port=80 --target-port=80 --type=NodePort

# Get service YAML
kubectl get service myservice -o yaml

# Edit service on the fly
kubectl edit service myservice

# Watch service endpoints
kubectl get endpoints myservice -w

# Test service connectivity from within cluster
kubectl run test --image=busybox --rm -it -- wget -qO- http://myservice:8081

# Port forward service to localhost
kubectl port-forward service/myservice 8080:8081

# Get service URL (Minikube)
minikube service myservice --url
```

---

## Next Steps

1. **Lab 03**: Learn about Ingress for HTTP/HTTPS routing
2. **Lab 04**: Explore ConfigMaps and Secrets
3. **Lab 05**: Implement persistent storage with Volumes

---

## Additional Reading

- [Kubernetes Services Documentation](https://kubernetes.io/docs/concepts/services-networking/service/)
- [Service Types Comparison](https://kubernetes.io/docs/tutorials/kubernetes-basics/expose/expose-intro/)
- [DNS for Services and Pods](https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/)

---

**Lab Created**: March 2026
**Compatible with**: Kubernetes 1.24+
**Tested on**: Minikube, AWS EKS, GCP GKE
