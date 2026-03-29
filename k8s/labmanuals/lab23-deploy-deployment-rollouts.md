# Lab 23: Deployment Strategies and Rollouts

## Overview
In this lab, you will master Kubernetes deployment strategies, rolling updates, and rollback mechanisms. You'll learn how to perform zero-downtime deployments, manage deployment history, control rollout speed, and recover from failed deployments using real-world scenarios and best practices.

## Prerequisites
- A running Kubernetes cluster (Minikube, Kind, or any K8s cluster)
- `kubectl` CLI tool installed and configured
- Basic understanding of Deployments and Services
- Completion of Lab 01 (Creating Pods) recommended

## Learning Objectives
By the end of this lab, you will be able to:
- Perform rolling updates with zero downtime
- Control rollout parameters (maxSurge, maxUnavailable)
- Monitor rollout status and progress
- View and manage deployment revision history
- Rollback deployments to previous versions
- Pause and resume rollouts for canary deployments
- Implement different deployment strategies
- Troubleshoot failed rollouts

---

## What are Deployment Rollouts?

### The Challenge of Application Updates

Updating applications in production is risky:
- New versions may have bugs
- Updates can cause downtime
- Rollback procedures need to be fast
- Users expect continuous availability

**Kubernetes Deployments** solve these challenges with built-in rollout and rollback capabilities.

### Key Capabilities

- **Rolling Updates**: Gradually replace old Pods with new ones
- **Zero Downtime**: Service remains available during updates
- **Revision History**: Track and manage deployment versions
- **Declarative Rollback**: Revert to any previous version instantly
- **Pause/Resume**: Control rollout progress for testing
- **Configurable Speed**: Control how fast updates occur

### Rollout Strategies

| Strategy | Downtime | Risk | Speed | Use Case |
|----------|----------|------|-------|----------|
| **RollingUpdate** | None | Low | Medium | Most production apps |
| **Recreate** | Yes | High | Fast | Dev/test environments |
| **Blue/Green** | None | Low | Fast | Critical applications |
| **Canary** | None | Very Low | Slow | High-risk updates |

---

## Exercise 1: Basic Rolling Update with Alpine

### Step 1: Navigate to Lab Directory

```bash
cd k8s/labs/workloads
```

### Step 2: Review the Alpine Deployment Manifest

Let's examine `alpine_rollout.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  annotations:
    kubernetes.io/change-cause: kubectl run mydep --image=alpine:latest --record=true --dry-run=true --output=yaml
  labels:
    run: mydep
  name: mydep
spec:
  replicas: 1
  selector:
    matchLabels:
      run: mydep
  template:
    metadata:
      labels:
        run: mydep
    spec:
      containers:
        - image: alpine:latest
          name: mydep
          command: ["/bin/sh"]
          args: ["-c", "while true; do echo 'Container is running'; sleep 3600; done"]
```

**Understanding the manifest:**

- `metadata.annotations.kubernetes.io/change-cause` - Records why this deployment was created (useful for history)
- `spec.replicas: 1` - Single replica for demonstration
- `image: alpine:latest` - Uses latest Alpine Linux image
- `command` and `args` - Keeps container running with a simple loop

**Note**: The comment suggests using `alpine:3.17`, `alpine:3.18`, or `alpine:3.19` for version-specific updates.

### Step 3: Deploy the Initial Version

Apply the deployment:

```bash
kubectl apply -f alpine_rollout.yaml
```

Expected output:
```
deployment.apps/mydep created
```

### Step 4: Verify the Deployment

Check deployment status:

```bash
kubectl get deployment mydep
```

Expected output:
```
NAME    READY   UP-TO-DATE   AVAILABLE   AGE
mydep   1/1     1            1           30s
```

Check the pod:

```bash
kubectl get pods -l run=mydep
```

Expected output:
```
NAME                     READY   STATUS    RESTARTS   AGE
mydep-xxxxxxxxxx-xxxxx   1/1     Running   0          45s
```

### Step 5: Check Current Image Version

Verify the image being used:

```bash
kubectl describe deployment mydep | grep Image
```

Output:
```
    Image:      alpine:latest
