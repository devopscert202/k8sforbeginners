# Lab 23: Multi-Port Services in Kubernetes

## Overview
In this lab, you will learn how to configure and expose applications that use multiple ports in Kubernetes. You'll work with multi-port Pods and Services, understand port naming conventions, and explore real-world use cases for multi-port configurations.

## Prerequisites
- A running Kubernetes cluster (Minikube, Kind, or any K8s cluster)
- `kubectl` CLI tool installed and configured
- Completion of [Lab 02: Creating Services](lab02-creating-services.md)
- Basic understanding of Kubernetes Services

## Learning Objectives
By the end of this lab, you will be able to:
- Create Pods with multiple container ports
- Configure Services with multiple port mappings
- Understand port naming conventions and best practices
- Access different ports of the same application
- Troubleshoot multi-port service configurations
- Apply multi-port patterns to real-world scenarios

---

## Understanding Multi-Port Services

### What are Multi-Port Services?

Many applications require multiple ports for different purposes:

- **Web applications**: HTTP (80) and HTTPS (443)
- **Databases**: Main connection port and admin/metrics port
- **Microservices**: Application port and health check port
- **Monitoring**: Application port and metrics/prometheus port

### Single Port vs Multi-Port

**Single Port Service:**
```yaml
ports:
- port: 80
  targetPort: 8080
```

**Multi-Port Service:**
```yaml
ports:
- name: http
  port: 8080
  targetPort: 8080
- name: custom
  port: 9090
  targetPort: 9090
```

**Key difference**: Multi-port services REQUIRE named ports for clarity.

---

## Exercise 1: Review Multi-Port Configuration

### Step 1: Navigate to Lab Directory

```bash
cd k8s/labs/networking
```

### Step 2: Review the Multi-Port Pod Manifest

Let's examine `multi-port-pod.yaml`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: multi-port-pod
  labels:
    app: multi-port-app
spec:
  containers:
  - name: multi-port-container
    image: hashicorp/http-echo
    args:
    - "-text=Hello, Multi-Port Service!"
    ports:
    - containerPort: 8080
      name: http
    - containerPort: 9090
      name: custom
```

**Understanding the manifest:**

- `metadata.labels.app: multi-port-app` - Label for Service selector
- `containers[0].image: hashicorp/http-echo` - Simple HTTP server
- `args` - Sets the response text
- `ports` - Declares multiple ports:
  - `containerPort: 8080, name: http` - Primary HTTP port
  - `containerPort: 9090, name: custom` - Secondary custom port
- **Port names** - Optional but recommended for clarity

**Note**: The hashicorp/http-echo image only actually listens on one port (5678 by default), but this manifest demonstrates the pattern.

### Step 3: Review the Multi-Port Service Manifest

Let's examine `multi-port-service.yaml`:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: multi-port-service
spec:
  selector:
    app: multi-port-app
  type: NodePort
  ports:
  - protocol: TCP
    port: 8080
    targetPort: 8080
    nodePort: 30080
    name: http
  - protocol: TCP
    port: 9090
    targetPort: 9090
    nodePort: 30090
    name: custom
```

**Understanding the manifest:**

- `selector.app: multi-port-app` - Selects Pods with this label
- `type: NodePort` - Exposes service externally
- `ports` - Multiple port configurations:
  - **First port (http)**:
    - `port: 8080` - Service port (ClusterIP access)
    - `targetPort: 8080` - Pod port
    - `nodePort: 30080` - External access port
    - `name: http` - Port identifier
  - **Second port (custom)**:
    - `port: 9090` - Service port
    - `targetPort: 9090` - Pod port
    - `nodePort: 30090` - External access port
    - `name: custom` - Port identifier

**Important**: When a Service has multiple ports, each port MUST have a unique name.

---

## Exercise 2: Deploy Multi-Port Application

### Step 1: Create a Working Multi-Port Pod

Since hashicorp/http-echo only listens on one port, let's create a more realistic example:

