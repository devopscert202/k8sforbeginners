# Lab 38: Basic Storage Volumes in Kubernetes

## Overview
In this lab, you will learn about Kubernetes storage fundamentals by working with basic volume types. You'll explore emptyDir and hostPath volumes, and understand how containers within a Pod can share data.

## Prerequisites
- A running Kubernetes cluster (Minikube, Kind, or any K8s cluster)
- `kubectl` CLI tool installed and configured
- Basic understanding of Pods and containers
- Completed Lab 01 (Creating Pods)

## Learning Objectives
By the end of this lab, you will be able to:
- Understand different types of Kubernetes volumes
- Create and use emptyDir volumes
- Work with hostPath volumes
- Share data between containers in a multi-container Pod
- Understand volume lifecycle and data persistence
- Troubleshoot common storage issues

---

## Understanding Kubernetes Volumes

### What is a Volume?
A **Volume** in Kubernetes is a directory that is accessible to containers in a Pod. Unlike container filesystems, which are ephemeral and lost when containers crash, volumes have a lifetime that matches the Pod.

### Volume Types Covered in This Lab

| Volume Type | Description | Use Case | Data Persistence |
|-------------|-------------|----------|------------------|
| **emptyDir** | Empty directory created when Pod starts | Temporary storage, cache, sharing data between containers | Lost when Pod is deleted |
| **hostPath** | Mounts a file or directory from the host node | Accessing host files, development/testing | Persists on node (risky in production) |

---

## Exercise 1: Working with emptyDir Volumes

### What is emptyDir?
An **emptyDir** volume is created when a Pod is assigned to a node and exists as long as the Pod runs on that node. It starts as an empty directory and is shared among all containers in the Pod.

### Step 1: Review the emptyDir Pod Manifest

Navigate to the storage labs directory:
```bash
cd k8s/labs/storage
```

Examine the `emptydir.yaml` file:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: emptydir-example
spec:
  containers:
  - name: app
    image: httpd:latest
    volumeMounts:
    - mountPath: "/data"
      name: cache-volume
  volumes:
  - name: cache-volume
    emptyDir: {}
```

**Understanding the manifest:**
- `volumeMounts` - Defines where the volume is mounted inside the container
- `mountPath: "/data"` - Volume is accessible at `/data` inside the container
- `volumes` - Defines the volume at the Pod level
- `emptyDir: {}` - Creates an empty directory volume

### Step 2: Deploy the emptyDir Pod

Create the Pod:
```bash
kubectl apply -f emptydir.yaml
```

Expected output:
```
pod/emptydir-example created
```

Verify the Pod is running:
```bash
kubectl get pod emptydir-example
```

### Step 3: Test the emptyDir Volume

Access the Pod shell:
```bash
kubectl exec -it emptydir-example -- /bin/bash
```

Inside the container, create a file in the mounted volume:
```bash
echo "Testing emptyDir volume" > /data/test.txt
cat /data/test.txt
```

List the volume contents:
```bash
ls -la /data/
```

Exit the container:
```bash
exit
```

### Step 4: Verify Data Persistence Within Pod Lifecycle

Read the file without entering the Pod:
```bash
kubectl exec emptydir-example -- cat /data/test.txt
```

Expected output:
```
Testing emptyDir volume
```

**Important**: The data persists as long as the Pod exists, even if the container restarts.

### Step 5: Understand emptyDir Lifecycle

Delete the Pod:
```bash
kubectl delete pod emptydir-example
```

Recreate the Pod:
```bash
kubectl apply -f emptydir.yaml
```

Try to read the file:
```bash
kubectl exec emptydir-example -- cat /data/test.txt
```

Expected output:
```
cat: /data/test.txt: No such file or directory
```

**Key Insight**: emptyDir data is lost when the Pod is deleted!

---

## Exercise 2: Working with hostPath Volumes

### What is hostPath?
A **hostPath** volume mounts a file or directory from the host node's filesystem into the Pod. The data persists even after the Pod is deleted because it exists on the host.

### Security Warning
**CAUTION**: hostPath volumes pose security risks in production:
- Provides access to the host filesystem
- Different nodes may have different data
- Can cause security vulnerabilities
- Use only for development, testing, or single-node clusters

### Step 1: Prepare the Host Directory

For **Minikube** users, SSH into the Minikube VM:
```bash
minikube ssh
```

Create the host directory:
```bash
sudo mkdir -p /tmp/host-directory
sudo chmod 777 /tmp/host-directory
echo "Hello from host!" | sudo tee /tmp/host-directory/index.html
exit
```

For **multi-node clusters**, ensure the directory exists on the node where the Pod will run.

### Step 2: Review the hostPath Manifest

Examine `hostpath.yaml`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: hostpath-example
spec:
  containers:
  - name: myapp-container
    image: nginx
    volumeMounts:
    - mountPath: /usr/share/nginx/html
      name: hostpath-volume
  volumes:
  - name: hostpath-volume
    hostPath:
      path: /tmp/host-directory
      type: Directory
```

