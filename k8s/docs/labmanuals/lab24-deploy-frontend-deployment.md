# Lab 37: Frontend Application Deployment in Kubernetes

## Overview
In this lab, you will learn best practices for deploying frontend applications in Kubernetes. You'll explore real-world deployment patterns, configuration management, scaling strategies, zero-downtime updates, and production-ready practices for serving web applications. This lab focuses on practical patterns used in modern cloud-native architectures.

## Prerequisites
- A running Kubernetes cluster (Minikube, Kind, or any K8s cluster)
- `kubectl` CLI tool installed and configured
- Basic understanding of Deployments (Lab 01)
- Familiarity with Services (Lab 02)
- Understanding of ConfigMaps and Secrets (Lab 04)

## Learning Objectives
By the end of this lab, you will be able to:
- Deploy production-ready frontend applications in Kubernetes
- Implement proper configuration management for frontend apps
- Configure resource limits and requests appropriately
- Implement zero-downtime deployment strategies
- Use health probes for frontend applications
- Configure horizontal pod autoscaling for web apps
- Implement best practices for serving static content
- Handle environment-specific configuration
- Set up proper ingress and routing for frontend apps

---

## Frontend Applications in Kubernetes

**Frontend applications** are client-facing web applications that users interact with directly. In Kubernetes, they require special considerations for availability, performance, and deployment practices.

### Common Frontend Architectures

```
┌─────────────────────────────────────────────────────────────┐
│                    Internet / Users                          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   Ingress Controller                         │
│              (nginx, traefik, ALB, etc.)                     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Kubernetes Service                        │
│                   (LoadBalancer/ClusterIP)                   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                Frontend App Deployment                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Pod 1   │  │  Pod 2   │  │  Pod 3   │  │  Pod N   │   │
│  │  nginx   │  │  nginx   │  │  nginx   │  │  nginx   │   │
│  │  React   │  │  React   │  │  React   │  │  React   │   │
│  │  App     │  │  App     │  │  App     │  │  App     │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Key Considerations for Frontend Apps

| Aspect | Consideration | Solution |
|--------|---------------|----------|
| **Availability** | Must be always accessible | Multiple replicas + HPA |
| **Performance** | Fast response times | CDN, caching, static assets |
| **Configuration** | Environment-specific settings | ConfigMaps, runtime config |
| **Updates** | Zero-downtime deployments | Rolling updates, health probes |
| **Scalability** | Handle traffic spikes | Horizontal Pod Autoscaling |
| **Security** | Secure communication | TLS, HTTPS, security headers |
| **Observability** | Monitor user experience | Logging, metrics, tracing |

---

## Exercise 1: Basic Frontend Deployment

### Step 1: Review the Frontend App Manifest

Navigate to the workloads directory:
```bash
cd k8s/labs/workloads
```

Examine `frontend-app.yaml`:

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

**Understanding the Manifest:**
- **replicas: 3**: Three instances for high availability
- **selector.matchLabels**: Links deployment to pods
- **template**: Pod template for creating replicas
- **image: nginx:1.16.1**: Nginx web server (common for serving frontend apps)
- **containerPort: 80**: Standard HTTP port

### Step 2: Deploy the Basic Frontend App

```bash
# Deploy the frontend application
kubectl apply -f frontend-app.yaml

# Verify deployment
kubectl get deployment frontend-app

# Check replica status
kubectl get pods -l run=frontend-app
```

**Expected Output:**
```
NAME                            READY   STATUS    RESTARTS   AGE
frontend-app-7c8d5fb9b6-4x7km   1/1     Running   0          10s
frontend-app-7c8d5fb9b6-8n2lp   1/1     Running   0          10s
frontend-app-7c8d5fb9b6-m9wqt   1/1     Running   0          10s
```

### Step 3: Expose the Frontend App

```bash
# Create a LoadBalancer service
kubectl expose deployment frontend-app --type=LoadBalancer --port=80 --target-port=80 --name=frontend-service

# Get service details
kubectl get service frontend-service

# For Minikube, get the URL
minikube service frontend-service --url
```

### Step 4: Test the Application

```bash
# Get the service URL (for Minikube)
export FRONTEND_URL=$(minikube service frontend-service --url)

