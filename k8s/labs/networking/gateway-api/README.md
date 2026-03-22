# Gateway API Lab Files

This directory contains YAML manifests for Lab 41: Gateway API - Next Generation Ingress.

## Files Overview

### 1. backend-services.yaml
Deploys sample applications for testing Gateway API routing:
- **app1-blue** - Stable version (Version 1.0)
- **app1-green** - New version (Version 2.0) for canary testing
- **app2** - Second application for multi-app routing
- **app3-nginx** - Nginx application for comparison

All applications include Deployments and Services (ClusterIP).

### 2. gateway.yaml
Gateway resources that define traffic entry points:
- **my-gateway** - Basic HTTP Gateway
- **hostname-gateway** - Gateway with hostname restrictions
- **multi-port-gateway** - Gateway with multiple listeners

### 3. httproute-paths.yaml
HTTPRoute examples for path-based routing:
- **path-based-route** - Routes by URL path (/app1, /app2)
- **exact-path-route** - Exact path matching
- **rewrite-path-route** - Path rewriting example

### 4. httproute-hosts.yaml
HTTPRoute examples for host-based routing:
- **host-based-route** - Routes by hostname (app1.example.local)
- **host-based-route-app2** - Second hostname route
- **wildcard-host-route** - Wildcard hostname matching (*.apps.local)
- **combined-route** - Host + path matching
- **nipio-route** - Template for nip.io usage

### 5. traffic-splitting.yaml
HTTPRoute examples for traffic splitting:
- **weighted-route-canary** - 90/10 canary deployment
- **weighted-route-bluegreen** - 50/50 blue-green deployment
- **progressive-canary** - Progressive rollout example
- **header-based-canary** - Header-based routing for testing
- **multi-backend-route** - Multi-backend distribution

### 6. tls-example.yaml
HTTPS/TLS configuration examples:
- **https-gateway** - Gateway with HTTPS listener
- **https-route** - HTTPRoute for HTTPS traffic
- **http-to-https-redirect** - Automatic HTTPS redirect
- **multi-cert-gateway** - Multiple TLS certificates (SNI)
- **tls-passthrough-gateway** - TLS passthrough example

## Quick Start

### 1. Install Gateway API CRDs
```bash
kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.0.0/standard-install.yaml
```

### 2. Install Gateway Controller (NGINX)
```bash
kubectl apply -f https://github.com/nginxinc/nginx-gateway-fabric/releases/download/v1.1.0/crds.yaml
kubectl apply -f https://github.com/nginxinc/nginx-gateway-fabric/releases/download/v1.1.0/nginx-gateway.yaml
```

### 3. Deploy Backend Applications
```bash
kubectl apply -f backend-services.yaml
```

### 4. Create Gateway
```bash
kubectl apply -f gateway.yaml
```

### 5. Create Routes (Choose One)
```bash
# Path-based routing
kubectl apply -f httproute-paths.yaml

# Or host-based routing
kubectl apply -f httproute-hosts.yaml

# Or traffic splitting
kubectl apply -f traffic-splitting.yaml
```

## Testing Without a Domain Name

### Option 1: Using nip.io
```bash
# Get Gateway IP
GATEWAY_IP=$(kubectl get gateway my-gateway -o jsonpath='{.status.addresses[0].value}')

# Test with nip.io
curl http://app1.${GATEWAY_IP}.nip.io
```

### Option 2: Using /etc/hosts
```bash
# Add to /etc/hosts (Linux/Mac)
GATEWAY_IP=$(kubectl get gateway my-gateway -o jsonpath='{.status.addresses[0].value}')
echo "$GATEWAY_IP app1.example.local app2.example.local" | sudo tee -a /etc/hosts

# Test
curl http://app1.example.local
```

### Option 3: Using Port Forward
```bash
# Forward Gateway to localhost
kubectl port-forward -n nginx-gateway service/nginx-gateway 8080:80

# Test (in another terminal)
curl http://localhost:8080/app1
```

### Option 4: Using Host Header
```bash
# Get Gateway IP
GATEWAY_IP=$(kubectl get gateway my-gateway -o jsonpath='{.status.addresses[0].value}')

# Test with Host header
curl -H "Host: app1.example.local" http://$GATEWAY_IP
```

## Common Commands

### View Resources
```bash
# View Gateways
kubectl get gateway

# View HTTPRoutes
kubectl get httproute

# View GatewayClasses
kubectl get gatewayclass

# Detailed information
kubectl describe gateway my-gateway
kubectl describe httproute path-based-route
```

### Test Traffic Splitting
```bash
# Run 20 requests to see distribution
for i in {1..20}; do
  curl -s http://canary.example.local
done | sort | uniq -c
```

### Debug
```bash
# Check Gateway controller logs
kubectl logs -n nginx-gateway -l app=nginx-gateway -f

# Check Gateway status
kubectl get gateway my-gateway -o yaml

# Check HTTPRoute status
kubectl get httproute path-based-route -o yaml
```

## Cleanup

```bash
# Delete all resources
kubectl delete httproute --all
kubectl delete gateway --all
kubectl delete -f backend-services.yaml

# Optional: Remove Gateway controller
kubectl delete namespace nginx-gateway

# Optional: Remove CRDs
kubectl delete -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.0.0/standard-install.yaml
```

## File Structure

```
gateway-api/
├── README.md                    # This file
├── backend-services.yaml        # Sample applications
├── gateway.yaml                 # Gateway resources
├── httproute-paths.yaml        # Path-based routing
├── httproute-hosts.yaml        # Host-based routing
├── traffic-splitting.yaml      # Canary/Blue-Green deployments
└── tls-example.yaml            # HTTPS/TLS examples
```

## Requirements

- Kubernetes 1.26+ (for Gateway API GA)
- kubectl CLI configured
- Gateway API CRDs installed
- Gateway Controller (NGINX/Envoy) installed

## Learn More

See the full lab manual: `k8s/docs/labmanuals/lab44-net-gateway-api.md`

## Support

For issues or questions:
1. Check the Troubleshooting section in the lab manual
2. Verify Gateway controller is running: `kubectl get pods -n nginx-gateway`
3. Check Gateway status: `kubectl describe gateway my-gateway`
4. Review HTTPRoute status: `kubectl describe httproute <name>`

## License

These lab files are part of the k8sforbeginners training materials.
