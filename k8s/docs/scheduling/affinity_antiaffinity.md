# Practical guide to affinity and anti-affinity in Kubernetes

## Introduction

**Affinity** and **anti-affinity** steer Pod placement using **labels** on nodes and Pods. **Node affinity** constrains or prefers nodes by label selectors. **Pod affinity** and **pod anti-affinity** express placement relative to Pods that already run (same node, rack, zone, and so on) via **`topologyKey`**. Together they support high availability (spread replicas), co-location (latency), and tenancy patterns.

On a multi-node cluster, you can reason about placement by picturing labeled workers (for example, `env=production` on one node and `env=staging` on another): node affinity pins a workload to a pool, while pod anti-affinity spreads replicas away from the same hostname or zone.

**Why it matters**

- **Affinity** can place Pods that communicate often on the same node or in the same failure domain for lower latency.
- **Anti-affinity** avoids putting multiple replicas of a critical app on one node or in one zone.

**When to use which**

- **Node affinity**: Target hardware, OS, environment, or other **node** labels.
- **Pod affinity**: Co-locate Pods that should run near each other (for example, app and cache).
- **Pod anti-affinity**: Spread replicas across nodes or zones for availability, or keep conflicting Pods apart.

Rules use the suffix **`IgnoredDuringExecution`**: if labels change **after** the Pod is scheduled, Kubernetes does **not** evict the Pod—only the initial scheduling decision is affected.

---

## Labels, selectors, operators, and topologyKey

**Labels** are the data plane for these rules: administrators or cloud integrations label nodes; Pod templates set Pod labels. Affinity blocks reference those labels with **`matchLabels`** and/or **`matchExpressions`**.

**Common operators** (node and Pod selectors): `In`, `NotIn`, `Exists`, `DoesNotExist`; node affinity also supports numeric **`Gt`** / **`Lt`** where applicable.

**`topologyKey`** (pod affinity / anti-affinity only) names a **node label** that defines the boundary of a domain. If two nodes share the same value for that label, they are in the same domain for that rule. Typical keys:

- `kubernetes.io/hostname` — per-node spread or co-location
- `topology.kubernetes.io/zone` or `topology.kubernetes.io/region` — broader failure domains

Every node in the relevant domain should carry the topology label; missing values can make domains look empty or uniform and yield surprising placement.

---

## Node affinity

Node affinity filters or scores nodes using **`nodeAffinity`** under **`spec.affinity`**.

- **Hard** requirements: **`requiredDuringSchedulingIgnoredDuringExecution`**. If no node matches at schedule time, the Pod stays **Pending** until something changes.
- **Soft** preferences: **`preferredDuringSchedulingIgnoredDuringExecution`** entries with a **`weight`**; the scheduler adds score for matching nodes but can still place the Pod elsewhere.

**`nodeSelectorTerms`**: multiple terms are **OR**’d; **`matchExpressions`** within one term are **AND**’d. For a single key, **`In`** with multiple **`values`** means “any of these values.”

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

**Example** (required affinity allowing **either** `production` **or** `staging`):

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: prod-or-staging-pod
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

**Example** (**preferred** rule: avoid nodes labeled `env=k8slearning`, weight `1`):

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: preferred-node-affinity-pod
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

**Structural outline** (required node affinity):

```yaml
affinity:
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
      - matchExpressions:
        - key: <key>
          operator: In
          values:
          - <value>
```

---

## Pod affinity

**Pod affinity** schedules a Pod onto a node (or into a topology domain) where Pods matching a **label selector** already run—useful for co-locating an app with a cache, agent, or peer service.

**Structural outline** (required pod affinity; note the **list** under `requiredDuringSchedulingIgnoredDuringExecution`):

```yaml
affinity:
  podAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
    - labelSelector:
        matchExpressions:
        - key: <key>
          operator: In
          values:
          - <value>
      topologyKey: <topologyKey>
```

**Example** (run on the same node as Pods labeled `app=cache`):

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-with-cache-affinity
spec:
  affinity:
    podAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchLabels:
            app: cache
        topologyKey: kubernetes.io/hostname
  containers:
  - name: nginx
    image: nginx
