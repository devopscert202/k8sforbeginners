# Lab 44: Gateway API - Next Generation Ingress

## Overview

In this lab, you will explore Kubernetes Gateway API, the next-generation solution for ingress traffic management. Gateway API is a significant evolution beyond traditional Ingress, providing more expressive, extensible, and role-oriented APIs for managing traffic routing in Kubernetes. You'll learn how to install Gateway API CRDs, configure Gateway resources, create routing rules with HTTPRoute, and implement advanced traffic management patterns including canary deployments and traffic splitting.

**Important Note**: This lab includes comprehensive workarounds for testing without a registered domain name, using techniques like nip.io, /etc/hosts modifications, and localhost port mapping.

## Prerequisites

- A running Kubernetes cluster (Minikube, Kind, or any K8s cluster) with version 1.26 or higher
- `kubectl` CLI tool installed and configured
- Completion of [Lab 35: Ingress Controllers and EndpointSlices](lab35-net-ingress-endpointslices.md) (recommended)
- Basic understanding of HTTP, DNS, and load balancing
- **Note**: You do NOT need a registered domain name - workarounds are provided!

## Learning Objectives

By the end of this lab, you will be able to:
- Understand what Gateway API is and why it's superior to traditional Ingress
- Install Gateway API CRDs and configure a Gateway Controller
- Create Gateway resources to define traffic entry points
- Use HTTPRoute for path-based and host-based routing
- Implement traffic splitting for canary and blue-green deployments
- Apply domain name workarounds (nip.io, /etc/hosts, localhost) for testing
- Compare Gateway API with traditional Ingress
- Troubleshoot Gateway API issues effectively

---

## Part 1: Understanding Gateway API

### What is Gateway API?

**Gateway API** is a collection of resources that model service networking in Kubernetes. It's the successor to the Ingress API, designed to improve upon its limitations.

Gateway API was introduced as an alpha feature in Kubernetes 1.18 and became Generally Available (GA) in Kubernetes 1.26.

### The Evolution: Ingress → Gateway API

**Problems with Traditional Ingress:**
1. **Limited expressiveness**: Cannot handle complex routing scenarios
2. **Vendor-specific annotations**: Each controller has different annotations
3. **Single role**: No separation of concerns (platform vs app teams)
4. **No traffic splitting**: Canary deployments require workarounds
5. **Limited protocol support**: Primarily HTTP/HTTPS
6. **No extensibility**: Hard to add new features

**Gateway API Solutions:**
1. **Expressive**: Rich routing rules with headers, query params, methods
2. **Portable**: Standard API across all implementations
3. **Role-oriented**: Separate resources for platform and app teams
4. **Built-in traffic management**: Native traffic splitting and weighting
5. **Protocol extensibility**: HTTP, HTTPS, TCP, UDP, gRPC
6. **Future-proof**: Designed for extensibility

### Gateway API Architecture

```
                    Internet
                       |
              [Gateway Resource]  ← Platform Admin manages
                       |
         +-------------+-------------+
         |                           |
   [HTTPRoute]                  [TCPRoute]  ← App Developer manages
         |                           |
   [Service] → [Pods]          [Service] → [Pods]
```

### Key Resources in Gateway API

| Resource | Role | Managed By | Purpose |
|----------|------|------------|---------|
| **GatewayClass** | Cluster-scoped | Platform Admin | Defines Gateway controller (nginx, envoy, etc.) |
| **Gateway** | Namespaced | Platform Admin | Defines infrastructure (listeners, ports, protocols) |
| **HTTPRoute** | Namespaced | App Developer | Defines HTTP routing rules |
| **TCPRoute** | Namespaced | App Developer | Defines TCP routing rules |
| **TLSRoute** | Namespaced | App Developer | Defines TLS routing rules |

### Gateway API vs Traditional Ingress

| Feature | Traditional Ingress | Gateway API |
|---------|-------------------|-------------|
| **API Maturity** | GA since K8s 1.19 | GA since K8s 1.26 |
| **Role Separation** | Single resource | Gateway (infra) + Routes (apps) |
| **Traffic Splitting** | Via annotations (vendor-specific) | Native in HTTPRoute |
| **Header Routing** | Limited/vendor-specific | First-class support |
| **Extensibility** | Annotations (non-portable) | CRDs (standardized) |
| **Protocol Support** | HTTP/HTTPS | HTTP, HTTPS, TCP, UDP, gRPC |
| **Canary/Blue-Green** | Requires workarounds | Built-in with weights |
| **Cross-namespace** | No | Yes (with ReferenceGrants) |

### When to Use Gateway API vs Ingress

**Use Gateway API if:**
- Starting a new project (Kubernetes 1.26+)
- Need advanced traffic management (canary, A/B testing)
- Want vendor-portable configuration
- Require role-based resource management
- Need TCP/UDP routing capabilities

**Use Traditional Ingress if:**
- Running Kubernetes < 1.26
- Have existing Ingress resources (migration takes time)
- Only need simple HTTP routing
- Team is familiar with Ingress

---

## Exercise 1: Install Gateway API CRDs

Gateway API is not installed by default in Kubernetes. We must install the Custom Resource Definitions (CRDs).

### Step 1: Check Kubernetes Version

Gateway API requires Kubernetes 1.26 or higher for GA features.

```bash
kubectl version --short
```

Expected output:
```
Client Version: v1.28.0
Server Version: v1.28.2
```

**Note**: If your version is < 1.26, Gateway API is available but may be in beta.

### Step 2: Install Gateway API CRDs

Install the standard Gateway API CRDs:

```bash
kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.0.0/standard-install.yaml
```

Expected output:
```
customresourcedefinition.apiextensions.k8s.io/gatewayclasses.gateway.networking.k8s.io created
customresourcedefinition.apiextensions.k8s.io/gateways.gateway.networking.k8s.io created
customresourcedefinition.apiextensions.k8s.io/httproutes.gateway.networking.k8s.io created
customresourcedefinition.apiextensions.k8s.io/referencegrants.gateway.networking.k8s.io created
```

### Step 3: Verify CRD Installation

