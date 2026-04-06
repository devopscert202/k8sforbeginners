### **Ingress Controllers and TLS in Kubernetes**

An **Ingress Controller** is a specialized component that fulfills **Ingress** resources: it terminates HTTP/HTTPS (or other protocols, depending on implementation), applies routing rules, and forwards traffic to **Services**. Common implementations include NGINX Ingress, Traefik, HAProxy-based controllers, and cloud-managed ingress controllers.

**Ingress** itself is only configuration (rules, hosts, paths, TLS secrets); **a controller must be installed** in the cluster to act on those rules.

Key benefits:

- Consolidates multiple applications behind one or a few entry points.
- Supports host- and path-based routing to different Services.
- Centralizes TLS termination at the cluster edge (certificates stored as Kubernetes Secrets and referenced from Ingress).

---

### **What is Transport Layer Security (TLS)?**

TLS encrypts data in transit between clients and the ingress (or app). It provides:

- **Confidentiality** — eavesdroppers cannot read payloads.
- **Integrity** — tampering is detectable.
- **Authentication** — clients verify the server identity via the certificate chain (and optionally mutual TLS for clients).

In Kubernetes, Ingress typically references a **TLS Secret** (`kubernetes.io/tls`) containing certificate and key material for the hostnames listed under `spec.tls`.

---

### **Illustrative Ingress with TLS**

The following shows the shape of an Ingress that uses TLS, an ingress class, and path-based routing to a Service. Controller-specific **annotations** (for example rewrite rules) vary by implementation.

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: example-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /$2
spec:
  tls:
  - hosts:
      - app.example.com
    secretName: tls-cert
  ingressClassName: nginx
  rules:
  - host: app.example.com
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

**TLS Secret**: create a Secret of type `kubernetes.io/tls` with `tls.crt` and `tls.key` (from a CA-trusted cert or a self-signed cert for lab use). The Ingress `spec.tls[].secretName` must reference that Secret.

**Client access**: Clients need a hostname that resolves to the controller’s external address (load balancer, NodePort, or host network). For local testing, operators sometimes add static host entries on the client machine; in-cluster clients usually rely on cluster DNS and Service names instead.

---

### **Troubleshooting (conceptual)**

- **Ingress not taking effect**: Confirm an Ingress controller is running, `ingressClassName` matches an installed class, and the controller logs show no sync errors.
- **TLS errors**: Verify the Secret exists in the same namespace as the Ingress, keys match the `hosts` list, and the certificate is not expired.
- **404 or wrong backend**: Check path `pathType`, Service name/port, and Endpoints behind the Service.

---

## Hands-On Labs

Practice these concepts with guided lab exercises:

| Lab | Description |
|-----|-------------|
| [Lab 35: Ingress Controllers and HTTP Routing](../../labmanuals/lab35-net-ingress.md) | Deploy a controller, define Ingress rules, TLS, and verify HTTP/HTTPS routing. |
