# Lab 21: Pod Lifecycle Hooks and Multi-Container Patterns

## Overview
In this lab, you will learn about Pod lifecycle hooks (postStart and preStop) and multi-container patterns including sidecar, ambassador, and adapter patterns. These advanced concepts enable sophisticated application architectures and operational workflows.

## Prerequisites
- A running Kubernetes cluster (Minikube, Kind, or any K8s cluster)
- `kubectl` CLI tool installed and configured
- Completion of Lab 01 (Creating Pods) and Lab 25 (Init Containers) is recommended
- Basic understanding of container networking and logging

## Learning Objectives
By the end of this lab, you will be able to:
- Understand the complete Pod lifecycle
- Implement postStart and preStop lifecycle hooks
- Create multi-container Pods
- Implement the sidecar pattern for logging and monitoring
- Implement the ambassador pattern for proxy functionality
- Implement the adapter pattern for standardizing output
- Choose the appropriate pattern for different use cases
- Debug multi-container Pods effectively

---

## Part 1: Pod Lifecycle and Hooks

### Understanding Pod Lifecycle

A Pod goes through several phases during its lifecycle:

1. **Pending**: Pod accepted but containers not yet created
2. **Running**: Pod bound to node, containers created and running
3. **Succeeded**: All containers terminated successfully
4. **Failed**: All containers terminated, at least one failed
5. **Unknown**: Pod state cannot be determined

### Container Lifecycle Hooks

Kubernetes provides two lifecycle hooks for containers:

#### 1. postStart Hook
- **Runs**: Immediately after container is created
- **Timing**: No guarantee it runs before container ENTRYPOINT
- **Use cases**: Registration, notification, setup tasks
- **Blocking**: Can delay container from reaching Running state

#### 2. preStop Hook
- **Runs**: Immediately before container is terminated
- **Timing**: Synchronous - termination waits for hook to complete
- **Use cases**: Graceful shutdown, cleanup, deregistration
- **Timeout**: Respects terminationGracePeriodSeconds

### Hook Handler Types

1. **Exec**: Executes a command inside the container
2. **HTTP**: Sends HTTP request to container endpoint

---

## Exercise 1: Basic Lifecycle Hooks

### Step 1: Create a Pod with Lifecycle Hooks

Create a Pod with both postStart and preStop hooks:

```bash
cat > lifecycle-hooks-pod.yaml <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: lifecycle-demo
  labels:
    app: lifecycle
spec:
  containers:
  - name: nginx
    image: nginx
    lifecycle:
      postStart:
        exec:
          command:
          - sh
          - -c
          - |
            echo "Container started at \$(date)" > /usr/share/nginx/html/startup.html
            echo "postStart hook executed" >> /var/log/lifecycle.log
      preStop:
        exec:
          command:
          - sh
          - -c
          - |
            echo "Container stopping at \$(date)" >> /var/log/lifecycle.log
            echo "Performing graceful shutdown..."
            sleep 5
            echo "preStop hook completed" >> /var/log/lifecycle.log
    volumeMounts:
    - name: log-volume
      mountPath: /var/log
  volumes:
  - name: log-volume
    emptyDir: {}
EOF
```

**Understanding the manifest:**
- `postStart` hook creates a startup.html file and logs the event
- `preStop` hook logs shutdown event and performs 5-second graceful shutdown
- Shared volume persists logs during container lifecycle
- Both hooks use shell commands via `exec`

### Step 2: Deploy and Test postStart Hook

Apply the manifest:
```bash
kubectl apply -f lifecycle-hooks-pod.yaml
```

Wait for Pod to be running:
```bash
kubectl get pod lifecycle-demo -w
```

Check if postStart hook executed:
```bash
kubectl exec lifecycle-demo -- cat /usr/share/nginx/html/startup.html
```

Expected output:
```
Container started at Mon Jan 15 10:00:00 UTC 2026
```

Check the lifecycle log:
```bash
kubectl exec lifecycle-demo -- cat /var/log/lifecycle.log
```

Expected output:
```
postStart hook executed
```

### Step 3: Test preStop Hook

Delete the Pod to trigger preStop hook:
```bash
kubectl delete pod lifecycle-demo
```

The deletion will take about 5 seconds due to the sleep in preStop hook.

To verify the preStop hook ran, we need to capture logs before deletion. Let's create a more observable version:

