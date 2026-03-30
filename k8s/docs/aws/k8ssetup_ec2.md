## Kubernetes Cluster Setup Guide (v1.31) on Ubuntu EC2 Instances

### Introduction
This guide provides step-by-step instructions to manually set up a Kubernetes cluster (v1.31) using one master node and two worker nodes on AWS EC2 instances. It uses containerd as the container runtime and Calico as the networking CNI. Each command is thoroughly explained, and troubleshooting steps are included to help resolve common issues.

The setup includes:
- Preparing the infrastructure (AWS EC2).
- Installing and configuring required components (containerd, Kubernetes tools).
- Bootstrapping the cluster and joining worker nodes.
- Testing the cluster with a sample application.

---
### 1. Preparing AWS EC2 Instances
Launch three Ubuntu 22.04 EC2 instances:
- **Master Node**: Name it `k8s-master`.
- **Worker Nodes**: Name them `k8s-worker-1` and `k8s-worker-2`.

**Suggested instance type:** `t3.medium` (2 vCPUs, 4GB RAM minimum).

#### Configure Security Groups:
- **Inbound Rules:**
  - TCP 22: Allow SSH from your IP.
  - TCP 6443: Allow Kubernetes API server access from worker nodes.
  - TCP 10250, 30000-32767: Allow access for kubelet and NodePort services.
- **Outbound Rules:** Allow all traffic.

#### Network ACLs (NACL):
- Ensure that your NACL allows traffic on ports 6443, 10250, and the range 30000-32767.

#### Whitelisting Ports Between Nodes:
- Modify Security Groups to allow traffic between the master and worker nodes:
  - Master Node should allow incoming traffic from worker nodes on ports 6443, 10250.
  - Worker Nodes should allow incoming traffic from the master node on ports 10250.

---
### 2. Installing and Configuring Components

#### Update the System
```
sudo apt update && sudo apt upgrade -y
```
Ensures all packages are up to date.

#### Remove Docker (if installed)
```
sudo apt-get purge -y docker-engine docker docker.io docker-ce docker-ce-cli
sudo apt-get autoremove -y --purge
sudo rm -rf /var/lib/docker /etc/docker
sudo rm /etc/containerd/config.toml
sudo systemctl restart containerd
```
Ensures a clean setup for containerd.

#### Install and Configure containerd
```
sudo apt update
sudo apt install -y containerd
```

Configure containerd:
```
sudo mkdir -p /etc/containerd
containerd config default | sudo tee /etc/containerd/config.toml
```

Edit `/etc/containerd/config.toml` and set:
```
[plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc.options]
  SystemdCgroup = true
```

Restart containerd:
```
sudo systemctl restart containerd
sudo systemctl enable containerd
```

#### Enable Kernel Modules (Required)
```
sudo modprobe overlay
sudo modprobe br_netfilter
```
Persist the settings:
```
echo "overlay" | sudo tee -a /etc/modules-load.d/containerd.conf
```
```
echo "br_netfilter" | sudo tee -a /etc/modules-load.d/containerd.conf
```
Set the required sysctl params:
```
echo "net.bridge.bridge-nf-call-iptables = 1" | sudo tee -a /etc/sysctl.d/kubernetes.conf
```
```
echo "net.ipv4.ip_forward = 1" | sudo tee -a /etc/sysctl.d/kubernetes.conf
```
```
sudo sysctl --system
```

#### Install Kubernetes Components
```
sudo apt update
sudo apt install -y apt-transport-https curl
```
```
curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo gpg --dearmor -o /etc/apt/trusted.gpg.d/kubernetes-archive-keyring.gpg
```
```
echo "deb https://apt.kubernetes.io/ kubernetes-xenial main" | sudo tee /etc/apt/sources.list.d/kubernetes.list
```
```
sudo apt update
sudo apt install -y kubeadm kubelet kubectl
sudo apt-mark hold kubeadm kubelet kubectl
```

---
### 3. Bootstrapping the Cluster (Master Node)

#### Initialize Kubernetes
```
sudo kubeadm init --pod-network-cidr=192.168.0.0/16
```
The `--pod-network-cidr` flag is necessary for Calico.

#### Configure kubectl Access
```
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config
```

---
### 4. Setting Up Networking (Calico)

#### Install Calico CNI
```
kubectl apply -f https://docs.projectcalico.org/manifests/calico.yaml
```
Verify nodes:
```
kubectl get nodes
```

---
### 5. Joining Worker Nodes

Retrieve the join command from the `kubeadm init` output. Example:
```
sudo kubeadm join <Master_Node_IP>:6443 --token <token> --discovery-token-ca-cert-hash sha256:<hash>
```
Run this command on each worker node.

Verify the nodes:
```
kubectl get nodes
```

---
### 6. Testing the Cluster

Deploy a test application:
```
kubectl create deployment nginx --image=nginx
```
Expose the deployment:
```
kubectl expose deployment nginx --port=80 --type=NodePort
```
Check the service details:
```
kubectl get svc nginx
```
Access the service using `NodePort`.

### 7. Troubleshooting

- Ensure proper connectivity between nodes.
- Check kubelet logs if nodes are not joining.
- Verify `containerd` status: `sudo systemctl status containerd`.

---
### 8. Cleanup (Optional)

To reset nodes:
```
sudo kubeadm reset -f
```
Remove configuration files:
```
sudo rm -rf /etc/cni/net.d
```

## Conclusion
You have successfully set up a Kubernetes cluster (v1.31) on AWS EC2 instances using containerd as the container runtime and Calico as the networking CNI. The master node is configured to manage the control plane, while worker nodes handle workloads. The cluster was validated by deploying a sample NGINX application and accessing it via NodePort.

In this guide, we have covered:

#### Preparing the infrastructure (AWS EC2 Instances).

#### Installing and configuring essential components (containerd, Kubernetes tools).

#### Enabling necessary kernel modules for networking.

#### Bootstrapping the cluster and joining worker nodes.

#### Securing communication between control and data planes via Security Groups and NACLs.

#### Verifying the cluster functionality through application deployment.

#### Troubleshooting common issues related to networking, tokens, and services.

The setup ensures a functional Kubernetes cluster that can be scaled and customized according to your specific requirements. For production-grade clusters, consider implementing enhanced security measures, high availability setups, and monitoring tools.
