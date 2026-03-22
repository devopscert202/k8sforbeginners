# Lab 31: StatefulSets & Stateful Applications

## Overview
In this lab, you will learn about StatefulSets, a Kubernetes workload type designed for stateful applications that require stable network identities, persistent storage, and ordered deployment. You'll deploy stateful applications like databases, understand the differences between StatefulSets and Deployments, and master techniques for managing stateful workloads in production.

## Prerequisites
- A running Kubernetes cluster (Minikube, Kind, or any K8s cluster)
- `kubectl` CLI tool installed and configured
- Basic understanding of Pods, Deployments, and Services (Lab 01, Lab 02)
- Understanding of Persistent Volumes and Persistent Volume Claims (Lab 14)
- Storage provisioner configured in your cluster

## Learning Objectives
By the end of this lab, you will be able to:
- Understand what StatefulSets are and when to use them
- Differentiate between StatefulSets and Deployments
- Deploy stateful applications with stable network identities
- Configure Headless Services for StatefulSet DNS
- Use volumeClaimTemplates for dynamic persistent storage
- Scale StatefulSets up and down safely
- Perform rolling updates on StatefulSets
- Deploy real-world stateful applications like databases
- Troubleshoot common StatefulSet issues

---

## What is a StatefulSet?

A **StatefulSet** is a Kubernetes workload API object used to manage stateful applications. Unlike Deployments, which are designed for stateless applications, StatefulSets provide guarantees about the ordering and uniqueness of Pods.

### Key Characteristics

- **Stable Network Identity**: Each Pod gets a persistent hostname that survives rescheduling
- **Ordered Deployment**: Pods are created sequentially (pod-0, pod-1, pod-2...)
- **Ordered Scaling**: Scale up creates Pods in order; scale down deletes in reverse order
- **Ordered Updates**: Rolling updates proceed in order (reverse for OnDelete strategy)
- **Stable Storage**: Each Pod can have its own persistent volume that follows it
- **Persistent Pod Names**: Pod names are predictable: `<statefulset-name>-<ordinal>`

### StatefulSet vs Deployment

| Feature | StatefulSet | Deployment |
|---------|-------------|------------|
| **Pod Identity** | Stable, persistent (web-0, web-1) | Random hash (web-abc123) |
| **Network Identity** | Stable DNS hostname | Ephemeral, changes on restart |
| **Storage** | Unique per Pod (volumeClaimTemplates) | Shared or no persistence |
| **Scaling Order** | Sequential (0, 1, 2...) | Parallel |
| **Update Order** | Sequential, ordered | Parallel or rolling |
| **Use Case** | Databases, queues, clustered apps | Stateless web apps, APIs |
| **Pod Naming** | Predictable ordinal index | Random suffix |
| **Deletion Order** | Reverse ordinal (2, 1, 0) | Random |

### Common Use Cases

1. **Databases**: MySQL, PostgreSQL, MongoDB, Cassandra
2. **Message Queues**: RabbitMQ, Kafka, NATS
3. **Distributed Systems**: ZooKeeper, etcd, Consul
4. **Caching Systems**: Redis Cluster, Memcached
5. **Search Engines**: Elasticsearch clusters
6. **Monitoring**: Prometheus with persistent storage

---

## Exercise 1: Understanding StatefulSet Components

### Step 1: Check Your Cluster

Verify you have a storage class available:

```bash
kubectl get storageclass
```

Example output:
```
NAME                 PROVISIONER             RECLAIMPOLICY   VOLUMEBINDINGMODE
standard (default)   k8s.io/minikube-hostpath   Delete          Immediate
```

If you don't have a default storage class, create one or modify the YAML examples to use your available storage class.

### Step 2: Understand StatefulSet Components

A StatefulSet requires:

1. **StatefulSet Object**: Defines the stateful application
2. **Headless Service**: Provides stable network identity
3. **PersistentVolumeClaims**: (Optional) Provides stable storage
4. **PersistentVolumes**: Backing storage for PVCs

---

## Exercise 2: Deploy Your First StatefulSet

### Step 1: Review the Basic StatefulSet Manifest

Navigate to the workloads directory:
```bash
cd k8s/labs/workloads
```

Examine the `basic-statefulset.yaml` file:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: nginx-headless
  labels:
    app: nginx-stateful
