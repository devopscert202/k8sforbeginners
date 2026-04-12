# **Working with Kubernetes Security Contexts**

Security contexts define **pod-level** and **container-level** security settings: the UID/GID processes run as, whether privilege escalation is allowed, supplemental groups, seccomp and AppArmor profiles (where supported), and read-only root filesystems. They are a primary lever for **reducing blast radius** and meeting **Pod Security** / CIS-style baselines.

---

## **1. Introduction to Security Contexts**

### **What is a Security Context?**
A security context specifies settings such as:
- User and group IDs for running processes (`runAsUser`, `runAsGroup`, `fsGroup`).
- Whether privilege escalation is allowed (`allowPrivilegeEscalation`).
- Linux capabilities (`capabilities`) and seccomp profile references.
- Read-only root filesystem (`readOnlyRootFilesystem`).

### **Why Use Security Contexts?**
- **Enhanced Security**: Avoid unnecessary root and restrict syscalls and capabilities.
- **Compliance**: Align workloads with organizational and benchmark guidance.
- **Controlled Access**: Enforce consistent ownership and permissions on volumes.

### **When to Use Security Contexts?**
- When applications support non-root execution.
- When you mount writable volumes and need consistent `fsGroup` behavior.
- When hardening new workloads or migrating images to stricter profiles.

---

## **2. Illustrative Pod with pod and container securityContext**

The pod sets defaults (`runAsUser`, `runAsGroup`, `fsGroup`); the container disables privilege escalation. A volume is included to show how `fsGroup` affects group ownership on `emptyDir` (behavior may vary slightly by volume plugin and Kubernetes version).

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

---

## **3. What to validate (conceptually)**

1. Processes run as the intended UID/GID (`runAsUser` / `runAsGroup`).
2. Volume mounts reflect `fsGroup` where applicable.
3. `allowPrivilegeEscalation: false` and dropped capabilities (if configured) appear in `kubectl describe pod` under the security context sections.

Operational commands and exec-based checks are covered in the lab manual.

---

## **4. Summary**

| **Setting**                    | **Typical intent**                                      |
|--------------------------------|---------------------------------------------------------|
| `runAsNonRoot` / `runAsUser`   | Avoid root in the container user namespace              |
| `readOnlyRootFilesystem`       | Limit tampering with image layers                       |
| `capabilities.drop: ["ALL"]`  | Remove default Docker capabilities; add back only needs |
| `seccompProfile`               | Restrict syscalls (for example `RuntimeDefault`)          |
| `fsGroup`                      | Group ownership for projected volumes                   |

---

## Hands-On Labs

Practice these concepts with guided lab exercises:

| Lab | Description |
|-----|-------------|
| [Lab 12: Pod Security Context](../../labmanuals/lab12-sec-security-context.md) | Apply, inspect, and validate pod and container security contexts. |
