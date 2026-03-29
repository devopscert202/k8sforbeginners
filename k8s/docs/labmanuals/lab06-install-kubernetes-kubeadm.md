# Lab 06: Kubernetes Cluster Installation

## Overview
In this comprehensive lab, you will install a complete Kubernetes cluster from scratch on Ubuntu Linux systems using kubeadm. You'll set up one control-plane (master) node and multiple worker nodes, configure networking, and verify the installation.

## Prerequisites
- Multiple Ubuntu 20.04 or 22.04 machines (VMs or bare metal)
  - 1 master node (control-plane)
  - 2+ worker nodes
- Minimum 2 CPUs and 4 GB RAM per node
- At least 20 GB free disk space per node
- Network connectivity between all nodes
- Root or sudo access on all nodes
- Basic Linux command-line knowledge

## Learning Objectives
By the end of this lab, you will be able to:
- Prepare systems for Kubernetes installation
- Install and configure container runtime (containerd)
- Install Kubernetes components (kubeadm, kubelet, kubectl)
- Bootstrap a Kubernetes control-plane
- Configure pod networking with Calico
- Join worker nodes to the cluster
- Verify cluster functionality
- Troubleshoot common installation issues

---

## What is Kubernetes?

### Introduction
Kubernetes (K8s) is an open-source platform designed to automate the deployment, scaling, and management of containerized applications. It provides powerful orchestration features such as:

- **Load balancing** - Distributes traffic across containers
- **Service discovery** - Automatic DNS and environment variables
- **Self-healing** - Restarts failed containers
- **Automated rollouts and rollbacks** - Zero-downtime deployments
- **Configuration management** - Secrets and ConfigMaps
- **Storage orchestration** - Automatic volume mounting

---

## High-Level Installation Process

```
1. Prepare System → 2. Set Hostnames → 3. Install containerd
         ↓
4. Install K8s Tools → 5. Initialize Control Plane → 6. Install CNI
         ↓
7. Join Worker Nodes → 8. Verify Cluster → 9. Test Deployment
```

---

## Understanding Kubernetes Components

### Key Tools

| Component | Purpose | Runs On | Use Case |
|-----------|---------|---------|----------|
| **kubeadm** | Bootstraps secure Kubernetes clusters | All nodes | Initialize control plane, join nodes |
| **kubectl** | CLI for interacting with Kubernetes API | Master node (can be on workers too) | Manage cluster resources |
| **kubelet** | Node agent ensuring containers are running | All nodes | Maintains desired pod state |

### Control Plane Components (Master Node)

- **kube-apiserver**: Front-end for Kubernetes control plane
- **etcd**: Consistent and highly-available key-value store
- **kube-scheduler**: Assigns pods to nodes
- **kube-controller-manager**: Runs controller processes
- **cloud-controller-manager**: Interacts with cloud providers (if applicable)

### Node Components (All Nodes)

- **kubelet**: Agent that runs on each node
- **kube-proxy**: Network proxy maintaining network rules
- **Container Runtime**: containerd, CRI-O, or Docker

---

## Exercise 1: System Preparation

Perform these steps on **ALL nodes** (master and workers).

### Step 1: Update System Packages

```bash
sudo apt update && sudo apt upgrade -y
```

**Why?** Ensures all packages are up-to-date and security patches are applied.

### Step 2: Disable Swap

Kubernetes requires swap to be disabled:

```bash
sudo swapoff -a
```

Make it permanent by editing /etc/fstab:

```bash
sudo sed -i '/ swap / s/^/#/' /etc/fstab
```

Verify swap is off:

```bash
free -h
```

The Swap line should show 0B total.

**Why?** Kubernetes scheduler requires predictable memory allocation. Swap can cause performance issues.

### Step 3: Remove Docker (If Installed)

If Docker is installed, remove it to avoid conflicts with containerd:

```bash
sudo apt-get purge -y docker-engine docker docker.io docker-ce docker-ce-cli
sudo apt-get autoremove -y --purge
sudo rm -rf /var/lib/docker /etc/docker
sudo rm -f /etc/containerd/config.toml
```

### Step 4: Enable Required Kernel Modules

Load overlay and br_netfilter modules:

```bash
sudo modprobe overlay
sudo modprobe br_netfilter
```

Make them load on boot:

```bash
cat <<EOF | sudo tee /etc/modules-load.d/containerd.conf
overlay
br_netfilter
EOF
```

### Step 5: Configure Kernel Parameters

Set required sysctl parameters:

```bash
cat <<EOF | sudo tee /etc/sysctl.d/kubernetes.conf
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward                 = 1
EOF
```

Apply sysctl parameters:

```bash
sudo sysctl --system
```

Verify settings:

```bash
sysctl net.bridge.bridge-nf-call-iptables net.ipv4.ip_forward
```

