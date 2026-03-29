# Lab 08: Cluster Administration with kubeadm

## Overview
In this lab, you will learn essential cluster administration tasks using kubeadm and kubectl. You'll manage cluster certificates, tokens, nodes, and perform administrative operations to maintain a healthy Kubernetes cluster.

## Prerequisites
- A running Kubernetes cluster
- SSH access to control-plane (master) node
- `kubectl` and `kubeadm` installed
- Root or sudo privileges
- Completion of previous labs (recommended)

## Learning Objectives
By the end of this lab, you will be able to:
- Manage cluster join tokens
- Check and renew TLS certificates
- View and export cluster configuration
- Monitor cluster health
- Work with kubeconfig files
- Access the Kubernetes API server
- Perform cluster maintenance tasks

---

## Exercise 1: Managing Join Tokens

### What are Join Tokens?
Join tokens are secure, time-limited credentials that allow worker nodes to join the cluster. They authenticate the node during the join process.

### Step 1: List Existing Tokens

View all current join tokens:

```bash
kubeadm token list
```

Expected output:
```
TOKEN                     TTL         EXPIRES                USAGES                   DESCRIPTION
abcdef.0123456789abcdef   23h         2026-03-17T10:30:00Z   authentication,signing   default token
```

**Understanding the columns:**
- **TOKEN**: The actual token value
- **TTL**: Time To Live (remaining validity)
- **EXPIRES**: Expiration timestamp
- **USAGES**: Token purpose (authentication, signing)
- **DESCRIPTION**: Token description

### Step 2: Generate a New Token

Create a new token without applying it:

```bash
kubeadm token generate
```

Expected output (example):
```
qg5kgy.o1ov92iu7d50dkye
```

**Use case**: Pre-generate tokens for automation or security audit before creation.

### Step 3: Create a Token with TTL

Create a token that expires in 2 hours:

```bash
kubeadm token create --ttl 2h --print-join-command
```

Expected output:
```
kubeadm join 172.31.33.66:6443 --token qg5kgy.o1ov92iu7d50dkye --discovery-token-ca-cert-hash sha256:e3f0feef4ad831253c3535f72e17c3bddc0c631e789c621f7a130e7e798aa313
```

**Understanding the output:**
- Complete command ready to run on worker nodes
- Includes token and CA certificate hash for verification

**TTL options:**
- `--ttl 0` - Token never expires (not recommended for production)
- `--ttl 2h` - Expires in 2 hours
- `--ttl 24h` - Expires in 24 hours

### Step 4: Delete a Token

Remove a specific token for security:

```bash
kubeadm token delete <token>
```

Example:
```bash
kubeadm token delete qg5kgy.o1ov92iu7d50dkye
```

Expected output:
```
bootstrap token "qg5kgy.o1ov92iu7d50dkye" deleted
```

**When to delete tokens:**
- After all nodes have joined
- If a token is compromised
- Regular security maintenance

---

## Exercise 2: Certificate Management

### Why Manage Certificates?
Kubernetes uses TLS certificates for secure communication between components. Certificates expire and need renewal to maintain cluster security.

### Step 1: Check Certificate Expiration

View expiration dates for all cluster certificates:

```bash
sudo kubeadm certs check-expiration
```

Expected output:
```
CERTIFICATE                EXPIRES                  RESIDUAL TIME   CERTIFICATE AUTHORITY   EXTERNALLY MANAGED
admin.conf                 Mar 16, 2027 10:30 UTC   364d            ca                      no
apiserver                  Mar 16, 2027 10:30 UTC   364d            ca                      no
apiserver-etcd-client      Mar 16, 2027 10:30 UTC   364d            etcd-ca                 no
apiserver-kubelet-client   Mar 16, 2027 10:30 UTC   364d            ca                      no
controller-manager.conf    Mar 16, 2027 10:30 UTC   364d            ca                      no
etcd-healthcheck-client    Mar 16, 2027 10:30 UTC   364d            etcd-ca                 no
etcd-peer                  Mar 16, 2027 10:30 UTC   364d            etcd-ca                 no
etcd-server                Mar 16, 2027 10:30 UTC   364d            etcd-ca                 no
front-proxy-client         Mar 16, 2027 10:30 UTC   364d            front-proxy-ca          no
scheduler.conf             Mar 16, 2027 10:30 UTC   364d            ca                      no

CERTIFICATE AUTHORITY   EXPIRES                  RESIDUAL TIME   EXTERNALLY MANAGED
ca                      Mar 14, 2036 10:30 UTC   9y              no
etcd-ca                 Mar 14, 2036 10:30 UTC   9y              no
front-proxy-ca          Mar 14, 2036 10:30 UTC   9y              no
```