spec:
  clusterIP: None  # Headless Service
  selector:
    app: nginx-stateful
  ports:
  - port: 80
    name: web
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: web
spec:
  serviceName: "nginx-headless"  # Must match the headless service name
  replicas: 3
  selector:
    matchLabels:
      app: nginx-stateful
  template:
    metadata:
      labels:
        app: nginx-stateful
    spec:
      containers:
      - name: nginx
        image: nginx:1.25
        ports:
        - containerPort: 80
          name: web
```

**Understanding the Manifest:**

- `clusterIP: None` - Creates a Headless Service (no load balancing, direct Pod IPs)
- `serviceName` - Links StatefulSet to the Headless Service
- `replicas: 3` - Creates 3 Pods (web-0, web-1, web-2)
- Pod names are predictable: `web-0`, `web-1`, `web-2`

### Step 2: Deploy the StatefulSet

Apply the manifest:

```bash
kubectl apply -f basic-statefulset.yaml
```

Expected output:
```
service/nginx-headless created
statefulset.apps/web created
```

### Step 3: Watch the Sequential Pod Creation

Monitor Pod creation in real-time:

```bash
kubectl get pods -l app=nginx-stateful -w
```

Observe:
```
NAME    READY   STATUS              RESTARTS   AGE
web-0   0/1     ContainerCreating   0          2s
web-0   1/1     Running             0          5s
web-1   0/1     ContainerCreating   0          0s
web-1   1/1     Running             0          3s
web-2   0/1     ContainerCreating   0          0s
web-2   1/1     Running             0          3s
```

Notice:
- Pods are created **one at a time** (sequential)
- Each Pod waits for the previous one to be Running and Ready
- Pod names have ordinal indexes: 0, 1, 2

Press `Ctrl+C` to stop watching.

### Step 4: Verify the StatefulSet

Check the StatefulSet status:

```bash
kubectl get statefulset web
```

Expected output:
```
NAME   READY   AGE
web    3/3     2m
```

List the Pods with their IPs and nodes:

```bash
kubectl get pods -l app=nginx-stateful -o wide
```

Example output:
```
NAME    READY   STATUS    RESTARTS   AGE   IP           NODE
web-0   1/1     Running   0          3m    10.244.1.5   node01
web-1   1/1     Running   0          3m    10.244.2.5   node02
web-2   1/1     Running   0          2m    10.244.1.6   node01
```

---

## Exercise 3: Stable Network Identities with Headless Services

### Step 1: Understand Headless Services

A Headless Service (with `clusterIP: None`) doesn't provide load balancing. Instead, it creates DNS entries for each Pod.

### Step 2: Check DNS Records

Run a DNS lookup from within the cluster:

```bash
# Create a temporary Pod for DNS testing
kubectl run -it --rm debug --image=busybox --restart=Never -- sh

# Inside the Pod, run:
nslookup nginx-headless.default.svc.cluster.local
```

Expected output:
```
Server:    10.96.0.10
Address 1: 10.96.0.10 kube-dns.kube-system.svc.cluster.local

Name:      nginx-headless.default.svc.cluster.local
Address 1: 10.244.1.5 web-0.nginx-headless.default.svc.cluster.local
Address 2: 10.244.2.5 web-1.nginx-headless.default.svc.cluster.local
Address 3: 10.244.1.6 web-2.nginx-headless.default.svc.cluster.local
```

### Step 3: Access Individual Pods by DNS

Each StatefulSet Pod gets a stable DNS name:

```
<pod-name>.<service-name>.<namespace>.svc.cluster.local
```

Test accessing individual Pods:

```bash
# Still inside the debug Pod
nslookup web-0.nginx-headless.default.svc.cluster.local
nslookup web-1.nginx-headless.default.svc.cluster.local
nslookup web-2.nginx-headless.default.svc.cluster.local

