# **Kubernetes Container Security and Hardening Techniques**

This document covers key techniques for securing Kubernetes containers, focusing on privilege escalation prevention and additional hardening practices aligned with the **CIS Kubernetes Benchmarks**. Practical YAML examples are provided for each configuration.

---

## **1. Prevent Privilege Escalation**

### **What is Privilege Escalation?**
Privilege escalation allows processes inside a container to gain elevated privileges, such as root-level access. Disabling privilege escalation reduces the risk of exploitation.

### **Configuration Example**

#### YAML: Prevent Privilege Escalation
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: no-priv-escalation-pod
spec:
  containers:
  - name: nginx
    image: nginx
    securityContext:
      allowPrivilegeEscalation: false
      runAsNonRoot: true
      capabilities:
        drop:
        - ALL
```

---

## **2. Run Containers as Non-Root**

### **Why?**
Running containers as non-root prevents potential attackers from accessing the host system with elevated privileges if the container is compromised.

### **Configuration Example**

#### YAML: Run Containers as Non-Root
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: non-root-pod
spec:
  containers:
  - name: app
    image: my-app:latest
    securityContext:
      runAsUser: 1000
      runAsGroup: 3000
      runAsNonRoot: true
```

---

## **3. Use Read-Only File Systems**

### **Why?**
A read-only file system prevents attackers from tampering with sensitive files or binaries within the container.

### **Configuration Example**

#### YAML: Read-Only Root File System
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: read-only-pod
spec:
  containers:
  - name: nginx
    image: nginx
    securityContext:
      readOnlyRootFilesystem: true
```

---

## **4. Limit Linux Capabilities**

### **Why?**
Linux capabilities provide granular control over what processes inside a container can do. Dropping unnecessary capabilities reduces the attack surface.

### **Configuration Example**

#### YAML: Drop All Capabilities
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: limited-capabilities-pod
spec:
  containers:
  - name: app
    image: my-app:latest
    securityContext:
      capabilities:
        drop:
        - ALL
```

---

## **5. Use Seccomp Profiles**

### **Why?**
Seccomp (Secure Computing Mode) restricts system calls that a container can make, reducing the risk of kernel-level exploits.

### **Configuration Example**

#### YAML: Apply a Seccomp Profile
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: seccomp-pod
spec:
  securityContext:
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: app
    image: my-app:latest
```

---

## **6. Enforce Resource Limits**

### **Why?**
Defining resource limits ensures containers cannot exhaust node resources, which could lead to Denial of Service (DoS) attacks.

### **Configuration Example**

#### YAML: Define Resource Limits
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: resource-limits-pod
spec:
  containers:
  - name: app
    image: my-app:latest
    resources:
      limits:
        memory: "512Mi"
        cpu: "500m"
      requests:
        memory: "256Mi"
        cpu: "250m"
```

---

## **7. Restrict Networking Capabilities**

### **Why?**
Applying network policies restricts container-to-container communication, reducing the risk of lateral movement in the cluster.

### **Configuration Example**

#### YAML: Apply a Network Policy
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: restrict-app-traffic
  namespace: default
spec:
  podSelector:
    matchLabels:
      app: my-app
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: trusted-service
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: database
```

---

## **8. Use Image Pull Policies**

### **Why?**
Always pulling the latest image ensures that containers run with the latest security patches.

### **Configuration Example**

#### YAML: Always Pull the Latest Image
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pull-policy-pod
spec:
  containers:
  - name: app
    image: my-app:latest
    imagePullPolicy: Always
```

---

## **9. Use Minimal Base Images**

### **Why?**
Minimal base images reduce the attack surface by including only essential binaries and dependencies.

**Best Practice**: Use images like `distroless` or `alpine`.

---

## **10. Enable Audit Logging**

### **Why?**
Audit logs provide visibility into cluster activity, enabling you to detect and respond to potential security incidents.

### **Configuration Example**

#### Enable Auditing in API Server
Modify the `kube-apiserver` configuration:
```yaml
apiVersion: kubeadm.k8s.io/v1beta2
kind: ClusterConfiguration
apiServer:
  extraArgs:
    audit-log-path: "/var/log/kubernetes/audit.log"
    audit-log-maxage: "30"
    audit-log-maxbackup: "10"
    audit-log-maxsize: "100"
```

---

## **11. Summary of Techniques**

| **Technique**                  | **Purpose**                                           | **Configuration Example**              |
|--------------------------------|-------------------------------------------------------|----------------------------------------|
| Prevent Privilege Escalation   | Avoid unauthorized privilege gain inside containers.  | `allowPrivilegeEscalation: false`      |
| Run Containers as Non-Root     | Reduce risk of host compromise.                       | `runAsNonRoot: true`                   |
| Read-Only File System          | Prevent tampering with container files.              | `readOnlyRootFilesystem: true`         |
| Limit Linux Capabilities       | Minimize container permissions.                      | `capabilities: { drop: ALL }`          |
| Use Seccomp Profiles           | Restrict system calls to the kernel.                 | `seccompProfile: RuntimeDefault`       |
| Enforce Resource Limits        | Prevent resource exhaustion.                         | Define memory and CPU limits.          |
| Apply Network Policies         | Restrict communication between pods.                 | Use `networking.k8s.io/v1` policies.   |
| Pull Latest Images             | Ensure containers use updated images.               | `imagePullPolicy: Always`              |

---

By implementing these configurations, you can align your Kubernetes environment with the **CIS Kubernetes Benchmarks**, significantly improving its security posture. The provided YAML examples are ready for deployment and can be customized based on your specific requirements.