**Key certificates:**
- **apiserver**: API server certificate
- **apiserver-kubelet-client**: API server to kubelet communication
- **etcd-server**: etcd server certificate
- **ca**: Cluster Certificate Authority (10 year validity)

### Step 2: Generate Certificate Key

Create a key for uploading certificates during join:

```bash
kubeadm certs certificate-key
```

Expected output:
```
f6d0c0e7c69f9c0d8e4a5b3f2e1d0c9b8a7f6e5d4c3b2a1f0e9d8c7b6a5f4e3
```

**Use case**: Multi-master cluster setup where additional control-plane nodes need certificates.

### Step 3: Renew All Certificates

Renew all cluster certificates:

```bash
sudo kubeadm certs renew all
```

Expected output:
```
certificate embedded in the kubeconfig file for the admin to use and for kubeadm itself renewed
certificate for serving the Kubernetes API renewed
certificate for the API server to connect to kubelet renewed
certificate embedded in the kubeconfig file for the controller manager to use renewed
certificate for the front proxy client renewed
certificate for serving etcd renewed
certificate for the API server to connect to etcd renewed
certificate embedded in the kubeconfig file for the scheduler manager to use renewed
```

**Important**: After renewal, restart control-plane components:
```bash
sudo systemctl restart kubelet
```

### Step 4: Renew Specific Certificate

Renew only the API server certificate:

```bash
sudo kubeadm certs renew apiserver
```

Expected output:
```
certificate for serving the Kubernetes API renewed
```

---

## Exercise 3: Cluster Configuration Management

### Step 1: View Current Cluster Info

Display basic cluster information:

```bash
kubectl cluster-info
```

Expected output:
```
Kubernetes control plane is running at https://172.31.33.66:6443
CoreDNS is running at https://172.31.33.66:6443/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy

To further debug and diagnose cluster problems, use 'kubectl cluster-info dump'.
```

### Step 2: Generate Cluster Dump

Create a comprehensive diagnostic dump:

```bash
kubectl cluster-info dump > kubernetes_cluster_dump.txt
```

View the dump file:
```bash
head -50 kubernetes_cluster_dump.txt
```

**What's included:**
- Namespace configurations
- Pod specifications and status
- Service definitions
- Node information
- Events and logs

### Step 3: Generate Namespace-Specific Dump

Dump information for kube-system namespace only:

```bash
kubectl cluster-info dump --namespaces kube-system > kube-system-dump.txt
```

**Use cases:**
- Troubleshooting specific namespace issues
- Sharing relevant logs with support
- Auditing namespace configurations

### Step 4: Print Default Init Configuration

View kubeadm's default initialization configuration:

```bash
kubeadm config print init-defaults > kubeadm-init-defaults.yaml
```

Review the file:
```bash
cat kubeadm-init-defaults.yaml
```

**Key sections:**
- `apiVersion`: Kubeadm API version
- `kind`: ClusterConfiguration or InitConfiguration
- `kubernetesVersion`: K8s version to install
- `networking`: Pod and service CIDR
- `controlPlaneEndpoint`: API server endpoint

### Step 5: Initialize Cluster with Custom Config

Use custom configuration (example, DO NOT run on existing cluster):

```bash
# Example only - don't run on production cluster!
# kubeadm init --config kubeadm-init-config.yaml
```

---

## Exercise 4: Kubeconfig Management

### Step 1: View Kubeconfig

Display the current kubeconfig:

