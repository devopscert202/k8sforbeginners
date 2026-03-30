### **What is EndpointSlice?**
EndpointSlice is a Kubernetes resource that provides a scalable and efficient way to track network endpoints (e.g., Pods) within a cluster. Introduced to address scalability issues with traditional Endpoints, it supports:
- Larger clusters.
- Distribution of network endpoints across multiple EndpointSlices.
- Better support for multi-address types (e.g., IPv4 and IPv6).

#### **When to Use EndpointSlice?**
- When managing large-scale clusters with many services and pods.
- To improve network performance and scalability.
- When leveraging advanced features like topology-aware routing or custom endpoints.

---

### **Lab Setup**

#### **Prerequisites**
- A Kubernetes cluster running (e.g., GKE, kubeadm-based, etc.).
- Tools: `kubectl`, `kubeadm`, `kubelet`, and `containerd`.
- Basic understanding of Kubernetes YAML files.

---

### **Steps**

#### **1. Create a Deployment and Identify its EndpointSlice**

1.1 **Create the Deployment YAML File**  
Save the following content to `frontend-app.yaml`:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend-app
spec:
  replicas: 3
  selector:
    matchLabels:
      run: frontend-app
  template:
    metadata:
      labels:
        run: frontend-app
    spec:
      containers:
      - name: frontend-app
        image: nginx:1.16.1
        ports:
        - containerPort: 80
```

1.2 **Apply the Deployment YAML**:
```bash
kubectl apply -f frontend-app.yaml
```

1.3 **Check Deployment Status**:
```bash
kubectl get deploy frontend-app
kubectl get pods -l run=frontend-app
```

1.4 **Expose the Deployment as a Service**:
```bash
kubectl expose deploy frontend-app --port 80 --target-port 80
```

1.5 **Identify the Service Endpoints**:
```bash
kubectl get svc frontend-app
kubectl get endpointslices
```
You’ll notice an EndpointSlice (e.g., `frontend-app-xyz12`) created for the service.

1.6 **Inspect EndpointSlice Details**:
```bash
kubectl get endpointslices <endpoint-slice-name> -o yaml
```

---

#### **2. Create a Custom EndpointSlice**

2.1 **Create a YAML File for Custom EndpointSlice Configuration**  
Save the following content to `endpoint-slice.yaml`:
```yaml
apiVersion: discovery.k8s.io/v1
kind: EndpointSlice
metadata:
  name: custom-endpoint-slice
  labels:
    kubernetes.io/service-name: endpoint-slice-example
addressType: IPv4
ports:
  - name: http
    protocol: TCP
    port: 80
endpoints:
  - addresses:
      - "172.31.2.237"
    conditions:
      ready: true
    hostname: pod-1
    nodeName: node-1
    zone: us-west2-a
```

2.2 **Apply the EndpointSlice YAML**:
```bash
kubectl apply -f endpoint-slice.yaml
```

2.3 **Verify the Resource**:
```bash
kubectl get endpointslices
kubectl describe endpointslices custom-endpoint-slice
```

---

#### **3. Troubleshooting**

- **Issue: EndpointSlice Not Created Automatically**
  - Ensure your cluster has EndpointSlice feature gate enabled.
  - Check service configuration; ensure it references `ClusterIP` or `LoadBalancer`.

- **Issue: Pods Not Listed in EndpointSlice**
  - Confirm pods are labeled correctly (`run: frontend-app`).
  - Check if the pods are healthy (`kubectl get pods`).
  
- **Issue: Custom EndpointSlice Not Applied**
  - Check YAML for errors (`kubectl describe` will provide details).
  - Ensure IP and node values are correct.

---

By following the steps above, you’ll learn how to configure EndpointSlice effectively, verify its creation, and troubleshoot common issues. Would you like to dive deeper into any part of this tutorial?
