# Lab 12: Pod Security Context

## Overview
In this lab, you will learn how to configure security contexts for Pods and containers in Kubernetes. Security contexts define privilege and access control settings for a Pod or Container, helping you implement security best practices and the principle of least privilege.

## Prerequisites
- A running Kubernetes cluster
- kubectl CLI tool installed and configured
- Basic understanding of Linux users, groups, and file permissions
- Completion of Lab 01 (recommended)

## Learning Objectives
By the end of this lab, you will be able to:
- Understand Pod and Container security contexts
- Configure user and group IDs for Pods
- Set file system permissions using fsGroup
- Control privilege escalation
- Verify security settings inside containers
- Apply security best practices to your workloads

---

## Understanding Security Context

### What is a Security Context?

A **Security Context** defines privilege and access control settings for a Pod or Container. These settings include:
- **User ID (UID)** - Which user runs the container process
- **Group ID (GID)** - Which group owns the process
- **File System Group (fsGroup)** - Group ID for mounted volumes
- **Privilege Escalation** - Whether a process can gain more privileges
- **Capabilities** - Fine-grained Linux kernel privileges
- **SELinux Options** - Security-Enhanced Linux settings

### Why Use Security Context?

Security contexts help you:
- Run containers as non-root users
- Prevent privilege escalation attacks
- Control file system permissions
- Implement defense-in-depth security
- Meet compliance requirements
- Follow the principle of least privilege

### Security Context Levels

Security settings can be configured at two levels:

| Level | Scope | Overrides |
|-------|-------|-----------|
| **Pod Security Context** | Applies to all containers in the Pod | Can be overridden by container settings |
| **Container Security Context** | Applies to specific container | Takes precedence over Pod settings |

---

## Exercise 1: Understanding the Security Context Configuration

### Step 1: Review the Manifest

Navigate to the security labs directory:
```bash
cd k8s/labs/security
```

Let's examine the `security-context.yaml` file:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: security-context-1
spec:
  securityContext:
    runAsUser: 1000
    runAsGroup: 3000
    fsGroup: 2000
  volumes:
  - name: sec-ctx-vol
    emptyDir: {}
  containers:
  - name: sec-ctx-demo
    image: busybox:1.28
    command: [ "sh", "-c", "sleep 1h" ]
    volumeMounts:
    - name: sec-ctx-vol
      mountPath: /data/demo
    securityContext:
      allowPrivilegeEscalation: false
```

**Understanding the configuration:**

**Pod-level Security Context:**
- `runAsUser: 1000` - Run all containers as user ID 1000
- `runAsGroup: 3000` - Run processes with group ID 3000
- `fsGroup: 2000` - All mounted volumes will be owned by group ID 2000

**Container-level Security Context:**
- `allowPrivilegeEscalation: false` - Prevents the process from gaining more privileges than its parent process

**Why these settings matter:**
- Running as non-root (UID 1000) reduces attack surface
- fsGroup ensures proper volume permissions
- Disabling privilege escalation prevents container breakout attempts

---

## Exercise 2: Deploy and Test Security Context

### Step 1: Deploy the Pod

Create the Pod with security context:

```bash
kubectl apply -f security-context.yaml
```

Expected output:
```
pod/security-context-1 created
```

### Step 2: Verify Pod Status

Check if the Pod is running:

```bash
kubectl get pod security-context-1
```

Expected output:
```
NAME                 READY   STATUS    RESTARTS   AGE
security-context-1   1/1     Running   0          15s
```

### Step 3: Verify User and Group Settings

Check which user is running the process:

```bash
kubectl exec security-context-1 -- id
```

Expected output:
```
uid=1000 gid=3000 groups=2000
```

**What this shows:**
- `uid=1000` - Process is running as user 1000 (not root!)
- `gid=3000` - Primary group is 3000
- `groups=2000` - Also member of group 2000 (fsGroup)

### Step 4: Verify the Process Owner

Check the running processes:

```bash
kubectl exec security-context-1 -- ps aux
```

Expected output:
```
PID   USER     TIME  COMMAND
    1 1000      0:00 sh -c sleep 1h
    7 1000      0:00 sleep 1h
   13 1000      0:00 ps aux