```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: multi-port-pod
  labels:
    app: multi-port-app
spec:
  containers:
  - name: nginx
    image: nginx:latest
    ports:
    - containerPort: 80
      name: http
  - name: metrics
    image: nginx/nginx-prometheus-exporter:latest
    args:
    - "-nginx.scrape-uri=http://localhost/nginx_status"
    ports:
    - containerPort: 9113
      name: metrics
EOF
```

**This Pod has:**
- **nginx container** - Serves web traffic on port 80
- **metrics container** - Exposes Prometheus metrics on port 9113

Expected output:
```
pod/multi-port-pod created
```

### Step 2: Verify Pod Status

```bash
kubectl get pod multi-port-pod
```

Expected output:
```
NAME             READY   STATUS    RESTARTS   AGE
multi-port-pod   2/2     Running   0          30s
```

**Notice**: READY shows 2/2 (both containers running)

### Step 3: View Detailed Pod Information

```bash
kubectl describe pod multi-port-pod
```

Look for the **Containers** section - you should see both containers and their ports:

```
Containers:
  nginx:
    Port:          80/TCP
  metrics:
    Port:          9113/TCP
```

---

## Exercise 3: Create Multi-Port Service

### Step 1: Create the Service

```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Service
metadata:
  name: multi-port-service
spec:
  selector:
    app: multi-port-app
  type: NodePort
  ports:
  - protocol: TCP
    port: 80
    targetPort: 80
    nodePort: 30080
    name: http
  - protocol: TCP
    port: 9113
    targetPort: 9113
    nodePort: 30113
    name: metrics
EOF
```

Expected output:
```
service/multi-port-service created
```

### Step 2: Verify the Service

```bash
kubectl get service multi-port-service
```

Expected output:
```
NAME                 TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)                        AGE
multi-port-service   NodePort   10.96.200.100   <none>        80:30080/TCP,9113:30113/TCP    15s
```

**Notice**: PORT(S) shows both port mappings: `80:30080/TCP,9113:30113/TCP`

### Step 3: View Detailed Service Information

```bash
kubectl describe service multi-port-service
```

Key sections:

```
Port:                     http  80/TCP
TargetPort:               80/TCP
NodePort:                 http  30080/TCP
Endpoints:                10.244.0.5:80

Port:                     metrics  9113/TCP
TargetPort:               9113/TCP
NodePort:                 metrics  30113/TCP
Endpoints:                10.244.0.5:9113
```

**Notice**: Each port has:
- A unique name (http, metrics)
- Its own port mapping
- Separate endpoint

### Step 4: Check Service Endpoints

```bash
kubectl get endpoints multi-port-service
```

Expected output:
```
NAME                 ENDPOINTS                              AGE
multi-port-service   10.244.0.5:80,10.244.0.5:9113          1m
```

Both ports on the same Pod IP are registered as endpoints!

---

## Exercise 4: Access Multi-Port Service

### Step 1: Test From Within Cluster

Create a test Pod:

```bash
kubectl run test-pod --image=busybox --rm -it --restart=Never -- /bin/sh
```

Inside the test Pod:

```bash
# Test HTTP port (port 80)
wget -qO- http://multi-port-service:80

# Test metrics port (port 9113)
wget -qO- http://multi-port-service:9113/metrics
```

Both should work!

Exit the Pod:
```bash
exit
```

### Step 2: Test Using Port-Forward

**Port-forward the HTTP port:**

```bash
kubectl port-forward service/multi-port-service 8080:80
```

In another terminal or browser:
```bash
curl http://localhost:8080
```

You should see the nginx welcome page!

**Port-forward the metrics port:**

Press `Ctrl+C` to stop the previous port-forward, then:

```bash
kubectl port-forward service/multi-port-service 9113:9113
```

In another terminal:
```bash
curl http://localhost:9113/metrics
```

You should see Prometheus metrics!

### Step 3: Test Using NodePort (Minikube)

Get Minikube IP:
```bash
minikube ip
```

