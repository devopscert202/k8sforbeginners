### **Azure Kubernetes Service (AKS) — Part 3: Ingress**

---

### **1. What Ingress is**

**Ingress** is a Kubernetes API object that defines **HTTP/HTTPS routing** from outside the cluster to **Services**, usually through an **Ingress controller** (e.g. NGINX, App Gateway, Traefik). It supports hostnames, paths, TLS, and annotations for controller-specific behavior.

On AKS, controllers are often installed via **Helm** or marketplace offerings; the controller typically sits behind an Azure **LoadBalancer** Service and reconciles Ingress objects into data plane config (e.g. NGINX server blocks).

---

### **2. Controller and routing (conceptual)**

- **Install** the controller (chart/version varies); it runs as Pods plus a Service (often `LoadBalancer`) that receives traffic.
- **Deploy** backend applications and **ClusterIP** Services.
- **Create** an `Ingress` resource with `rules` mapping `host`/`path` to `service` name and port.
- **Annotations** (e.g. rewrite rules) are controller-specific; consult the NGINX Ingress [documentation](https://kubernetes.github.io/ingress-nginx/) for supported keys.

---

### **3. Illustrative multi-path Ingress**

The following shows **path-based routing** to two Services in namespace `website`. Replace the `host` with your DNS name or the controller’s public hostname as appropriate.

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: website-ingress
  namespace: website
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - host: example.contoso.com
    http:
      paths:
      - path: /site1
        pathType: Prefix
        backend:
          service:
            name: website-1-service
            port:
              number: 80
      - path: /site2
        pathType: Prefix
        backend:
          service:
            name: website-2-service
            port:
              number: 80
```

Backends are ordinary Deployments + Services; ConfigMaps or other volume sources can inject HTML or config as needed.

---

### **4. Operations notes**

- **DNS:** Production setups use Azure DNS or external DNS pointing at the controller Service IP.
- **TLS:** Use `spec.tls` on the Ingress or cert-manager for certificates.
- **Debugging:** `kubectl describe ingress`, controller Pod logs, and verifying **Endpoints** for backend Services are the first checks when routes return 404 or 502.

---

## Hands-On Labs

Practice these concepts with guided lab exercises:

| Lab | Description |
|-----|-------------|
| [Lab 35: Ingress Controllers and HTTP Routing](../../labmanuals/lab35-net-ingress.md) | Install a controller, define Ingress rules, and verify HTTP routing |
