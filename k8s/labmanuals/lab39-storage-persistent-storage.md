# Lab 39: Persistent Volumes and Advanced Storage

## Overview
In this lab, you will learn about Kubernetes persistent storage concepts including PersistentVolumes (PV), PersistentVolumeClaims (PVC), network storage with NFS, and using Secrets as volumes. You'll work with real-world storage patterns used in production environments.

## Prerequisites
- A running Kubernetes cluster (Minikube, Kind, or any K8s cluster)
- `kubectl` CLI tool installed and configured
- Completed Lab 09 (Basic Storage Volumes)
- For NFS exercises: NFS server access or ability to set one up

## Learning Objectives
By the end of this lab, you will be able to:
- Understand PersistentVolumes (PV) and PersistentVolumeClaims (PVC)
- Create and bind PVs and PVCs
- Work with different storage classes
- Set up and use NFS storage
- Mount Secrets as volumes
- Implement multi-container patterns with persistent storage
- Troubleshoot common persistent storage issues

---

## Understanding Persistent Storage in Kubernetes

### Storage Abstraction Model

```
┌─────────────────────────────────────────┐
│           Application Pod               │
│  ┌───────────────────────────────────┐  │
│  │     Container                     │  │
│  │  Accesses: /mnt/data              │  │
│  └───────────────┬───────────────────┘  │
└──────────────────┼──────────────────────┘
                   │ (references)
                   ▼
      ┌────────────────────────┐
      │ PersistentVolumeClaim  │ ← Application's storage request
      │      (PVC)             │
      └────────────┬───────────┘
                   │ (binds to)
                   ▼
      ┌────────────────────────┐
      │   PersistentVolume     │ ← Actual storage resource
      │       (PV)             │
      └────────────┬───────────┘
                   │ (backed by)
                   ▼
      ┌────────────────────────┐
      │  Physical Storage      │ ← hostPath, NFS, cloud disk
      └────────────────────────┘
```

### Key Concepts

| Component | Description | Created By | Lifecycle |
|-----------|-------------|------------|-----------|
| **PersistentVolume (PV)** | Cluster storage resource | Admin | Independent of Pods |
| **PersistentVolumeClaim (PVC)** | Storage request by user | User/Developer | Can outlive Pods |
| **StorageClass** | Dynamic provisioning template | Admin | Cluster-level |

---

## Exercise 1: PersistentVolumes with hostPath

### What is a PersistentVolume?
A **PersistentVolume (PV)** is a piece of storage in the cluster that has been provisioned by an administrator or dynamically provisioned using Storage Classes. It's a cluster resource independent of any individual Pod.

### What is a PersistentVolumeClaim?
A **PersistentVolumeClaim (PVC)** is a request for storage by a user. It's similar to a Pod: Pods consume node resources, and PVCs consume PV resources.

### Step 1: Prepare the Host Storage

For **Minikube** users:
```bash
minikube ssh
sudo mkdir -p /mnt/data
sudo chmod 777 /mnt/data
echo "Persistent storage initialized" | sudo tee /mnt/data/init.txt
exit
```

For **multi-node clusters**, create the directory on the target node.

### Step 2: Review the PV/PVC Manifest

Navigate to the storage labs:
```bash
cd k8s/labs/storage
```

Examine `hostpath-pv-pvc.yaml`:

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
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: hostpath-pvc
spec:
  storageClassName: manual
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
---
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

**Understanding PersistentVolume fields:**
- `capacity.storage: 1Gi` - Size of the volume
- `accessModes: ReadWriteOnce` - Can be mounted read-write by single node
- `persistentVolumeReclaimPolicy: Retain` - Keep data after PVC is deleted
- `storageClassName: manual` - Used to match PV with PVC
- `hostPath.path` - Actual storage location on host

**Understanding PersistentVolumeClaim fields:**
- `storageClassName: manual` - Must match PV's storageClassName
- `accessModes: ReadWriteOnce` - Must match or be subset of PV's modes
- `resources.requests.storage: 1Gi` - Requests 1Gi (PV must have at least this)

**Access Modes:**
- `ReadWriteOnce (RWO)` - Volume can be mounted read-write by a single node
- `ReadOnlyMany (ROX)` - Volume can be mounted read-only by many nodes
- `ReadWriteMany (RWX)` - Volume can be mounted read-write by many nodes

### Step 3: Create PV, PVC, and Pod