Expected output:
```
net.bridge.bridge-nf-call-iptables = 1
net.ipv4.ip_forward = 1
```

---

## Exercise 2: Install Container Runtime (containerd)

Perform on **ALL nodes**.

### Step 1: Install containerd

```bash
sudo apt update
sudo apt install -y containerd
```

### Step 2: Configure containerd

Generate default configuration:

```bash
sudo mkdir -p /etc/containerd
containerd config default | sudo tee /etc/containerd/config.toml
```

### Step 3: Enable SystemdCgroup

Edit the config file:

```bash
sudo nano /etc/containerd/config.toml
```

Find this section:
```toml
[plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc.options]
```

And set `SystemdCgroup` to `true`:
```toml
  SystemdCgroup = true
```

**Tip**: Use `Ctrl+W` in nano to search for "SystemdCgroup".

Save and exit (`Ctrl+X`, then `Y`, then `Enter`).

### Step 4: Restart containerd

```bash
sudo systemctl restart containerd
sudo systemctl enable containerd
```

Verify it's running:

```bash
sudo systemctl status containerd
```

Should show `active (running)`.

---

## Exercise 3: Install Kubernetes Tools

Perform on **ALL nodes**.

### Step 1: Install Dependencies

```bash
sudo apt update
sudo apt install -y apt-transport-https ca-certificates curl
```

### Step 2: Add Kubernetes APT Repository

Download the GPG key:

```bash
curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo gpg --dearmor -o /etc/apt/trusted.gpg.d/kubernetes-archive-keyring.gpg
```

Add the repository:

```bash
echo "deb https://apt.kubernetes.io/ kubernetes-xenial main" | sudo tee /etc/apt/sources.list.d/kubernetes.list
```

### Step 3: Install kubeadm, kubelet, and kubectl

Update package list:

```bash
sudo apt update
```

Install Kubernetes tools:

```bash
sudo apt install -y kubelet kubeadm kubectl
```

Prevent automatic updates (hold packages):

```bash
sudo apt-mark hold kubelet kubeadm kubectl
```

**Why hold packages?** Kubernetes versions must be upgraded in a controlled manner.

### Step 4: Verify Installation

Check versions:

```bash
kubeadm version
kubelet --version
kubectl version --client
```

---

## Exercise 4: Set Hostnames

Perform on respective nodes.

### Step 1: Set Master Node Hostname

On the **master node**:

```bash
sudo hostnamectl set-hostname master.example.com
```

### Step 2: Set Worker Node Hostnames

On **worker node 1**:

```bash
sudo hostnamectl set-hostname worker-node-1.example.com
```

On **worker node 2**:

```bash
sudo hostnamectl set-hostname worker-node-2.example.com
```

### Step 3: Verify Hostnames

On each node:

```bash
hostnamectl
```

Should show your new hostname.

### Step 4: Update /etc/hosts (Optional but Recommended)

Add all node IPs and hostnames to /etc/hosts on ALL nodes:

```bash
sudo nano /etc/hosts
```

Add entries like:
```
172.31.33.66    master.example.com
172.31.35.22    worker-node-1.example.com
172.31.40.18    worker-node-2.example.com
```

---

## Exercise 5: Reset Previous Configuration (If Needed)

If this is not a fresh system, reset any existing Kubernetes configuration.

**⚠️ WARNING**: This destroys existing cluster data!

On **ALL nodes** (if needed):

```bash
sudo kubeadm reset -f
sudo rm -rf /etc/cni/net.d
sudo rm -rf $HOME/.kube/config
```

---

## Exercise 6: Initialize Control Plane

Perform **ONLY on the MASTER node**.

### Step 1: Initialize the Cluster

Run kubeadm init with pod network CIDR:

```bash
sudo kubeadm init --pod-network-cidr=192.168.0.0/16 --ignore-preflight-errors=all
```

**Understanding the flags:**
- `--pod-network-cidr=192.168.0.0/16` - Required for Calico CNI
- `--ignore-preflight-errors=all` - Ignores non-critical warnings

**This will take 2-5 minutes. Wait for completion!**

### Step 2: Save the Join Command

At the end of the output, you'll see:

```bash
kubeadm join 172.31.33.66:6443 --token qg5kgy.o1ov92iu7d50dkye \
    --discovery-token-ca-cert-hash sha256:e3f0feef4ad831253c3535f72e17c3bddc0c631e789c621f7a130e7e798aa313
```

**⚠️ IMPORTANT**: Copy this entire command! You'll need it to join worker nodes.

### Step 3: Configure kubectl for Regular User

Still on the **master node**, run:

```bash
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config
```

**What this does:**
- Creates `.kube` directory in your home folder
- Copies admin kubeconfig to your user directory
- Sets proper ownership so you can run kubectl without sudo

### Step 4: Verify Control Plane

Check nodes (will show NotReady until CNI is installed):

