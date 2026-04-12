# Role-Based Access Control (RBAC) in Kubernetes

RBAC is the primary mechanism for regulating access to Kubernetes cluster resources. It lets administrators define **who** (users, groups, service accounts) can perform **which actions** (verbs) on **which resources** — ensuring least-privilege security across the cluster.

---

## How RBAC Works

### The RBAC Controller

The **RBAC Controller** is a component of the Kubernetes control plane (running inside the API server). Every API request passes through an authorization check: the controller evaluates the request against defined **Roles** and **Bindings** to decide whether to allow or deny it.

```
kubectl get pods ──► API Server ──► Authentication ──► RBAC Authorization ──► Admitted / Denied
                                     (who are you?)    (are you allowed?)
```

### The Four RBAC Objects

| Object | Scope | Purpose |
|--------|-------|---------|
| **Role** | Namespace | Defines permissions within a single namespace |
| **ClusterRole** | Cluster | Defines permissions cluster-wide or for cluster-scoped resources |
| **RoleBinding** | Namespace | Grants a Role (or ClusterRole) to subjects within a namespace |
| **ClusterRoleBinding** | Cluster | Grants a ClusterRole to subjects across the entire cluster |

---

## Key Components

### 1. Operations (Verbs)

Actions that can be performed on Kubernetes objects:

| Verb | Description |
|------|-------------|
| `get` | Read a single resource |
| `list` | Read multiple resources |
| `create` | Add new resources |
| `update` | Modify existing resources |
| `patch` | Partially modify resources |
| `delete` | Remove resources |
| `watch` | Monitor changes to resources in real time |
| `deletecollection` | Remove multiple resources at once |

### 2. Objects (Resources)

Resources being acted upon — can be **namespace-scoped** or **cluster-scoped**:

| Namespace-scoped | Cluster-scoped |
|-------------------|----------------|
| Pods, Deployments, Services | Nodes, Namespaces, PersistentVolumes |
| ConfigMaps, Secrets | ClusterRoles, ClusterRoleBindings |
| Jobs, CronJobs, StatefulSets | StorageClasses, IngressClasses |
| Roles, RoleBindings | CustomResourceDefinitions |

### 3. Subjects (Who)

Entities that receive permissions via bindings:

| Subject type | Description |
|-------------|-------------|
| **User** | Human user authenticated via certificates, tokens, or external identity providers |
| **Group** | A set of users (e.g., `system:masters`, or an LDAP group) |
| **ServiceAccount** | An in-cluster identity attached to Pods for API access |

---

## RBAC Object Examples

### Role (namespace-scoped)

Grants read access to Pods in the `default` namespace:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: default
  name: pod-reader
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "watch", "list"]
```

### ClusterRole (cluster-wide)

Grants full access to Deployments and Pods across all namespaces:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: deployment-manager
rules:
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list", "watch", "delete"]
```

### RoleBinding (binds Role to subjects in a namespace)

Grants the `pod-reader` Role to user `jane` in the `default` namespace:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: read-pods
  namespace: default
subjects:
- kind: User
  name: jane
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
```

### ClusterRoleBinding (binds ClusterRole cluster-wide)

Grants the `cluster-admin` ClusterRole to user `admin` across the entire cluster:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: cluster-admin-binding
subjects:
- kind: User
  name: admin
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: cluster-admin
  apiGroup: rbac.authorization.k8s.io
```

---

## Role vs ClusterRole Comparison

| Aspect | Role | ClusterRole |
|--------|------|-------------|
| **Scope** | Single namespace | Cluster-wide |
| **Resources** | Namespace-scoped only | Both cluster-scoped and namespace-scoped |
| **Binding** | RoleBinding | ClusterRoleBinding (or RoleBinding to scope it to one namespace) |
| **Use case** | "Developers can manage pods in `dev` namespace" | "Admins can manage nodes" or "read pods in all namespaces" |
| **Example** | `pods` in `default` only | `nodes`, or all `pods` in all namespaces |