```

Notice all processes are owned by user 1000, not root (0).

### Step 5: Verify Volume Permissions

Check the mounted volume permissions:

```bash
kubectl exec security-context-1 -- ls -ld /data/demo
```

Expected output:
```
drwxrwsrwx    2 root     2000             6 Mar 16 10:00 /data/demo
```

**Understanding the output:**
- `drwxrwsrwx` - Directory with read/write/execute for all
- `root` - Owner is root (volume mounted by kubelet)
- `2000` - Group is 2000 (from fsGroup setting)
- The `s` in permissions indicates SGID bit (files created inherit group)

### Step 6: Test File Creation

Create a file in the volume:

```bash
kubectl exec security-context-1 -- sh -c "echo 'test data' > /data/demo/testfile.txt"
```

Check the file ownership:

```bash
kubectl exec security-context-1 -- ls -l /data/demo/testfile.txt
```

Expected output:
```
-rw-r--r--    1 1000     2000            10 Mar 16 10:05 /data/demo/testfile.txt
```

**What this shows:**
- `1000` - File is owned by user 1000 (runAsUser)
- `2000` - File belongs to group 2000 (fsGroup)

This ensures proper permissions for shared volumes!

---

## Exercise 3: Testing Without Security Context

### Step 1: Create a Pod Without Security Context

Let's compare with a Pod that doesn't have security context:

Create a file called `no-security-context.yaml`:

```bash
cat > no-security-context.yaml <<'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: no-security-context
spec:
  volumes:
  - name: test-vol
    emptyDir: {}
  containers:
  - name: test-container
    image: busybox:1.28
    command: [ "sh", "-c", "sleep 1h" ]
    volumeMounts:
    - name: test-vol
      mountPath: /data
EOF
```

Deploy the Pod:

```bash
kubectl apply -f no-security-context.yaml
```

### Step 2: Compare User Settings

Check the user in this Pod:

```bash
kubectl exec no-security-context -- id
```

Expected output:
```
uid=0(root) gid=0(root) groups=0(root),10(wheel)
```

**Notice**: This Pod runs as root (uid=0), which is a security risk!

### Step 3: Compare Volume Permissions

Check the volume permissions:

```bash
kubectl exec no-security-context -- ls -ld /data
```

Expected output:
```
drwxrwxrwx    2 root     root             6 Mar 16 10:10 /data
```

Both owner and group are root.

### Step 4: Security Comparison

| Aspect | With Security Context | Without Security Context |
|--------|----------------------|--------------------------|
| **User** | Non-root (UID 1000) | Root (UID 0) |
| **Group** | Custom GID 3000 | Root (GID 0) |
| **Volume Group** | fsGroup 2000 | Root (GID 0) |
| **Privilege Escalation** | Disabled | Enabled (default) |
| **Security Risk** | LOW | HIGH |

---

## Exercise 4: Advanced Security Context Settings

### Step 1: Create a Read-Only Root Filesystem Pod

Create a Pod with read-only root filesystem:

```bash
cat > readonly-rootfs.yaml <<'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: readonly-rootfs-pod
spec:
  securityContext:
    runAsUser: 1000
    runAsGroup: 3000
  containers:
  - name: readonly-container
    image: nginx:alpine
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      runAsNonRoot: true
    volumeMounts:
    - name: cache-volume
      mountPath: /var/cache/nginx
    - name: run-volume
      mountPath: /var/run
  volumes:
  - name: cache-volume
    emptyDir: {}
  - name: run-volume
    emptyDir: {}
