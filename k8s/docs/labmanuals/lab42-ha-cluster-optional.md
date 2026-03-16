# Lab 42: High Availability Kubernetes Cluster (Optional Advanced Lab)

## Overview

**IMPORTANT: This is an OPTIONAL ADVANCED LAB** - This lab covers advanced High Availability (HA) concepts that go beyond basic Kubernetes knowledge required for CKA certification. While understanding HA principles is valuable for production environments, setting up HA clusters is typically not tested in depth on the CKA exam.

In this lab, you will learn how to design and set up a highly available Kubernetes cluster with multiple control plane nodes, load balancers, and etcd clustering. This lab is intended for those pursuing production Kubernetes deployments or advanced learning goals.

**Who should complete this lab:**
- Production platform engineers
- Site reliability engineers (SREs)
- Advanced learners interested in HA architectures
- Those preparing for production deployments

**You can skip this lab if:**
- You're focused solely on CKA exam preparation
- You're learning basic Kubernetes concepts
- You don't manage production clusters

## Prerequisites

- Strong understanding of Kubernetes architecture
- Completion of Labs 1-6 (especially Lab 6: Kubernetes Installation)
- At least 3 Linux nodes (VMs or bare metal) with 2 CPU cores and 4GB RAM each
- Knowledge of load balancing concepts
- Understanding of distributed systems concepts
- Familiarity with etcd basics
- Root or sudo access on all nodes
- Network connectivity between all nodes

## Learning Objectives

By the end of this lab, you will be able to:
- Understand why and when High Availability is needed
- Design HA Kubernetes architecture topologies
- Set up a load balancer for Kubernetes API servers
- Initialize a multi-control-plane Kubernetes cluster
- Configure stacked vs external etcd architectures
- Join additional control plane and worker nodes
- Verify HA functionality and health
- Test failover scenarios
- Apply production-ready considerations
- Evaluate cost vs benefit of HA setups

---

## Understanding High Availability in Kubernetes

### What is High Availability?

**High Availability (HA)** in Kubernetes refers to a cluster architecture that eliminates single points of failure by running multiple instances of critical components:

- **Multiple Control Plane Nodes** - API servers, schedulers, and controller managers
- **Load Balancer** - Distributes API requests across control plane nodes
- **Clustered etcd** - Distributed key-value store with data replication

### Why High Availability?

**Production Requirements:**
- **Zero downtime** - Maintenance without service interruption
- **Fault tolerance** - Survive node failures
- **Disaster recovery** - Quick recovery from failures
- **SLA compliance** - Meet uptime requirements (99.9%, 99.99%)
- **Business continuity** - Critical workloads must remain available

**Use Cases:**
- Production environments with strict SLAs
- Mission-critical applications
- 24/7 operations
- Regulated industries (finance, healthcare)
- Multi-tenant platforms

### When is HA NOT Needed?

**Skip HA for:**
- Development and testing environments
- Learning and experimentation
- Non-critical workloads
- Cost-sensitive deployments
- Small-scale deployments
- Single-team projects

**Trade-offs:**
- **Cost** - 3x or more infrastructure costs
- **Complexity** - More components to manage and troubleshoot
- **Operational overhead** - More monitoring, maintenance, and expertise required

---

## High Availability Architecture

### Architecture Overview

```
                    ┌─────────────────┐
                    │  Load Balancer  │
                    │  (HAProxy/NGINX)│
                    │   VIP: 10.0.0.10│
                    └────────┬────────┘
                             │
            ┌────────────────┼────────────────┐
            │                │                │
            │                │                │
     ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐
     │ Control      │  │ Control      │  │ Control      │
     │ Plane 1      │  │ Plane 2      │  │ Plane 3      │
     │              │  │              │  │              │
     │ API Server   │  │ API Server   │  │ API Server   │
     │ Scheduler    │  │ Scheduler    │  │ Scheduler    │
     │ Controller   │  │ Controller   │  │ Controller   │
     │              │  │              │  │              │
     │ ┌──────────┐ │  │ ┌──────────┐ │  │ ┌──────────┐ │
     │ │   etcd   │◄├──┼─┤   etcd   │◄├──┼─┤   etcd   │ │
     │ └──────────┘ │  │ └──────────┘ │  │ └──────────┘ │
     └──────────────┘  └──────────────┘  └──────────────┘
            │                │                │
            └────────────────┼────────────────┘
                             │
            ┌────────────────┼────────────────┐
            │                │                │
     ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐
     │   Worker 1   │  │   Worker 2   │  │   Worker 3   │
     │              │  │              │  │              │
     │   kubelet    │  │   kubelet    │  │   kubelet    │
     │   kube-proxy │  │   kube-proxy │  │   kube-proxy │
     │   Container  │  │   Container  │  │   Container  │
     │   Runtime    │  │   Runtime    │  │   Runtime    │
     └──────────────┘  └──────────────┘  └──────────────┘
```

### Stacked etcd Topology

**Stacked etcd** runs etcd on the same nodes as control plane components:

**Advantages:**
- Simpler setup and management
- Fewer nodes required (minimum 3)
- Lower infrastructure costs
- Easier to maintain

**Disadvantages:**
- Control plane and etcd share resources
- Node failure affects both control plane and etcd
- Less isolation between components

**Recommended for:**
- Most production deployments
- Cost-conscious HA setups
- Smaller to medium-scale clusters

### External etcd Topology

**External etcd** runs etcd on dedicated nodes separate from control plane:

