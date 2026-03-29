# Lab 30: Horizontal Pod Autoscaling (HPA)

## Overview
In this lab, you will learn about Horizontal Pod Autoscaling (HPA), a powerful Kubernetes feature that automatically scales your application based on observed metrics. You'll deploy applications with resource requests, configure HPAs, generate load to trigger scaling, and understand best practices for auto-scaling in production.

## Prerequisites
- A running Kubernetes cluster (Minikube, Kind, or any K8s cluster)
- `kubectl` CLI tool installed and configured
- Basic understanding of Pods and Deployments (Lab 01)
- Metrics Server installed (required for HPA)
- Basic understanding of CPU and memory metrics

## Learning Objectives
By the end of this lab, you will be able to:
- Understand Horizontal Pod Autoscaling concepts
- Install and verify Metrics Server
- Configure resource requests and limits
- Create and manage HorizontalPodAutoscaler objects
- Generate load to test autoscaling
- Monitor scaling events and metrics
- Understand scaling policies and behaviors
- Implement autoscaling best practices

---

## What is Horizontal Pod Autoscaling?

**Horizontal Pod Autoscaling (HPA)** automatically scales the number of Pods in a Deployment, ReplicaSet, or StatefulSet based on observed metrics like CPU utilization, memory usage, or custom metrics.

### Key Characteristics

- **Automatic Scaling**: Scales Pods up or down based on metrics
- **Resource-Based**: Uses CPU, memory, or custom metrics
- **Target-Based**: Maintains target metric values
- **Cool-Down Periods**: Prevents rapid scaling oscillations
- **Min/Max Bounds**: Set limits on scaling range

### Horizontal vs Vertical Scaling

| Feature | Horizontal (HPA) | Vertical (VPA) |
|---------|------------------|----------------|
| **Method** | Add/remove Pods | Change Pod resources |
| **Use Case** | Handle varying load | Right-size containers |
| **Downtime** | None | Pod restart required |
| **Limitations** | Node capacity | Pod resource limits |
| **Best For** | Stateless apps | Stateful apps |

### Common Use Cases

1. **Web Applications**: Scale based on HTTP requests
2. **API Services**: Handle varying API traffic
3. **Batch Processing**: Scale workers based on queue depth
4. **Microservices**: Auto-scale individual services
5. **Seasonal Traffic**: Handle traffic spikes automatically

---

## Exercise 1: Install and Verify Metrics Server

### Step 1: Check if Metrics Server is Installed

```bash
kubectl get deployment metrics-server -n kube-system
```

If not found, proceed to install it.

### Step 2: Install Metrics Server

For most clusters:
```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

For local development (Minikube, Kind) with self-signed certificates:
```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Patch for insecure TLS (development only)
kubectl patch deployment metrics-server -n kube-system --type='json' -p='[
  {
    "op": "add",
    "path": "/spec/template/spec/containers/0/args/-",
    "value": "--kubelet-insecure-tls"
  }
]'
```

### Step 3: Verify Metrics Server is Running

```bash
kubectl get pods -n kube-system | grep metrics-server
```

Expected output:
```
metrics-server-xxxxxxxxxx-xxxxx   1/1     Running   0          1m
```

Wait for metrics to be available (can take 1-2 minutes):

```bash
kubectl top nodes
```

Expected output:
```
NAME           CPU(cores)   CPU%   MEMORY(bytes)   MEMORY%
controlplane   150m         7%     1200Mi          30%
node01         100m         5%     800Mi           20%
```

Check Pod metrics:

```bash
kubectl top pods
```

---

## Exercise 2: Deploy Application with Resource Requests

### Step 1: Review the Application Manifest

Navigate to the workloads directory:
```bash
cd k8s/labs/workloads
```

Let's examine `app-hpa.yaml`:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: php-apache
spec:
  ports:
  - port: 80
    protocol: TCP
    targetPort: 80
  selector:
    run: php-apache
---
apiVersion: apps/v1
kind: Deployment
metadata:
  labels:
    run: php-apache
  name: php-apache
spec:
  replicas: 1
  selector:
    matchLabels:
      run: php-apache
  template:
    metadata:
      labels:
        run: php-apache
    spec:
      containers:
      - image: k8s.gcr.io/hpa-example
        name: php-apache
        ports:
        - containerPort: 80
        resources:
          requests:
            cpu: 200m
```