```bash
kubectl config view
```

Expected output:
```yaml
apiVersion: v1
clusters:
- cluster:
    certificate-authority-data: DATA+OMITTED
    server: https://172.31.33.66:6443
  name: kubernetes
contexts:
- context:
    cluster: kubernetes
    user: kubernetes-admin
  name: kubernetes-admin@kubernetes
current-context: kubernetes-admin@kubernetes
kind: Config
preferences: {}
users:
- name: kubernetes-admin
  user:
    client-certificate-data: REDACTED
    client-key-data: REDACTED
```

**Key components:**
- **clusters**: API server endpoints
- **users**: Authentication credentials
- **contexts**: Cluster + user combinations
- **current-context**: Active configuration

### Step 2: View Current Context

Check which context is active:

```bash
kubectl config current-context
```

Expected output:
```
kubernetes-admin@kubernetes
```

### Step 3: List All Contexts

View all available contexts:

```bash
kubectl config get-contexts
```

Expected output:
```
CURRENT   NAME                          CLUSTER      AUTHINFO           NAMESPACE
*         kubernetes-admin@kubernetes   kubernetes   kubernetes-admin
```

### Step 4: Switch Context

Switch to a different context (if you have multiple):

```bash
kubectl config use-context <context-name>
```

---

## Exercise 5: Namespace Management

### Step 1: Create a Namespace

Create a namespace for isolation:

```bash
kubectl create namespace firstnamespace
```

Expected output:
```
namespace/firstnamespace created
```

### Step 2: List All Namespaces

View all namespaces in the cluster:

```bash
kubectl get namespaces
```

Expected output:
```
NAME              STATUS   AGE
default           Active   5d
firstnamespace    Active   10s
kube-node-lease   Active   5d
kube-public       Active   5d
kube-system       Active   5d
```

### Step 3: Set Default Namespace

Change the default namespace for kubectl commands:

```bash
kubectl config set-context --current --namespace=firstnamespace
```

Verify:
```bash
kubectl config view --minify | grep namespace:
```

Now `kubectl get pods` will query `firstnamespace` by default.

---

## Exercise 6: API Server Access

### Step 1: Start Kubectl Proxy

Create a proxy to the API server on port 8080:

```bash
kubectl proxy --port=8080
```

Expected output:
```
Starting to serve on 127.0.0.1:8080
```

**Leave this running and open a new terminal for the next steps.**

### Step 2: Access API via Proxy

In a new terminal, query the API:

```bash
curl http://localhost:8080/api/v1/namespaces
```

You should see JSON output with namespace information.

List pods via API:
```bash
curl http://localhost:8080/api/v1/namespaces/default/pods
```

### Step 3: Access Specific Endpoints

View API versions:
```bash
curl http://localhost:8080/api
```

View available API groups:
```bash
curl http://localhost:8080/apis
```

### Step 4: Stop the Proxy

Return to the first terminal and press `Ctrl+C` to stop the proxy.

---

## Exercise 7: Cluster Health Checks

### Step 1: Check Component Status

View control-plane component health:

```bash
kubectl get componentstatuses
```

Or shorter:
```bash
kubectl get cs
```

**Note**: In recent Kubernetes versions, this may show deprecated warnings.

### Step 2: Check Node Status

View node health:

```bash
kubectl get nodes
```

For detailed node conditions:
```bash
kubectl describe nodes
```

**Key node conditions:**
- **Ready**: Node can accept pods
- **MemoryPressure**: Node has sufficient memory
- **DiskPressure**: Node has sufficient disk space
- **PIDPressure**: Node has sufficient process IDs
- **NetworkUnavailable**: Node network is properly configured

### Step 3: Check System Pods

Verify kube-system pods are healthy:

```bash
kubectl get pods -n kube-system
```

All pods should show `Running` status:
```
NAME                                     READY   STATUS    RESTARTS   AGE
coredns-787d4945fb-abc12                 1/1     Running   0          5d
coredns-787d4945fb-def34                 1/1     Running   0          5d
etcd-master.example.com                  1/1     Running   0          5d
kube-apiserver-master.example.com        1/1     Running   0          5d
kube-controller-manager-master           1/1     Running   0          5d
kube-proxy-ghi56                         1/1     Running   0          5d
kube-scheduler-master.example.com        1/1     Running   0          5d
```