# Test the application
curl $FRONTEND_URL

# Or open in browser
minikube service frontend-service
```

**Expected Output:** Nginx welcome page HTML

---

## Exercise 2: Production-Ready Frontend Deployment

Let's enhance our deployment with production best practices.

### Step 1: Create Enhanced Deployment with Resources and Probes

```bash
# Create production-ready deployment
cat <<EOF > frontend-production.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend-app-prod
  labels:
    app: frontend
    tier: web
    environment: production
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: frontend
      tier: web
  template:
    metadata:
      labels:
        app: frontend
        tier: web
        version: v1
    spec:
      containers:
      - name: nginx
        image: nginx:1.21-alpine
        ports:
        - name: http
          containerPort: 80
          protocol: TCP

        # Resource management
        resources:
          requests:
            memory: "64Mi"
            cpu: "100m"
          limits:
            memory: "128Mi"
            cpu: "200m"

        # Health probes
        livenessProbe:
          httpGet:
            path: /
            port: 80
            scheme: HTTP
          initialDelaySeconds: 10
          periodSeconds: 10
          timeoutSeconds: 5
          successThreshold: 1
          failureThreshold: 3

        readinessProbe:
          httpGet:
            path: /
            port: 80
            scheme: HTTP
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          successThreshold: 1
          failureThreshold: 2

        # Security context
        securityContext:
          runAsNonRoot: true
          runAsUser: 101
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL

        # Volume mounts for writable directories
        volumeMounts:
        - name: cache
          mountPath: /var/cache/nginx
        - name: run
          mountPath: /var/run
        - name: tmp
          mountPath: /tmp

      volumes:
      - name: cache
        emptyDir: {}
      - name: run
        emptyDir: {}
      - name: tmp
        emptyDir: {}

      # Pod-level security and scheduling
      securityContext:
        fsGroup: 101

      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - frontend
              topologyKey: kubernetes.io/hostname
EOF

# Apply the production deployment
kubectl apply -f frontend-production.yaml
```

### Step 2: Understand the Production Enhancements

```bash
# Check deployment details
kubectl describe deployment frontend-app-prod

# Verify resource requests and limits
kubectl get pods -l app=frontend -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[0].resources}{"\n"}{end}'

# Check pod distribution across nodes (anti-affinity)
kubectl get pods -l app=frontend -o wide
```

**Key Enhancements Explained:**

1. **Rolling Update Strategy**
   - `maxSurge: 1`: One extra pod during updates
   - `maxUnavailable: 0`: Zero downtime guarantee

2. **Resource Management**
   - Requests: Guaranteed resources
   - Limits: Maximum resources
   - Prevents resource starvation

3. **Health Probes**
   - Liveness: Restart unhealthy pods
   - Readiness: Remove from service when not ready

4. **Security Context**
   - Non-root user
   - Read-only root filesystem
   - Dropped capabilities

5. **Pod Anti-Affinity**
   - Spreads pods across nodes
   - Improves availability

---

## Exercise 3: Configuration Management for Frontend Apps

Frontend apps often need environment-specific configuration (API URLs, feature flags, etc.).

### Step 1: Create ConfigMap for Frontend Configuration

```bash
# Create ConfigMap with frontend configuration
cat <<EOF > frontend-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: frontend-config
data:
  # API endpoints
  API_URL: "https://api.example.com"
  API_VERSION: "v1"

  # Feature flags
  ENABLE_ANALYTICS: "true"
  ENABLE_DARK_MODE: "true"

  # App settings
  APP_NAME: "My Frontend App"
  APP_VERSION: "1.0.0"

  # Nginx configuration
  nginx.conf: |
    server {
      listen 80;
      server_name _;

      root /usr/share/nginx/html;
      index index.html;

      # SPA routing - redirect all to index.html
      location / {
        try_files \$uri \$uri/ /index.html;
      }

      # API proxy (optional)
      location /api/ {
        proxy_pass https://api.example.com/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
      }

      # Cache static assets
      location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
      }

      # Security headers
      add_header X-Frame-Options "SAMEORIGIN" always;
      add_header X-Content-Type-Options "nosniff" always;
      add_header X-XSS-Protection "1; mode=block" always;
      add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    }