```
     ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
     │   etcd 1     │  │   etcd 2     │  │   etcd 3     │
     └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
            │                 │                 │
            └─────────────────┼─────────────────┘
                              │
            ┌─────────────────┼─────────────────┐
            │                 │                 │
     ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐
     │ Control      │  │ Control      │  │ Control      │
     │ Plane 1      │  │ Plane 2      │  │ Plane 3      │
     │ (No etcd)    │  │ (No etcd)    │  │ (No etcd)    │
     └──────────────┘  └──────────────┘  └──────────────┘
```

**Advantages:**
- Better resource isolation
- Independent scaling of etcd
- Higher fault tolerance
- Better for large clusters (1000+ nodes)

**Disadvantages:**
- More complex setup
- Requires 6+ nodes minimum (3 etcd + 3 control plane)
- Higher infrastructure costs
- More operational complexity

**Recommended for:**
- Large-scale deployments
- Critical production environments
- When maximum reliability is required

---

## Exercise 1: Plan Your HA Architecture

### Step 1: Choose Your Topology

**For this lab, we'll use the Stacked etcd Topology** as it's more practical for most use cases.

**Infrastructure Requirements:**

| Component | Minimum | Recommended | Purpose |
|-----------|---------|-------------|---------|
| Control Plane Nodes | 3 | 3 or 5 | Odd numbers for etcd quorum |
| Worker Nodes | 2 | 3+ | Run workloads |
| Load Balancer | 1 | 2 (HA LB) | API server endpoint |
| CPU per node | 2 cores | 4 cores | Control plane needs |
| RAM per node | 4 GB | 8 GB | etcd and components |
| Network | 1 Gbps | 10 Gbps | Inter-node communication |

### Step 2: Network Planning

**IP Address Allocation:**

For this lab, we'll use the following example:

```
Load Balancer VIP:    10.0.0.10   (Virtual IP for API server)

Control Plane Nodes:
  cp1:                10.0.0.11   (controlplane1.example.com)
  cp2:                10.0.0.12   (controlplane2.example.com)
  cp3:                10.0.0.13   (controlplane3.example.com)

Worker Nodes:
  worker1:            10.0.0.21   (worker1.example.com)
  worker2:            10.0.0.22   (worker2.example.com)
  worker3:            10.0.0.23   (worker3.example.com)
```

**Port Requirements:**

| Component | Port | Protocol | Purpose |
|-----------|------|----------|---------|
| API Server | 6443 | TCP | Kubernetes API |
| etcd client | 2379 | TCP | etcd client API |
| etcd peer | 2380 | TCP | etcd peer communication |
| Kubelet | 10250 | TCP | Kubelet API |
| Scheduler | 10259 | TCP | Scheduler health check |
| Controller Manager | 10257 | TCP | Controller health check |

### Step 3: Design Decisions Checklist

Before starting, answer these questions:

- [ ] Have I provisioned at least 3 control plane nodes?
- [ ] Do I have a load balancer solution (HAProxy, NGINX, cloud LB)?
- [ ] Have I configured DNS or /etc/hosts for all nodes?
- [ ] Are all required ports open in firewalls?
- [ ] Do I have root/sudo access to all nodes?
- [ ] Have I disabled swap on all nodes?
- [ ] Is container runtime installed on all nodes?
- [ ] Have I synchronized time across all nodes (NTP)?

---

## Exercise 2: Set Up the Load Balancer

### Why a Load Balancer?

The load balancer provides:
- **Single endpoint** - Clients connect to one stable address
- **High availability** - Routes to healthy API servers only
- **Load distribution** - Spreads requests across control planes
- **Health checking** - Detects and excludes failed API servers

### Option A: HAProxy (Recommended for this lab)

**Step 1: Install HAProxy**

On a dedicated node or one of the control plane nodes (for demo):

```bash
# On Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y haproxy

# On RHEL/CentOS
sudo yum install -y haproxy
```

**Step 2: Configure HAProxy**

Create the configuration file:

```bash
sudo tee /etc/haproxy/haproxy.cfg > /dev/null <<EOF
global
    log /dev/log    local0
    log /dev/log    local1 notice
    chroot /var/lib/haproxy
    stats socket /run/haproxy/admin.sock mode 660 level admin
    stats timeout 30s
    user haproxy
    group haproxy
    daemon

defaults
    log     global
    mode    tcp
    option  tcplog
    option  dontlognull
    timeout connect 5000
    timeout client  50000
    timeout server  50000

# Frontend for Kubernetes API Server
frontend kubernetes-api
    bind *:6443
    mode tcp
    option tcplog
    default_backend kubernetes-api-backend

# Backend for Kubernetes API Servers
backend kubernetes-api-backend
    mode tcp
    balance roundrobin
    option tcp-check
    # Health check: TCP connection to port 6443
    tcp-check connect port 6443
    default-server inter 10s downinter 5s rise 2 fall 2 slowstart 60s maxconn 250 maxqueue 256 weight 100

    # Add control plane nodes
    server cp1 10.0.0.11:6443 check
    server cp2 10.0.0.12:6443 check
    server cp3 10.0.0.13:6443 check

# Optional: Stats page
listen stats
    bind *:8404
    mode http
    stats enable
    stats uri /stats
    stats refresh 30s
    stats admin if TRUE
EOF
```

**Understanding the Configuration:**

- `frontend kubernetes-api` - Listens on port 6443
- `backend kubernetes-api-backend` - Defines backend API servers
- `balance roundrobin` - Distributes requests evenly
- `option tcp-check` - Health checks via TCP connection
- `inter 10s` - Health check every 10 seconds
- `rise 2 fall 2` - 2 successful/failed checks to change state

