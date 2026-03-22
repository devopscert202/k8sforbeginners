# Lab 21: Init Containers in Kubernetes

## Overview
In this lab, you will learn how to use Init Containers to perform initialization tasks before your main application containers start. Init Containers are specialized containers that run and complete before the main application containers in a Pod start.

## Prerequisites
- A running Kubernetes cluster (Minikube, Kind, or any K8s cluster)
- `kubectl` CLI tool installed and configured
- Completion of Lab 01 (Creating Pods) is recommended
- Basic understanding of Pods and Services

## Learning Objectives
By the end of this lab, you will be able to:
- Understand what Init Containers are and when to use them
- Create Pods with Init Containers
- Use Init Containers for service dependency checks
- Implement multi-stage initialization
- Debug Init Container failures
- Apply Init Containers to real-world scenarios

---

## What are Init Containers?

**Init Containers** are specialized containers that run before app containers in a Pod. They are useful for setup scripts, utilities, or initialization tasks that you don't want in your main application image.

### Key Characteristics

1. **Sequential Execution**: Init Containers run one at a time, in the order defined
2. **Must Complete**: Each Init Container must complete successfully before the next one starts
3. **Blocking**: Main containers don't start until all Init Containers succeed
4. **Separate Images**: Can use different images from app containers
5. **No Probes**: Don't support liveness, readiness, or startup probes

### Common Use Cases

- **Wait for Services**: Wait for dependencies (databases, APIs) to be ready
- **Configuration Setup**: Download configurations, initialize data
- **Security**: Clone repositories, retrieve secrets, set permissions
- **Database Initialization**: Run schema migrations, seed data
- **Pre-requisite Checks**: Verify environment conditions before starting
- **Network Configuration**: Set up networking, register with service mesh

### Init Containers vs Sidecar Containers

| Feature | Init Container | Sidecar Container |
|---------|----------------|-------------------|
| **When runs** | Before main containers | Alongside main containers |
| **Lifecycle** | Runs once and exits | Runs continuously |
| **Order** | Sequential | Parallel |
| **Purpose** | Setup and initialization | Support and monitoring |
| **Failure impact** | Pod won't start | Pod may continue running |

---

## Exercise 1: Basic Init Container - Service Dependency

### Understanding the Scenario

In microservices architectures, applications often depend on other services (databases, caches, APIs). Init Containers can wait for these dependencies to be available before starting the main application.

### Step 1: Review the Init Container Manifest

Let's look at `init2-container.yaml`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: myapp-pod
  labels:
    app: myapp
spec:
  initContainers:
  - name: init-myservice
    image: registry.access.redhat.com/ubi8/ubi:latest
    command: ['sh', '-c', 'until getent hosts myservice; do echo waiting for myservice; sleep 2; done;']
  - name: init-mydb
    image: registry.access.redhat.com/ubi8/ubi:latest
    command: ['sh', '-c', 'until getent hosts mydb; do echo waiting for mydb; sleep 2; done;']
  containers:
  - name: myapp-container
    image: registry.access.redhat.com/ubi8/ubi:latest
    command: ['sh', '-c', 'echo The app is running! && sleep 3600']
```

**Understanding the manifest:**
- `initContainers` section defines two Init Containers
- `init-myservice` waits for the `myservice` service to be resolvable via DNS
- `init-mydb` waits for the `mydb` service to be resolvable
- Both use `getent hosts` to check if DNS resolution works
- They retry every 2 seconds until successful
- Main container only starts after both Init Containers complete
- Main application runs for 1 hour (3600 seconds)

### Step 2: Deploy the Pod (Without Dependencies)

Navigate to the workloads directory:
```bash
cd k8s/labs/workloads
```

Deploy the Pod:
```bash
kubectl apply -f init2-container.yaml
```

Expected output:
```
pod/myapp-pod created
```

### Step 3: Observe Init Container Behavior

Check Pod status:
```bash
kubectl get pod myapp-pod
```

Expected output:
```
NAME        READY   STATUS     RESTARTS   AGE
myapp-pod   0/1     Init:0/2   0          10s
```

The status `Init:0/2` means 0 of 2 Init Containers have completed.

Get detailed information:
```bash
kubectl describe pod myapp-pod
```

Look for the Init Containers section:
```
Init Containers:
  init-myservice:
    State:          Running
    Started:        Mon, 15 Jan 2026 10:00:00 +0000
  init-mydb:
    State:          Waiting
    Reason:         PodInitializing