```bash
cat > lifecycle-hooks-observable.yaml <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: lifecycle-observable
spec:
  containers:
  - name: nginx
    image: nginx
    lifecycle:
      postStart:
        exec:
          command:
          - sh
          - -c
          - |
            echo "\$(date): postStart hook started" | tee -a /usr/share/message.log
            sleep 2
            echo "\$(date): postStart hook completed" | tee -a /usr/share/message.log
      preStop:
        exec:
          command:
          - sh
          - -c
          - |
            echo "\$(date): preStop hook started" | tee -a /usr/share/message.log
            echo "Draining connections..."
            sleep 5
            echo "\$(date): preStop hook completed" | tee -a /usr/share/message.log
    volumeMounts:
    - name: shared-logs
      mountPath: /usr/share
  - name: log-watcher
    image: busybox
    command:
    - sh
    - -c
    - |
      echo "Log watcher started"
      tail -f /usr/share/message.log
    volumeMounts:
    - name: shared-logs
      mountPath: /usr/share
  volumes:
  - name: shared-logs
    emptyDir: {}
EOF
```

Apply and monitor:
```bash
kubectl apply -f lifecycle-hooks-observable.yaml
```

Watch logs from log-watcher container:
```bash
kubectl logs lifecycle-observable -c log-watcher -f
```

In another terminal, delete the Pod:
```bash
kubectl delete pod lifecycle-observable
```

You'll see the preStop hook messages in the log-watcher output before the Pod terminates.

---

## Exercise 2: HTTP Lifecycle Hooks

### Step 1: Create a Pod with HTTP Hooks

```bash
cat > http-lifecycle-pod.yaml <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: http-lifecycle
spec:
  containers:
  - name: app-server
    image: nginx
    ports:
    - containerPort: 80
    lifecycle:
      postStart:
        httpGet:
          path: /startup
          port: 80
          scheme: HTTP
      preStop:
        httpGet:
          path: /shutdown
          port: 80
          scheme: HTTP
  - name: lifecycle-handler
    image: hashicorp/http-echo
    args:
    - "-text=Lifecycle handler running"
    ports:
    - containerPort: 5678
EOF
```

**Note**: This example will fail because nginx doesn't have /startup and /shutdown endpoints. Let's create a more realistic example:

```bash
cat > http-lifecycle-working.yaml <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: http-lifecycle-working
spec:
  containers:
  - name: main-app
    image: busybox
    command:
    - sh
    - -c
    - |
      echo "Starting web server..."
      mkdir -p /www
      cat > /www/index.html <<HTML
      <html><body>Main Application</body></html>
      HTML
      cd /www
      httpd -f -p 8080
    ports:
    - containerPort: 8080
    lifecycle:
      postStart:
        exec:
          command:
          - sh
          - -c
          - |
            # Wait for server to be ready
            sleep 3
            echo "Application registered with service mesh"
      preStop:
        exec:
          command:
          - sh
          - -c
          - |
            echo "Deregistering from service mesh"
            sleep 5
            echo "Deregistration complete"
EOF
```

---

## Exercise 3: Lifecycle Hook Failure Handling

### Understanding Hook Failures

- If postStart fails, the container is killed
- If preStop fails, the container continues termination
- Hook failures are logged in Pod events

### Step 1: Create a Pod with Failing postStart Hook

```bash
cat > failing-poststart.yaml <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: failing-poststart
spec:
  containers:
  - name: nginx
    image: nginx
    lifecycle:
      postStart:
        exec:
          command:
          - sh
          - -c
          - |
            echo "postStart hook starting..."
            exit 1  # Simulate failure
  restartPolicy: Never
EOF
```

Apply and observe:
```bash
kubectl apply -f failing-poststart.yaml
kubectl get pod failing-poststart -w
```

Check Pod events:
```bash
kubectl describe pod failing-poststart
```

Look for events showing the postStart hook failure.

---

## Part 2: Multi-Container Patterns

### Understanding Multi-Container Pods

Multiple containers in a Pod:
- Share the same network namespace (localhost communication)
- Share the same storage volumes
- Are scheduled together on the same node
- Start and stop together as a unit

### Common Patterns

1. **Sidecar**: Helper container that enhances the main container
2. **Ambassador**: Proxy container that represents the main container to the outside world
3. **Adapter**: Transforms the output of the main container to a standard format

---

## Exercise 4: Basic Multi-Container Pod

### Step 1: Review and Deploy Multi-Container Pod

Let's look at the existing `multi-pod.yaml`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: multicontainer-pod
spec:
  containers:
  # Container 01
  - name: web
    image: nginx
    ports:
    - containerPort: 80
  # Container 02
  - name: redis
    image: redis
    ports:
    - containerPort: 6379