**Step 3: Start and Enable HAProxy**

```bash
# Test configuration
sudo haproxy -c -f /etc/haproxy/haproxy.cfg

# Start HAProxy
sudo systemctl start haproxy
sudo systemctl enable haproxy

# Check status
sudo systemctl status haproxy
```

**Step 4: Verify Load Balancer**

Check HAProxy stats page:

```bash
# From any node with browser access
http://<load-balancer-ip>:8404/stats
```

Or check with netcat:

```bash
nc -v <load-balancer-ip> 6443
```

### Option B: NGINX

**Step 1: Install NGINX**

```bash
# On Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y nginx

# On RHEL/CentOS
sudo yum install -y nginx
```

**Step 2: Configure NGINX**

```bash
sudo tee /etc/nginx/nginx.conf > /dev/null <<EOF
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log;
pid /run/nginx.pid;

events {
    worker_connections 1024;
}

stream {
    upstream kubernetes {
        server 10.0.0.11:6443 max_fails=3 fail_timeout=30s;
        server 10.0.0.12:6443 max_fails=3 fail_timeout=30s;
        server 10.0.0.13:6443 max_fails=3 fail_timeout=30s;
    }

    server {
        listen 6443;
        proxy_pass kubernetes;
        proxy_timeout 10m;
        proxy_connect_timeout 1s;
    }
}
EOF
```

**Step 3: Start NGINX**

```bash
sudo systemctl start nginx
sudo systemctl enable nginx
sudo systemctl status nginx
```

### Step 5: Configure DNS or Hosts File

On **ALL nodes** (control plane and workers):

```bash
sudo tee -a /etc/hosts > /dev/null <<EOF
10.0.0.10   k8s-api.example.com
10.0.0.11   controlplane1.example.com cp1
10.0.0.12   controlplane2.example.com cp2
10.0.0.13   controlplane3.example.com cp3
10.0.0.21   worker1.example.com worker1
10.0.0.22   worker2.example.com worker2
10.0.0.23   worker3.example.com worker3
EOF
```

---

## Exercise 3: Prepare All Nodes

Perform these steps on **ALL nodes** (control plane and workers):

### Step 1: Disable Swap

```bash
sudo swapoff -a
sudo sed -i '/ swap / s/^\(.*\)$/#\1/g' /etc/fstab
```

### Step 2: Load Kernel Modules

```bash
cat <<EOF | sudo tee /etc/modules-load.d/k8s.conf
overlay
br_netfilter
EOF

sudo modprobe overlay
sudo modprobe br_netfilter
```

### Step 3: Configure sysctl

```bash
cat <<EOF | sudo tee /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward                 = 1
EOF

sudo sysctl --system
```

### Step 4: Install Container Runtime (containerd)

```bash
# Install containerd
sudo apt-get update
sudo apt-get install -y containerd

# Configure containerd
sudo mkdir -p /etc/containerd
containerd config default | sudo tee /etc/containerd/config.toml

# Set systemd as cgroup driver
sudo sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml

# Restart containerd
sudo systemctl restart containerd
sudo systemctl enable containerd
```

### Step 5: Install kubeadm, kubelet, kubectl

```bash
# Add Kubernetes apt repository
sudo apt-get update
sudo apt-get install -y apt-transport-https ca-certificates curl gpg

curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.29/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg

echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.29/deb/ /' | sudo tee /etc/apt/sources.list.d/kubernetes.list

# Install packages
sudo apt-get update
sudo apt-get install -y kubelet kubeadm kubectl
sudo apt-mark hold kubelet kubeadm kubectl

# Enable kubelet
sudo systemctl enable kubelet
```

### Step 6: Configure Firewall (if enabled)

On **control plane nodes**:

```bash
sudo ufw allow 6443/tcp      # API server
sudo ufw allow 2379:2380/tcp # etcd
sudo ufw allow 10250/tcp     # Kubelet
sudo ufw allow 10259/tcp     # Scheduler
sudo ufw allow 10257/tcp     # Controller Manager
```

On **worker nodes**:

```bash
sudo ufw allow 10250/tcp     # Kubelet
sudo ufw allow 30000:32767/tcp # NodePort services
```

---

## Exercise 4: Initialize the First Control Plane Node

### Step 1: Create kubeadm Configuration

On **the first control plane node (cp1)**, create the configuration:

```bash
cat <<EOF > kubeadm-config.yaml
apiVersion: kubeadm.k8s.io/v1beta3
kind: ClusterConfiguration
kubernetesVersion: v1.29.0
# Load balancer endpoint
controlPlaneEndpoint: "k8s-api.example.com:6443"
networking:
  podSubnet: "10.244.0.0/16"
  serviceSubnet: "10.96.0.0/12"
etcd:
  local:
    # External etcd example (comment out for stacked)
    # external:
    #   endpoints:
    #     - https://10.0.0.31:2379
    #     - https://10.0.0.32:2379
    #     - https://10.0.0.33:2379
    #   caFile: /etc/kubernetes/pki/etcd/ca.crt
    #   certFile: /etc/kubernetes/pki/apiserver-etcd-client.crt
    #   keyFile: /etc/kubernetes/pki/apiserver-etcd-client.key
---
apiVersion: kubeadm.k8s.io/v1beta3
kind: InitConfiguration
localAPIEndpoint:
  advertiseAddress: "10.0.0.11"
  bindPort: 6443
nodeRegistration:
  criSocket: unix:///var/run/containerd/containerd.sock
  taints:
    - key: node-role.kubernetes.io/control-plane
      effect: NoSchedule
EOF
```

