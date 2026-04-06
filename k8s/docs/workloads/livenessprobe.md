### **Liveness and Readiness Probes in Kubernetes: A Brief Overview**

#### **What are liveness and readiness probes?**
- **Liveness probe**: Determines whether a container is still alive. If it fails repeatedly, the kubelet **restarts** the container (subject to the Pod’s restart policy).
- **Readiness probe**: Determines whether a container is ready to **receive Service traffic**. If it fails, the Pod’s endpoint is removed from matching Services until it recovers.

#### **Use cases**
1. **Liveness**: Recover from deadlocks, hung processes, or broken application state without manual intervention.
2. **Readiness**: Hold traffic during startup, migrations, or brief dependency outages; avoid sending users to Pods that cannot serve yet.

#### **Benefits**
- **Stability**: Unhealthy containers can be restarted automatically.
- **Traffic safety**: Unready Pods are excluded from load-balanced endpoints.
- **Clearer signals**: Probe success/failure shows up in Pod status and events.

---

### **Illustrative example: exec liveness probe**

The following Pod runs a script that creates `/tmp/healthy`, removes it after a delay, and then sleeps. The **liveness** probe runs `cat /tmp/healthy`; once the file is gone, the probe fails and Kubernetes restarts the container.

```yaml
apiVersion: v1
kind: Pod
metadata:
  labels:
    test: liveness
  name: liveness-exec
spec:
  containers:
  - name: liveness
    image: registry.k8s.io/busybox
    args:
    - /bin/sh
    - -c
    - touch /tmp/healthy; sleep 30; rm -rf /tmp/healthy; sleep 600
    livenessProbe:
      exec:
        command:
        - cat
        - /tmp/healthy
      initialDelaySeconds: 5
      periodSeconds: 5
```

**What to expect conceptually**
- While `/tmp/healthy` exists, the probe succeeds and the container keeps running.
- After the script removes the file, probe failures accumulate until the kubelet **kills and restarts** the container.
- **`kubectl describe pod`** on that Pod shows probe configuration and **Events** such as `Unhealthy` and `Killing` tied to probe failure.
- The **`RESTARTS`** column from **`kubectl get pod`** increases across restart cycles.

---

### **Choosing probe types**

- **`exec`**: Run a command inside the container; useful when HTTP or TCP checks do not fit.
- **`httpGet`**: Hit an HTTP endpoint; common for web services.
- **`tcpSocket`**: Open a TCP socket; common for non-HTTP listeners.
- **`grpc`**: Where supported, for gRPC health-check protocols.

Tune **`initialDelaySeconds`**, **`periodSeconds`**, **`timeoutSeconds`**, **`successThreshold`**, and **`failureThreshold`** so probes tolerate normal startup without hiding real failures.

---

### **Summary**

Liveness and readiness probes separate **“should this container be running?”** from **“should this Pod receive traffic?”**. Used well, they improve resilience and safe rollouts; misconfigured probes (too aggressive or checking the wrong signal) can cause restart loops or accidental traffic drain. Hands-on practice with probe timing and events is in the linked lab.

---

## Hands-On Labs

Practice these concepts with guided lab exercises:

| Lab | Description |
|-----|-------------|
| [Lab 9: Pod health probes](../../labmanuals/lab09-pod-health-probes.md) | Configure liveness and readiness probes, observe failures and restarts, and interpret Pod events. |
