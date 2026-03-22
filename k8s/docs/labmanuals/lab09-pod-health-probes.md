# Lab 09: Health Checks with Liveness and Readiness Probes

## Overview
In this lab, you will learn about Kubernetes health probes - liveness, readiness, and startup probes. You'll implement different probe types (exec, HTTP, and TCP), understand their use cases, configure probe parameters, and learn best practices for ensuring application health and reliability in production.

## Prerequisites
- A running Kubernetes cluster (Minikube, Kind, or any K8s cluster)
- `kubectl` CLI tool installed and configured
- Basic understanding of Pods and Deployments (Lab 01)
- Basic understanding of container health and lifecycle

## Learning Objectives
By the end of this lab, you will be able to:
- Understand the three types of health probes
- Implement exec, HTTP, and TCP liveness probes
- Configure readiness probes for traffic management
- Use startup probes for slow-starting applications
- Configure probe parameters (delays, timeouts, thresholds)
- Troubleshoot probe failures
- Apply probe best practices in production

---

## What are Kubernetes Health Probes?

**Health Probes** are diagnostic mechanisms that allow Kubernetes to check the health of your containers and take automatic actions based on the results.

### Three Types of Probes

1. **Liveness Probe**
   - Checks if container is alive
   - **Action**: Restarts container if probe fails
   - **Use Case**: Detect deadlocks, hung applications

2. **Readiness Probe**
   - Checks if container is ready to serve traffic
   - **Action**: Removes Pod from Service endpoints if probe fails
   - **Use Case**: Prevent traffic to not-ready Pods

3. **Startup Probe**
   - Checks if container has started successfully
   - **Action**: Disables liveness/readiness until successful
   - **Use Case**: Slow-starting applications

### Probe Mechanisms

| Mechanism | Description | Use Case |
|-----------|-------------|----------|
| **exec** | Executes command in container | File checks, custom scripts |
| **httpGet** | HTTP GET request | Web applications, REST APIs |
| **tcpSocket** | TCP connection check | Databases, TCP services |
| **grpc** | gRPC health check | gRPC services (K8s 1.24+) |

---

## Exercise 1: Liveness Probe with Exec Command

### Understanding the Scenario

We'll deploy a Pod that:
1. Creates a file `/tmp/healthy` at startup
2. Removes the file after 30 seconds
3. Has a liveness probe that checks for the file
4. Gets restarted when the file is missing

### Step 1: Review the Exec Liveness Probe

Navigate to the workloads directory:
```bash
cd k8s/labs/workloads
```

Let's examine `exec-liveness.yaml`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  labels:
    test: liveness
  name: liveness-exec
spec:
  containers:
  - name: liveness
    image: k8s.gcr.io/busybox
    args:
    - /bin/sh
    - -c
    - touch /tmp/healthy; sleep 30; rm -rf /tmp/healthy; sleep 600
    livenessProbe:
      exec:
        command:
        - cat
        - /tmp/healthy
      initialDelaySeconds: 5
      periodSeconds: 5