```bash
kubectl get nodes
```

Expected output:
```
NAME                 STATUS     ROLES           AGE   VERSION
master.example.com   NotReady   control-plane   1m    v1.29.x
```

Check system pods:

```bash
kubectl get pods -n kube-system
```

You should see several pods, but CoreDNS will be Pending until networking is configured.

---

## Exercise 7: Install Network Plugin (Calico)

Perform **ONLY on the MASTER node**.

### Step 1: Apply Calico Manifest

```bash
kubectl apply -f https://docs.projectcalico.org/manifests/calico.yaml
```

Expected output:
```
configmap/calico-config created
customresourcedefinition.apiextensions.k8s.io/bgpconfigurations.crd.projectcalico.org created
customresourcedefinition.apiextensions.k8s.io/bgppeers.crd.projectcalico.org created
...
daemonset.apps/calico-node created
deployment.apps/calico-kube-controllers created
```

### Step 2: Watch Pods Come Up

Monitor pod status:

```bash
kubectl get pods -n kube-system -w
```

Wait until all pods show `Running`. Press `Ctrl+C` to exit watch mode.

### Step 3: Verify Master Node is Ready

```bash
kubectl get nodes
```

Expected output:
```
NAME                 STATUS   ROLES           AGE   VERSION
master.example.com   Ready    control-plane   5m    v1.29.x
```

**The STATUS should now be "Ready"!**

---

## Exercise 8: Join Worker Nodes

Perform on **EACH WORKER NODE**.

### Step 1: Run the Join Command

Use the join command you saved from Exercise 6, Step 2.

On **each worker node**, run:

```bash
sudo kubeadm join 172.31.33.66:6443 --token qg5kgy.o1ov92iu7d50dkye \
    --discovery-token-ca-cert-hash sha256:e3f0feef4ad831253c3535f72e17c3bddc0c631e789c621f7a130e7e798aa313
```

(Use YOUR actual command, not this example!)

Expected output:
```
[preflight] Running pre-flight checks
[preflight] Reading configuration from the cluster...
[preflight] FYI: You can look at this config file with 'kubectl -n kube-system get cm kubeadm-config -o yaml'
[kubelet-start] Writing kubelet configuration to file "/var/lib/kubelet/config.yaml"
[kubelet-start] Writing kubelet environment file with flags to file "/var/lib/kubelet/kubeadm-flags.env"
[kubelet-start] Starting the kubelet
[kubelet-start] Waiting for the kubelet to perform the TLS Bootstrap...

This node has joined the cluster:
* Certificate signing request was sent to apiserver and a response was received.
* The Kubelet was informed of the new secure connection details.

Run 'kubectl get nodes' on the control-plane to see this node join the cluster.
```

### Step 2: Verify from Master Node

Back on the **master node**, check all nodes:

```bash
kubectl get nodes
```

Expected output:
```
NAME                        STATUS   ROLES           AGE   VERSION
master.example.com          Ready    control-plane   10m   v1.29.x
worker-node-1.example.com   Ready    <none>          2m    v1.29.x
worker-node-2.example.com   Ready    <none>          1m    v1.29.x
```

All nodes should show `Ready` status!

---

## Exercise 9: Verify Cluster Functionality

Perform on the **MASTER node**.

### Step 1: Deploy a Test Application

Create an nginx deployment:

```bash
kubectl create deployment nginx --image=nginx
```

Expected output:
```
deployment.apps/nginx created
```

### Step 2: Check Deployment Status

```bash
kubectl get deployments
```

Expected output:
```
NAME    READY   UP-TO-DATE   AVAILABLE   AGE
nginx   1/1     1            1           30s
```

Check pods:

```bash
kubectl get pods -o wide
```

You should see the nginx pod running on one of your nodes.

### Step 3: Expose the Deployment

Create a NodePort service:

```bash
kubectl expose deployment nginx --port=80 --type=NodePort
```

Expected output:
```
service/nginx exposed
```

### Step 4: Get Service Details

```bash
kubectl get svc nginx
```

Expected output:
```
NAME    TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
nginx   NodePort   10.96.100.200   <none>        80:30123/TCP   10s
```

Note the NodePort (30123 in this example).

### Step 5: Test Access

Get any node's IP:

```bash
kubectl get nodes -o wide
```

Test nginx (replace with your node IP and NodePort):

```bash
curl http://<node-ip>:30123
```

You should see the nginx welcome page HTML!

---

## Exercise 10: Cluster Inspection

### Step 1: List All Resources

View all resources across all namespaces:

```bash
kubectl get all -A
```

### Step 2: Check System Pod Health

```bash
kubectl get pods -n kube-system
```