```

Or use a more specific command:

```bash
kubectl get deployment mydep -o jsonpath='{.spec.template.spec.containers[0].image}'
```

### Step 6: View Initial Rollout History

Check deployment revision history:

```bash
kubectl rollout history deployment/mydep
```

Expected output:
```
deployment.apps/mydep
REVISION  CHANGE-CAUSE
1         kubectl run mydep --image=alpine:latest --record=true --dry-run=true --output=yaml
```

Notice the CHANGE-CAUSE comes from the annotation in the YAML!

---

## Exercise 2: Perform Rolling Update

### Step 1: Update to Alpine 3.17

Update the image to a specific version:

```bash
kubectl set image deployment/mydep mydep=alpine:3.17
```

Expected output:
```
deployment.apps/mydep image updated
```

**Note**: `mydep` after the deployment name is the container name within the pod template.

### Step 2: Watch the Rollout in Real-Time

Monitor the rollout status:

```bash
kubectl rollout status deployment/mydep
```

Expected output:
```
Waiting for deployment "mydep" rollout to finish: 0 of 1 updated replicas are available...
deployment "mydep" successfully rolled out
```

Watch pods during update:

```bash
kubectl get pods -l run=mydep -w
```

You'll see:
1. Old pod running
2. New pod being created
3. New pod becomes ready
4. Old pod terminates

Press `Ctrl+C` to stop watching.

### Step 3: Verify the Update

Check the new image:

```bash
kubectl describe deployment mydep | grep Image
```

Output:
```
    Image:      alpine:3.17
```

### Step 4: View Updated Rollout History

```bash
kubectl rollout history deployment/mydep
```

Expected output:
```
deployment.apps/mydep
REVISION  CHANGE-CAUSE
1         kubectl run mydep --image=alpine:latest --record=true --dry-run=true --output=yaml
2         <none>
```

Notice revision 2 has no change-cause! Let's fix that.

### Step 5: Annotate the Deployment for Better History

Add a meaningful change-cause annotation:

```bash
kubectl annotate deployment/mydep kubernetes.io/change-cause="Updated to Alpine 3.17 for stability"
```

Now check history again:

```bash
kubectl rollout history deployment/mydep
```

Output:
```
deployment.apps/mydep
REVISION  CHANGE-CAUSE
1         kubectl run mydep --image=alpine:latest --record=true --dry-run=true --output=yaml
2         Updated to Alpine 3.17 for stability
```

Much better! Now you know why each revision was created.

### Step 6: Update to Alpine 3.18

Perform another update:

```bash
kubectl set image deployment/mydep mydep=alpine:3.18
kubectl annotate deployment/mydep kubernetes.io/change-cause="Updated to Alpine 3.18 for security patches"
```

Check history:

```bash
kubectl rollout history deployment/mydep
```

Output:
```
deployment.apps/mydep
REVISION  CHANGE-CAUSE
1         kubectl run mydep --image=alpine:latest --record=true --dry-run=true --output=yaml
2         Updated to Alpine 3.17 for stability
3         Updated to Alpine 3.18 for security patches
```

---

## Exercise 3: Rollback Deployments

### Step 1: View Specific Revision Details

Get details of revision 2:

```bash
kubectl rollout history deployment/mydep --revision=2
```

Expected output:
```
deployment.apps/mydep with revision #2
Pod Template:
  Labels:	run=mydep
  Annotations:	kubernetes.io/change-cause: Updated to Alpine 3.17 for stability
  Containers:
   mydep:
    Image:	alpine:3.17
    ...
```

### Step 2: Rollback to Previous Version

Undo the last rollout (back to 3.17):

```bash
kubectl rollout undo deployment/mydep
```

Expected output:
```
deployment.apps/mydep rolled back
```

Monitor the rollback:

```bash
kubectl rollout status deployment/mydep
```

### Step 3: Verify Rollback

Check current image:

```bash
kubectl describe deployment mydep | grep Image
```

Output:
```
    Image:      alpine:3.17