```

View Init Container logs:
```bash
kubectl logs myapp-pod -c init-myservice
```

Expected output (repeating):
```
waiting for myservice
waiting for myservice
waiting for myservice
...
```

The Init Container is stuck waiting because the service doesn't exist yet!

### Step 4: Create the Required Services

Review `init2-myservice.yaml`:

```yaml
kind: Service
apiVersion: v1
metadata:
  name: myservice
spec:
  ports:
  - protocol: TCP
    port: 80
    targetPort: 9376
```

Review `init2-mydb.yaml`:

```yaml
kind: Service
apiVersion: v1
metadata:
  name: mydb
spec:
  ports:
  - protocol: TCP
    port: 80
    targetPort: 9377
```

**Note**: These are headless services without selectors, just for DNS resolution demonstration.

Create the first service:
```bash
kubectl apply -f init2-myservice.yaml
```

Expected output:
```
service/myservice created
```

Check Pod status:
```bash
kubectl get pod myapp-pod
```

Expected output:
```
NAME        READY   STATUS     RESTARTS   AGE
myapp-pod   0/1     Init:1/2   0          2m
```

Now `Init:1/2` shows the first Init Container completed! Check logs:
```bash
kubectl logs myapp-pod -c init-myservice
```

You'll see the waiting messages end when the service was created.

Check the second Init Container:
```bash
kubectl logs myapp-pod -c init-mydb -f
```

Expected output (repeating):
```
waiting for mydb
waiting for mydb
...
```

Create the second service:
```bash
kubectl apply -f init2-mydb.yaml
```

Expected output:
```
service/mydb created
```

### Step 5: Verify Pod Startup

Watch the Pod status:
```bash
kubectl get pod myapp-pod -w
```

You should see the transition:
```
NAME        READY   STATUS     RESTARTS   AGE
myapp-pod   0/1     Init:1/2   0          3m
myapp-pod   0/1     Init:1/2   0          3m10s
myapp-pod   0/1     PodInitializing   0     3m12s
myapp-pod   1/1     Running    0          3m15s
```

Press Ctrl+C to exit watch mode.

View the main container logs:
```bash
kubectl logs myapp-pod
```

Expected output:
```
The app is running!
```

Get detailed Pod information:
```bash
kubectl describe pod myapp-pod
```

Look at the Init Containers section - both should show `State: Terminated` with `Reason: Completed`.

---

## Exercise 2: Init Container for Configuration Setup

### Step 1: Create a Pod with Configuration Init Container

Create a new manifest that uses an Init Container to set up configuration:

```bash
cat > init-config-pod.yaml <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: config-init-pod
spec:
  initContainers:
  - name: install-config
    image: busybox
    command:
    - sh
    - -c
    - |
      echo "Downloading configuration..."
      echo "app.name=MyApplication" > /work-dir/config.properties
      echo "app.version=1.0.0" >> /work-dir/config.properties
      echo "app.environment=production" >> /work-dir/config.properties
      echo "Configuration downloaded successfully"
      ls -l /work-dir/
    volumeMounts:
    - name: workdir
      mountPath: /work-dir
  containers:
  - name: main-app
    image: busybox
    command:
    - sh
    - -c
    - |
      echo "Starting application..."
      echo "Configuration file contents:"
      cat /config/config.properties
      echo "Application running..."
      sleep 3600
    volumeMounts:
    - name: workdir
      mountPath: /config
  volumes:
  - name: workdir
    emptyDir: {}