**Understanding the Manifest:**

- `kind: Service` - Exposes the application
- `kind: Deployment` - Manages the Pods
- `replicas: 1` - Starts with 1 Pod
- `image: k8s.gcr.io/hpa-example` - Sample CPU-intensive application
- `resources.requests.cpu: 200m` - **Critical**: Requests 200 millicores (0.2 CPU)
  - HPA uses this as the baseline for percentage calculations
  - Without resource requests, HPA cannot calculate CPU percentage

### Step 2: Deploy the Application

Apply the manifest:

```bash
kubectl apply -f app-hpa.yaml
```

Expected output:
```
service/php-apache created
deployment.apps/php-apache created
```

### Step 3: Verify Deployment

Check the deployment:

```bash
kubectl get deployment php-apache
```

Expected output:
```
NAME         READY   UP-TO-DATE   AVAILABLE   AGE
php-apache   1/1     1            1           30s
```

Check the Pod:

```bash
kubectl get pods -l run=php-apache
```

Check resource usage:

```bash
kubectl top pod -l run=php-apache
```

Expected output:
```
NAME                          CPU(cores)   MEMORY(bytes)
php-apache-xxxxxxxxxx-xxxxx   1m           10Mi
```

---

## Exercise 3: Create Horizontal Pod Autoscaler

### Method 1: Using kubectl (Recommended for Learning)

Create an HPA using kubectl command:

```bash
kubectl autoscale deployment php-apache --cpu-percent=50 --min=1 --max=10
```

Expected output:
```
horizontalpodautoscaler.autoscaling/php-apache autoscaled
```

**Understanding the command:**
- `--cpu-percent=50` - Target 50% CPU utilization
- `--min=1` - Minimum 1 Pod
- `--max=10` - Maximum 10 Pods
- Target is calculated: If Pod requests 200m CPU, 50% = 100m CPU per Pod

### Method 2: Using YAML Manifest

Alternatively, review the `hpa.yaml` file:

```yaml
apiVersion: autoscaling/v1
kind: HorizontalPodAutoscaler
metadata:
  name: php-apache
spec:
  maxReplicas: 10
  minReplicas: 1
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: php-apache
  targetCPUUtilizationPercentage: 50
```

Apply it:

```bash
kubectl apply -f hpa.yaml
```

### Step 4: Verify HPA Creation

Check the HPA:

```bash
kubectl get hpa
```

Expected output:
```
NAME         REFERENCE               TARGETS   MINPODS   MAXPODS   REPLICAS   AGE
php-apache   Deployment/php-apache   1%/50%    1         10        1          30s
```

**Understanding the output:**
- `REFERENCE` - The Deployment being scaled
- `TARGETS` - Current/Target CPU percentage
- `MINPODS` - Minimum replicas
- `MAXPODS` - Maximum replicas
- `REPLICAS` - Current number of Pods

Get detailed information:

```bash
kubectl describe hpa php-apache
```

---

## Exercise 4: Generate Load and Trigger Scaling

### Step 1: Create Load Generator

Open a new terminal window and run a load generator Pod:

```bash
kubectl run -i --tty load-generator --rm --image=busybox --restart=Never -- /bin/sh
```

This creates an interactive Pod that will be deleted when you exit.

### Step 2: Generate Load

Inside the load generator Pod, run:

```bash
while true; do wget -q -O- http://php-apache; done
```

This creates an infinite loop sending requests to the php-apache service.

### Step 3: Monitor Scaling in Real-Time

In your original terminal, watch the HPA:

```bash
kubectl get hpa php-apache -w
```

You should see the CPU percentage increase:

```
NAME         REFERENCE               TARGETS    MINPODS   MAXPODS   REPLICAS   AGE
php-apache   Deployment/php-apache   1%/50%     1         10        1          2m
php-apache   Deployment/php-apache   250%/50%   1         10        1          3m
php-apache   Deployment/php-apache   250%/50%   1         10        5          3m
php-apache   Deployment/php-apache   80%/50%    1         10        5          4m
```

Watch Pods being created:

```bash
kubectl get pods -l run=php-apache -w
```

Check deployment scaling:

```bash
kubectl get deployment php-apache -w
```

### Step 4: Monitor Metrics

In another terminal, continuously check Pod metrics:

```bash
watch kubectl top pods -l run=php-apache
```

Check HPA events:

```bash
kubectl describe hpa php-apache | grep -A 10 Events
```

Expected events:
```
Events:
  Type    Reason             Age   From                       Message
  ----    ------             ----  ----                       -------
  Normal  SuccessfulRescale  2m    horizontal-pod-autoscaler  New size: 5; reason: cpu resource utilization (percentage of request) above target
```

### Step 5: Stop Load and Observe Scale Down

Return to the load generator terminal and press `Ctrl+C` to stop the load.

Exit the load generator:
```bash
exit
```

Watch the HPA scale down (takes 5 minutes by default):

```bash
kubectl get hpa php-apache -w
```

After cool-down period:
```
NAME         REFERENCE               TARGETS   MINPODS   MAXPODS   REPLICAS   AGE
php-apache   Deployment/php-apache   80%/50%   1         10        5          5m
php-apache   Deployment/php-apache   1%/50%    1         10        5          6m
php-apache   Deployment/php-apache   1%/50%    1         10        1          11m
```

---

## Exercise 5: Advanced HPA with Memory Metrics

### Step 1: Create Deployment with Memory Requests

Create `memory-app.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: memory-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: memory-app
  template:
    metadata:
      labels:
        app: memory-app
    spec:
      containers:
      - name: app
        image: k8s.gcr.io/hpa-example
        resources:
          requests:
            cpu: 200m
            memory: 64Mi
          limits:
            cpu: 500m
            memory: 128Mi
```

Apply it:

```bash
kubectl apply -f memory-app.yaml
```

### Step 2: Create HPA with Multiple Metrics

Create `memory-hpa.yaml`:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: memory-app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: memory-app
  minReplicas: 1
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 50
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 70
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
```

**Understanding the manifest:**
- `apiVersion: autoscaling/v2` - Newer API with more features
- Multiple metrics: CPU and Memory
- `behavior` section controls scaling speed
- `scaleDown.stabilizationWindowSeconds: 300` - Wait 5 minutes before scaling down
- `scaleUp.stabilizationWindowSeconds: 0` - Scale up immediately

Apply it:

```bash
kubectl apply -f memory-hpa.yaml
```

View the HPA:

```bash
kubectl get hpa memory-app-hpa
```

Expected output:
```
NAME              REFERENCE               TARGETS          MINPODS   MAXPODS   REPLICAS   AGE
memory-app-hpa    Deployment/memory-app   1%/50%, 5%/70%   1         10        1          30s
```

---

## Exercise 6: HPA with Custom Metrics (Conceptual)

### Understanding Custom Metrics

Beyond CPU and memory, HPA can use:

1. **Pod Metrics**: Custom metrics from the application (e.g., requests per second)
2. **Object Metrics**: Metrics from other Kubernetes objects (e.g., Ingress)
3. **External Metrics**: Metrics from external systems (e.g., SQS queue length)

### Example: HPA Based on HTTP Requests

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: web-app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: web-app
  minReplicas: 2
  maxReplicas: 20
  metrics:
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: "1000"
```

This requires:
- Prometheus or similar metrics system
- Custom metrics API server
- Application exposing the metrics

---

## Exercise 7: Testing HPA Limits

### Step 1: Test Minimum Replicas

Scale down the deployment manually:

```bash
kubectl scale deployment php-apache --replicas=0
```

Watch the HPA restore minimum replicas:

```bash
kubectl get pods -l run=php-apache -w
```

The HPA will scale it back to 1 (the minimum).

