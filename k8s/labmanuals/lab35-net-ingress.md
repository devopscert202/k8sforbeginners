> For EndpointSlices, see [Lab 58: EndpointSlices](lab58-net-endpointslices.md).

# Lab 35: Ingress Controllers and HTTP Routing

## Overview
In this lab, you will learn how Kubernetes **Ingress** exposes HTTP and HTTPS traffic to Services using host-based and path-based rules, TLS termination at the edge, and a shared entry point (one controller / load balancer for many apps). You will install an Ingress controller, deploy sample applications, and build path-based, host-based, and TLS-enabled Ingress resources.

## Prerequisites
- A running Kubernetes cluster (Minikube, Kind, or any K8s cluster)
- `kubectl` CLI tool installed and configured
- Completion of [Lab 02: Creating Services](lab02-basics-creating-services.md)
- Basic understanding of HTTP, DNS, and load balancing
- For how Kubernetes publishes and scales **endpoints** behind Services, see [Lab 58: EndpointSlices](lab58-net-endpointslices.md)

## Learning Objectives
By the end of this lab, you will be able to:
- Understand the difference between Services and Ingress
- Install and configure an Ingress Controller
- Create Ingress resources with path-based and host-based routing
- Configure TLS/SSL termination with Ingress
- Troubleshoot Ingress issues

---

## Repository YAML Files

Manifests in the repo used by this lab:

- [`k8s/labs/networking/ingress-rule.yaml`](../labs/networking/ingress-rule.yaml) — advanced Ingress with TLS (Exercise 5)

---

## Part 1: Ingress Controllers

### What is Kubernetes Ingress?

**The Problem:**
- Services (NodePort/LoadBalancer) expose individual applications
- Each LoadBalancer costs money (cloud environments)
- Managing multiple external IPs is complex
- No built-in HTTP routing (path-based, host-based)

**The Solution: Ingress**

An **Ingress** is an API object that provides HTTP/HTTPS routing to Services based on:
- **Host-based routing**: different domains → different services
- **Path-based routing**: different paths → different services
- **TLS/SSL termination**: HTTPS at edge
- **Single entry point**: one LoadBalancer for many services

### Ingress Architecture

```
Internet
    |
[Ingress Controller (nginx/traefik)]
    |
[Ingress Resource (rules)]
    |
[Services] → [Pods]
```

### Service vs Ingress

| Feature | Service (LoadBalancer) | Ingress |
|---------|----------------------|---------|
| **Layer** | Layer 4 (TCP/UDP) | Layer 7 (HTTP/HTTPS) |
| **Routing** | IP:Port only | Host/Path-based |
| **TLS** | Requires app config | Built-in termination |
| **Cost** | One LoadBalancer per service | One LoadBalancer for many services |
| **Use case** | TCP/UDP traffic | HTTP/HTTPS web traffic |

### Common Ingress Controllers

| Controller | Description | Best For |
|------------|-------------|----------|
| **NGINX** | Most popular, feature-rich | General purpose |
| **Traefik** | Modern, auto-discovery | Microservices |
| **HAProxy** | High performance | High traffic |
| **Kong** | API gateway features | APIs, plugins |
| **AWS ALB** | AWS Application Load Balancer | AWS environments |
| **GCE** | Google Cloud Load Balancer | GCP environments |

---

## Exercise 1: Install NGINX Ingress Controller

### Step 1: Install Ingress Controller (Minikube)

If using Minikube:

```bash
# Enable ingress addon
minikube addons enable ingress
```

Verify installation:
```bash
kubectl get pods -n ingress-nginx
```

Expected output:
```
NAME                                        READY   STATUS    RESTARTS   AGE
ingress-nginx-controller-xxxxx              1/1     Running   0          1m
ingress-nginx-admission-create-xxxxx        0/1     Completed 0          1m
ingress-nginx-admission-patch-xxxxx         0/1     Completed 0          1m
```

### Step 2: Install Ingress Controller (Standard Kubernetes)

For non-Minikube clusters:

```bash
# Install NGINX Ingress Controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml
```

Wait for the controller to be ready:
```bash
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=120s
```

