# Lab 35: Ingress Controllers and EndpointSlices

## Overview
In this lab, you will learn about Kubernetes Ingress resources for HTTP/HTTPS routing and EndpointSlices for efficient service endpoint management. You'll understand how to expose multiple services through a single entry point and how Kubernetes tracks and distributes traffic to Pod endpoints at scale.

## Prerequisites
- A running Kubernetes cluster (Minikube, Kind, or any K8s cluster)
- `kubectl` CLI tool installed and configured
- Completion of [Lab 02: Creating Services](lab02-basics-creating-services.md)
- Basic understanding of HTTP, DNS, and load balancing

## Learning Objectives
By the end of this lab, you will be able to:
- Understand the difference between Services and Ingress
- Install and configure an Ingress Controller
- Create Ingress resources with path-based and host-based routing
- Configure TLS/SSL termination with Ingress
- Understand EndpointSlices and their advantages
- Create custom EndpointSlices for external services
- Troubleshoot Ingress and endpoint issues

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

## Part 2: EndpointSlices

### What are EndpointSlices?

**The Problem with Endpoints:**
- Single Endpoints object per Service
- Doesn't scale well (100+ Pods = huge object)
- Updates cause entire object to be transmitted
- Network overhead at scale

**The Solution: EndpointSlices**

**EndpointSlices** are a scalable alternative to Endpoints:
- Split endpoints into smaller, manageable chunks
- Each slice contains max 100 endpoints
- Efficient updates (only changed slices updated)
- Better network performance
- Supports dual-stack (IPv4 + IPv6)

### EndpointSlices vs Endpoints

| Feature | Endpoints | EndpointSlices |
|---------|-----------|----------------|
| **Max size** | Unlimited (one object) | 100 endpoints per slice |
| **Scalability** | Poor (>100 Pods) | Excellent (1000+ Pods) |
| **Update efficiency** | Full object replacement | Partial updates |
| **Dual-stack** | No | Yes (IPv4 + IPv6) |
| **API** | v1 (legacy) | discovery.k8s.io/v1 |

---

## Exercise 6: Understanding EndpointSlices

### Step 1: View Existing EndpointSlices

```bash
kubectl get endpointslices
```

Expected output:
```
NAME                  ADDRESSTYPE   PORTS   ENDPOINTS              AGE
app1-service-abc123   IPv4          5678    10.244.0.5,10.244.0.6  5m
app2-service-xyz789   IPv4          5678    10.244.0.7,10.244.0.8  5m
myapp1-def456         IPv4          80      10.244.0.9,10.244.0.10 5m
```

**Notice**: Kubernetes automatically created EndpointSlices for our Services!

### Step 2: Compare with Traditional Endpoints

```bash
# View old-style Endpoints
kubectl get endpoints

# Compare with EndpointSlices
kubectl get endpointslices
```

Both show the same Pod IPs, but EndpointSlices provide additional metadata.

### Step 3: Examine EndpointSlice Details

```bash
kubectl describe endpointslice <endpointslice-name>
```

Look for:
- **Address Type**: IPv4 or IPv6
- **Endpoints**: List of Pod IPs with ready status
- **Ports**: Port configuration
- **Topology**: Zone/region information (cloud environments)

### Step 4: View EndpointSlice YAML

```bash
kubectl get endpointslice <endpointslice-name> -o yaml
```

Key fields:
```yaml
addressType: IPv4
endpoints:
- addresses:
  - "10.244.0.5"
  conditions:
    ready: true
    serving: true
    terminating: false
  nodeName: minikube
  targetRef:
    kind: Pod
    name: app1-xxxxx
ports:
- name: ""
  port: 5678
  protocol: TCP
```

---

## Exercise 7: Create Custom EndpointSlice

### What are Custom EndpointSlices?

Custom EndpointSlices allow you to:
- Route traffic to external services (outside cluster)
- Integrate legacy systems
- Create hybrid cloud/on-prem setups
- Implement custom load balancing

### Step 1: Navigate to Lab Directory

```bash
cd k8s/labs/networking
```

### Step 2: Review the EndpointSlice Manifest

Let's examine `endpointslices.yaml`:

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

**Understanding the manifest:**
- `apiVersion: discovery.k8s.io/v1` - EndpointSlice API
- `labels.kubernetes.io/service-name` - Associates with a Service
- `addressType: IPv4` - IP version
- `ports` - Port configuration
- `endpoints` - List of endpoint addresses
  - `addresses` - IP addresses to route to
  - `conditions.ready: true` - Endpoint is ready to receive traffic
  - `hostname`, `nodeName`, `zone` - Topology information