### Step 2: Test Maximum Replicas

Edit the HPA to set max to 3:

```bash
kubectl patch hpa php-apache -p '{"spec":{"maxReplicas":3}}'
```

Generate heavy load and observe it won't exceed 3 Pods:

```bash
kubectl run load-generator --image=busybox --restart=Never -- /bin/sh -c "while true; do wget -q -O- http://php-apache; done" &
```

Monitor:

```bash
kubectl get hpa php-apache -w
```

---

## Lab Cleanup

Remove all HPA and application resources:

```bash
# Delete HPAs
kubectl delete hpa php-apache
kubectl delete hpa memory-app-hpa

# Delete Deployments
kubectl delete deployment php-apache
kubectl delete deployment memory-app

# Delete Services
kubectl delete service php-apache

# Delete any load generator Pods
kubectl delete pod load-generator --ignore-not-found

# Verify cleanup
kubectl get hpa
kubectl get deployments
kubectl get pods
```

---

## Key Takeaways

1. **Resource Requests are Required** - HPA needs resource requests to calculate percentages
2. **Metrics Server is Essential** - Install and verify before using HPA
3. **Scaling is Not Instant** - Default cool-down periods prevent rapid changes
4. **Set Appropriate Targets** - 50-80% CPU is typical for most applications
5. **Test Your Scaling** - Always load test to verify HPA behavior
6. **Monitor Scaling Events** - Use `kubectl describe hpa` to see scaling decisions
7. **Set Min/Max Wisely** - Prevent scaling to 0 or exceeding node capacity
8. **Consider Costs** - Auto-scaling can increase infrastructure costs

---

## Best Practices

### 1. Always Set Resource Requests

```yaml
resources:
  requests:
    cpu: 200m      # Required for CPU-based HPA
    memory: 128Mi  # Required for memory-based HPA
  limits:
    cpu: 500m      # Prevent resource hogging
    memory: 256Mi
```

### 2. Use Realistic Targets

```yaml
# Good: Leaves headroom for spikes
targetCPUUtilizationPercentage: 70

# Risky: May cause constant scaling
targetCPUUtilizationPercentage: 90
```

### 3. Set Appropriate Min/Max

```yaml
spec:
  minReplicas: 2   # Ensure HA, never scale to 0
  maxReplicas: 20  # Prevent runaway scaling
```

### 4. Configure Scaling Behavior (v2 API)

```yaml
behavior:
  scaleDown:
    stabilizationWindowSeconds: 300  # Wait 5 min before scaling down
    policies:
    - type: Percent
      value: 50         # Scale down by 50% at most
      periodSeconds: 60
  scaleUp:
    stabilizationWindowSeconds: 0    # Scale up immediately
    policies:
    - type: Percent
      value: 100        # Double Pods if needed
      periodSeconds: 30
```

### 5. Monitor and Alert

```bash
# Set up alerts for:
# - HPA at max replicas (capacity issue)
# - HPA failing to scale (metrics issue)
# - Frequent scaling events (target too sensitive)
```

### 6. Use Multiple HPAs for Different Services

```bash
# Don't: Single HPA for entire app
# Do: Separate HPA for each microservice
kubectl autoscale deployment frontend --cpu-percent=70 --min=2 --max=10
kubectl autoscale deployment backend --cpu-percent=60 --min=3 --max=20
kubectl autoscale deployment worker --cpu-percent=80 --min=1 --max=50
```

---

## Additional Commands Reference

```bash
# Create HPA imperatively
kubectl autoscale deployment <name> --cpu-percent=<target> --min=<min> --max=<max>

# View HPA status
kubectl get hpa
kubectl get hpa -w  # Watch mode

# Describe HPA (view events)
kubectl describe hpa <name>

# Edit HPA
kubectl edit hpa <name>

# Patch HPA (change target)
kubectl patch hpa <name> -p '{"spec":{"targetCPUUtilizationPercentage":70}}'

# Get HPA in YAML
kubectl get hpa <name> -o yaml

# Delete HPA (keeps Deployment)
kubectl delete hpa <name>

# View current metrics
kubectl top pods
kubectl top nodes

# View HPA metrics
kubectl get hpa <name> -o jsonpath='{.status.currentMetrics}'

# Check if Metrics Server is working
kubectl get apiservice v1beta1.metrics.k8s.io -o yaml
```

