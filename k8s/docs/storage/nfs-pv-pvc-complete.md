# Configuring Kubernetes with NFS-Based Persistent Volumes: Complete Guide

---

## Table of Contents

1. [Overview](#1-overview)
2. [Concept](#2-concept)
3. [Benefits](#3-benefits)
4. [Use Cases](#4-use-cases)
5. [Real-World Scenario](#5-real-world-scenario)
6. [Setting Up NFS Server](#6-setting-up-nfs-server)
   - 6.1 [Install NFS Server](#61-install-nfs-server)
   - 6.2 [Configure NFS Exports](#62-configure-nfs-exports)
   - 6.3 [Start NFS Server](#63-start-nfs-server)
   - 6.4 [Verify NFS Server](#64-verify-nfs-server)
7. [Configuring the Client Node](#7-configuring-the-client-node)
   - 7.1 [Install NFS Client](#71-install-nfs-client)
   - 7.2 [Mount NFS File System](#72-mount-nfs-file-system)
   - 7.3 [Verify NFS Mount](#73-verify-nfs-mount)
8. [Creating Kubernetes Persistent Volume (PV)](#8-creating-kubernetes-persistent-volume-pv)
9. [Creating Persistent Volume Claim (PVC)](#9-creating-persistent-volume-claim-pvc)
10. [Creating Pod Using NFS PVC](#10-creating-pod-using-nfs-pvc)
11. [Verification Steps](#11-verification-steps)

---

## 1. Overview

In Kubernetes, an NFS (Network File System) volume allows Pods to mount shared directories from an external NFS server. Using NFS provides a scalable way to share data between multiple Pods and nodes, which can be useful for scenarios requiring persistent storage that needs to be shared across multiple Pods. This tutorial explains how to set up an NFS server, configure a Persistent Volume (PV) and Persistent Volume Claim (PVC) with an NFS server, and mount the volume in a Pod.

---

## 2. Concept

An NFS-based volume is a shared network file system that multiple Pods can access concurrently. It is especially useful when you need persistent data that should be accessible across Pods on different nodes. By using NFS with Kubernetes, you can ensure that your application has access to the same data, regardless of the node on which the Pod is running. Kubernetes supports NFS volumes, allowing Pods to dynamically mount shared directories for persistent storage.

### How It Works

- **NFS Server**: The NFS server exports a directory, which is then mounted by the Pods via a Persistent Volume (PV).
- **PV**: The Persistent Volume uses the NFS server's exported directory as its source.
- **PVC**: A Persistent Volume Claim is created to request storage from the PV.
- **Pod**: The Pod is configured to use the PVC, thus mounting the NFS volume.

---

## 3. Benefits

- **Shared Storage**: NFS allows multiple Pods to share the same storage, which is ideal for applications that require access to the same data.
- **Scalability**: It is scalable across nodes and Pods, providing flexibility for growing applications.
- **Centralized Data Management**: Data is stored centrally on the NFS server, which makes it easier to manage and back up.
- **Cross-Node Access**: Pods can access the same data even if they are running on different nodes.

---

## 4. Use Cases

- **Shared Configuration Files**: When multiple Pods need access to shared configuration files or static data.
- **Database Storage**: For database applications that require a consistent, shared data storage location.
- **Log Aggregation**: Aggregating logs from multiple Pods into a shared directory accessible by other Pods for processing or analysis.

---

## 5. Real-World Scenario

In an e-commerce application, multiple Pods run various microservices like product catalog, customer management, and order processing. These microservices need access to shared configuration files and logs. By using an NFS-based Persistent Volume, all Pods can access the same directory to retrieve configuration files and write logs, ensuring data consistency and easy log aggregation.

---

## 6. Setting Up NFS Server

In this section, we will install and configure an NFS server on a Debian machine. This NFS server will be used to share files with Kubernetes pods.

### 6.1 Install NFS Server

```bash
sudo apt update
sudo apt install nfs-kernel-server
```

This will install the necessary packages to run the NFS server on your Debian machine.

### 6.2 Configure NFS Exports

The NFS server will share a specific directory. For this example, let's create a directory `/mnt/nfs_share` to share.

```bash
sudo mkdir -p /mnt/nfs_share && chmod -R 777 /mnt/nfs_share
```

Next, we need to configure which directories the server will export. Edit the `/etc/exports` file:

```bash
sudo nano /etc/exports
```

Add the following line to the file to export `/mnt/nfs_share` to clients:

```
/mnt/nfs_share *(rw,sync,no_subtree_check)
```

- `*` allows any client to access the directory (you can limit it to specific IPs if needed).
- `rw` allows read and write permissions.
- `sync` ensures that changes are written to disk before responding.
- `no_subtree_check` disables subtree checking for performance reasons.

### 6.3 Start NFS Server

Once the exports are configured, apply the changes and start the NFS server:

```bash
sudo exportfs -a
sudo systemctl start nfs-kernel-server
sudo systemctl enable nfs-kernel-server
```

This will start the NFS server and enable it to start on boot.

### 6.4 Verify NFS Server

To verify that the NFS server is running, use the following command:

```bash
sudo systemctl status nfs-kernel-server
```

You should see that the NFS server is active and running.

To check which directories are being exported, run:

```bash
sudo exportfs -v
```

This will display the exported directories and their permissions.

---

## 7. Configuring the Client Node

In this section, we will configure a client node to mount the NFS file system so that it can access the shared files.

### 7.1 Install NFS Client

On the client node, you need to install the NFS client utilities:

```bash
sudo apt update
sudo apt install nfs-common
```

### 7.2 Mount NFS File System

Next, mount the NFS share to a local directory on the client node. For example, mount it to `/mnt/nfs_mount`:

```bash
sudo mkdir -p /mnt/nfs_mount
sudo mount <NFS_SERVER_IP>:/mnt/nfs_share /mnt/nfs_mount
```

Replace `<NFS_SERVER_IP>` with the actual IP address of your NFS server. If the server IP is `192.168.1.100`, the command will look like this:

```bash
sudo mount 192.168.1.100:/mnt/nfs_share /mnt/nfs_mount
```

### 7.3 Verify NFS Mount

You can verify that the NFS mount is successful by listing the files in the mount directory:

```bash
ls /mnt/nfs_mount
```

You should be able to see the contents of the `/mnt/nfs_share` directory from the NFS server.

---

## 8. Creating Kubernetes Persistent Volume (PV)

Now that we have the NFS server running and accessible by the client, we will create a Kubernetes Persistent Volume (PV) that uses the NFS share.

### Define the NFS Persistent Volume

Create a `nfs-pv.yaml` file:

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: nfs-pv
spec:
  capacity:
    storage: 1Gi
  accessModes:
    - ReadWriteMany
  persistentVolumeReclaimPolicy: Retain
  volumeMode: Filesystem
  storageClassName: manual
  nfs:
    path: /mnt/nfs_mount
    server: 172.31.29.84  # Replace with the actual NFS server IP address
```

### Explanation of the YAML

- **nfs.path**: Specifies the directory on the NFS server to be used as the Persistent Volume.
- **nfs.server**: The IP address of the NFS server.
- **accessModes**: `ReadWriteMany` means that multiple Pods can mount the volume simultaneously for read and write access.
- **persistentVolumeReclaimPolicy**: Retains the volume after it is released, rather than deleting it.
- **capacity**: The storage size requested from the NFS server (1Gi in this case).

### Apply the PV Configuration

Apply the PV configuration to the Kubernetes cluster:

```bash
kubectl apply -f nfs-pv.yaml
```

### Verify the PV

To verify that the Persistent Volume is created, run:

```bash
kubectl get pv
```

You should see the `nfs-pv` in the list of persistent volumes.

---

## 9. Creating Persistent Volume Claim (PVC)

Next, we will create a Persistent Volume Claim (PVC) to request the storage from the `nfs-pv`.

### Define the PVC

Create a `nfs-pvc.yaml` file:

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
      storage: 1Gi
```

### Explanation of the YAML

- **accessModes**: Matches the PV's access mode (`ReadWriteMany`), meaning the PVC will request a volume that allows multiple Pods to read and write simultaneously.
- **resources.requests.storage**: Requests 1Gi of storage from the PV.

### Apply the PVC Configuration

Apply the PVC configuration to the Kubernetes cluster:

```bash
kubectl apply -f nfs-pvc.yaml
```

### Verify the PVC

To verify that the PVC is created, run:

```bash
kubectl get pvc
```

You should see the `nfs-pvc` in the list of persistent volume claims.

---

## 10. Creating Pod Using NFS PVC

Now, we will create a Pod that uses the NFS Persistent Volume Claim.

### Define the Pod YAML

Create a `nfs-pod.yaml` file:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nfs-pod
spec:
  containers:
  - name: nginx
    image: nginx
    volumeMounts:
    - name: nfs-volume
      mountPath: /usr/share/nginx/html
  volumes:
  - name: nfs-volume
    persistentVolumeClaim:
      claimName: nfs-pvc
```

### Explanation of the YAML

- **volumeMounts.mountPath**: Mounts the volume to the `/usr/share/nginx/html` directory in the container.
- **volumes.persistentVolumeClaim.claimName**: Refers to the PVC (`nfs-pvc`) requesting the NFS storage.

### Apply the Pod Configuration

Apply the Pod configuration to the Kubernetes cluster:

```bash
kubectl apply -f nfs-pod.yaml
```

### Verify the Pod

To verify that the Pod is running, use the following command:

```bash
kubectl get pods
```

You should see the `nfs-pod` in the list of pods.

---

## 11. Verification Steps

1. **Verify the PVC is Bound to the PV**:
   Check if the PVC is correctly bound to the PV:
   ```bash
   kubectl get pvc nfs-pvc
   ```
   The `STATUS` should be `Bound`.

2. **Check the Pod Status**:
   Check the status of the Pod to ensure it is running:
   ```bash
   kubectl get pods
   ```

3. **Verify the Mounted Volume**:
   Enter the Pod and check if the volume is correctly mounted to the specified path:
   ```bash
   kubectl exec -it nfs-pod -- /bin/bash
   ls /usr/share/nginx/html
   ```
   You should see the content from the NFS-mounted directory (`/mnt/nfs_mount`).

4. **Test Data Sharing Across Pods**:
   Create multiple Pods using the same PVC and verify that they can all access and modify the same data, confirming proper sharing across different nodes.

---

## Conclusion

In this comprehensive tutorial, you have learned how to:

1. Set up an NFS server on a Debian-based machine.
2. Configure an NFS client to mount the file system.
3. Create a Persistent Volume (PV), Persistent Volume Claim (PVC), and Pod in Kubernetes to access the NFS volume.
4. Verify proper configuration and data sharing across multiple Pods.

This process provides a simple and effective way to share storage across multiple Kubernetes nodes using NFS, enabling centralized data management and ensuring data consistency across distributed applications.

---
