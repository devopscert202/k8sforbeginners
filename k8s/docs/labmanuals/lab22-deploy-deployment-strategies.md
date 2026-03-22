# Lab 22: Kubernetes Deployment Strategies

## Overview
In this lab, you will learn how to deploy applications using Kubernetes Deployments and Services. You'll understand deployment strategies, scaling, rolling updates, and how to expose your applications to network traffic.

## Prerequisites
- A running Kubernetes cluster (Minikube, Kind, or any K8s cluster)
- `kubectl` CLI tool installed and configured
- Completion of [Lab 01: Creating Pods](lab01-basics-creating-pods.md) and [Lab 02: Creating Services](lab02-basics-creating-services.md)
- Basic understanding of Pods and Services

## Learning Objectives
By the end of this lab, you will be able to:
- Deploy applications using Kubernetes Deployments
- Create and configure Services to expose Deployments
- Scale Deployments up and down
- Perform rolling updates and rollbacks
- Understand deployment strategies (RollingUpdate, Recreate)
- Troubleshoot common deployment issues

---

## What is a Kubernetes Deployment?

### The Power of Deployments

A **Deployment** is a Kubernetes resource that manages the lifecycle of Pods and ReplicaSets. It provides:

- **Declarative updates** - Define desired state, Kubernetes makes it happen
- **Rolling updates** - Update applications with zero downtime
- **Rollback capability** - Revert to previous versions easily
- **Self-healing** - Automatically replaces failed Pods
- **Scaling** - Easily scale applications up or down
- **Version history** - Track deployment revisions

### Deployment vs Pod

| Feature | Pod | Deployment |
|---------|-----|------------|
| **Self-healing** | No | Yes |
| **Rolling updates** | No | Yes |
| **Rollback** | No | Yes |
| **Scaling** | Manual | Automatic/Easy |
| **Revision history** | No | Yes |
| **Production use** | No | Yes |

---

## Exercise 1: Review the Apache Deployment

### Step 1: Navigate to the Lab Directory

```bash
cd k8s/labs/deployment
```

### Step 2: Review the Deployment Manifest

Let's examine `apache_deploy.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: apache-deployment
  labels:
    app: apache
spec:
  replicas: 2
  selector:
    matchLabels:
      app: apache
  template:
    metadata:
      labels:
        app: apache
    spec:
      containers:
      - name: apache-container
        image: karthickponcloud/k8slabs:apache_v1
        ports:
        - containerPort: 80
```

**Understanding the manifest:**

- `apiVersion: apps/v1` - Uses the apps API group (for Deployments)
- `kind: Deployment` - Defines this as a Deployment resource
- `metadata.name: apache-deployment` - Name of the Deployment
- `metadata.labels.app: apache` - Labels for the Deployment itself
- `spec.replicas: 2` - Runs 2 identical Pods
- `spec.selector.matchLabels` - How the Deployment finds its Pods
- `spec.template` - Pod template used to create Pods
  - `metadata.labels.app: apache` - Labels applied to Pods (must match selector)
  - `containers` - Container specification
  - `image: karthickponcloud/k8slabs:apache_v1` - Custom Apache image (version 1)
  - `containerPort: 80` - Apache HTTP port

**Important**: The labels in `selector.matchLabels` MUST match the labels in `template.metadata.labels`.

---

## Exercise 2: Deploy the Apache Application

### Step 1: Create the Deployment

Apply the Deployment manifest:

```bash
kubectl apply -f apache_deploy.yaml
```

Expected output:
```
deployment.apps/apache-deployment created
```

### Step 2: Verify the Deployment

Check Deployment status:
```bash
kubectl get deployments
```

Expected output:
```
NAME                READY   UP-TO-DATE   AVAILABLE   AGE
apache-deployment   2/2     2            2           30s
```

**Understanding the output:**
- `READY: 2/2` - 2 out of 2 desired Pods are ready
- `UP-TO-DATE: 2` - 2 Pods are at the latest version
- `AVAILABLE: 2` - 2 Pods are available to serve traffic
- `AGE: 30s` - Deployment age

### Step 3: View the Pods

List Pods created by the Deployment:
```bash
kubectl get pods -l app=apache
```

Expected output:
```
NAME                                 READY   STATUS    RESTARTS   AGE
apache-deployment-5d6c8f5b7d-abc12   1/1     Running   0          45s
apache-deployment-5d6c8f5b7d-xyz89   1/1     Running   0          45s
```

Notice the Pod names follow the pattern: `<deployment-name>-<replicaset-hash>-<random>`

### Step 4: View the ReplicaSet

Deployments create ReplicaSets to manage Pods:

```bash
kubectl get replicasets -l app=apache
```

Expected output:
```
NAME                           DESIRED   CURRENT   READY   AGE
apache-deployment-5d6c8f5b7d   2         2         2       1m
```

The ReplicaSet ensures the desired number of Pods are always running.

### Step 5: Get Detailed Information

View comprehensive Deployment details:
```bash
kubectl describe deployment apache-deployment
```

Key sections to examine:
- **Replicas**: Shows desired, current, and available replicas
- **Selector**: Label selector used to find Pods
- **Pod Template**: The template used to create Pods
- **Events**: Recent activities (scaling, updates, etc.)

---

## Exercise 3: Create the Service

### Step 1: Review the Service Manifest

Let's examine `apache_service.yaml`:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: apache-service
spec:
  selector:
    app: apache
  ports:
  - protocol: TCP
    port: 80
    targetPort: 80
  type: NodePort
```