### Step 3: Verify Ingress Controller Service

```bash
kubectl get service -n ingress-nginx
```

Expected output:
```
NAME                                 TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)
ingress-nginx-controller             LoadBalancer   10.96.100.50    <pending>     80:30080/TCP,443:30443/TCP
```

**Note**: On Minikube, EXTERNAL-IP stays `<pending>` - that's normal!

### Step 4: Check Ingress Class

```bash
kubectl get ingressclass
```

Expected output:
```
NAME    CONTROLLER             PARAMETERS   AGE
nginx   k8s.io/ingress-nginx   <none>       2m
```

---

## Exercise 2: Create Sample Applications

### Step 1: Create First Application (App1)

```bash
# Create deployment
kubectl create deployment app1 --image=hashicorp/http-echo --replicas=2 -- -text="App1: Hello from application 1"

# Expose as service
kubectl expose deployment app1 --port=5678 --target-port=5678 --name=app1-service
```

Verify:
```bash
kubectl get deployment app1
kubectl get service app1-service
```

### Step 2: Create Second Application (App2)

```bash
# Create deployment
kubectl create deployment app2 --image=hashicorp/http-echo --replicas=2 -- -text="App2: Hello from application 2"

# Expose as service
kubectl expose deployment app2 --port=5678 --target-port=5678 --name=app2-service
```

Verify:
```bash
kubectl get deployment app2
kubectl get service app2-service
```

### Step 3: Create Third Application (MyApp1)

```bash
# Create deployment
kubectl create deployment myapp1 --image=nginx --replicas=2

# Expose as service
kubectl expose deployment myapp1 --port=80 --target-port=80 --name=myapp1
```

Verify all applications:
```bash
kubectl get deployments
kubectl get services
```

Expected output:
```
NAME     READY   UP-TO-DATE   AVAILABLE   AGE
app1     2/2     2            2           1m
app2     2/2     2            2           1m
myapp1   2/2     2            2           1m

NAME           TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)
app1-service   ClusterIP   10.96.100.101    <none>        5678/TCP
app2-service   ClusterIP   10.96.100.102    <none>        5678/TCP
myapp1         ClusterIP   10.96.100.103    <none>        80/TCP
```

---

## Exercise 3: Create Path-Based Ingress

### Step 1: Create Simple Path-Based Ingress

```bash
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: path-based-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx
  rules:
  - http:
      paths:
      - path: /app1
        pathType: Prefix
        backend:
          service:
            name: app1-service
            port:
              number: 5678
      - path: /app2
        pathType: Prefix
        backend:
          service:
            name: app2-service
            port:
              number: 5678
EOF
```

**Understanding the manifest:**
- `annotations.nginx.ingress.kubernetes.io/rewrite-target: /` - Rewrites URL path
- `ingressClassName: nginx` - Uses NGINX Ingress Controller
- `rules[0].http.paths` - Multiple path-based routes
  - `/app1` → app1-service
  - `/app2` → app2-service
- `pathType: Prefix` - Matches path prefix

Expected output:
```
ingress.networking.k8s.io/path-based-ingress created
```

### Step 2: Verify Ingress

```bash
kubectl get ingress
```

Expected output:
```
NAME                 CLASS   HOSTS   ADDRESS         PORTS   AGE
path-based-ingress   nginx   *       192.168.49.2    80      30s
```

Get detailed information:
```bash
kubectl describe ingress path-based-ingress
```

Look for:
- **Rules**: Shows path mappings
- **Backend**: Shows target services
- **Events**: Shows ingress creation/updates

### Step 3: Test Path-Based Routing

**Using Minikube:**

Get Minikube IP:
```bash
minikube ip
```

Test the routes:
```bash
# Test /app1
curl http://$(minikube ip)/app1

# Expected: "App1: Hello from application 1"

# Test /app2
curl http://$(minikube ip)/app2

# Expected: "App2: Hello from application 2"
```

**Using port-forward (alternative):**

```bash
# Port forward the ingress controller
kubectl port-forward -n ingress-nginx service/ingress-nginx-controller 8080:80
```

In another terminal:
```bash
curl http://localhost:8080/app1
curl http://localhost:8080/app2
```

