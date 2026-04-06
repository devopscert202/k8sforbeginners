# Lab 61: Kubeconfig and Context Management

## Overview

When working with Kubernetes — especially across multiple clusters, users, and namespaces — you need a way to tell `kubectl` **which cluster** to talk to, **which credentials** to use, and **which namespace** to default to. That is the job of the **kubeconfig** file and **contexts**.

A **context** is a named grouping of a cluster, a user, and a namespace. By switching contexts, you can jump between your dev cluster, staging cluster, and production cluster in a single terminal without editing files.

In this lab you will explore your kubeconfig file, create and switch contexts, set default namespaces, manage multiple kubeconfig files, and clean up contexts you no longer need.

## Prerequisites

- A running Kubernetes cluster (Minikube, Kind, or any K8s cluster)
- `kubectl` CLI tool installed and configured
- Completion of [Lab 03: kubectl Essentials](lab03-basics-kubectl-essentials.md) (recommended)

## Learning Objectives

By the end of this lab, you will be able to:

- Understand the structure of a kubeconfig file (clusters, users, contexts)
- View, create, switch, rename, and delete contexts
- Set and change the default namespace for a context
- Merge multiple kubeconfig files using the `KUBECONFIG` environment variable
- Use `kubectl config view` to inspect the effective configuration
- Understand how contexts relate to RBAC user switching

---

## Concepts

### Kubeconfig Structure

The kubeconfig file (`~/.kube/config` by default) is a YAML file with three main sections:

```yaml
apiVersion: v1
kind: Config
clusters:          # API server endpoints + CA certificates
- name: my-cluster
  cluster:
    server: https://192.168.1.100:6443
    certificate-authority-data: <base64-ca-cert>

users:             # Credentials (certificates, tokens, OIDC, etc.)
- name: admin
  user:
    client-certificate-data: <base64-cert>
    client-key-data: <base64-key>

contexts:          # Named combinations of cluster + user + namespace
- name: admin@my-cluster
  context:
    cluster: my-cluster
    user: admin
    namespace: default

current-context: admin@my-cluster   # The active context
```

### How Context Switching Works

```
Context = Cluster + User + Namespace
                ↓
kubectl config use-context <name>
                ↓
All subsequent kubectl commands use that cluster, user, and namespace
```

---

## Exercise 1: Exploring Your Current Kubeconfig

### Step 1: View the current context

```bash
kubectl config current-context
```

This prints the name of the context `kubectl` is currently using.

### Step 2: List all available contexts

```bash
kubectl config get-contexts
```

Expected output:

```
CURRENT   NAME                 CLUSTER          AUTHINFO         NAMESPACE
*         kubernetes-admin     kubernetes       kubernetes-admin default
```

The `*` marks the active context. Columns show the context name, which cluster and user it maps to, and the default namespace.

### Step 3: View the full kubeconfig

```bash
kubectl config view
```

This shows the entire kubeconfig (with secrets redacted). To see raw secrets:

```bash
kubectl config view --raw
```

### Step 4: View just the clusters

```bash
kubectl config get-clusters
```

### Step 5: View just the users

```bash
kubectl config get-users
```

---

## Exercise 2: Creating and Switching Contexts

### Step 1: Create namespaces for the exercise

```bash
kubectl create namespace dev
kubectl create namespace staging
kubectl create namespace production
```

### Step 2: Create a context for the dev namespace

```bash
kubectl config set-context dev-context \
  --cluster=$(kubectl config view -o jsonpath='{.clusters[0].name}') \
  --user=$(kubectl config view -o jsonpath='{.users[0].name}') \
  --namespace=dev
```

**What this does**: Creates a new context called `dev-context` that points to your current cluster and user but defaults to the `dev` namespace.

### Step 3: Create contexts for staging and production

```bash
kubectl config set-context staging-context \
  --cluster=$(kubectl config view -o jsonpath='{.clusters[0].name}') \
  --user=$(kubectl config view -o jsonpath='{.users[0].name}') \
  --namespace=staging

kubectl config set-context prod-context \
  --cluster=$(kubectl config view -o jsonpath='{.clusters[0].name}') \
  --user=$(kubectl config view -o jsonpath='{.users[0].name}') \
  --namespace=production
```

### Step 4: Verify all contexts exist

```bash
kubectl config get-contexts
```

You should now see your original context plus `dev-context`, `staging-context`, and `prod-context`.

### Step 5: Switch to the dev context

```bash
kubectl config use-context dev-context
```

### Step 6: Verify the switch

```bash
kubectl config current-context
```

Expected: `dev-context`

### Step 7: Create a pod in the dev namespace (via context default)

```bash
kubectl run dev-nginx --image=nginx:1.25-alpine
kubectl get pods
```

The pod is created in the `dev` namespace because that is the default for `dev-context`. You did not need to pass `--namespace=dev`.

### Step 8: Switch to staging and verify isolation

```bash
kubectl config use-context staging-context
kubectl get pods
```

Expected: No pods (the dev-nginx pod is in `dev`, not `staging`).

### Step 9: Switch back to the original context

```bash
kubectl config use-context $(kubectl config get-contexts -o name | head -1)
```

Or use the name you noted in Step 1.

---

## Exercise 3: Changing the Default Namespace

### Step 1: Check the current default namespace

```bash
kubectl config view --minify -o jsonpath='{.contexts[0].context.namespace}'
echo
```

### Step 2: Change the default namespace for the current context

```bash
kubectl config set-context --current --namespace=kube-system
```

### Step 3: Verify — pods now show kube-system by default

```bash
kubectl get pods
```

You should see system pods (coredns, kube-proxy, etc.) without needing `--namespace=kube-system`.

### Step 4: Reset to default namespace

```bash
kubectl config set-context --current --namespace=default
```

