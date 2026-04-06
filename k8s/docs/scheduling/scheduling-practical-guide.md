# Kubernetes Scheduling: Concepts and Practice

This guide explains how the Kubernetes scheduler places Pods on nodes, from core mechanics (including topics that often appear on the CKA exam) through advanced tuning, resource accounting, and preemption. Use it as a map: detailed mechanics for **nodeSelector**, **affinity**, **taints/tolerations**, and **namespace quotas** live in the linked deep-dives below.

---

## Scheduler fundamentals

The **kube-scheduler** is a control plane component that watches for Pods with no `spec.nodeName`, evaluates which nodes can run them, ranks the feasible nodes, and binds the Pod to the chosen node.

**Responsibilities**

- Find schedulable Pods (no node assigned yet, not excluded by gates or other controllers).
- Match each Pod against cluster state: node capacity, labels, taints, affinity rules, and configured plugins.
- Select a node and record the assignment (bind).

**Key inputs**

- The Pod spec: resource requests/limits, affinity, tolerations, topology spread, priority, runtime class, and scheduler name.
- Cluster state: nodes (Ready, allocatable resources, labels, taints), existing workloads, and policy objects (ResourceQuota, LimitRange, PriorityClass).

### Scheduling framework (Filter and Score)

Scheduling is implemented as a **plugin pipeline**. For exams and day-to-day reasoning, the most important phases are **Filter** (feasibility: node must fit) and **Score** (preference: best node among those that fit). The full sequence is:

1. **PreFilter** — Preconditions (e.g. whether scheduling is allowed, some affinity checks).
2. **Filter** — Remove nodes that cannot run the Pod (resources, node selector/affinity, taints, pod affinity, volume topology, etc.).
3. **Score** — Rank remaining nodes (resource fit, spread, affinity preferences, custom plugins).
4. **Reserve** — Reserve resources on the chosen node (coordination with storage/volume plugins where applicable).
5. **Permit** — Optional wait/approve/deny hooks.
6. **Bind** — Persist the Pod–node assignment.

If no node passes Filter, the Pod stays **Pending** with events explaining the failure (for example insufficient CPU, unmatched taint, or anti-affinity).

---

## Node selection and binding

**Node selection** applies Filter/Score using, among other things:

- **Node conditions** — Typically the node must be Ready and not marked unschedulable.
- **Allocatable resources** — Sum of existing Pod requests on the node plus this Pod’s **requests** must fit allocatable CPU/memory (and extended resources if requested).
- **Labels and affinity** — Required and preferred node rules.
- **Taints and tolerations** — Taints evict or block Pods unless tolerated.
- **Inter-pod affinity / anti-affinity** — Co-location or separation from other Pods.
- **Topology spread** — Even distribution across domains such as zone or hostname.

**Binding** is the final step: the scheduler sets the Pod’s node (kubelet then starts containers on that node). Admission controllers and ResourceQuota/LimitRange can still reject or mutate the Pod before or during admission; the scheduler assumes quotas and limits that affect feasibility are enforced consistently with the API.

---

## Scheduling policies (overview)

These mechanisms **compose**: a node can be eligible by resources but still rejected by a taint or affinity rule.

| Mechanism | Role |
|-----------|------|
| **nodeSelector** | Simple required match on node labels. |
| **Node affinity** | Required and/or preferred rules on node labels (richer than nodeSelector). |
| **Pod affinity / anti-affinity** | Place Pods near or away from Pods with given labels, optionally scoped by topology. |
| **Taints and tolerations** | Nodes repel Pods unless the Pod tolerates the taint (`NoSchedule`, `PreferNoSchedule`, `NoExecute`). |

**Deep dives**

- [NodeSelector](nodeselector-complete.md)
- [Node and Pod affinity / anti-affinity](affinity_antiaffinity.md)
- [Taints and tolerations](taints-tolerations-complete.md)

---

## Illustrative combined constraints

The following Pod assumes a node is labeled `disktype=ssd` and tainted `key=value:NoSchedule`. A matching **toleration** allows the node to be considered; **required node affinity** enforces the SSD label. **Resource requests** participate in feasibility during Filter.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: scheduling-demo
spec:
  tolerations:
  - key: "key"
    operator: "Equal"
    value: "value"
    effect: "NoSchedule"
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: "disktype"
            operator: "In"
            values:
            - "ssd"
  containers:
  - name: nginx
    image: nginx
    resources:
      requests:
        memory: "64Mi"
        cpu: "250m"
```

If no node satisfies taints, affinity, and free resources, the Pod remains **Pending** until cluster state changes.

---

## Advanced scheduler configuration

### Performance tuning

On large or high-churn clusters, scheduling latency and throughput depend on scheduler **parallelism**, how many nodes are **scored** (e.g. `percentageOfNodesToScore`), and API/cache behavior. Tune the scheduler through its **KubeSchedulerConfiguration** (mounted into the `kube-scheduler` static Pod or equivalent control plane deployment), not by treating the scheduler as an arbitrary app Deployment.

Example (fields vary slightly by Kubernetes version; confirm against your cluster version’s API):

```yaml
apiVersion: kubescheduler.config.k8s.io/v1
kind: KubeSchedulerConfiguration
parallelism: 16
profiles:
  - schedulerName: default-scheduler
```

### Scheduling profiles

**Profiles** let you enable, disable, or reorder **plugins** per scheduler name. Pods select a scheduler with `spec.schedulerName` (default is `default-scheduler`).

```yaml
apiVersion: kubescheduler.config.k8s.io/v1
kind: KubeSchedulerConfiguration
profiles:
- schedulerName: "default-scheduler"
  plugins:
    score:
      enabled:
      - name: NodeResourcesFit