> **Tip:** You can bind a ClusterRole using a **RoleBinding** to limit its effect to a single namespace. This is a common pattern — define reusable ClusterRoles and scope them per namespace via RoleBindings.

---

## User Authentication with Client Certificates

Many clusters authenticate human or CI users with **X.509 client certificates** signed by the cluster CA. The **Common Name (CN)** in the certificate maps to the username the API server recognizes, and the **Organization (O)** field maps to groups.

```
Certificate CN: jane   ──►  Kubernetes user: jane
Certificate O:  dev-team ──►  Kubernetes group: dev-team
```

The typical flow:
1. Generate a private key and Certificate Signing Request (CSR)
2. Sign the CSR with the cluster CA (or submit a Kubernetes CSR object)
3. Create a kubeconfig context with `kubectl config set-credentials` and `set-context`
4. Create a Role + RoleBinding for the user
5. Switch context and verify with `kubectl auth can-i`

---

## Verifying Permissions

Use `kubectl auth can-i` to check whether a user/service account has permission:

```bash
kubectl auth can-i get pods --namespace default
kubectl auth can-i create deployments --namespace dev
kubectl auth can-i delete nodes                          # cluster-scoped
kubectl auth can-i get pods --as jane --namespace default # impersonate user
```

List all permissions for the current user:

```bash
kubectl auth can-i --list --namespace default
```

---

## Common Use Cases

### 1. Namespace Isolation
Limit developers to resources within their team's namespace:
- Create a `Role` with the needed verbs on pods, deployments, services
- Bind it to the team's group via a `RoleBinding`

### 2. Service Account Permissions
Grant Pods API access through service accounts:
- A monitoring Pod reads metrics via the Kubernetes API
- A CI/CD runner creates deployments in a target namespace

### 3. Cluster Administration
Provide cluster-wide administrative access:
- System administrators get `cluster-admin` ClusterRole via ClusterRoleBinding
- Use sparingly — this grants full control over the entire cluster

### 4. Read-Only Access
Create read-only roles for auditing or security review:
- Define a ClusterRole with `get`, `list`, `watch` verbs only
- Bind to auditors via ClusterRoleBinding

### 5. Multi-Tenant Environments
Isolate tenants with per-namespace Roles and quotas:
- Each tenant gets their own namespace, Role, and RoleBinding
- Combine with NetworkPolicies and ResourceQuotas for full isolation

---

## Best Practices

| Practice | Why |
|----------|-----|
| **Principle of Least Privilege** | Only grant the permissions required to perform the task |
| **Start with namespace Roles** | Avoid ClusterRoles until you genuinely need cluster-wide access |
| **Use Groups over individual Users** | Easier to manage, scales better with team changes |
| **Avoid wildcard `*` rules** | Wildcards grant everything — be explicit about resources and verbs |
| **Audit regularly** | Review RoleBindings/ClusterRoleBindings periodically |
| **Use `kubectl auth can-i`** | Always verify permissions before relying on them |
| **Leverage built-in ClusterRoles** | `view`, `edit`, `admin`, `cluster-admin` cover common patterns |

### Built-in ClusterRoles

| ClusterRole | Permissions |
|-------------|-------------|
| `view` | Read-only access to most namespace resources (no secrets) |
| `edit` | Read-write access to most namespace resources (no roles/bindings) |
| `admin` | Full namespace access including roles and bindings |
| `cluster-admin` | Full cluster access (superuser) |

---

## Hands-On Labs

Practice these concepts with guided lab exercises:

| Lab | Description |
|-----|-------------|
| [Lab 11: Role-Based Access Control (RBAC)](../../labmanuals/lab11-sec-rbac-security.md) | End-to-end RBAC: create users via client certificates, Roles, RoleBindings, kubeconfig contexts, and permission validation |