EOF
```

Deploy the Pod:

```bash
kubectl apply -f readonly-rootfs.yaml
```

### Step 2: Understand the Configuration

**New security settings:**
- `readOnlyRootFilesystem: true` - Container's root filesystem is read-only
- `runAsNonRoot: true` - Kubernetes validates the container doesn't run as root
- Volume mounts for `/var/cache/nginx` and `/var/run` - Required directories that nginx needs to write to

### Step 3: Test Read-Only Filesystem

Try to create a file in a non-mounted directory:

```bash
kubectl exec readonly-rootfs-pod -- sh -c "touch /tmp/testfile"
```

Expected output (ERROR):
```
touch: /tmp/testfile: Read-only file system
command terminated with exit code 1
```

This is expected! The root filesystem is read-only for security.

### Step 4: Verify Writable Volumes

Test writing to mounted volumes:

```bash
kubectl exec readonly-rootfs-pod -- sh -c "echo 'test' > /var/cache/nginx/test.txt"
kubectl exec readonly-rootfs-pod -- ls /var/cache/nginx/
```

This should work because we mounted a writable emptyDir volume.

---

## Exercise 5: Testing Privilege Escalation

### Step 1: Create Pod That Allows Privilege Escalation

Create a test Pod:

```bash
cat > allow-escalation.yaml <<'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: allow-escalation
spec:
  securityContext:
    runAsUser: 1000
  containers:
  - name: escalation-test
    image: busybox:1.28
    command: [ "sh", "-c", "sleep 1h" ]
    securityContext:
      allowPrivilegeEscalation: true
EOF
```

Deploy the Pod:

```bash
kubectl apply -f allow-escalation.yaml
```

### Step 2: Create Pod That Denies Privilege Escalation

Create another Pod:

```bash
cat > deny-escalation.yaml <<'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: deny-escalation
spec:
  securityContext:
    runAsUser: 1000
  containers:
  - name: escalation-test
    image: busybox:1.28
    command: [ "sh", "-c", "sleep 1h" ]
    securityContext:
      allowPrivilegeEscalation: false
EOF
```

Deploy the Pod:

```bash
kubectl apply -f deny-escalation.yaml
```

### Step 3: Compare the Settings

Both Pods run as non-root user, but one allows privilege escalation and one doesn't.

Check process capabilities:

```bash
kubectl exec allow-escalation -- cat /proc/1/status | grep CapEff
kubectl exec deny-escalation -- cat /proc/1/status | grep CapEff
```

The capability bitmask will be different, showing different privilege levels.

---

## Exercise 6: Using Linux Capabilities

### Step 1: Add Specific Capabilities

Create a Pod with specific Linux capabilities:

```bash
cat > capabilities-demo.yaml <<'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: capabilities-demo
spec:
  securityContext:
    runAsUser: 1000
    runAsGroup: 3000
  containers:
  - name: cap-test
    image: busybox:1.28
    command: [ "sh", "-c", "sleep 1h" ]
    securityContext:
      allowPrivilegeEscalation: false
      capabilities:
        add: ["NET_ADMIN", "SYS_TIME"]
        drop: ["ALL"]
EOF
```

**Understanding capabilities:**
- `drop: ["ALL"]` - Remove all default capabilities
- `add: ["NET_ADMIN", "SYS_TIME"]` - Add only specific capabilities
  - `NET_ADMIN` - Network administration operations
  - `SYS_TIME` - System clock modification

Deploy the Pod:

```bash
kubectl apply -f capabilities-demo.yaml
```

### Step 2: Verify Capabilities

Check the process capabilities:

```bash
kubectl exec capabilities-demo -- cat /proc/1/status | grep Cap
```

This shows the capability bitmask. Only NET_ADMIN and SYS_TIME capabilities should be present.

---

## Lab Cleanup

### Step 1: Delete All Test Pods

Remove all Pods created in this lab:

```bash
kubectl delete pod security-context-1
kubectl delete pod no-security-context
kubectl delete pod readonly-rootfs-pod
kubectl delete pod allow-escalation
kubectl delete pod deny-escalation
kubectl delete pod capabilities-demo
```

Or delete all at once:

```bash
kubectl delete pod --all
```

### Step 2: Clean Up YAML Files

Remove temporary YAML files:

```bash
rm -f no-security-context.yaml
rm -f readonly-rootfs.yaml
rm -f allow-escalation.yaml
rm -f deny-escalation.yaml
rm -f capabilities-demo.yaml
```

### Step 3: Verify Cleanup

Confirm all Pods are deleted:

```bash
kubectl get pods
```

Expected output:
```
No resources found in default namespace.
```

---

## Security Context Best Practices

### User and Group Settings
- Always run containers as non-root users
- Use high UIDs (1000+) to avoid conflicts with system users
- Set fsGroup for shared volumes to ensure correct permissions
- Use runAsNonRoot: true to enforce non-root requirement

### Privilege Control
- Set allowPrivilegeEscalation: false by default
- Drop all capabilities and add only what's needed
- Use readOnlyRootFilesystem when possible
- Mount only necessary directories as writable

### Volume Security
- Use fsGroup to control volume permissions
- Limit volume mounts to only what's necessary
- Use read-only mounts when data doesn't need to be modified
- Avoid mounting sensitive host paths

### Container Images
- Use minimal base images (alpine, distroless)
- Scan images for vulnerabilities
- Create images that run as non-root by default
- Keep images updated with security patches

---

## Common Security Context Patterns

### Least Privilege Pod

```yaml
securityContext:
  runAsUser: 1000
  runAsGroup: 3000
  runAsNonRoot: true
  fsGroup: 2000