```bash
kubectl get crd | grep gateway
```

Expected output:
```
gatewayclasses.gateway.networking.k8s.io          2024-03-16T10:30:00Z
gateways.gateway.networking.k8s.io                2024-03-16T10:30:00Z
httproutes.gateway.networking.k8s.io              2024-03-16T10:30:00Z
referencegrants.gateway.networking.k8s.io         2024-03-16T10:30:00Z
```

### Step 4: Verify API Resources

```bash
kubectl api-resources | grep gateway
```

Expected output:
```
gatewayclasses                    gc           gateway.networking.k8s.io/v1          false        GatewayClass
gateways                          gtw          gateway.networking.k8s.io/v1          true         Gateway
httproutes                                     gateway.networking.k8s.io/v1          true         HTTPRoute
referencegrants                   refgrant     gateway.networking.k8s.io/v1beta1     true         ReferenceGrant
```

**Success!** Gateway API CRDs are now installed.

---

## Exercise 2: Install Gateway Controller

A Gateway Controller implements the Gateway API. Popular options include NGINX Gateway Fabric, Envoy Gateway, Kong, and Istio.

### Option A: Install NGINX Gateway Fabric (Recommended for Beginners)

#### Step 1: Install NGINX Gateway Fabric

```bash
kubectl apply -f https://github.com/nginxinc/nginx-gateway-fabric/releases/download/v1.1.0/crds.yaml
kubectl apply -f https://github.com/nginxinc/nginx-gateway-fabric/releases/download/v1.1.0/nginx-gateway.yaml
```

#### Step 2: Wait for Deployment

```bash
kubectl wait --namespace nginx-gateway \
  --for=condition=available deployment/nginx-gateway \
  --timeout=90s
```

Expected output:
```
deployment.apps/nginx-gateway condition met
```

#### Step 3: Verify Installation

```bash
kubectl get pods -n nginx-gateway
```

Expected output:
```
NAME                             READY   STATUS    RESTARTS   AGE
nginx-gateway-5d4f8b7c9d-xxxxx   2/2     Running   0          2m
```

#### Step 4: Check GatewayClass

```bash
kubectl get gatewayclass
```

Expected output:
```
NAME    CONTROLLER                            ACCEPTED   AGE
nginx   gateway.nginx.org/nginx-gateway-controller   True       2m
```

### Option B: Install Envoy Gateway (Alternative)

```bash
# Install Envoy Gateway
kubectl apply -f https://github.com/envoyproxy/gateway/releases/download/v0.6.0/install.yaml

# Wait for deployment
kubectl wait --namespace envoy-gateway-system \
  --for=condition=available deployment/envoy-gateway \
  --timeout=90s

# Verify
kubectl get pods -n envoy-gateway-system
```

### Option C: Using Minikube (Easiest)

If using Minikube, you might need to enable gateway features:

```bash
# Start minikube with sufficient resources
minikube start --cpus=4 --memory=8192

# Install Gateway API CRDs (as in Exercise 1)
kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.0.0/standard-install.yaml
```

Then follow Option A or B to install a Gateway controller.

---

## Exercise 3: Deploy Backend Applications

Before creating Gateway resources, let's deploy some backend applications to route traffic to.

### Step 1: Navigate to Lab Directory

```bash
cd k8s/labs/networking/gateway-api
```

### Step 2: Review Backend Services

Let's examine `backend-services.yaml`. This file contains:
- **App1 Blue** (Version 1.0) - Stable version
- **App1 Green** (Version 2.0) - New version for canary testing
- **App2** - Second application for routing examples
- **App3** - Nginx application for comparison

```bash
cat backend-services.yaml
```

Key points:
- All apps use `hashicorp/http-echo` or `nginx` images
- Each has labels for version tracking
- Services are ClusterIP (not exposed externally yet)
- Resource limits are defined for production readiness

### Step 3: Deploy Backend Applications

```bash
kubectl apply -f backend-services.yaml
```

Expected output:
```
deployment.apps/app1-blue created
deployment.apps/app1-green created
service/app1-blue-service created
service/app1-green-service created
deployment.apps/app2 created
service/app2-service created
deployment.apps/app3-nginx created
service/app3-service created
```

### Step 4: Verify Deployments

```bash
kubectl get deployments
```

Expected output:
```
NAME          READY   UP-TO-DATE   AVAILABLE   AGE
app1-blue     2/2     2            2           1m
app1-green    2/2     2            2           1m
app2          2/2     2            2           1m
app3-nginx    2/2     2            2           1m
```

### Step 5: Verify Services

```bash
kubectl get services
```

Expected output:
```
NAME                  TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)    AGE
app1-blue-service     ClusterIP   10.96.100.10     <none>        8080/TCP   1m
app1-green-service    ClusterIP   10.96.100.11     <none>        8080/TCP   1m
app2-service          ClusterIP   10.96.100.12     <none>        8080/TCP   1m
app3-service          ClusterIP   10.96.100.13     <none>        80/TCP     1m
```

### Step 6: Test Services (Internal)

Test that services work before adding Gateway:

```bash
# Test app1-blue
kubectl run test --image=busybox --rm -it --restart=Never -- wget -qO- http://app1-blue-service:8080

# Expected: "App1 Blue - Version 1.0"

# Test app1-green
kubectl run test --image=busybox --rm -it --restart=Never -- wget -qO- http://app1-green-service:8080

# Expected: "App1 Green - Version 2.0"
```

**Success!** Backend applications are ready.

---

## Exercise 4: Create Your First Gateway

A Gateway defines the infrastructure for accepting traffic. Think of it as the "load balancer" configuration.

### Step 1: Review Gateway Manifest

Let's examine `gateway.yaml`:

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: my-gateway
  namespace: default
spec:
  gatewayClassName: nginx
  listeners:
  - name: http
    protocol: HTTP
    port: 80
    allowedRoutes:
      namespaces:
        from: Same