- schedulerName: "gpu-scheduler"
  plugins:
    filter:
      enabled:
      - name: NodeResourcesFit
    score:
      enabled:
      - name: NodeAffinity
```

### NUMA and topology-aware placement

For latency-sensitive or bandwidth-heavy workloads, **topology manager** policies on the **kubelet** (`topologyManagerPolicy`, and related scope/policy options) influence how CPU/memory/devices are aligned on NUMA nodes. This is node-local coordination with the scheduler and device plugins, not a replacement for Pod-level affinity or spread.

```yaml
apiVersion: kubelet.config.k8s.io/v1
kind: KubeletConfiguration
topologyManagerPolicy: "restricted"
```

### Pod topology spread constraints

**Topology spread** balances Pods across failure domains (for example `topology.kubernetes.io/zone` or `kubernetes.io/hostname`) using `maxSkew`, `topologyKey`, and `whenUnsatisfiable` (`DoNotSchedule` or `ScheduleAnyway`).

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: spread-demo
spec:
  replicas: 6
  selector:
    matchLabels:
      app: demo
  template:
    metadata:
      labels:
        app: demo
    spec:
      topologySpreadConstraints:
      - maxSkew: 1
        topologyKey: topology.kubernetes.io/zone
        whenUnsatisfiable: DoNotSchedule
        labelSelector:
          matchLabels:
            app: demo
      containers:
      - name: app
        image: nginx
```

---

## Resource management and scheduling

### Requests, limits, and pod overhead

- **Requests** — Used by the scheduler for feasibility and by the kubelet for allocation. They represent the minimum resources you expect the workload to need.
- **Limits** — Cap runtime usage (enforced by the container runtime/C groups where applicable). They do **not** determine whether a node is “big enough” for scheduling; **requests** do.
- **Pod overhead** — For some runtimes (sandboxed runtimes, etc.), **RuntimeClass** can declare fixed overhead so scheduling accounts for extra CPU/memory beyond container sums.

```yaml
apiVersion: node.k8s.io/v1
kind: RuntimeClass
metadata:
  name: overhead-runtime
handler: runsc
overhead:
  podFixed:
    cpu: "100m"
    memory: "50Mi"
```

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: resource-demo
spec:
  containers:
  - name: nginx
    image: nginx
    resources:
      requests:
        memory: "256Mi"
        cpu: "500m"
      limits:
        memory: "512Mi"
        cpu: "1"
```

### Quotas and limit ranges

ResourceQuotas let administrators cap the total CPU, memory, and object counts that a namespace can consume. They enforce fair sharing in multi-tenant clusters by rejecting requests that would exceed the quota. Quotas don't affect scheduling directly—the scheduler still fits Pods using **requests** against node allocatable—but they ensure namespaces don't consume more than their share at admission time.

For detailed configuration, YAML examples, and use cases, see [Resource Quotas and Limits](../workloads/resourcequota.md).

**LimitRange** sets defaults, minima, and maxima for individual containers or Pods in a namespace. It affects whether Pods can be **created**; the scheduler still primarily uses **requests** vs node allocatable for fit.

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: container-limits
  namespace: my-namespace
spec:
  limits:
  - max:
      memory: "1Gi"
      cpu: "1"
    min:
      memory: "128Mi"
      cpu: "200m"
    type: Container
```

---

## Priority and preemption

**PriorityClass** assigns an integer **priority** to Pods. When a high-priority Pod cannot schedule, the scheduler may **preempt** (evict) lower-priority Pods to free resources, subject to PDBs and other safety constraints. Set `globalDefault: true` on one class only if you want a default priority for Pods without an explicit class.

```yaml
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: high-priority
value: 1000
globalDefault: false
description: "Priority for critical workloads"
---
apiVersion: v1
kind: Pod
metadata:
  name: high-priority-pod
spec:
  priorityClassName: high-priority
  containers:
  - name: nginx
    image: nginx
```

---

## Summary reference

| Topic | Role |
|-------|------|
| **Scheduler** | Assigns Pending Pods to nodes using plugins (Filter/Score central). |
| **Requests** | Drive feasibility; limits cap runtime use. |
| **nodeSelector / affinity** | Required and preferred placement by labels (and topology for pod affinity). |
| **Taints / tolerations** | Node repulsion and dedicated pools. |
| **Topology spread** | Balance replicas across domains. |
| **Profiles** | Customize plugin sets per `schedulerName`. |
| **Quota / LimitRange** | Namespace policy; see linked workload doc. |
| **Priority** | Ordering and preemption under contention. |

---

## Common use cases

1. **High availability** — Spread across zones or hosts (topology spread, anti-affinity).
2. **Specialized hardware** — Node labels + affinity or taints for GPU/SSD pools.
3. **Isolation** — Taints for control plane or dedicated tenants; tolerations only where intended.
4. **Fair sharing** — Requests for predictable packing; quotas per namespace.
5. **Compliance** — Required node affinity to allowed regions or environments.

---

## Hands-On Labs

| Lab | Description |
|-----|-------------|
| [Lab 17: Pod Scheduling with NodeSelector](../../labmanuals/lab17-sched-nodeselector.md) | Node labels and nodeSelector-style scheduling |
| [Lab 18: Pod Scheduling with Node and Pod Affinity](../../labmanuals/lab18-sched-affinity-antiaffinity.md) | Node and Pod affinity / anti-affinity |
| [Lab 19: Pod Scheduling with PriorityClass](../../labmanuals/lab19-sched-priorityclass.md) | Pod priority and preemption |
| [Lab 20: Pod Scheduling with Taints and Tolerations](../../labmanuals/lab20-sched-taints-tolerations.md) | Taints, tolerations, and dedicated nodes |

Together, these labs reinforce the behaviors described in this guide for both exam preparation and production clusters.
