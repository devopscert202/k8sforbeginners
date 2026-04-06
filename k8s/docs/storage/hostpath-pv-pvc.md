# HostPath-based PersistentVolume and PersistentVolumeClaim

## Overview
A **hostPath** volume mounts a file or directory from the **node’s** filesystem into a Pod. It is common in development and constrained environments but is a poor fit for most production clusters: data is tied to one node, poses security and portability risks, and **ReadWriteMany** on hostPath does not give true multi-node shared storage. Pairing hostPath with a **PersistentVolume (PV)** and **PersistentVolumeClaim (PVC)** still expresses the standard persistence API, but operators must understand node binding and access modes.

## Concept
- **PV**: Cluster-scoped storage resource; for hostPath, the `spec` points at a path on a specific node (often combined with node affinity for local volumes).
- **PVC**: Namespaced request for storage; binds to a PV whose class, size, and access modes match.
- **Pod**: Mounts the PVC; the kubelet resolves it to the host path on the node where the Pod runs.

## Benefits and trade-offs
- **Low friction** for local dev and single-node tests.
- **Persistence across Pod restarts** on the same node (data remains on the host path).
- **Not portable** across nodes for RWO; **RWX with hostPath** is misleading for multi-node clusters—use NFS, CSI file shares, or cloud RWX volumes for real shared storage.

## Use cases
- Local development and CI-like clusters.
- Node-local caches or fixtures where data loss on reschedule is acceptable.
- Learning PV/PVC flow before moving to CSI or network storage.

## Example manifests

**PersistentVolume** (hostPath, manual class):

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: hostpath-pv
spec:
  capacity:
    storage: 1Gi
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  volumeMode: Filesystem
  storageClassName: manual
  hostPath:
    path: /mnt/data
    type: Directory
```

**PersistentVolumeClaim**:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: hostpath-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
```

**Pod** using the claim:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: hostpath-pod
spec:
  containers:
  - name: nginx
    image: nginx
    volumeMounts:
    - name: hostpath-volume
      mountPath: /usr/share/nginx/html
  volumes:
  - name: hostpath-volume
    persistentVolumeClaim:
      claimName: hostpath-pvc
```

---

# Access modes (reference)

When defining PVs and PVCs, **access modes** describe how a volume may be mounted.

### **ReadWriteOnce (RWO)**  
- **Description**: Read-write by a single node (legacy semantics allowed multiple pods on that node; **ReadWriteOncePod** tightens to one pod when supported).  
- **Use case**: Block-like volumes, single-writer workloads.

### **ReadOnlyMany (ROX)**  
- **Description**: Read-only on many nodes.  
- **Use case**: Shared static content.

### **ReadWriteMany (RWX)**  
- **Description**: Read-write from multiple nodes.  
- **Use case**: Shared file systems (NFS, EFS, managed file services).  
- **Requires** a backend that actually supports concurrent writers.

### **ReadWriteOncePod (RWOP)**  
- **Description**: At most one pod may mount the volume read-write.  
- **Use case**: Strict single-writer semantics with supported drivers.

### **PV, PVC, and StorageClass**
- The PV declares supported access modes; the PVC requests a subset that must be satisfied for binding.
- The **StorageClass** and provisioner determine which access modes are valid for dynamically provisioned volumes.

### **Summary**

| **Access Mode**    | **Multiple pods (typical)** | **Multiple nodes** | **Notes**                    |
|--------------------|-----------------------------|--------------------|------------------------------|
| **ReadWriteOnce**  | Often, same node            | Single writer node | Common for block storage     |
| **ReadOnlyMany**   | Yes                         | Yes                | Read-only shared data        |
| **ReadWriteMany**| Yes                         | Yes                | Needs true shared filesystem |
| **ReadWriteOncePod** | No (one pod RW)         | N/A                | CSI / newer plugins          |

---

## Hands-On Labs

Practice these concepts with guided lab exercises:

| Lab | Description |
|-----|-------------|
| [Lab 38: Basic Storage Volumes in Kubernetes](../../labmanuals/lab38-storage-basic-volumes.md) | emptyDir, hostPath, and sharing data between containers |
| [Lab 39: Persistent Volumes and Advanced Storage](../../labmanuals/lab39-storage-persistent-storage.md) | PVs, PVCs, and persistent storage patterns |