### Step 3: Create a Service for Custom Endpoints

First, create a Service without selector (manual endpoint management):

```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Service
metadata:
  name: endpoint-slice-example
spec:
  ports:
  - port: 80
    targetPort: 80
    protocol: TCP
EOF
```

**Note**: No `selector` - this Service won't automatically discover Pods!

### Step 4: Deploy the Custom EndpointSlice

```bash
kubectl apply -f endpointslices.yaml
```

Expected output:
```
endpointslice.discovery.k8s.io/custom-endpoint-slice created
```

### Step 5: Verify the Association

```bash
# Check the Service
kubectl get service endpoint-slice-example

# Check the EndpointSlice
kubectl get endpointslice custom-endpoint-slice

# Verify the label association
kubectl get endpointslice custom-endpoint-slice -o jsonpath='{.metadata.labels.kubernetes\.io/service-name}'
```

Expected output: `endpoint-slice-example`

### Step 6: Describe the EndpointSlice

```bash
kubectl describe endpointslice custom-endpoint-slice
```

Output shows:
```
Address Type:  IPv4
Ports:
  Name     Port  Protocol
  ----     ----  --------
  http     80    TCP
Endpoints:
  - Addresses:  172.31.2.237
    Conditions:
      Ready:    true
    Hostname:   pod-1
    NodeName:   node-1
    Zone:       us-west2-a
```

### Step 7: Test the Custom EndpointSlice (Optional)

**Note**: This will only work if 172.31.2.237 is actually reachable from your cluster!

```bash
# Try to access the service
kubectl run test --image=busybox --rm -it --restart=Never -- wget -qO- http://endpoint-slice-example
```

If the IP is not reachable, you'll see a timeout (expected for this example).

### Step 8: Create a Working Example with Real Endpoints

Let's create a practical example:

```bash
# Create a deployment
kubectl create deployment web --image=nginx --replicas=2

# Get Pod IPs
kubectl get pods -l app=web -o wide

# Create Service without selector
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Service
metadata:
  name: manual-service
spec:
  ports:
  - port: 80
    targetPort: 80
EOF

# Create EndpointSlice with actual Pod IPs
POD_IP_1=$(kubectl get pod -l app=web -o jsonpath='{.items[0].status.podIP}')
POD_IP_2=$(kubectl get pod -l app=web -o jsonpath='{.items[1].status.podIP}')

cat <<EOF | kubectl apply -f -
apiVersion: discovery.k8s.io/v1
kind: EndpointSlice
metadata:
  name: manual-endpoints
  labels:
    kubernetes.io/service-name: manual-service
addressType: IPv4
ports:
- name: http
  protocol: TCP
  port: 80
endpoints:
- addresses:
  - "$POD_IP_1"
  conditions:
    ready: true
- addresses:
  - "$POD_IP_2"
  conditions:
    ready: true
EOF
```

Test it:
```bash
kubectl run test --image=busybox --rm -it --restart=Never -- wget -qO- http://manual-service
```

This should work! Traffic routes through the Service to the manually configured endpoints.

---

## Exercise 8: EndpointSlice Use Cases

### Use Case 1: External Database Service

Route traffic to external database:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: external-postgres
spec:
  ports:
  - port: 5432
    protocol: TCP
---
apiVersion: discovery.k8s.io/v1
kind: EndpointSlice
metadata:
  name: external-postgres-endpoints
  labels:
    kubernetes.io/service-name: external-postgres
addressType: IPv4
ports:
- port: 5432
  protocol: TCP
endpoints:
- addresses:
  - "192.168.1.50"  # External database IP
  conditions:
    ready: true
```

**Use case**: Legacy database that can't run in Kubernetes

### Use Case 2: Multi-Region Service

Create geo-distributed endpoints:

```yaml
apiVersion: discovery.k8s.io/v1
kind: EndpointSlice
metadata:
  name: global-api-us-west
  labels:
    kubernetes.io/service-name: global-api
addressType: IPv4
ports:
- port: 443
  protocol: TCP
endpoints:
- addresses:
  - "10.1.0.50"
  conditions:
    ready: true
  zone: us-west-1a
---
apiVersion: discovery.k8s.io/v1
kind: EndpointSlice
metadata:
  name: global-api-us-east
  labels:
    kubernetes.io/service-name: global-api
addressType: IPv4
ports:
- port: 443
  protocol: TCP
endpoints:
- addresses:
  - "10.2.0.50"
  conditions:
    ready: true
  zone: us-east-1a
