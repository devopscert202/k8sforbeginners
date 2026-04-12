# NFS-based PersistentVolumes in Kubernetes

---

## Table of Contents

1. [Overview](#1-overview)
2. [Concept](#2-concept)
3. [Benefits](#3-benefits)
4. [Use cases](#4-use-cases)
5. [Real-world scenario](#5-real-world-scenario)
6. [NFS server and cluster prerequisites](#6-nfs-server-and-cluster-prerequisites)
7. [Kubernetes objects](#7-kubernetes-objects)
8. [Binding and multi-pod access](#8-binding-and-multi-pod-access)

---

## 1. Overview

An **NFS** volume lets Pods mount a directory exported by an NFS server. With a **PersistentVolume (PV)** backed by NFS and a **PersistentVolumeClaim (PVC)**, workloads get a stable abstraction: the same claim can be reused across Pod restarts and, with **ReadWriteMany**, by multiple Pods on different nodes—provided the NFS server and network path are highly available and correctly permissioned.

---

## 2. Concept

- **NFS server**: Exports a path (e.g. `/mnt/nfs_share`) to clients. Every node that might run a Pod using the volume must reach this server and export.
- **PV**: Declares `spec.nfs.server` and `spec.nfs.path` (the **export path on the server**, not a client mount path), capacity, access modes, reclaim policy, and optional `storageClassName`.
- **PVC**: Requests compatible storage; Kubernetes binds it to a matching PV (static) or provisions one (dynamic, if a provisioner supports NFS).
- **Pod**: References the PVC in a volume; the mount path inside the container is independent of the server export path.

---

## 3. Benefits

- **Shared storage** across Pods and nodes when using **ReadWriteMany**.
- **Centralized data** for backup and operations on the NFS side.
- **Familiar pattern** for lift-and-shift and on-premises clusters.

---

## 4. Use cases

- Shared configuration or static assets consumed by many replicas.
- Shared read/write data where the application tolerates NFS semantics (locking, latency).
- Log or content directories that must outlive any single Pod.

---

## 5. Real-world scenario

Multiple microservices might read shared configuration and write logs or uploads to one namespace on NFS so operators can back up and tune the file server independently of Kubernetes upgrades.

---

## 6. NFS server and cluster prerequisites

Operating an NFS server (packages, `/etc/exports`, firewalls, and client mounts on nodes) is **infrastructure work outside the Kubernetes API**. In short: export a directory from a reachable server, ensure cluster nodes can mount it with compatible NFS versions and permissions, and size the export for your workloads. Labs in this repo step through a concrete server-and-client setup.

---

## 7. Kubernetes objects

### PersistentVolume (illustrative)

Replace `server` and `nfs.path` with your environment. **`nfs.path` must be the path exported by the server.**

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
    path: /mnt/nfs_share
    server: 192.168.1.100
```

- **accessModes: ReadWriteMany**: Appropriate when multiple Pods need concurrent read-write access and the backend supports it.
- **persistentVolumeReclaimPolicy: Retain**: Keeps data after the claim is released; operators must reclaim or delete PVs explicitly when appropriate.

### PersistentVolumeClaim

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
  storageClassName: manual
```

### Pod mounting the PVC

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

---

## 8. Binding and multi-pod access

Once a PVC **binds** to the PV, Pods that reference the claim receive the same underlying NFS export. To validate behavior in a cluster, check PVC status, Pod events, and mount tables inside the container. Multiple Pods can share one PVC only when access modes and the storage backend allow it; for strict isolation, use separate claims or RWO backends.

---

## Hands-On Labs

Practice these concepts with guided lab exercises:

| Lab | Description |
|-----|-------------|
| [Lab 39: Persistent Volumes and Advanced Storage](../../labmanuals/lab39-storage-persistent-storage.md) | PVs, PVCs, NFS-oriented workflows, and related storage practice |