EOF
```

**Understanding the manifest:**
- Init Container creates a configuration file in a shared volume
- Uses `emptyDir` volume to share data between Init and main containers
- Init Container writes to `/work-dir`
- Main container reads from `/config` (same volume, different mount path)
- Main application verifies configuration was created

### Step 2: Deploy and Verify

Apply the manifest:
```bash
kubectl apply -f init-config-pod.yaml
```

Watch the Pod start:
```bash
kubectl get pod config-init-pod -w
```

View Init Container logs:
```bash
kubectl logs config-init-pod -c install-config
```

Expected output:
```
Downloading configuration...
Configuration downloaded successfully
total 4
-rw-r--r--    1 root     root            78 Jan 15 10:00 config.properties
```

View main container logs:
```bash
kubectl logs config-init-pod
```

Expected output:
```
Starting application...
Configuration file contents:
app.name=MyApplication
app.version=1.0.0
app.environment=production
Application running...
```

---

## Exercise 3: Multiple Init Containers - Sequential Processing

### Step 1: Create a Pod with Multi-Stage Initialization

Create a manifest demonstrating sequential Init Container execution:

```bash
cat > multi-init-pod.yaml <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: multi-init-pod
spec:
  initContainers:
  - name: init-stage1
    image: busybox
    command:
    - sh
    - -c
    - |
      echo "Stage 1: Checking system requirements..."
      sleep 5
      echo "Stage 1 complete!" > /shared/stage1.txt
      date >> /shared/stage1.txt
    volumeMounts:
    - name: shared-data
      mountPath: /shared
  - name: init-stage2
    image: busybox
    command:
    - sh
    - -c
    - |
      echo "Stage 2: Setting up database schema..."
      cat /shared/stage1.txt
      sleep 5
      echo "Stage 2 complete!" > /shared/stage2.txt
      date >> /shared/stage2.txt
    volumeMounts:
    - name: shared-data
      mountPath: /shared
  - name: init-stage3
    image: busybox
    command:
    - sh
    - -c
    - |
      echo "Stage 3: Loading initial data..."
      cat /shared/stage2.txt
      sleep 5
      echo "Stage 3 complete!" > /shared/stage3.txt
      date >> /shared/stage3.txt
    volumeMounts:
    - name: shared-data
      mountPath: /shared
  containers:
  - name: application
    image: busybox
    command:
    - sh
    - -c
    - |
      echo "Application starting..."
      echo "Initialization history:"
      cat /shared/stage*.txt
      echo "Application ready!"
      sleep 3600
    volumeMounts:
    - name: shared-data
      mountPath: /shared
  volumes:
  - name: shared-data
    emptyDir: {}
EOF
```

### Step 2: Deploy and Monitor

Apply the manifest:
```bash
kubectl apply -f multi-init-pod.yaml
```

Monitor in real-time:
```bash
kubectl get pod multi-init-pod -w
```

You'll see:
```
NAME              READY   STATUS     RESTARTS   AGE
multi-init-pod    0/1     Init:0/3   0          5s
multi-init-pod    0/1     Init:1/3   0          10s
multi-init-pod    0/1     Init:2/3   0          15s
multi-init-pod    0/1     PodInitializing   0   20s
multi-init-pod    1/1     Running    0          25s
```

View logs from each Init Container:
```bash
kubectl logs multi-init-pod -c init-stage1
kubectl logs multi-init-pod -c init-stage2
kubectl logs multi-init-pod -c init-stage3
```

View final application logs:
```bash
kubectl logs multi-init-pod
```

---

## Exercise 4: Init Container Failure Handling

### Understanding Init Container Failures

If an Init Container fails:
1. Kubernetes restarts the Pod (including all Init Containers)
2. The Pod's restart policy applies to Init Containers
3. Init Containers that already succeeded don't run again (unless Pod restarts)

### Step 1: Create a Failing Init Container

```bash
cat > failing-init-pod.yaml <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: failing-init-pod
spec:
  initContainers:
  - name: init-success
    image: busybox
    command: ['sh', '-c', 'echo "Init 1 succeeded"; exit 0']
  - name: init-failure
    image: busybox
    command: ['sh', '-c', 'echo "Init 2 failed"; exit 1']
  containers:
  - name: main-container
    image: busybox
    command: ['sh', '-c', 'echo "Main container running"; sleep 3600']
  restartPolicy: Never