All pods should be `Running`:
```
NAME                                       READY   STATUS    RESTARTS   AGE
calico-kube-controllers-5b644bc49c-xyz     1/1     Running   0          10m
calico-node-abc12                          1/1     Running   0          10m
calico-node-def34                          1/1     Running   0          5m
calico-node-ghi56                          1/1     Running   0          4m
coredns-787d4945fb-jkl78                   1/1     Running   0          15m
coredns-787d4945fb-mno90                   1/1     Running   0          15m
etcd-master.example.com                    1/1     Running   0          15m
kube-apiserver-master.example.com          1/1     Running   0          15m
kube-controller-manager-master             1/1     Running   0          15m
kube-proxy-pqr12                           1/1     Running   0          15m
kube-proxy-stu34                           1/1     Running   0          5m
kube-proxy-vwx56                           1/1     Running   0          4m
kube-scheduler-master.example.com          1/1     Running   0          15m
```

### Step 3: Check Cluster Info

```bash
kubectl cluster-info
```

Expected output:
```
Kubernetes control plane is running at https://172.31.33.66:6443
CoreDNS is running at https://172.31.33.66:6443/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy
```

---

## Lab Cleanup

To clean up the test deployment:

```bash
# Delete nginx service and deployment
kubectl delete service nginx
kubectl delete deployment nginx

# Verify cleanup
kubectl get all
```

**To completely remove the cluster** (⚠️ DESTRUCTIVE):

```bash
# On all nodes:
sudo kubeadm reset -f
sudo rm -rf /etc/cni/net.d
sudo rm -rf $HOME/.kube/config
```

---

## Key Takeaways

1. **System preparation** is critical - disable swap, load kernel modules
2. **Container runtime** must be configured before Kubernetes installation
3. **kubeadm init** only on master node
4. **CNI plugin** is required for pod networking
5. **Join tokens** authenticate worker nodes
6. **Verification** at each step prevents troubleshooting later
7. **NodePort services** expose applications externally

---

## Troubleshooting Guide

### Issue: Worker node not joining

**Symptoms**: Join command fails or times out

**Solutions**:
```bash
# Check connectivity from worker to master on port 6443
telnet 172.31.33.66 6443

# Check firewall (on master)
sudo ufw status
sudo ufw allow 6443/tcp

# Regenerate token if expired
sudo kubeadm token create --print-join-command
```

### Issue: Pods stuck in Pending

**Symptoms**: Pods never start after deployment

**Solutions**:
```bash
# Check if CNI is installed
kubectl get pods -n kube-system | grep calico

# Reapply Calico
kubectl apply -f https://docs.projectcalico.org/manifests/calico.yaml

# Check node resources
kubectl describe nodes
```

### Issue: kubectl not working

**Symptoms**: `The connection to the server localhost:8080 was refused`

**Solutions**:
```bash
# Reconfigure kubectl
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config

# Verify
kubectl get nodes
```

### Issue: CoreDNS pods in CrashLoopBackOff

**Symptoms**: DNS pods constantly restarting

**Solutions**:
```bash
# Check kubelet logs
sudo journalctl -u kubelet -f

# Verify SystemdCgroup is enabled in containerd
grep SystemdCgroup /etc/containerd/config.toml

# Restart containerd
sudo systemctl restart containerd
```

### Issue: Swap is not disabled

**Symptoms**: kubeadm refuses to start

**Solutions**:
```bash
# Disable swap temporarily
sudo swapoff -a

# Disable permanently
sudo sed -i '/ swap / s/^/#/' /etc/fstab

# Verify
free -h
```

---

## Port Requirements

Ensure these ports are open:

### Master Node (Control Plane)
- **6443**: Kubernetes API server
- **2379-2380**: etcd server client API
- **10250**: Kubelet API
- **10259**: kube-scheduler
- **10257**: kube-controller-manager

### Worker Nodes
- **10250**: Kubelet API
- **30000-32767**: NodePort Services

### All Nodes
- **179**: Calico BGP (if using BGP)
- **4789**: Calico VXLAN (if using VXLAN)

---

## Next Steps

Now that you have a working cluster:

1. Complete the earlier labs (Lab 01-05) to practice on your new cluster
2. Explore advanced topics:
   - Persistent Storage with PersistentVolumes
   - Ingress Controllers for HTTP routing
   - RBAC for security
   - Monitoring with Prometheus
   - Logging with EFK stack

---

## Additional Resources

- [Official kubeadm Installation Guide](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/install-kubeadm/)
- [Creating a cluster with kubeadm](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/create-cluster-kubeadm/)
- [Calico Documentation](https://docs.projectcalico.org/)
- [Container Runtime Setup](https://kubernetes.io/docs/setup/production-environment/container-runtimes/)

---

**Lab Created**: March 2026
**Compatible with**: Kubernetes 1.24+
**Based on**: labs/installation/install.md
**Tested on**: Ubuntu 20.04, Ubuntu 22.04
**Estimated Time**: 60-90 minutes
