# **Lab: Configuring DNS for Kubernetes Services and Pods**

This lab demonstrates how to configure and verify DNS in Kubernetes, ensuring proper network resolution and connectivity for services and pods. It also explores advanced DNS configurations using `hostNetwork`, `dnsPolicy`, and `dnsConfig` to handle specific use cases.

---

## **Objective**
1. Understand and verify the default DNS setup in Kubernetes.
2. Perform DNS queries to test connectivity.
3. Configure DNS policies and custom DNS configurations for pods.
4. Explore advanced configurations for `hostNetwork` and custom DNS (`dnsPolicy: None`).

---

## **Prerequisites**
- A Kubernetes cluster with tools installed: `kubectl`, `kubeadm`, `kubelet`.
- Basic knowledge of YAML files and Kubernetes commands.

---

## **1. Verifying the Default DNS Setup**

### **Step 1: Check CoreDNS Deployment**
To identify the CoreDNS deployment running in the cluster:
```bash
kubectl get deploy coredns -n kube-system
```

### **Step 2: Check CoreDNS Pods**
To list the CoreDNS pods:
```bash
kubectl get pods -l k8s-app=kube-dns -n kube-system
```

### **Step 3: Check CoreDNS Service**
To view the CoreDNS service:
```bash
kubectl get svc kube-dns -n kube-system
```

### **Step 4: Check DNS Endpoints**
To verify CoreDNS endpoints:
```bash
kubectl get endpoints kube-dns -n kube-system
kubectl describe endpoints kube-dns -n kube-system
```

---

## **2. Executing DNS Queries**

### **Step 1: Create an NGINX Deployment**
Create a YAML file for an NGINX deployment:

**`nginx.yaml`**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-nginx
spec:
  selector:
    matchLabels:
      run: my-nginx
  replicas: 2
  template:
    metadata:
      labels:
        run: my-nginx
    spec:
      containers:
      - name: my-nginx
        image: nginx
        ports:
        - containerPort: 80
```

Apply the file:
```bash
kubectl apply -f nginx.yaml
```

### **Step 2: Create a Service for NGINX**
Create a service to expose the NGINX deployment:

**`my-nginx-service.yaml`**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-nginx
spec:
  type: NodePort
  ports:
    - port: 80
      targetPort: 80
  selector:
    run: my-nginx
```

Apply the file:
```bash
kubectl apply -f my-nginx-service.yaml
```

Verify the service:
```bash
kubectl get svc my-nginx
kubectl get ep my-nginx
```

### **Step 3: Test DNS Resolution**
Run a pod with network tools to test DNS queries:
```bash
kubectl run curl --image=radial/busyboxplus:curl -i --tty
```

Inside the pod:
```bash
nslookup google.com
nslookup my-nginx
nslookup my-nginx.default.svc.cluster.local
curl my-nginx
```

Exit the pod:
```bash
exit
```

---

## **3. Advanced Configurations**

### **3.1 Configuring Host Network with DNS Policy**

**YAML File**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: busybox-hostnetwork
spec:
  containers:
  - name: busybox
    image: busybox:1.28
    command: ["sleep", "3600"]
  hostNetwork: true
  dnsPolicy: ClusterFirstWithHostNet
```

**Explanation**:
- **`hostNetwork: true`**: The pod uses the host's network stack, sharing its IP and bypassing Kubernetes networking.
- **`dnsPolicy: ClusterFirstWithHostNet`**: Ensures the pod can resolve both Kubernetes service names and external DNS names.

**Deploy and Verify**:
1. Apply the configuration:
   ```bash
   kubectl apply -f busybox-hostnetwork.yaml
   ```
2. Verify the pod:
   ```bash
   kubectl describe pod busybox-hostnetwork
   ```
3. Execute DNS queries inside the pod:
   ```bash
   kubectl exec -it busybox-hostnetwork -- nslookup my-nginx
   ```

---

### **3.2 Configuring Custom DNS for a Pod**

**YAML File**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: custom-dns-pod
spec:
  containers:
  - name: nginx
    image: nginx
  dnsPolicy: "None"
  dnsConfig:
    nameservers:
      - 8.8.8.8
    searches:
      - my-custom.search.suffix
    options:
      - name: ndots
        value: "1"
```