**Understanding the manifest:**
- `hostPath.path: /tmp/host-directory` - Path on the host node
- `hostPath.type: Directory` - Expects a directory (fails if not present)
- `mountPath: /usr/share/nginx/html` - Nginx's default web root

**hostPath types:**
- `Directory` - Must exist on host
- `DirectoryOrCreate` - Creates if doesn't exist
- `File` - Must be a file
- `FileOrCreate` - Creates file if doesn't exist

### Step 3: Deploy the hostPath Pod

Create the Pod:
```bash
kubectl apply -f hostpath.yaml
```

Verify it's running:
```bash
kubectl get pod hostpath-example
```

### Step 4: Verify Host Data is Accessible

Check the file we created on the host:
```bash
kubectl exec hostpath-example -- cat /usr/share/nginx/html/index.html
```

Expected output:
```
Hello from host!
```

### Step 5: Test Data Persistence

Create a new file from inside the Pod:
```bash
kubectl exec hostpath-example -- sh -c "echo 'Created from Pod' > /usr/share/nginx/html/pod-file.txt"
```

Delete the Pod:
```bash
kubectl delete pod hostpath-example
```

Verify data still exists on host (Minikube):
```bash
minikube ssh
cat /tmp/host-directory/pod-file.txt
exit
```

Expected output:
```
Created from Pod
```

Recreate the Pod:
```bash
kubectl apply -f hostpath.yaml
```

Verify data is still accessible:
```bash
kubectl exec hostpath-example -- cat /usr/share/nginx/html/pod-file.txt
```

**Key Insight**: hostPath data persists on the node even after Pod deletion!

---

## Exercise 3: Data Sharing Between Containers

### What is Multi-Container Data Sharing?
In a multi-container Pod, containers can share volumes to exchange data. This is useful for:
- Sidecar logging patterns
- Data processing pipelines
- File-based communication

### Step 1: Review the Data Sharing Manifest

Examine `data-sharing.yaml`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: data-sharing-pod
spec:
  containers:
  - name: app-container-1
    image: nginx
    volumeMounts:
    - mountPath: /usr/share/nginx/html
      name: shared-data
  - name: app-container-2
    image: busybox
    command: ["/bin/sh", "-c", "echo 'Shared data from app-container-2' > /usr/share/nginx/html/index.html && sleep 3600"]
    volumeMounts:
    - mountPath: /usr/share/nginx/html
      name: shared-data
  volumes:
  - name: shared-data
    emptyDir: {}