```

Successfully rolled back to Alpine 3.17!

Check history:

```bash
kubectl rollout history deployment/mydep
```

Output:
```
deployment.apps/mydep
REVISION  CHANGE-CAUSE
1         kubectl run mydep --image=alpine:latest --record=true --dry-run=true --output=yaml
3         Updated to Alpine 3.18 for security patches
4         Updated to Alpine 3.17 for stability
```

Notice:
- Revision 2 is gone (it became revision 4)
- We're now at revision 4 with Alpine 3.17

### Step 4: Rollback to Specific Revision

Rollback to revision 1 (alpine:latest):

```bash
kubectl rollout undo deployment/mydep --to-revision=1
```

Expected output:
```
deployment.apps/mydep rolled back
```

Verify:

```bash
kubectl describe deployment mydep | grep Image
```

Output:
```
    Image:      alpine:latest
```

---

## Exercise 4: Nginx Deployment with Service

### Step 1: Review Nginx Deployment Manifests

Let's examine `nginx_deploy.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
  labels:
    app: nginx
spec:
  replicas: 2
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:latest
        ports:
        - containerPort: 80
```

And `nginx_service.yaml`:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: nginx-service
spec:
  selector:
    app: nginx
  ports:
    - protocol: TCP
      port: 8084
      targetPort: 80
```

**Understanding the setup:**
- Deployment with 2 replicas for high availability
- Service exposes on port 8084, forwards to container port 80
- Perfect for demonstrating zero-downtime updates

### Step 2: Deploy Nginx Application

Apply both manifests:

```bash
kubectl apply -f nginx_deploy.yaml
kubectl apply -f nginx_service.yaml
```

Expected output:
```
deployment.apps/nginx-deployment created
service/nginx-service created
```

### Step 3: Verify Deployment and Service

Check deployment:

```bash
kubectl get deployment nginx-deployment
```

Expected output:
```
NAME               READY   UP-TO-DATE   AVAILABLE   AGE
nginx-deployment   2/2     2            2           30s
```

Check service:

```bash
kubectl get service nginx-service
```

Expected output:
```
NAME            TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)    AGE
nginx-service   ClusterIP   10.96.150.200   <none>        8084/TCP   45s
```

Check pods:

```bash
kubectl get pods -l app=nginx
```

Expected output:
```
NAME                                READY   STATUS    RESTARTS   AGE
nginx-deployment-xxxxxxxxxx-xxxxx   1/1     Running   0          1m
nginx-deployment-xxxxxxxxxx-yyyyy   1/1     Running   0          1m
```

### Step 4: Test the Service

Test from within cluster:

```bash
kubectl run test-pod --image=busybox --rm -it --restart=Never -- wget -qO- http://nginx-service:8084
```

You should see the Nginx welcome page HTML!

Or use port-forward:

```bash
kubectl port-forward service/nginx-service 8084:8084
```

In another terminal or browser: `curl http://localhost:8084`

---

## Exercise 5: Controlled Rolling Update with Multiple Replicas

### Step 1: Scale Up Nginx Deployment

Increase replicas to 4 for better demonstration:

```bash
kubectl scale deployment nginx-deployment --replicas=4
```

Wait for all pods:

```bash
kubectl get pods -l app=nginx -w
```

Press `Ctrl+C` once all 4 are running.

### Step 2: Update Nginx Version

Update to a specific nginx version:

```bash
kubectl set image deployment/nginx-deployment nginx=nginx:1.25
kubectl annotate deployment/nginx-deployment kubernetes.io/change-cause="Updated to nginx 1.25"
```

### Step 3: Watch Rolling Update

In one terminal, watch the rollout:

```bash
kubectl rollout status deployment/nginx-deployment
```

In another terminal, watch pods:

```bash
kubectl get pods -l app=nginx -w
```

You'll observe:
1. New pods created one by one
2. Old pods terminated gradually
3. Service remains available throughout
4. Update completes with all 4 pods on new version

### Step 4: Verify ReplicaSets

View all ReplicaSets:

```bash
kubectl get replicasets -l app=nginx
```

Expected output:
```
NAME                          DESIRED   CURRENT   READY   AGE
nginx-deployment-5d6c8f5b7d   0         0         0       5m
nginx-deployment-7f8b9c4a2e   4         4         4       2m
```

Notice:
- Old ReplicaSet: 0 pods (kept for rollback)
- New ReplicaSet: 4 pods (current version)

