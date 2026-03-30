
# 🧩 Kubernetes Installation Tutorial

## **Introduction**

Kubernetes (K8s) is an open-source platform designed to automate the deployment, scaling, and management of containerized applications. It provides powerful orchestration features such as load balancing, service discovery, self-healing, and automated rollouts/rollbacks.

This tutorial walks you through installing Kubernetes on **Ubuntu Linux** systems using **kubeadm**, covering both the **control plane (master)** and **worker nodes** setup.

---

## **High-Level Installation Process**

1. Prepare your system and remove any existing Kubernetes configurations.
2. Set hostnames for the master and worker nodes.
3. Initialize the Kubernetes cluster using `kubeadm`.
4. Configure `kubectl` for cluster management.
5. Install a network plugin (e.g., Calico).
6. Join worker nodes to the master node.

---

## **Prerequisites for Installation on Ubuntu Linux**

1. **Operating System:**
   Ubuntu 20.04 or Ubuntu 22.04 (64-bit).

2. **Hardware Requirements:**

   * Minimum **2 CPUs** and **4 GB RAM** per node.
   * At least **20 GB** of free disk space per node.

3. **Network Configuration:**

   * All nodes (master and workers) must be able to communicate over the network.
   * Ensure ports **6443**, **10250**, **10255**, and **8472** are open.

4. **Disable Swap:**
   Kubernetes requires swap to be disabled for performance and stability.

   ```bash
   sudo swapoff -a
   sudo sed -i '/ swap / s/^/#/' /etc/fstab
   ```

5. **Install a Container Runtime (Docker or containerd):**

   ```bash
   sudo apt update
   sudo apt install -y containerd
   sudo systemctl enable containerd
   sudo systemctl start containerd
   ```

6. **Install Kubernetes Tools:**
   Install the three key tools — `kubeadm`, `kubelet`, and `kubectl`:

   ```bash
   sudo apt update
   sudo apt install -y apt-transport-https ca-certificates curl
   curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
   echo "deb https://apt.kubernetes.io/ kubernetes-xenial main" | sudo tee /etc/apt/sources.list.d/kubernetes.list
   sudo apt update
   sudo apt install -y kubelet kubeadm kubectl
   sudo apt-mark hold kubelet kubeadm kubectl
   ```

---

## **Key Kubernetes Tools: Purpose and Use Cases**

| **Component** | **Purpose**                                                                                               | **Use Case**                                                           |
| ------------- | --------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| **kubeadm**   | Bootstraps a secure Kubernetes cluster by handling control-plane setup, token creation, and node joining. | Used to initialize the control plane and join worker nodes.            |
| **kubectl**   | Command-line interface for interacting with the Kubernetes API Server.                                    | Used for managing cluster resources and deployments.                   |
| **kubelet**   | Node-level agent that ensures containers are running as expected. Communicates with the API server.       | Runs on all nodes (master and workers) to maintain desired pod states. |

---

## **Step-by-Step Installation**

### 🧰 Step 1: Reset Any Existing Configuration

If a previous installation exists, reset it to ensure a clean environment:

```bash
sudo kubeadm reset -f
```

---

### 🖥️ Step 2: Set Hostnames

Assign unique and descriptive hostnames for all nodes:

```bash
# On master node
sudo hostnamectl set-hostname master.example.com

# On worker nodes
sudo hostnamectl set-hostname worker-node-1.example.com
sudo hostnamectl set-hostname worker-node-2.example.com
```

Confirm the changes:

```bash
hostnamectl
```

---

### 🚀 Step 3: Initialize the Kubernetes Control Plane

Run the following command **on the master node** to initialize the cluster:

```bash
sudo kubeadm init --ignore-preflight-errors=all
```

After initialization, `kubeadm` will display:

* The **join command** (save it for later — used by worker nodes).
* Paths to the cluster configuration files.

---

### ⚙️ Step 4: Configure `kubectl`

To enable cluster management using `kubectl`, configure it for your current user:

```bash
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config
```

Verify that your master node is ready:

```bash
kubectl get nodes
```

---

### 🌐 Step 5: Install Calico Networking Plugin

Apply the Calico network plugin manifest to enable pod-to-pod communication:

```bash
kubectl apply -f https://docs.projectcalico.org/manifests/calico.yaml
```

Check that all system pods are running:

```bash
kubectl get pods -n kube-system
```

---

### 🔗 Step 6: Join Worker Nodes to the Cluster

1. On the **master node**, generate the join command:

   ```bash
   sudo kubeadm token create --print-join-command
   ```

   Example output:

   ```bash
   kubeadm join 172.31.33.66:6443 --token qg5kgy.o1ov92iu7d50dkye --discovery-token-ca-cert-hash sha256:e3f0feef4ad831253c3535f72e17c3bddc0c631e789c621f7a130e7e798aa313
   ```

2. **Important:**
   ➤ Run the **join command** **on each worker node**, not on the master node.
   This connects the worker nodes to the control plane.

   Example:

   ```bash
   sudo kubeadm join 172.31.33.66:6443 --token qg5kgy.o1ov92iu7d50dkye --discovery-token-ca-cert-hash sha256:e3f0feef4ad831253c3535f72e17c3bddc0c631e789c621f7a130e7e798aa313
   ```

---

## ✅ Verification

After joining all worker nodes, verify the cluster setup from the master node:

1. **List all nodes:**

   ```bash
   kubectl get nodes
   ```

   Expected output:

   ```
   NAME                STATUS   ROLES           AGE   VERSION
   master.example.com  Ready    control-plane   10m   v1.29.x
   worker-node-1       Ready    <none>          3m    v1.29.x
   worker-node-2       Ready    <none>          2m    v1.29.x
   ```

2. **Check all running pods:**

   ```bash
   kubectl get pods -A
   ```

   All system pods (in `kube-system`) should show as `Running`.

---

## 🚧 Troubleshooting Tips

| **Issue**                        | **Possible Cause**          | **Fix**                                                           |
| -------------------------------- | --------------------------- | ----------------------------------------------------------------- |
| Worker node not joining          | Firewall blocking port 6443 | Allow port using `ufw allow 6443` or disable firewall temporarily |
| Pods stuck in `Pending` state    | Network plugin not applied  | Reapply Calico manifest                                           |
| `kubectl` not working after init | Missing kubeconfig setup    | Re-run Step 4 configuration commands                              |

---

## 🎯 Next Steps

You now have a functional Kubernetes cluster!
You can proceed to:

* Deploy your first application using YAML manifests.
* Experiment with scaling, networking, and persistent storage.
* Explore advanced topics such as Ingress, RBAC, and monitoring.

---