```

Deploy the Pod:
```bash
cd k8s/labs/workloads
kubectl apply -f multi-pod.yaml
```

Verify both containers are running:
```bash
kubectl get pod multicontainer-pod
```

Expected output:
```
NAME                  READY   STATUS    RESTARTS   AGE
multicontainer-pod    2/2     Running   0          10s
```

Notice `READY` shows `2/2` - both containers are running.

### Step 2: Test Container Communication

Containers in the same Pod can communicate via localhost:

Execute command in the web container to reach redis:
```bash
kubectl exec multicontainer-pod -c web -- curl -s localhost:6379
```

This demonstrates that both containers share the same network namespace.

View logs from specific containers:
```bash
kubectl logs multicontainer-pod -c web
kubectl logs multicontainer-pod -c redis
```

### Step 3: Explore Container Details

Get detailed information about both containers:
```bash
kubectl describe pod multicontainer-pod
```

Look at the Containers section showing both containers with their individual resource usage.

---

## Exercise 5: Sidecar Pattern - Log Aggregation

### Understanding the Sidecar Pattern

The sidecar pattern uses a helper container that runs alongside the main application to provide supporting functionality without modifying the main application.

**Common use cases:**
- Log shipping and aggregation
- Monitoring and metrics collection
- Service mesh proxies (Envoy, Istio)
- Configuration synchronization
- SSL/TLS termination

### Step 1: Create a Sidecar Logging Container

```bash
cat > sidecar-logging-pod.yaml <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: sidecar-logging
  labels:
    app: myapp
spec:
  containers:
  # Main application container
  - name: application
    image: busybox
    command:
    - sh
    - -c
    - |
      echo "Application starting..."
      while true; do
        echo "\$(date): Processing request ID \$RANDOM" >> /var/log/app.log
        sleep 5
      done
    volumeMounts:
    - name: log-volume
      mountPath: /var/log

  # Sidecar container for log shipping
  - name: log-shipper
    image: busybox
    command:
    - sh
    - -c
    - |
      echo "Log shipper started"
      while true; do
        if [ -f /var/log/app.log ]; then
          echo "=== Shipping logs to central system ==="
          tail -n 5 /var/log/app.log
          echo "=== End of log batch ==="
          sleep 10
        else
          echo "Waiting for log file..."
          sleep 2
        fi
      done
    volumeMounts:
    - name: log-volume
      mountPath: /var/log

  volumes:
  - name: log-volume
    emptyDir: {}
EOF
```

**Understanding the pattern:**
- Main container writes logs to a shared volume
- Sidecar container reads from the same volume
- Sidecar "ships" logs (simulated with echo)
- Both containers run continuously
- Neither container needs to know about the other

### Step 2: Deploy and Monitor

Apply the manifest:
```bash
kubectl apply -f sidecar-logging-pod.yaml
```

Watch the application container:
```bash
kubectl logs sidecar-logging -c application -f
```

In another terminal, watch the log-shipper:
```bash
kubectl logs sidecar-logging -c log-shipper -f
```

You'll see the sidecar reading and "shipping" logs from the main application.

### Step 3: Test Container Interaction

Access the shared log file from both containers:

From application container:
```bash
kubectl exec sidecar-logging -c application -- tail /var/log/app.log
```

From log-shipper container:
```bash
kubectl exec sidecar-logging -c log-shipper -- tail /var/log/app.log
```

Both see the same file!

---

## Exercise 6: Sidecar Pattern - Metrics Collection

### Step 1: Create a Metrics Exporter Sidecar

```bash
cat > sidecar-metrics-pod.yaml <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: sidecar-metrics
spec:
  containers:
  # Main application
  - name: webapp
    image: busybox
    command:
    - sh
    - -c
    - |
      mkdir -p /tmp/metrics
      echo "Web application started"
      while true; do
        # Simulate application metrics
        REQUESTS=\$((RANDOM % 1000))
        LATENCY=\$((RANDOM % 500))
        echo "requests_total \$REQUESTS" > /tmp/metrics/metrics.txt
        echo "request_latency_ms \$LATENCY" >> /tmp/metrics/metrics.txt
        sleep 5
      done
    volumeMounts:
    - name: metrics-volume
      mountPath: /tmp/metrics

  # Metrics exporter sidecar
  - name: metrics-exporter
    image: busybox
    command:
    - sh
    - -c
    - |
      echo "Metrics exporter started on port 9090"
      mkdir -p /www
      while true; do
        if [ -f /tmp/metrics/metrics.txt ]; then
          cp /tmp/metrics/metrics.txt /www/metrics
          echo "Metrics updated: \$(cat /www/metrics)"
        fi
        sleep 3
      done
    volumeMounts:
    - name: metrics-volume
      mountPath: /tmp/metrics
    ports:
    - containerPort: 9090
      name: metrics

  volumes:
  - name: metrics-volume
    emptyDir: {}