```

**Understanding the manifest:**
- `gatewayClassName: nginx` - Uses NGINX Gateway controller
- `listeners` - Defines how to accept traffic
  - `name: http` - Listener name (can have multiple)
  - `protocol: HTTP` - Protocol type (HTTP, HTTPS, TCP, UDP)
  - `port: 80` - Port to listen on
  - `allowedRoutes.namespaces.from: Same` - Only routes in same namespace allowed

### Step 2: Create the Gateway

```bash
kubectl apply -f gateway.yaml
```

Expected output:
```
gateway.gateway.networking.k8s.io/my-gateway created
```

### Step 3: Check Gateway Status

```bash
kubectl get gateway
```

Expected output:
```
NAME         CLASS   ADDRESS        PROGRAMMED   AGE
my-gateway   nginx   10.96.100.50   True         30s
```

**Key fields:**
- **CLASS**: GatewayClass being used
- **ADDRESS**: External IP or internal service IP
- **PROGRAMMED**: True means controller configured it successfully

### Step 4: Describe Gateway (Detailed Info)

```bash
kubectl describe gateway my-gateway
```

Look for:
- **Status**: Should show "Programmed: True"
- **Listeners**: Configuration of the HTTP listener
- **Events**: Any issues will appear here

### Step 5: Get Gateway IP/Hostname

This is crucial for testing later!

```bash
# Get the Gateway address
kubectl get gateway my-gateway -o jsonpath='{.status.addresses[0].value}'
```

**Save this value** - you'll need it for testing!

**For Minikube users:**
```bash
# Get Minikube IP instead
minikube ip
```

**For Kind users:**
```bash
# Kind requires port forwarding (covered in Exercise 5)
kubectl get service -n nginx-gateway
```

---

## Exercise 5: Domain Name Workarounds (CRITICAL)

**Most Important Section!** Since you likely don't own a domain, here are comprehensive workarounds.

### Understanding the Domain Name Challenge

Gateway API (and Ingress) uses the HTTP `Host` header for routing. When you request `http://app1.example.com`, your browser sends `Host: app1.example.com` in the HTTP request.

**The Problem:**
- You don't own `example.com`
- DNS won't resolve `app1.example.com` to your cluster
- HTTPRoute rules with hostnames won't work

**Three Solutions:**
1. **nip.io** - Wildcard DNS service (easiest)
2. **/etc/hosts** - Local DNS override (most reliable)
3. **localhost ports** - Port forwarding (simplest)

---

### Workaround 1: Using nip.io (Recommended)

**What is nip.io?**
nip.io is a free DNS service that resolves any IP address embedded in a domain name.

**Examples:**
- `app1.192.168.49.2.nip.io` → resolves to `192.168.49.2`
- `test.10.0.0.5.nip.io` → resolves to `10.0.0.5`
- `anything.127.0.0.1.nip.io` → resolves to `127.0.0.1`

#### Step 1: Get Your Gateway IP

```bash
# For most setups
GATEWAY_IP=$(kubectl get gateway my-gateway -o jsonpath='{.status.addresses[0].value}')
echo "Gateway IP: $GATEWAY_IP"

# For Minikube
GATEWAY_IP=$(minikube ip)
echo "Gateway IP: $GATEWAY_IP"

# For Kind (use 127.0.0.1 after port-forward)
GATEWAY_IP="127.0.0.1"
```

#### Step 2: Create HTTPRoute with nip.io Hostnames

Create a file `httproute-nipio.yaml`:

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: nipio-route
  namespace: default
spec:
  parentRefs:
  - name: my-gateway

  # Replace <GATEWAY-IP> with actual IP
  hostnames:
  - "app1.${GATEWAY_IP}.nip.io"

  rules:
  - backendRefs:
    - name: app1-blue-service
      port: 8080
```

Apply with environment variable substitution:

```bash
# Create the route with your Gateway IP
cat <<EOF | kubectl apply -f -
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: nipio-route-app1
  namespace: default
spec:
  parentRefs:
  - name: my-gateway
  hostnames:
  - "app1.${GATEWAY_IP}.nip.io"
  rules:
  - backendRefs:
    - name: app1-blue-service
      port: 8080
EOF
```

#### Step 3: Test with nip.io

```bash
# Test the route
curl http://app1.${GATEWAY_IP}.nip.io

# Expected: "App1 Blue - Version 1.0"
```

#### Step 4: Create Additional Routes

```bash
# App2 route
cat <<EOF | kubectl apply -f -
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: nipio-route-app2
spec:
  parentRefs:
  - name: my-gateway
  hostnames:
  - "app2.${GATEWAY_IP}.nip.io"
  rules:
  - backendRefs:
    - name: app2-service
      port: 8080
EOF

# Test
curl http://app2.${GATEWAY_IP}.nip.io
```

**Advantages of nip.io:**
- No configuration needed
- Works from any machine
- Real DNS resolution
- Great for demos and testing

**Disadvantages:**
- Requires internet connection
- External dependency
- Can be blocked by corporate firewalls

---

### Workaround 2: Using /etc/hosts (Most Reliable)

Modify your local hosts file to map hostnames to the Gateway IP.

#### Step 1: Get Gateway IP

```bash
# Get the IP
GATEWAY_IP=$(kubectl get gateway my-gateway -o jsonpath='{.status.addresses[0].value}' 2>/dev/null)

# If empty, use Minikube IP
if [ -z "$GATEWAY_IP" ]; then
  GATEWAY_IP=$(minikube ip 2>/dev/null)
fi

