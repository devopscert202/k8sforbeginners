# Kubernetes Deployment rollouts, revisions, and rollbacks

## Objective (conceptual)
Deployments manage replicated application Pods and change them through **rolling updates**: new Pods are brought up gradually while old ones terminate, bounded by `maxSurge` and `maxUnavailable`. Each template change creates a new **ReplicaSet** and a new **revision** in rollout history. Operators can **pause**, **resume**, **inspect history**, and **roll back** when a release misbehaves—without rebuilding images if the previous image tag is still available in the registry.

## How rolling updates relate to ReplicaSets
- The Deployment controller owns one or more ReplicaSets keyed by the Pod template hash.
- The **active** ReplicaSet matches `spec.template`; older ReplicaSets may retain scaled-to-zero replicas for rollback.
- A **Service** selecting the same labels continues to route to Ready endpoints as the new Pods pass readiness checks.

## Revisions and change tracking
- `kubectl rollout history deployment/<name>` shows revision numbers and, if set, the **change-cause** annotation (`kubernetes.io/change-cause`) documenting why a rollout happened.
- `kubectl rollout status deployment/<name>` streams progress until the new ReplicaSet is complete or a deadline is hit.

## Changing the running version
- **Declarative**: edit `spec.template` (often `image`) and apply the Deployment manifest.
- **Imperative**: `kubectl set image deployment/<name> <container>=<image:tag>` updates the template and starts a rollout.
- **Record / annotations**: recording via `--record` on `set image` is deprecated; prefer explicit `change-cause` annotations in Git or CI.

## Rollback behavior
- `kubectl rollout undo deployment/<name>` moves the Deployment back to the previous revision.
- `kubectl rollout undo deployment/<name> --to-revision=<N>` selects a specific historical revision.
- Rollback restores the **previous Pod template** (including image and env); it does not magically recover corrupted external state.

## Illustrative Deployment and Service

**Deployment** (two replicas, simple HTTP image):

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
        image: example.registry/apache:v1
        ports:
        - containerPort: 80
```

**Service** (example `NodePort` for lab-style clusters):

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

Updating `spec.template.spec.containers[0].image` (or using `kubectl set image`) triggers a new rollout; the Service continues to match `app: apache` throughout.

## Operational commands (reference)
- `kubectl get deploy,rs,pods`
- `kubectl describe deployment <name>`
- `kubectl rollout history deployment/<name>`
- `kubectl rollout pause|resume deployment/<name>`

---

## Hands-On Labs

Practice these concepts with guided lab exercises:

| Lab | Description |
|-----|-------------|
| [Lab 22: Kubernetes Deployment Strategies](../../labmanuals/lab22-deploy-deployment-strategies.md) | Deployments, Services, scaling, and rolling updates |
| [Lab 23: Deployment Strategies and Rollouts](../../labmanuals/lab23-deploy-deployment-rollouts.md) | Rollouts, history, rollback, and rollout controls |