```

Pod affinity rules only match **existing** Pods (in the relevant namespace scope for the selector). If no Pod matches, a **required** rule leaves the new Pod **Pending**.

---

## Pod anti-affinity

**Pod anti-affinity** prevents (or discourages) scheduling near Pods that match a label selector. Use **`topologyKey`** to define the **failure domain**—commonly `kubernetes.io/hostname` for “not on the same node,” or zone labels for broader spread.

For pod-to-pod rules to work, **already-running** Pods must carry labels the selector can match.

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

**Structural outline** (required pod anti-affinity):

```yaml
affinity:
  podAntiAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
    - labelSelector:
        matchExpressions:
        - key: <key>
          operator: In
          values:
          - <value>
      topologyKey: <topologyKey>
```

Use **preferred** anti-affinity when strict spread is desirable but not mandatory; **required** rules can prevent scheduling entirely if the cluster is too small or labels do not allow enough domains.

---

## Comparison tables and use cases

### Node vs pod affinity vs pod anti-affinity

| Mechanism | What it matches | Typical goal |
|-----------|-----------------|--------------|
| **Node affinity** | **Node** labels | Run on SSD/GPU pools, regions, environments |
| **Pod affinity** | **Pod** labels + `topologyKey` | Co-locate related Pods in the same node/zone |
| **Pod anti-affinity** | **Pod** labels + `topologyKey` | Spread replicas or separate noisy neighbors |

### Scenario cheat sheet

| Scenario | Affinity type | Idea |
|----------|---------------|------|
| Schedule Pods on a specific node pool | Node affinity | Node labels (e.g. `env=production`, `disktype=ssd`) |
| Run Pods together | Pod affinity | Same topology domain as Pods with chosen labels |
| Keep replicas apart | Pod anti-affinity | Same `topologyKey`, different domain values (e.g. different hostnames) |
| Spread across zones | Pod anti-affinity (or topology spread constraints) | `topologyKey` such as `topology.kubernetes.io/zone` |

### nodeSelector vs nodeAffinity

Both steer Pods using node labels; node affinity is strictly more expressive.

| Feature | nodeSelector | nodeAffinity |
|--------|--------------|--------------|
| **Definition** | Exact `key: value` match on the node | Label selectors with operators and multiple terms |
| **Operators** | Equality only | `In`, `NotIn`, `Exists`, `DoesNotExist`, `Gt`, `Lt` (where supported) |
| **Hard vs soft** | Always hard | Required vs preferred (`preferredDuringSchedulingIgnoredDuringExecution`) |
| **Complexity** | Minimal | Higher; validate on real clusters |
| **When to use** | Simple pools (`disktype=ssd`) | OR of values, soft preferences, exclusion rules |

---

## Best practices

- Start with the **smallest** constraint that meets the requirement (often `nodeSelector` or a single required node affinity term).
- Prefer **preferred** rules before **required** ones when business logic allows, to avoid unnecessary **Pending** Pods.
- Ensure **topology labels** exist and are consistent on nodes before relying on zone- or rack-level rules.
- **Label Pods** that participate in pod affinity/anti-affinity so selectors have stable targets.
- Validate behavior under failure (loss of a single node or zone) and under combined constraints (**taints/tolerations**, **topology spread constraints**, **PriorityClass**).

---

## Validation and troubleshooting

- **Pending Pods**: `kubectl describe pod <name>` shows scheduler messages (unsatisfied affinity, taints, resources).
- **Topology**: Missing `topologyKey` labels on nodes make domains misleading.
- **Interaction effects**: Affinity combines with **taints/tolerations**, **nodeSelector**, **topology spread constraints**, and **PriorityClass**—conflicting rules keep Pods unschedulable.

Operational checks such as `kubectl get pods -o wide`, inspecting events, and verifying node labels belong in hands-on labs, not in this conceptual guide.

---

## Conclusion

Affinity and anti-affinity encode **where** Pods may run relative to nodes and peer Pods. **Node affinity** targets node labels; **pod affinity** and **pod anti-affinity** express co-location or separation across a **topology** (hostname, zone, region). Used together, they help balance performance, isolation, and high availability.

---

## Hands-On Labs

Practice these concepts with guided lab exercises:

| Lab | Description |
|-----|-------------|
| [Lab 18: Pod Scheduling with Node and Pod Affinity](../../labmanuals/lab18-sched-affinity-antiaffinity.md) | Node and Pod affinity and anti-affinity, topology keys, and scheduling verification on a multi-node cluster. |