```

**Understanding the Manifest:**

- `args` - Container lifecycle:
  1. Creates `/tmp/healthy` file
  2. Sleeps 30 seconds (file exists)
  3. Removes `/tmp/healthy` file
  4. Sleeps 600 seconds (file missing)

- `livenessProbe.exec` - Probe configuration:
  - `command: cat /tmp/healthy` - Checks if file exists
  - `initialDelaySeconds: 5` - Wait 5s before first probe
  - `periodSeconds: 5` - Check every 5 seconds

**Expected Behavior:**
- First 30s: Probe succeeds (file exists)
- After 30s: Probe fails (file removed)
- After ~3 failures: Container restarts

### Step 2: Deploy the Pod

Apply the manifest:

```bash
kubectl apply -f exec-liveness.yaml
```

Expected output:
```
pod/liveness-exec created
```

### Step 3: Monitor Pod Behavior

Watch the Pod status:

```bash
kubectl get pod liveness-exec -w
```

Initial output:
```
NAME            READY   STATUS    RESTARTS   AGE
liveness-exec   1/1     Running   0          10s
```

After ~35 seconds, you'll see:
```
NAME            READY   STATUS    RESTARTS   AGE
liveness-exec   1/1     Running   0          35s
liveness-exec   1/1     Running   1          40s  # Container restarted
```

### Step 4: Investigate the Restart

Check Pod events:

```bash
kubectl describe pod liveness-exec
```

Look for events like:
```
Events:
  Type     Reason     Age               From               Message
  ----     ------     ----              ----               -------
  Normal   Scheduled  2m                default-scheduler  Successfully assigned default/liveness-exec to node01
  Normal   Pulled     2m                kubelet            Successfully pulled image
  Normal   Created    2m (x2 over 2m)   kubelet            Created container liveness
  Normal   Started    2m (x2 over 2m)   kubelet            Started container liveness
  Warning  Unhealthy  90s (x3 over 2m)  kubelet            Liveness probe failed: cat: can't open '/tmp/healthy': No such file or directory
  Normal   Killing    90s               kubelet            Container liveness failed liveness probe, will be restarted
```

**Key observations:**
- `Unhealthy` - Liveness probe failed 3 times
- `Killing` - Container was killed
- Container automatically restarted

Check restart count:

```bash
kubectl get pod liveness-exec -o jsonpath='{.status.containerStatuses[0].restartCount}'
```

### Step 5: View Container Logs

View current logs:

```bash
kubectl logs liveness-exec
```

View logs from previous container (before restart):

```bash
kubectl logs liveness-exec --previous
```

---

## Exercise 2: HTTP Liveness Probe

### Step 1: Create HTTP Liveness Probe Pod

Since we only have the exec example in the workloads folder, let's create an HTTP liveness probe example.

Create `http-liveness.yaml`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  labels:
    test: liveness
  name: liveness-http
spec:
  containers:
  - name: liveness
    image: k8s.gcr.io/liveness
    args:
    - /server
    livenessProbe:
      httpGet:
        path: /healthz
        port: 8080
        httpHeaders:
        - name: Custom-Header
          value: Awesome
      initialDelaySeconds: 3
      periodSeconds: 3
      timeoutSeconds: 1
      successThreshold: 1
      failureThreshold: 3
```

**Understanding the HTTP Probe:**

- `httpGet.path: /healthz` - HTTP endpoint to check
- `httpGet.port: 8080` - Port to connect to
- `httpHeaders` - Optional custom headers
- `timeoutSeconds: 1` - Timeout for the probe
- `successThreshold: 1` - Success after 1 successful probe
- `failureThreshold: 3` - Fail after 3 consecutive failures

**HTTP Status Codes:**
- **Success**: 200-399
- **Failure**: < 200 or >= 400

### Step 2: Deploy and Monitor

Apply the manifest:

```bash
kubectl apply -f http-liveness.yaml
```

Monitor the Pod:

```bash
kubectl get pod liveness-http -w
```

The `k8s.gcr.io/liveness` image returns:
- HTTP 200 for first 10 seconds
- HTTP 500 after 10 seconds
- Container will be restarted

Check events:

```bash
kubectl describe pod liveness-http | grep -A 10 Events
```

---

## Exercise 3: TCP Liveness Probe

### Step 1: Create TCP Liveness Probe Pod

Create `tcp-liveness.yaml`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  labels:
    test: liveness
  name: liveness-tcp
spec:
  containers:
  - name: nginx
    image: nginx:1.25
    ports:
    - containerPort: 80
    livenessProbe:
      tcpSocket:
        port: 80
      initialDelaySeconds: 15
      periodSeconds: 10
      timeoutSeconds: 2
      successThreshold: 1
      failureThreshold: 3