# Exit the debug Pod
exit
```

This stable DNS hostname persists even if the Pod is rescheduled to a different node!

---

## Exercise 4: StatefulSet with Persistent Storage

### Step 1: Review StatefulSet with volumeClaimTemplates

Examine the `statefulset-with-storage.yaml` file:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: nginx-storage
  labels:
    app: nginx-storage
spec:
  clusterIP: None
  selector:
    app: nginx-storage
  ports:
  - port: 80
    name: web
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: web-storage
spec:
  serviceName: "nginx-storage"
  replicas: 3
  selector:
    matchLabels:
      app: nginx-storage
  template:
    metadata:
      labels:
        app: nginx-storage
    spec:
      containers:
      - name: nginx
        image: nginx:1.25
        ports:
        - containerPort: 80
          name: web
        volumeMounts:
        - name: www
          mountPath: /usr/share/nginx/html
  volumeClaimTemplates:
  - metadata:
      name: www
    spec:
      accessModes: [ "ReadWriteOnce" ]
      resources:
        requests:
          storage: 1Gi
```

**Key Points:**

- `volumeClaimTemplates` - Creates a unique PVC for each Pod
- Each Pod gets its own persistent volume
- PVCs are named: `<volume-name>-<pod-name>` (e.g., `www-web-storage-0`)
- Storage persists even if Pods are deleted and recreated

### Step 2: Deploy the StatefulSet with Storage

Apply the manifest:

```bash
kubectl apply -f statefulset-with-storage.yaml
```

### Step 3: Verify PersistentVolumeClaims

Check the automatically created PVCs:

```bash
kubectl get pvc
```

Expected output:
```
NAME                 STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
www-web-storage-0    Bound    pvc-abc123...                              1Gi        RWO            standard       30s
www-web-storage-1    Bound    pvc-def456...                              1Gi        RWO            standard       25s
www-web-storage-2    Bound    pvc-ghi789...                              1Gi        RWO            standard       20s
```

Each Pod has its own dedicated PVC!

### Step 4: Write Data to Each Pod's Volume

Write unique data to each Pod:

```bash
# Write to web-storage-0
kubectl exec web-storage-0 -- sh -c 'echo "Hello from web-storage-0" > /usr/share/nginx/html/index.html'

# Write to web-storage-1
kubectl exec web-storage-1 -- sh -c 'echo "Hello from web-storage-1" > /usr/share/nginx/html/index.html'

# Write to web-storage-2
kubectl exec web-storage-2 -- sh -c 'echo "Hello from web-storage-2" > /usr/share/nginx/html/index.html'
```

### Step 5: Verify Data Persistence

Read the data from each Pod:

```bash
kubectl exec web-storage-0 -- cat /usr/share/nginx/html/index.html
kubectl exec web-storage-1 -- cat /usr/share/nginx/html/index.html
kubectl exec web-storage-2 -- cat /usr/share/nginx/html/index.html
```

### Step 6: Test Data Persistence After Pod Deletion

Delete a Pod and watch it recreate:

```bash
kubectl delete pod web-storage-0
kubectl get pods -l app=nginx-storage -w
```

After the Pod is recreated, verify the data is still there:

```bash
kubectl exec web-storage-0 -- cat /usr/share/nginx/html/index.html
```

The data persists because the same PVC is remounted!

---

## Exercise 5: Scaling StatefulSets

### Step 1: Scale Up (Adding Replicas)

Scale the StatefulSet from 3 to 5 replicas:

```bash
kubectl scale statefulset web-storage --replicas=5
```

Watch the sequential scaling:

```bash
kubectl get pods -l app=nginx-storage -w
```

Observe:
- `web-storage-3` is created first
- `web-storage-4` is created only after `web-storage-3` is Ready
- New PVCs are automatically created

Check the new PVCs:

```bash
kubectl get pvc
```

### Step 2: Scale Down (Removing Replicas)

Scale back down to 3 replicas:

```bash
kubectl scale statefulset web-storage --replicas=3
```

Watch the sequential scale-down:

```bash
kubectl get pods -l app=nginx-storage -w
```

Observe:
- `web-storage-4` is deleted first (reverse order)
- `web-storage-3` is deleted only after `web-storage-4` is fully terminated

**Important**: Check the PVCs:

```bash
kubectl get pvc
```

Notice: **PVCs are NOT automatically deleted** when scaling down! This prevents accidental data loss.

To clean up orphaned PVCs:

```bash
kubectl delete pvc www-web-storage-3 www-web-storage-4
```

---

## Exercise 6: StatefulSet Update Strategies

### Step 1: Check Current Update Strategy

View the update strategy:

```bash
kubectl get statefulset web-storage -o yaml | grep -A 5 updateStrategy
```