**Understanding the manifest:**
- `metadata.name: apache-service` - Service name
- `spec.selector.app: apache` - Selects Pods with label `app=apache`
- `spec.ports`:
  - `port: 80` - Service port (how it's accessed)
  - `targetPort: 80` - Container port (where traffic goes)
  - `protocol: TCP` - Transport protocol
- `type: NodePort` - Exposes service on Node's IP at a static port

### Step 2: Create the Service

Apply the Service manifest:

```bash
kubectl apply -f apache_service.yaml
```

Expected output:
```
service/apache-service created
```

### Step 3: Verify the Service

Check Service details:
```bash
kubectl get service apache-service
```

Expected output:
```
NAME             TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
apache-service   NodePort   10.96.150.200   <none>        80:30456/TCP   15s
```

The NodePort (30456 in this example) is randomly assigned between 30000-32767.

### Step 4: Check Service Endpoints

Verify the Service has discovered the Pods:
```bash
kubectl get endpoints apache-service
```

Expected output:
```
NAME             ENDPOINTS                           AGE
apache-service   172.17.0.3:80,172.17.0.4:80         30s
```

You should see two endpoints (one for each Pod)!

### Step 5: Test the Service

**Option A: From within the cluster**
```bash
kubectl run test-pod --image=busybox --rm -it --restart=Never -- wget -qO- http://apache-service
```

**Option B: Using port-forward**
```bash
kubectl port-forward service/apache-service 8080:80
```

In another terminal or browser:
```bash
curl http://localhost:8080
```

**Option C: Using Minikube (if applicable)**
```bash
minikube service apache-service
```

---

## Exercise 4: Scaling the Deployment

### What is Scaling?

Scaling adjusts the number of Pod replicas running your application. You can:
- **Scale up** - Increase replicas to handle more traffic
- **Scale down** - Decrease replicas to save resources

### Step 1: Scale Up

Increase replicas from 2 to 5:

```bash
kubectl scale deployment apache-deployment --replicas=5
```

Expected output:
```
deployment.apps/apache-deployment scaled
```

### Step 2: Verify Scaling

Watch the Pods being created:
```bash
kubectl get pods -l app=apache -w
```

Press `Ctrl+C` to stop watching.

Check final state:
```bash
kubectl get deployment apache-deployment
```

Expected output:
```
NAME                READY   UP-TO-DATE   AVAILABLE   AGE
apache-deployment   5/5     5            5           5m
```

### Step 3: Verify Service Endpoints

The Service automatically discovered the new Pods:

```bash
kubectl get endpoints apache-service
```

You should now see 5 endpoints instead of 2!

### Step 4: Scale Down

Reduce replicas to 3:

```bash
kubectl scale deployment apache-deployment --replicas=3
```

Verify:
```bash
kubectl get pods -l app=apache
```

You should see only 3 Pods running. Kubernetes terminated 2 Pods gracefully.

---

## Exercise 5: Rolling Updates

### What are Rolling Updates?

Rolling updates allow you to update your application with **zero downtime** by:
- Gradually replacing old Pods with new ones
- Ensuring minimum availability during updates
- Automatically rolling back if updates fail

### Step 1: Check Current Image

View the current image version:
```bash
kubectl describe deployment apache-deployment | grep Image
```

Output:
```
    Image:        karthickponcloud/k8slabs:apache_v1
```

### Step 2: Update the Image

Update to version 2 (simulating a new release):

```bash
kubectl set image deployment/apache-deployment apache-container=karthickponcloud/k8slabs:apache_v2
```

Expected output:
```
deployment.apps/apache-deployment image updated
```

**Note**: `apache-container` is the name of the container in the Pod template.

### Step 3: Watch the Rolling Update

Monitor the update in real-time:

```bash
kubectl rollout status deployment/apache-deployment
```

Expected output:
```
Waiting for deployment "apache-deployment" rollout to finish: 1 out of 3 new replicas have been updated...
Waiting for deployment "apache-deployment" rollout to finish: 2 out of 3 new replicas have been updated...
Waiting for deployment "apache-deployment" rollout to finish: 2 old replicas are pending termination...
deployment "apache-deployment" successfully rolled out
```

### Step 4: Verify the Update

Check the new image:
```bash
kubectl describe deployment apache-deployment | grep Image
```

Output:
```
    Image:        karthickponcloud/k8slabs:apache_v2
```

View the ReplicaSets:
```bash
kubectl get replicasets -l app=apache
```

Expected output:
```
NAME                           DESIRED   CURRENT   READY   AGE
apache-deployment-5d6c8f5b7d   0         0         0       10m
apache-deployment-7f8b9c4a2e   3         3         3       2m
```

Notice:
- Old ReplicaSet (5d6c8f5b7d) has 0 Pods
- New ReplicaSet (7f8b9c4a2e) has 3 Pods
- Old ReplicaSet is kept for rollback purposes

### Step 5: View Rollout History

Check deployment history:
```bash
kubectl rollout history deployment/apache-deployment
```

Expected output:
```
deployment.apps/apache-deployment
REVISION  CHANGE-CAUSE
1         <none>
2         <none>
```

To see details of a specific revision:
```bash
kubectl rollout history deployment/apache-deployment --revision=2
```

---

## Exercise 6: Rollback

### When to Rollback?

Rollback when:
- New version has critical bugs
- Application crashes or fails health checks
- Performance degradation
- Configuration errors

### Step 1: Rollback to Previous Version

Undo the last deployment:

```bash
kubectl rollout undo deployment/apache-deployment
```

Expected output:
```
deployment.apps/apache-deployment rolled back
```

### Step 2: Verify Rollback

Check rollout status:
```bash
kubectl rollout status deployment/apache-deployment
```

Verify the image is back to v1:
```bash
kubectl describe deployment apache-deployment | grep Image
```

Output:
```
    Image:        karthickponcloud/k8slabs:apache_v1
```

### Step 3: Rollback to Specific Revision

You can rollback to any previous revision:

```bash
kubectl rollout undo deployment/apache-deployment --to-revision=1
```

### Step 4: View Updated History

```bash
kubectl rollout history deployment/apache-deployment
```

Notice the revision numbers have changed!

---

## Exercise 7: Deployment Strategies

### Understanding Deployment Strategies

Kubernetes supports two main deployment strategies:

#### 1. RollingUpdate (Default)

- Gradually replaces old Pods with new ones
- Zero downtime
- Configurable with `maxSurge` and `maxUnavailable`

**Configuration:**
```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1        # Max number of Pods over desired count
    maxUnavailable: 0  # Max number of Pods that can be unavailable
```

**Use cases**: Most production applications

#### 2. Recreate

- Terminates all old Pods before creating new ones
- Causes downtime
- Faster than rolling update
- Guarantees no two versions run simultaneously

**Configuration:**
```yaml
strategy:
  type: Recreate
```

**Use cases**: Applications that can't run multiple versions simultaneously

### Step 1: View Current Strategy

```bash
kubectl get deployment apache-deployment -o yaml | grep -A 5 strategy
```

Default output:
```yaml
strategy:
  rollingUpdate:
    maxSurge: 25%
    maxUnavailable: 25%
  type: RollingUpdate
```

### Step 2: Update Strategy (Optional Exercise)

Create a modified deployment with Recreate strategy:

```bash
kubectl patch deployment apache-deployment -p '{"spec":{"strategy":{"type":"Recreate"}}}'
```

Now try an update and observe the difference:
```bash
kubectl set image deployment/apache-deployment apache-container=karthickponcloud/k8slabs:apache_v2
kubectl get pods -l app=apache -w
```

You'll see all Pods terminate before new ones are created!

---

## Exercise 8: Self-Healing Demonstration

### Step 1: Test Self-Healing

Delete a Pod and watch it get recreated:

```bash
# Get a Pod name
POD_NAME=$(kubectl get pods -l app=apache -o jsonpath='{.items[0].metadata.name}')

# Delete it
kubectl delete pod $POD_NAME

# Watch Pods
kubectl get pods -l app=apache -w
```

Result: A new Pod is automatically created to maintain the desired replica count!

### Step 2: Simulate Node Failure (Advanced)

If you have multiple nodes:

```bash
# Cordon a node (mark it unschedulable)
kubectl cordon <node-name>

# Drain the node (evict Pods)
kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data

# Watch Pods get rescheduled to other nodes
kubectl get pods -l app=apache -o wide -w
```

Clean up:
```bash
kubectl uncordon <node-name>
```

---

## Exercise 9: Deployment Best Practices

### 1. Always Use Labels

Labels help organize and select resources:

```yaml
metadata:
  labels:
    app: apache
    version: v1
    environment: production
```

### 2. Set Resource Requests and Limits

Ensure proper resource allocation:

```yaml
resources:
  requests:
    memory: "128Mi"
    cpu: "100m"
  limits:
    memory: "256Mi"
    cpu: "200m"
```

### 3. Use Health Checks

Add liveness and readiness probes:

```yaml
livenessProbe:
  httpGet:
    path: /
    port: 80
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /
    port: 80
  initialDelaySeconds: 5
  periodSeconds: 5
```

### 4. Configure Update Strategy

Fine-tune rolling updates:

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1
    maxUnavailable: 0
```

### 5. Use Change-Cause Annotations

Track deployment changes:

```bash
kubectl annotate deployment apache-deployment kubernetes.io/change-cause="Update to v2 with bug fixes"
```

Now rollout history shows the change cause!

---

## Lab Cleanup

Remove all resources created in this lab:

```bash
# Delete the Service
kubectl delete -f apache_service.yaml

# Delete the Deployment (also deletes Pods and ReplicaSets)
kubectl delete -f apache_deploy.yaml

# Verify cleanup
kubectl get all -l app=apache
```

Alternative command-line cleanup:
```bash
kubectl delete deployment apache-deployment
kubectl delete service apache-service
```

---

## Troubleshooting Guide

### Issue: Deployment stuck in progress

**Symptoms**: Pods not reaching ready state

**Check 1**: View Deployment events
```bash
kubectl describe deployment apache-deployment
```

**Check 2**: Check Pod status
```bash
kubectl get pods -l app=apache
kubectl describe pod <pod-name>
```

**Check 3**: View Pod logs
```bash
kubectl logs <pod-name>
```

**Common causes**:
- Image pull errors (wrong image name/tag)
- Insufficient resources
- Failed health checks
- Configuration errors

### Issue: Rolling update too slow

**Solution**: Adjust update strategy
```bash
kubectl patch deployment apache-deployment -p '{"spec":{"strategy":{"rollingUpdate":{"maxSurge":"50%","maxUnavailable":"25%"}}}}'
```

### Issue: Service not routing to new Pods

**Check**: Verify label selectors match
```bash
# Check Deployment labels
kubectl get deployment apache-deployment -o jsonpath='{.spec.template.metadata.labels}'

# Check Service selector
kubectl get service apache-service -o jsonpath='{.spec.selector}'
```

They must match!

### Issue: Can't rollback

**Check**: View rollout history
```bash
kubectl rollout history deployment/apache-deployment
```

**Note**: History limit defaults to 10. Old revisions are automatically deleted.

---

## Key Takeaways

1. **Deployments** provide declarative updates and self-healing for Pods
2. **ReplicaSets** (created by Deployments) ensure desired Pod count
3. **Services** use label selectors to discover and route traffic to Pods
4. **Scaling** is easy with `kubectl scale` command
5. **Rolling updates** enable zero-downtime deployments
6. **Rollback** capability provides safety net for bad deployments
7. **RollingUpdate** strategy is best for most production workloads
8. Always use **health checks** in production
9. Set **resource requests/limits** to ensure stability
10. Use **labels** consistently for organization and selection

---

## Additional Commands Reference

```bash
# Create deployment from command line
kubectl create deployment apache --image=httpd --replicas=3

# Get deployment YAML
kubectl get deployment apache-deployment -o yaml

# Edit deployment
kubectl edit deployment apache-deployment

# Pause rollout (for canary deployments)
kubectl rollout pause deployment/apache-deployment

# Resume rollout
kubectl rollout resume deployment/apache-deployment

# View deployment in YAML with status
kubectl get deployment apache-deployment -o yaml

# Scale with autoscaling
kubectl autoscale deployment apache-deployment --min=2 --max=10 --cpu-percent=80

# Delete deployment but keep Pods (rarely used)
kubectl delete deployment apache-deployment --cascade=orphan

# Force rolling restart (useful for picking up ConfigMap changes)
kubectl rollout restart deployment/apache-deployment
```

---

## Next Steps

1. **Lab 10**: Explore DNS Configuration in Kubernetes
2. **Lab 11**: Learn about Multi-Port Services
3. **Lab 12**: Implement Ingress Controllers for HTTP routing

---

## Additional Reading

- [Kubernetes Deployments Documentation](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
- [Rolling Update Strategy](https://kubernetes.io/docs/tutorials/kubernetes-basics/update/update-intro/)
- [Deployment Strategies Comparison](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#strategy)
- [Health Checks Best Practices](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)

---

**Lab Created**: March 2026
**Compatible with**: Kubernetes 1.24+
**Tested on**: Minikube, Kind, AWS EKS, GCP GKE
