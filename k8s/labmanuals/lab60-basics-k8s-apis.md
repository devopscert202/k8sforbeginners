# Lab 60: Kubernetes API Discovery and Exploration

## Overview

Every object in Kubernetes — Pods, Deployments, Services, ConfigMaps, Custom Resources — is managed through the **Kubernetes API Server**. Before you can write YAML manifests, you need to know **which API group** a resource belongs to, **what version** to use, and **what fields** are available.

This lab teaches you how to discover and explore the Kubernetes API using built-in `kubectl` commands. You will learn to find the correct `apiVersion` for any resource, list all available resources and their capabilities, inspect object schemas with `kubectl explain`, and use output formatting options (`-o wide`, `-o yaml`, `-o json`, `-o jsonpath`) to extract exactly the information you need.

## Prerequisites

- A running Kubernetes cluster (Minikube, Kind, or any K8s cluster)
- `kubectl` CLI tool installed and configured
- Completion of [Lab 03: kubectl Essentials](lab03-basics-kubectl-essentials.md) (recommended)

## Learning Objectives

By the end of this lab, you will be able to:

- Use `kubectl api-versions` to list all API group/versions in a cluster
- Use `kubectl api-resources` to discover resources, short names, and verbs
- Filter and search resources by group, kind, or namespace scope
- Use `kubectl explain` to inspect object schemas and field documentation
- Determine the correct `apiVersion` for any resource
- Use output formats (`-o wide`, `-o yaml`, `-o json`, `-o jsonpath`, `-o custom-columns`) effectively
- Query raw API endpoints with `kubectl get --raw`

---

## Concepts

### API Structure

Every Kubernetes resource has three identity components:

| Component | Example | Purpose |
|-----------|---------|---------|
| **API Group** | `apps`, `batch`, `networking.k8s.io` | Logical grouping of related resources |
| **Version** | `v1`, `v1beta1`, `v1alpha1` | Stability level of the API |
| **Kind** | `Deployment`, `CronJob`, `Ingress` | The specific object type |

These combine into the `apiVersion` field in every manifest:

```yaml
apiVersion: apps/v1        # group/version
kind: Deployment            # kind
```

Core resources (Pod, Service, ConfigMap, Secret, Namespace) live in the **core group** with no prefix — their `apiVersion` is simply `v1`.

### API Stability Levels

| Level | Example | Meaning |
|-------|---------|---------|
| **GA (stable)** | `v1`, `apps/v1` | Production-ready, backward-compatible |
| **Beta** | `v1beta1` | Feature-complete but may change between releases |
| **Alpha** | `v1alpha1` | Experimental, may be removed without notice |

**Rule of thumb**: Always use the highest stable version available for production manifests.

---

## Exercise 1: Discovering API Versions

### Step 1: List all API versions

```bash
kubectl api-versions
```

Expected output (abbreviated):

```
admissionregistration.k8s.io/v1
apiextensions.k8s.io/v1
apps/v1
autoscaling/v1
autoscaling/v2
batch/v1
certificates.k8s.io/v1
coordination.k8s.io/v1
discovery.k8s.io/v1
networking.k8s.io/v1
node.k8s.io/v1
policy/v1
rbac.authorization.k8s.io/v1
scheduling.k8s.io/v1
storage.k8s.io/v1
v1
```

### Step 2: Count how many API versions your cluster serves

```bash
kubectl api-versions | wc -l
```

### Step 3: Find a specific group

```bash
kubectl api-versions | grep networking
```

Expected: `networking.k8s.io/v1`

### Step 4: Check for beta or alpha APIs

```bash
kubectl api-versions | grep beta
kubectl api-versions | grep alpha
```

These indicate features that may not be fully stable in your cluster.

---

## Exercise 2: Exploring API Resources

### Step 1: List all resources

```bash
kubectl api-resources
```

This shows every resource type the cluster knows about, including CRDs.

### Step 2: Use wide output for full details

```bash
kubectl api-resources -o wide
```

Key columns:
- **NAME**: Resource name (used in `kubectl get <name>`)
- **SHORTNAMES**: Abbreviations (e.g., `po` for pods, `deploy` for deployments)
- **APIVERSION**: The API group/version
- **NAMESPACED**: `true` if resource lives in a namespace, `false` if cluster-scoped
- **KIND**: The object type used in YAML manifests
- **VERBS**: Supported operations (`create`, `delete`, `get`, `list`, `patch`, `update`, `watch`)

### Step 3: Filter by API group