Output:
```yaml
updateStrategy:
  rollingUpdate:
    partition: 0
  type: RollingUpdate
```

### Update Strategy Types

1. **RollingUpdate** (default): Automatically updates Pods in reverse ordinal order
2. **OnDelete**: Updates Pods only when manually deleted

### Step 2: Perform a Rolling Update

Update the NGINX image:

```bash
kubectl set image statefulset/web-storage nginx=nginx:1.26
```

Watch the rolling update:

```bash
kubectl rollout status statefulset/web-storage
```

Monitor Pod updates:

```bash
kubectl get pods -l app=nginx-storage -w
```

Observe:
- Pods are updated in **reverse order** (web-storage-2, then web-storage-1, then web-storage-0)
- Each Pod is fully terminated and recreated before the next one updates
- Ensures ordinal order is maintained

### Step 3: Using Partition for Staged Rollouts

The `partition` parameter allows you to update only Pods with ordinal >= partition.

Update only Pods 2 and above:

```bash
kubectl patch statefulset web-storage -p '{"spec":{"updateStrategy":{"type":"RollingUpdate","rollingUpdate":{"partition":2}}}}'

# Now update the image
kubectl set image statefulset/web-storage nginx=nginx:alpine
```

Check which Pods updated:

```bash
kubectl get pods -l app=nginx-storage -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[0].image}{"\n"}{end}'
```

Output:
```
web-storage-0    nginx:1.26
web-storage-1    nginx:1.26
web-storage-2    nginx:alpine
```

Only `web-storage-2` (ordinal >= 2) was updated!

Reset the partition to update all:

```bash
kubectl patch statefulset web-storage -p '{"spec":{"updateStrategy":{"rollingUpdate":{"partition":0}}}}'
```

---

## Exercise 7: Deploy a Real Stateful Application (MySQL)

### Step 1: Review the MySQL StatefulSet

Create `mysql-statefulset.yaml`:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: mysql-headless
  labels:
    app: mysql
spec:
  clusterIP: None
  selector:
    app: mysql
  ports:
  - port: 3306
    name: mysql
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: mysql
spec:
  serviceName: "mysql-headless"
  replicas: 1
  selector:
    matchLabels:
      app: mysql
  template:
    metadata:
      labels:
        app: mysql
    spec:
      containers:
      - name: mysql
        image: mysql:8.0
        ports:
        - containerPort: 3306
          name: mysql
        env:
        - name: MYSQL_ROOT_PASSWORD
          value: "MySecurePassword123"
        - name: MYSQL_DATABASE
          value: "testdb"
        volumeMounts:
        - name: mysql-data
          mountPath: /var/lib/mysql
        livenessProbe:
          exec:
            command:
            - mysqladmin
            - ping
            - -h
            - localhost
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
        readinessProbe:
          exec:
            command:
            - mysql
            - -h
            - localhost
            - -u
            - root
            - -pMySecurePassword123
            - -e
            - "SELECT 1"
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 2
  volumeClaimTemplates:
  - metadata:
      name: mysql-data
    spec:
      accessModes: [ "ReadWriteOnce" ]
      resources:
        requests:
          storage: 2Gi
```

### Step 2: Deploy MySQL

Apply the manifest:

```bash
kubectl apply -f mysql-statefulset.yaml
```

Wait for MySQL to be ready:

```bash
kubectl get pods -l app=mysql -w
```

### Step 3: Connect to MySQL and Create Data

Connect to the MySQL Pod:

```bash
kubectl exec -it mysql-0 -- mysql -uroot -pMySecurePassword123
```

Inside MySQL:

```sql
USE testdb;

CREATE TABLE users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100),
  email VARCHAR(100)
);

INSERT INTO users (name, email) VALUES
  ('Alice', 'alice@example.com'),
  ('Bob', 'bob@example.com'),
  ('Charlie', 'charlie@example.com');

SELECT * FROM users;

EXIT;
```

### Step 4: Test Data Persistence

Delete the MySQL Pod:

```bash
kubectl delete pod mysql-0
```

Wait for it to recreate:

```bash
kubectl get pods -l app=mysql -w
```

Reconnect and verify data:

```bash
kubectl exec -it mysql-0 -- mysql -uroot -pMySecurePassword123 -e "SELECT * FROM testdb.users;"
```

The data persists because the PVC is remounted!

---

## Troubleshooting Guide

### Issue 1: Pods Stuck in Pending

Check PVC status:

```bash
kubectl get pvc
kubectl describe pvc <pvc-name>
```

Common causes:
- No StorageClass available
- Insufficient storage capacity
- StorageClass doesn't support dynamic provisioning

Solution:
```bash
# Check available storage classes
kubectl get storageclass

