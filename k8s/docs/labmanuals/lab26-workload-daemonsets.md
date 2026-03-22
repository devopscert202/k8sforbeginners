# Lab 26: Kubernetes DaemonSets

## Overview
In this lab, you will learn about DaemonSets, a powerful Kubernetes workload type that ensures a copy of a Pod runs on all (or selected) nodes in your cluster. You'll deploy and manage DaemonSets, understand their use cases, and learn when to use them in production environments.

## Prerequisites
- A running Kubernetes cluster (Minikube, Kind, or any K8s cluster)
- `kubectl` CLI tool installed and configured
- Basic understanding of Pods and Deployments (Lab 01)
- Cluster with multiple nodes (recommended but not required)

## Learning Objectives
By the end of this lab, you will be able to:
- Understand what DaemonSets are and their use cases
- Deploy a DaemonSet across all cluster nodes
- Monitor DaemonSet Pods distribution
- Update and manage DaemonSets
- Understand the difference between DaemonSets and Deployments
- Use node selectors to control DaemonSet placement

---

## What is a DaemonSet?

A **DaemonSet** ensures that all (or some) nodes run a copy of a Pod. As nodes are added to the cluster, Pods are automatically added to them. As nodes are removed from the cluster, those Pods are garbage collected.

### Key Characteristics

- **One Pod per Node**: Automatically runs one Pod on each node
- **Automatic Scheduling**: New nodes automatically get the DaemonSet Pod
- **Cluster-wide Coverage**: Ideal for node-level operations
- **No Replica Count**: Unlike Deployments, you don't specify replicas
- **Node Affinity**: Can be restricted to specific nodes using node selectors

### Common Use Cases

1. **Monitoring Agents**: Running Prometheus node exporter, Datadog agents
2. **Log Collectors**: Fluentd, Logstash, or Filebeat on every node
3. **Storage Daemons**: Ceph, GlusterFS storage daemon on each node
4. **Network Plugins**: Kube-proxy, CNI plugins (Calico, Weave)
5. **Security Agents**: Host-level security scanning tools

---

## Exercise 1: Understanding Your Cluster

### Step 1: Check Cluster Nodes

Before deploying a DaemonSet, let's see how many nodes we have:

```bash
kubectl get nodes
```

Example output:
```
NAME           STATUS   ROLES           AGE   VERSION
controlplane   Ready    control-plane   10d   v1.28.0
node01         Ready    <none>          10d   v1.28.0
node02         Ready    <none>          10d   v1.28.0
```

Make note of the number of nodes. Your DaemonSet will create one Pod per node.

### Step 2: Check Node Labels

View node labels (useful for node selection later):

```bash
kubectl get nodes --show-labels
```

Get detailed information about a node:

```bash
kubectl describe node <node-name>
```

---

## Exercise 2: Deploy Your First DaemonSet

### Step 1: Review the DaemonSet Manifest

Navigate to the workloads directory:
```bash
cd k8s/labs/workloads
```

Let's examine the `daemonset.yaml` file:

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: node-nginx-simple
  namespace: default
  labels:
    app: node-nginx-simple
spec:
  selector:
    matchLabels:
      app: node-nginx-simple
  template:
    metadata:
      labels:
        app: node-nginx-simple
    spec:
      containers:
      - name: nginx
        image: nginx:1.25
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 80
          name: http