```

**Understanding the pattern:**
- Both containers mount the same volume (`shared-data`)
- Container 2 (busybox) writes an HTML file
- Container 1 (nginx) serves that file
- Uses emptyDir for temporary shared storage

### Step 2: Deploy the Multi-Container Pod

Create the Pod:
```bash
kubectl apply -f data-sharing.yaml
```

Verify both containers are running:
```bash
kubectl get pod data-sharing-pod
```

Expected output shows `READY 2/2`:
```
NAME               READY   STATUS    RESTARTS   AGE
data-sharing-pod   2/2     Running   0          10s
```

### Step 3: Verify Data Sharing

Check the file created by container-2:
```bash
kubectl exec data-sharing-pod -c app-container-1 -- cat /usr/share/nginx/html/index.html
```

Expected output:
```
Shared data from app-container-2
```

Check from container-2's perspective:
```bash
kubectl exec data-sharing-pod -c app-container-2 -- cat /usr/share/nginx/html/index.html
```

**Same output!** Both containers see the same data.

### Step 4: Test Read-Write Access

Write from container-1 (nginx):
```bash
kubectl exec data-sharing-pod -c app-container-1 -- sh -c "echo 'Modified by nginx' > /usr/share/nginx/html/test.txt"
```

Read from container-2 (busybox):
```bash
kubectl exec data-sharing-pod -c app-container-2 -- cat /usr/share/nginx/html/test.txt
```

Expected output:
```
Modified by nginx
```

### Step 5: View Container Logs

Check nginx logs:
```bash
kubectl logs data-sharing-pod -c app-container-1
```

Check busybox logs:
```bash
kubectl logs data-sharing-pod -c app-container-2
```

### Step 6: Test with Port Forwarding (Optional)

Forward nginx port to local machine:
```bash
kubectl port-forward pod/data-sharing-pod 8080:80
```

Open a browser or use curl:
```bash
curl http://localhost:8080
```

Expected output:
```
Shared data from app-container-2
```

Press `Ctrl+C` to stop port forwarding.

---

## Exercise 4: Comparing Volume Types

### Hands-On Comparison

Create a test file in each volume type and observe behavior:

**Test 1: emptyDir (already deployed)**
```bash
kubectl exec emptydir-example -- sh -c "date > /data/timestamp.txt"
kubectl exec emptydir-example -- cat /data/timestamp.txt
```

**Test 2: hostPath (already deployed)**
```bash
kubectl exec hostpath-example -- sh -c "date > /usr/share/nginx/html/timestamp.txt"
kubectl exec hostpath-example -- cat /usr/share/nginx/html/timestamp.txt
```

### Simulate Node Failure (emptyDir)

Delete and recreate emptyDir Pod:
```bash
kubectl delete pod emptydir-example
kubectl apply -f emptydir.yaml
kubectl exec emptydir-example -- cat /data/timestamp.txt
```

Result: File is gone!

### Simulate Node Restart (hostPath)

Delete and recreate hostPath Pod:
```bash
kubectl delete pod hostpath-example
kubectl apply -f hostpath.yaml
kubectl exec hostpath-example -- cat /usr/share/nginx/html/timestamp.txt
```

Result: File still exists!

---

## Exercise 5: Volume Troubleshooting

### Common Issues and Solutions

**Issue 1: Pod Stuck in Pending**
```bash
kubectl describe pod hostpath-example
```

Look for events like:
```
Warning  FailedMount  hostPath type check failed: /tmp/host-directory is not a directory
```

**Solution**: Create the directory on the host node.

**Issue 2: Permission Denied**
```bash
kubectl logs hostpath-example
```

**Solution**:
```bash
minikube ssh
sudo chmod 777 /tmp/host-directory
exit
```

**Issue 3: Container Can't Write to Volume**

Check if volume is mounted read-only:
```bash
kubectl exec hostpath-example -- mount | grep nginx
```

Verify volumeMounts doesn't have `readOnly: true`.

**Issue 4: Wrong Mount Path**

Describe the Pod to check actual mount points:
```bash
kubectl describe pod emptydir-example | grep -A 5 "Mounts:"
```

---

## Lab Cleanup

Remove all Pods created in this lab:

```bash
kubectl delete pod emptydir-example
kubectl delete pod hostpath-example
kubectl delete pod data-sharing-pod
```

Or use the YAML files:
```bash
kubectl delete -f emptydir.yaml
kubectl delete -f hostpath.yaml
kubectl delete -f data-sharing.yaml
```

Clean up host directory (Minikube):
```bash
minikube ssh
sudo rm -rf /tmp/host-directory
exit
```

Verify cleanup:
```bash
kubectl get pods
```

---

## Key Takeaways

1. **emptyDir** volumes are perfect for temporary storage and data sharing between containers
2. **emptyDir** data is lost when the Pod is deleted
3. **hostPath** volumes persist data on the host node
4. **hostPath** is useful for development but risky for production
5. Multiple containers in a Pod can share volumes for data exchange
6. Volume lifecycle is tied to Pod lifecycle (except hostPath)
7. Always check volume permissions and mount paths when troubleshooting

---

## Additional Commands Reference

```bash
# View volume information for a Pod
kubectl describe pod <pod-name> | grep -A 10 "Volumes:"

# Check volume mounts in a container
kubectl exec <pod-name> -- df -h

# View all mount points in a container
kubectl exec <pod-name> -- mount

# Create a file with timestamp
kubectl exec <pod-name> -- sh -c "date > /path/to/file"

# Copy files from Pod to local machine
kubectl cp <pod-name>:/path/to/file ./local-file

# Copy files from local machine to Pod
kubectl cp ./local-file <pod-name>:/path/to/file

# Check disk usage in a container
kubectl exec <pod-name> -- du -sh /data
```

---

## Best Practices

1. **Use emptyDir for**:
   - Temporary caches
   - Scratch space for computations
   - Sharing data between containers in a Pod

2. **Avoid hostPath in production** because:
   - Data location depends on which node the Pod runs on
   - Security risks from host filesystem access
   - Not portable across different clusters

3. **For production persistent storage**, use:
   - PersistentVolumes (covered in Lab 10)
   - Cloud provider storage (EBS, Azure Disk, etc.)
   - Network storage (NFS, Ceph, etc.)

4. **Volume naming**:
   - Use descriptive names like `cache-volume`, `shared-data`
   - Be consistent across your manifests

5. **Security**:
   - Use `readOnly: true` when containers only need read access
   - Minimize use of hostPath volumes
   - Apply proper file permissions on host directories

---

## Next Steps

Proceed to [Lab 39: Persistent Volumes and Advanced Storage](lab39-storage-persistent-storage.md) to learn about:
- PersistentVolumes (PV) and PersistentVolumeClaims (PVC)
- Network storage with NFS
- Secret volumes
- Multi-container Pods with persistent storage

---

## Troubleshooting Guide

| Problem | Possible Cause | Solution |
|---------|---------------|----------|
| Pod stuck in ContainerCreating | Volume mount failure | Check `kubectl describe pod` for events |
| Permission denied errors | Wrong directory permissions | Fix permissions on host: `chmod 777` |
| File not found | Wrong mount path | Verify mountPath in manifest |
| Data lost after Pod restart | Using emptyDir instead of persistent volume | Switch to PersistentVolume |
| Container restart loop | Application can't access volume | Check volume is mounted correctly |
| HostPath not working | Directory doesn't exist on node | Create directory or use `DirectoryOrCreate` |

---

**Lab Created**: March 2026
**Compatible with**: Kubernetes 1.24+