Apply the manifest:
```bash
kubectl apply -f hostpath-pv-pvc.yaml
```

Expected output:
```
persistentvolume/hostpath-pv created
persistentvolumeclaim/hostpath-pvc created
pod/hostpath-pod created
```

### Step 4: Verify PV and PVC Binding

Check PersistentVolume:
```bash
kubectl get pv
```

Expected output:
```
NAME          CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS   CLAIM                  STORAGECLASS   AGE
hostpath-pv   1Gi        RWO            Retain           Bound    default/hostpath-pvc   manual         10s
```

Check PersistentVolumeClaim:
```bash
kubectl get pvc
```

Expected output:
```
NAME           STATUS   VOLUME        CAPACITY   ACCESS MODES   STORAGECLASS   AGE
hostpath-pvc   Bound    hostpath-pv   1Gi        RWO            manual         10s
```

**Important**: STATUS should be `Bound` for both PV and PVC!

Detailed PV information:
```bash
kubectl describe pv hostpath-pv
```

Detailed PVC information:
```bash
kubectl describe pvc hostpath-pvc
```

### Step 5: Verify Pod Uses the Persistent Storage

Check Pod status:
```bash
kubectl get pod hostpath-pod
```

Read the initialization file:
```bash
kubectl exec hostpath-pod -- cat /usr/share/nginx/html/init.txt
```

Expected output:
```
Persistent storage initialized
```

### Step 6: Test Data Persistence

Create a new file:
```bash
kubectl exec hostpath-pod -- sh -c "echo 'Data from Pod' > /usr/share/nginx/html/pod-data.txt"
```

Delete the Pod:
```bash
kubectl delete pod hostpath-pod
```

**Important**: The PVC still exists!
```bash
kubectl get pvc
```

Recreate the Pod (remove the Pod section and reapply, or extract it):
```bash
kubectl apply -f - <<EOF
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
EOF
```

Verify data persists:
```bash
kubectl exec hostpath-pod -- cat /usr/share/nginx/html/pod-data.txt
```

Expected output:
```
Data from Pod
```

**Key Insight**: Data persists because PVC wasn't deleted!

---

## Exercise 2: Network Storage with NFS

### What is NFS Storage?
**Network File System (NFS)** allows you to share storage across multiple nodes, enabling `ReadWriteMany` access mode. This is crucial for applications that need shared storage across multiple Pod replicas.

### Prerequisites for NFS

You need an NFS server. Here's how to set one up on Ubuntu/Debian:

**On NFS Server:**
```bash
# Install NFS server
sudo apt-get update
sudo apt-get install -y nfs-kernel-server

# Create shared directory
sudo mkdir -p /mnt/nfs_share
sudo chmod 777 /mnt/nfs_share

# Configure NFS exports
echo "/mnt/nfs_share *(rw,sync,no_subtree_check,no_root_squash)" | sudo tee -a /etc/exports

# Export the shared directory
sudo exportfs -a
sudo systemctl restart nfs-kernel-server

# Get server IP
ip addr show
```

**On Kubernetes Nodes (if separate from NFS server):**
```bash
# Install NFS client
sudo apt-get update
sudo apt-get install -y nfs-common
```

**For Minikube:**
```bash
minikube ssh
sudo apt-get update
sudo apt-get install -y nfs-common
exit
```

### Step 1: Update NFS Server IP

Edit `nfs-pv-pvc.yaml` to replace the server IP with your NFS server IP:
```bash
# Find your NFS server IP first
kubectl get nodes -o wide

# Edit the file (or use sed)
sed -i 's/172.31.29.84/YOUR_NFS_SERVER_IP/g' nfs-pv-pvc.yaml
```

Or manually edit the file.

### Step 2: Review the NFS Manifest

Examine `nfs-pv-pvc.yaml`:

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
    server: 172.31.29.84  # Replace with actual NFS server IP
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: nfs-pvc
spec:
  storageClassName: manual
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 1Gi
---
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

**Key differences from hostPath:**
- `accessModes: ReadWriteMany` - Multiple Pods can write simultaneously
- `nfs.server` - NFS server IP address
- `nfs.path` - Path on the NFS server

### Step 3: Create NFS Storage Resources

Apply the manifest:
```bash
kubectl apply -f nfs-pv-pvc.yaml
```

Verify PV and PVC are bound:
```bash
kubectl get pv,pvc
```

