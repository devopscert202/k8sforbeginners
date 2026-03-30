**Implementation Approach Guide for Kubernetes End Project**

## Project Title: **Real-World Kubernetes Scenario Implementation**

### **Summary**
This project simulates real-world responsibilities of a Kubernetes administrator, including managing etcd backups, configuring namespaces and network policies, assigning role-based access control (RBAC), and upgrading the Kubernetes cluster. By completing this project, learners will develop a strong foundation in Kubernetes administration, enabling them to support organizational needs effectively.

---

### **Prerequisite Knowledge**
To successfully implement this project, ensure familiarity with:
1. Kubernetes core concepts: Pods, Namespaces, Network Policies, and RBAC.
2. Managing etcd, Kubernetes’ key-value store.
3. YAML configuration files and kubectl commands.
4. Basic Linux commands.
5. Kubernetes cluster upgrade process.
6. Access to a Kubernetes cluster with at least one master node and three worker nodes.

---

### **Implementation Tasks**

#### **Task 1: Take a Backup of etcd**
##### Description:
As the infrastructure admin, ensure the etcd database is backed up to a file named `/tmp/myback`.

##### Underlying Kubernetes Concept:
- etcd is a distributed key-value store used by Kubernetes to store all cluster state data.
- Backups are crucial to restore the cluster in case of failures.

##### Steps:
1. SSH into the master node where etcd is running.
2. Run the following command to back up etcd:
   ```bash
   ETCDCTL_API=3 etcdctl snapshot save /tmp/myback \
     --endpoints=https://127.0.0.1:2379 \
     --cacert=/etc/kubernetes/pki/etcd/ca.crt \
     --cert=/etc/kubernetes/pki/etcd/server.crt \
     --key=/etc/kubernetes/pki/etcd/server.key
   ```
3. Verify the backup:
   ```bash
   ETCDCTL_API=3 etcdctl snapshot status /tmp/myback
   ```

---

#### **Task 2: Create a Namespace with Network Policy**
##### Description:
Create a namespace `cep-project2` and configure a network policy to allow Pods within the namespace to communicate with each other, while blocking Pods from other namespaces.

##### Underlying Kubernetes Concept:
- Namespaces isolate resources within a cluster.
- Network Policies define communication rules for Pods.

##### Steps:
1. Create the namespace `cep-project2`:
   ```yaml
   apiVersion: v1
   kind: Namespace
   metadata:
     name: cep-project2
   ```
   Apply the configuration:
   ```bash
   kubectl apply -f namespace.yaml
   ```

2. Define the network policy:
   ```yaml
   apiVersion: networking.k8s.io/v1
   kind: NetworkPolicy
   metadata:
     name: restrict-external-access
     namespace: cep-project2
   spec:
     podSelector:
       matchLabels: {}
     ingress:
     - from:
       - podSelector: {}
   ```
   Apply the configuration:
   ```bash
   kubectl apply -f networkpolicy.yaml
   ```

3. Explanation of the YAML:
   - The `podSelector` matches all Pods within the `cep-project2` namespace.
   - The `ingress` rule allows communication only from Pods in the same namespace (as they match the empty `podSelector` field).
   - Pods outside `cep-project2` are denied access by default because no explicit rules allow their traffic.

---

#### **Task 3: Configure RBAC for User4**
##### Description:
Grant user4 view-only access to resources in the `cep-project2` namespace.

##### Underlying Kubernetes Concept:
- RBAC (Role-Based Access Control) restricts user permissions based on roles.
- A `Role` and `RoleBinding` are namespace-specific.

##### Steps:
1. Add user4 to the cluster:
   - Ensure the user4’s credentials are configured in the kubeconfig file on the client machine. This typically involves generating certificates for the user and adding an entry in the kubeconfig file.

2. Set the context for user4:
   ```bash
   kubectl config set-context user4-context \
     --cluster=<cluster-name> \
     --user=user4 \
     --namespace=cep-project2
   ```

3. Create a `Role` in the `cep-project2` namespace:
   ```yaml
   apiVersion: rbac.authorization.k8s.io/v1
   kind: Role
   metadata:
     namespace: cep-project2
     name: view-role
   rules:
   - apiGroups: [""]
     resources: ["pods", "services", "endpoints", "configmaps"]
     verbs: ["get", "list", "watch"]
   ```
   Apply the configuration:
   ```bash
   kubectl apply -f role.yaml
   ```

4. Create a `RoleBinding` to bind the role to user4:
   ```yaml
   apiVersion: rbac.authorization.k8s.io/v1
   kind: RoleBinding
   metadata:
     name: view-rolebinding
     namespace: cep-project2
   subjects:
   - kind: User
     name: user4
     apiGroup: rbac.authorization.k8s.io
   roleRef:
     kind: Role
     name: view-role
     apiGroup: rbac.authorization.k8s.io
   ```
   Apply the configuration:
   ```bash
   kubectl apply -f rolebinding.yaml
   ```

5. Test user4’s access:
   - Switch to the user4 context:
     ```bash
     kubectl config use-context user4-context
     ```
   - Check user4’s permissions:
     ```bash
     kubectl auth can-i list pods --namespace=cep-project2
     ```

---

#### **Task 4: Upgrade Kubernetes Master Node**
##### Description:
Update the Kubernetes master node to the latest version.

##### Underlying Kubernetes Concept:
- Kubernetes upgrades ensure the cluster remains secure and up-to-date with new features.
- Upgrading the control plane is critical before upgrading worker nodes.

##### Steps:
1. Select the Kubernetes version:
   - Use the `kubeadm upgrade plan` command to view available versions.
   - Ensure the new version is compatible with the current version. Kubernetes supports upgrades across one minor version (e.g., 1.25 to 1.26). Skipping multiple minor versions is not supported.
   - Check the [Kubernetes version skew policy](https://kubernetes.io/docs/setup/release/version-skew-policy/) for detailed limitations.

2. Check the current version:
   ```bash
   kubectl version --short
   ```

3. SSH into the master node.

4. Follow the upgrade steps using kubeadm:
   ```bash
   sudo apt update && sudo apt install -y kubeadm
   sudo kubeadm upgrade plan
   sudo kubeadm upgrade apply <latest-version>
   ```

5. Update kubelet and kubectl:
   ```bash
   sudo apt install -y kubelet kubectl
   sudo systemctl restart kubelet
   ```

6. Verify the upgrade:
   ```bash
   kubectl get nodes
   ```

---

### **Conclusion**
This project provides hands-on experience with crucial Kubernetes administrative tasks:
- Managing etcd backups ensures disaster recovery preparedness.
- Namespace and network policy configuration reinforces security and resource isolation.
- RBAC implementation highlights the importance of least privilege access.
- Upgrading the Kubernetes cluster demonstrates lifecycle management expertise.

By mastering these tasks, learners position themselves as proficient Kubernetes administrators capable of enhancing organizational infrastructure reliability and security.

Good luck!