---

## Exercise 8: Version Information

### Step 1: Check kubeadm Version

```bash
kubeadm version
```

Expected output:
```
kubeadm version: &version.Info{Major:"1", Minor:"29", GitVersion:"v1.29.2", ...}
```

### Step 2: Check kubectl and Server Version

```bash
kubectl version --short
```

Or:
```bash
kubectl version
```

### Step 3: Check Kubelet Version

```bash
kubelet --version
```

---

## Lab Cleanup

This lab mostly involves viewing and managing cluster state. To clean up the test namespace:

```bash
# Delete the test namespace
kubectl delete namespace firstnamespace

# Reset default namespace
kubectl config set-context --current --namespace=default

# Verify
kubectl config view --minify | grep namespace:
```

---

## Key Takeaways

1. **Join tokens** - Manage with `kubeadm token` commands
2. **Certificates** - Check expiration with `kubeadm certs check-expiration`
3. **Renewal** - Use `kubeadm certs renew all` before expiration
4. **Cluster info** - `kubectl cluster-info` for basic health
5. **Kubeconfig** - Manage contexts and namespaces
6. **API proxy** - `kubectl proxy` for direct API access
7. **Regular maintenance** - Check certificates, tokens, and cluster health

---

## Essential Commands Reference

### Token Management
```bash
kubeadm token list
kubeadm token generate
kubeadm token create --ttl 2h --print-join-command
kubeadm token delete <token>
```

### Certificate Management
```bash
sudo kubeadm certs check-expiration
sudo kubeadm certs renew all
sudo kubeadm certs renew apiserver
kubeadm certs certificate-key
```

### Cluster Information
```bash
kubectl cluster-info
kubectl cluster-info dump
kubectl cluster-info dump --namespaces <namespace>
```

### Configuration Management
```bash
kubeadm config print init-defaults
kubeadm config view
kubeadm version
```

### Kubeconfig Operations
```bash
kubectl config view
kubectl config current-context
kubectl config get-contexts
kubectl config use-context <name>
kubectl config set-context --current --namespace=<namespace>
```

### Cluster Health
```bash
kubectl get nodes
kubectl get componentstatuses
kubectl get pods -n kube-system
kubectl version
```

---

## Troubleshooting Guide

### Issue: Token expired

**Solution**: Create a new token
```bash
kubeadm token create --ttl 24h --print-join-command
```

### Issue: Certificates expiring soon

**Solution**: Renew certificates
```bash
sudo kubeadm certs renew all
sudo systemctl restart kubelet
```

### Issue: Unable to access API server

**Solution**: Check API server status
```bash
kubectl get pods -n kube-system -l component=kube-apiserver
sudo systemctl status kubelet
```

### Issue: Context not found

**Solution**: Recreate kubeconfig
```bash
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config
```

---

## Cluster Reset (⚠️ DESTRUCTIVE)

**Only use in test/development environments:**

```bash
sudo kubeadm reset -f
```

This command:
- Removes all Kubernetes configurations
- Deletes cluster state
- Cleans up network settings
- Requires cluster re-initialization

**WARNING**: This destroys the cluster! Only use when rebuilding from scratch.

---

## Next Steps

Proceed to [Lab 06: Kubernetes Installation](lab06-install-kubernetes-kubeadm.md) to learn how to set up a cluster from scratch.

## Additional Reading

- [kubeadm Documentation](https://kubernetes.io/docs/reference/setup-tools/kubeadm/)
- [Certificate Management](https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/kubeadm-certs/)
- [Cluster Administration](https://kubernetes.io/docs/tasks/administer-cluster/)

---

**Lab Created**: March 2026
**Compatible with**: Kubernetes 1.24+
**Based on**: labs/administration/kubeadm.txt, managingk8s.txt
**Tested on**: kubeadm clusters