**Understanding the Configuration:**

- `controlPlaneEndpoint` - Load balancer address (CRITICAL for HA)
- `podSubnet` - Network range for Pods
- `advertiseAddress` - This control plane node's IP
- `etcd.local` - Uses stacked etcd topology

### Step 2: Initialize the Cluster

```bash
sudo kubeadm init --config=kubeadm-config.yaml --upload-certs
```

**IMPORTANT**: Save the output! You'll need:
1. **Control plane join command** with certificate key
2. **Worker node join command**

Example output:

```
Your Kubernetes control-plane has initialized successfully!

To start using your cluster, you need to run the following as a regular user:

  mkdir -p $HOME/.kube
  sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
  sudo chown $(id -u):$(id -g) $HOME/.kube/config

You can now join any number of control-plane nodes by copying certificate authorities
and service account keys on each node and then running the following as root:

  kubeadm join k8s-api.example.com:6443 --token abc123.xyz987 \
    --discovery-token-ca-cert-hash sha256:1234567890abcdef... \
    --control-plane --certificate-key fedcba0987654321...

Then you can join any number of worker nodes by running the following on each as root:

  kubeadm join k8s-api.example.com:6443 --token abc123.xyz987 \
    --discovery-token-ca-cert-hash sha256:1234567890abcdef...
```

### Step 3: Configure kubectl for Regular User

On **cp1**:

```bash
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config
```

### Step 4: Install a Pod Network (CNI)

Install Calico for networking:

```bash
kubectl apply -f https://raw.githubusercontent.com/projectcalico/calico/v3.27.0/manifests/calico.yaml
```

Or install Flannel:

```bash
kubectl apply -f https://github.com/flannel-io/flannel/releases/latest/download/kube-flannel.yml
```

### Step 5: Verify First Control Plane

```bash
kubectl get nodes
```

Expected output:

```
NAME   STATUS   ROLES           AGE   VERSION
cp1    Ready    control-plane   2m    v1.29.0
```

Check component status:

```bash
kubectl get pods -n kube-system
```

All pods should be Running:

```
NAME                          READY   STATUS    RESTARTS   AGE
calico-node-xxxxx             1/1     Running   0          1m
coredns-xxxxx                 1/1     Running   0          2m
etcd-cp1                      1/1     Running   0          2m
kube-apiserver-cp1            1/1     Running   0          2m
kube-controller-manager-cp1   1/1     Running   0          2m
kube-scheduler-cp1            1/1     Running   0          2m
```

---

## Exercise 5: Join Additional Control Plane Nodes

### Step 1: Verify Certificate Key is Valid

The `--certificate-key` from kubeadm init is valid for 2 hours. If expired, regenerate:

```bash
# On cp1
sudo kubeadm init phase upload-certs --upload-certs
```

### Step 2: Join Second Control Plane (cp2)

On **cp2**, run the control plane join command from Exercise 4:

```bash
sudo kubeadm join k8s-api.example.com:6443 --token abc123.xyz987 \
  --discovery-token-ca-cert-hash sha256:1234567890abcdef... \
  --control-plane --certificate-key fedcba0987654321... \
  --apiserver-advertise-address 10.0.0.12
```

**Note**: Add `--apiserver-advertise-address` with this node's IP.

Expected output:

```
This node has joined the cluster and a new control plane instance was created:

* Certificate signing request was sent to apiserver and approval was received.
* The Kubelet was informed of the new secure connection details.
* Control plane label and taint were applied to the new node.
* The Kubernetes control plane instances scaled up.
* A new etcd member was added to the local/stacked etcd cluster.
```

### Step 3: Configure kubectl on cp2

```bash
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config
```

### Step 4: Verify Second Control Plane

From **cp1 or cp2**:

```bash
kubectl get nodes
```

Expected output:

```
NAME   STATUS   ROLES           AGE   VERSION
cp1    Ready    control-plane   5m    v1.29.0
cp2    Ready    control-plane   1m    v1.29.0
```

Check etcd members:

```bash
sudo kubectl exec -n kube-system etcd-cp1 -- etcdctl \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  member list
```

Expected output (2 members):

```
abc123, started, cp1, https://10.0.0.11:2380, https://10.0.0.11:2379, false
def456, started, cp2, https://10.0.0.12:2380, https://10.0.0.12:2379, false
```

### Step 5: Join Third Control Plane (cp3)

Repeat Step 2 on **cp3**:

```bash
sudo kubeadm join k8s-api.example.com:6443 --token abc123.xyz987 \
  --discovery-token-ca-cert-hash sha256:1234567890abcdef... \
  --control-plane --certificate-key fedcba0987654321... \
  --apiserver-advertise-address 10.0.0.13
```

Configure kubectl:

```bash
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config
```

### Step 6: Verify All Control Planes

```bash
kubectl get nodes
```

Expected output:

```
NAME   STATUS   ROLES           AGE   VERSION
cp1    Ready    control-plane   10m   v1.29.0
cp2    Ready    control-plane   6m    v1.29.0
cp3    Ready    control-plane   2m    v1.29.0
```

Check etcd cluster has 3 members:

```bash
sudo kubectl exec -n kube-system etcd-cp1 -- etcdctl \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  member list -w table
```

Expected output:

```
+------------------+---------+------+---------------------------+---------------------------+------------+
|        ID        | STATUS  | NAME |        PEER ADDRS         |       CLIENT ADDRS        | IS LEARNER |
+------------------+---------+------+---------------------------+---------------------------+------------+
| abc123           | started | cp1  | https://10.0.0.11:2380    | https://10.0.0.11:2379    |      false |
| def456           | started | cp2  | https://10.0.0.12:2380    | https://10.0.0.12:2379    |      false |
| ghi789           | started | cp3  | https://10.0.0.13:2380    | https://10.0.0.13:2379    |      false |
+------------------+---------+------+---------------------------+---------------------------+------------+
```

**Success!** You now have a 3-node control plane with clustered etcd.

---

## Exercise 6: Join Worker Nodes

### Step 1: Join First Worker

On **worker1**, run the worker join command from Exercise 4:

```bash
sudo kubeadm join k8s-api.example.com:6443 --token abc123.xyz987 \
  --discovery-token-ca-cert-hash sha256:1234567890abcdef...
```

Expected output:

```
This node has joined the cluster:
* Certificate signing request was sent to apiserver and a response was received.
* The Kubelet was informed of the new secure connection details.
```

### Step 2: Join Remaining Workers

Repeat on **worker2** and **worker3**:

```bash
sudo kubeadm join k8s-api.example.com:6443 --token abc123.xyz987 \
  --discovery-token-ca-cert-hash sha256:1234567890abcdef...
```

### Step 3: Verify All Nodes

From any control plane node:

```bash
kubectl get nodes -o wide
```

Expected output:

```
NAME      STATUS   ROLES           AGE   VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION      CONTAINER-RUNTIME
cp1       Ready    control-plane   15m   v1.29.0   10.0.0.11     <none>        Ubuntu 22.04.3 LTS   5.15.0-91-generic   containerd://1.7.12
cp2       Ready    control-plane   11m   v1.29.0   10.0.0.12     <none>        Ubuntu 22.04.3 LTS   5.15.0-91-generic   containerd://1.7.12
cp3       Ready    control-plane   7m    v1.29.0   10.0.0.13     <none>        Ubuntu 22.04.3 LTS   5.15.0-91-generic   containerd://1.7.12
worker1   Ready    <none>          3m    v1.29.0   10.0.0.21     <none>        Ubuntu 22.04.3 LTS   5.15.0-91-generic   containerd://1.7.12
worker2   Ready    <none>          2m    v1.29.0   10.0.0.22     <none>        Ubuntu 22.04.3 LTS   5.15.0-91-generic   containerd://1.7.12
worker3   Ready    <none>          1m    v1.29.0   10.0.0.23     <none>        Ubuntu 22.04.3 LTS   5.15.0-91-generic   containerd://1.7.12
```

### Step 4: Token Management (if needed)

If the join token expired (24 hours default), generate a new one:

```bash
# Generate new token
kubeadm token create --print-join-command
```

This outputs a complete join command you can use.

---

## Exercise 7: Verify HA Functionality

### Step 1: Check API Server Health

Test all API servers directly:

```bash
# Test cp1 API server
curl -k https://10.0.0.11:6443/healthz

# Test cp2 API server
curl -k https://10.0.0.12:6443/healthz

# Test cp3 API server
curl -k https://10.0.0.13:6443/healthz
```

Expected output for each:

```
ok
```

Test through load balancer:

```bash
curl -k https://k8s-api.example.com:6443/healthz
```

### Step 2: Verify etcd Cluster Health

Check etcd health:

```bash
sudo kubectl exec -n kube-system etcd-cp1 -- etcdctl \
  --endpoints=https://10.0.0.11:2379,https://10.0.0.12:2379,https://10.0.0.13:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  endpoint health
```

Expected output:

```
https://10.0.0.11:2379 is healthy: successfully committed proposal: took = 1.234ms
https://10.0.0.12:2379 is healthy: successfully committed proposal: took = 1.567ms
https://10.0.0.13:2379 is healthy: successfully committed proposal: took = 1.890ms
```

Check etcd cluster status:

```bash
sudo kubectl exec -n kube-system etcd-cp1 -- etcdctl \
  --endpoints=https://10.0.0.11:2379,https://10.0.0.12:2379,https://10.0.0.13:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  endpoint status -w table
```

Expected output shows leader election:

```
+---------------------------+------------------+---------+---------+-----------+------------+-----------+------------+--------------------+--------+
|         ENDPOINT          |        ID        | VERSION | DB SIZE | IS LEADER | IS LEARNER | RAFT TERM | RAFT INDEX | RAFT APPLIED INDEX | ERRORS |
+---------------------------+------------------+---------+---------+-----------+------------+-----------+------------+--------------------+--------+
| https://10.0.0.11:2379    | abc123           | 3.5.10  |   20 kB |      true |      false |         2 |         10 |                 10 |        |
| https://10.0.0.12:2379    | def456           | 3.5.10  |   20 kB |     false |      false |         2 |         10 |                 10 |        |
| https://10.0.0.13:2379    | ghi789           | 3.5.10  |   20 kB |     false |      false |         2 |         10 |                 10 |        |
+---------------------------+------------------+---------+---------+-----------+------------+-----------+------------+--------------------+--------+
```

**Note**: One etcd member is the leader.

### Step 3: Deploy a Test Application

Deploy NGINX to verify cluster functionality:

```bash
kubectl create deployment nginx-ha-test --image=nginx:alpine --replicas=3
kubectl expose deployment nginx-ha-test --port=80 --type=NodePort
```

Verify deployment:

```bash
kubectl get pods -o wide
```

Expected output shows Pods distributed across workers:

```
NAME                             READY   STATUS    RESTARTS   AGE   IP           NODE      NOMINATED NODE   READINESS GATES
nginx-ha-test-xxxxxxxxxx-xxxxx   1/1     Running   0          30s   10.244.1.2   worker1   <none>           <none>
nginx-ha-test-xxxxxxxxxx-yyyyy   1/1     Running   0          30s   10.244.2.2   worker2   <none>           <none>
nginx-ha-test-xxxxxxxxxx-zzzzz   1/1     Running   0          30s   10.244.3.2   worker3   <none>           <none>
```

### Step 4: Test kubectl Through Load Balancer

Verify kubectl uses the load balancer endpoint:

```bash
kubectl config view | grep server
```

Expected output:

```
    server: https://k8s-api.example.com:6443
```

Test API access:

```bash
kubectl get nodes
kubectl get pods --all-namespaces
kubectl cluster-info
```

All commands should work normally.

---

## Exercise 8: Test Failover Scenarios

### Scenario 1: Control Plane Node Failure

**Step 1: Simulate Control Plane Failure**

On **cp2**, stop the kubelet:

```bash
# On cp2
sudo systemctl stop kubelet
```

Or power off the entire node:

```bash
# On cp2 (CAUTION)
sudo poweroff
```

**Step 2: Verify Cluster Still Works**

From your workstation or **cp1**:

```bash
# This should still work
kubectl get nodes
kubectl get pods
kubectl create deployment test-failover --image=nginx:alpine
```

**Observation**: The cluster continues to function! The load balancer routes to healthy API servers.

**Step 3: Check Node Status**

```bash
kubectl get nodes
```

Expected output:

```
NAME      STATUS     ROLES           AGE   VERSION
cp1       Ready      control-plane   30m   v1.29.0
cp2       NotReady   control-plane   25m   v1.29.0   # This node is down
cp3       Ready      control-plane   20m   v1.29.0
worker1   Ready      <none>          15m   v1.29.0
worker2   Ready      <none>          14m   v1.29.0
worker3   Ready      <none>          13m   v1.29.0
```

**Step 4: Check etcd Quorum**

Verify etcd still has quorum (2 out of 3):

```bash
sudo kubectl exec -n kube-system etcd-cp1 -- etcdctl \
  --endpoints=https://10.0.0.11:2379,https://10.0.0.13:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  endpoint health
```

Expected output:

```
https://10.0.0.11:2379 is healthy: successfully committed proposal: took = 1.234ms
https://10.0.0.13:2379 is healthy: successfully committed proposal: took = 1.890ms
```

**etcd quorum math:**
- 3 nodes: Can tolerate 1 failure (quorum = 2)
- 5 nodes: Can tolerate 2 failures (quorum = 3)
- Formula: quorum = (n/2) + 1

**Step 5: Restore Control Plane Node**

Restart **cp2**:

```bash
# On cp2
sudo systemctl start kubelet
```

Or power on the node if it was shut down.

Wait for the node to rejoin:

```bash
kubectl get nodes -w
```

After a few minutes:

```
NAME      STATUS   ROLES           AGE   VERSION
cp1       Ready    control-plane   35m   v1.29.0
cp2       Ready    control-plane   30m   v1.29.0   # Back to Ready!
cp3       Ready    control-plane   25m   v1.29.0
```

### Scenario 2: etcd Member Failure

**Step 1: Stop etcd on cp3**

```bash
# On cp3
sudo systemctl stop kubelet
```

**Step 2: Verify etcd Still Works**

```bash
sudo kubectl exec -n kube-system etcd-cp1 -- etcdctl \
  --endpoints=https://10.0.0.11:2379,https://10.0.0.12:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  endpoint health
```

Expected output (2 healthy):

```
https://10.0.0.11:2379 is healthy: successfully committed proposal: took = 1.234ms
https://10.0.0.12:2379 is healthy: successfully committed proposal: took = 1.567ms
```

Cluster operations continue normally!

**Step 3: Test CRITICAL Failure (DO NOT DO IN PRODUCTION)**

**WARNING**: This demonstrates etcd quorum loss - DO NOT test in production!

Stop TWO etcd members (cp2 and cp3):

```bash
# On cp2 and cp3 (DO NOT DO IN PRODUCTION)
sudo systemctl stop kubelet
```

**Result**: Cluster stops working! Only 1 etcd member (cp1) remains, which is less than quorum (2).

```bash
kubectl get nodes
```

Expected error:

```
The connection to the server k8s-api.example.com:6443 was refused
```

**Recovery**: Restart at least one control plane node to restore quorum:

```bash
# On cp2
sudo systemctl start kubelet
```

After a few moments, the cluster becomes operational again.

### Scenario 3: Load Balancer Failure

If the load balancer fails, kubectl and workers lose API access!

**Mitigation strategies:**
1. Use highly available load balancers (keepalived + HAProxy)
2. Use cloud load balancers (AWS ELB, GCP LB, Azure LB)
3. Configure multiple load balancer IPs in kubeconfig

### Scenario 4: Network Partition

Network partitions can split the cluster. With 3 control planes:
- 2 nodes in partition A → retains quorum, continues working
- 1 node in partition B → loses quorum, stops working

This is why odd numbers (3, 5, 7) are critical for etcd!

---

## Production Considerations

### 1. Infrastructure Planning

**Compute Resources:**
- Control plane: 2-4 CPU cores, 4-8 GB RAM minimum
- Scale up for large clusters (1000+ nodes)
- Monitor CPU/memory usage and adjust

**Network:**
- Low latency between control plane nodes (<10ms ideal)
- High bandwidth for etcd replication
- Separate management and data networks (advanced)