EOF
```

### Step 2: Deploy and Monitor Metrics

Apply the manifest:
```bash
kubectl apply -f sidecar-metrics-pod.yaml
```

Check metrics from the exporter:
```bash
kubectl logs sidecar-metrics -c metrics-exporter -f
```

View application logs:
```bash
kubectl logs sidecar-metrics -c webapp
```

---

## Exercise 7: Modern Sidecar Containers with restartPolicy (K8s 1.28+)

### Understanding the New Sidecar Specification

Starting with Kubernetes 1.28, a new feature allows init containers to run as true sidecars throughout the Pod's lifecycle by using `restartPolicy: Always`. This provides a cleaner and more explicit way to define sidecar containers compared to the traditional pattern.

**Key advantages of the new sidecar spec:**
- **Proper startup ordering**: Sidecar starts before main containers
- **Runs throughout Pod lifecycle**: Continues running alongside main containers
- **Explicit intent**: Clearly declares a container as a sidecar
- **Better semantics**: Uses init container ordering with sidecar behavior

### Comparison: Old Sidecar Pattern vs New Sidecar Spec

| Feature | Old Sidecar Pattern | New Sidecar Spec |
|---------|-------------------|-----------------|
| **Definition** | Regular container | Init container with `restartPolicy: Always` |
| **Startup Order** | Simultaneous with main app | Starts and reaches ready state before main app |
| **Lifecycle** | Runs throughout Pod lifecycle | Runs throughout Pod lifecycle |
| **Kubernetes Version** | All versions | 1.28+ |
| **Clarity** | Implicit sidecar behavior | Explicit sidecar declaration |
| **Use Case** | Works everywhere | Better semantics and ordering |

### Step 1: Review the New Sidecar Container Specification

Let's examine the modern sidecar specification:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: modern-sidecar-demo
spec:
  initContainers:
  - name: sidecar-logger
    image: busybox
    restartPolicy: Always  # New in 1.28 - makes this a sidecar
    command:
    - sh
    - -c
    - |
      while true; do
        echo "[$(date)] Sidecar is running" >> /shared/sidecar.log
        sleep 5
      done
    volumeMounts:
    - name: shared-logs
      mountPath: /shared
  containers:
  - name: main-app
    image: nginx
    volumeMounts:
    - name: shared-logs
      mountPath: /usr/share/nginx/html
  volumes:
  - name: shared-logs
    emptyDir: {}
```

**Understanding the specification:**
- Init container with `restartPolicy: Always` runs as a sidecar
- Sidecar starts first and must be ready before main container
- Sidecar continues running throughout Pod lifecycle
- If sidecar crashes, it restarts (due to `restartPolicy: Always`)
- Main app can access sidecar's output through shared volume

### Step 2: Deploy and Test the Modern Sidecar

Deploy the modern sidecar demo:
```bash
cd k8s/labs/workloads
kubectl apply -f sidecar-container-spec.yaml
```

Wait for Pod to be running:
```bash
kubectl get pod modern-sidecar-demo -w
```

**Expected behavior:**
1. Sidecar logger init container starts first
2. Once sidecar is running, main-app container starts
3. Both containers run simultaneously

### Step 3: Verify Sidecar Behavior

Check the sidecar logger output:
```bash
kubectl logs modern-sidecar-demo -c sidecar-logger
```

Expected output:
```
[Mon Mar 16 10:00:00 UTC 2026] Sidecar is running
[Mon Mar 16 10:00:05 UTC 2026] Sidecar is running
[Mon Mar 16 10:00:10 UTC 2026] Sidecar is running
```

Access the shared logs from the main container:
```bash
kubectl exec modern-sidecar-demo -c main-app -- cat /usr/share/nginx/html/sidecar.log
```

You'll see the log entries written by the sidecar, accessible to the main application!

### Step 4: Test Sidecar Restart Behavior

Simulate a sidecar crash to observe the restart policy:
```bash
kubectl exec modern-sidecar-demo -c sidecar-logger -- kill 1
```

Check Pod status:
```bash
kubectl get pod modern-sidecar-demo
```

Watch the sidecar restart:
```bash
kubectl get pod modern-sidecar-demo -w
```

The sidecar will automatically restart due to `restartPolicy: Always`, while the main container continues running!

### Step 5: Compare Startup Order

To see the startup order difference, describe the Pod:
```bash
kubectl describe pod modern-sidecar-demo
```

Look at the **Init Containers** section and notice the sidecar logger with its restart policy.

### When to Use Modern Sidecar Spec

**Use the new sidecar spec when:**
- Running on Kubernetes 1.28 or newer
- Sidecar must start before main application
- You want explicit sidecar semantics
- Startup ordering is critical (e.g., proxy must be ready first)

**Use traditional sidecar pattern when:**
- Need compatibility with older Kubernetes versions
- Startup order doesn't matter
- Want simultaneous container startup

### Real-World Use Cases

**1. Service Mesh Proxy (Istio/Envoy)**
```yaml
initContainers:
- name: envoy-proxy
  image: envoyproxy/envoy:v1.28
  restartPolicy: Always
  # Proxy must be ready before app starts
```

**2. Log Aggregator (Fluentd)**
```yaml
initContainers:
- name: fluentd
  image: fluent/fluentd:v1.16
  restartPolicy: Always
  # Logging infrastructure ready before app logs
```