---

## Exercise 6: Configure Rollout Strategy

### Step 1: View Current Strategy

Check rollout strategy:

```bash
kubectl get deployment nginx-deployment -o yaml | grep -A 5 strategy
```

Default output:
```yaml
  strategy:
    rollingUpdate:
      maxSurge: 25%
      maxUnavailable: 25%
    type: RollingUpdate
```

**Understanding the parameters:**
- `maxSurge: 25%` - Max 25% more pods than desired during update
  - With 4 replicas: max 5 pods total (4 + 1)
- `maxUnavailable: 25%` - Max 25% of pods can be unavailable
  - With 4 replicas: max 1 pod unavailable
  - Minimum available: 3 pods

### Step 2: Modify Rollout Strategy for Faster Updates

Update strategy for faster rollout:

```bash
kubectl patch deployment nginx-deployment -p '{"spec":{"strategy":{"rollingUpdate":{"maxSurge":"50%","maxUnavailable":"50%"}}}}'
```

Expected output:
```
deployment.apps/nginx-deployment patched
```

Verify:

```bash
kubectl get deployment nginx-deployment -o yaml | grep -A 5 strategy
```

Output:
```yaml
  strategy:
    rollingUpdate:
      maxSurge: 50%
      maxUnavailable: 50%
    type: RollingUpdate
```

### Step 3: Test Faster Rollout

Update to nginx 1.26:

```bash
kubectl set image deployment/nginx-deployment nginx=nginx:1.26
```

Watch the update:

```bash
kubectl get pods -l app=nginx -w
```

Notice it updates faster! With 50% maxSurge and 50% maxUnavailable:
- Can have up to 6 pods (4 + 50% = 6)
- Can have as few as 2 available (4 - 50% = 2)
- Updates complete more quickly

### Step 4: Configure for Zero Downtime (Conservative)

For critical applications, ensure maximum availability:

```bash
kubectl patch deployment nginx-deployment -p '{"spec":{"strategy":{"rollingUpdate":{"maxSurge":"1","maxUnavailable":"0"}}}}'
```

This configuration:
- `maxSurge: 1` - Add one new pod at a time
- `maxUnavailable: 0` - Never reduce available pods
- Guarantees: All 4 pods always available
- Trade-off: Slower updates

---

## Exercise 7: Pause and Resume Rollouts

### What is Pausing?

Pausing allows you to:
- Stop a rollout mid-update
- Test new version with partial traffic
- Perform canary deployments
- Resume when ready

### Step 1: Start an Update

Update to nginx 1.27:

```bash
kubectl set image deployment/nginx-deployment nginx=nginx:1.27
```

### Step 2: Immediately Pause the Rollout

```bash
kubectl rollout pause deployment/nginx-deployment
```

Expected output:
```
deployment.apps/nginx-deployment paused
```

### Step 3: Check Rollout Status

```bash
kubectl rollout status deployment/nginx-deployment
```

Output:
```
Waiting for deployment "nginx-deployment" rollout to finish: 1 out of 4 new replicas have been updated...
```

Check pods:

```bash
kubectl get pods -l app=nginx
```

You'll see a mix of old and new versions running together!

### Step 4: Test Canary Deployment

With the rollout paused:
- Some traffic goes to new version
- Some traffic goes to old version
- You can monitor metrics, logs, errors
- Validate new version before full rollout

Test the service:

```bash
# Multiple requests will hit both versions
for i in {1..10}; do
  kubectl run test-$i --image=busybox --rm -it --restart=Never -- wget -qO- http://nginx-service:8084 | grep nginx
done
```

### Step 5: Resume the Rollout

If new version looks good, resume:

```bash
kubectl rollout resume deployment/nginx-deployment
```

Expected output:
```
deployment.apps/nginx-deployment resumed
```

Monitor completion:

```bash
kubectl rollout status deployment/nginx-deployment
```

If new version has issues, rollback instead:

```bash
kubectl rollout undo deployment/nginx-deployment
```

---

## Exercise 8: Alternative Nginx Deployment Configuration

### Step 1: Review Alternative Manifests