**Storage:**
- Fast SSD storage for etcd (critical!)
- Monitor etcd disk latency (< 10ms)
- Regular etcd backups (automated)

### 2. Load Balancer Best Practices

**High Availability:**
- Use redundant load balancers (keepalived, VRRP)
- Cloud load balancers (AWS NLB, GCP TCP LB)
- Health checks every 5-10 seconds
- Proper timeout configurations

**Security:**
- TLS termination (if applicable)
- Rate limiting and DDoS protection
- Firewall rules limiting access

### 3. etcd Best Practices

**Performance:**
- Dedicated fast SSDs (NVMe if possible)
- Monitor disk latency (etcd_disk_wal_fsync_duration_seconds)
- Avoid running etcd on same disk as logs

**Backups:**
- Automated daily etcd backups
- Store backups off-cluster
- Test restore procedures regularly

**Monitoring:**
- Alert on etcd latency spikes
- Monitor member health
- Watch for leader elections (should be rare)

### 4. Scaling Considerations

**Control Plane Scaling:**
- 3 control planes: Up to 100 nodes
- 5 control planes: Up to 500 nodes
- 5+ control planes: 500+ nodes (with external etcd)

**When to add more control planes:**
- API server CPU/memory consistently high
- Increased API request latency
- Scaling to more worker nodes

**When NOT to scale control plane:**
- More control planes ≠ more performance
- etcd quorum overhead increases with size
- Stick with 3 or 5 for most deployments

### 5. Disaster Recovery

**Backup Strategy:**
- Automate etcd snapshots (every 6-24 hours)
- Back up certificates and keys
- Document cluster configuration

**Restore Procedures:**
- Test etcd restore process
- Practice control plane recovery
- Maintain runbooks

### 6. Monitoring and Alerting

**Critical Metrics:**
- API server latency and availability
- etcd leader elections (should be rare)
- etcd disk latency and fsync duration
- Control plane CPU and memory usage
- Network latency between nodes

**Tools:**
- Prometheus + Grafana
- kube-state-metrics
- node-exporter
- etcd metrics

### 7. Security Hardening

**Control Plane Security:**
- Restrict API server access (firewall, network policies)
- Enable audit logging
- Rotate certificates regularly
- Use RBAC strictly
- Enable admission controllers (PSP, OPA)

**etcd Security:**
- Enable TLS for client and peer communication (default)
- Restrict etcd network access
- Encrypt etcd data at rest
- Regular security patches

### 8. Cost Analysis

**Infrastructure Costs:**

| Component | Minimum | Recommended | Monthly Cost (AWS) |
|-----------|---------|-------------|-------------------|
| Control Plane (3x) | 3 x t3.medium | 3 x t3.large | $50 - $150 |
| Load Balancer | 1 x ALB/NLB | 2 x ALB/NLB | $25 - $50 |
| etcd Storage | 3 x 20GB GP3 | 3 x 50GB GP3 | $15 - $30 |
| **Total** | - | - | **$90 - $230/month** |

**Plus worker nodes (actual workload costs).**

**Cost Optimization:**
- Use smaller control plane instances for small clusters
- Shared control plane + worker nodes (small deployments)
- Cloud spot/preemptible instances (NOT for production control plane)

### 9. When to Use External etcd

**Use stacked etcd (recommended) when:**
- Cluster size < 500 nodes
- Cost is a consideration
- Simpler operations preferred
- Team has limited distributed systems expertise

**Use external etcd when:**
- Cluster size > 500 nodes
- Maximum fault isolation required
- Dedicated etcd performance tuning needed
- Compliance requires separation

---

## Troubleshooting Guide

### Issue 1: Control Plane Join Fails

**Error**: "certificate key expired"

**Solution**:
```bash
# On cp1, regenerate certificate key
sudo kubeadm init phase upload-certs --upload-certs

# Use the new certificate key in join command
```

### Issue 2: etcd Cluster Not Forming

**Error**: etcd members not visible

**Solution**:
```bash
# Check etcd logs
sudo journalctl -u kubelet -f

# Verify firewall allows ports 2379, 2380
sudo ufw status

# Check etcd Pod status
kubectl get pods -n kube-system -l component=etcd
```

### Issue 3: Load Balancer Not Working

**Error**: Connection refused on port 6443

**Solution**:
```bash
# Check HAProxy status
sudo systemctl status haproxy

# Test backend servers
nc -zv 10.0.0.11 6443
nc -zv 10.0.0.12 6443
nc -zv 10.0.0.13 6443

# Check HAProxy logs
sudo tail -f /var/log/haproxy.log

# Verify HAProxy configuration
sudo haproxy -c -f /etc/haproxy/haproxy.cfg
```

### Issue 4: API Server Not Accessible

**Error**: "The connection to the server was refused"

**Solution**:
```bash
# Check API server is running
sudo systemctl status kubelet

# Check API server logs
sudo journalctl -u kubelet | grep apiserver

# Verify API server Pod
kubectl get pods -n kube-system -l component=kube-apiserver

# Check load balancer endpoint
curl -k https://k8s-api.example.com:6443/healthz
```

### Issue 5: etcd Quorum Lost

**Error**: "etcdserver: no leader"

**Solution**:
```bash
# Check how many etcd members are healthy
sudo kubectl exec -n kube-system etcd-cp1 -- etcdctl \
  --endpoints=https://10.0.0.11:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  member list

# Need at least (N/2)+1 healthy members
# For 3 nodes: need 2 healthy
# For 5 nodes: need 3 healthy

# Start stopped control plane nodes to restore quorum
```

