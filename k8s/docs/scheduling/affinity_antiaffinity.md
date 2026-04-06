# Practical guide to affinity and anti-affinity in Kubernetes

## Introduction
**Affinity** and **anti-affinity** steer Pod placement using **labels** on nodes and Pods. **Node affinity** constrains or prefers nodes by label selectors. **Pod affinity / anti-affinity** express placement relative to Pods that already run (same node, rack, zone, etc.) via `topologyKey`. Together they support high availability (spread replicas), co-location (latency), and tenancy patterns.

**Labels** are the data plane for these rules: nodes are labeled by administrators or cloud integrations; Pods inherit labels from templates. Affinity rules reference those labels with operators such as `In`, `NotIn`, `Exists`, and `DoesNotExist`.

---

## Node affinity
Node affinity filters or scores nodes using `nodeAffinity` under `spec.affinity`. **Hard** requirements use `requiredDuringSchedulingIgnoredDuringExecution`; **soft** preferences use `preferredDuringSchedulingIgnoredDuringExecution` with weights.

**Example** (Pod must land on nodes labeled `env=production`):

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: production-pod
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
  containers:
  - name: nginx
    image: nginx
```

- **`requiredDuringSchedulingIgnoredDuringExecution`**: If no node matches at schedule time, the Pod stays **Pending** (until something changes).
- **`nodeSelectorTerms`**: OR across terms; expressions within a term are ANDed.

---

## Pod anti-affinity
Pod anti-affinity prevents (or discourages) scheduling near Pods that match a label selector. `topologyKey` defines the **failure domain**—commonly `kubernetes.io/hostname` for “not on the same node,” or zone labels for broader spread.

**Example** (do not schedule on the same node as Pods labeled `env=staging`):

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: anti-affinity-pod-2
spec:
  affinity:
    podAntiAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchExpressions:
          - key: "env"
            operator: In
            values:
            - staging
        topologyKey: kubernetes.io/hostname
  containers:
  - name: nginx
    image: nginx
```

Use **preferred** anti-affinity when strict spread is desirable but not mandatory; required rules can deadlock scheduling if the cluster is too small.

---

## Validation and troubleshooting
- **Pending Pods**: `kubectl describe pod <name>` surfaces scheduler messages (unsatisfied affinity, taints, resources).
- **Topology**: Ensure `topologyKey` labels exist on nodes; missing labels make domains look empty or uniform.
- **Interaction effects**: Affinity combines with **taints/tolerations**, **nodeSelector**, **topology spread constraints**, and **PriorityClass**—conflicting rules keep Pods unschedulable.

---

## NodeSelector vs nodeAffinity

Both steer Pods using node labels; nodeAffinity is strictly more expressive.

| Feature | nodeSelector | nodeAffinity |
|--------|--------------|--------------|
| **Definition** | Exact `key: value` match required on the node | Label selectors with operators and multiple terms |
| **Operators** | Equality only | `In`, `NotIn`, `Exists`, `DoesNotExist`, `Gt`, `Lt` (where supported) |
| **Hard vs soft** | Always hard | Required vs preferred (`preferredDuringSchedulingIgnoredDuringExecution`) |
| **Complexity** | Minimal | Higher; needs careful testing |
| **When to use** | Simple pools (`disktype=ssd`) | OR of values, soft preferences, exclusion rules |

---

## Conclusion
Affinity and anti-affinity let you encode **where** Pods may run relative to nodes and peer Pods. Start with the smallest rule that meets the requirement (often `nodeSelector` or a single required node affinity term), add **preferred** rules before **required** ones to avoid unnecessary scheduling failures, and always verify behavior under failure (single node or single zone loss).

---

## Hands-On Labs

Practice these concepts with guided lab exercises:

| Lab | Description |
|-----|-------------|
| [Lab 18: Pod Scheduling with Node and Pod Affinity](../../labmanuals/lab18-sched-affinity-antiaffinity.md) | Guided exercises for node and Pod affinity rules |