**Explanation**:
- **`dnsPolicy: None`**: Disables default DNS configuration; the pod uses the custom settings provided in `dnsConfig`.
- **`dnsConfig.nameservers`**: Specifies the DNS server to use (`8.8.8.8`).
- **`dnsConfig.searches`**: Appends custom search suffixes during resolution.
- **`dnsConfig.options`**:
  - `ndots=1`: Treat names with fewer than 1 dot as incomplete and append search domains.

**Deploy and Verify**:
1. Apply the configuration:
   ```bash
   kubectl apply -f custom-dns-pod.yaml
   ```
2. Verify the pod’s DNS configuration:
   ```bash
   kubectl exec -it custom-dns-pod -- cat /etc/resolv.conf
   ```
3. Test DNS resolution:
   ```bash
   kubectl exec -it custom-dns-pod -- nslookup google.com
   ```

---

## **4. Clean Up**

To delete all resources created during this lab:
```bash
kubectl delete -f nginx.yaml
kubectl delete -f my-nginx-service.yaml
kubectl delete -f busybox-hostnetwork.yaml
kubectl delete -f custom-dns-pod.yaml
```

---

## **What We’re Accomplishing**
1. **Default DNS Validation**: Ensure Kubernetes DNS works for service discovery.
2. **Host Networking**: Validate the behavior of pods using the host network stack.
3. **Custom DNS Configuration**: Demonstrate how to override Kubernetes DNS with custom settings.

---

## **Verification**
1. Run `nslookup` commands to test DNS resolution.
2. Check `/etc/resolv.conf` in the custom DNS pod to ensure the configuration matches `dnsConfig`.

Here’s the comparison in a table format for the DNS configurations:

---

| **Configuration**                     | **Purpose**                                                                                       | **Behavior**                                                                                              |
|---------------------------------------|---------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| **`hostNetwork: true`**               | Enables the pod to use the host's network stack.                                                  | Shares the host's IP address and network while bypassing Kubernetes networking (e.g., CNI plugins).      |
| **`dnsPolicy: ClusterFirstWithHostNet`** | Ensures Kubernetes service DNS resolution works even with `hostNetwork: true`.                   | Resolves both Kubernetes service names (e.g., `my-service.default.svc.cluster.local`) and external DNS.  |
| **`dnsPolicy: None`**                 | Disables the default Kubernetes DNS setup for the pod.                                            | Requires custom DNS settings to be defined using `dnsConfig`.                                            |
| **`dnsConfig.nameservers`**           | Specifies custom DNS servers for the pod.                                                        | Overrides the default Kubernetes DNS servers (e.g., CoreDNS).                                            |
| **`dnsConfig.searches`**              | Adds custom DNS search domains for resolving short names.                                         | Appends the domains during DNS resolution (e.g., `my-service` becomes `my-service.my.dns.search.suffix`).|
| **`dnsConfig.options`**               | Customizes DNS resolution behavior.                                                              | Includes advanced settings like `ndots` (e.g., required dots for FQDN) and `edns0` (extended DNS options). |

---

### **How to Use This Table**
- Use **`hostNetwork` and `ClusterFirstWithHostNet`** for pods needing access to both Kubernetes DNS and external networks via the host.
- Use **`dnsPolicy: None` with `dnsConfig`** when you need full control over DNS settings (e.g., for testing custom DNS resolvers or specific search domains). 

This table provides a concise comparison of the DNS settings and their intended purposes in Kubernetes.
---

This combined lab covers DNS basics and advanced configurations, ensuring you have the knowledge to customize DNS for Kubernetes workloads effectively.