**3. Security Agent**
```yaml
initContainers:
- name: security-agent
  image: mycompany/security-agent:latest
  restartPolicy: Always
  # Security monitoring active before app starts
```

### Cleanup

Remove the modern sidecar demo:
```bash
kubectl delete pod modern-sidecar-demo
```

---

## Exercise 8: Ambassador Pattern - Proxy Container

### Understanding the Ambassador Pattern

The ambassador pattern uses a proxy container to handle external connections, simplifying the main application's networking logic.

**Common use cases:**
- Database connection pooling
- Circuit breaking
- Rate limiting
- Protocol translation
- Service discovery

### Step 1: Create an Ambassador Proxy

```bash
cat > ambassador-pod.yaml <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: ambassador-pattern
spec:
  containers:
  # Main application
  - name: application
    image: busybox
    command:
    - sh
    - -c
    - |
      echo "Application started"
      echo "Connecting to database via ambassador at localhost:3306"
      while true; do
        echo "\$(date): Executing query via localhost:3306"
        # In real scenario, app connects to localhost:3306
        # Ambassador forwards to actual database
        sleep 10
      done

  # Ambassador proxy container
  - name: db-ambassador
    image: busybox
    command:
    - sh
    - -c
    - |
      echo "Ambassador proxy started"
      echo "Listening on port 3306"
      echo "Forwarding to mysql-service:3306"
      while true; do
        echo "\$(date): Ambassador: Proxying database connection"
        echo "         - Connection pooling enabled"
        echo "         - Circuit breaker: CLOSED"
        echo "         - Active connections: \$((RANDOM % 10))"
        sleep 15
      done
    ports:
    - containerPort: 3306
      name: mysql-proxy
EOF
```

**Understanding the pattern:**
- Application connects to `localhost:3306`
- Ambassador container listens on port 3306 in the Pod
- Ambassador handles connection pooling, retries, circuit breaking
- Application is simpler - just connects to localhost
- Ambassador can be updated independently

### Step 2: Deploy and Monitor

Apply the manifest:
```bash
kubectl apply -f ambassador-pod.yaml
```

Watch the application:
```bash
kubectl logs ambassador-pattern -c application -f
```

Watch the ambassador:
```bash
kubectl logs ambassador-pattern -c db-ambassador -f
```

---

## Exercise 9: Adapter Pattern - Log Formatting

### Understanding the Adapter Pattern

The adapter pattern uses a container to transform or standardize the output of the main container, making it compatible with external systems.

**Common use cases:**
- Log format standardization (convert to JSON)
- Metrics format conversion (Prometheus, StatsD)
- Data transformation
- Protocol adaptation

### Step 1: Create an Adapter Container

```bash
cat > adapter-pod.yaml <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: adapter-pattern
spec:
  containers:
  # Main application with non-standard log format
  - name: legacy-app
    image: busybox
    command:
    - sh
    - -c
    - |
      echo "Legacy application started"
      mkdir -p /var/log/app
      while true; do
        # Logs in custom format: TIMESTAMP|LEVEL|MESSAGE
        echo "\$(date +%s)|\$((RANDOM % 4))|User action: operation_\$RANDOM" >> /var/log/app/legacy.log
        sleep 3
      done
    volumeMounts:
    - name: log-volume
      mountPath: /var/log/app

  # Adapter container that transforms logs to JSON
  - name: log-adapter
    image: busybox
    command:
    - sh
    - -c
    - |
      echo "Log adapter started"
      echo "Converting legacy logs to JSON format"
      while true; do
        if [ -f /var/log/app/legacy.log ]; then
          # Read last line and convert to JSON
          tail -n 1 /var/log/app/legacy.log | while IFS='|' read timestamp level message; do
            if [ -n "\$timestamp" ]; then
              echo "{\"timestamp\": \$timestamp, \"level\": \$level, \"message\": \"\$message\"}"
            fi
          done
          sleep 3
        else
          sleep 1
        fi
      done
    volumeMounts:
    - name: log-volume
      mountPath: /var/log/app

  volumes:
  - name: log-volume
    emptyDir: {}
EOF
```

**Understanding the pattern:**
- Legacy app writes logs in custom format: `TIMESTAMP|LEVEL|MESSAGE`
- Adapter reads these logs from shared volume
- Adapter transforms to JSON format: `{"timestamp": ..., "level": ..., "message": ...}`
- External log aggregator reads standardized JSON format
- Legacy app doesn't need modification

### Step 2: Deploy and Monitor

Apply the manifest:
```bash
kubectl apply -f adapter-pod.yaml
```

Watch the legacy application:
```bash
kubectl logs adapter-pattern -c legacy-app -f
```

Watch the adapter (transformed output):
```bash
kubectl logs adapter-pattern -c log-adapter -f
```

You'll see the adapter converting the pipe-delimited format to JSON!

### Step 3: Compare Raw and Transformed Logs