**Access HTTP port:**
```bash
curl http://<minikube-ip>:30080
```

**Access metrics port:**
```bash
curl http://<minikube-ip>:30113/metrics
```

### Step 4: Test Using Minikube Service

```bash
# Open HTTP port in browser
minikube service multi-port-service --url
```

This returns both URLs:
```
http://192.168.49.2:30080
http://192.168.49.2:30113
```

---

## Exercise 5: Port Naming Best Practices

### Why Name Ports?

**Requirements:**
1. Services with multiple ports MUST name each port
2. Port names must be unique within the Service
3. Port names help with Ingress and service mesh configurations

### Standard Port Names

Use descriptive, conventional names:

| Port Name | Common Use | Example Port |
|-----------|------------|--------------|
| `http` | HTTP traffic | 80, 8080, 8000 |
| `https` | HTTPS traffic | 443, 8443 |
| `grpc` | gRPC traffic | 50051 |
| `metrics` | Prometheus metrics | 9090, 9113 |
| `admin` | Admin interface | 8081, 9000 |
| `health` | Health check endpoint | 8086 |
| `postgres` | PostgreSQL | 5432 |
| `mysql` | MySQL/MariaDB | 3306 |
| `redis` | Redis | 6379 |
| `mongodb` | MongoDB | 27017 |

### Port Naming Rules

```yaml
# Good: descriptive names
ports:
- name: http
  port: 80
- name: https
  port: 443
- name: metrics
  port: 9090

# Bad: generic names
ports:
- name: port1
  port: 80
- name: port2
  port: 443

# Bad: no names (only allowed for single port)
ports:
- port: 80
- port: 443  # ERROR: second port requires name
```

**Naming conventions:**
- Use lowercase
- Use hyphens for multi-word names (e.g., `admin-api`)
- Keep it short but descriptive
- Follow protocol conventions when applicable

---

## Exercise 6: Real-World Multi-Port Patterns

### Pattern 1: Web Application with Metrics

**Use case**: Application serving HTTP traffic + Prometheus metrics

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web-app
  template:
    metadata:
      labels:
        app: web-app
    spec:
      containers:
      - name: app
        image: my-web-app:v1.0
        ports:
        - containerPort: 8080
          name: http
        - containerPort: 9090
          name: metrics
---
apiVersion: v1
kind: Service
metadata:
  name: web-app-service
spec:
  selector:
    app: web-app
  ports:
  - name: http
    port: 80
    targetPort: http
  - name: metrics
    port: 9090
    targetPort: metrics
```

**Benefits:**
- HTTP traffic on standard port 80
- Metrics on separate port for Prometheus scraping
- Port names enable ServiceMonitor (Prometheus Operator)

### Pattern 2: Database with Admin Interface

**Use case**: Database with separate admin/monitoring port

```yaml
apiVersion: v1
kind: Service
metadata:
  name: postgres-service
spec:
  selector:
    app: postgres
  ports:
  - name: postgres
    port: 5432
    targetPort: 5432
  - name: metrics
    port: 9187
    targetPort: 9187  # postgres_exporter
  type: ClusterIP
```

**Benefits:**
- Main database port for application connections
- Separate metrics port for monitoring
- ClusterIP keeps it internal

### Pattern 3: Microservice with gRPC and HTTP

**Use case**: Service exposing both gRPC and REST APIs

```yaml
apiVersion: v1
kind: Service
metadata:
  name: api-service
spec:
  selector:
    app: api-server
  ports:
  - name: grpc
    port: 50051
    targetPort: 50051
  - name: http
    port: 8080
    targetPort: 8080
  - name: metrics
    port: 9090
    targetPort: 9090
```

**Benefits:**
- gRPC for internal service-to-service communication
- HTTP/REST for external clients
- Metrics for observability

### Pattern 4: HTTP and HTTPS

**Use case**: Service supporting both HTTP and HTTPS

```yaml
apiVersion: v1
kind: Service
metadata:
  name: secure-web-service