containers:
- securityContext:
    allowPrivilegeEscalation: false
    readOnlyRootFilesystem: true
    capabilities:
      drop: ["ALL"]
```

### Web Server Pod

```yaml
securityContext:
  runAsUser: 1000
  fsGroup: 2000
containers:
- securityContext:
    allowPrivilegeEscalation: false
    capabilities:
      drop: ["ALL"]
      add: ["NET_BIND_SERVICE"]  # Bind to ports < 1024
```

### Database Pod

```yaml
securityContext:
  runAsUser: 999
  fsGroup: 999
containers:
- securityContext:
    allowPrivilegeEscalation: false
    capabilities:
      drop: ["ALL"]
```

---

## Troubleshooting Guide

### Issue: Container fails with "Permission denied"

**Cause**: User doesn't have permissions to access files/directories

**Solution**:
```bash
# Check current user in container
kubectl exec <pod-name> -- id

# Check file permissions
kubectl exec <pod-name> -- ls -la /path/to/file

# Adjust fsGroup or runAsUser to match required permissions
```

### Issue: "container has runAsNonRoot and image will run as root"

**Cause**: Image's default user is root, but runAsNonRoot: true is set

**Solution**:
```yaml
securityContext:
  runAsUser: 1000  # Explicitly set non-root user
  runAsNonRoot: true
```

### Issue: Application can't write to required directories

**Cause**: readOnlyRootFilesystem prevents writes

**Solution**:
```yaml
volumeMounts:
- name: tmp-volume
  mountPath: /tmp
- name: var-volume
  mountPath: /var
volumes:
- name: tmp-volume
  emptyDir: {}
- name: var-volume
  emptyDir: {}
```

### Issue: "Operation not permitted" for network operations

**Cause**: Missing required capabilities

**Solution**:
```yaml
securityContext:
  capabilities:
    add: ["NET_ADMIN", "NET_RAW"]
```

---

## Key Takeaways

1. Always run containers as non-root users
2. Use fsGroup to manage volume permissions properly
3. Disable privilege escalation by default
4. Use read-only root filesystems when possible
5. Drop all capabilities and add only what's needed
6. Test security settings thoroughly before production
7. Security contexts are essential for defense-in-depth
8. Pod-level settings apply to all containers, container-level settings override

---

## Additional Reading

- [Kubernetes Security Context Documentation](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/)
- [Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/)
- [Linux Capabilities](https://man7.org/linux/man-pages/man7/capabilities.7.html)
- [CIS Kubernetes Benchmark](https://www.cisecurity.org/benchmark/kubernetes)

---

**Lab Created**: March 2026
**Compatible with**: Kubernetes 1.24+
**Based on**: labs/security/security-context.yaml
**Tested on**: kubeadm clusters
**Estimated Time**: 45-60 minutes