EOF

# Apply the ConfigMap
kubectl apply -f frontend-config.yaml
```

### Step 2: Create Deployment Using ConfigMap

```bash
cat <<EOF > frontend-with-config.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend-app-configured
spec:
  replicas: 3
  selector:
    matchLabels:
      app: frontend-configured
  template:
    metadata:
      labels:
        app: frontend-configured
    spec:
      containers:
      - name: nginx
        image: nginx:1.21-alpine
        ports:
        - containerPort: 80

        # Environment variables from ConfigMap
        env:
        - name: API_URL
          valueFrom:
            configMapKeyRef:
              name: frontend-config
              key: API_URL
        - name: API_VERSION
          valueFrom:
            configMapKeyRef:
              name: frontend-config
              key: API_VERSION
        - name: APP_NAME
          valueFrom:
            configMapKeyRef:
              name: frontend-config
              key: APP_NAME

        # Mount ConfigMap as files
        volumeMounts:
        - name: config-volume
          mountPath: /etc/nginx/conf.d
          subPath: nginx.conf
        - name: cache
          mountPath: /var/cache/nginx
        - name: run
          mountPath: /var/run

      volumes:
      - name: config-volume
        configMap:
          name: frontend-config
          items:
          - key: nginx.conf
            path: default.conf
      - name: cache
        emptyDir: {}
      - name: run
        emptyDir: {}
EOF

# Deploy
kubectl apply -f frontend-with-config.yaml

# Verify environment variables
kubectl exec -it $(kubectl get pod -l app=frontend-configured -o jsonpath='{.items[0].metadata.name}') -- env | grep -E "(API_URL|APP_NAME)"
```

---

## Exercise 4: Runtime Configuration for SPAs

Modern Single Page Applications (React, Vue, Angular) need runtime configuration that's injected when the app loads.

### Step 1: Create Runtime Config ConfigMap

```bash
cat <<EOF > spa-runtime-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: spa-runtime-config
data:
  config.js: |
    window.APP_CONFIG = {
      apiUrl: 'https://api.example.com/v1',
      environment: 'production',
      features: {
        analytics: true,
        darkMode: true,
        newDashboard: false
      },
      version: '1.0.0'
    };
EOF

kubectl apply -f spa-runtime-config.yaml
```

### Step 2: Create Deployment with Runtime Config Injection

```bash
cat <<EOF > spa-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: spa-frontend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: spa-frontend
  template:
    metadata:
      labels:
        app: spa-frontend
    spec:
      containers:
      - name: nginx
        image: nginx:1.21-alpine
        ports:
        - containerPort: 80

        volumeMounts:
        # Mount runtime config as a JS file
        - name: runtime-config
          mountPath: /usr/share/nginx/html/config.js
          subPath: config.js
        - name: nginx-config
          mountPath: /etc/nginx/conf.d/default.conf
          subPath: nginx.conf
        - name: cache
          mountPath: /var/cache/nginx
        - name: run
          mountPath: /var/run

      volumes:
      - name: runtime-config
        configMap:
          name: spa-runtime-config
      - name: nginx-config
        configMap:
          name: frontend-config
          items:
          - key: nginx.conf
            path: nginx.conf
      - name: cache
        emptyDir: {}
      - name: run
        emptyDir: {}
EOF

kubectl apply -f spa-deployment.yaml
```

**HTML Usage Example:**
```html
<!DOCTYPE html>
<html>
<head>
  <title>My SPA</title>
  <!-- Load runtime config first -->
  <script src="/config.js"></script>
</head>
<body>
  <div id="app"></div>
  <script>
    // Access config in your app
    console.log('API URL:', window.APP_CONFIG.apiUrl);
    console.log('Environment:', window.APP_CONFIG.environment);
  </script>
</body>
</html>
```

---

## Exercise 5: Horizontal Pod Autoscaling for Frontend Apps

Scale your frontend based on CPU or memory usage.

### Step 1: Create HPA for Frontend App

```bash
# Create HPA based on CPU utilization
kubectl autoscale deployment frontend-app-prod \
  --cpu-percent=70 \
  --min=3 \
  --max=10 \
  --name=frontend-hpa

