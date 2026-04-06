# Kubernetes Contexts: Managing Multiple Clusters, Users, and Namespaces

## Introduction

When working with Kubernetes — especially across multiple clusters, namespaces, and user roles — you need a consistent way to tell `kubectl` **which cluster** to connect to, **which credentials** to authenticate with, and **which namespace** to use by default. Kubernetes **contexts** provide exactly that: a named grouping of cluster + user + namespace that you can switch between instantly.

---

## Key Concepts

### Kubeconfig File

The `kubeconfig` file is a YAML configuration that stores everything `kubectl` needs to connect to one or more clusters. It has three main sections:

| Section | What it stores | Example |
|---------|---------------|---------|
| **clusters** | API server endpoints and CA certificates | `https://dev.k8s.example.com:6443` |
| **users** | Authentication credentials (certificates, tokens, OIDC) | Client cert for `jane`, token for `ci-bot` |
| **contexts** | Named combinations of cluster + user + namespace | `dev-context` → dev-cluster + jane + dev namespace |

The file also has a `current-context` field that specifies which context is active.

**Default location**: `~/.kube/config`

You can override it with the `KUBECONFIG` environment variable, or merge multiple files:

```bash
export KUBECONFIG=~/.kube/dev-config:~/.kube/prod-config
```

### What Is a Context?

A **context** is a named triple:

```
Context = Cluster + User + Namespace
```

When you run `kubectl config use-context dev-context`, all subsequent `kubectl` commands automatically target that cluster, authenticate as that user, and default to that namespace.

### Illustrative Kubeconfig

```yaml
apiVersion: v1
kind: Config
clusters:
- name: dev-cluster
  cluster:
    server: https://dev.k8s.example.com
- name: prod-cluster
  cluster:
    server: https://prod.k8s.example.com
contexts:
- name: dev-context
  context:
    cluster: dev-cluster
    user: dev-user
    namespace: development
- name: prod-context
  context:
    cluster: prod-cluster
    user: prod-user
    namespace: production
current-context: dev-context
users:
- name: dev-user
  user:
    token: <dev-token>
- name: prod-user
  user:
    token: <prod-token>
```

---

## Why Contexts Matter

| Use case | How contexts help |
|----------|-------------------|
| **Multi-cluster management** | Switch between dev, staging, prod clusters without editing files |
| **Namespace isolation** | Set a default namespace per context so you don't need `--namespace` every time |
| **User switching** | Test RBAC permissions by creating a context with a limited user |
| **CI/CD pipelines** | Each pipeline stage uses a different context (build → deploy-staging → deploy-prod) |
| **Safety** | Naming contexts clearly (e.g., `PROD-admin`) prevents accidental commands against production |

---

## Command Reference

| Command | Purpose |
|---------|---------|
| `kubectl config current-context` | Show the active context |
| `kubectl config get-contexts` | List all contexts (`*` marks active) |
| `kubectl config use-context <name>` | Switch to a different context |
| `kubectl config set-context <name> --cluster=... --user=... --namespace=...` | Create or update a context |
| `kubectl config set-context --current --namespace=<ns>` | Change the default namespace for the current context |
| `kubectl config rename-context <old> <new>` | Rename a context |
| `kubectl config delete-context <name>` | Remove a context |
| `kubectl config view` | Show the full kubeconfig (secrets redacted) |
| `kubectl config view --minify` | Show only the active context's config |
| `kubectl config view --raw` | Show the full kubeconfig with raw secrets |
| `kubectl config get-clusters` | List cluster entries |
| `kubectl config get-users` | List user entries |
| `kubectl config set-credentials <name> --token=...` | Add or update user credentials |
| `kubectl config unset users.<name>` | Remove a user entry |
| `kubectl config unset clusters.<name>` | Remove a cluster entry |

---

## Contexts and RBAC

Contexts are central to **RBAC testing**. When you create a new user (via client certificates or service account tokens) and bind a Role to them, you verify their permissions by:

1. Adding their credentials with `kubectl config set-credentials`
2. Creating a context that uses those credentials with `kubectl config set-context`
3. Switching to that context with `kubectl config use-context`
4. Running commands to confirm what is allowed and what is forbidden
5. Using `kubectl auth can-i` for quick permission checks

This pattern is used extensively in the RBAC lab linked below.

---

## Best Practices

| Practice | Why |
|----------|-----|
| **Name contexts clearly** | Use descriptive names like `prod-admin`, `dev-readonly`, `staging-deployer` |
| **Use aliases for frequent switches** | `alias kdev="kubectl config use-context dev-context"` |
| **Split kubeconfig files per cluster** | Easier to share, rotate, and revoke access |
| **Always verify before production commands** | Run `kubectl config current-context` before destructive operations |
| **Use `--minify` for debugging** | Shows only the active context, removing noise |
| **Combine with `kubectx`/`kubens`** | Community tools for faster context and namespace switching |

---

## Interactive Explainer

- [Kubeconfig & Contexts — Interactive HTML](../../html/kubeconfig-contexts.html) — visual walkthrough of kubeconfig structure, context switching flow, command reference, and real-world scenarios.

## Hands-On Labs

Practice these concepts with guided lab exercises:

| Lab | Description |
|-----|-------------|
| [Lab 61: Kubeconfig and Context Management](../../labmanuals/lab61-basics-kubeconfig-contexts.md) | Create, switch, rename, and delete contexts; set default namespaces; merge kubeconfig files; RBAC context switching |
| [Lab 11: Role-Based Access Control (RBAC)](../../labmanuals/lab11-sec-rbac-security.md) | Full RBAC workflow that uses context switching to test user permissions with client certificates |

---

## Additional Resources

- [Organize Cluster Access Using kubeconfig](https://kubernetes.io/docs/concepts/configuration/organize-cluster-access-kubeconfig/)
- [Configure Access to Multiple Clusters](https://kubernetes.io/docs/tasks/access-application-cluster/configure-access-multiple-clusters/)
- [kubectl config reference](https://kubernetes.io/docs/reference/generated/kubectl/kubectl-commands#config)