```

**Understanding the TCP Probe:**

- `tcpSocket.port: 80` - Checks if TCP port 80 is open
- Probe succeeds if TCP connection is established
- Probe fails if connection is refused or times out

### Step 2: Deploy and Test

Apply the manifest:

```bash
kubectl apply -f tcp-liveness.yaml
```

Check Pod status:

```bash
kubectl get pod liveness-tcp
```

Expected output:
```
NAME            READY   STATUS    RESTARTS   AGE
liveness-tcp    1/1     Running   0          30s
```

This Pod should stay healthy because NGINX keeps port 80 open.

### Step 3: Simulate Failure

Kill the NGINX process to simulate failure:

```bash
kubectl exec liveness-tcp -- /bin/sh -c "killall nginx"
```

Watch the Pod:

```bash
kubectl get pod liveness-tcp -w
```

The container will be restarted after ~30 seconds (failureThreshold * periodSeconds).

---

## Exercise 4: Readiness Probe

### Understanding Readiness vs Liveness

| Probe | Action on Failure | Use Case |
|-------|-------------------|----------|
| **Liveness** | Restart container | Detect hung applications |
| **Readiness** | Remove from Service | Prevent traffic to not-ready Pods |

### Step 1: Create Deployment with Readiness Probe

Create `readiness-demo.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: readiness-demo
spec:
  replicas: 3
  selector:
    matchLabels:
      app: readiness-demo
  template:
    metadata:
      labels:
        app: readiness-demo
    spec:
      containers:
      - name: nginx
        image: nginx:1.25
        ports:
        - containerPort: 80
        readinessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 5
          failureThreshold: 3
        livenessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 10
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: readiness-demo
spec:
  selector:
    app: readiness-demo
  ports:
  - port: 80
    targetPort: 80
  type: ClusterIP
```

### Step 2: Deploy and Create Service

Apply the manifest:

```bash
kubectl apply -f readiness-demo.yaml
```

Check Pods:

```bash
kubectl get pods -l app=readiness-demo
```

Expected output:
```
NAME                              READY   STATUS    RESTARTS   AGE
readiness-demo-xxxxxxxxxx-xxxxx   1/1     Running   0          30s
readiness-demo-xxxxxxxxxx-yyyyy   1/1     Running   0          30s
readiness-demo-xxxxxxxxxx-zzzzz   1/1     Running   0          30s
```

### Step 3: Check Service Endpoints

View Service endpoints:

```bash
kubectl get endpoints readiness-demo
```

Expected output:
```
NAME             ENDPOINTS                                      AGE
readiness-demo   10.244.1.5:80,10.244.1.6:80,10.244.2.5:80      1m
```

All 3 Pods are registered as endpoints.

### Step 4: Simulate Readiness Failure

Stop NGINX in one Pod to make it not ready:

```bash
POD_NAME=$(kubectl get pods -l app=readiness-demo -o jsonpath='{.items[0].metadata.name}')
kubectl exec $POD_NAME -- nginx -s stop
```

Check Pod status:

```bash
kubectl get pods -l app=readiness-demo
```

Expected output:
```
NAME                              READY   STATUS    RESTARTS   AGE
readiness-demo-xxxxxxxxxx-xxxxx   0/1     Running   0          2m  # Not Ready
readiness-demo-xxxxxxxxxx-yyyyy   1/1     Running   0          2m
readiness-demo-xxxxxxxxxx-zzzzz   1/1     Running   0          2m
```

Check endpoints again:

```bash
kubectl get endpoints readiness-demo
```

Expected output:
```
NAME             ENDPOINTS                       AGE
readiness-demo   10.244.1.6:80,10.244.2.5:80     2m
```

**The not-ready Pod is removed from endpoints!** Traffic won't be sent to it.

### Step 5: Observe Container Restart

Wait and watch the Pod:

```bash
kubectl get pods -l app=readiness-demo -w
```

After liveness probe failures, the container will be restarted and become ready again.

---

## Exercise 5: Startup Probe for Slow Applications

### Understanding Startup Probes

**Startup Probes** are useful for:
- Applications with long initialization times
- Prevents premature liveness probe failures
- Disables liveness/readiness checks until startup succeeds

### Step 1: Create Slow-Starting Application

Create `startup-probe.yaml`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  labels:
    test: startup
  name: startup-demo
spec:
  containers:
  - name: slow-app
    image: busybox
    args:
    - /bin/sh
    - -c
    - |
      echo "Starting slow initialization..."
      sleep 60
      echo "Initialization complete"
      touch /tmp/ready
      sleep 3600
    startupProbe:
      exec:
        command:
        - cat
        - /tmp/ready
      initialDelaySeconds: 0
      periodSeconds: 5
      failureThreshold: 30  # 30 * 5 = 150s maximum startup time
    livenessProbe:
      exec:
        command:
        - cat
        - /tmp/ready
      initialDelaySeconds: 0
      periodSeconds: 10
    readinessProbe:
      exec:
        command:
        - cat
        - /tmp/ready
      initialDelaySeconds: 0
      periodSeconds: 5
```