EOF
```

### Step 2: Deploy and Observe Failure

Apply the manifest:
```bash
kubectl apply -f failing-init-pod.yaml
```

Watch the Pod:
```bash
kubectl get pod failing-init-pod -w
```

Expected status:
```
NAME               READY   STATUS       RESTARTS   AGE
failing-init-pod   0/1     Init:Error   0          10s
```

Describe the Pod:
```bash
kubectl describe pod failing-init-pod
```

Look for Init Container statuses showing the failure.

View logs:
```bash
kubectl logs failing-init-pod -c init-success
kubectl logs failing-init-pod -c init-failure
```

### Step 3: Fix the Init Container

Create a corrected version:
```bash
cat > fixed-init-pod.yaml <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: fixed-init-pod
spec:
  initContainers:
  - name: init-check
    image: busybox
    command:
    - sh
    - -c
    - |
      echo "Performing health check..."
      # Simulate check that might fail
      if [ -f /tmp/should-fail ]; then
        echo "Health check failed"
        exit 1
      fi
      echo "Health check passed"
      exit 0
  containers:
  - name: main-container
    image: busybox
    command: ['sh', '-c', 'echo "Application running"; sleep 3600']
EOF
```

Apply and verify:
```bash
kubectl apply -f fixed-init-pod.yaml
kubectl get pod fixed-init-pod
```

---

## Exercise 5: Real-World Scenario - Database Migration

### Step 1: Create a Database Migration Init Container

This example simulates a real-world scenario where an Init Container runs database migrations before the application starts:

```bash
cat > db-migration-pod.yaml <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: webapp-with-migration
  labels:
    app: webapp
spec:
  initContainers:
  - name: wait-for-db
    image: busybox
    command:
    - sh
    - -c
    - |
      echo "Waiting for database to be ready..."
      # In real scenario, this would check actual database connectivity
      for i in 1 2 3 4 5; do
        echo "Attempt $i: Checking database connection..."
        sleep 2
      done
      echo "Database is ready!"
  - name: run-migrations
    image: busybox
    command:
    - sh
    - -c
    - |
      echo "Running database migrations..."
      echo "Migration 001: Create users table"
      sleep 2
      echo "Migration 002: Create products table"
      sleep 2
      echo "Migration 003: Add indexes"
      sleep 2
      echo "All migrations completed successfully"
      echo "migration-complete" > /migrations/status.txt
    volumeMounts:
    - name: migration-status
      mountPath: /migrations
  containers:
  - name: webapp
    image: busybox
    command:
    - sh
    - -c
    - |
      echo "Starting web application..."
      echo "Checking migration status:"
      cat /migrations/status.txt
      echo "Web application is ready to serve traffic"
      echo "Listening on port 8080..."
      sleep 3600
    volumeMounts:
    - name: migration-status
      mountPath: /migrations
  volumes:
  - name: migration-status
    emptyDir: {}
EOF
```

### Step 2: Deploy and Monitor

Apply the manifest:
```bash
kubectl apply -f db-migration-pod.yaml
```

Monitor the initialization:
```bash
kubectl get pod webapp-with-migration -w
```

Check each Init Container's logs:
```bash
kubectl logs webapp-with-migration -c wait-for-db
kubectl logs webapp-with-migration -c run-migrations
```

Check the application logs:
```bash
kubectl logs webapp-with-migration
```

---

## Exercise 6: Init Containers with Resource Limits

### Best Practice: Setting Resource Limits

Init Containers should have resource limits to prevent them from consuming excessive resources:

```bash
cat > resource-limited-init.yaml <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: resource-init-pod
spec:
  initContainers:
  - name: data-processor
    image: busybox
    command: ['sh', '-c', 'echo "Processing data..."; sleep 10; echo "Done"']
    resources:
      requests:
        memory: "32Mi"
        cpu: "100m"
      limits:
        memory: "64Mi"
        cpu: "200m"
  containers:
  - name: application
    image: busybox
    command: ['sh', '-c', 'echo "App running"; sleep 3600']
    resources:
      requests:
        memory: "64Mi"
        cpu: "250m"
      limits:
        memory: "128Mi"
        cpu: "500m"