---

## Troubleshooting

**Issue**: HPA shows `<unknown>` for targets

```bash
# Check Metrics Server
kubectl get pods -n kube-system | grep metrics-server

# Check metrics availability
kubectl top nodes
kubectl top pods

# Common causes:
# - Metrics Server not installed
# - Metrics Server not ready (wait 2 minutes)
# - No resource requests defined
```

**Issue**: HPA not scaling

```bash
# Check HPA status
kubectl describe hpa <name>

# Look for events like:
# - "missing request for cpu"
# - "unable to get metrics"
# - "unable to compute replica count"

# Verify resource requests
kubectl get deployment <name> -o yaml | grep -A 5 resources

# Check current load
kubectl top pods -l <label-selector>
```

**Issue**: Pods scaling up and down rapidly

```bash
# Adjust stabilization window (v2 API)
kubectl patch hpa <name> --type='json' -p='[
  {
    "op": "replace",
    "path": "/spec/behavior/scaleDown/stabilizationWindowSeconds",
    "value": 600
  }
]'

# Or adjust target threshold
kubectl patch hpa <name> -p '{"spec":{"targetCPUUtilizationPercentage":60}}'
```

**Issue**: HPA at max replicas constantly

```bash
# Increase max replicas
kubectl patch hpa <name> -p '{"spec":{"maxReplicas":20}}'

# Or optimize application (reduce CPU usage)
# Or increase resource requests (changes percentage calculation)
```

---

## Scaling Calculations

### How HPA Calculates Desired Replicas

```
desiredReplicas = ceil[currentReplicas * (currentMetricValue / targetMetricValue)]
```

**Example:**
- Current Replicas: 2
- Current CPU: 200m per Pod (average)
- Target CPU: 100m (50% of 200m request)

```
desiredReplicas = ceil[2 * (200m / 100m)] = ceil[4] = 4
```

HPA will scale to 4 Pods.

### Percentage Calculation

If Pod requests 200m CPU:
- 50% target = 100m actual CPU usage per Pod
- 100% target = 200m actual CPU usage per Pod

---

## Real-World Example: E-Commerce Application

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ecommerce-frontend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ecommerce-frontend
  template:
    metadata:
      labels:
        app: ecommerce-frontend
    spec:
      containers:
      - name: frontend
        image: ecommerce/frontend:v1
        resources:
          requests:
            cpu: 300m
            memory: 256Mi
          limits:
            cpu: 1000m
            memory: 512Mi
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ecommerce-frontend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ecommerce-frontend
  minReplicas: 3    # HA: minimum 3 for redundancy
  maxReplicas: 30   # Peak traffic: Black Friday capacity
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 50      # Increase by 50% per minute
        periodSeconds: 60
      - type: Pods
        value: 5       # Add max 5 Pods per minute
        periodSeconds: 60
      selectPolicy: Max
    scaleDown:
      stabilizationWindowSeconds: 300  # Wait 5 min
      policies:
      - type: Percent
        value: 25      # Decrease by 25% per 2 minutes
        periodSeconds: 120
      selectPolicy: Max
```

---

## Next Steps

Now that you understand Horizontal Pod Autoscaling, proceed to:
- [Lab 09: Health Checks and Probes](lab09-pod-health-probes.md) - Implement liveness and readiness probes
- Explore Vertical Pod Autoscaling (VPA)
- Learn about Cluster Autoscaler for node-level scaling

## Further Reading

- [Kubernetes HPA Documentation](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)
- [HPA Walkthrough](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale-walkthrough/)
- [Metrics Server](https://github.com/kubernetes-sigs/metrics-server)
- [Custom Metrics API](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/#support-for-custom-metrics)

---

**Lab Created**: March 2026
**Compatible with**: Kubernetes 1.24+