# View HPA status
kubectl get hpa frontend-hpa

# Describe HPA
kubectl describe hpa frontend-hpa
```

### Step 2: Create Advanced HPA with Multiple Metrics

```bash
cat <<EOF > frontend-hpa-advanced.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: frontend-hpa-advanced
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: frontend-app-prod
  minReplicas: 3
  maxReplicas: 15
  metrics:
  # CPU-based scaling
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  # Memory-based scaling
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 100
        periodSeconds: 30
      - type: Pods
        value: 2
        periodSeconds: 30
      selectPolicy: Max
EOF

kubectl apply -f frontend-hpa-advanced.yaml
```

### Step 3: Simulate Load and Watch Scaling

```bash
# Generate load (requires metrics-server)
kubectl run -it --rm load-generator --image=busybox --restart=Never -- /bin/sh -c "while true; do wget -q -O- http://frontend-service; done"

# Watch HPA in another terminal
kubectl get hpa frontend-hpa-advanced --watch

# Watch pod scaling
kubectl get pods -l app=frontend --watch
```

---

## Exercise 6: Zero-Downtime Deployment Strategies

### Strategy 1: Rolling Update (Default)

```bash
# Update the image
kubectl set image deployment/frontend-app-prod nginx=nginx:1.22-alpine

# Watch the rollout
kubectl rollout status deployment/frontend-app-prod

# Check rollout history
kubectl rollout history deployment/frontend-app-prod
```

### Strategy 2: Blue-Green Deployment

```bash
# Current deployment (Blue)
kubectl get deployment frontend-app-prod

# Create new deployment (Green) with new version
cat <<EOF > frontend-green.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend-app-green
spec:
  replicas: 3
  selector:
    matchLabels:
      app: frontend
      version: green
  template:
    metadata:
      labels:
        app: frontend
        version: green
    spec:
      containers:
      - name: nginx
        image: nginx:1.22-alpine
        ports:
        - containerPort: 80
EOF

kubectl apply -f frontend-green.yaml

# Test green deployment
kubectl run test-pod --rm -it --image=busybox --restart=Never -- wget -q -O- http://frontend-app-green

# Switch traffic to green
kubectl patch service frontend-service -p '{"spec":{"selector":{"version":"green"}}}'

# Verify traffic switch
kubectl describe service frontend-service | grep Selector

# Rollback if needed
kubectl patch service frontend-service -p '{"spec":{"selector":{"version":"blue"}}}'

# Delete old blue deployment after verification
kubectl delete deployment frontend-app-prod
```

### Strategy 3: Canary Deployment

```bash
# Scale down main deployment to 8 replicas
kubectl scale deployment frontend-app-prod --replicas=8

# Deploy canary with 2 replicas (20% traffic)
cat <<EOF > frontend-canary.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend-app-canary
spec:
  replicas: 2
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
        version: canary
    spec:
      containers:
      - name: nginx
        image: nginx:1.22-alpine
        ports:
        - containerPort: 80
EOF

kubectl apply -f frontend-canary.yaml

# Monitor canary performance
kubectl top pods -l version=canary

# If successful, scale up canary and scale down main
kubectl scale deployment frontend-app-canary --replicas=10
kubectl scale deployment frontend-app-prod --replicas=0

# Delete old deployment
kubectl delete deployment frontend-app-prod
```

---

## Exercise 7: Ingress Configuration for Frontend Apps

### Step 1: Create Ingress for Frontend App

```bash
cat <<EOF > frontend-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: frontend-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "false"
    # Enable gzip compression
    nginx.ingress.kubernetes.io/enable-compression: "true"
    # Rate limiting
    nginx.ingress.kubernetes.io/limit-rps: "100"
spec:
  ingressClassName: nginx
  rules:
  - host: frontend.example.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend-service
            port:
              number: 80
EOF

kubectl apply -f frontend-ingress.yaml
```

### Step 2: Configure TLS/HTTPS

```bash
# Create self-signed certificate (for testing)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout tls.key -out tls.crt \
  -subj "/CN=frontend.example.local/O=example"