Expected output:
```
NAME                        CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS   CLAIM              STORAGECLASS   AGE
persistentvolume/nfs-pv     1Gi        RWX            Retain           Bound    default/nfs-pvc    manual         10s

NAME                              STATUS   VOLUME   CAPACITY   ACCESS MODES   STORAGECLASS   AGE
persistentvolumeclaim/nfs-pvc     Bound    nfs-pv   1Gi        RWX            manual         10s
```

Check Pod status:
```bash
kubectl get pod nfs-pod
```

### Step 4: Test NFS Storage

Create a test file:
```bash
kubectl exec nfs-pod -- sh -c "echo 'NFS Test Data' > /usr/share/nginx/html/nfs-test.txt"
```

Verify on NFS server:
```bash
# On NFS server or via minikube ssh if NFS is on Minikube
cat /mnt/nfs_share/nfs-test.txt
```

Expected output:
```
NFS Test Data
```

### Step 5: Test ReadWriteMany Access

Create multiple Pods using the same PVC:
```bash
kubectl apply -f - <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: nfs-pod-2
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
EOF
```

Both Pods should access the same data:
```bash
kubectl exec nfs-pod -- cat /usr/share/nginx/html/nfs-test.txt
kubectl exec nfs-pod-2 -- cat /usr/share/nginx/html/nfs-test.txt
```

Write from Pod 2:
```bash
kubectl exec nfs-pod-2 -- sh -c "echo 'Written by Pod 2' > /usr/share/nginx/html/pod2.txt"
```

Read from Pod 1:
```bash
kubectl exec nfs-pod -- cat /usr/share/nginx/html/pod2.txt
```

**Key Insight**: NFS allows true shared storage with ReadWriteMany!

---

## Exercise 3: Using Secrets as Volumes

### What are Secret Volumes?
Secrets can be mounted as volumes in Pods, making sensitive data available as files. This is useful for:
- Database credentials
- API keys
- TLS certificates
- Configuration files with sensitive data

### Step 1: Review the Secret Volume Manifest

Examine `secret-volume.yaml`:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-credentials
type: Opaque
data:
  username: c3VwZXJ1c2Vy # base64 encoded 'superuser'
  password: cGFzc3dvcmQ= # base64 encoded 'password'
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: secret-deployment
spec:
  replicas: 1
  selector:
    matchLabels:
      app: secret-app
  template:
    metadata:
      labels:
        app: secret-app
    spec:
      containers:
      - name: secret-container
        image: nginx
        volumeMounts:
        - name: secret-volume
          mountPath: /etc/secrets
          readOnly: true
      volumes:
      - name: secret-volume
        secret:
          secretName: db-credentials
```

**Understanding Secret volumes:**
- `type: Opaque` - Generic secret type
- `data` - Base64-encoded values
- `mountPath: /etc/secrets` - Where secrets are mounted
- `readOnly: true` - Best practice for security
- Each key becomes a file in the mounted directory

### Step 2: Understand Base64 Encoding

Decode the secrets to understand the values:
```bash
echo "c3VwZXJ1c2Vy" | base64 -d
echo "cGFzc3dvcmQ=" | base64 -d
```

Expected output:
```
superuser
password
```

Create your own base64-encoded values:
```bash
echo -n "myusername" | base64
echo -n "mypassword" | base64
```

### Step 3: Deploy the Secret and Application

Apply the manifest:
```bash
kubectl apply -f secret-volume.yaml
```

Verify Secret is created:
```bash
kubectl get secrets
```

Expected output:
```
NAME              TYPE     DATA   AGE
db-credentials    Opaque   2      10s
```

View Secret details (doesn't show actual values):
```bash
kubectl describe secret db-credentials
```

Get the Pod name:
```bash
kubectl get pods -l app=secret-app
```

### Step 4: Verify Secret Files

List files in the mounted secret directory:
```bash
kubectl exec deployment/secret-deployment -- ls -la /etc/secrets/
```

Expected output:
```
total 0
drwxrwxrwt 3 root root  120 Mar 16 10:00 .
drwxr-xr-x 1 root root 4096 Mar 16 10:00 ..
drwxr-xr-x 2 root root   80 Mar 16 10:00 ..data
lrwxrwxrwx 1 root root   15 Mar 16 10:00 password -> ..data/password
lrwxrwxrwx 1 root root   15 Mar 16 10:00 username -> ..data/username
```

Read the username secret:
```bash
kubectl exec deployment/secret-deployment -- cat /etc/secrets/username
```

Expected output:
```
superuser
```

Read the password secret:
```bash
kubectl exec deployment/secret-deployment -- cat /etc/secrets/password
```

Expected output:
```
password
```

### Step 5: Update the Secret

Secrets mounted as volumes are automatically updated (with a delay):

Update the secret:
```bash
kubectl create secret generic db-credentials \
  --from-literal=username=newuser \
  --from-literal=password=newpass \
  --dry-run=client -o yaml | kubectl apply -f -
