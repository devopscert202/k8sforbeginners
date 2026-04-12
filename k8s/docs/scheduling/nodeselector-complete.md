# Complete guide to nodeSelector in Kubernetes

## Introduction

When deploying applications in Kubernetes, it is often necessary to control the placement of pods on specific nodes to optimize performance, ensure resource allocation, or maintain compliance. Kubernetes provides **`nodeSelector`** as a simple mechanism for pod placement, along with the more advanced **`nodeAffinity`** feature for complex scenarios.

This guide covers conceptual behavior, representative manifests, comparison with node affinity, and troubleshooting signals.

---

## What is nodeSelector?

**nodeSelector** is a map of required **node labels**. The scheduler only places the pod on nodes whose labels contain **all** specified key/value pairs.

### Why use nodeSelector?

- **Workload isolation**: Run workloads only on designated nodes (e.g. GPU, SSD, environment pools).
- **Resource optimization**: Steer heavy jobs to larger instance types via labels.
- **Compliance**: Target nodes in approved regions or hardware profiles.
- **Simplicity**: Minimal YAML and mental model.

### How it works

1. Nodes are labeled with `key=value` pairs (by admins, installers, or cloud integrations).
2. The pod spec’s `nodeSelector` lists required labels.
3. The scheduler assigns the pod only to matching nodes (subject to other constraints: taints, resources, affinity, etc.).

Labels are managed with `kubectl label` and inspected with `kubectl get nodes --show-labels` (and similarly for pods).

---

## Examples

### Basic nodeSelector

Pod that requires `env=production` on the node:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: simple-node-selector
spec:
  nodeSelector:
    env: production
  containers:
  - name: nginx
    image: nginx
```

### Multiple labels (AND)

All listed labels must be present on the node:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: multi-label-selector
spec:
  nodeSelector:
    env: production
    disktype: ssd
  containers:
  - name: nginx
    image: nginx
```

### Environment-based separation

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx-labels
  labels:
    env: test
spec:
  containers:
  - name: nginx
    image: nginx
    imagePullPolicy: IfNotPresent
  nodeSelector:
    env: k8slearning
```

---

## Node affinity (advanced scheduling)

**nodeAffinity** supports operators, multiple values, soft preferences, and OR of selector terms—capabilities nodeSelector does not have.

### Required node affinity

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: advanced-node-affinity
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: env
            operator: In
            values:
            - production
            - staging
  containers:
  - name: nginx
    image: nginx
```

### Preferred (soft) affinity with NotIn

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: with-node-affinity
spec:
  affinity:
    nodeAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 1
        preference:
          matchExpressions:
          - key: env
            operator: NotIn
            values:
            - k8slearning
  containers:
  - name: httpd
    image: docker.io/httpd
```

---

## Comparison: nodeSelector vs nodeAffinity

| Feature | nodeSelector | nodeAffinity |
|---------|-------------|--------------|
| **Definition** | Required exact label matches | Selector expressions with operators |
| **Capabilities** | Equality only | `In`, `NotIn`, `Exists`, `DoesNotExist`, `Gt`, `Lt` (where supported) |
| **Complexity** | Low | Higher |
| **Hard vs soft** | Always hard | Required vs preferred |
| **Multiple values per key** | No (duplicate keys impossible in a map) | Yes (`In` with a list) |
| **Use case** | Simple pools | OR conditions, exclusions, weighted preferences |

### When to use which?

**Use nodeSelector** for straightforward “must run on pool X” rules.

**Use nodeAffinity** when you need OR of environments, soft preferences, exclusion (`NotIn`), or richer expressions.

---

## Troubleshooting

Typical signals when placement fails:

- **`kubectl describe pod <pod-name>`** → Events such as `didn't match node selector`, `had taint`, or insufficient CPU/memory.
- **`kubectl get nodes --show-labels`** → Confirm required labels exist on expected nodes.
- **Taints/tolerations** and **affinity/anti-affinity** can override an otherwise matching nodeSelector.

**Pending pod**: no matching labels, cordoned nodes, resource shortage, or conflicting rules.

**Unexpected node**: multiple nodes share the same label, or a softer rule (preferred affinity) was used instead of nodeSelector.

---

## Best practices

1. Use clear, documented label keys (`env`, `tier`, `disktype`, `instance-type`).
2. Prefer the **simplest** constraint that satisfies the requirement.
3. Combine with **taints/tolerations** for dedicated pools when appropriate.
4. Audit stale labels periodically.

---

## Summary

- **nodeSelector** is the minimal API for “run only on labeled nodes.”
- **nodeAffinity** extends that with operators, OR terms, and preferences.
- **Labels** are the shared foundation; scheduling always considers the full constraint set.

---

## Hands-On Labs

Practice these concepts with guided lab exercises:

| Lab | Description |
|-----|-------------|
| [Lab 17: Pod Scheduling with NodeSelector](../../labmanuals/lab17-sched-nodeselector.md) | Hands-on scheduling with node labels and selectors |