**Understanding the Configuration:**

- Application takes 60 seconds to initialize
- `startupProbe` allows up to 150 seconds (30 failures * 5s period)
- Liveness/readiness probes disabled until startup succeeds
- After startup success, liveness/readiness probes activate

### Step 2: Deploy and Monitor

Apply the manifest:

```bash
kubectl apply -f startup-probe.yaml
```

Watch the Pod:

```bash
kubectl get pod startup-demo -w
```

Check probe status during startup:

```bash
kubectl describe pod startup-demo | grep -A 5 "Startup:"
```

After ~60 seconds, all probes will succeed.

---

## Exercise 6: Configuring Probe Parameters

### Understanding Probe Parameters

```yaml
livenessProbe:
  httpGet:
    path: /healthz
    port: 8080
  initialDelaySeconds: 30    # Wait before first probe
  periodSeconds: 10          # Probe frequency
  timeoutSeconds: 5          # Timeout for probe response
  successThreshold: 1        # Success after X consecutive successes
  failureThreshold: 3        # Fail after X consecutive failures
```

### Parameter Guidelines

| Parameter | Liveness | Readiness | Startup |
|-----------|----------|-----------|---------|
| `initialDelaySeconds` | App startup time | 0-5s | 0 |
| `periodSeconds` | 10-30s | 5-10s | 5-10s |
| `timeoutSeconds` | 1-5s | 1-5s | 1-5s |
| `successThreshold` | 1 | 1 | 1 |
| `failureThreshold` | 3 | 3 | 30 |

### Example: Fine-Tuned Probes

Create `tuned-probes.yaml`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: tuned-probes
spec:
  containers:
  - name: app
    image: nginx:1.25
    ports:
    - containerPort: 80
    startupProbe:
      httpGet:
        path: /
        port: 80
      initialDelaySeconds: 0
      periodSeconds: 5
      timeoutSeconds: 3
      failureThreshold: 12      # 60s maximum startup time
    livenessProbe:
      httpGet:
        path: /
        port: 80
      initialDelaySeconds: 0
      periodSeconds: 15
      timeoutSeconds: 2
      failureThreshold: 2       # Restart after 30s unhealthy
    readinessProbe:
      httpGet:
        path: /
        port: 80
      initialDelaySeconds: 0
      periodSeconds: 5
      timeoutSeconds: 2
      failureThreshold: 2       # Remove from service after 10s not ready
      successThreshold: 1       # Add back after 1 success