```

Wait a moment (secrets sync every 60 seconds by default), then check:
```bash
kubectl exec deployment/secret-deployment -- cat /etc/secrets/username
```

Eventually shows:
```
newuser
```

### Step 6: Security Best Practices

View Secret in base64 (not secure!):
```bash
kubectl get secret db-credentials -o yaml
```

**Better approach**: Use `stringData` for creating secrets:
```bash
kubectl apply -f - <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: better-secret
type: Opaque
stringData:
  username: "admin"
  password: "securepass123"
EOF
```

View it (still base64 encoded):
```bash
kubectl get secret better-secret -o yaml
```

---

## Exercise 4: Multi-Container Pods with Persistent Storage

### Use Case: Sidecar Pattern
A common pattern is having a main application container and a sidecar container that logs or processes data, both sharing persistent storage.

### Step 1: Review the Multi-Container Manifest

Examine `multicontainer-rw.yaml`:

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
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: multi-container-pvc
spec:
  storageClassName: manual
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 2Gi
---
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
    command: [ "sh", "-c", "while true; do echo Logging data at $(date) >> /usr/share/nginx/html/log.txt; sleep 5; done" ]
    volumeMounts:
    - name: shared-storage
      mountPath: /usr/share/nginx/html
  volumes:
  - name: shared-storage
    persistentVolumeClaim:
      claimName: multi-container-pvc
```

**Pattern explanation:**
- Container 1 (nginx) serves web content
- Container 2 (busybox) continuously writes logs
- Both share persistent storage via PVC
- Logs survive Pod restarts

### Step 2: Deploy the Multi-Container Application

Apply the manifest:
```bash
kubectl apply -f multicontainer-rw.yaml
```

Verify PV, PVC, and Pod:
```bash
kubectl get pv,pvc,pod multi-container-pod
```

Check both containers are running:
```bash
kubectl get pod multi-container-pod
```

Expected output shows `READY 2/2`:
```
NAME                  READY   STATUS    RESTARTS   AGE
multi-container-pod   2/2     Running   0          10s
```

### Step 3: Monitor the Logging Sidecar

Watch the log file being written:
```bash
kubectl exec multi-container-pod -c app-container-1 -- tail -f /usr/share/nginx/html/log.txt
```

You'll see entries like:
```
Logging data at Mon Mar 16 10:00:00 UTC 2026
Logging data at Mon Mar 16 10:00:05 UTC 2026
Logging data at Mon Mar 16 10:00:10 UTC 2026
```

Press `Ctrl+C` to stop.

### Step 4: View Logs from Each Container

View nginx logs:
```bash
kubectl logs multi-container-pod -c app-container-1
```

View busybox logger logs:
```bash
kubectl logs multi-container-pod -c app-container-2
```

### Step 5: Test Persistence with Pod Restart

Note the current number of log entries:
```bash
kubectl exec multi-container-pod -c app-container-1 -- wc -l /usr/share/nginx/html/log.txt
```

Delete the Pod:
```bash
kubectl delete pod multi-container-pod
```

Recreate it:
```bash
kubectl apply -f multicontainer-rw.yaml
```

Wait for it to be ready:
```bash
kubectl wait --for=condition=ready pod/multi-container-pod --timeout=60s
```

Check log entries again:
```bash
kubectl exec multi-container-pod -c app-container-1 -- wc -l /usr/share/nginx/html/log.txt
```

**Key Insight**: The log file persisted and continues growing!

### Step 6: Access Logs via HTTP

Port forward the nginx container:
```bash
kubectl port-forward pod/multi-container-pod 8080:80
```

In another terminal, access the logs:
```bash
curl http://localhost:8080/log.txt
```

Or open in browser: `http://localhost:8080/log.txt`

---

## Exercise 5: Storage Troubleshooting

### Common Issues and Solutions

**Issue 1: PVC Stuck in Pending**
```bash
kubectl describe pvc hostpath-pvc
```

