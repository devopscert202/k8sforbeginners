### **Lab Tutorial: Setting Up an Ingress Controller with Transport Layer Security (TLS)**

This tutorial explains the purpose of Ingress controllers, the concept of Transport Layer Security, and provides a step-by-step guide for configuring an Ingress controller with TLS.

---

### **What is an Ingress Controller?**
An **Ingress Controller** is a specialized load balancer for Kubernetes that manages external access to services within a cluster. It routes HTTP and HTTPS traffic to cluster services based on defined rules (Ingress resources).

Key benefits:
- Consolidates multiple service accesses into a single entry point.
- Supports routing rules, such as host- and path-based routing.
- Simplifies SSL/TLS termination by handling certificates at the cluster edge.

---

### **What is Transport Layer Security (TLS)?**
TLS is the modern standard for securing data transmission over networks. It encrypts communication between clients and servers to ensure:
- **Confidentiality**: Prevents unauthorized access to data in transit.
- **Integrity**: Ensures data is not altered during transmission.
- **Authentication**: Verifies the identity of servers (and optionally, clients).

In Kubernetes, TLS is typically used in Ingress configurations for secure HTTPS traffic.

---

### **Lab Steps: Setting Up an Ingress Controller with TLS**

#### **Prerequisites**
- Kubernetes cluster set up.
- Tools: `kubectl`, `openssl`.

---

#### **1. Deploy the Ingress Controller**

1.1 Deploy the NGINX Ingress Controller:
```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.1.0/deploy/static/provider/cloud/deploy.yaml
```

1.2 Verify the Ingress Controller components:
```bash
kubectl get all -n ingress-nginx
kubectl get pod -n ingress-nginx
```

---

#### **2. Deploy Sample Applications**

2.1 Deploy two sample apps:
```bash
kubectl create deployment myapp1 --image=docker.io/httpd
kubectl create deployment myapp2 --image=docker.io/openshift/hello-openshift
```

2.2 Expose the apps as services:
```bash
kubectl expose deployment myapp1 --port=80
kubectl expose deployment myapp2 --port=8080
kubectl get svc
```

---

#### **3. Generate and Apply TLS Certificates**

3.1 Generate a self-signed SSL certificate:
```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout ingress.key -out ingress.crt -subj "/CN=master.example.com/O=security"
```

3.2 Create a Kubernetes secret for the certificate:
```bash
kubectl create secret tls tls-cert --key ingress.key --cert ingress.crt
```

---

#### **4. Configure and Apply Ingress Rules**

4.1 Create an Ingress rule file (`ingress-rule.yaml`):
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: rewrite
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /$2
spec:
  tls:
  - hosts:
      - master.example.com
    secretName: tls-cert
  ingressClassName: nginx
  rules:
  - host: master.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: myapp1
            port:
              number: 80
```

4.2 Apply the Ingress rule:
```bash
kubectl apply -f ingress-rule.yaml
kubectl get ingress
```

4.3 Update the `/etc/hosts` file to map `master.example.com` to the Ingress IP:
```bash
sudo vi /etc/hosts
```
Add the line:
```
<Ingress_Node_IP> master.example.com
```

---

#### **5. Verify the Configuration**

5.1 Check the Ingress service and its NodePort:
```bash
kubectl get svc -n ingress-nginx
kubectl get pod -n ingress-nginx -o wide
```

5.2 Verify the certificate:
```bash
curl -kv https://master.example.com:<NodePort>/test
```

---

### **Troubleshooting**

1. **Ingress Pods Not Running**:
   - Check the logs of the Ingress pods:
     ```bash
     kubectl logs <ingress-pod-name> -n ingress-nginx
     ```

2. **Invalid TLS Configuration**:
   - Verify the TLS secret:
     ```bash
     kubectl describe secret tls-cert
     ```

3. **Unable to Access the Application**:
   - Ensure the `/etc/hosts` entry maps correctly.
   - Check Ingress rules and service ports.

---

**Summary of Where to Add /etc/hosts Entry**
```
If curling from your local machine: Add an entry for the node's internal IP in your local /etc/hosts.
If curling from a pod inside the cluster: No need to modify /etc/hosts, as Kubernetes DNS handles service name resolution.
If curling directly from a node in the cluster: Add an entry in the /etc/hosts of that specific node (use 127.0.0.1 or the service's ClusterIP).
```

This step-by-step guide helps you set up a secure Ingress Controller with TLS to manage HTTPS traffic in a Kubernetes cluster. Let me know if you'd like further clarification on any part!