EOF
```

Apply and verify:
```bash
kubectl apply -f resource-limited-init.yaml
kubectl describe pod resource-init-pod
```

Look at the resource allocation in the Pod description.

---

## Lab Cleanup

Remove all resources created in this lab:

```bash
# Delete Pods
kubectl delete pod myapp-pod
kubectl delete pod config-init-pod
kubectl delete pod multi-init-pod
kubectl delete pod failing-init-pod
kubectl delete pod fixed-init-pod
kubectl delete pod webapp-with-migration
kubectl delete pod resource-init-pod

# Delete Services
kubectl delete service myservice
kubectl delete service mydb

# Delete using YAML files
kubectl delete -f init2-container.yaml
kubectl delete -f init2-myservice.yaml
kubectl delete -f init2-mydb.yaml

# Verify cleanup
kubectl get pods
kubectl get services
```

Clean up local files:
```bash
rm -f init-config-pod.yaml multi-init-pod.yaml failing-init-pod.yaml \
      fixed-init-pod.yaml db-migration-pod.yaml resource-limited-init.yaml
```

---

## Key Takeaways

1. **Init Containers run before main containers** and must complete successfully
2. **Sequential execution** ensures ordered initialization steps
3. **Service dependencies** can be handled gracefully with Init Containers
4. **Shared volumes** enable data transfer between Init and main containers
5. **Failure handling** follows Pod restart policies
6. **Resource limits** should be set for Init Containers
7. **Use cases include** service waits, configuration setup, migrations, and pre-checks
8. **Init Containers are isolated** from main container lifecycles
9. **No probes** are supported for Init Containers
10. **Each Init Container** restarts independently if it fails

---

## Additional Commands Reference

```bash
# View Init Container logs
kubectl logs <pod-name> -c <init-container-name>

# Follow Init Container logs
kubectl logs <pod-name> -c <init-container-name> -f

# Get Pod with Init Container status
kubectl get pod <pod-name> -o jsonpath='{.status.initContainerStatuses[*].state}'

# Describe Pod to see Init Container details
kubectl describe pod <pod-name>

# Watch Pod initialization
kubectl get pod <pod-name> -w

# Get Init Container names
kubectl get pod <pod-name> -o jsonpath='{.spec.initContainers[*].name}'

# Check if Init Containers completed
kubectl get pod <pod-name> -o jsonpath='{.status.initContainerStatuses[*].state.terminated.reason}'

# View all containers (init + main)
kubectl get pod <pod-name> -o jsonpath='{.spec.initContainers[*].name} {.spec.containers[*].name}'
```

---

## Best Practices

### Design Principles

1. **Keep Init Containers Simple**: Each should do one thing well
2. **Make Them Idempotent**: Safe to run multiple times
3. **Set Timeouts**: Don't let them run indefinitely
4. **Use Appropriate Images**: Choose minimal images for faster startup
5. **Share Data via Volumes**: Use emptyDir or configMaps
6. **Log Verbosely**: Make troubleshooting easier
7. **Set Resource Limits**: Prevent resource exhaustion

### When to Use Init Containers

**Good use cases:**
- Waiting for service dependencies
- Running database migrations
- Downloading configuration or data
- Setting up security contexts
- Performing pre-flight checks
- Registering with external systems

**Avoid using for:**
- Long-running processes (use sidecar instead)
- Tasks that need to run alongside main app
- Application logic (belongs in main container)
- Continuous monitoring (use liveness/readiness probes)

### Security Considerations

```yaml
# Example: Init Container with security context
apiVersion: v1
kind: Pod
metadata:
  name: secure-init-pod
spec:
  initContainers:
  - name: secure-init
    image: busybox
    command: ['sh', '-c', 'echo "Running as non-root"; id']
    securityContext:
      runAsNonRoot: true
      runAsUser: 1000
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
    volumeMounts:
    - name: workdir
      mountPath: /work
  containers:
  - name: app
    image: busybox
    command: ['sh', '-c', 'sleep 3600']
  volumes:
  - name: workdir
    emptyDir: {}