```

Apply and test:

```bash
kubectl apply -f tuned-probes.yaml
kubectl describe pod tuned-probes
```

---

## Exercise 7: Debugging Probe Failures

### Step 1: Identify Failing Probes

List Pods with issues:

```bash
kubectl get pods --field-selector status.phase!=Running,status.phase!=Succeeded
```

Check Pod events:

```bash
kubectl describe pod <pod-name> | grep -A 10 Events
```

### Step 2: Test Probe Manually

For exec probes:

```bash
kubectl exec <pod-name> -- cat /tmp/healthy
```

For HTTP probes:

```bash
kubectl exec <pod-name> -- curl -f http://localhost:8080/healthz
```

For TCP probes:

```bash
kubectl exec <pod-name> -- nc -zv localhost 8080
```

### Step 3: Check Probe Configuration

```bash
kubectl get pod <pod-name> -o yaml | grep -A 20 livenessProbe
```

### Common Issues and Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| Probe fails immediately | `initialDelaySeconds` too short | Increase delay |
| Frequent restarts | Probe too aggressive | Increase `failureThreshold` or `periodSeconds` |
| Slow traffic routing | Readiness probe too conservative | Decrease `periodSeconds` |
| Startup timeouts | Slow initialization | Use startup probe |
| Port not open | Wrong port number | Verify container port |

---

## Lab Cleanup

Remove all probe demonstration Pods:

```bash
# Delete individual Pods
kubectl delete pod liveness-exec
kubectl delete pod liveness-http
kubectl delete pod liveness-tcp
kubectl delete pod startup-demo
kubectl delete pod tuned-probes

# Delete Deployment and Service
kubectl delete deployment readiness-demo
kubectl delete service readiness-demo

# Verify cleanup
kubectl get pods
```

---

## Key Takeaways

1. **Liveness Probes** - Restart unhealthy containers
2. **Readiness Probes** - Control traffic routing
3. **Startup Probes** - Handle slow-starting applications
4. **Three Mechanisms** - Exec, HTTP, TCP (and gRPC)
5. **Tune Parameters** - Balance responsiveness vs stability
6. **Always Use Both** - Liveness AND readiness in production
7. **Test Thoroughly** - Verify probe behavior under load
8. **Monitor Failures** - Set alerts for probe failures

---

## Best Practices

### 1. Always Implement Readiness Probes

```yaml
# Prevents traffic to not-ready Pods
readinessProbe:
  httpGet:
    path: /ready
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 5
```

### 2. Use Startup Probes for Slow Apps

```yaml
# For apps taking > 30s to start
startupProbe:
  httpGet:
    path: /healthz
    port: 8080
  failureThreshold: 30
  periodSeconds: 5
```

### 3. Design Lightweight Health Checks

```python
# Good: Fast, simple check
@app.route('/healthz')
def health():
    return 'OK', 200

# Bad: Heavy database queries
@app.route('/healthz')
def health():
    # Don't do expensive operations
    db.query('SELECT * FROM users')
    return 'OK', 200
```

### 4. Use Different Endpoints

```yaml
# Liveness: Basic check (app alive?)
livenessProbe:
  httpGet:
    path: /healthz   # Simple "am I alive" check

# Readiness: Dependency check (can I serve traffic?)
readinessProbe:
  httpGet:
    path: /ready     # Check DB connections, caches, etc.
```

### 5. Set Appropriate Timeouts

```yaml
# Fast response expected
timeoutSeconds: 1

# Network dependency involved
timeoutSeconds: 5
```

### 6. Conservative Failure Thresholds

```yaml
# Don't restart on single failure
failureThreshold: 3

# For startup, allow more time
startupProbe:
  failureThreshold: 30
```

---

## Real-World Example: Microservice with All Probes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: user-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: user-service
  template:
    metadata:
      labels:
        app: user-service
    spec:
      containers:
      - name: user-service
        image: mycompany/user-service:v1.5
        ports:
        - containerPort: 8080
          name: http
        env:
        - name: DB_HOST
          value: "postgres-service"
        resources:
          requests:
            cpu: 200m
            memory: 256Mi
          limits:
            cpu: 500m
            memory: 512Mi

        # Startup: Handles initialization (DB migration, cache warmup)
        startupProbe:
          httpGet:
            path: /startup
            port: 8080
          initialDelaySeconds: 0
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 24     # 2 minutes max startup

        # Liveness: Detects deadlocks, hung threads
        livenessProbe:
          httpGet:
            path: /healthz
            port: 8080
          initialDelaySeconds: 0   # Startup probe protects this
          periodSeconds: 15
          timeoutSeconds: 2
          failureThreshold: 3      # 45s unhealthy = restart

        # Readiness: Checks dependencies (DB, cache, external API)
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 0
          periodSeconds: 5
          timeoutSeconds: 2
          successThreshold: 1
          failureThreshold: 2      # 10s not ready = remove from service
```