# Create a default storage class if missing
# Or modify your StatefulSet to use an existing storage class
```

### Issue 2: Pod Not Starting in Order

Check Pod status:

```bash
kubectl describe pod <pod-name>
```

Common causes:
- Previous Pod not Ready (check probes)
- Previous Pod in CrashLoopBackOff
- Resource constraints (CPU/Memory)

Solution:
```bash
# Fix the blocking Pod first
kubectl logs <previous-pod-name>
kubectl describe pod <previous-pod-name>
```

### Issue 3: Headless Service Not Resolving

Test DNS resolution:

```bash
kubectl run -it --rm debug --image=busybox --restart=Never -- nslookup <service-name>
```

Common causes:
- Service name doesn't match `serviceName` in StatefulSet
- CoreDNS not running
- Network policies blocking DNS

Solution:
```bash
# Verify CoreDNS is running
kubectl get pods -n kube-system -l k8s-app=kube-dns

# Check service configuration
kubectl get svc <service-name> -o yaml
```

### Issue 4: PVC Not Deleted After Scale Down

This is **by design** to prevent data loss.

Manual cleanup:

```bash
# List orphaned PVCs
kubectl get pvc

# Delete specific PVCs
kubectl delete pvc <pvc-name>

# Delete all PVCs for a StatefulSet (CAUTION: Data loss!)
kubectl delete pvc -l app=<statefulset-label>
```

### Issue 5: Rolling Update Stuck

Check rollout status:

```bash
kubectl rollout status statefulset/<name>
kubectl describe statefulset <name>
```

Common causes:
- New image doesn't exist or can't be pulled
- Pod fails health checks with new version
- Insufficient resources for new Pod

Solution:
```bash
# Check Pod logs
kubectl logs <pod-name>

# Rollback to previous version
kubectl rollout undo statefulset/<name>

# Or manually fix and delete Pods
kubectl delete pod <pod-name>
```

---

## Key Takeaways

1. **Stable Identity**: StatefulSets provide stable Pod names (web-0, web-1) and DNS hostnames
2. **Ordered Operations**: Pods are created, scaled, and updated in sequential order
3. **Persistent Storage**: volumeClaimTemplates create unique PVCs for each Pod
4. **Headless Services**: Required for stable network identity (clusterIP: None)
5. **Use for Stateful Apps**: Databases, queues, clustered systems requiring stable identity
6. **PVC Retention**: PVCs are not auto-deleted on scale-down (prevents data loss)
7. **Rolling Updates**: Occur in reverse ordinal order (2, 1, 0)
8. **Partition Updates**: Allow staged rollouts to specific Pod ordinals
9. **Different from Deployments**: Sequential operations vs parallel, stable identity vs random

---

## Comparison Table: StatefulSet vs Deployment vs DaemonSet

| Feature | StatefulSet | Deployment | DaemonSet |
|---------|-------------|------------|-----------|
| **Pod Identity** | Stable, ordered (web-0, web-1) | Random (web-abc123) | One per node |
| **Scaling Order** | Sequential | Parallel | Automatic (node count) |
| **Update Order** | Sequential (reverse) | Rolling or recreate | Rolling per node |
| **Storage** | Unique per Pod | Shared or none | Usually host volumes |
| **DNS** | Stable hostname | Via Service only | Via Service |
| **Use Case** | Databases, queues | Stateless apps | Node services |
| **Replica Count** | User specified | User specified | Node count |
| **Pod Naming** | Predictable ordinal | Random suffix | Random suffix |

---

## CKA Exam Relevance

StatefulSets are a key topic in the CKA exam. You should know:

1. How to create a StatefulSet with persistent storage
2. How to configure Headless Services
3. How to scale StatefulSets
4. How to update StatefulSets using rolling updates
5. How to troubleshoot StatefulSet Pod issues
6. The differences between StatefulSets and Deployments
7. How to access individual StatefulSet Pods via DNS

**Exam Tips:**
- Practice creating StatefulSets from scratch (not just applying YAML)
- Know the kubectl commands for scaling and updating
- Understand volumeClaimTemplates syntax
- Be familiar with Pod ordering and naming conventions

---

## Lab Cleanup

Remove all StatefulSet resources:

```bash
# Delete the basic StatefulSet
kubectl delete statefulset web
kubectl delete service nginx-headless

