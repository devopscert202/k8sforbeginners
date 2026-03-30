# Lab 32: Headlamp Kubernetes UI

## Overview

In this lab, you will install **Headlamp** as an in-cluster Kubernetes web UI on a **3-node VM-based Kubernetes cluster**. This lab uses the official **in-cluster** installation path from the Headlamp documentation and then adds a practical access method using a ServiceAccount token and `kubectl port-forward`.

This lab is the recommended replacement path for older Kubernetes Dashboard-based UI exercises.

## Background

The Kubernetes Dashboard project was officially retired and archived on **January 21, 2026**. The official Kubernetes Dashboard GitHub repository says the project is no longer maintained. That same repository recommends that users consider **Headlamp** instead.

Because of that, Headlamp is now the better choice for new Kubernetes UI labs.

## Prerequisites

- A working **3-node Kubernetes cluster on VMs**
- `kubectl` configured with cluster-admin access
- `helm` installed on the control plane node or admin workstation
- Internet access from the cluster or admin workstation to pull images and the Helm chart
- Basic familiarity with:
  - Pods and Deployments
  - Services
  - RBAC
  - port-forwarding

## Learning Objectives

By the end of this lab, you will be able to:

- explain why Headlamp is now a better UI option for new Kubernetes labs
- install Headlamp in-cluster using Helm
- verify Headlamp Deployment, Pod, and Service resources
- create a ServiceAccount for Headlamp access
- generate a login token
- access Headlamp with `kubectl port-forward`
- validate cluster visibility from the UI
- understand safe next steps for ingress and OIDC-based access

---

## Lab Topology

This lab assumes a VM-based cluster similar to:

- **Node 1**: control plane
- **Node 2**: worker
- **Node 3**: worker

You will run the installation commands from the control plane node or from an admin VM that already has cluster-admin kubeconfig access.

---

## Exercise 1: Confirm Cluster Readiness

### Step 1: Check node status

```bash
kubectl get nodes -o wide
```

Expected result:

- all 3 nodes should be in `Ready` state

### Step 2: Confirm access to the cluster

```bash
kubectl cluster-info
kubectl get ns
```

### Step 3: Check Helm

```bash
helm version
```

If Helm is not installed, install it first before continuing.

---

## Exercise 2: Install Headlamp In-Cluster

The official Headlamp documentation says the easiest way to install Headlamp in an existing cluster is to use **Helm**.

### Step 1: Add the Headlamp Helm repository

```bash
helm repo add headlamp https://kubernetes-sigs.github.io/headlamp/
helm repo update
```

### Step 2: Install Headlamp into `kube-system`

```bash
helm install my-headlamp headlamp/headlamp --namespace kube-system
```

Expected output will include:

- release name `my-headlamp`
- namespace `kube-system`
- successful deployment details

### Step 3: Verify the Helm release

```bash
helm list -n kube-system
helm status my-headlamp -n kube-system
```

---

## Exercise 3: Verify the Headlamp Resources

### Step 1: Check Pod, Deployment, and Service

```bash
kubectl get deploy,po,svc -n kube-system | grep headlamp
```

You should see:

- a **Deployment**
- a **Pod** in `Running` state
- a **Service** named `headlamp`

### Step 2: Describe the Deployment

```bash
kubectl describe deployment headlamp -n kube-system
```

### Step 3: Check logs

```bash
kubectl logs deployment/headlamp -n kube-system
```

If the Pod is not running, inspect:

```bash
kubectl get pods -n kube-system
kubectl describe pod -n kube-system <headlamp-pod-name>
```

---

## Exercise 4: Understand How Headlamp Auth Works In-Cluster

According to the official documentation, when Headlamp runs in-cluster it uses the **default ServiceAccount** from the namespace it is deployed to and generates a kubeconfig from it named `main`.

That means:

- Headlamp itself runs with Kubernetes credentials
- the actual permissions depend on the ServiceAccount and RBAC granted
- browser login and user access should still be controlled carefully

For this lab, we will create a **separate admin ServiceAccount** so the UI can be accessed safely in a controlled environment.

---

## Exercise 5: Create a Lab Access User for Headlamp

### Step 1: Create the access manifest

Use the manifest at `k8s/labs/k8s-headlamp/headlamp-admin.yaml` or create the same file manually:

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: headlamp-admin
  namespace: kube-system
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: headlamp-admin
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cluster-admin
subjects:
- kind: ServiceAccount
  name: headlamp-admin
  namespace: kube-system