```

**Understanding the Manifest:**

- `kind: DaemonSet` - Defines this as a DaemonSet resource
- `selector.matchLabels` - Identifies which Pods the DaemonSet manages
- `template` - Pod template (same as Deployment)
- `image: nginx:1.25` - Uses NGINX web server
- `imagePullPolicy: IfNotPresent` - Only pulls image if not cached locally
- **No replicas field** - DaemonSet automatically determines replica count based on nodes

### Step 2: Deploy the DaemonSet

Apply the manifest:

```bash
kubectl apply -f daemonset.yaml
```

Expected output:
```
daemonset.apps/node-nginx-simple created
```

### Step 3: Verify DaemonSet Creation

Check the DaemonSet:

```bash
kubectl get daemonset
```

Expected output:
```
NAME                DESIRED   CURRENT   READY   UP-TO-DATE   AVAILABLE   NODE SELECTOR   AGE
node-nginx-simple   3         3         3       3            3           <none>          20s
```

**Understanding the output:**
- `DESIRED`: Number of nodes that should run the Pod
- `CURRENT`: Number of nodes running the Pod
- `READY`: Number of Pods ready
- `UP-TO-DATE`: Number of Pods updated to latest spec
- `AVAILABLE`: Number of Pods available
- `NODE SELECTOR`: Node selection criteria (none in this case)

### Step 4: View the Pods

List Pods created by the DaemonSet:

```bash
kubectl get pods -l app=node-nginx-simple -o wide
```

Expected output:
```
NAME                      READY   STATUS    RESTARTS   AGE   IP           NODE
node-nginx-simple-abcd1   1/1     Running   0          30s   10.244.1.5   node01
node-nginx-simple-abcd2   1/1     Running   0          30s   10.244.2.5   node02
node-nginx-simple-abcd3   1/1     Running   0          30s   10.244.0.5   controlplane
```

Notice:
- One Pod per node
- Each Pod has a unique name with a random suffix
- Pods are distributed across all nodes

### Step 5: Inspect DaemonSet Details

Get detailed information:

```bash
kubectl describe daemonset node-nginx-simple
```

Look for:
- Events showing Pod creation on each node
- Update strategy
- Pod template specifications

---

## Exercise 3: Testing DaemonSet Behavior

### Test 1: Pod Self-Healing

Delete one of the DaemonSet Pods:

```bash
# Get a Pod name
POD_NAME=$(kubectl get pods -l app=node-nginx-simple -o jsonpath='{.items[0].metadata.name}')

# Delete it
kubectl delete pod $POD_NAME
```

Immediately check the Pods:

```bash
kubectl get pods -l app=node-nginx-simple -o wide
```

Result: The Pod is automatically recreated on the same node!

### Test 2: Scaling Behavior (Demonstration Only)

Try to scale the DaemonSet:

```bash
kubectl scale daemonset node-nginx-simple --replicas=5
```

Output:
```
Error from server (NotFound): the server could not find the requested resource
```

Why? **DaemonSets cannot be scaled manually** - they automatically match the number of nodes.

### Test 3: Adding a New Node (If Possible)

If you're using a cluster where you can add nodes:

```bash
# For Minikube
minikube node add

# For Kind (create multi-node cluster)
kind create cluster --config=multi-node-config.yaml
```

After adding a node:

```bash
kubectl get pods -l app=node-nginx-simple -o wide
```

You'll see a new Pod automatically created on the new node!

---

## Exercise 4: DaemonSet with Node Selectors

### Step 1: Label a Node

Add a custom label to a node:

```bash
# Replace <node-name> with your actual node name
kubectl label nodes <node-name> disktype=ssd
```

Verify the label:

```bash
kubectl get nodes --show-labels | grep disktype
```

### Step 2: Create a DaemonSet with Node Selector

Create a new file `daemonset-nodeselect.yaml`:

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: nginx-ssd-only
  namespace: default
spec:
  selector:
    matchLabels:
      app: nginx-ssd
  template:
    metadata:
      labels:
        app: nginx-ssd
    spec:
      nodeSelector:
        disktype: ssd
      containers:
      - name: nginx
        image: nginx:1.25
        ports:
        - containerPort: 80
```

Apply it:

```bash
kubectl apply -f daemonset-nodeselect.yaml
```

### Step 3: Verify Selective Deployment

Check where Pods are running:

```bash
kubectl get pods -l app=nginx-ssd -o wide
```

Result: Pods only run on nodes with the `disktype=ssd` label!

---

## Exercise 5: Updating a DaemonSet

### Step 1: Check Current Update Strategy

View the update strategy:

```bash
kubectl get daemonset node-nginx-simple -o yaml | grep -A 5 updateStrategy
```

Default strategy is `RollingUpdate`.

### Step 2: Update the DaemonSet Image

Edit the DaemonSet to use a different NGINX version:

```bash
kubectl set image daemonset/node-nginx-simple nginx=nginx:1.26
```

### Step 3: Monitor the Rollout

Watch the rollout:

```bash
kubectl rollout status daemonset/node-nginx-simple
```

Check rollout history:

```bash
kubectl rollout history daemonset/node-nginx-simple
```

### Step 4: Verify the Update

Describe a Pod to confirm the new image:

```bash
POD_NAME=$(kubectl get pods -l app=node-nginx-simple -o jsonpath='{.items[0].metadata.name}')
kubectl describe pod $POD_NAME | grep Image:
```

---

## Exercise 6: DaemonSet vs Deployment

### Key Differences

| Feature | DaemonSet | Deployment |
|---------|-----------|------------|
| **Scheduling** | One Pod per node (automatic) | User-specified replicas |
| **Use Case** | Node-level services | Application workloads |
| **Scaling** | Scales with cluster nodes | Manual or auto-scaling |
| **Pod Distribution** | Guaranteed one per node | Distributed by scheduler |
| **Replica Count** | Not specified | Explicitly set |
| **Node Addition** | Automatic Pod creation | No automatic action |

### When to Use DaemonSet

Use DaemonSets when you need:
- A service running on every node
- Node monitoring or logging
- Storage or network daemons
- Security agents
- System-level utilities

### When to Use Deployment

Use Deployments when you need:
- Application workloads
- Microservices
- Specific number of replicas
- Rolling updates
- Horizontal scaling

---

## Exercise 7: Accessing DaemonSet Pods

### Option 1: Port Forward to a Pod

```bash
POD_NAME=$(kubectl get pods -l app=node-nginx-simple -o jsonpath='{.items[0].metadata.name}')
kubectl port-forward pod/$POD_NAME 8080:80
```

Test in another terminal:
```bash
curl http://localhost:8080
```

### Option 2: Create a Service (NodePort)

Create a Service for the DaemonSet:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: nginx-daemonset-svc
spec:
  type: NodePort
  selector:
    app: node-nginx-simple
  ports:
  - port: 80
    targetPort: 80
    nodePort: 30080
```

Apply and access:

```bash
kubectl apply -f daemonset-service.yaml

# Get node IP
kubectl get nodes -o wide

# Access via any node
curl http://<node-ip>:30080
```

---

## Lab Cleanup

Remove all DaemonSet resources:

```bash
# Delete the main DaemonSet
kubectl delete daemonset node-nginx-simple

# Delete the selective DaemonSet (if created)
kubectl delete daemonset nginx-ssd-only

# Delete the Service (if created)
kubectl delete service nginx-daemonset-svc

# Remove node labels (if added)
kubectl label nodes <node-name> disktype-

# Verify cleanup
kubectl get daemonsets
kubectl get pods -l app=node-nginx-simple
```

---

## Key Takeaways

1. **DaemonSets ensure one Pod per node** - Perfect for node-level services
2. **Automatic scaling** - Pods are automatically added/removed as nodes join/leave
3. **No manual replica count** - The cluster determines the number of Pods
4. **Node selectors** - Control which nodes run DaemonSet Pods
5. **Rolling updates supported** - Update DaemonSets like Deployments
6. **Use cases**: Monitoring, logging, storage, networking, security agents
7. **Different from Deployments** - Use for cluster-wide node services, not applications

---

## Advanced Topics

### Using Taints and Tolerations

DaemonSets can use tolerations to run on tainted nodes:

```yaml
spec:
  template:
    spec:
      tolerations:
      - key: node-role.kubernetes.io/control-plane
        effect: NoSchedule
```

This allows DaemonSet Pods to run on control-plane nodes.

### Resource Limits

Always set resource limits for DaemonSets:

```yaml
spec:
  template:
    spec:
      containers:
      - name: nginx
        resources:
          requests:
            memory: "64Mi"
            cpu: "250m"
          limits:
            memory: "128Mi"
            cpu: "500m"
