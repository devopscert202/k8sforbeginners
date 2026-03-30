# Kubernetes Contexts: Managing Multiple Clusters, Users, and Namespaces

## Introduction
When working with Kubernetes, especially in environments involving multiple clusters, namespaces, and user roles, managing access and configurations efficiently is critical. Kubernetes contexts provide a powerful way to manage and switch between configurations seamlessly.

This tutorial explains the concept of Kubernetes contexts, their role in managing clusters, users, and namespaces, and provides practical examples and commands for admins.

---

## Key Concepts

### 1. Kubernetes Configuration (`kubeconfig`)
The `kubeconfig` file is a YAML file that stores configuration details about:
- **Clusters**: Represents a specific Kubernetes API server.
- **Users**: Represents credentials to authenticate with the cluster.
- **Contexts**: Combines cluster, user, and namespace information for easy switching.

#### Default Location
The default location for the `kubeconfig` file is:
```bash
~/.kube/config
```

You can specify another file using the `KUBECONFIG` environment variable.

---

### 2. Kubernetes Contexts
A Kubernetes context is a named grouping of:
- A **cluster**.
- A **user**.
- A **namespace**.

Contexts make it easier to switch between multiple Kubernetes environments, such as dev, staging, and production clusters.

---

## Why Use Kubernetes Contexts?

1. **Multi-cluster Management**: Seamlessly switch between clusters without modifying the configuration file manually.
2. **Namespace Isolation**: Target specific namespaces for resource management.
3. **User Management**: Use different user credentials based on the environment.
4. **Productivity**: Avoid repetitive configurations and potential mistakes when running commands across different environments.

---

## Managing Contexts with `kubectl`

### 1. Viewing Current Context
To see the current context in use:
```bash
kubectl config current-context
```

### 2. Viewing All Contexts
List all available contexts:
```bash
kubectl config get-contexts
```

### 3. Switching Contexts
Switch to a specific context:
```bash
kubectl config use-context <context-name>
```

### 4. Creating a New Context
Create a context by specifying the cluster, user, and namespace:
```bash
kubectl config set-context <context-name> \
  --cluster=<cluster-name> \
  --user=<user-name> \
  --namespace=<namespace>
```

### 5. Deleting a Context
Remove a specific context:
```bash
kubectl config delete-context <context-name>
```

---

## Example: Managing Contexts

### 1. Setting Up a Kubeconfig File
Assume you have two clusters:
- `dev-cluster`
- `prod-cluster`

Your `~/.kube/config` file might look like this:
```yaml
apiVersion: v1
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
    namespace: development
    user: dev-user
- name: prod-context
  context:
    cluster: prod-cluster
    namespace: production
    user: prod-user
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

### 2. Switching Between Contexts
Switch from the dev environment to the prod environment:
```bash
kubectl config use-context prod-context
```

---

### 3. Creating a New Context
Add a QA context for the `qa-cluster`:
```bash
kubectl config set-context qa-context \
  --cluster=qa-cluster \
  --user=qa-user \
  --namespace=qa
```

---

### 4. Namespace-Specific Operations
Use the `--namespace` flag to override the default namespace in a context:
```bash
kubectl get pods --namespace=staging
```

Alternatively, modify the current context to change the default namespace:
```bash
kubectl config set-context --current --namespace=staging
```

---

## Best Practices for Managing Contexts

1. **Name Contexts Clearly**: Use descriptive names for contexts (e.g., `dev-context`, `prod-context`) to avoid confusion.
2. **Organize `kubeconfig` Files**: If managing many clusters, split configurations into multiple `kubeconfig` files and use the `KUBECONFIG` environment variable:
   ```bash
   export KUBECONFIG=~/.kube/dev-config:~/.kube/prod-config
   ```
3. **Scripts for Context Switching**: Use scripts or aliases for frequently used contexts:
   ```bash
   alias kdev="kubectl config use-context dev-context"
   alias kprod="kubectl config use-context prod-context"
   ```

---

## Lab Exercise: Managing Contexts

### Objective
Configure and manage Kubernetes contexts for multiple clusters.

### Prerequisites
1. Access to two Kubernetes clusters (e.g., `dev-cluster` and `prod-cluster`).
2. A valid `kubeconfig` file.

---

### Step 1: Verify Clusters
List available clusters:
```bash
kubectl config get-clusters
```

### Step 2: Create Contexts
Set up contexts for each cluster:
```bash
kubectl config set-context dev-context \
  --cluster=dev-cluster \
  --user=dev-user \
  --namespace=development

kubectl config set-context prod-context \
  --cluster=prod-cluster \
  --user=prod-user \
  --namespace=production
```

### Step 3: Switch Contexts
Switch to the development environment:
```bash
kubectl config use-context dev-context
```

List pods in the `development` namespace:
```bash
kubectl get pods
```

Switch to the production environment:
```bash
kubectl config use-context prod-context
```

List pods in the `production` namespace:
```bash
kubectl get pods
```

### Step 4: Cleanup
Delete the `dev-context`:
```bash
kubectl config delete-context dev-context
```

---

## Summary

Kubernetes contexts simplify managing multiple clusters, users, and namespaces by allowing quick and consistent configuration switching. By mastering contexts, administrators can efficiently operate across complex Kubernetes environments.

---

## Additional Resources

- [Kubernetes Official Documentation on Contexts](https://kubernetes.io/docs/reference/generated/kubectl/kubectl-commands#config)
- [Managing Multiple Clusters with Kubeconfig](https://kubernetes.io/docs/concepts/configuration/organize-cluster-access-kubeconfig/)