**Health Check Endpoints Implementation:**

```python
from flask import Flask, jsonify
import psycopg2

app = Flask(__name__)

@app.route('/startup')
def startup():
    """Startup probe: Check if initialization is complete"""
    if not app.config.get('INITIALIZED'):
        return 'Not initialized', 503
    return 'Started', 200

@app.route('/healthz')
def liveness():
    """Liveness probe: Simple check that app is alive"""
    # Quick check - don't check dependencies
    return 'OK', 200

@app.route('/ready')
def readiness():
    """Readiness probe: Check if ready to serve traffic"""
    try:
        # Check critical dependencies
        db = psycopg2.connect(app.config['DB_URL'])
        db.close()

        # Check cache connection
        redis_client.ping()

        return 'Ready', 200
    except Exception as e:
        return f'Not ready: {str(e)}', 503
```

---

## Additional Commands Reference

```bash
# View probe configuration
kubectl describe pod <pod-name> | grep -A 10 "Liveness:\|Readiness:\|Startup:"

# Get probe status
kubectl get pod <pod-name> -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}'

# View probe events
kubectl get events --field-selector involvedObject.name=<pod-name>,reason=Unhealthy

# Check container restart count
kubectl get pod <pod-name> -o jsonpath='{.status.containerStatuses[0].restartCount}'

# View last termination reason
kubectl get pod <pod-name> -o jsonpath='{.status.containerStatuses[0].lastState.terminated.reason}'

# Export Pod YAML with probes
kubectl get pod <pod-name> -o yaml > pod-with-probes.yaml
```

---

## Troubleshooting Guide

### Probe Failing: File Not Found (Exec)

```bash
# Test command manually
kubectl exec <pod-name> -- cat /tmp/healthy

# Check file permissions
kubectl exec <pod-name> -- ls -la /tmp/

# Verify file creation in logs
kubectl logs <pod-name>
```

### Probe Failing: HTTP 404/500

```bash
# Test HTTP endpoint manually
kubectl exec <pod-name> -- curl -v http://localhost:8080/healthz

# Check application logs
kubectl logs <pod-name>

# Verify port is correct
kubectl get pod <pod-name> -o yaml | grep containerPort
```

### Probe Failing: Connection Refused (TCP)

```bash
# Check if port is listening
kubectl exec <pod-name> -- netstat -tlnp

# Test connection
kubectl exec <pod-name> -- nc -zv localhost 8080

# Check application status
kubectl exec <pod-name> -- ps aux
```

### Too Many Restarts

```bash
# Increase initialDelaySeconds
kubectl patch deployment <name> --type='json' -p='[
  {
    "op": "replace",
    "path": "/spec/template/spec/containers/0/livenessProbe/initialDelaySeconds",
    "value": 60
  }
]'

# Or increase failureThreshold
kubectl patch deployment <name> --type='json' -p='[
  {
    "op": "replace",
    "path": "/spec/template/spec/containers/0/livenessProbe/failureThreshold",
    "value": 5
  }
]'
```

---

## Next Steps

Now that you understand health probes, continue exploring:
- ConfigMaps and Secrets for application configuration
- Persistent Volumes for stateful applications
- StatefulSets for stateful workloads
- Ingress Controllers for advanced routing

## Further Reading

- [Kubernetes Liveness and Readiness Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
- [Pod Lifecycle](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/)
- [Container Probes](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#container-probes)
- [Best Practices for Health Checks](https://kubernetes.io/docs/concepts/configuration/liveness-readiness-startup-probes/)

---

**Lab Created**: March 2026
**Compatible with**: Kubernetes 1.24+