```

### HostPath Volumes

DaemonSets often need access to host filesystem:

```yaml
spec:
  template:
    spec:
      containers:
      - name: log-collector
        volumeMounts:
        - name: varlog
          mountPath: /var/log
      volumes:
      - name: varlog
        hostPath:
          path: /var/log
```

---

## Additional Commands Reference

```bash
# List all DaemonSets
kubectl get daemonsets --all-namespaces

# Get DaemonSet YAML
kubectl get daemonset <name> -o yaml

# Edit DaemonSet
kubectl edit daemonset <name>

# Delete DaemonSet (keeps Pods)
kubectl delete daemonset <name> --cascade=orphan

# View DaemonSet events
kubectl get events --field-selector involvedObject.kind=DaemonSet

# Check which nodes run DaemonSet Pods
kubectl get pods -l <label-selector> -o wide

# Restart DaemonSet Pods (update any field)
kubectl patch daemonset <name> -p '{"spec":{"template":{"metadata":{"annotations":{"kubectl.kubernetes.io/restartedAt":"'$(date +%Y-%m-%dT%H:%M:%S)'"}}}}}'
```

---

## Troubleshooting

**Issue**: DaemonSet Pods not scheduling

Check:
```bash
kubectl describe daemonset <name>
kubectl describe pod <pod-name>
```

Common causes:
- Node taints preventing scheduling
- Insufficient resources on nodes
- Node selector doesn't match any nodes
- Image pull errors

**Issue**: Pods missing on some nodes

```bash
# Check node conditions
kubectl describe node <node-name>

# Check node labels
kubectl get nodes --show-labels

# Verify node selector matches
kubectl get daemonset <name> -o yaml | grep -A 5 nodeSelector
```

**Issue**: Old Pods not terminating during update

```bash
# Check update strategy
kubectl get daemonset <name> -o yaml | grep -A 10 updateStrategy

# Force delete stuck Pod
kubectl delete pod <pod-name> --grace-period=0 --force
```

---

## Real-World Examples

### Example 1: Log Collection DaemonSet (Fluentd)

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: fluentd
  namespace: kube-system
spec:
  selector:
    matchLabels:
      app: fluentd
  template:
    metadata:
      labels:
        app: fluentd
    spec:
      containers:
      - name: fluentd
        image: fluent/fluentd-kubernetes-daemonset:v1
        volumeMounts:
        - name: varlog
          mountPath: /var/log
        - name: varlibdockercontainers
          mountPath: /var/lib/docker/containers
          readOnly: true
      volumes:
      - name: varlog
        hostPath:
          path: /var/log
      - name: varlibdockercontainers
        hostPath:
          path: /var/lib/docker/containers
```

### Example 2: Node Monitoring (Node Exporter)

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: node-exporter
  namespace: monitoring
spec:
  selector:
    matchLabels:
      app: node-exporter
  template:
    metadata:
      labels:
        app: node-exporter
    spec:
      hostNetwork: true
      hostPID: true
      containers:
      - name: node-exporter
        image: prom/node-exporter:latest
        ports:
        - containerPort: 9100
          hostPort: 9100
        volumeMounts:
        - name: proc
          mountPath: /host/proc
          readOnly: true
        - name: sys
          mountPath: /host/sys
          readOnly: true
      volumes:
      - name: proc
        hostPath:
          path: /proc
      - name: sys
        hostPath:
          path: /sys
```

---

## Next Steps

Now that you understand DaemonSets, proceed to:
- [Lab 29: CronJobs](lab29-workload-cronjobs.md) - Learn about scheduled jobs
- [Lab 30: Horizontal Pod Autoscaling](lab30-workload-hpa.md) - Auto-scale your workloads
- [Lab 09: Health Checks and Probes](lab09-pod-health-probes.md) - Implement liveness and readiness probes

## Further Reading

- [Kubernetes DaemonSet Documentation](https://kubernetes.io/docs/concepts/workloads/controllers/daemonset/)
- [DaemonSet Rolling Update](https://kubernetes.io/docs/tasks/manage-daemon/update-daemon-set/)
- [Node Affinity and Selectors](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/)

---

**Lab Created**: March 2026
**Compatible with**: Kubernetes 1.24+