```

---

## Real-World Examples

### Example 1: Git Repository Clone

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: git-sync-pod
spec:
  initContainers:
  - name: git-clone
    image: alpine/git
    command:
    - sh
    - -c
    - |
      git clone https://github.com/kubernetes/examples.git /git/repo
      cd /git/repo
      git log -1
    volumeMounts:
    - name: git-repo
      mountPath: /git
  containers:
  - name: web-server
    image: nginx
    volumeMounts:
    - name: git-repo
      mountPath: /usr/share/nginx/html
      subPath: repo
  volumes:
  - name: git-repo
    emptyDir: {}
```

### Example 2: Wait for Multiple Services

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: multi-service-wait
spec:
  initContainers:
  - name: wait-redis
    image: busybox
    command: ['sh', '-c', 'until nslookup redis-service; do echo waiting for redis; sleep 2; done']
  - name: wait-postgres
    image: busybox
    command: ['sh', '-c', 'until nslookup postgres-service; do echo waiting for postgres; sleep 2; done']
  - name: wait-rabbitmq
    image: busybox
    command: ['sh', '-c', 'until nslookup rabbitmq-service; do echo waiting for rabbitmq; sleep 2; done']
  containers:
  - name: application
    image: myapp:latest
    command: ['./start-app']
```

### Example 3: Configuration Template Processing

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: config-processor
spec:
  initContainers:
  - name: process-config
    image: busybox
    command:
    - sh
    - -c
    - |
      # Read template
      cat > /config/app.conf.template << EOF
      server {
        listen 80;
        server_name ${SERVER_NAME};
        root ${DOCUMENT_ROOT};
      }
      EOF
      # Process template with environment variables
      export SERVER_NAME="example.com"
      export DOCUMENT_ROOT="/var/www/html"
      envsubst < /config/app.conf.template > /config/app.conf
      echo "Configuration processed successfully"
    volumeMounts:
    - name: config
      mountPath: /config
  containers:
  - name: nginx
    image: nginx
    volumeMounts:
    - name: config
      mountPath: /etc/nginx/conf.d
  volumes:
  - name: config
    emptyDir: {}
```

---

## Troubleshooting

**Init Container stuck in waiting?**
- Check logs: `kubectl logs <pod> -c <init-container>`
- Verify service dependencies exist
- Check network policies aren't blocking access
- Ensure DNS is working: `kubectl run -it --rm debug --image=busybox --restart=Never -- nslookup <service>`

**Init Container keeps restarting?**
- Check exit code in Pod description
- Review container logs for errors
- Verify image exists and is accessible
- Check resource limits aren't too restrictive

**Pod stuck in Init:Error?**
- View Init Container status: `kubectl describe pod <pod>`
- Check container logs for failure reason
- Verify commands and arguments are correct
- Test the command locally with same image

**Init Container takes too long?**
- Check if waiting for unavailable service
- Add timeout mechanism to Init Container command
- Use `activeDeadlineSeconds` to limit total time
- Review network connectivity

**Data not shared between Init and main container?**
- Verify volume is mounted in both containers
- Check mount paths are correct
- Ensure Init Container writes to correct path
- Verify volume type supports read/write

---

## Next Steps

You've completed the Init Containers lab! Consider exploring:
- [Lab 22: Pod Lifecycle and Multi-Container Patterns](lab22-pod-lifecycle-multi-container.md)
- [Lab 18: Jobs and Batch Processing](lab18-jobs-batch.md)
- [Lab 30: Health Checks with Probes](lab30-probes.md)
- StatefulSets for stateful applications

## Additional Resources

- [Kubernetes Init Containers Documentation](https://kubernetes.io/docs/concepts/workloads/pods/init-containers/)
- [Init Containers Best Practices](https://kubernetes.io/docs/concepts/workloads/pods/init-containers/#init-containers-in-use)
- [Pod Lifecycle](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/)

---

**Lab Created**: March 2026
**Compatible with**: Kubernetes 1.24+