# Create TLS secret
kubectl create secret tls frontend-tls \
  --cert=tls.crt \
  --key=tls.key

# Update Ingress with TLS
cat <<EOF > frontend-ingress-tls.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: frontend-ingress
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - frontend.example.local
    secretName: frontend-tls
  rules:
  - host: frontend.example.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend-service
            port:
              number: 80
EOF

kubectl apply -f frontend-ingress-tls.yaml
```

---

## Best Practices Summary

### 1. High Availability
```yaml
# Multiple replicas
replicas: 3

# Pod anti-affinity
affinity:
  podAntiAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
    - weight: 100
      podAffinityTerm:
        topologyKey: kubernetes.io/hostname
```

### 2. Resource Management
```yaml
resources:
  requests:
    memory: "64Mi"
    cpu: "100m"
  limits:
    memory: "128Mi"
    cpu: "200m"
```

### 3. Health Checks
```yaml
livenessProbe:
  httpGet:
    path: /
    port: 80
readinessProbe:
  httpGet:
    path: /
    port: 80
```

### 4. Zero-Downtime Updates
```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1
    maxUnavailable: 0
```

### 5. Configuration Management
- Use ConfigMaps for environment-specific settings
- Inject runtime config for SPAs
- Never hardcode API URLs or feature flags

### 6. Security
- Run as non-root user
- Use read-only root filesystem
- Enable TLS/HTTPS
- Add security headers

### 7. Observability
- Structured logging
- Prometheus metrics
- Distributed tracing
- User experience monitoring

---

## Cleanup

```bash
# Delete deployments
kubectl delete deployment frontend-app
kubectl delete deployment frontend-app-prod
kubectl delete deployment frontend-app-configured
kubectl delete deployment spa-frontend
kubectl delete deployment frontend-app-green
kubectl delete deployment frontend-app-canary

# Delete services
kubectl delete service frontend-service

# Delete ConfigMaps
kubectl delete configmap frontend-config
kubectl delete configmap spa-runtime-config

# Delete HPA
kubectl delete hpa frontend-hpa
kubectl delete hpa frontend-hpa-advanced

# Delete Ingress
kubectl delete ingress frontend-ingress

# Delete secrets
kubectl delete secret frontend-tls

# Clean up test files
rm -f tls.key tls.crt
```

---

## Additional Resources

### Official Documentation
- [Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
- [Horizontal Pod Autoscaling](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)
- [Ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/)
- [ConfigMaps](https://kubernetes.io/docs/concepts/configuration/configmap/)

### Related Labs
- Lab 01: Basic Deployments
- Lab 02: Services and Networking
- Lab 04: ConfigMaps and Secrets
- Lab 11: Horizontal Pod Autoscaling
- Lab 12: Health Probes

---

## Challenge Exercises

### Challenge 1: Multi-Environment Deployment
Create separate deployments for dev, staging, and production environments with different configurations.

### Challenge 2: CDN Integration
Configure nginx to serve static assets with optimal caching headers and integrate with a CDN.

### Challenge 3: A/B Testing Setup
Implement an A/B testing setup where 10% of traffic goes to a new feature version.

### Challenge 4: Progressive Delivery
Implement a progressive delivery pipeline with automated canary analysis and rollback.

---

## Conclusion

In this lab, you've learned production-ready patterns for deploying frontend applications in Kubernetes. You now understand:

- How to create highly available frontend deployments
- Proper resource management and health checks
- Configuration management strategies for SPAs
- Zero-downtime deployment techniques
- Autoscaling based on metrics
- Ingress configuration with TLS
- Security best practices

These patterns are used in production by companies running modern web applications at scale. Apply these practices to ensure your frontend applications are reliable, secure, and performant.

**Next Steps:**
- Explore service mesh (Istio/Linkerd) for advanced traffic management
- Implement observability with Prometheus and Grafana
- Study GitOps practices for automated deployments
- Practice disaster recovery and backup strategies

---

**Lab Complete!** You now have the knowledge to deploy production-ready frontend applications in Kubernetes.