# If still empty, use service IP
if [ -z "$GATEWAY_IP" ]; then
  GATEWAY_IP=$(kubectl get service -n nginx-gateway nginx-gateway -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
fi

echo "Gateway IP: $GATEWAY_IP"
```

#### Step 2: Edit /etc/hosts

**On Linux/Mac:**

```bash
# Add entries to /etc/hosts
echo "$GATEWAY_IP app1.example.local app2.example.local app3.example.local" | sudo tee -a /etc/hosts
```

**On Windows:**

1. Open Notepad as Administrator
2. Open `C:\Windows\System32\drivers\etc\hosts`
3. Add these lines:
```
192.168.49.2 app1.example.local
192.168.49.2 app2.example.local
192.168.49.2 app3.example.local
```
4. Save and close

**Verify:**
```bash
# Test DNS resolution
ping app1.example.local

# Should resolve to your Gateway IP
```

#### Step 3: Create HTTPRoutes with Local Domains

```bash
# Create route for app1.example.local
cat <<EOF | kubectl apply -f -
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: hosts-route-app1
spec:
  parentRefs:
  - name: my-gateway
  hostnames:
  - "app1.example.local"
  rules:
  - backendRefs:
    - name: app1-blue-service
      port: 8080
EOF

# Create route for app2.example.local
cat <<EOF | kubectl apply -f -
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: hosts-route-app2
spec:
  parentRefs:
  - name: my-gateway
  hostnames:
  - "app2.example.local"
  rules:
  - backendRefs:
    - name: app2-service
      port: 8080
EOF
```

#### Step 4: Test with Local Domains

```bash
# Test app1
curl http://app1.example.local

# Expected: "App1 Blue - Version 1.0"

# Test app2
curl http://app2.example.local

# Expected: "App2 - Hello from Application 2"

# Test in browser
# Open: http://app1.example.local
```

**Advantages of /etc/hosts:**
- Works offline
- No external dependencies
- Fast and reliable
- Great for development

**Disadvantages:**
- Only works on the machine where configured
- Requires admin/sudo access
- Manual cleanup needed
- Different process per OS

---

### Workaround 3: Using Localhost with Port Forwarding (Simplest)

Use `kubectl port-forward` to expose the Gateway on localhost.

#### Step 1: Start Port Forward

```bash
# Forward Gateway service to localhost:8080
kubectl port-forward -n nginx-gateway service/nginx-gateway 8080:80
```

**Keep this terminal open!**

#### Step 2: Create HTTPRoutes (In Another Terminal)

```bash
# Create routes using localhost
cat <<EOF | kubectl apply -f -
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: localhost-route-app1
spec:
  parentRefs:
  - name: my-gateway
  hostnames:
  - "localhost"
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /app1
    backendRefs:
    - name: app1-blue-service
      port: 8080
  - matches:
    - path:
        type: PathPrefix
        value: /app2
    backendRefs:
    - name: app2-service
      port: 8080
EOF
```

#### Step 3: Test via Localhost

```bash
# Test app1
curl http://localhost:8080/app1

# Expected: "App1 Blue - Version 1.0"

# Test app2
curl http://localhost:8080/app2

# Expected: "App2 - Hello from Application 2"
```

**Alternative: Use Host Header**

```bash
# Test with Host header (doesn't require /etc/hosts)
curl -H "Host: app1.example.local" http://localhost:8080

# This works with the host-based routes!
```

**Advantages:**
- No system configuration
- Easy to start/stop
- Works on any OS
- Great for quick testing

**Disadvantages:**
- Terminal must stay open
- Only accessible from localhost
- Port might conflict with other services
- Not suitable for team testing

---

### Workaround 4: Using curl with Host Header (Testing Only)

If you have HTTPRoutes configured with specific hostnames but can't modify DNS, use the Host header.

```bash
# Get Gateway IP
GATEWAY_IP=$(kubectl get gateway my-gateway -o jsonpath='{.status.addresses[0].value}')

# Test with Host header
curl -H "Host: app1.example.local" http://$GATEWAY_IP

# Or for Minikube
curl -H "Host: app1.example.local" http://$(minikube ip)
```

This sends the request to the Gateway IP but includes the hostname in the HTTP header, triggering host-based routing.

---

### Comparison of Workarounds

| Method | Difficulty | Requires Internet | Works in Browser | Team Sharing | Best For |
|--------|-----------|-------------------|------------------|--------------|----------|
| **nip.io** | Easy | Yes | Yes | Yes | Demos, CI/CD |
| **/etc/hosts** | Medium | No | Yes | No | Development |
| **Port Forward** | Easy | No | Yes | No | Quick testing |
| **Host Header** | Easy | No | No | No | CLI testing only |

---

## Exercise 6: Path-Based Routing with HTTPRoute

Path-based routing directs traffic based on the URL path (e.g., `/app1`, `/app2`).

### Step 1: Review Path-Based HTTPRoute

Let's examine `httproute-paths.yaml`:

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: path-based-route
spec:
  parentRefs:
  - name: my-gateway

  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /app1
    backendRefs:
    - name: app1-blue-service
      port: 8080

  - matches:
    - path:
        type: PathPrefix
        value: /app2
    backendRefs:
    - name: app2-service
      port: 8080
```

**Understanding the manifest:**
- `parentRefs` - References the Gateway to use
- `rules` - Array of routing rules
- `matches` - Conditions for this rule to apply
- `path.type: PathPrefix` - Matches paths starting with the value
- `backendRefs` - Target service(s)

**Path Types:**
- `PathPrefix`: Matches prefix (e.g., `/app1` matches `/app1`, `/app1/test`)
- `Exact`: Exact match only (e.g., `/app1` matches only `/app1`)

### Step 2: Apply Path-Based Route

```bash
kubectl apply -f httproute-paths.yaml
```

Expected output:
```
httproute.gateway.networking.k8s.io/path-based-route created
```

### Step 3: Verify HTTPRoute

```bash
kubectl get httproute
```

Expected output:
```
NAME               HOSTNAMES   AGE
path-based-route   *           30s
```

Get detailed information:
```bash
kubectl describe httproute path-based-route
```

Look for:
- **Parent Refs**: Reference to my-gateway
- **Rules**: Path matching configuration
- **Status**: Should show "Accepted: True"

### Step 4: Test Path-Based Routing

**Using nip.io:**
```bash
GATEWAY_IP=$(kubectl get gateway my-gateway -o jsonpath='{.status.addresses[0].value}')

curl http://${GATEWAY_IP}.nip.io/app1
# Expected: "App1 Blue - Version 1.0"

curl http://${GATEWAY_IP}.nip.io/app2
# Expected: "App2 - Hello from Application 2"
```

**Using port-forward:**
```bash
# In one terminal:
kubectl port-forward -n nginx-gateway service/nginx-gateway 8080:80

# In another terminal:
curl http://localhost:8080/app1
curl http://localhost:8080/app2
```

**Using /etc/hosts:**
```bash
curl http://app1.example.local/app1
curl http://app1.example.local/app2
```

### Step 5: Test Path Matching Behavior

```bash
# These should work (PathPrefix matches subpaths)
curl http://localhost:8080/app1/anything
curl http://localhost:8080/app2/test/nested

# This won't match any rule
curl http://localhost:8080/app3
# Expected: 404 Not Found
```

---

## Exercise 7: Host-Based Routing with HTTPRoute

Host-based routing directs traffic based on the HTTP Host header (domain name).

### Step 1: Review Host-Based HTTPRoute

Let's examine `httproute-hosts.yaml`:

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: host-based-route
spec:
  parentRefs:
  - name: my-gateway

  hostnames:
  - "app1.example.local"

  rules:
  - backendRefs:
    - name: app1-blue-service
      port: 8080
```

**Understanding the manifest:**
- `hostnames` - Array of hostnames this route handles
- `rules` - All traffic to this hostname goes to the backend
- No `matches` needed - hostname is the match criteria

### Step 2: Set Up Domain Workaround

**Choose your preferred method from Exercise 5:**

**Option A - Using /etc/hosts:**
```bash
# Get Gateway IP
GATEWAY_IP=$(kubectl get gateway my-gateway -o jsonpath='{.status.addresses[0].value}' 2>/dev/null || minikube ip)

# Add to /etc/hosts
echo "$GATEWAY_IP app1.example.local app2.example.local" | sudo tee -a /etc/hosts
```

**Option B - Using nip.io:**
```bash
# Modify httproute-hosts.yaml to use nip.io
GATEWAY_IP=$(kubectl get gateway my-gateway -o jsonpath='{.status.addresses[0].value}')

cat <<EOF | kubectl apply -f -
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: host-based-route-nipio
spec:
  parentRefs:
  - name: my-gateway
  hostnames:
  - "app1.${GATEWAY_IP}.nip.io"
  rules:
  - backendRefs:
    - name: app1-blue-service
      port: 8080
EOF
```

### Step 3: Apply Host-Based Routes

```bash
kubectl apply -f httproute-hosts.yaml
```

Expected output:
```
httproute.gateway.networking.k8s.io/host-based-route created
httproute.gateway.networking.k8s.io/host-based-route-app2 created
httproute.gateway.networking.k8s.io/wildcard-host-route created
httproute.gateway.networking.k8s.io/combined-route created
```

### Step 4: Verify HTTPRoutes

```bash
kubectl get httproute
```

Expected output:
```
NAME                  HOSTNAMES                AGE
host-based-route      app1.example.local       30s
host-based-route-app2 app2.example.local       30s
wildcard-host-route   *.apps.local             30s
combined-route        api.example.local        30s
```

### Step 5: Test Host-Based Routing

**Using /etc/hosts:**
```bash
# Test app1
curl http://app1.example.local
# Expected: "App1 Blue - Version 1.0"

# Test app2
curl http://app2.example.local
# Expected: "App2 - Hello from Application 2"

# Test wildcard (*.apps.local)
curl http://anything.apps.local
# Expected: nginx welcome page
```

**Using nip.io:**
```bash
GATEWAY_IP=$(kubectl get gateway my-gateway -o jsonpath='{.status.addresses[0].value}')

curl http://app1.${GATEWAY_IP}.nip.io
curl http://app2.${GATEWAY_IP}.nip.io
```

**Using Host header (no DNS setup needed):**
```bash
GATEWAY_IP=$(kubectl get gateway my-gateway -o jsonpath='{.status.addresses[0].value}')

curl -H "Host: app1.example.local" http://$GATEWAY_IP
curl -H "Host: app2.example.local" http://$GATEWAY_IP
```

### Step 6: Test Combined Host + Path Routing

The `combined-route` uses both hostname AND path matching:

```bash
# Add to /etc/hosts if needed
echo "$GATEWAY_IP api.example.local" | sudo tee -a /etc/hosts

# Test different paths
curl http://api.example.local/v1
# Expected: "App1 Blue - Version 1.0"

curl http://api.example.local/v2
# Expected: "App2 - Hello from Application 2"
```

---

## Exercise 8: Traffic Splitting for Canary Deployments

One of Gateway API's most powerful features is native traffic splitting for canary and blue-green deployments.

### What is Traffic Splitting?

**Traffic Splitting** distributes requests across multiple backend services based on weights.

**Use Cases:**
- **Canary Deployment**: Route 10% to new version, 90% to stable
- **Blue-Green Deployment**: Route 50/50 for A/B testing
- **Progressive Rollout**: Gradually increase traffic to new version
- **Multi-Region**: Distribute traffic across regions

### Step 1: Review Traffic Splitting Manifest

Let's examine `traffic-splitting.yaml`:

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: weighted-route-canary
spec:
  parentRefs:
  - name: my-gateway

  hostnames:
  - "app1.example.local"

  rules:
  - backendRefs:
    - name: app1-blue-service
      port: 8080
      weight: 90
    - name: app1-green-service
      port: 8080
      weight: 10
```

**Understanding the manifest:**
- `weight: 90` - 90% of traffic to blue (stable version)
- `weight: 10` - 10% of traffic to green (canary version)
- Weights are relative (90:10 = 9:1 ratio)
- Total doesn't need to equal 100

### Step 2: Set Up Domain (if not already done)

```bash
# Using /etc/hosts
GATEWAY_IP=$(kubectl get gateway my-gateway -o jsonpath='{.status.addresses[0].value}' 2>/dev/null || minikube ip)
echo "$GATEWAY_IP canary.example.local bluegreen.example.local" | sudo tee -a /etc/hosts
```

### Step 3: Apply Traffic Splitting Routes

```bash
kubectl apply -f traffic-splitting.yaml
```

Expected output:
```
httproute.gateway.networking.k8s.io/weighted-route-canary created
httproute.gateway.networking.k8s.io/weighted-route-bluegreen created
httproute.gateway.networking.k8s.io/progressive-canary created
httproute.gateway.networking.k8s.io/header-based-canary created
```

### Step 4: Test Canary Deployment (90/10 Split)

```bash
# Run 20 requests and see the distribution
for i in {1..20}; do
  curl -s http://canary.example.local
done | sort | uniq -c
```

Expected output (approximately):
```
  18 App1 Blue - Version 1.0
   2 App1 Green - Version 2.0
```

You should see roughly 90% blue, 10% green.

### Step 5: Test Blue-Green Deployment (50/50 Split)

```bash
# View the blue-green route
kubectl get httproute weighted-route-bluegreen -o yaml

# Test with 20 requests
for i in {1..20}; do
  curl -s http://bluegreen.example.local
done | sort | uniq -c
```

Expected output (approximately):
```
  10 App1 Blue - Version 1.0
  10 App1 Green - Version 2.0
```

You should see roughly 50/50 distribution.

### Step 6: Progressive Canary Rollout

Simulate a gradual rollout by updating weights:

```bash
# Start: 95% blue, 5% green
kubectl apply -f - <<EOF
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: progressive-canary
spec:
  parentRefs:
  - name: my-gateway
  hostnames:
  - "canary.example.local"
  rules:
  - backendRefs:
    - name: app1-blue-service
      port: 8080
      weight: 95
    - name: app1-green-service
      port: 8080
      weight: 5
EOF

# Wait 10 minutes, monitor metrics...

# Update to 80/20
kubectl patch httproute progressive-canary --type=merge -p '
{
  "spec": {
    "rules": [{
      "backendRefs": [
        {"name": "app1-blue-service", "port": 8080, "weight": 80},
        {"name": "app1-green-service", "port": 8080, "weight": 20}
      ]
    }]
  }
}'

# Continue increasing green traffic...
# 50/50, then 20/80, then 0/100
```

### Step 7: Header-Based Canary (Advanced)

Route specific users to canary version based on HTTP headers:

```bash
# Test normal users (go to blue)
curl http://app1.example.local

# Test canary users (go to green)
curl -H "X-Canary: true" http://app1.example.local
```

This allows you to:
- Test with internal team first
- Enable canary for specific users
- A/B test with controlled groups

### Step 8: Monitor Traffic Distribution

```bash
# Watch HTTPRoute status
kubectl get httproute -w

# Check backend service endpoints
kubectl get endpoints app1-blue-service app1-green-service

# View Gateway events
kubectl describe gateway my-gateway
```

---

## Exercise 9: Compare Gateway API vs Traditional Ingress

Let's compare the same routing scenario implemented with both APIs.

### Scenario: Multi-App Routing

**Requirements:**
- Route `/app1` to app1-service
- Route `/app2` to app2-service
- Support different domains
- Enable traffic splitting

### Traditional Ingress Implementation

```yaml
# Requires annotations (vendor-specific)
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: multi-app-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    # Traffic splitting requires additional annotations (nginx-specific)
    nginx.ingress.kubernetes.io/canary: "true"
    nginx.ingress.kubernetes.io/canary-weight: "10"
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
              number: 8080
  - host: app2.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: app2-service
            port:
              number: 8080
```

**Limitations:**
- Annotations are vendor-specific
- Traffic splitting requires separate Ingress resources
- No native support for weights
- Limited to HTTP/HTTPS

### Gateway API Implementation

```yaml
# Standard, portable configuration
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: my-gateway
spec:
  gatewayClassName: nginx
  listeners:
  - name: http
    protocol: HTTP
    port: 80
---
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: multi-app-route
spec:
  parentRefs:
  - name: my-gateway
  hostnames:
  - "app1.example.com"
  rules:
  - backendRefs:
    - name: app1-blue-service
      port: 8080
      weight: 90
    - name: app1-green-service
      port: 8080
      weight: 10
---
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: app2-route
spec:
  parentRefs:
  - name: my-gateway
  hostnames:
  - "app2.example.com"
  rules:
  - backendRefs:
    - name: app2-service
      port: 8080
```

**Advantages:**
- No vendor-specific annotations
- Native traffic splitting with weights
- Clear separation of Gateway and Routes
- Role-oriented (platform vs app teams)
- Extensible for future protocols

### Side-by-Side Comparison

| Feature | Ingress | Gateway API |
|---------|---------|-------------|
| **Path routing** | ✅ Yes | ✅ Yes |
| **Host routing** | ✅ Yes | ✅ Yes |
| **Traffic splitting** | ⚠️ Annotations | ✅ Native |
| **Header routing** | ⚠️ Limited | ✅ Full support |
| **Method routing** | ❌ No | ✅ Yes (GET, POST, etc.) |
| **Query param routing** | ❌ No | ✅ Yes |
| **TLS termination** | ✅ Yes | ✅ Yes |
| **TCP routing** | ❌ No | ✅ Yes |
| **UDP routing** | ❌ No | ✅ Yes |
| **Vendor portability** | ⚠️ Annotations vary | ✅ Standard API |
| **Role separation** | ❌ Single resource | ✅ Gateway + Routes |
| **Cross-namespace** | ❌ No | ✅ Yes (with ReferenceGrant) |

### Migration Path

If you have existing Ingress resources:

1. **Keep Ingress running** (no downtime)
2. **Install Gateway API** alongside
3. **Create Gateway** resource
4. **Create HTTPRoutes** matching Ingress rules
5. **Test thoroughly** with both systems
6. **Switch traffic** gradually
7. **Decommission Ingress** when confident

---

## Repository YAML Files

The following pre-built YAML manifests are available in the repository for this lab (under `k8s/labs/networking/gateway-api/` unless noted):

| File | Description |
|------|-------------|
| `backend-services.yaml` | Deployments and ClusterIP Services for app1 blue/green, app2, and app3 (Exercise 3). |
| `gateway.yaml` | Sample `Gateway` bound to the nginx GatewayClass (Exercise 4). |
| `httproute-paths.yaml` | Path-based `HTTPRoute` rules (Exercise 6). |
| `httproute-hosts.yaml` | Host-based routes, wildcard, combined host+path, and nip.io placeholder route (Exercise 7). |
| `traffic-splitting.yaml` | Weighted canary, blue-green, progressive canary, header-based, and multi-backend routes (Exercise 8). |
| `tls-example.yaml` | Multi-document Gateway API TLS examples: HTTPS listener with cert `Secret` termination, HTTPRoute on the HTTPS listener, HTTP→HTTPS redirect, multi-cert/SNI Gateway, and TLS passthrough Gateway plus `TLSRoute` (v1alpha2). Requires a TLS `Secret` (e.g. `gateway-tls-cert`) and a compatible Gateway controller before apply. |

From the gateway-api directory (after installing CRDs and a Gateway controller):

```bash
cd k8s/labs/networking/gateway-api
kubectl apply -f backend-services.yaml
kubectl apply -f gateway.yaml
# Then apply httproute-paths.yaml, httproute-hosts.yaml, traffic-splitting.yaml as each exercise directs.
```

TLS bundle (after creating the TLS secret and backends as documented in the file comments):

```bash
kubectl apply -f k8s/labs/networking/gateway-api/tls-example.yaml
```

---

## Lab Cleanup

Remove all resources created in this lab:

```bash
# Delete HTTPRoutes
kubectl delete httproute --all

# Delete Gateway
kubectl delete gateway my-gateway

# Delete backend applications
kubectl delete deployment app1-blue app1-green app2 app3-nginx
kubectl delete service app1-blue-service app1-green-service app2-service app3-service

# Delete Gateway Controller (optional)
kubectl delete namespace nginx-gateway

# Delete Gateway API CRDs (optional - only if you want complete removal)
kubectl delete -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.0.0/standard-install.yaml

# Clean up /etc/hosts
# Remove these lines (manual step):
# - app1.example.local
# - app2.example.local
# - app3.example.local
# - canary.example.local
# - bluegreen.example.local

# Verify cleanup
kubectl get gateway,httproute,deployment,service
```

---

## Troubleshooting Guide

### Issue 1: Gateway Not Getting IP Address

**Symptoms**: Gateway ADDRESS column is empty

**Diagnosis:**
```bash
# Check Gateway status
kubectl describe gateway my-gateway

# Check Gateway controller
kubectl get pods -n nginx-gateway

# Check controller logs
kubectl logs -n nginx-gateway -l app=nginx-gateway
```

**Solutions:**
- Ensure Gateway controller is running
- For Minikube, run `minikube tunnel` in separate terminal
- Check GatewayClass is correct: `kubectl get gatewayclass`
- Verify listener configuration in Gateway spec

### Issue 2: HTTPRoute Not Working (404 Not Found)

**Symptoms**: curl returns 404 or "no route found"

**Diagnosis:**
```bash
# Check HTTPRoute status
kubectl describe httproute <route-name>

# Look for "Accepted: False" in status
# Check backend services exist
kubectl get service <service-name>

# Check service has endpoints
kubectl get endpoints <service-name>
```

**Common Causes:**
- Service name mismatch
- Wrong port number
- Gateway reference incorrect (`parentRefs`)
- Hostname doesn't match (check Host header)
- Path doesn't match

**Solutions:**
```bash
# Verify backend service
kubectl get service app1-blue-service

# Check endpoints (should show Pod IPs)
kubectl get endpoints app1-blue-service

# Test with verbose curl
curl -v http://app1.example.local

# Check if Host header is being sent
curl -H "Host: app1.example.local" -v http://<gateway-ip>
```

### Issue 3: Domain Name Not Resolving

**Symptoms**: "Could not resolve host" or "Name or service not known"

**Diagnosis:**
```bash
# Test DNS resolution
nslookup app1.example.local

# Test with Host header instead
curl -H "Host: app1.example.local" http://<gateway-ip>
```

**Solutions:**
- **Use nip.io**: Replace `app1.example.local` with `app1.<gateway-ip>.nip.io`
- **Use /etc/hosts**: Add `<gateway-ip> app1.example.local` to `/etc/hosts`
- **Use port-forward**: `kubectl port-forward -n nginx-gateway service/nginx-gateway 8080:80`
- **Use Host header**: `curl -H "Host: app1.example.local" http://<ip>`

### Issue 4: Traffic Splitting Not Working

**Symptoms**: All traffic goes to one backend

**Diagnosis:**
```bash
# Check HTTPRoute weights
kubectl get httproute <route-name> -o yaml

# Verify both services have endpoints
kubectl get endpoints app1-blue-service app1-green-service

# Test multiple times
for i in {1..20}; do curl -s http://app1.example.local; done | sort | uniq -c
```

**Solutions:**
- Verify both services are running
- Check weights are specified correctly
- Ensure both backendRefs use same port
- Wait a few seconds for configuration to propagate

### Issue 5: Gateway Controller Not Installing

**Symptoms**: Pods not starting in nginx-gateway namespace

**Diagnosis:**
```bash
# Check pods
kubectl get pods -n nginx-gateway

# Check events
kubectl get events -n nginx-gateway --sort-by='.lastTimestamp'

# Check pod logs
kubectl logs -n nginx-gateway <pod-name>
```

**Solutions:**
- Ensure Kubernetes version is 1.26+
- Check CRDs are installed: `kubectl get crd | grep gateway`
- Verify sufficient cluster resources
- Try alternative controller (Envoy Gateway)

### Issue 6: nip.io Not Working

**Symptoms**: nip.io domains not resolving

**Diagnosis:**
```bash
# Test nip.io DNS
nslookup 192.168.49.2.nip.io

# Check internet connectivity
ping 8.8.8.8
```

**Solutions:**
- Check firewall allows DNS queries
- Corporate network may block nip.io
- Use alternative: /etc/hosts or port-forward
- Try alternative service: sslip.io (192.168.49.2.sslip.io)

---

## Key Takeaways

### Gateway API Fundamentals

1. **Gateway API** is the successor to Ingress, providing more features and better design
2. **GatewayClass** defines the controller (nginx, envoy, etc.)
3. **Gateway** defines infrastructure (listeners, ports, protocols)
4. **HTTPRoute** defines application routing rules
5. **Role separation** enables platform and app teams to manage independently

### Traffic Management

1. **Path-based routing** routes by URL path (`/app1`, `/app2`)
2. **Host-based routing** routes by domain name (`app1.com`, `app2.com`)
3. **Traffic splitting** uses weights for canary and blue-green deployments
4. **Header-based routing** enables A/B testing and gradual rollouts
5. **Combined routing** can match multiple criteria (host + path + headers)

### Domain Name Workarounds

1. **nip.io** provides wildcard DNS without configuration (requires internet)
2. **/etc/hosts** provides reliable local DNS (requires admin access)
3. **Port forwarding** exposes Gateway on localhost (simplest for testing)
4. **Host header** allows testing without DNS (curl only)
5. Choose the method that fits your environment and team

### Gateway API vs Ingress

1. Gateway API is **more expressive** than Ingress
2. Gateway API is **vendor-portable** (no annotations)
3. Gateway API has **native traffic splitting** (no workarounds)
4. Gateway API supports **more protocols** (TCP, UDP, gRPC)
5. Gateway API is **role-oriented** (platform vs app resources)

---

## Best Practices

### Gateway Configuration

1. **Use one Gateway per environment**
```yaml
# Production Gateway
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: production-gateway
  namespace: production
spec:
  gatewayClassName: nginx
```

2. **Configure resource limits on Gateway controller**
```yaml
resources:
  requests:
    cpu: 200m
    memory: 256Mi
  limits:
    cpu: 1000m
    memory: 512Mi
```

3. **Use TLS for production**
```yaml
listeners:
- name: https
  protocol: HTTPS
  port: 443
  tls:
    mode: Terminate
    certificateRefs:
    - name: tls-cert
```

### HTTPRoute Best Practices

1. **Use specific hostnames over wildcards**
```yaml
# Good
hostnames:
- "app1.example.com"

# Avoid in production
hostnames:
- "*.example.com"
```

2. **Order rules from most to least specific**
```yaml
rules:
# Exact paths first
- matches:
  - path:
      type: Exact
      value: /api/health

# Prefix paths last
- matches:
  - path:
      type: PathPrefix
      value: /api
```

3. **Use meaningful names**
```yaml
metadata:
  name: api-canary-route-v2  # Good
  # Not: route-1
```

4. **Document traffic weights**
```yaml
# Canary: 10% to v2, 90% to v1
backendRefs:
- name: api-v1
  weight: 90
- name: api-v2
  weight: 10
```

### Traffic Splitting Best Practices

1. **Start with small canary percentages**
```yaml
# Start: 95/5
# Then: 90/10
# Then: 75/25
# Then: 50/50
# Finally: 0/100
```

2. **Monitor before increasing traffic**
```bash
# Watch metrics before adjusting weights
kubectl top pods
kubectl logs -f <pod-name>
```

3. **Use header-based routing for internal testing**
```yaml
# Test with team first
- matches:
  - headers:
    - name: X-Beta-User
      value: "true"
  backendRefs:
  - name: app-v2
```

### Domain Name Workarounds for Teams

1. **For development**: Use /etc/hosts (reliable, offline)
2. **For CI/CD**: Use nip.io (no configuration needed)
3. **For demos**: Use nip.io (works from any machine)
4. **For local testing**: Use port-forward (simplest)

---

## Additional Commands Reference

```bash
# Gateway commands
kubectl get gateway
kubectl describe gateway <name>
kubectl get gateway <name> -o yaml

# HTTPRoute commands
kubectl get httproute
kubectl describe httproute <name>
kubectl get httproute <name> -o yaml

# GatewayClass commands
kubectl get gatewayclass
kubectl describe gatewayclass nginx

# Check Gateway controller
kubectl get pods -n nginx-gateway
kubectl logs -n nginx-gateway -l app=nginx-gateway -f

# Test routing
curl -v http://app1.example.local
curl -H "Host: app1.example.local" http://<gateway-ip>

# Test traffic splitting (20 requests)
for i in {1..20}; do curl -s http://canary.example.local; done | sort | uniq -c

# Port forward Gateway
kubectl port-forward -n nginx-gateway service/nginx-gateway 8080:80

# Watch resources
kubectl get gateway,httproute -w

# Debug with test pod
kubectl run netshoot --rm -it --image=nicolaka/netshoot -- bash
# Inside: curl, dig, nslookup, traceroute, etc.
```

---

## Next Steps

1. **Practice**: Implement canary deployment for a real application
2. **Explore**: Try other Gateway controllers (Envoy Gateway, Kong)
3. **Advanced**: Implement cross-namespace routing with ReferenceGrant
4. **Security**: Configure mutual TLS (mTLS) with Gateway API
5. **Observability**: Integrate with Prometheus for traffic metrics
6. **Automation**: Use GitOps (ArgoCD/Flux) to manage Gateway resources

---

## Additional Reading

- [Gateway API Official Documentation](https://gateway-api.sigs.k8s.io/)
- [NGINX Gateway Fabric Documentation](https://docs.nginx.com/nginx-gateway-fabric/)
- [Envoy Gateway Documentation](https://gateway.envoyproxy.io/)
- [Gateway API Migration Guide](https://gateway-api.sigs.k8s.io/guides/migrating-from-ingress/)
- [Traffic Splitting Guide](https://gateway-api.sigs.k8s.io/guides/traffic-splitting/)
- [nip.io Service](https://nip.io/)
- [Gateway API vs Ingress Comparison](https://gateway-api.sigs.k8s.io/concepts/why/)

---

**Lab Created**: March 2026
**Compatible with**: Kubernetes 1.26+ (Gateway API GA)
**Tested on**: Minikube 1.32+, Kind 0.20+, AWS EKS 1.28+, GCP GKE 1.28+

---

**Need Help?**

If you encounter issues:
1. Check the Troubleshooting Guide above
2. Verify all prerequisites are met
3. Review the domain name workarounds (Exercise 5)
4. Test with port-forward first (simplest)
5. Check Gateway controller logs: `kubectl logs -n nginx-gateway -l app=nginx-gateway`
