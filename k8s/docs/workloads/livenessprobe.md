### **Liveness and Readiness Probes in Kubernetes: A Brief Overview**

#### **What are Liveness and Readiness Probes?**
- **Liveness Probes:** Used to determine if a container is running. If a liveness probe fails, Kubernetes will restart the container.
- **Readiness Probes:** Used to determine if a container is ready to serve traffic. If a readiness probe fails, Kubernetes removes the Pod from the Service's endpoints until it recovers.

#### **Use Cases**
1. **Liveness Probes:**
   - Restarting a container that is stuck or deadlocked.
   - Monitoring container health in long-running applications.
2. **Readiness Probes:**
   - Temporarily removing Pods from traffic during initialization or maintenance.
   - Ensuring traffic is routed only to fully operational Pods.

#### **Benefits**
- **Increased Stability:** Ensures Pods recover automatically from unhealthy states.
- **Traffic Management:** Prevents routing traffic to unready Pods.
- **Improved Fault Tolerance:** Restarts stuck containers, ensuring the application remains functional.

---

### **Commands Extracted from the PDF**

#### **Step 1: Create a Pod with Liveness Probe**

1. **Create a YAML File:**
   ```bash
   vi exec-liveness.yaml
   ```
   Add the following content:
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
       image: k8s.gcr.io/busybox
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

2. **Create the Pod:**
   ```bash
   kubectl create -f exec-liveness.yaml
   ```

3. **Check Pod Status:**
   ```bash
   kubectl get pod
   ```

---

#### **Step 2: Describe the Pod**

1. **Describe the Pod:**
   ```bash
   kubectl describe pod liveness-exec
   ```

---

### **Expected Output of Commands**

1. **`kubectl get pod`**
   Example Output:
   ```
   NAME             READY   STATUS    RESTARTS   AGE
   liveness-exec    1/1     Running   3          1m
   ```
   - **STATUS:** Shows if the Pod is running.
   - **RESTARTS:** Increases whenever the liveness probe fails.

2. **`kubectl describe pod liveness-exec`**
   Key Sections in the Output:
   - **Liveness Probe Details:**  
     ```text
     Liveness:  exec [cat /tmp/healthy] delay=5s period=5s #success=1 #failure=3
     ```
   - **Events:**  
     ```text
     Warning  Unhealthy  Liveness probe failed: cat: can't open '/tmp/healthy': No such file or directory
     Normal   Killing    Killing container with id: ...: Liveness probe failed
     ```

---

### **Demonstration: How Liveness Probe Monitors Pod Health**

#### **What Happens in the YAML Example:**
1. **Container Behavior:**
   - Initially, the script creates a file (`/tmp/healthy`) to indicate the container is healthy.
   - After 30 seconds, it deletes the file and simulates a failure by sleeping for 600 seconds.
2. **Liveness Probe Behavior:**
   - The liveness probe checks for the existence of `/tmp/healthy` every 5 seconds.
   - When the file is deleted, the probe fails, and Kubernetes restarts the container.

#### **Steps to Observe the Probe in Action:**
1. **Watch Pod Status:**
   ```bash
   kubectl get pod liveness-exec -w
   ```
   - Observe the **RESTARTS** column increase every time the liveness probe fails.

2. **View Pod Events:**
   ```bash
   kubectl describe pod liveness-exec
   ```
   - Look for failure events in the **Events** section.

3. **View Logs (Optional):**
   ```bash
   kubectl logs liveness-exec
   ```
   - Check the logs for the `touch` and `rm` commands being executed.

---

### **Summary**

**Liveness and Readiness Probes** are essential for maintaining the stability and reliability of applications in Kubernetes. By configuring the liveness probe in this example:
- The container is automatically restarted when it simulates failure by deleting `/tmp/healthy`.
- Kubernetes ensures the Pod remains functional without manual intervention.

**Benefits Demonstrated:**
- Automatic recovery from unhealthy states.
- Detailed monitoring of container health.

By using liveness probes, you can ensure high availability and fault tolerance for your applications in Kubernetes clusters.