### Issue 6: High etcd Latency

**Symptom**: Slow API operations, etcd disk latency alerts

**Solution**:
```bash
# Check etcd disk performance
sudo kubectl exec -n kube-system etcd-cp1 -- etcdctl \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  endpoint status -w table

# Defragment etcd database
sudo kubectl exec -n kube-system etcd-cp1 -- etcdctl \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  defrag

# Check disk I/O
iostat -x 1
```

---

## Lab Cleanup

**WARNING**: This will destroy your HA cluster!

### Option 1: Reset All Nodes

On **each node** (control planes and workers):

```bash
sudo kubeadm reset -f
sudo rm -rf /etc/cni/net.d
sudo rm -rf $HOME/.kube
sudo iptables -F && sudo iptables -t nat -F && sudo iptables -t mangle -F && sudo iptables -X
```

### Option 2: Destroy Infrastructure

If using VMs or cloud instances, simply delete them.

### Cleanup Load Balancer

```bash
# Stop and disable HAProxy
sudo systemctl stop haproxy
sudo systemctl disable haproxy

# Remove configuration
sudo rm /etc/haproxy/haproxy.cfg
```

---

## Key Takeaways

1. **High Availability eliminates single points of failure** but adds complexity and cost
2. **3 control plane nodes** is the sweet spot for most deployments
3. **Load balancer** is critical - it's the single entry point for API access
4. **etcd quorum** requires (N/2)+1 members - use odd numbers (3, 5, 7)
5. **Stacked etcd** is simpler and sufficient for most use cases
6. **External etcd** provides better isolation but requires more infrastructure
7. **Failover works automatically** - kubectl and workloads continue during node failures
8. **Monitor etcd health** - disk latency and leader elections are critical metrics
9. **Test failover regularly** - ensure your HA setup actually works
10. **HA is expensive** - evaluate if your use case justifies the cost and complexity

### HA is NOT Required For:
- Development and test environments
- Learning and certification prep (CKA focuses on single-node control plane)
- Non-critical workloads
- Small teams and projects

### HA is REQUIRED For:
- Production environments with SLAs
- Mission-critical applications
- 24/7 operations
- Large-scale multi-tenant platforms

---

## Cost/Benefit Analysis

### Benefits of HA

| Benefit | Value |
|---------|-------|
| **Zero downtime** | Maintenance without service interruption |
| **Fault tolerance** | Survive control plane node failures |
| **SLA compliance** | Meet 99.9% or 99.99% uptime requirements |
| **Peace of mind** | Sleep better knowing the cluster is resilient |
| **Professional grade** | Industry-standard production architecture |

### Costs of HA

| Cost | Impact |
|------|--------|
| **Infrastructure** | 3x control plane nodes + load balancer ($90-$230/month) |
| **Complexity** | More components to configure, monitor, and troubleshoot |
| **Operations** | More expertise required for distributed systems |
| **Setup time** | 2-4 hours initial setup vs 30 minutes for single control plane |
| **Maintenance** | Ongoing monitoring and updates for all control plane nodes |

### Decision Framework

Use this decision tree:

```
Is this production?
  └─ YES → Do you have SLA requirements?
            └─ YES → Do you need 99.9%+ uptime?
                     └─ YES → USE HA CLUSTER
                     └─ NO  → Single control plane may suffice
            └─ NO  → Single control plane is likely enough
  └─ NO  → Single control plane is fine
```

**Rule of thumb**: If losing the cluster for 15-30 minutes (reboot time) is acceptable, you don't need HA.

---

## Additional Resources

### Documentation
- [Kubernetes HA Topologies](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/ha-topology/)
- [Creating HA Clusters with kubeadm](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/high-availability/)
- [etcd Operations Guide](https://etcd.io/docs/v3.5/op-guide/)

### Tools
- [HAProxy Documentation](http://www.haproxy.org/)
- [keepalived for HA Load Balancers](https://www.keepalived.org/)
- [Prometheus Operator for Monitoring](https://github.com/prometheus-operator/prometheus-operator)

### Advanced Topics
- [External etcd Setup](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/setup-ha-etcd-with-kubeadm/)
- [etcd Performance Tuning](https://etcd.io/docs/v3.5/tuning/)
- [Kubernetes Production Best Practices](https://kubernetes.io/docs/setup/best-practices/)

---

## Next Steps

**For Production Deployments:**
1. Set up monitoring and alerting (Prometheus, Grafana)
2. Implement automated etcd backups
3. Configure log aggregation (ELK, Loki)
4. Set up disaster recovery procedures
5. Document runbooks for common scenarios

**For Learning:**
1. Return to core Kubernetes labs for workload management
2. Study monitoring and observability (Labs 18-20)
3. Practice CKA exam topics (single control plane focus)
4. Explore managed Kubernetes offerings (EKS, GKE, AKS)

---

**Lab Created**: March 2026
**Compatible with**: Kubernetes 1.29+
**Difficulty Level**: Advanced (Optional)
**Estimated Time**: 3-4 hours
**CKA Relevance**: Low (HA setup not deeply tested)
**Production Relevance**: High (critical for production environments)

---

**REMINDER: This is an OPTIONAL ADVANCED LAB**

If you're preparing for CKA certification, focus on:
- Single control plane cluster setup (Lab 6)
- Core workload management (Labs 1-5)
- Troubleshooting and administration (Labs 4-5)
- Security, networking, and storage fundamentals

HA cluster setup is valuable knowledge for production environments but not a primary focus of the CKA exam.