---

## Exercise 4: Working with Multiple Kubeconfig Files

### Step 1: Export a context to a separate file

```bash
kubectl config view --minify --flatten > /tmp/dev-kubeconfig.yaml
```

This saves the current context's config (cluster, user, context) to a standalone file.

### Step 2: View the exported file

```bash
cat /tmp/dev-kubeconfig.yaml
```

### Step 3: Use a specific kubeconfig file

```bash
kubectl --kubeconfig=/tmp/dev-kubeconfig.yaml get nodes
```

### Step 4: Merge multiple kubeconfig files

```bash
export KUBECONFIG=~/.kube/config:/tmp/dev-kubeconfig.yaml
kubectl config get-contexts
```

The `KUBECONFIG` variable accepts colon-separated paths. All clusters, users, and contexts from both files are available.

### Step 5: Reset KUBECONFIG

```bash
unset KUBECONFIG
```

---

## Exercise 5: Renaming and Deleting Contexts

### Step 1: Rename a context

```bash
kubectl config rename-context dev-context development
```

Verify:

```bash
kubectl config get-contexts
```

`dev-context` is now `development`.

### Step 2: Delete a context

```bash
kubectl config delete-context staging-context
```

### Step 3: Verify deletion

```bash
kubectl config get-contexts
```

`staging-context` should no longer appear.

### Step 4: Delete a user entry (optional)

```bash
kubectl config unset users.<user-name>
```

### Step 5: Delete a cluster entry (optional)

```bash
kubectl config unset clusters.<cluster-name>
```

---

## Exercise 6: Context Switching for RBAC Testing

When testing RBAC policies, you create users with limited permissions and switch contexts to verify access. This exercise demonstrates the pattern.

### Step 1: Create a namespace and service account

```bash
kubectl create namespace rbac-test
kubectl create serviceaccount test-user -n rbac-test
```

### Step 2: Create a Role with limited permissions

```bash
cat <<EOF | kubectl apply -f -
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: rbac-test
  name: pod-reader
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list"]
EOF
```

### Step 3: Bind the role to the service account

```bash
cat <<EOF | kubectl apply -f -
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: test-user-pod-reader
  namespace: rbac-test
subjects:
- kind: ServiceAccount
  name: test-user
  namespace: rbac-test
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
EOF
```

### Step 4: Get a token for the service account

```bash
SA_TOKEN=$(kubectl create token test-user -n rbac-test --duration=1h)
```

### Step 5: Create a context for the test user

```bash
CLUSTER_NAME=$(kubectl config view -o jsonpath='{.clusters[0].name}')
CLUSTER_SERVER=$(kubectl config view -o jsonpath='{.clusters[0].cluster.server}')

kubectl config set-credentials test-user --token=$SA_TOKEN
kubectl config set-context test-user-context \
  --cluster=$CLUSTER_NAME \
  --user=test-user \
  --namespace=rbac-test
```

### Step 6: Switch to the test user context and verify access

```bash
kubectl config use-context test-user-context

kubectl get pods -n rbac-test
kubectl get deployments -n rbac-test
```

Expected:
- `get pods` → succeeds (allowed by Role)
- `get deployments` → **forbidden** (not in the Role)

### Step 7: Verify with `auth can-i`

```bash
kubectl auth can-i get pods -n rbac-test
kubectl auth can-i create pods -n rbac-test
kubectl auth can-i get deployments -n rbac-test
```

### Step 8: Switch back to admin context

```bash
kubectl config use-context $(kubectl config get-contexts -o name | grep -v test-user | head -1)
```

---

## Lab Cleanup

```bash
kubectl config use-context $(kubectl config get-contexts -o name | grep -v test-user | grep -v development | grep -v prod | head -1)

kubectl config delete-context development 2>/dev/null
kubectl config delete-context prod-context 2>/dev/null
kubectl config delete-context test-user-context 2>/dev/null
kubectl config unset users.test-user 2>/dev/null

kubectl delete namespace dev staging production rbac-test --ignore-not-found=true
kubectl delete pod dev-nginx -n dev --ignore-not-found=true

rm -f /tmp/dev-kubeconfig.yaml

kubectl config get-contexts
```

---

## Key Takeaways

1. A **context** = cluster + user + namespace — switch with `kubectl config use-context`
2. `kubectl config get-contexts` shows all contexts; `*` marks the active one
3. Set a default namespace with `kubectl config set-context --current --namespace=<ns>`
4. Merge kubeconfig files with `KUBECONFIG=file1:file2`
5. Context switching is essential for **RBAC testing** — create a user, bind a Role, switch context, verify permissions
6. `kubectl config view --minify` shows only the active context's config
7. Always know which context you are in before running destructive commands in production

---

## Next Steps

1. **RBAC deep dive**: Practice full certificate-based user creation and RBAC in [Lab 11: RBAC Security](lab11-sec-rbac-security.md)
2. **kubectl essentials**: Review core commands in [Lab 03: kubectl Essentials](lab03-basics-kubectl-essentials.md)
3. **API discovery**: Explore cluster APIs in [Lab 60: Kubernetes API Discovery](lab60-basics-k8s-apis.md)

---

## Additional Reading

- [Organize Cluster Access Using kubeconfig](https://kubernetes.io/docs/concepts/configuration/organize-cluster-access-kubeconfig/)
- [Configure Access to Multiple Clusters](https://kubernetes.io/docs/tasks/access-application-cluster/configure-access-multiple-clusters/)
- [kubectl config reference](https://kubernetes.io/docs/reference/generated/kubectl/kubectl-commands#config)

---

**Lab Created**: March 2026
**Compatible with**: Kubernetes 1.24+
**Tested on**: Minikube, Kind, kubeadm clusters
