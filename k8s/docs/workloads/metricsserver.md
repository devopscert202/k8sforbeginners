# Metrics Server and Use Cases

Metrics Server is an aggregator for resource usage data, such as CPU and memory, from Kubernetes nodes and pods. It provides this data via the Metrics API, which other Kubernetes tools, like kubectl top and the Horizontal Pod Autoscaler (HPA), rely on.

# Use Cases
### Real-Time Monitoring: View resource usage for pods and nodes.
### Autoscaling: Supports Horizontal Pod Autoscalers (HPA) by providing resource metrics.
### Debugging Performance Issues: Helps identify resource bottlenecks or misconfigured workloads.
### Capacity Planning: Enables better planning and optimization of cluster resources.

# Steps for Creating and Configuring the metrics server

### Create a new YAML file for defining a deployment
```bash
##Content of metricsserver.yaml:
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  labels:
    app: guestbook
    tier: frontend
spec:
  replicas: 3
  selector:
    matchLabels:
      tier: frontend
  template:
    metadata:
      labels:
        tier: frontend
    spec:
      containers:
        - name: php-redis
          image: gcr.io/google_samples/gb-frontend:v3

```

### Create a deployment using the YAML file
kubectl create -f deployment.yaml

### Check the status of the deployment named 'frontend'
kubectl get deployment frontend

### List all ReplicaSets in the current namespace
kubectl get rs

### List all pods with the label 'tier=frontend'
kubectl get pods -l tier=frontend

### Describe the deployment named 'frontend'
kubectl describe deploy/frontend

### Apply the metrics server components from the official repository
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

###Verify the status of the metrics server pods in the 'kube-system' namespace
kubectl get pods -n kube-system

### Download the patch file for the metrics server
wget -c https://gist.githubusercontent.com/initcron/1a2bd25353e1faa22a0ad41ad1c01b62/raw/008e23f9fbf4d7e2cf79df1dd008de2f1db62a10/k8s-metrics-server.patch.yaml

### View the content of the patch file
cat k8s-metrics-server.patch.yaml

### Patch the metrics server deployment using the downloaded patch file
kubectl patch deploy metrics-server -p "$(cat k8s-metrics-server.patch.yaml)" -n kube-system

### Verify the metrics server is running by checking its pods in the 'kube-system' namespace
kubectl get pods -n kube-system

### List resource usage (CPU/memory) for all nodes
kubectl top nodes

### Sort nodes by CPU usage
kubectl top nodes --sort-by cpu

### Sort nodes by memory usage
kubectl top nodes --sort-by memory

### Display resource usage for a specific node
kubectl top nodes master.example.com

# Key Use Cases:

### Autoscaling: Enables Horizontal Pod Autoscaler (HPA) to scale workloads dynamically based on real-time metrics.
### Resource Monitoring: Provides data for kubectl top to observe resource usage of nodes and pods.
### Troubleshooting: Identifies nodes or pods with high resource consumption.
### Capacity Planning: Helps ensure that resources are appropriately provisioned for current and future workloads.

### By following these steps, you'll have a fully functional Kubernetes deployment and Metrics Server, which is essential for resource management and operational efficiency.

### If you’re looking for alternatives to Kubernetes Metrics Server, here are some tools that can serve as replacements or enhancements, depending on your needs for monitoring and observability:

| **Tool**             | **Description**                                                                 | **Advantages**                                                                 | **Use Case**                                      |
|-----------------------|---------------------------------------------------------------------------------|--------------------------------------------------------------------------------|--------------------------------------------------|
| **Prometheus**        | Open-source monitoring and alerting toolkit.                                    | - Highly customizable with PromQL.                                            | Comprehensive monitoring and alerting.           |
|                       |                                                                                 | - Handles historical data.                                                    |                                                  |
|                       |                                                                                 | - Integrates well with Grafana.                                               |                                                  |
| **Grafana Agent**     | Lightweight Prometheus alternative for pushing metrics.                        | - Lower resource usage.                                                       | Minimalist setups integrating with Grafana Cloud.|
|                       |                                                                                 | - Simplified setup.                                                           |                                                  |
| **OpenTelemetry**     | Observability framework supporting metrics, tracing, and logs.                 | - Standardized, vendor-neutral.                                               | Unified observability for distributed systems.   |
|                       |                                                                                 | - Flexible deployment.                                                        |                                                  |
| **Datadog**           | Commercial monitoring platform with Kubernetes integration.                    | - Out-of-the-box dashboards.                                                  | Enterprises needing managed, feature-rich tools. |
|                       |                                                                                 | - Includes logging and tracing.                                               |                                                  |
| **Sysdig**            | Kubernetes and container-focused monitoring and security.                      | - Deep container runtime visibility.                                          | Kubernetes performance and security monitoring.  |
|                       |                                                                                 | - Network monitoring capabilities.                                            |                                                  |
| **cAdvisor**          | Monitors container resource usage and performance.                             | - Lightweight, focused on containers.                                         | Basic container-level monitoring.                |
|                       |                                                                                 | - Integrates with Prometheus.                                                 |                                                  |
| **Zabbix**            | General-purpose monitoring tool that supports Kubernetes.                      | - Hybrid infrastructure support.                                              | Monitoring across Kubernetes and other systems.  |
|                       |                                                                                 | - Includes alerting and reporting.                                            |                                                  |
| **VictoriaMetrics**   | High-performance time-series database compatible with Prometheus.              | - Drop-in Prometheus replacement.                                             | Scalable metric storage for Kubernetes.          |
|                       |                                                                                 | - Optimized for large-scale use.                                              |                                                  |
| **InfluxDB**          | Time-series database for Kubernetes monitoring (via Telegraf).                 | - Purpose-built for time-series data.                                         | Time-series data storage and visualization.      |
|                       |                                                                                 | - Integrates with Grafana.                                                    |                                                  |
| **CloudWatch**        | AWS monitoring for containers.                                                 | - Fully managed service.                                                      | Cloud-native Kubernetes on AWS.                  |
| **Azure Monitor**     | Azure's monitoring solution for containers.                                    | - Integrated with Azure ecosystem.                                            | Cloud-native Kubernetes on Azure.                |
| **GKE Monitoring**    | Monitoring solution for GCP’s Kubernetes Engine.                               | - Simple setup for GCP users.                                                 | Cloud-native Kubernetes on GCP.                  |