Look for events:
```
Warning  ProvisioningFailed  no persistent volumes available for this claim
```

**Causes:**
- No matching PV available
- StorageClassName mismatch
- AccessMode incompatibility
- Insufficient capacity

**Solution**:
```bash
# Check available PVs
kubectl get pv

# Verify storageClassName matches
kubectl get pv hostpath-pv -o yaml | grep storageClassName
kubectl get pvc hostpath-pvc -o yaml | grep storageClassName

# Check access modes
kubectl describe pv hostpath-pv | grep "Access Modes"
kubectl describe pvc hostpath-pvc | grep "Access Modes"
```

**Issue 2: Pod Can't Mount Volume**
```bash
kubectl describe pod hostpath-pod
```

Events might show:
```
Warning  FailedMount  MountVolume.SetUp failed: hostPath type check failed
```

**Solution**: Ensure the directory exists on the node:
```bash
minikube ssh
sudo mkdir -p /mnt/data
sudo chmod 777 /mnt/data
exit
```

**Issue 3: NFS Mount Failures**
```bash
kubectl describe pod nfs-pod
```

Events:
```
Warning  FailedMount  mount.nfs: Connection refused
```

**Solutions**:
- Verify NFS server is running: `systemctl status nfs-kernel-server`
- Check NFS exports: `showmount -e NFS_SERVER_IP`
- Install nfs-common on nodes: `apt-get install nfs-common`
- Check network connectivity: `ping NFS_SERVER_IP`
- Verify firewall rules allow NFS traffic (port 2049)

**Issue 4: Secret Not Appearing as Files**
```bash
kubectl exec deployment/secret-deployment -- ls /etc/secrets/
```

If empty:
- Verify Secret exists: `kubectl get secret db-credentials`
- Check volume mount path in Pod spec
- Verify Secret name matches in volume definition

**Issue 5: ReadWriteMany Not Working**

Error:
```
Warning  FailedAttachVolume  Multi-Attach error for volume "pvc-xxx" Volume is already attached
```

**Cause**: Using RWO (ReadWriteOnce) instead of RWX (ReadWriteMany)

**Solution**: Use storage that supports RWX (like NFS) and set:
```yaml
accessModes:
  - ReadWriteMany
```

### Debugging Commands

```bash
# Check all PVs and their status
kubectl get pv -o wide

# Check all PVCs and their bindings
kubectl get pvc -o wide

# View detailed PV/PVC information
kubectl describe pv <pv-name>
kubectl describe pvc <pvc-name>

# Check which node a Pod is running on
kubectl get pod <pod-name> -o wide

# View storage-related events
kubectl get events --sort-by='.lastTimestamp' | grep -i volume

# Check if volume is mounted in container
kubectl exec <pod-name> -- df -h

# View volume mounts
kubectl exec <pod-name> -- mount | grep <mount-path>

# Test write permissions
kubectl exec <pod-name> -- touch /mnt/data/test-write
```

---

## Lab Cleanup

Clean up all resources:

```bash
# Delete Pods
kubectl delete pod hostpath-pod nfs-pod nfs-pod-2 multi-container-pod

# Delete Deployments
kubectl delete deployment secret-deployment

# Delete PVCs (this won't delete PVs with Retain policy)
kubectl delete pvc hostpath-pvc nfs-pvc multi-container-pvc

# Delete PVs
kubectl delete pv hostpath-pv nfs-pv multi-container-pv

# Delete Secrets
kubectl delete secret db-credentials better-secret

# Or delete using files
kubectl delete -f hostpath-pv-pvc.yaml
kubectl delete -f nfs-pv-pvc.yaml
kubectl delete -f secret-volume.yaml
kubectl delete -f multicontainer-rw.yaml
```

Clean up host directories (Minikube):
```bash
minikube ssh
sudo rm -rf /mnt/data/*
sudo rm -rf /tmp/host-directory
exit
```

Verify cleanup:
```bash
kubectl get all,pv,pvc,secrets
```

---

## Key Takeaways

1. **PersistentVolumes (PV)** are cluster resources that represent storage
2. **PersistentVolumeClaims (PVC)** are requests for storage by users
3. **StorageClass** must match between PV and PVC for binding
4. **Access Modes** determine how volumes can be mounted:
   - RWO: Single node read-write
   - ROX: Many nodes read-only
   - RWX: Many nodes read-write (requires network storage like NFS)