View raw logs:
```bash
kubectl exec adapter-pattern -c legacy-app -- tail /var/log/app/legacy.log
```

View adapter's transformation:
```bash
kubectl logs adapter-pattern -c log-adapter --tail=5
```

---

## Exercise 10: Advanced Pattern - Service Mesh Sidecar

### Step 1: Simulate Service Mesh Proxy

```bash
cat > service-mesh-pod.yaml <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: service-mesh-demo
  labels:
    app: myservice
    version: v1
spec:
  containers:
  # Main application
  - name: application
    image: busybox
    command:
    - sh
    - -c
    - |
      mkdir -p /www
      cat > /www/index.html <<HTML
      <html><body>Application v1.0</body></html>
      HTML
      echo "Application starting on port 8080"
      cd /www && httpd -f -p 8080
    ports:
    - containerPort: 8080
      name: http

  # Envoy-like sidecar proxy
  - name: proxy
    image: busybox
    command:
    - sh
    - -c
    - |
      echo "Service mesh proxy started on port 15001"
      echo "Proxying traffic to/from application:8080"
      while true; do
        echo "\$(date): Proxy intercepting traffic"
        echo "  - TLS termination"
        echo "  - Load balancing"
        echo "  - Circuit breaking"
        echo "  - Metrics collection"
        sleep 20
      done
    ports:
    - containerPort: 15001
      name: proxy-port
    - containerPort: 15090
      name: metrics
EOF
```

Deploy and monitor:
```bash
kubectl apply -f service-mesh-pod.yaml
kubectl logs service-mesh-pod -c application
kubectl logs service-mesh-pod -c proxy -f
```

---

## Exercise 11: Pattern Comparison and Selection

### Step 1: Create a Complex Multi-Container Pod

This example combines multiple patterns:

```bash
cat > multi-pattern-pod.yaml <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: multi-pattern-demo
spec:
  # Init Container (runs first)
  initContainers:
  - name: init-setup
    image: busybox
    command: ['sh', '-c', 'echo "Setup complete" > /shared/init.txt']
    volumeMounts:
    - name: shared-data
      mountPath: /shared

  containers:
  # Main application
  - name: main-app
    image: nginx
    ports:
    - containerPort: 80
    volumeMounts:
    - name: shared-data
      mountPath: /usr/share/nginx/html
    - name: logs
      mountPath: /var/log/nginx
    lifecycle:
      postStart:
        exec:
          command: ["/bin/sh", "-c", "echo 'App started' >> /var/log/nginx/lifecycle.log"]
      preStop:
        exec:
          command: ["/bin/sh", "-c", "echo 'App stopping' >> /var/log/nginx/lifecycle.log; sleep 5"]

  # Sidecar: Log shipper
  - name: log-shipper
    image: busybox
    command:
    - sh
    - -c
    - |
      while true; do
        if [ -f /logs/access.log ]; then
          echo "Shipping access logs..."
          tail -n 1 /logs/access.log 2>/dev/null || echo "No new logs"
        fi
        sleep 10
      done
    volumeMounts:
    - name: logs
      mountPath: /logs

  # Adapter: Metrics formatter
  - name: metrics-adapter
    image: busybox
    command:
    - sh
    - -c
    - |
      while true; do
        echo "Converting metrics to Prometheus format..."
        echo "nginx_requests_total \$((RANDOM % 1000))"
        sleep 15
      done

  volumes:
  - name: shared-data
    emptyDir: {}
  - name: logs
    emptyDir: {}
EOF
```

Deploy and explore:
```bash
kubectl apply -f multi-pattern-pod.yaml
kubectl get pod multi-pattern-demo
kubectl logs multi-pattern-demo -c main-app
kubectl logs multi-pattern-demo -c log-shipper -f
```

---

## Pattern Selection Guide

### When to Use Each Pattern

| Pattern | Use When | Examples |
|---------|----------|----------|
| **Init Container** | Need setup before main app starts | DB migrations, config download, wait for services |
| **Sidecar (Traditional)** | Need continuous supporting functionality | Log shipping, metrics export (K8s <1.28) |
| **Sidecar (Modern)** | Need sidecar with startup ordering | Service mesh proxy, log aggregator (K8s 1.28+) |
| **Ambassador** | Need to simplify networking for main app | Connection pooling, rate limiting, circuit breakers |
| **Adapter** | Need to standardize output format | Log format conversion, metrics transformation |

### Decision Tree

```
Need to run before main container?
  YES → Use Init Container
  NO → Continue

Need to modify/transform main container's output?
  YES → Use Adapter pattern
  NO → Continue

Need to handle external communication?
  YES → Use Ambassador pattern
  NO → Use Sidecar pattern
```

---

## Repository YAML Files

The following pre-built YAML manifests are available in the repository for this lab:

| File | Description |
|------|-------------|
| `k8s/labs/workloads/podlifecycle.yaml` | Simple nginx Pod named `webserver` in namespace `test` with labels `app`, `tier`, `version`, and `env`; exposes container port 80. Use as a starting point for lifecycle, labeling, or namespace-scoped exercises (create namespace `test` if needed). |
| `k8s/labs/workloads/multi-pod.yaml` | Two-container Pod `multicontainer-pod` (nginx + redis) for localhost networking exercises. |
| `k8s/labs/workloads/sidecar-container-spec.yaml` | Pod `modern-sidecar-demo` using initContainer sidecar with `restartPolicy: Always` (Kubernetes 1.28+). |

You can apply these directly (from repo root):

```bash
kubectl apply -f k8s/labs/workloads/podlifecycle.yaml
kubectl apply -f k8s/labs/workloads/multi-pod.yaml
kubectl apply -f k8s/labs/workloads/sidecar-container-spec.yaml
```

---

## Lab Cleanup

Remove all resources created in this lab:

```bash
# Delete lifecycle Pods
kubectl delete pod lifecycle-demo lifecycle-observable http-lifecycle-working failing-poststart

# Delete multi-container Pods
kubectl delete pod multicontainer-pod sidecar-logging sidecar-metrics

# Delete modern sidecar Pod
kubectl delete pod modern-sidecar-demo

# Delete pattern Pods
kubectl delete pod ambassador-pattern adapter-pattern service-mesh-demo multi-pattern-demo

# Delete from YAML files
kubectl delete -f multi-pod.yaml

# Verify cleanup
kubectl get pods
```

Clean up local files:
```bash
rm -f lifecycle-hooks-pod.yaml lifecycle-hooks-observable.yaml \
      http-lifecycle-pod.yaml http-lifecycle-working.yaml \
      failing-poststart.yaml sidecar-logging-pod.yaml \
      sidecar-metrics-pod.yaml ambassador-pod.yaml \
      adapter-pod.yaml service-mesh-pod.yaml multi-pattern-pod.yaml
```

---

## Key Takeaways

### Lifecycle Hooks

1. **postStart runs immediately** after container creation
2. **preStop runs before** container termination
3. **Hooks can fail** and affect container lifecycle
4. **preStop is synchronous** - termination waits for completion
5. **Use hooks for** registration, cleanup, graceful shutdown
6. **Set appropriate timeouts** with terminationGracePeriodSeconds

### Multi-Container Patterns

1. **Sidecar pattern** adds functionality without modifying main app
2. **Modern sidecar spec** (K8s 1.28+) provides explicit sidecar semantics with startup ordering
3. **Ambassador pattern** simplifies networking for main app
4. **Adapter pattern** standardizes output format
5. **Containers share** network namespace and volumes
6. **Communication via localhost** within the same Pod
7. **Init Containers run first**, then main containers start together
8. **restartPolicy: Always** on init containers creates true sidecars (K8s 1.28+)
9. **Each pattern solves** different architectural problems

---

## Additional Commands Reference

```bash
# View specific container logs
kubectl logs <pod> -c <container-name>

# Follow logs from specific container
kubectl logs <pod> -c <container-name> -f

# Execute command in specific container
kubectl exec <pod> -c <container-name> -- <command>

# Get Pod with container statuses
kubectl get pod <pod> -o jsonpath='{.status.containerStatuses[*].name}'

# Check container restart counts
kubectl get pod <pod> -o jsonpath='{.status.containerStatuses[*].restartCount}'

# View all containers in Pod
kubectl get pod <pod> -o jsonpath='{.spec.containers[*].name}'

# Check init container and regular container names
kubectl get pod <pod> -o json | jq '.spec | {initContainers: [.initContainers[]?.name], containers: [.containers[].name]}'

# Get container images
kubectl get pod <pod> -o jsonpath='{.spec.containers[*].image}'

# Port forward to specific container
kubectl port-forward <pod> 8080:80

# Stream logs from all containers
kubectl logs <pod> --all-containers=true -f
```

---

## Best Practices

### Lifecycle Hooks

1. **Keep hooks simple and fast** - avoid long-running operations
2. **Make hooks idempotent** - safe to run multiple times
3. **Set appropriate grace periods** - balance cleanup time and responsiveness
4. **Log hook execution** - aids debugging
5. **Handle failures gracefully** - hooks may not always succeed
6. **Test hooks thoroughly** - verify behavior in all scenarios
7. **Use preStop for graceful shutdown** - drain connections, save state

### Multi-Container Pods

1. **Use shared volumes** for data exchange between containers
2. **Keep containers focused** - single responsibility principle
3. **Consider resource limits** for each container
4. **Use init containers** for setup tasks
5. **Name containers clearly** - indicates purpose
6. **Monitor all containers** - each can fail independently
7. **Secure inter-container communication** - even though they're local

