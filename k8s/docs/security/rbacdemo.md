# Kubernetes RBAC with client certificates (conceptual overview)

Before hands-on work, review [RBAC concepts](rbac-concepts.md): **Roles**, **ClusterRoles**, **RoleBindings**, and **ClusterRoleBindings**, and how the API server evaluates **user**, **group**, and **service account** subjects.

## What this pattern demonstrates

Many clusters authenticate human or CI users with **X.509 client certificates** signed by the cluster CA (or an intermediate). The **Common Name** (and optionally **O** / **OU** fields) in the certificate typically maps to a username the API server recognizes. You then **bind** that identity to a **Role** or **ClusterRole** so `kubectl` actions succeed only where policy allows.

A complete walkthrough—namespace creation, OpenSSL CSR flow, signing with the cluster CA, `kubectl config set-credentials` / `set-context`, and positive/negative tests—belongs in the lab manual linked below.

## Illustrative Role (namespace-scoped)

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: role
  name: example-pod-manager
rules:
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list", "watch", "delete"]
```

## Illustrative RoleBinding

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: example-user-binding
  namespace: role
subjects:
- kind: User
  name: user3
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: example-pod-manager
  apiGroup: rbac.authorization.k8s.io
```

## Verifying effective permissions

Use `kubectl auth can-i` (with `--as` or the user’s kubeconfig context) to confirm whether verbs on resources are allowed or forbidden before relying on the binding in automation.

---

## Hands-On Labs

Practice these concepts with guided lab exercises:

| Lab | Description |
|-----|-------------|
| [Lab 11: Role-Based Access Control (RBAC)](../../labmanuals/lab11-sec-rbac-security.md) | End-to-end certificate user, Role, RoleBinding, context switching, and permission checks. |