# Delete the StatefulSet with storage
kubectl delete statefulset web-storage
kubectl delete service nginx-storage
kubectl delete pvc -l app=nginx-storage

# Delete MySQL StatefulSet
kubectl delete statefulset mysql
kubectl delete service mysql-headless
kubectl delete pvc -l app=mysql

# Verify cleanup
kubectl get statefulsets
kubectl get pvc
kubectl get pods
```

---

## Additional Commands Reference

```bash
# Create StatefulSet
kubectl create -f statefulset.yaml

# Get StatefulSets
kubectl get statefulsets
kubectl get sts  # Short form

# Describe StatefulSet
kubectl describe statefulset <name>

# Scale StatefulSet
kubectl scale statefulset <name> --replicas=<count>

# Update StatefulSet image
kubectl set image statefulset/<name> <container>=<image>

# Check rollout status
kubectl rollout status statefulset/<name>

# View rollout history
kubectl rollout history statefulset/<name>

# Rollback to previous version
kubectl rollout undo statefulset/<name>

# Patch StatefulSet
kubectl patch statefulset <name> -p '<json-patch>'

# Delete StatefulSet (keeps PVCs)
kubectl delete statefulset <name>

# Delete StatefulSet and PVCs
kubectl delete statefulset <name>
kubectl delete pvc -l app=<label>

# Get StatefulSet YAML
kubectl get statefulset <name> -o yaml

# Edit StatefulSet
kubectl edit statefulset <name>

# View events
kubectl get events --field-selector involvedObject.kind=StatefulSet

# Check Pod distribution
kubectl get pods -l <label> -o wide

# Access specific Pod
kubectl exec -it <pod-name> -- /bin/bash

# DNS lookup
kubectl run -it --rm debug --image=busybox -- nslookup <pod-name>.<service-name>
```

---

## Real-World Example: Redis Cluster

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: redis-config
data:
  redis.conf: |
    appendonly yes
    appendfilename "appendonly.aof"
    appendfsync everysec
---
apiVersion: v1
kind: Service
metadata:
  name: redis-headless
spec:
  clusterIP: None
  selector:
    app: redis
  ports:
  - port: 6379
    name: redis
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: redis
spec:
  serviceName: "redis-headless"
  replicas: 3
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7.2-alpine
        command:
        - redis-server
        - /config/redis.conf
        ports:
        - containerPort: 6379
          name: redis
        volumeMounts:
        - name: redis-data
          mountPath: /data
        - name: config
          mountPath: /config
        livenessProbe:
          tcpSocket:
            port: 6379
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          exec:
            command:
            - redis-cli
            - ping
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: config
        configMap:
          name: redis-config
  volumeClaimTemplates:
  - metadata:
      name: redis-data
    spec:
      accessModes: [ "ReadWriteOnce" ]
      resources:
        requests:
          storage: 1Gi
```

---

## Additional Resources

- [Kubernetes StatefulSet Documentation](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/)
- [StatefulSet Basics Tutorial](https://kubernetes.io/docs/tutorials/stateful-application/basic-stateful-set/)
- [Deploying MySQL with StatefulSets](https://kubernetes.io/docs/tasks/run-application/run-replicated-stateful-application/)
- [StatefulSet Update Strategies](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/#update-strategies)
- [Debugging StatefulSets](https://kubernetes.io/docs/tasks/debug/debug-application/debug-statefulset/)

---

## Next Steps

Now that you understand StatefulSets, proceed to:
- [Lab 39: Persistent Storage](lab39-storage-persistent-storage.md) - Deep dive into storage concepts
- [Lab 09: Health Checks and Probes](lab09-pod-health-probes.md) - Implement health checks for stateful apps
- [Lab 37: Resource Quotas & Limits](lab37-resmgmt-resource-quotas-limits.md) - Resource management

---

**Lab Created**: March 2026
**Compatible with**: Kubernetes 1.24+
**Exam Relevance**: CKA, CKAD