spec:
  selector:
    app: web-server
  type: LoadBalancer
  ports:
  - name: http
    port: 80
    targetPort: 8080
  - name: https
    port: 443
    targetPort: 8443
```

**Benefits:**
- Support legacy HTTP clients
- HTTPS for secure communication
- LoadBalancer for external access

---

## Exercise 7: Advanced Multi-Port Scenarios

### Scenario 1: Named Port References

You can reference Pod ports by name in Services:

**Pod with named ports:**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-pod
  labels:
    app: myapp
spec:
  containers:
  - name: app
    image: myapp:latest
    ports:
    - containerPort: 8080
      name: web
    - containerPort: 9090
      name: admin
```

**Service using port names:**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: app-service
spec:
  selector:
    app: myapp
  ports:
  - name: web-port
    port: 80
    targetPort: web      # References Pod port name
  - name: admin-port
    port: 9000
    targetPort: admin    # References Pod port name
```

**Benefits:**
- Decouple Service from specific port numbers
- Change Pod ports without updating Service
- More maintainable

### Scenario 2: Multiple Services for Same Pod

You can create separate Services for different ports:

**Application Pod:**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app
  labels:
    app: myapp
spec:
  containers:
  - name: app
    image: myapp:latest
    ports:
    - containerPort: 8080
      name: public
    - containerPort: 9090
      name: internal
```

**Public Service (external):**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: app-public
spec:
  selector:
    app: myapp
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: public
```

**Internal Service (internal only):**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: app-internal
spec:
  selector:
    app: myapp
  type: ClusterIP
  ports:
  - port: 9090
    targetPort: internal
```

**Benefits:**
- Different access controls per port
- Public port exposed via LoadBalancer
- Internal port only accessible within cluster
- Separate DNS names

### Test This Pattern

Create the resources:

```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: dual-service-pod
  labels:
    app: dual-service
spec:
  containers:
  - name: nginx
    image: nginx:latest
    ports:
    - containerPort: 80
      name: web
---
apiVersion: v1
kind: Service
metadata:
  name: external-service
spec:
  selector:
    app: dual-service
  type: NodePort
  ports:
  - port: 80
    targetPort: web
    nodePort: 30088
---
apiVersion: v1
kind: Service
metadata:
  name: internal-service
spec:
  selector:
    app: dual-service
  type: ClusterIP
  ports:
  - port: 8080
    targetPort: web
EOF
```

Verify both services:

```bash
# Check services
kubectl get service external-service internal-service

# Both services point to same Pod!
kubectl get endpoints external-service internal-service
```

Test access:

```bash
# Test internal service
kubectl run test --image=busybox --rm -it --restart=Never -- wget -qO- http://internal-service:8080

# Test external service (Minikube)
minikube service external-service --url
```

---

## Lab Cleanup

Remove all resources created in this lab:

```bash
# Delete the multi-port application
kubectl delete pod multi-port-pod --ignore-not-found=true
kubectl delete service multi-port-service --ignore-not-found=true

# Delete dual-service example
kubectl delete pod dual-service-pod --ignore-not-found=true
kubectl delete service external-service internal-service --ignore-not-found=true

# Verify cleanup
kubectl get pods,services
```

---

## Troubleshooting Multi-Port Services

### Issue 1: Port Not Accessible

**Symptoms**: One port works, another doesn't

**Diagnosis:**
```bash
# Check if Pod is listening on all ports
kubectl exec <pod-name> -- netstat -tlnp

# Check Service endpoints
kubectl get endpoints <service-name> -o yaml

# Check if container port is exposed
kubectl describe pod <pod-name> | grep -A 5 Ports
```

**Common causes:**
- Container not actually listening on the port
- Port number mismatch between Pod and Service
- Firewall/security group blocking the port

### Issue 2: Wrong Port Mapping

**Symptoms**: Accessing port gives unexpected response

**Diagnosis:**
```bash
# Verify port mappings
kubectl describe service <service-name>

# Check which port is which
kubectl get service <service-name> -o yaml | grep -A 5 ports
```