### Container Communication

```yaml
# Example: Secure multi-container communication
apiVersion: v1
kind: Pod
metadata:
  name: secure-multi-container
spec:
  securityContext:
    runAsNonRoot: true
    fsGroup: 2000
  containers:
  - name: app
    image: myapp:latest
    securityContext:
      runAsUser: 1000
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
    volumeMounts:
    - name: shared
      mountPath: /shared
  - name: sidecar
    image: sidecar:latest
    securityContext:
      runAsUser: 1000
      allowPrivilegeEscalation: false
    volumeMounts:
    - name: shared
      mountPath: /shared
  volumes:
  - name: shared
    emptyDir: {}
```

---

## Real-World Examples

### Example 1: Istio Service Mesh Injection

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: bookinfo-app
  labels:
    app: reviews
    version: v1
spec:
  initContainers:
  - name: istio-init
    image: istio/proxyv2:1.14.0
    command: ['sh', '-c', 'iptables-setup.sh']
    securityContext:
      capabilities:
        add: ["NET_ADMIN"]
  containers:
  - name: reviews
    image: reviews:v1
    ports:
    - containerPort: 9080
  - name: istio-proxy
    image: istio/proxyv2:1.14.0
    ports:
    - containerPort: 15001
    - containerPort: 15090
```

### Example 2: Fluentd Logging Sidecar

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-with-fluentd
spec:
  containers:
  - name: application
    image: myapp:1.0
    volumeMounts:
    - name: varlog
      mountPath: /var/log
  - name: fluentd
    image: fluent/fluentd:v1.14
    env:
    - name: FLUENTD_ARGS
      value: -c /fluentd/etc/fluent.conf
    volumeMounts:
    - name: varlog
      mountPath: /var/log
    - name: fluentd-config
      mountPath: /fluentd/etc
  volumes:
  - name: varlog
    emptyDir: {}
  - name: fluentd-config
    configMap:
      name: fluentd-config
```

### Example 3: Cloud SQL Proxy Ambassador

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-with-cloudsql
spec:
  containers:
  - name: application
    image: myapp:1.0
    env:
    - name: DB_HOST
      value: "127.0.0.1"
    - name: DB_PORT
      value: "3306"
  - name: cloudsql-proxy
    image: gcr.io/cloudsql-docker/gce-proxy:latest
    command:
    - /cloud_sql_proxy
    - -instances=project:region:instance=tcp:3306
    - -credential_file=/secrets/cloudsql/credentials.json
    volumeMounts:
    - name: cloudsql-credentials
      mountPath: /secrets/cloudsql
      readOnly: true
  volumes:
  - name: cloudsql-credentials
    secret:
      secretName: cloudsql-credentials
```

---

## Troubleshooting

**postStart hook failing?**
- Check hook command syntax
- Verify files/paths exist in container
- Check container logs: `kubectl logs <pod> -c <container> --previous`
- Review Pod events: `kubectl describe pod <pod>`

**preStop hook not executing?**
- Check if Pod was force-deleted
- Verify terminationGracePeriodSeconds is sufficient
- Ensure hook completes within grace period
- Check for hook timeout

**Container can't communicate with sidecar?**
- Verify both containers use localhost
- Check port numbers match
- Ensure containers are both running
- Test with: `kubectl exec <pod> -c <container> -- nc -zv localhost <port>`

**Shared volume not working?**
- Verify volume mount paths
- Check both containers mount same volume
- Ensure volume type supports read/write
- Test with: `kubectl exec <pod> -c <container> -- ls -la /mount/path`

**One container crashing in multi-container Pod?**
- Check specific container logs: `kubectl logs <pod> -c <container>`
- Review container status: `kubectl describe pod <pod>`
- Check resource limits: `kubectl top pod <pod> --containers`
- Verify dependencies between containers

---

## Next Steps

You've completed the Pod Lifecycle and Multi-Container Patterns lab! Consider exploring:
- [Lab 10: Init Containers](lab10-pod-init-containers.md) for more init container details
- [Lab 09: Health Checks with Probes](lab09-pod-health-probes.md) for liveness and readiness
- [Lab 26: DaemonSets](lab26-workload-daemonsets.md) for node-level workloads
- StatefulSets for stateful multi-container applications

## Additional Resources

- [Kubernetes Pod Lifecycle](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/)
- [Container Lifecycle Hooks](https://kubernetes.io/docs/concepts/containers/container-lifecycle-hooks/)
- [Multi-Container Pod Patterns](https://kubernetes.io/blog/2015/06/the-distributed-system-toolkit-patterns/)
- [Istio Sidecar Injection](https://istio.io/latest/docs/setup/additional-setup/sidecar-injection/)

---

**Lab Created**: March 2026
**Compatible with**: Kubernetes 1.24+
**Modern Sidecar Feature**: Kubernetes 1.28+