5. **Reclaim Policy** determines what happens to PV after PVC deletion:
   - Retain: Manual cleanup required
   - Delete: Automatic deletion
   - Recycle: Basic scrubbing (deprecated)
6. **Secrets as volumes** provide secure way to inject sensitive data
7. **Multi-container Pods** can share persistent storage for sidecar patterns
8. **NFS** enables true shared storage across multiple Pods and nodes

---

## Storage Reclaim Policies

| Policy | Behavior | Use Case |
|--------|----------|----------|
| **Retain** | PV kept after PVC deletion, manual cleanup needed | Production data you don't want automatically deleted |
| **Delete** | PV and underlying storage deleted with PVC | Dynamically provisioned cloud storage |
| **Recycle** | Basic scrub (rm -rf), deprecated | Legacy, use dynamic provisioning instead |

---

## Best Practices

1. **Always use PVCs in production**, not direct hostPath
2. **Use appropriate access modes**:
   - RWO for single-instance applications
   - RWX for multi-replica stateful applications
3. **Set resource requests** to ensure adequate storage
4. **Use StorageClasses** for dynamic provisioning in production
5. **Backup important data** regardless of PV reclaim policy
6. **Use network storage** (NFS, Ceph, cloud providers) for multi-node clusters
7. **Mount Secrets as readonly** volumes
8. **Don't store secrets in base64** in version control (use sealed secrets or vault)
9. **Test disaster recovery** procedures regularly
10. **Monitor storage usage** to prevent full disk issues

---

## Production Storage Options

### Cloud Provider Storage

**AWS:**
```yaml
storageClassName: gp3  # EBS GP3 volumes
```

**Azure:**
```yaml
storageClassName: managed-premium  # Azure Managed Disks
```

**GCP:**
```yaml
storageClassName: pd-ssd  # Persistent Disk SSD
```

### Dynamic Provisioning Example

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: dynamic-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  storageClassName: standard  # Uses default storage class
```

### Storage Operators
- **Rook/Ceph**: Cloud-native storage orchestration
- **OpenEBS**: Container-attached storage
- **Portworx**: Enterprise storage platform
- **Longhorn**: Lightweight distributed storage

---

## Additional Commands Reference

```bash
# List all storage-related resources
kubectl get pv,pvc,sc

# Watch PVC binding in real-time
kubectl get pvc -w

# Get PV details in YAML format
kubectl get pv <pv-name> -o yaml

# Patch PV reclaim policy
kubectl patch pv <pv-name> -p '{"spec":{"persistentVolumeReclaimPolicy":"Retain"}}'

# Expand PVC (if storage class allows)
kubectl patch pvc <pvc-name> -p '{"spec":{"resources":{"requests":{"storage":"2Gi"}}}}'

# Create secret from file
kubectl create secret generic my-secret --from-file=./secret-file.txt

# Create secret from literal values
kubectl create secret generic my-secret --from-literal=username=admin --from-literal=password=pass123

# Decode all secret data
kubectl get secret <secret-name> -o jsonpath='{.data}' | jq 'map_values(@base64d)'

# Check storage class details
kubectl describe sc <storage-class-name>

# Get default storage class
kubectl get sc -o jsonpath='{.items[?(@.metadata.annotations.storageclass\.kubernetes\.io/is-default-class=="true")].metadata.name}'
```

---

## Next Steps

Continue exploring advanced Kubernetes topics:
- StatefulSets for stateful applications
- Dynamic provisioning with StorageClasses
- CSI (Container Storage Interface) drivers
- Backup and disaster recovery solutions
- Storage monitoring and performance tuning

---

## Reference Architecture: Complete Storage Stack

```yaml
# StorageClass (defines provisioner)
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-storage
provisioner: kubernetes.io/aws-ebs
parameters:
  type: gp3
  fsType: ext4
---
# PersistentVolumeClaim (user request)
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: app-data
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  storageClassName: fast-storage
---
# StatefulSet (uses PVC)
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: database
spec:
  serviceName: database
  replicas: 3
  selector:
    matchLabels:
      app: database
  template:
    metadata:
      labels:
        app: database
    spec:
      containers:
      - name: postgres
        image: postgres:14
        volumeMounts:
        - name: data
          mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: [ "ReadWriteOnce" ]
      storageClassName: fast-storage
      resources:
        requests:
          storage: 10Gi
```

---

**Lab Created**: March 2026
**Compatible with**: Kubernetes 1.24+