---

## Exercise 4: Create Host-Based Ingress

### Step 1: Create Host-Based Ingress

```bash
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: host-based-ingress
spec:
  ingressClassName: nginx
  rules:
  - host: app1.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: app1-service
            port:
              number: 5678
  - host: app2.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: app2-service
            port:
              number: 5678
EOF
```

**Understanding the manifest:**
- Different `host` values route to different services
- `app1.example.com` → app1-service
- `app2.example.com` → app2-service
- Both use root path `/`

Expected output:
```
ingress.networking.k8s.io/host-based-ingress created
```

### Step 2: Configure Local DNS (for testing)

Since we don't own these domains, we'll use /etc/hosts:

**On Linux/Mac:**
```bash
# Get Minikube IP
MINIKUBE_IP=$(minikube ip)

# Add to /etc/hosts
echo "$MINIKUBE_IP app1.example.com app2.example.com" | sudo tee -a /etc/hosts
```

**On Windows:**
Edit `C:\Windows\System32\drivers\etc\hosts` (as Administrator):
```
192.168.49.2 app1.example.com app2.example.com
```

### Step 3: Test Host-Based Routing

```bash
# Test app1.example.com
curl http://app1.example.com

# Expected: "App1: Hello from application 1"

# Test app2.example.com
curl http://app2.example.com

# Expected: "App2: Hello from application 2"
```

**Alternative (using Host header):**
```bash
curl -H "Host: app1.example.com" http://$(minikube ip)
curl -H "Host: app2.example.com" http://$(minikube ip)
```

---

## Exercise 5: Advanced Ingress with TLS

### Step 1: Create Self-Signed Certificate

```bash
# Generate private key
openssl genrsa -out tls.key 2048

# Generate certificate
openssl req -new -x509 -key tls.key -out tls.cert -days 360 -subj "/CN=master.example.com"
```

### Step 2: Create Kubernetes Secret

```bash
kubectl create secret tls tls-cert --cert=tls.cert --key=tls.key
```

Verify:
```bash
kubectl get secret tls-cert
```

Expected output:
```
NAME       TYPE                DATA   AGE
tls-cert   kubernetes.io/tls   2      10s
```

### Step 3: Review the Advanced Ingress Manifest

Navigate to the labs directory:
```bash
cd k8s/labs/networking
```

Let's examine `ingress-rule.yaml`:

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

**Understanding the manifest:**
- `tls` section - Enables HTTPS
- `hosts` - Domain name for the certificate
- `secretName: tls-cert` - Reference to TLS secret
- `annotations.nginx.ingress.kubernetes.io/rewrite-target: /$2` - Advanced URL rewriting

### Step 4: Deploy the Ingress

```bash
kubectl apply -f ingress-rule.yaml
```

Expected output:
```
ingress.networking.k8s.io/rewrite created
```

### Step 5: Configure Local DNS

Add to /etc/hosts:
```bash
echo "$(minikube ip) master.example.com" | sudo tee -a /etc/hosts
```

### Step 6: Test HTTPS Access

```bash
# Test HTTPS (ignore certificate warning)
curl -k https://master.example.com

# Test with verbose to see TLS handshake
curl -kv https://master.example.com
```

**Expected**: You'll see the nginx welcome page over HTTPS!

**Note**: `-k` ignores certificate validation (needed for self-signed certs)

---

## Lab Cleanup

Remove Ingress-related resources from this lab:

```bash
# Delete Ingress resources
kubectl delete ingress path-based-ingress host-based-ingress rewrite --ignore-not-found=true

# Delete applications
kubectl delete deployment app1 app2 myapp1 --ignore-not-found=true
kubectl delete service app1-service app2-service myapp1 --ignore-not-found=true

# Delete TLS secret
kubectl delete secret tls-cert --ignore-not-found=true

# Clean up certificates (local files)
rm -f tls.key tls.cert

# Clean up /etc/hosts (manual step)
# Remove these lines:
# - app1.example.com
# - app2.example.com
# - master.example.com

# Verify cleanup
kubectl get all,ingress,secret
```

---

## Troubleshooting Guide

### Ingress Issues