Examine `nginx-deployment.yaml` (different from nginx_deploy.yaml):

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
spec:
  replicas: 4
  selector:
    matchLabels:
      app: httpd
  template:
    metadata:
      labels:
        app: httpd
    spec:
      containers:
        - name: nginx
          image: nginx:latest
          ports:
            - containerPort: 80
```

**Notice the difference:**
- Uses label `app: httpd` (not `app: nginx`)
- Replicas: 4 (instead of 2)
- This demonstrates label mismatch scenarios

And `nginx-service.yaml`:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: nginx-service
spec:
  type: NodePort
  selector:
    app: httpd
  ports:
    - protocol: TCP
      port: 8084
      targetPort: 80
```

**Key difference:**
- `type: NodePort` - Exposes service on node IP
- Selector matches `app: httpd`

### Step 2: Clean Up Previous Deployment

```bash
kubectl delete -f nginx_deploy.yaml
kubectl delete -f nginx_service.yaml
```

### Step 3: Deploy Alternative Configuration

```bash
kubectl apply -f nginx-deployment.yaml
kubectl apply -f nginx-service.yaml
```

### Step 4: Access via NodePort

Get the NodePort:

```bash
kubectl get service nginx-service
```

Expected output:
```
NAME            TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)          AGE
nginx-service   NodePort   10.96.150.200   <none>        8084:30456/TCP   15s
```

Access it:

**If using Minikube:**
```bash
minikube service nginx-service
```

**If using regular cluster:**
```bash
curl http://<node-ip>:30456
```

---

## Lab Cleanup

Remove all resources created in this lab:

```bash
# Delete Alpine deployment
kubectl delete -f alpine_rollout.yaml

# Delete Nginx resources
kubectl delete -f nginx-deployment.yaml
kubectl delete -f nginx-service.yaml

# Or if using the other nginx files
kubectl delete -f nginx_deploy.yaml
kubectl delete -f nginx_service.yaml

# Delete any test pods
kubectl delete pod test-pod --ignore-not-found

# Verify cleanup
kubectl get deployments
kubectl get services
kubectl get pods
```

---

## Key Takeaways

1. **Rolling Updates** enable zero-downtime deployments
2. **Rollout History** tracks all deployment revisions
3. **Rollback** is instant and safe with `kubectl rollout undo`
4. **Annotations** help document why changes were made
5. **maxSurge and maxUnavailable** control update speed and availability
6. **Pause/Resume** enables canary testing and gradual rollouts
7. **ReplicaSets** manage pod versions during updates
8. **Change-Cause** annotations make history meaningful
9. **Rollout Status** command monitors deployment progress
10. **Services** continue routing to available pods during updates

---

## Best Practices

### 1. Always Annotate Changes

```bash
kubectl set image deployment/myapp myapp=myapp:v2
kubectl annotate deployment/myapp kubernetes.io/change-cause="Deploy v2 with bug fix #1234"
```

### 2. Use Specific Image Tags (Not :latest)

```yaml
# Bad: unpredictable
image: nginx:latest

# Good: reproducible
image: nginx:1.25.3
```

### 3. Set Appropriate Rollout Strategy

```yaml
# For critical apps - maximum availability
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1
    maxUnavailable: 0

# For fast updates - acceptable brief downtime
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 50%
    maxUnavailable: 50%
```

### 4. Set Revision History Limit

```yaml
spec:
  revisionHistoryLimit: 10  # Keep last 10 revisions (default)
```

### 5. Add Health Checks

```yaml
spec:
  template:
    spec:
      containers:
      - name: myapp
        image: myapp:v2
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 15
          periodSeconds: 10
```

Health checks ensure:
- New pods are ready before old ones terminate
- Failed pods are automatically restarted
- Rollouts pause if pods fail health checks

### 6. Use Canary Deployments for High-Risk Updates

```bash
# Update image
kubectl set image deployment/myapp myapp=myapp:v2

# Immediately pause
kubectl rollout pause deployment/myapp

# Check status (some pods on v2, some on v1)
kubectl get pods -l app=myapp

# Monitor metrics, logs, errors
# If good:
kubectl rollout resume deployment/myapp

# If bad:
kubectl rollout undo deployment/myapp
```