```

**Use case**: Multi-region failover, topology-aware routing

### Use Case 3: Hybrid Cloud

Mix in-cluster and external endpoints:

```yaml
apiVersion: discovery.k8s.io/v1
kind: EndpointSlice
metadata:
  name: hybrid-service
  labels:
    kubernetes.io/service-name: hybrid-app
addressType: IPv4
ports:
- port: 8080
  protocol: TCP
endpoints:
- addresses:
  - "10.244.0.10"  # In-cluster Pod
  conditions:
    ready: true
  nodeName: k8s-node-1
- addresses:
  - "192.168.1.100"  # On-prem server
  conditions:
    ready: true
```

**Use case**: Gradual migration to Kubernetes

---

## Lab Cleanup

Remove all resources created in this lab:

```bash
# Delete Ingress resources
kubectl delete ingress path-based-ingress host-based-ingress rewrite --ignore-not-found=true

# Delete applications
kubectl delete deployment app1 app2 myapp1 web --ignore-not-found=true
kubectl delete service app1-service app2-service myapp1 endpoint-slice-example manual-service --ignore-not-found=true

# Delete EndpointSlices
kubectl delete endpointslice custom-endpoint-slice manual-endpoints --ignore-not-found=true

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
kubectl get all,ingress,endpointslice,secret
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

### EndpointSlice Issues

#### Issue 1: Service not routing to endpoints

**Diagnosis:**
```bash
# Check EndpointSlice exists
kubectl get endpointslice

# Check label matches service name
kubectl get endpointslice <name> -o jsonpath='{.metadata.labels.kubernetes\.io/service-name}'

# Verify endpoint IPs are reachable
kubectl run test --image=busybox --rm -it -- ping <endpoint-ip>
```

**Solutions:**
- Verify `kubernetes.io/service-name` label matches Service name exactly
- Ensure endpoint IPs are reachable from cluster
- Check `conditions.ready: true` is set

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

### EndpointSlices

1. **EndpointSlices** are the modern replacement for Endpoints
2. Scales better for large deployments (100+ Pods)
3. More efficient updates (partial vs full)
4. Supports **topology-aware routing** (zones, regions)
5. Custom EndpointSlices enable **external service integration**
6. Label `kubernetes.io/service-name` associates with Service
7. Use for **hybrid cloud**, **legacy integration**, **external services**

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

### EndpointSlice Best Practices

1. **Let Kubernetes manage when possible** - Don't create custom unless needed

2. **Use for external services only**
```yaml
# Good: external database
- addresses: ["192.168.1.50"]

# Bad: in-cluster Pods (use Service selector instead)
```

3. **Set ready conditions properly**
```yaml
conditions:
  ready: true      # Endpoint can receive traffic
  serving: true    # Endpoint is serving requests
  terminating: false  # Endpoint is not shutting down
```

4. **Include topology information**
```yaml
zone: us-west-1a
nodeName: node-1
```

5. **Monitor endpoint health**
```bash
kubectl get endpointslice -w
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

# EndpointSlice commands
kubectl get endpointslices
kubectl describe endpointslice <name>
kubectl get endpointslice <name> -o yaml

# Watch endpoint changes
kubectl get endpointslice -w

# Filter by service
kubectl get endpointslice -l kubernetes.io/service-name=myservice

# Debug tools
kubectl run netshoot --rm -it --image=nicolaka/netshoot -- bash
# Inside pod: curl, dig, nslookup, traceroute, etc.
```

---

## Next Steps

1. **Practice**: Deploy a multi-service application with Ingress
2. **Advanced**: Explore service mesh (Istio/Linkerd) for more routing features
3. **Security**: Implement cert-manager for automated TLS certificates
4. **Monitoring**: Set up Prometheus scraping of Ingress metrics

---

## Additional Reading

- [Kubernetes Ingress Documentation](https://kubernetes.io/docs/concepts/services-networking/ingress/)
- [NGINX Ingress Controller](https://kubernetes.github.io/ingress-nginx/)
- [EndpointSlices Documentation](https://kubernetes.io/docs/concepts/services-networking/endpoint-slices/)
- [Ingress TLS Configuration](https://kubernetes.io/docs/concepts/services-networking/ingress/#tls)
- [Topology Aware Routing](https://kubernetes.io/docs/concepts/services-networking/topology-aware-routing/)

---

**Lab Created**: March 2026
**Compatible with**: Kubernetes 1.24+
**Tested on**: Minikube, Kind, AWS EKS, GCP GKE