**Solution**: Verify targetPort matches containerPort

### Issue 3: Service Without Port Names

**Error message:**
```
Service "my-service" is invalid: spec.ports[1].name: Required value
```

**Solution**: Add unique names to all ports:
```yaml
ports:
- name: http
  port: 80
- name: metrics
  port: 9090
```

### Issue 4: Duplicate Port Names

**Error message:**
```
Service "my-service" is invalid: spec.ports[1].name: Duplicate value: "http"
```

**Solution**: Ensure each port has a unique name:
```yaml
ports:
- name: http
  port: 80
- name: http-alt  # Changed from 'http'
  port: 8080
```

---

## Key Takeaways

1. **Multi-port Services** enable complex application architectures
2. **Port names** are REQUIRED when a Service has multiple ports
3. Use **descriptive port names** (http, metrics, admin, etc.)
4. Each port in a Service can have different configurations
5. **targetPort** can reference Pod port names for flexibility
6. Create **separate Services** for different access patterns
7. Multi-port is common for apps with metrics/admin endpoints
8. Always **test each port** independently
9. Use `kubectl describe` to verify port mappings
10. Consider security implications of exposing multiple ports

---

## Best Practices

### 1. Use Named Ports in Pods

```yaml
# Good
ports:
- containerPort: 8080
  name: http
- containerPort: 9090
  name: metrics

# Then reference by name in Service
targetPort: http
```

### 2. Follow Naming Conventions

```yaml
# Standard names everyone understands
- name: http
- name: https
- name: grpc
- name: metrics
- name: admin
```

### 3. Separate Public and Private Ports

```yaml
# Public service (LoadBalancer)
ports:
- name: http
  port: 80
  targetPort: 8080

# Private service (ClusterIP)
ports:
- name: admin
  port: 9090
  targetPort: 9090
- name: metrics
  port: 9091
  targetPort: 9091
```

### 4. Document Port Purposes

```yaml
metadata:
  annotations:
    description: "Port 80 for public HTTP, Port 9090 for Prometheus metrics"
```

### 5. Use Consistent Port Numbers

```yaml
# All microservices use same metrics port
- name: metrics
  port: 9090
  targetPort: 9090
```

---

## Additional Commands Reference

```bash
# Create multi-port service from CLI
kubectl expose pod my-pod --port=80,8080 --name=multi-service

# Get service with custom columns
kubectl get service -o custom-columns=NAME:.metadata.name,PORTS:.spec.ports[*].port

# Test specific port
kubectl port-forward service/my-service 8080:80
kubectl port-forward service/my-service 9090:9090

# View all endpoints
kubectl get endpoints --all-namespaces

# Check which port a container is listening on
kubectl exec <pod-name> -- netstat -tlnp

# Test connectivity to specific port
kubectl run test --image=nicolaka/netshoot --rm -it -- bash
# Inside pod:
nc -zv my-service 8080
nc -zv my-service 9090

# Get Service YAML showing all ports
kubectl get service <service-name> -o yaml | grep -A 20 ports
```

---

## Next Steps

1. **Lab 12**: Learn about Ingress and EndpointSlices for advanced routing
2. **Advanced**: Implement service mesh (Istio/Linkerd) for advanced multi-port scenarios
3. **Practice**: Deploy a real application with HTTP, gRPC, and metrics ports

---

## Additional Reading

- [Kubernetes Services Documentation](https://kubernetes.io/docs/concepts/services-networking/service/)
- [Service Ports Configuration](https://kubernetes.io/docs/concepts/services-networking/service/#multi-port-services)
- [Port Naming Best Practices](https://kubernetes.io/docs/concepts/services-networking/service/#defining-a-service)
- [Service Discovery Patterns](https://kubernetes.io/docs/concepts/services-networking/service/#discovering-services)

---

**Lab Created**: March 2026
**Compatible with**: Kubernetes 1.24+
**Tested on**: Minikube, Kind, AWS EKS, GCP GKE
