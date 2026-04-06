### **Understanding Access Modes and StorageClasses in Non-Cloud Kubernetes**

In Kubernetes, **storage management** is critical for applications that require persistent data. When working in non-cloud environments such as on-premises or bare-metal clusters, understanding **access modes** and **StorageClasses** is essential for configuring storage effectively. This guide explains access modes and how to set up manual StorageClasses for common storage solutions like NFS and local storage.

---

### **Kubernetes Access Modes**

Access modes define how a volume can be mounted by pods. These modes are essential for ensuring that storage behaves as expected based on the application's needs.

#### **1. ReadWriteOnce (RWO)**  
- **Description**: The volume can be mounted as read-write by a single node.  
- **Use Case**: Ideal for single-instance applications, such as a database running on one node.  
- **Limitation**: Only one pod on one node can write to the volume.

#### **2. ReadOnlyMany (ROX)**  
- **Description**: The volume can be mounted as read-only by multiple nodes.  
- **Use Case**: Suitable for workloads that require access to shared, static data, such as configuration files or logs.  
- **Limitation**: No pod can modify the data.

#### **3. ReadWriteMany (RWX)**  
- **Description**: The volume can be mounted as read-write by multiple nodes.  
- **Use Case**: Best for shared storage scenarios, such as distributed file systems or collaborative workloads.  
- **Limitation**: Requires a storage backend that supports simultaneous access (e.g., NFS, Ceph).

#### **4. ReadWriteOncePod (RWOP)**  
- **Description**: The volume can be mounted as read-write by a single pod, even if other pods are on the same node.  
- **Use Case**: Suitable for scenarios requiring strict isolation for a single pod.  
- **Limitation**: Limited support and typically used with CSI drivers.

---

### **What is a StorageClass?**

A **StorageClass** in Kubernetes defines how storage resources are provisioned. It abstracts the storage backend configuration, making it easier to manage storage across different environments. In cloud environments, StorageClasses enable **dynamic provisioning**. However, in non-cloud setups, they are often used with **manual provisioning**, where Persistent Volumes (PVs) are created in advance.

---

### **Manual StorageClass patterns in non-cloud Kubernetes**

For non-cloud environments, two common storage solutions are **NFS** and **local storage**. Below are representative manifests for manual provisioning (no dynamic provisioner).

---

### **1. Manual StorageClass for NFS**

NFS is widely used in non-cloud environments for its ability to provide shared storage across multiple nodes.

#### **StorageClass**

A manual StorageClass that refers to NFS storage:

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: nfs-manual
provisioner: kubernetes.io/no-provisioner
volumeBindingMode: Immediate
```

- **`provisioner: kubernetes.io/no-provisioner`**: Indicates that the StorageClass does not support dynamic provisioning.
- **`volumeBindingMode: Immediate`**: Ensures the PV will bind to a PVC as soon as it is created.

#### **Persistent Volume (PV)**

A PV that references an exported NFS path on the server:

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: nfs-pv
spec:
  capacity:
    storage: 10Gi
  accessModes:
    - ReadWriteMany
  persistentVolumeReclaimPolicy: Retain
  storageClassName: nfs-manual
  nfs:
    path: /exported/path
    server: 192.168.1.100
```

#### **Persistent Volume Claim (PVC)**

A PVC that requests storage with the manual NFS StorageClass:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: nfs-pvc
spec:
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 10Gi
  storageClassName: nfs-manual
```

This pattern makes NFS-backed storage available to pods with shared read-write access when the backend export supports **ReadWriteMany**.

---

### **2. Manual StorageClass for local storage**

Local storage leverages physical disks or directories on nodes, making it ideal for high-performance workloads or single-node setups.

#### **StorageClass**

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: local-storage
provisioner: kubernetes.io/no-provisioner
volumeBindingMode: WaitForFirstConsumer
```

- **`volumeBindingMode: WaitForFirstConsumer`**: Delays PV binding until a pod using the PVC is scheduled. This helps bind storage on the correct node.

#### **Persistent Volume (PV)**

A PV that pins data to a directory on a specific node:

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: local-pv
spec:
  capacity:
    storage: 50Gi
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  storageClassName: local-storage
  local:
    path: /mnt/disks/ssd1
  nodeAffinity:
    required:
      nodeSelectorTerms:
        - matchExpressions:
            - key: kubernetes.io/hostname
              operator: In
              values:
                - node-1
```

- **`local.path`**: Directory on the node where data lives.
- **Node affinity**: Restricts which node can use this PV.

#### **Persistent Volume Claim (PVC)**

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: local-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 50Gi
  storageClassName: local-storage
```

---

### **Conclusion**

In non-cloud Kubernetes environments, manual StorageClasses for NFS and local storage provide flexibility and control over storage resources. While these configurations require manual PV (and often server-side) setup, they are effective for on-premises clusters where dynamic provisioning is unavailable. Combining access modes with StorageClasses lets you align storage with application needs.

---

## Hands-On Labs

Practice these concepts with guided lab exercises:

| Lab | Description |
|-----|-------------|
| [Lab 39: Persistent Volumes and Advanced Storage](../../labmanuals/lab39-storage-persistent-storage.md) | PVs, PVCs, NFS-style patterns, and advanced storage practice |