```

### Step 2: Apply the manifest

```bash
kubectl apply -f k8s/labs/k8s-headlamp/headlamp-admin.yaml
```

### Step 3: Verify the ServiceAccount and binding

```bash
kubectl get sa headlamp-admin -n kube-system
kubectl get clusterrolebinding headlamp-admin
```

### Security note

This lab uses `cluster-admin` only for setup convenience. In production:

- prefer OIDC for human users
- prefer namespace-scoped roles
- avoid giving broad admin rights through a long-lived token

---

## Exercise 6: Generate a Login Token

### Step 1: Create a token

```bash
kubectl create token headlamp-admin -n kube-system
```

Copy the token output and keep it ready for browser login.

### Step 2: Optional short-duration token

If you want a shorter session:

```bash
kubectl create token headlamp-admin -n kube-system --duration=1h
```

---

## Exercise 7: Access Headlamp with Port-Forward

The official in-cluster documentation gives this port-forward example:

```bash
kubectl port-forward -n kube-system service/headlamp 8080:80
```

### Step 1: Start port-forward

```bash
kubectl port-forward -n kube-system service/headlamp 8080:80
```

Keep this terminal open.

### Step 2: Open the UI

From a browser on the same machine, open:

```text
http://localhost:8080
```

If your browser is on another machine, use SSH port forwarding or run the port-forward on the machine where the browser is available.

---

## Exercise 8: Log In and Explore the UI

### Step 1: Log in

- open Headlamp in the browser
- choose the token-based login flow if prompted
- paste the token created earlier

### Step 2: Validate the home page

Confirm that you can see:

- cluster overview
- namespaces
- nodes
- workloads
- configuration resources

### Step 3: Validate node visibility

Use the UI to check:

- control plane node
- worker node 1
- worker node 2

### Step 4: Validate workloads

Browse:

- Pods
- Deployments
- Services
- ConfigMaps
- Secrets

### Step 5: Validate namespace switching

Move between namespaces such as:

- `default`
- `kube-system`
- any application namespace already present in your lab environment

---

## Exercise 9: Functional Testing Checklist

Use this checklist after login:

- [ ] Headlamp home page opens
- [ ] Login succeeds with the generated token
- [ ] Nodes are visible
- [ ] Namespaces are visible
- [ ] Pods in `kube-system` are visible
- [ ] Deployment list loads
- [ ] Service list loads
- [ ] Resource details page opens
- [ ] YAML view works
- [ ] Events or logs can be inspected

If all of the above work, the in-cluster installation is functioning correctly.

---

## Exercise 10: Optional Shared Access with Ingress

The official Headlamp docs also provide an ingress sample. For this lab, **port-forward** is the simplest and safest option.

Move to ingress only when:

- multiple users need browser access
- DNS is available
- TLS is available
- you are ready to add stronger authentication such as OIDC

---

## Troubleshooting

### Issue 1: Helm install fails

```bash
helm repo list
helm repo update
kubectl get nodes
```

Check:

- internet access
- DNS resolution
- Helm repository availability
- cluster connectivity

### Issue 2: Headlamp Pod not running

```bash
kubectl get pods -n kube-system
kubectl describe pod -n kube-system <headlamp-pod-name>
kubectl logs -n kube-system <headlamp-pod-name>
```

Common causes:

- image pull failure
- proxy or firewall issue
- cluster resource pressure

### Issue 3: Port-forward does not open

```bash
kubectl get svc headlamp -n kube-system
kubectl port-forward -n kube-system service/headlamp 8080:80
```

Check:

- the Service exists
- the local port is free
- the Headlamp Pod is healthy

### Issue 4: Login fails with token

Check:

```bash
kubectl get sa headlamp-admin -n kube-system
kubectl get clusterrolebinding headlamp-admin
kubectl create token headlamp-admin -n kube-system
```

If required, recreate the token and retry.

### Issue 5: UI opens but resources are missing

This usually means the login identity does not have enough RBAC permissions.

Check:

```bash
kubectl auth can-i get pods --as=system:serviceaccount:kube-system:headlamp-admin -A
```

---

## Cleanup

### Option 1: Stop access only

Stop the port-forward process with `Ctrl+C`.

### Option 2: Remove the lab access user

```bash
kubectl delete -f k8s/labs/k8s-headlamp/headlamp-admin.yaml
```

### Option 3: Uninstall Headlamp completely

```bash
helm uninstall my-headlamp -n kube-system
```

Verify cleanup:

```bash
kubectl get deploy,po,svc -n kube-system | grep headlamp
```

---

## Key Takeaways

1. Headlamp is the more current Kubernetes UI choice for new labs.
2. The official in-cluster installation path is Helm-based and simple.
3. Port-forward is the easiest access path for a VM-based training cluster.
4. Authentication and authorization still depend on Kubernetes identities and RBAC.
5. For production, prefer ingress plus OIDC rather than broad admin tokens.

---

## Further Reading

- Headlamp intro: https://headlamp.dev/docs/latest/
- Headlamp in-cluster install: https://headlamp.dev/docs/latest/installation/in-cluster/
- Headlamp plugins: https://headlamp.dev/docs/latest/installation/in-cluster/
- Archived Kubernetes Dashboard repository note: https://github.com/kubernetes/dashboard

---

**Lab Created**: March 2026  
**Compatible with**: Kubernetes 1.24+ | Headlamp latest in-cluster documentation