```bash
kubectl api-resources --api-group=apps
```

Expected:

```
NAME                  SHORTNAMES   APIVERSION   NAMESPACED   KIND
controllerrevisions                apps/v1      true         ControllerRevision
daemonsets            ds           apps/v1      true         DaemonSet
deployments           deploy       apps/v1      true         Deployment
replicasets           rs           apps/v1      true         ReplicaSet
statefulsets          sts          apps/v1      true         StatefulSet
```

### Step 4: Filter by other API groups

```bash
kubectl api-resources --api-group=batch
kubectl api-resources --api-group=networking.k8s.io
kubectl api-resources --api-group=rbac.authorization.k8s.io
kubectl api-resources --api-group=storage.k8s.io
```

### Step 5: List only namespaced resources

```bash
kubectl api-resources --namespaced=true
```

### Step 6: List only cluster-scoped resources

```bash
kubectl api-resources --namespaced=false
```

These include Nodes, Namespaces, PersistentVolumes, ClusterRoles, etc.

### Step 7: Search for a specific resource

```bash
kubectl api-resources | grep -i deploy
kubectl api-resources | grep -i ingress
kubectl api-resources | grep -i network
```

### Step 8: Find short names

```bash
kubectl api-resources | grep -E "^NAME|deploy|svc|po |ns |no "
```

Common short names:

| Short | Full |
|-------|------|
| `po` | pods |
| `svc` | services |
| `deploy` | deployments |
| `ds` | daemonsets |
| `sts` | statefulsets |
| `rs` | replicasets |
| `ns` | namespaces |
| `no` | nodes |
| `pv` | persistentvolumes |
| `pvc` | persistentvolumeclaims |
| `cm` | configmaps |
| `sa` | serviceaccounts |
| `ep` | endpoints |
| `ing` | ingresses |
| `netpol` | networkpolicies |
| `crd` | customresourcedefinitions |

---

## Exercise 3: Using `kubectl explain`

### Step 1: Get top-level documentation for a resource

```bash
kubectl explain pod
```

This shows the resource description, API version, and top-level fields.

### Step 2: Drill into nested fields

```bash
kubectl explain pod.spec
kubectl explain pod.spec.containers
kubectl explain pod.spec.containers.resources
kubectl explain pod.spec.containers.resources.limits
```

### Step 3: Explore Deployment fields

```bash
kubectl explain deployment
kubectl explain deployment.spec
kubectl explain deployment.spec.strategy
kubectl explain deployment.spec.strategy.rollingUpdate
```

### Step 4: Check Service fields

```bash
kubectl explain service.spec
kubectl explain service.spec.type
kubectl explain service.spec.ports
```

### Step 5: Use recursive output

Show the full field tree for a resource:

```bash
kubectl explain pod.spec --recursive | head -50
```

This is useful for quickly finding the exact field path you need.

### Step 6: Check for deprecated fields

```bash
kubectl explain pod.spec.containers.securityContext
```

Look for `DEPRECATED` markers in the field descriptions.

### Step 7: Explore CRD fields (if any CRDs exist)

```bash
kubectl get crd
kubectl explain <crd-kind>
```

---

## Exercise 4: Output Formatting Options

### Step 1: Create sample resources for exploration

```bash
kubectl create deployment api-demo --image=nginx:1.25-alpine --replicas=3
kubectl expose deployment api-demo --port=80 --target-port=80 --type=ClusterIP
```

### Step 2: Default output

```bash
kubectl get pods
kubectl get deployments
kubectl get services
```

### Step 3: Wide output (`-o wide`)

```bash
kubectl get pods -o wide
```

Shows additional columns: Node, IP, Nominated Node, Readiness Gates.

```bash
kubectl get nodes -o wide
```

Shows: Internal IP, External IP, OS Image, Kernel Version, Container Runtime.

### Step 4: YAML output (`-o yaml`)

```bash
kubectl get deployment api-demo -o yaml
```

This is the full object as stored in etcd. Key sections:
- `apiVersion` and `kind` at the top
- `metadata` (name, namespace, labels, annotations, uid, resourceVersion)
- `spec` (desired state)
- `status` (current state, managed by controllers)

### Step 5: JSON output (`-o json`)

```bash
kubectl get deployment api-demo -o json
```

Same data as YAML, in JSON format — useful for piping to `jq`.

### Step 6: JSONPath — extract specific fields

```bash
kubectl get pods -o jsonpath='{.items[*].metadata.name}'
```

More examples:

```bash
kubectl get pods -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.phase}{"\n"}{end}'

kubectl get nodes -o jsonpath='{.items[*].status.addresses[?(@.type=="InternalIP")].address}'

kubectl get deployment api-demo -o jsonpath='{.spec.replicas}'
```

### Step 7: Custom columns

```bash
kubectl get pods -o custom-columns=NAME:.metadata.name,STATUS:.status.phase,IP:.status.podIP,NODE:.spec.nodeName
```

### Step 8: Name-only output

```bash
kubectl get pods -o name
```

Output: `pod/api-demo-xxxxx`, useful for scripting.

---

## Exercise 5: Raw API Discovery

### Step 1: Query the core API

```bash
kubectl get --raw /api
```

This returns the versions served by the core group (typically just `v1`).

### Step 2: Query all API groups

```bash
kubectl get --raw /apis | python3 -m json.tool | head -40
```

Or with `jq` if available:

```bash
kubectl get --raw /apis | jq '.groups[].name'
```

### Step 3: Query a specific API group

```bash
kubectl get --raw /apis/apps
kubectl get --raw /apis/apps/v1
```

### Step 4: List resources in an API group

```bash
kubectl get --raw /apis/apps/v1 | python3 -m json.tool | grep '"name"' | head -20
```

### Step 5: Query APIService objects

```bash
kubectl get apiservices
```

These represent APIs registered via the aggregation layer (e.g., `metrics.k8s.io` from Metrics Server).

```bash
kubectl get apiservices | grep -v Local
```

This filters to show only non-local (aggregated) API services.

---

## Exercise 6: Putting It All Together

### Scenario: Find the correct `apiVersion` for a HorizontalPodAutoscaler

```bash
kubectl api-resources | grep -i horizontalpodautoscaler
```

You might see both `autoscaling/v1` and `autoscaling/v2`. Check which is preferred:

```bash
kubectl api-versions | grep autoscaling
```

Use `v2` for the full feature set (multiple metrics, behavior configuration).

### Scenario: Discover what verbs are available for NetworkPolicies

```bash
kubectl api-resources -o wide | grep -i networkpolic
```

The `VERBS` column shows what operations are supported.

### Scenario: Find all cluster-scoped resources in the RBAC group

```bash
kubectl api-resources --api-group=rbac.authorization.k8s.io --namespaced=false
```

Expected: `ClusterRole`, `ClusterRoleBinding`.

### Scenario: Get the image of all running pods

```bash
kubectl get pods -A -o jsonpath='{range .items[*]}{.metadata.namespace}/{.metadata.name}{"\t"}{.spec.containers[*].image}{"\n"}{end}'
```

---

## Lab Cleanup

```bash
kubectl delete deployment api-demo
kubectl delete service api-demo
```

---

## Key Takeaways

1. **`kubectl api-versions`** lists all API group/versions your cluster serves
2. **`kubectl api-resources -o wide`** is the single most useful command for mapping resource → apiVersion
3. **`kubectl explain`** shows field-level documentation and deprecation notices
4. Core resources use `apiVersion: v1`; grouped resources use `<group>/<version>`
5. **`-o yaml`** reveals the full object including `status`; use it to understand any resource
6. **`-o jsonpath`** and **`-o custom-columns`** let you extract exactly the fields you need
7. **`kubectl get --raw /apis`** gives programmatic access to the API discovery endpoints
8. Always prefer **stable (GA)** API versions in production manifests

---

## Next Steps

1. **kubectl essentials**: Review [Lab 03: kubectl Essentials](lab03-basics-kubectl-essentials.md) for CRUD operations
2. **YAML manifests**: Practice writing manifests in [Lab 46: YAML Manifests](lab46-basics-yaml-manifests.md)
3. **CRDs**: Explore custom APIs in [Lab 43: Custom Resource Definitions](lab43-adv-custom-resource-definitions.md)
4. **Troubleshooting commands**: Expand your command toolkit in [Lab 54: Commands Reference](lab54-ts-commands-reference.md)

---

## Additional Reading

- [Kubernetes API Overview](https://kubernetes.io/docs/reference/using-api/)
- [API Groups and Versioning](https://kubernetes.io/docs/reference/using-api/#api-groups)
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)
- [JSONPath Support](https://kubernetes.io/docs/reference/kubectl/jsonpath/)

---

**Lab Created**: March 2026
**Compatible with**: Kubernetes 1.24+
**Tested on**: Minikube, Kind, AWS EKS, GCP GKE