#### Issue 1: Ingress not getting IP address

**Symptoms**: ADDRESS column shows empty

**Diagnosis:**
```bash
# Check ingress controller
kubectl get pods -n ingress-nginx

# Check ingress controller logs
kubectl logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx
```

**Solutions:**
- Ensure Ingress Controller is installed and running
- For Minikube, run `minikube tunnel` in separate terminal
- Check cloud provider LoadBalancer configuration

#### Issue 2: 404 Not Found

**Symptoms**: curl returns 404

**Diagnosis:**
```bash
# Check Ingress rules
kubectl describe ingress <ingress-name>

# Check backend service exists
kubectl get service <service-name>

# Check service endpoints
kubectl get endpoints <service-name>
```

**Common causes:**
- Service name mismatch
- Wrong path or host
- Service has no endpoints (Pods not running)

#### Issue 3: TLS certificate issues

**Symptoms**: Certificate warnings, HTTPS not working

**Diagnosis:**
```bash
# Check secret exists
kubectl get secret tls-cert

# Check secret data
kubectl get secret tls-cert -o yaml

# Verify certificate
kubectl get secret tls-cert -o jsonpath='{.data.tls\.crt}' | base64 -d | openssl x509 -text -noout
```

**Solutions:**
- Verify secret name matches Ingress spec
- Ensure certificate includes correct domain name
- Check certificate expiration date

---

## Key Takeaways

### Ingress

1. **Ingress** provides Layer 7 (HTTP/HTTPS) routing
2. **Ingress Controller** implements the routing logic (nginx, traefik, etc.)
3. **Path-based routing** routes by URL path (/app1, /app2)
4. **Host-based routing** routes by domain name (app1.com, app2.com)
5. **TLS termination** handles HTTPS at the edge
6. One **LoadBalancer** serves many applications
7. Always specify **ingressClassName**
8. Use **annotations** for controller-specific features

---

## Best Practices

### Ingress Best Practices

1. **Use TLS for production**
```yaml
tls:
- hosts:
  - myapp.example.com
  secretName: myapp-tls
```

2. **Set resource limits on Ingress Controller**
```yaml
resources:
  requests:
    cpu: 100m
    memory: 90Mi
  limits:
    cpu: 1000m
    memory: 512Mi
```

3. **Use meaningful annotations**
```yaml
annotations:
  nginx.ingress.kubernetes.io/rate-limit: "100"
  nginx.ingress.kubernetes.io/ssl-redirect: "true"
```

4. **Implement health checks**
```yaml
annotations:
  nginx.ingress.kubernetes.io/health-check-path: "/health"
```

5. **Use host-based routing for multi-tenant**
```yaml
rules:
- host: tenant1.example.com
- host: tenant2.example.com
```

---

## Additional Commands Reference

```bash
# Ingress commands
kubectl get ingress --all-namespaces
kubectl describe ingress <name>
kubectl get ingress <name> -o yaml
kubectl edit ingress <name>

# Check Ingress Controller
kubectl get pods -n ingress-nginx
kubectl logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx -f

# Test Ingress
curl -H "Host: myapp.com" http://<ingress-ip>
curl -kv https://myapp.com  # -k ignores cert validation
```

---

## Next Steps

- Continue with [Lab 58: EndpointSlices](lab58-net-endpointslices.md) to learn how Kubernetes publishes endpoints for Services.
- Explore [Lab 44: Gateway API](lab44-net-gateway-api.md) for the next-generation API for L7 routing.
- Automate TLS with [cert-manager](https://cert-manager.io/docs/) for production Ingress.

---

## Additional Reading

- [Kubernetes Ingress Documentation](https://kubernetes.io/docs/concepts/services-networking/ingress/)
- [NGINX Ingress Controller](https://kubernetes.github.io/ingress-nginx/)
- [Ingress TLS Configuration](https://kubernetes.io/docs/concepts/services-networking/ingress/#tls)
- [Lab 58: EndpointSlices](lab58-net-endpointslices.md)

---

**Lab Created**: March 2026
**Compatible with**: Kubernetes 1.24+
**Tested on**: Minikube, Kind, AWS EKS, GCP GKE