---

## Additional Commands Reference

```bash
# View rollout status
kubectl rollout status deployment/<name>

# View rollout history
kubectl rollout history deployment/<name>

# View specific revision
kubectl rollout history deployment/<name> --revision=<number>

# Rollback to previous version
kubectl rollout undo deployment/<name>

# Rollback to specific revision
kubectl rollout undo deployment/<name> --to-revision=<number>

# Pause rollout
kubectl rollout pause deployment/<name>

# Resume rollout
kubectl rollout resume deployment/<name>

# Restart deployment (rolling restart)
kubectl rollout restart deployment/<name>

# Update image
kubectl set image deployment/<name> <container>=<image>

# Annotate deployment
kubectl annotate deployment/<name> kubernetes.io/change-cause="<message>"

# Scale deployment
kubectl scale deployment/<name> --replicas=<number>

# Edit deployment
kubectl edit deployment/<name>

# View deployment details
kubectl describe deployment/<name>

# View in YAML
kubectl get deployment/<name> -o yaml

# Watch pods during rollout
kubectl get pods -l <label-selector> -w
```

---

## Troubleshooting

**Issue**: Rollout stuck, not progressing

```bash
# Check rollout status
kubectl rollout status deployment/<name>

# Check pod status
kubectl get pods -l <label-selector>

# Describe deployment for events
kubectl describe deployment/<name>

# Common causes:
# - Image pull errors
# - Failed health checks
# - Insufficient resources
# - Configuration errors

# View pod logs
kubectl logs <pod-name>

# Describe failing pod
kubectl describe pod <pod-name>
```

**Issue**: Want to rollback but no previous revision

```bash
# Check history
kubectl rollout history deployment/<name>

# If no history, you may need to:
# 1. Edit deployment manually
# 2. Apply previous YAML manifest
# 3. Increase revisionHistoryLimit for future
```

**Issue**: Rollout completed but pods not working

```bash
# Check pod status
kubectl get pods -l <label-selector>

# View logs
kubectl logs -l <label-selector>

# Rollback immediately
kubectl rollout undo deployment/<name>
```

**Issue**: Want to speed up slow rollout

```bash
# Update strategy
kubectl patch deployment/<name> -p '{"spec":{"strategy":{"rollingUpdate":{"maxSurge":"100%","maxUnavailable":"50%"}}}}'

# Or edit directly
kubectl edit deployment/<name>
```

---

## Real-World Example: Production Web Application

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
  annotations:
    kubernetes.io/change-cause: "Deploy v3.2.1 with security patches"
spec:
  replicas: 10
  revisionHistoryLimit: 10
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 2
      maxUnavailable: 0
  selector:
    matchLabels:
      app: web-app
      tier: frontend
  template:
    metadata:
      labels:
        app: web-app
        tier: frontend
        version: v3.2.1
    spec:
      containers:
      - name: web-app
        image: myregistry/web-app:3.2.1
        ports:
        - containerPort: 8080
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
          failureThreshold: 3
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
          failureThreshold: 3
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: VERSION
          value: "3.2.1"
```

**This example demonstrates:**
- 10 replicas for high availability
- Conservative rollout (maxSurge: 2, maxUnavailable: 0)
- Proper health checks
- Resource requests and limits
- Version tracking via labels
- Change-cause annotation

---

## Next Steps

Now that you master deployment rollouts, proceed to:
- [Lab 30: Horizontal Pod Autoscaling](lab30-workload-hpa.md) - Automatically scale based on load
- [Lab 09: Health Checks and Probes](lab09-pod-health-probes.md) - Implement comprehensive health monitoring
- Explore Blue/Green and Canary deployment patterns
- Learn about GitOps and continuous deployment

## Further Reading

- [Kubernetes Deployments Documentation](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
- [Performing a Rolling Update](https://kubernetes.io/docs/tutorials/kubernetes-basics/update/update-intro/)
- [Deployment Strategies](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#strategy)
- [ReplicaSet Documentation](https://kubernetes.io/docs/concepts/workloads/controllers/replicaset/)

---

**Lab Created**: March 2026
**Compatible with**: Kubernetes 1.24+
