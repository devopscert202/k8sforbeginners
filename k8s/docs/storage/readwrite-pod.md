# Multi-container Pods and ReadWriteMany (RWX) storage

## Overview
Kubernetes allows multiple containers in one Pod to share volumes. When several containers (or multiple Pods) need **concurrent read-write** access from different nodes, the backing volume must support **ReadWriteMany (RWX)**—for example NFS or a managed file service—not a single-node hostPath pretending to be shared.

## Concept
- **Multi-container Pod**: Containers share network (loopback), IPC (optional), and volumes.
- **PV / PVC**: The claim requests access modes and size; the PV’s plugin and backend must implement RWX if multiple nodes need writers.
- **RWX**: Multiple nodes may mount read-write; application-level consistency (locking, cache coherency) is still your responsibility.

## Benefits
- Shared scratch or content between sidecar and app containers in one Pod.
- One PVC referenced by several replicas when the file system supports it.

## Use cases
- Log collection sidecars writing to a shared directory.
- Shared static or uploaded content served by multiple containers.
- Pipelines where one container produces files another consumes (same Pod).

## Real-world scenario
A logging sidecar and a processor container mount the same RWX volume so logs are visible immediately without shipping bytes over the network from container to container—while long-term retention still depends on the NFS (or other) backend.

## Example manifests (illustrative)

**Note:** `hostPath` with `ReadWriteMany` does **not** create cluster-wide shared storage; the examples below mirror common teaching manifests. For real multi-node RWX, use NFS or a CSI driver that supports RWX.

**PersistentVolume**:

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: multi-container-pv
spec:
  capacity:
    storage: 2Gi
  accessModes:
    - ReadWriteMany
  persistentVolumeReclaimPolicy: Retain
  storageClassName: manual
  hostPath:
    path: /mnt/data
```

**PersistentVolumeClaim**:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: multi-container-pvc
spec:
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 2Gi
```

**Multi-container Pod**:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: multi-container-pod
spec:
  containers:
  - name: app-container-1
    image: nginx
    volumeMounts:
    - name: shared-storage
      mountPath: /usr/share/nginx/html
  - name: app-container-2
    image: busybox
    command: [ "sh", "-c", "while true; do echo 'Logging data' > /usr/share/nginx/html/log.txt; sleep 5; done" ]
    volumeMounts:
    - name: shared-storage
      mountPath: /usr/share/nginx/html
  volumes:
  - name: shared-storage
    persistentVolumeClaim:
      claimName: multi-container-pvc
```

Both containers see the same directory tree under their `mountPath`.

---

## Hands-On Labs

Practice these concepts with guided lab exercises:

| Lab | Description |
|-----|-------------|
| [Lab 38: Basic Storage Volumes in Kubernetes](../../labmanuals/lab38-storage-basic-volumes.md) | Volume fundamentals and sharing data between containers |
