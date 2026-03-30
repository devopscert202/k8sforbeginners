# Kubernetes Troubleshooting

## Introduction

Kubernetes is a powerful container orchestration platform, but as with any complex system, it can encounter various issues that require careful troubleshooting. This guide provides a curated list of common Kubernetes problems and their resolutions. While these scenarios primarily focus on standalone Kubernetes clusters, keep in mind that cloud-specific environments (such as AWS EKS, Azure AKS, and Google GKE) might involve different tools or approaches for troubleshooting.

The questions and answers included here are aimed at beginners who are building their expertise in managing Kubernetes clusters. They provide actionable insights and commands to resolve common issues effectively. For learners who wish to dive deeper into specific topics, additional references and resources are provided at the end of this section.

By practicing these troubleshooting techniques and exploring related resources, you can gain confidence in diagnosing and resolving Kubernetes issues in both standalone and cloud-based environments.

### Additional Learning Resources:
- **Official Kubernetes Documentation**: [https://kubernetes.io/docs/home/](https://kubernetes.io/docs/home/)
- **Kubernetes Networking Deep Dive**: [https://kubernetes.io/docs/concepts/cluster-administration/networking/](https://kubernetes.io/docs/concepts/cluster-administration/networking/)
- **Kubernetes API Debugging**: [https://kubernetes.io/docs/tasks/debug-application-cluster/debug-cluster/](https://kubernetes.io/docs/tasks/debug-application-cluster/debug-cluster/)
- **Cloud-Specific Kubernetes Troubleshooting Guides**:
  - AWS EKS: [https://docs.aws.amazon.com/eks/latest/userguide/troubleshooting.html](https://docs.aws.amazon.com/eks/latest/userguide/troubleshooting.html)
  - Azure AKS: [https://learn.microsoft.com/en-us/azure/aks/troubleshooting](https://learn.microsoft.com/en-us/azure/aks/troubleshooting)
  - Google GKE: [https://cloud.google.com/kubernetes-engine/docs/troubleshooting](https://cloud.google.com/kubernetes-engine/docs/troubleshooting)
- **Interactive Labs**:
  - Katacoda Scenarios: [https://www.katacoda.com/courses/kubernetes](https://www.katacoda.com/courses/kubernetes)
  - Play with Kubernetes: [https://www.katacoda.com/courses/kubernetes/playground](https://www.katacoda.com/courses/kubernetes/playground)

Now, dive into the troubleshooting scenarios and build a solid foundation for managing Kubernetes environments effectively!



# Overview of Troubleshooting in Kubernetes

## 1. What is the first step in diagnosing issues in a Kubernetes cluster?
- Check the status of the cluster using `kubectl get nodes` and `kubectl get pods -A` to identify any issues with nodes or pods.
- Inspect the events using `kubectl get events` for clues about recent errors.
- Verify the health of core components (e.g., API Server, etcd, scheduler) using `kubectl get --raw /healthz`.

## 2. How would you identify whether a problem is related to the control plane or worker nodes?
- Check control plane logs (`journalctl -u kube-apiserver`, `kube-scheduler`, `etcd`).
- Use `kubectl describe node <node-name>` to diagnose worker node status. Look for conditions like `NotReady`, taints, or errors.

## 3. Explain the importance of event logs in troubleshooting Kubernetes clusters.
- Kubernetes events provide context on cluster issues (e.g., pod scheduling failures, resource constraints).
- Use `kubectl describe pod/node` or `kubectl get events` to trace root causes.

## 4. A deployment is failing to schedule pods on nodes. What steps would you take to troubleshoot?
- Check pod status with `kubectl get pods` and use `kubectl describe pod <pod-name>` for scheduling events.
- Look for resource constraints (CPU/memory) or taints/affinity rules preventing scheduling.
- Use `kubectl describe nodes` to inspect node capacity and labels.

## 5. How would you approach debugging an intermittent issue in your Kubernetes cluster?
- Enable verbose logging for affected components (e.g., kubelet, API server).
- Monitor system metrics with tools like Prometheus or metrics-server.
- Check logs for patterns in timing or system load when issues occur.

# Troubleshooting Kubernetes Cluster

## 6. A cluster is unresponsive. How would you verify the health of the control plane components?
- Check the health endpoints: `kubectl get --raw /healthz`.
- Inspect logs for API Server (`journalctl -u kube-apiserver`), scheduler, and controller-manager.
- Verify etcd health using `etcdctl endpoint health`.

## 7. What are the common causes of API Server unavailability, and how would you troubleshoot them?
**Causes**:
- Out-of-memory (OOM), network issues, or etcd failure.

**Troubleshooting**:
- Check API Server logs for errors (`journalctl -u kube-apiserver`).
- Verify etcd connectivity.
- Check resource limits with `kubectl top pod` in the `kube-system` namespace.

## 8. How would you diagnose a failed kubeadm initialization during cluster setup?
- Examine the output of `kubeadm init` for specific errors.
- Check logs at `/var/log/kubelet.log` and `/var/log/containers`.
- Verify prerequisites: network connectivity, hostname resolution, and CNI plugin setup.

## 9. Describe the steps to recover from a failed etcd quorum.
1. Identify the available etcd nodes with `etcdctl member list`.
2. Restore etcd from a backup using `etcdctl snapshot restore`.
3. Reconfigure the etcd cluster and restart control plane components.

## 10. Nodes in your cluster are unreachable. What diagnostic commands would you use to find the root cause?
- Use `kubectl get nodes` to identify unreachable nodes.
- SSH into the node and check kubelet and container runtime status (`systemctl status kubelet`).
- Verify network connectivity between the node and control plane.

## 11. How would you troubleshoot a cluster-wide issue where all pods are stuck in Pending state?
- Check events with `kubectl get events`.
- Verify node capacity using `kubectl describe nodes`.
- Ensure the CNI plugin is functioning correctly.

## 12. You observe slow responses from the Kubernetes API Server. What metrics or logs would you examine?
- Inspect API Server logs for slow requests.
- Check etcd latency with `etcdctl endpoint status`.
- Use metrics-server or Prometheus to monitor API Server resource usage.

## 13. A cluster upgrade fails halfway through. How would you proceed with troubleshooting and rollback?
- Check the status of updated components.
- Review upgrade logs from kubeadm or the installer tool.
- Rollback to the previous working version using backups.

## 14. What are the key diagnostic steps for an issue where pods are evicted from nodes frequently?
- Check pod eviction events using `kubectl describe pod`.
- Diagnose resource pressure on nodes with `kubectl top node`.
- Adjust eviction thresholds in the kubelet configuration.

## 15. Describe how you would troubleshoot a degraded Kubernetes cluster after a new component was installed.
- Check component logs for errors.
- Verify compatibility with the Kubernetes version.
- Use `kubectl get events` for recent failures and system resource impacts.

# Kubernetes Cluster Logging Architecture

## 16. What are the main components of Kubernetes logging architecture?
- Node-level logging (e.g., kubelet logs).
- Cluster-level logging (e.g., Fluentd, ELK stack).
- Log aggregation systems (e.g., Loki, Elasticsearch).

## 17. How would you verify that Fluentd or a similar logging agent is running correctly on all nodes?
- Use `kubectl get pods -n kube-system` to check Fluentd pods.
- Review logs from Fluentd pods for errors.

## 18. Logs for a specific pod are missing from your centralized logging system. How would you debug this?
- Verify the Fluentd configuration for log collection from the namespace.
- Check the pod's logging output with `kubectl logs`.

## 19. A log ingestion service is experiencing high latency. How would you troubleshoot this in the context of Kubernetes?
- Check resource usage on ingestion services.
- Inspect network latency and load between Fluentd and the aggregation system.

## 20. Describe a scenario where the Kubernetes logging pipeline itself can be the source of the issue.

- Fluentd crash loops due to malformed log entries.
- Network congestion between nodes and the central logging service.

## Cluster and Node Logs

### 21. How would you access logs for a specific Kubernetes node?
- Use `journalctl` to check system logs:
  ```bash
  journalctl -u kubelet
  journalctl -u docker (or containerd)
  ```

### 22. What are the key logs to examine when troubleshooting a node connectivity issue?
- **Kubelet logs**:  
  ```bash
  journalctl -u kubelet
  ```
- **Network plugin logs** (e.g., Calico, Cilium).
- **System logs** for network interfaces: `dmesg` or `/var/log/syslog`.

### 23. A node fails to join the cluster. Which logs would you check to diagnose the issue?
- Kubelet logs on the failing node:  
  ```bash
  journalctl -u kubelet
  ```
- API Server logs for join attempts.
- Inspect `kubeadm` logs if `kubeadm` was used.

### 24. How would you use `journalctl` to diagnose a node failure in Kubernetes?
- Use `journalctl` to filter logs:
  ```bash
  journalctl -u kubelet --since "1 hour ago"
  journalctl -k | grep -i error
  ```

### 25. Explain the steps to analyze disk pressure issues on a Kubernetes node using logs.
- Check kubelet logs for eviction events due to disk pressure.
- Use `df -h` to inspect disk usage on the node.
- Verify log rotation and cleanup policies.

---

## Understanding Cluster and Node Logs

### 26. How can you filter logs to identify issues with specific Kubernetes components, such as kube-proxy?
- Use `kubectl logs` to fetch logs from kube-proxy pods.
- Apply labels to filter specific logs:
  ```bash
  kubectl logs -l k8s-app=kube-proxy -n kube-system
  ```

### 27. What are the best practices for managing and storing cluster and node logs for long-term analysis?
- Use a centralized logging system (e.g., ELK stack, Loki).
- Enable log rotation policies to manage disk usage.
- Store logs in an object storage system (e.g., S3) for long-term retention.

### 28. A node consistently reports NotReady status. What logs would help identify the root cause?
- **Kubelet logs**:  
  ```bash
  journalctl -u kubelet
  ```
- **Container runtime logs**:  
  ```bash
  journalctl -u docker or containerd
  ```
- **Network plugin logs** if connectivity is an issue.

### 29. How would you verify that node logs are correctly being sent to your centralized logging solution?
- Check Fluentd logs for successful forwarding.
- Cross-check node logs with the centralized log aggregation system.

### 30. How can log rotation be managed effectively in Kubernetes to prevent disk saturation?
- Configure log rotation for the container runtime (e.g., Docker or containerd).
- Use kubelet's `--log-max-size` and `--log-max-backups` flags.

---

## Node Not Ready

### 31. What are the common reasons for a node to report NotReady status?
- Network connectivity issues.
- Resource exhaustion (CPU, memory, disk).
- Kubelet failure or inability to communicate with the control plane.

### 32. Describe the steps to diagnose and fix a NotReady node caused by a networking issue.
- Verify node connectivity with the control plane using `ping` or `curl`.
- Check CNI plugin logs.
- Inspect kube-proxy and kubelet logs for errors.

### 33. How would you resolve a NotReady node due to high memory usage?
- Use `kubectl top node` to identify resource usage.
- Evict non-essential pods or increase node memory capacity.

### 34. A node is marked NotReady because the kubelet cannot communicate with the control plane. How would you troubleshoot?
- Check kubelet logs:  
  ```bash
  journalctl -u kubelet
  ```
- Verify network routes and firewall settings.
- Ensure API Server is reachable from the node.

### 35. How would you fix a node marked NotReady due to missing CNI plugins?
- Reinstall or reconfigure the CNI plugin (e.g., Calico, Flannel).
- Verify the correct CNI configuration is in `/etc/cni/net.d/`.

---

## Container Logs

### 36. How would you view the logs of a specific container running in a pod?
- Use:
  ```bash
  kubectl logs <pod-name> -c <container-name>
  ```

### 37. A pod is not generating logs. How would you troubleshoot the issue?
- Verify the container is running:  
  ```bash
  kubectl describe pod <pod-name>
  ```
- Check application-level logging configuration inside the container.

### 38. Logs from a container are incomplete or truncated. What could be the cause?
- Check if log rotation limits have been exceeded.
- Verify the container runtime's logging driver settings.

### 39. How would you configure log rotation for a containerized application?
- Configure Docker log rotation in `/etc/docker/daemon.json`:
  ```json
  {
    "log-driver": "json-file",
    "log-opts": {
      "max-size": "10m",
      "max-file": "3"
    }
  }
  ```

### 40. A container is producing excessive logs, affecting disk space. How would you manage this?
- Implement log rotation policies.
- Redirect logs to a centralized logging system.
- Limit logging verbosity in the application.

---

## Understanding Container Logs

### 41. How can you identify the source of an application issue using container logs?
- Use `kubectl logs` to examine errors or warnings in the logs.
- Correlate timestamps in logs with observed issues.

### 42. Describe how to debug a container that fails to start using its logs.
- Use:
  ```bash
  kubectl logs <pod-name> --previous
  ```
  to view logs from a failed container instance.

### 43. Logs are showing "connection refused" errors. How would you diagnose this in a Kubernetes context?
- Check service and endpoint configurations:
  ```bash
  kubectl get svc
  kubectl describe endpoints <service-name>
  ```
- Verify network policies and firewall rules.

### 44. How would you redirect container logs to a persistent volume for better analysis?
- Mount a persistent volume to the container and redirect logs to a file stored in the volume.

### 45. Explain the steps to analyze logs from a multi-container pod.
- Use:
  ```bash
  kubectl logs <pod-name> -c <container-name>
  ```
  for each container.
- Correlate logs across containers using timestamps.

## Advanced Kubernetes Troubleshooting (continued)

### 46. How would you debug a pod stuck in `CrashLoopBackOff`?
- Inspect pod details:
  ```bash
  kubectl describe pod <pod-name>
  ```
- View logs of the crashing container:
  ```bash
  kubectl logs <pod-name> --previous
  ```
- Check for misconfigured environment variables, application errors, or missing dependencies.

### 47. A pod is stuck in `Pending` state. What could be the cause, and how would you troubleshoot?
- Verify resource requests and limits:
  ```bash
  kubectl describe pod <pod-name>
  ```
- Check node capacity and scheduler events.
- Ensure sufficient cluster resources (CPU, memory).

### 48. How do you debug DNS resolution issues in a Kubernetes cluster?
- Verify CoreDNS is running:
  ```bash
  kubectl get pods -n kube-system -l k8s-app=kube-dns
  ```
- Use a test pod to check DNS resolution:
  ```bash
  kubectl run dns-test --image=busybox:1.28 --rm -it -- nslookup kubernetes.default
  ```

### 49. What steps would you take to diagnose a Kubernetes API Server issue?
- Check API Server logs for errors.
- Verify API Server connectivity:
  ```bash
  kubectl cluster-info
  ```
- Inspect etcd health if it impacts the API Server.

### 50. Describe how to troubleshoot a failing deployment in Kubernetes.
- Inspect deployment events:
  ```bash
  kubectl describe deployment <deployment-name>
  ```
- Check pod status and logs.
- Verify correct image version and configuration.

### 51. How can you debug network issues within a Kubernetes cluster?
- Check network policies and rules.
- Use tools like `ping`, `traceroute`, or `curl` to test connectivity between pods.
- Inspect logs for network plugins (e.g., Calico, Flannel).

### 52. What are the common reasons for kubelet to fail, and how would you troubleshoot?
- **Out-of-resource issues**: Check node resource usage with `kubectl top node`.
- **Configuration errors**: Inspect kubelet configuration files (e.g., `/var/lib/kubelet/config.yaml`).
- **Logs**: Use `journalctl -u kubelet` for troubleshooting.

### 53. How would you troubleshoot a Service that is unreachable within the cluster?
- Verify Service and endpoint configurations:
  ```bash
  kubectl get svc <service-name>
  kubectl describe endpoints <service-name>
  ```
- Check network policies and firewall rules.
- Test connectivity from a test pod:
  ```bash
  kubectl run test-pod --image=busybox:1.28 --rm -it -- wget <service-ip>
  ```

### 54. What steps would you take to investigate high pod restart counts in a Kubernetes cluster?
- Check pod events for errors:
  ```bash
  kubectl describe pod <pod-name>
  ```
- Inspect container logs for application-level issues.
- Ensure the readiness and liveness probes are configured correctly.

### 55. How would you debug an issue with Kubernetes Ingress?
- Verify Ingress resource configuration:
  ```bash
  kubectl describe ingress <ingress-name>
  ```
- Check the status of the Ingress controller.
- Test DNS resolution and connectivity to the backend pods.

### 56. A Kubernetes node is under high CPU usage. How would you investigate?
- Identify high-usage pods:
  ```bash
  kubectl top pod --all-namespaces
  ```
- Check node resource usage:
  ```bash
  kubectl top node
  ```
- Inspect logs and metrics for resource-hungry workloads.

### 57. How can you diagnose and resolve etcd-related issues in Kubernetes?
- Check etcd health:
  ```bash
  etcdctl endpoint health
  ```
- Verify etcd pod logs in the control plane:
  ```bash
  kubectl logs -n kube-system etcd-<node-name>
  ```
- Monitor disk I/O and latency metrics for etcd.

### 58. How would you troubleshoot a Kubernetes Job that is stuck in `Active` state?
- Check pod logs for errors.
- Verify Job configuration for incorrect parameters (e.g., `completions`, `parallelism`).
- Inspect node and resource availability.

### 59. What tools can help with advanced Kubernetes debugging?
- **kubectl debug**: Create ephemeral containers for debugging.
- **Lens**: Visualize and troubleshoot Kubernetes clusters.
- **Netshoot**: A network troubleshooting pod.
- **kubectl-trace**: Use BPF tracing for advanced diagnostics.

### 60. How would you diagnose and resolve issues with Kubernetes volume mounting?
- Check pod events for volume errors:
  ```bash
  kubectl describe pod <pod-name>
  ```
- Inspect the storage class and persistent volume configurations.
- Verify node permissions and mount points.

Here is the content with numbered questions starting from **61**:

```markdown
## Kubernetes Events  

### 61. What are Kubernetes events, and how do they help in troubleshooting?  
Kubernetes events are system-generated records that provide insights into resource state changes, failures, and activity within the cluster. They are helpful in diagnosing issues like pod scheduling, networking errors, and resource limits.  

**Use:**  
```bash
kubectl get events -A
```
Events reveal details such as why a pod failed to start or why a node is marked NotReady.  

### 62. How would you view events for a specific pod in Kubernetes?  
Use the following command to get events for a specific pod:  

```bash
kubectl describe pod <pod-name> -n <namespace>
```
The events section at the bottom will display issues like container restarts, image pull errors, or scheduling problems.  

### 63. A pod is stuck in the Pending state. What events would you look for to identify the issue?  
**Use:**  
```bash
kubectl describe pod <pod-name>
```
**Check for:**  
- **Insufficient resources**: Look for messages like `FailedScheduling` with `Insufficient CPU/memory`.  
- **Node selectors**: Verify node affinity/taints in pod spec.  
- **Storage issues**: Ensure persistent volumes are bound.  

### 64. How would you troubleshoot frequent Evicted events in your cluster?  
Eviction often occurs due to resource pressure (e.g., disk or memory).  

**Check disk pressure:**  
```bash
kubectl describe node <node-name>
```
Look for `DiskPressure` or `MemoryPressure` in node conditions.  

**Check pod resource limits**: Ensure pods have proper resource requests/limits defined in the spec.  

### 65. Explain how you would monitor events at the cluster level for early issue detection.  
- Use tools like Lens, `kubectl get events`, or enable logging integration with a monitoring tool (e.g., Prometheus/Grafana).  
- Automate event monitoring with alerts using tools like Loki, Fluentd, or ELK Stack.  

---

## Application Troubleshooting  

### 66. An application deployed on Kubernetes is not responding. What steps would you take to identify the issue?  
1. **Verify pod status:**  
    ```bash
    kubectl get pods -n <namespace>
    ```  
2. **Debug logs:**  
    ```bash
    kubectl logs <pod-name> -n <namespace>
    ```  
3. **Check readiness and liveness probes in the pod spec.**  
4. **Test networking connectivity:**  
    ```bash
    kubectl exec -it <pod-name> -- curl <service-name>:<port>
    ```  

### 67. How would you troubleshoot a failing deployment caused by invalid container images?  
- **Check deployment events:**  
    ```bash
    kubectl describe deployment <deployment-name>
    ```  
- Look for image pull errors and ensure the image exists in the container registry. Test with:  
    ```bash
    docker pull <image-name>
    ```  

### 68. A pod's readiness probe is failing. How would you debug this?  
1. **Inspect pod events:**  
    ```bash
    kubectl describe pod <pod-name>
    ```  
2. **Test the readiness probe command or endpoint manually inside the pod:**  
    ```bash
    kubectl exec -it <pod-name> -- curl <probe-endpoint>
    ```  

### 69. How would you diagnose a failing application with no logs being generated?  
1. Verify logging setup in the application code.  
2. Check if the container process is running:  
    ```bash
    kubectl exec -it <pod-name> -- ps aux
    ```  
3. Ensure logs are written to `stdout` and `stderr`.  

### 70. Describe how you would troubleshoot an application crash loop (CrashLoopBackOff).  
1. **Check logs:**  
    ```bash
    kubectl logs <pod-name>
    ```  
2. **Analyze the container exit code:**  
    ```bash
    kubectl describe pod <pod-name>
    ```  
3. **Common fixes:** Address configuration issues, increase resource limits, or debug application logic.  

---

## Monitoring Tools  

### 71. What are the best monitoring tools for Kubernetes, and how do they assist in troubleshooting?  
Popular tools include:  
- **Prometheus**: Metric collection.  
- **Grafana**: Data visualization.  
- **Loki**: Log aggregation.  
- **Kube-state-metrics**: Kubernetes-specific metrics.  

### 72. Describe how you would set up Prometheus to monitor a Kubernetes cluster.  
Use the `kube-prometheus-stack` Helm chart for deployment:  
```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install kube-prometheus-stack prometheus-community/kube-prometheus-stack
```  

### 73. How would you troubleshoot an issue using metrics collected by a monitoring tool?  
1. Identify anomalies in metrics such as CPU usage, memory, or pod restarts using Prometheus or Grafana.  
2. Correlate these anomalies with logs and events for deeper insights.  

### 74. Explain the role of Grafana in visualizing Kubernetes metrics.  
Grafana connects to Prometheus or other data sources to create custom dashboards for visualizing resource usage, pod performance, and cluster health.  

### 75. How would you use monitoring tools to debug a sudden increase in pod resource usage?  
**Steps:**  
1. Identify pods with increased resource usage via metrics.  
2. Examine container logs for potential memory leaks or high CPU spikes.  
3. Use tools like `kubectl top` to see live resource usage:  
    ```bash
    kubectl top pod -n <namespace>
    ```  

---

## Commands to Debug Networking Issues  

### 76. A pod cannot reach another pod within the same namespace. What debugging commands would you use?  
1. **Verify service discovery:**  
    ```bash
    kubectl get endpoints <service-name> -n <namespace>
    ```  
2. **Test pod-to-pod communication:**  
    ```bash
    kubectl exec -it <pod-name> -- ping <target-pod-IP>
    kubectl exec -it <pod-name> -- curl <target-pod-IP>:<port>
    ```  

### 77. How would you test DNS resolution for a service in Kubernetes?  
```bash
kubectl exec -it <pod-name> -- nslookup <service-name>
kubectl exec -it <pod-name> -- dig <service-name>
```  

### 78. A pod cannot access an external URL. What commands would help diagnose the issue?  
1. **Check DNS resolution:**  
    ```bash
    kubectl exec -it <pod-name> -- nslookup <url>
    ```  
2. **Test network access:**  
    ```bash
    kubectl exec -it <pod-name> -- curl <url>
    ```  

### 79. How would you debug issues with Kubernetes network policies blocking traffic?  
Use:  
```bash
kubectl describe networkpolicy <policy-name> -n <namespace>
```
Check whether ingress/egress rules allow the required traffic.  

### 80. Explain how to use traceroute and ping to debug networking issues in a cluster.  
- Run `traceroute` from a pod:  
    ```bash
    kubectl exec -it <pod-name> -- traceroute <target-IP>
    ```  
- Use `ping` to verify connectivity:  
    ```bash
    kubectl exec -it <pod-name> -- ping <target-IP>
    ```  
```

```markdown
## Handling Component Failure Threshold  

### 81. What are the common causes of failure in Kubernetes components, and how would you address them?  
Common causes include:  
- **API Server Failure**: Check API server logs for errors:  
   ```bash
   journalctl -u kube-apiserver
   ```  
   Ensure API server certificates and kubeconfig are valid.  

- **etcd Issues**: Check etcd cluster health:  
   ```bash
   etcdctl endpoint health
   ```  

- **Scheduler/Controller Issues**: Check pod logs:  
   ```bash
   kubectl logs -n kube-system kube-scheduler-<pod-name>
   kubectl logs -n kube-system kube-controller-manager-<pod-name>
   ```  
   Restart the component if required using systemd or by recreating the pod.  

### 82. How would you identify and recover from a kube-scheduler failure?  
- Check pod logs:  
   ```bash
   kubectl logs -n kube-system kube-scheduler-<pod-name>
   ```  
- Verify pod status:  
   ```bash
   kubectl get pod -n kube-system
   ```  
- If it's a systemd-managed service:  
   ```bash
   systemctl status kube-scheduler
   systemctl restart kube-scheduler
   ```  
- Ensure configuration files (e.g., `kube-scheduler.yaml`) are correctly set in `/etc/kubernetes/manifests/`.  

### 83. Describe how you would diagnose a kube-controller-manager performance issue.  
- Check logs for errors:  
   ```bash
   kubectl logs -n kube-system kube-controller-manager-<pod-name>
   ```  
- Analyze CPU/memory usage:  
   ```bash
   kubectl top pod -n kube-system | grep kube-controller-manager
   ```  
- Investigate reconciliation delays using metrics tools like Prometheus.  

### 84. What steps would you take to recover a failed kube-apiserver?  
- Check API server logs:  
   ```bash
   journalctl -u kube-apiserver
   ```  
- Validate that certificates in `/etc/kubernetes/pki` are valid and not expired.  
- Restart the API server pod if running as a static pod:  
   ```bash
   systemctl restart kubelet
   ```  
- Ensure no port conflicts on `6443`.  

### 85. Explain how to handle a situation where the kubelet crashes frequently on a node.  
- Review kubelet logs:  
   ```bash
   journalctl -u kubelet
   ```  
- Verify kubelet configuration:  
   Check `/var/lib/kubelet/config.yaml` for misconfigurations.  
- Restart kubelet service:  
   ```bash
   systemctl restart kubelet
   ```  
- Check node resource usage (disk, memory):  
   ```bash
   df -h
   free -m
   ```  

---

## Troubleshooting Networking Issues  

### 86. A service is unreachable from outside the cluster. How would you diagnose this issue?  
- Check the service type (e.g., NodePort, LoadBalancer):  
   ```bash
   kubectl get svc <service-name>
   ```  
- Verify NodePort accessibility:  
   ```bash
   curl <node-IP>:<nodePort>
   ```  
- Inspect firewall rules or cloud provider settings.  

### 87. Pods in different namespaces cannot communicate. How would you troubleshoot this?  
- Ensure NetworkPolicies are not restricting traffic:  
   ```bash
   kubectl describe networkpolicy -n <namespace>
   ```  
- Test pod-to-pod communication using:  
   ```bash
   kubectl exec -it <pod-name> -n <namespace> -- ping <target-pod-IP>
   ```  

### 88. How would you resolve a misconfigured Ingress that is blocking traffic?  
- Check Ingress resource configuration:  
   ```bash
   kubectl describe ingress <ingress-name>
   ```  
- Inspect logs of the Ingress controller:  
   ```bash
   kubectl logs -n <ingress-namespace> <ingress-controller-pod>
   ```  

### 89. A NetworkPolicy is blocking traffic unexpectedly. How would you debug this?  
- Verify NetworkPolicy rules:  
   ```bash
   kubectl describe networkpolicy <policy-name> -n <namespace>
   ```  
- Test access by temporarily removing the policy.  

### 90. How would you diagnose and fix a performance bottleneck in Kubernetes networking?  
- Monitor network traffic using tools like **Weave Scope**.  
- Check node resources (e.g., `kube-proxy`):  
   ```bash
   kubectl top pod -n kube-system | grep kube-proxy
   ```  

---

## Monitoring and Logging  

### 91. How would you set up a centralized logging and monitoring solution for a Kubernetes cluster?  
- Use tools like Fluentd, ELK Stack, or Loki for centralized logging.  
- Set up Prometheus and Grafana for metrics.  
- Deploy logging agents:  
   ```bash
   helm install fluentd stable/fluentd
   ```  

### 92. Explain how you would use logs to troubleshoot a failing pod.  
- Check pod logs:  
   ```bash
   kubectl logs <pod-name> -n <namespace>
   ```  
- If logs don’t exist, verify the container is running:  
   ```bash
   kubectl describe pod <pod-name>
   ```  

### 93. Describe how to use metrics from monitoring tools to diagnose high memory usage in a pod.  
- Use **kubectl top**:  
   ```bash
   kubectl top pod <pod-name>
   ```  
- Analyze detailed metrics in Prometheus or Grafana dashboards.  

### 94. How would you correlate logs and metrics to identify the root cause of an application issue?  
- Use tools like **Loki** for logs and Prometheus for metrics in a unified dashboard like Grafana.  

### 95. What steps would you take to configure log retention for compliance purposes in Kubernetes?  
- Configure retention in log aggregation tools (e.g., Elasticsearch or Loki):  
   ```yaml
   retention:
     days: 30
   ```  

---

## Networking and Service Connectivity  

### 96. A NodePort service is not accessible from an external machine. What steps would you take to identify and resolve the issue?  
- Verify service is exposed:  
   ```bash
   kubectl describe svc <service-name>
   ```  
- Check node firewall rules.  

### 97. Pods in two namespaces cannot communicate despite a service being created. How would you debug this scenario?  
- Verify service endpoints:  
   ```bash
   kubectl get endpoints -n <namespace>
   ```  
- Test pod communication using `curl` or `ping`.  

### 98. A pod cannot resolve DNS queries. How would you troubleshoot DNS issues in Kubernetes?  
- Verify `kube-dns` or `CoreDNS` pods are running:  
   ```bash
   kubectl get pods -n kube-system
   ```  
- Test DNS resolution:  
   ```bash
   kubectl exec -it <pod-name> -- nslookup <service-name>
   ```  

### 99. A LoadBalancer service is not exposing the application to the public. What steps would you follow to diagnose this issue?  
- Verify external IP assignment:  
   ```bash
   kubectl get svc <service-name>
   ```  
- Check cloud provider logs for LoadBalancer provisioning errors.  

### 100. Internal communication between pods fails in a Calico CNI-enabled cluster. How would you identify the root cause?  
- Inspect Calico logs:  
   ```bash
   kubectl logs -n kube-system <calico-pod>
   ```  
- Check if Calico policies allow traffic:  
   ```bash
   calicoctl get policy
   ```  


## Networking and Service Connectivity (Continued)

### 101. A Multi-Port Service Pod is not accessible through its secondary port. How would you debug this issue?  
- Verify the service's configuration for multiple ports:  
   ```bash
   kubectl describe svc <service-name>
   ```  
- Check pod's container port mappings in the deployment:  
   ```bash
   kubectl describe pod <pod-name>
   ```  
- Use a `curl` or `nc` command to test connectivity to the secondary port:  
   ```bash
   curl <pod-IP>:<secondary-port>
   ```  
- Inspect the logs of the application running on the secondary port to ensure it's serving traffic.  

### 102. The traffic is being routed incorrectly by an Ingress Controller. How would you troubleshoot the misconfiguration?  
- Inspect the Ingress resource for routing rules:  
   ```bash
   kubectl describe ingress <ingress-name>
   ```  
- Check the logs of the Ingress Controller pod:  
   ```bash
   kubectl logs <ingress-controller-pod-name> -n <ingress-namespace>
   ```  
- Validate DNS records and ensure they point to the correct IP.  
- Test the backend service manually:  
   ```bash
   curl <service-clusterIP>:<service-port>
   ```  
- If using annotations, ensure they are properly configured for your Ingress Controller.  

### 103. A service is not registering endpoints for its pods. What could cause this issue, and how would you address it?  
- Check if the pods have matching labels for the service selector:  
   ```bash
   kubectl describe svc <service-name>
   kubectl get pods --show-labels
   ```  
- Ensure the pods are running and Ready:  
   ```bash
   kubectl get pods -o wide
   ```  
- Verify if the endpoints exist:  
   ```bash
   kubectl get endpoints <service-name>
   ```  
- Fix misconfigured selectors or health probes if the pod is not considered Ready.  

### 104. A pod cannot reach a NodePort service running on a different node. How would you approach this problem?  
- Verify service details, including NodePort allocation:  
   ```bash
   kubectl describe svc <service-name>
   ```  
- Test connectivity to the NodePort from the pod using `curl`:  
   ```bash
   curl <node-IP>:<NodePort>
   ```  
- Ensure kube-proxy is running correctly on both nodes:  
   ```bash
   kubectl get pods -n kube-system | grep kube-proxy
   kubectl logs -n kube-system <kube-proxy-pod>
   ```  
- Check firewall settings or security groups for any rules blocking the NodePort traffic.  

### 105. All pods using a ClusterIP service are failing to respond to requests. What steps would you take to identify the problem?  
- Validate the ClusterIP service:  
   ```bash
   kubectl describe svc <service-name>
   ```  
- Test connectivity to the ClusterIP:  
   ```bash
   curl <ClusterIP>:<service-port>
   ```  
- Check the endpoints of the service:  
   ```bash
   kubectl get endpoints <service-name>
   ```  
- Inspect the logs of the pods behind the service for errors:  
   ```bash
   kubectl logs <pod-name>
   ```  

---

## Troubleshooting Application Issues  

### 106. An application deployed on Kubernetes is not responding. What steps would you take to identify the issue?  
- Check the pod status:  
   ```bash
   kubectl get pods -l app=<application-label>
   ```  
- Verify if the pod is reachable:  
   ```bash
   kubectl exec -it <pod-name> -- curl localhost:<application-port>
   ```  
- Inspect the logs for errors:  
   ```bash
   kubectl logs <pod-name>
   ```  
- Validate the health probe configuration in the deployment manifest:  
   ```yaml
   readinessProbe:
     httpGet:
       path: /
       port: <port>
   ```  

### 107. How would you troubleshoot a failing deployment caused by invalid container images?  
- Check pod events for errors:  
   ```bash
   kubectl describe pod <pod-name>
   ```  
- Inspect the image registry URL and tag in the deployment YAML:  
   ```yaml
   containers:
   - name: app
     image: <image-name>:<tag>
   ```  
- Ensure the image exists in the registry using tools like `docker pull` or equivalent.  
- Verify image pull secrets if the registry requires authentication:  
   ```bash
   kubectl get secret <secret-name>
   ```

### 108. How would you debug application scaling issues in Kubernetes?  
- Check Horizontal Pod Autoscaler (HPA) configuration:  
   ```bash
   kubectl describe hpa <hpa-name>
   ```  
- Verify resource limits and requests in the deployment spec:  
   ```yaml
   resources:
     requests:
       memory: "128Mi"
       cpu: "500m"
     limits:
       memory: "256Mi"
       cpu: "1"
   ```  
- Inspect metrics used by HPA for scaling (e.g., CPU, custom metrics).  
- Analyze resource consumption using `kubectl top` or Prometheus metrics.  

### 109. A pod is stuck in the Pending state. What events would you look for to identify the issue?  
- Check the pod events:  
   ```bash
   kubectl describe pod <pod-name>
   ```  
   Look for errors like:  
   - **NodeAffinity/Resource constraints**: No suitable nodes available.  
   - **Taint/Toleration mismatch**.  
- Validate if there are available nodes:  
   ```bash
   kubectl get nodes
   kubectl describe node <node-name>
   ```  
- Inspect cluster resource limits:  
   ```bash
   kubectl get resourcequota -A
   ```  

### 110. A pod's readiness probe is failing. How would you debug this?  
- Check the readiness probe configuration in the pod spec:  
   ```yaml
   readinessProbe:
     httpGet:
       path: /healthz
       port: <port>
     initialDelaySeconds: 5
     periodSeconds: 10
   ```  
- Test the readiness endpoint from within the pod:  
   ```bash
   kubectl exec -it <pod-name> -- curl http://localhost:<port>/healthz
   ```  
- Inspect pod events for probe failures:  
   ```bash
   kubectl describe pod <pod-name>
   ```  


----

    
### **Logs and Events (100–109)**

100. **Logs for an application pod are incomplete or truncated. How would you address this issue?**  
   - Ensure proper logging configuration in the application.  
   - Check the log rotation and retention policies on the node.  
   - Validate disk space availability on the node.  

101. **A pod's logs indicate frequent restarts due to an OOMKilled event. What would you do to debug this?**  
   - Check container resource limits: `kubectl describe pod <pod-name>`.  
   - Increase memory limits if necessary or optimize the application.  
   - Monitor memory usage with `kubectl top pod`.  

102. **Events for a deployment show FailedScheduling. What are the possible causes, and how would you troubleshoot this?**  
   - Check node capacity and resource requests.  
   - Verify taints and tolerations for the deployment.  
   - Inspect `kubectl describe pod` for more event details.  

103. **A node reports disk pressure. What logs would you check to diagnose the cause of this issue?**  
   - Inspect `journalctl -u kubelet`.  
   - Check `/var/log/` for disk usage or inode exhaustion.  
   - Use `df -h` and `du -sh` to identify large directories.  

104. **Kubernetes logs indicate connection refused errors from the API server. How would you debug this?**  
   - Check API server pod logs (`kubectl logs -n kube-system`).  
   - Verify control plane node networking and firewall rules.  
   - Test connectivity using `curl <api-server-url>`.  

105. **A pod is evicted due to high memory usage on the node. How would you troubleshoot and prevent this from happening again?**  
   - Use `kubectl describe pod` to confirm eviction reasons.  
   - Adjust resource requests/limits in the pod spec.  
   - Monitor node memory usage and scale up nodes if needed.  

106. **No logs are available for a pod due to the container failing to start. What diagnostic steps would you follow?**  
   - Check the pod's events with `kubectl describe pod`.  
   - Inspect the container runtime logs (e.g., containerd or Docker).  
   - Test image pull availability and configuration.  

107. **An application reports 503 Service Unavailable errors intermittently. How would you diagnose this using logs and events?**  
   - Inspect backend pod logs for crashes or readiness probe failures.  
   - Check Service and Ingress configurations.  
   - Use `kubectl describe service` to verify endpoints.  

108. **Fluentd is not forwarding logs from a node to the central logging system. How would you debug this issue?**  
   - Verify Fluentd configuration files (e.g., `fluent.conf`).  
   - Check Fluentd pod logs for errors.  
   - Confirm the central logging system's accessibility.  

109. **Logs indicate that a pod's readiness probe is failing. How would you identify the cause?**  
   - Inspect the readiness probe configuration in the deployment spec.  
   - Use `kubectl exec` to manually test the probe's endpoint.  
   - Check application logs for startup or health issues.  

---

### **Pod and Deployment Troubleshooting (110–119)**  
110. **A deployment rollout is stuck. What commands and steps would you use to identify the issue?**  
   - Run `kubectl rollout status deployment <deployment-name>`.  
   - Inspect events with `kubectl describe deployment`.  
   - Check for failing pods or invalid configurations.  

111. **Pods are stuck in Pending state due to insufficient CPU or memory on the nodes. How would you resolve this?**  
   - Use `kubectl describe pod` to confirm resource requests.  
   - Scale the cluster or reduce pod resource requests.  
   - Check node taints or affinity rules.  

112. **A pod is stuck in ContainerCreating state. What are the possible causes, and how would you address them?**  
   - Inspect events with `kubectl describe pod`.  
   - Check volume attachment or CNI plugin issues.  
   - Verify image pull accessibility.  

113. **A deployment rollback fails. What could cause this issue, and how would you resolve it?**  
   - Check for missing ReplicaSets from previous revisions.  
   - Ensure proper resource definitions in the rollback spec.  
   - Use `kubectl rollout undo deployment <deployment-name>` for debugging.  

114. **A StatefulSet fails to scale up. How would you troubleshoot the issue?**  
   - Verify PVC bindings for new replicas.  
   - Check StatefulSet pod events for resource conflicts.  
   - Debug networking issues for headless Service communication.  

115. **A Job is not completing successfully. How would you debug the issue?**  
   - Inspect pod logs and events with `kubectl logs` and `kubectl describe`.  
   - Check for missing permissions or invalid configurations.  
   - Verify retries and backoff limits in the Job spec.  

116. **Pods are experiencing high latency when accessing a Persistent Volume. What steps would you take to debug this issue?**  
   - Check storage class performance and backend IOPS.  
   - Monitor disk usage and access patterns on the node.  
   - Test PVC performance independently.  

117. **An Init Container is failing to start. How would you diagnose and fix this issue?**  
   - Use `kubectl logs <pod-name> -c <init-container-name>` to check logs.  
   - Verify resource limits for the Init Container.  
   - Check for missing dependencies or incorrect commands.  

118. **A pod is unable to pull the required container image. What steps would you follow to debug this?**  
   - Verify image name and tag in the pod spec.  
   - Test pulling the image manually from the container runtime.  
   - Check imagePullSecrets for authentication issues.  

119. **A DaemonSet is not scheduling pods on certain nodes. How would you troubleshoot this?**  
   - Verify node labels and DaemonSet nodeSelector rules.  
   - Check node taints and tolerations.  
   - Inspect events for scheduling errors.  

---

### **Cluster and Node Troubleshooting (120–129)**  
120. **A node is marked NotReady. What steps would you follow to identify and fix the issue?**  
   - Use `kubectl describe node` to check conditions.  
   - Inspect kubelet logs (`journalctl -u kubelet`).  
   - Test network connectivity to the API server.  

121. **All worker nodes are unreachable by the control plane. How would you debug and fix the issue?**  
   - Verify control plane network connectivity.  
   - Check the kube-proxy and CNI plugin configurations.  
   - Ensure worker node certificates are valid.  

122. **The kubelet service is failing to start on a node. What logs and configuration files would you check?**  
   - Inspect logs with `journalctl -u kubelet`.  
   - Check kubelet configuration files (`/var/lib/kubelet/config.yaml`).  
   - Validate node certificate expiration.  

123. **A cluster upgrade fails halfway through. How would you proceed to troubleshoot and resolve the issue?**  
   - Inspect `kubeadm` upgrade logs.  
   - Check API server and etcd health.  
   - Manually upgrade components on affected nodes.  

124. **The etcd cluster is reporting quorum not achieved. How would you diagnose and fix this issue?**  
   - Verify etcd member connectivity using `etcdctl`.  
   - Check etcd logs for leader election issues.  
   - Restore etcd from a backup if necessary.  

125. **A node consistently experiences high CPU utilization. How would you identify and resolve the root cause?**  
   - Use `top` or `htop` to monitor processes.  
   - Check for noisy neighbor workloads.  
   - Scale workloads or adjust resource requests/limits.  

126. **Kubernetes reports NodeUnderDiskPressure for a worker node. How would you troubleshoot and fix this?**  
   - Identify large directories using `du -sh`.  
   - Check log rotation and clean up old logs.  
   - Resize disk or reduce pod resource usage.  

127. **A node is unable to register with the API server. What could be the issue, and how would you address it?**  
   - Verify kubelet configuration and certificates.  
   - Check network connectivity to the API server.  
   - Inspect kubelet logs for registration errors.  

128. **A kubectl drain operation fails on a node. How would you identify the cause?**  
   - Use `kubectl describe node` for detailed events.  
   - Check for DaemonSets or pods without proper tolerations.  
   - Force eviction if safe using `kubectl drain --force`.  

129. **A node is unable to mount a Persistent Volume. What troubleshooting steps would you take?**  
   - Check the PV and PVC status using `kubectl describe`.  
   - Verify storage plugin logs on the node.  
   - Test the underlying storage connectivity.  

### **Networking Troubleshooting (130–139)**  

130. **A NetworkPolicy is incorrectly blocking traffic to an application. How would you identify and fix this?**  
   - Use `kubectl describe networkpolicy` to review the applied policies.  
   - Test connectivity using tools like `curl`, `ping`, or `netcat` from other pods.  
   - Check the pod labels to ensure they match the policy selectors.  
   - Adjust the NetworkPolicy rules to allow required traffic.            

131. **An Ingress is not routing traffic to the backend service. How would you debug this?**  
   - Validate Ingress rules with `kubectl describe ingress`.  
   - Check if the Ingress Controller is running and properly configured.  
   - Verify the Service's endpoints with `kubectl describe service`.  
   - Ensure DNS resolves correctly and troubleshoot with tools like `curl` or `wget`.  

132. **Pods are unable to communicate across namespaces despite proper services being in place. How would you approach this issue?**  
   - Check for restrictive NetworkPolicies in either namespace.  
   - Confirm Service discovery is functioning (e.g., DNS resolution of service names).  
   - Verify that the CNI plugin is correctly handling cross-namespace traffic.  

133. **Traffic is being dropped between pods due to a misconfigured CNI plugin. How would you debug and fix this?**  
   - Inspect CNI plugin logs and configurations (e.g., `flannel`, `calico`, `weave`).  
   - Verify CNI plugin installation and check for errors in the control plane logs.  
   - Reapply or reinitialize the CNI configuration if necessary.  

134. **A pod is unable to connect to an external database. What steps would you take to debug the issue?**  
   - Test connectivity using `curl` or `nc` from within the pod.  
   - Check if the external database allows connections from the cluster IP range.  
   - Inspect NetworkPolicies and firewalls for restrictions.  
   - Verify correct database credentials and connection strings.  

135. **An external application cannot connect to a Kubernetes LoadBalancer service. What troubleshooting steps would you follow?**  
   - Confirm LoadBalancer creation with `kubectl describe service`.  
   - Verify the cloud provider's LoadBalancer status (e.g., AWS, GCP, Azure).  
   - Check firewall rules to allow traffic on the required ports.  
   - Inspect pod readiness and ensure endpoints are available.  

136. **Pods are unable to resolve external DNS names. How would you troubleshoot and resolve this issue?**  
   - Verify the CoreDNS pod status with `kubectl get pods -n kube-system`.  
   - Check CoreDNS logs (`kubectl logs -n kube-system <coredns-pod-name>`).  
   - Test DNS resolution from within the pod using `nslookup` or `dig`.  
   - Ensure the `resolv.conf` file in the pod is correctly configured.  

137. **A pod reports connection timeout errors when connecting to another pod. How would you identify the issue?**  
   - Validate the target pod's readiness and IP using `kubectl describe pod`.  
   - Check Service endpoints and DNS resolution.  
   - Test connectivity with `ping` or `curl` from the source pod.  
   - Inspect NetworkPolicy or firewall rules blocking traffic.  

138. **A hostNetwork: true pod is not reachable on its specified IP. What steps would you take to debug this?**  
   - Verify the pod's host network IP with `kubectl describe pod`.  
   - Check for conflicting ports on the host node.  
   - Ensure firewalls allow traffic to the host network.  

139. **A service's endpoints are empty. What could be causing this issue, and how would you resolve it?**  
   - Use `kubectl describe service` to confirm the selector matches pod labels.  
   - Verify that the backend pods are in `Running` and `Ready` states.  
   - Check for missing readiness probes in the pod spec.  

---

### **Storage Troubleshooting (140–149)**  

140. **A Persistent Volume is stuck in Released state. How would you debug and resolve the issue?**  
   - Check if the PV is still bound to a deleted PVC.  
   - Delete and recreate the PV if no data persistence is required.  
   - Use the `reclaimPolicy` to retain or recycle data.  

141. **A pod using a hostPath volume is unable to access the specified directory. How would you troubleshoot this?**  
   - Verify the directory exists on the host node.  
   - Check file permissions for the directory.  
   - Inspect pod events for mount errors.  

142. **A Persistent Volume Claim is stuck in Pending state. What steps would you take to resolve this?**  
   - Check if a suitable Persistent Volume exists with matching specs.  
   - Verify the PVC and StorageClass configuration.  
   - Ensure the dynamic provisioning controller is working for the StorageClass.  

143. **Data corruption occurs on a volume used by multiple pods. How would you identify and fix this issue?**  
   - Ensure the volume supports multi-node access (e.g., ReadWriteMany).  
   - Verify application-level synchronization or locking mechanisms.  
   - Inspect the backend storage system for issues.  

144. **A pod fails to mount a PVC due to insufficient permissions. How would you debug and resolve the issue?**  
   - Check pod events for detailed error messages.  
   - Inspect the underlying storage permissions.  
   - Verify the Kubernetes service account permissions.  

145. **A StatefulSet is not able to attach its required Persistent Volumes. How would you troubleshoot this?**  
   - Check if the required PVCs are bound and available.  
   - Verify node affinity rules for the StatefulSet.  
   - Inspect pod events for mount or scheduling errors.  

146. **A node consistently fails to bind dynamic Persistent Volumes. What diagnostic steps would you take?**  
   - Check the storage provisioner logs.  
   - Verify the StorageClass configuration.  
   - Ensure the node has sufficient storage capacity.  

147. **Data stored on a volume is not persisting after pod restarts. What steps would you follow to debug this?**  
   - Check if the volume type supports persistence (e.g., hostPath is not persistent).  
   - Verify PVC binding and pod volume mounts.  
   - Inspect backend storage for data retention policies.  

148. **A PVC bound to an NFS-based Persistent Volume is experiencing high latency. How would you troubleshoot this?**  
   - Check NFS server logs and health.  
   - Test NFS network performance using tools like `iperf`.  
   - Monitor node and network resource utilization.  

149. **A volume snapshot is failing to be created. How would you debug this issue?**  
   - Verify VolumeSnapshot and VolumeSnapshotClass configurations.  
   - Check the CSI driver logs for errors.  
   - Ensure the backend storage supports snapshots.  

---

### **Control Plane and Component Issues (150)**  

150. **The kube-apiserver is responding slowly to requests. How would you identify the root cause?**  
   - Monitor API server metrics using `kubectl top` or Prometheus.  
   - Check control plane logs for errors or throttling messages.  
   - Validate etcd health and performance.  
   - Review network latency between nodes and the control plane.  

Here are detailed **answers for questions 151–200**, with diagnostic commands and solutions where applicable. The answers include a mix of practical steps, theoretical understanding, and troubleshooting insights.

---

### **Control Plane and Component Issues (151–159)**

151. **The kube-scheduler is failing to schedule pods. What steps would you follow to debug this?**
   - **Commands to check:**
     - `kubectl describe pod <pod-name>` to view scheduling events and errors.
     - `kubectl get nodes` to ensure sufficient resources are available.
   - **Fix:** Check for taints, tolerations, and resource requests that might prevent scheduling. Review the kube-scheduler logs (`journalctl -u kube-scheduler`).

152. **The kube-controller-manager is not reconciling objects. How would you diagnose the issue?**
   - **Commands to check:**
     - Inspect the logs: `journalctl -u kube-controller-manager`.
     - Check API server health: `kubectl get componentstatuses`.
   - **Fix:** Ensure the controller-manager has connectivity to the API server and sufficient resources.

153. **etcd is consuming excessive memory. How would you troubleshoot and optimize its performance?**
   - **Commands to check:**
     - `etcdctl endpoint status` to check health and resource usage.
     - `etcdctl defrag` to free space if data fragmentation is high.
   - **Fix:** Reduce key churn, increase etcd memory, or scale the etcd cluster.

154. **A control plane node runs out of disk space. How would you identify and resolve the issue?**
   - **Commands to check:**
     - `df -h` to view disk usage.
     - Check etcd data directory: `/var/lib/etcd`.
   - **Fix:** Clean up old logs, defrag etcd, and resize the disk if necessary.

155. **A pod cannot communicate with the kube-apiserver. What steps would you take to debug this?**
   - **Commands to check:**
     - Verify pod network connectivity: `ping <apiserver-ip>`.
     - Inspect kube-proxy logs for potential issues.
   - **Fix:** Check API server IP in kubelet configuration and network routing.

156. **The Kubernetes dashboard is inaccessible. What are the possible causes, and how would you fix them?**
   - **Commands to check:**
     - `kubectl get svc -n kubernetes-dashboard` to verify the service type and endpoint.
     - Check the dashboard pod logs: `kubectl logs <dashboard-pod> -n kubernetes-dashboard`.
   - **Fix:** Correct RBAC roles or expose the service using a NodePort or Ingress.

157. **Cluster autoscaler is not scaling nodes as expected. How would you debug and resolve this issue?**
   - **Commands to check:**
     - Inspect autoscaler logs: `kubectl logs -n kube-system <autoscaler-pod>`.
     - Review pending pods with `kubectl get pods --field-selector=status.phase=Pending`.
   - **Fix:** Ensure appropriate scaling policies and sufficient quotas with the cloud provider.

158. **A control plane component is frequently restarting. How would you troubleshoot this issue?**
   - **Commands to check:**
     - `kubectl get events -n kube-system` for relevant messages.
     - Inspect logs (`journalctl -u <component-name>`).
   - **Fix:** Check for resource exhaustion or misconfiguration in systemd or component flags.

159. **The kube-proxy service is not functioning on a node. How would you debug this?**
   - **Commands to check:**
     - Inspect kube-proxy logs: `journalctl -u kube-proxy`.
     - Test connectivity to the cluster IP using `curl`.
   - **Fix:** Verify the CNI plugin, iptables rules, and kube-proxy configuration.

---

### **Monitoring and Observability (160–169)**

160. **Prometheus is not collecting metrics from Kubernetes nodes. How would you troubleshoot this issue?**
   - **Commands to check:**
     - Verify Prometheus targets: `kubectl exec <prometheus-pod> -- curl <target-url>`.
     - Check service discovery configuration in Prometheus.
   - **Fix:** Ensure node exporters are running and scrape configurations are correct.

161. **Grafana dashboards show gaps in metrics data. What steps would you take to debug this?**
   - **Commands to check:**
     - Inspect Prometheus retention and storage configuration.
     - Review Grafana datasource configuration.
   - **Fix:** Allocate more resources for Prometheus or adjust retention settings.

162. **A pod's resource usage spikes unexpectedly. How would you use monitoring tools to identify the root cause?**
   - **Tools:** Use Prometheus and Grafana to review CPU/memory graphs.
   - Check logs of the application for spikes caused by load or memory leaks.

163. **Logs from a specific namespace are missing in your centralized logging system. How would you debug this?**
   - **Commands to check:**
     - Verify Fluentd configuration for the namespace.
     - Inspect Fluentd or Logstash logs for errors.
   - **Fix:** Update logging filters to include the namespace.

164. **Monitoring tools report high API server request latencies. What could be causing this issue?**
   - **Commands to check:**
     - Review API server metrics and logs.
     - Inspect etcd health and network latency.
   - **Fix:** Scale the API server or reduce request volume.

165. **A custom monitoring exporter is not scraping metrics correctly. How would you debug this issue?**
   - **Commands to check:**
     - Test the exporter endpoint: `curl <exporter-url>/metrics`.
     - Review Prometheus scrape configurations.
   - **Fix:** Correct exporter implementation or adjust scrape intervals.

166. **Logs for a specific pod show high volumes of error messages. How would you analyze and address this?**
   - **Commands to check:**
     - Inspect logs: `kubectl logs <pod-name>`.
     - Use logging queries to filter and identify the root cause.
   - **Fix:** Fix the application logic or adjust retries if errors are transient.

167. **Metrics indicate a memory leak in an application. How would you approach debugging this?**
   - **Steps:** Use profiling tools like `pprof` or `heapster` to identify leaks.
   - Fix code to release unused memory.

168. **A pod is using significantly more CPU than allocated. How would you identify the source of the problem?**
   - **Tools:** Use `kubectl top pod` and application-level profiling.
   - Fix by optimizing application code or increasing resource limits.

169. **Alerts from your monitoring system indicate a node is about to run out of resources. How would you prevent downtime?**
   - **Commands to check:**
     - Monitor resource usage: `kubectl describe node`.
     - Drain non-critical pods: `kubectl drain <node-name>`.
   - **Fix:** Scale nodes or optimize resource requests.

---

### **Advanced Troubleshooting Scenarios (170–179)**

170. **The control plane is completely unresponsive. What steps would you take to recover the cluster?**
   - **Steps:** Restore etcd from backup, restart control plane components, and verify API server health.

171. **A cluster backup has failed to restore correctly. How would you debug and fix the restoration process?**
   - **Commands to check:**
     - Verify backup integrity and compatibility with the restore process.
   - **Fix:** Follow vendor-specific restore steps or retry with a validated backup.

---

Here are the answers for **questions 172–179** with detailed steps and possible commands for debugging:

---

172. **A Job is creating too many pods, causing resource contention in the cluster. How would you address this issue?**  
   - **Commands to check:**
     - Review the Job spec:  
       ```bash
       kubectl describe job <job-name>
       ```
     - List pods created by the Job:  
       ```bash
       kubectl get pods --selector=job-name=<job-name>
       ```
   - **Fix:**  
     - Limit `parallelism` in the Job spec to control the number of concurrent pods:  
       ```yaml
       spec:
         parallelism: 3
       ```
     - Ensure proper backoff policy to reduce rapid retries:  
       ```yaml
       backoffLimit: 4
       ```

---

173. **A cluster experiences intermittent network partitions. How would you debug and resolve this issue?**  
   - **Commands to check:**
     - Check node connectivity:  
       ```bash
       kubectl get nodes -o wide
       ```
     - Inspect CNI logs:  
       ```bash
       journalctl -u kubelet
       ```
     - Validate network routes:  
       ```bash
       ip route
       ```
   - **Fix:**  
     - Investigate underlying network hardware or cloud network configurations.  
     - Restart the affected CNI plugin and nodes.  
     - Use `traceroute` to pinpoint network hops causing the issue.

---

174. **An etcd cluster is split-brained. How would you recover and stabilize it?**  
   - **Commands to check:**
     - Check etcd member status:  
       ```bash
       etcdctl member list
       ```
     - Inspect logs for split-brain conditions:  
       ```bash
       journalctl -u etcd
       ```
   - **Fix:**  
     - Remove faulty members using `etcdctl member remove <member-id>`.  
     - Reconfigure etcd to achieve quorum and avoid split-brain:  
       ```bash
       etcdctl member add <new-member> --peer-urls <peer-url>
       ```

---

175. **Autoscaling is causing application instability due to scaling up too quickly. How would you fix this issue?**  
   - **Commands to check:**
     - Inspect HPA or cluster autoscaler logs:  
       ```bash
       kubectl describe hpa <hpa-name>
       ```
     - Monitor metric values causing rapid scaling:  
       ```bash
       kubectl top pod
       ```
   - **Fix:**  
     - Adjust stabilization settings in HPA to prevent rapid scaling:  
       ```yaml
       spec:
         behavior:
           scaleUp:
             stabilizationWindowSeconds: 60
             policies:
               - type: Percent
                 value: 50
                 periodSeconds: 60
       ```
     - Use buffer resources to accommodate sudden spikes without scaling immediately.

---

176. **A complex multi-tier application deployment fails. How would you systematically debug and resolve the issue?**  
   - **Steps:**
     1. Debug tier-by-tier, starting with the first layer (e.g., database, backend, then frontend).  
     2. Check pod logs:  
        ```bash
        kubectl logs <pod-name>
        ```
     3. Validate service connectivity:  
        ```bash
        kubectl exec <pod-name> -- curl <service-url>
        ```
   - **Fix:**  
     - Fix issues at each tier (e.g., misconfigured services, environment variables).  
     - Use `kubectl port-forward` for testing internal service communication.

---

177. **Your cluster is under a heavy DDoS attack. How would you mitigate and secure the cluster?**  
   - **Steps:**
     - Identify attacking IPs using cloud provider’s monitoring tools or Kubernetes logs.  
     - Use NetworkPolicies to block malicious traffic:  
       ```yaml
       apiVersion: networking.k8s.io/v1
       kind: NetworkPolicy
       metadata:
         name: deny-malicious
       spec:
         podSelector: {}
         ingress:
           - from:
               - ipBlock:
                   cidr: <attacking-ip>/32
       ```
     - Scale up resources temporarily to absorb the attack.  
   - **Fix:**  
     - Enable DDoS protection (e.g., Google Cloud Armor, AWS Shield).  
     - Implement rate-limiting at the ingress level.

---

178. **A namespace deletion operation is stuck. What could cause this issue, and how would you resolve it?**  
   - **Commands to check:**
     - View namespace status:  
       ```bash
       kubectl get namespace <namespace> -o yaml
       ```
     - Identify stuck finalizers:  
       ```bash
       kubectl get namespace <namespace> -o jsonpath='{.spec.finalizers}'
       ```
   - **Fix:**  
     - Remove the finalizers causing the delay:  
       ```bash
       kubectl patch namespace <namespace> -p '{"spec":{"finalizers":[]}}'
       ```

---

179. **Persistent Volumes are not being cleaned up after namespace deletion. How would you debug this issue?**  
   - **Commands to check:**
     - Verify PV reclaim policy:  
       ```bash
       kubectl get pv
       ```
     - Inspect PVC references to the namespace:  
       ```bash
       kubectl describe pvc <pvc-name>
       ```
   - **Fix:**  
     - Update the PV reclaim policy to `Delete` for automatic cleanup:  
       ```yaml
       apiVersion: v1
       kind: PersistentVolume
       spec:
         persistentVolumeReclaimPolicy: Delete
       ```
     - Manually delete orphaned PVs:  
       ```bash
       kubectl delete pv <pv-name>
       ```

---

### **General Use Case Scenarios (180–189)**

180. **How would you debug a pod that is stuck in the Terminating state?**  
   - **Commands to check:**
     - `kubectl get pod <pod-name> -o yaml` to check for finalizers.
     - `kubectl describe pod <pod-name>` to view pending events.
   - **Fix:**
     - Remove stuck finalizers:  
       ```bash
       kubectl patch pod <pod-name> -p '{"metadata":{"finalizers":[]}}'
       ```
     - Investigate stuck processes (e.g., CSI volume detach issues).

181. **A cluster-wide ConfigMap update breaks multiple applications. How would you identify and roll back the changes?**  
   - **Commands to check:**
     - Inspect ConfigMap history:  
       ```bash
       kubectl get cm <config-name> -o yaml
       ```
     - Review application logs for errors.
   - **Fix:**
     - Restore a previous ConfigMap version:  
       ```bash
       kubectl apply -f <previous-config.yaml>
       ```

182. **A RollingUpdate strategy deployment is causing downtime. How would you debug and fix the issue?**  
   - **Commands to check:**
     - Monitor rollout status:  
       ```bash
       kubectl rollout status deployment/<deployment-name>
       ```
     - Inspect pod readiness: `kubectl describe pod`.
   - **Fix:**
     - Pause the rollout and fix the application:  
       ```bash
       kubectl rollout pause deployment/<deployment-name>
       ```

183. **How would you troubleshoot a failed `kubectl apply` operation?**  
   - **Commands to check:**
     - Check YAML for errors using `kubectl apply --dry-run=client -f <file>.yaml`.
     - Review API server logs.
   - **Fix:**
     - Correct invalid fields or syntax errors in the YAML.

184. **A pod is failing due to missing environment variables. How would you debug this?**  
   - **Commands to check:**
     - Inspect pod environment variables:  
       ```bash
       kubectl describe pod <pod-name>
       ```
     - Verify ConfigMap or Secret references.
   - **Fix:** Update the pod spec or the ConfigMap/Secret.

185. **A custom CNI plugin is not initializing correctly. How would you debug and resolve this issue?**  
   - **Commands to check:**
     - Review CNI logs: `journalctl -u kubelet`.
     - Inspect plugin configuration files in `/etc/cni/net.d/`.
   - **Fix:**
     - Correct the plugin’s configuration and ensure compatibility with the Kubernetes version.

186. **A pod's resource requests and limits are misconfigured, causing performance issues. How would you fix this?**  
   - **Commands to check:**
     - View pod resource usage:  
       ```bash
       kubectl top pod <pod-name>
       ```
   - **Fix:**
     - Adjust requests/limits in the pod spec to reflect actual usage:  
       ```yaml
       resources:
         requests:
           cpu: "500m"
           memory: "256Mi"
         limits:
           cpu: "1"
           memory: "512Mi"
       ```

187. **A StatefulSet fails to retain its persistent storage after a cluster upgrade. How would you address this issue?**  
   - **Commands to check:**
     - Inspect PersistentVolumeClaims (PVCs):  
       ```bash
       kubectl get pvc
       ```
   - **Fix:**
     - Verify storage class configurations and reattach volumes to StatefulSet pods.

188. **An application is not scaling as expected with Horizontal Pod Autoscaler. What steps would you take to debug this?**  
   - **Commands to check:**
     - Inspect HPA configuration:  
       ```bash
       kubectl describe hpa <hpa-name>
       ```
     - Verify metrics availability in `kubectl top pod`.
   - **Fix:** Correct HPA thresholds or ensure metric-server is functional.

189. **A pod's liveness probe causes frequent restarts. How would you debug and optimize it?**  
   - **Commands to check:**
     - Review probe configuration in YAML.
     - Inspect probe logs:  
       ```bash
       kubectl logs <pod-name>
       ```
   - **Fix:** Increase probe timeout or adjust the command/script for robustness.

---

### **Extending Kubernetes Troubleshooting (190–200)**

190. **How would you debug a custom resource that fails to reconcile in a custom operator?**  
   - **Commands to check:**
     - Inspect the controller logs:  
       ```bash
       kubectl logs <operator-pod>
       ```
   - **Fix:** Debug the reconcile function in the operator code and reapply the CRD.

191. **A Helm chart installation fails. What steps would you take to debug this?**  
   - **Commands to check:**
     - Dry run the installation:  
       ```bash
       helm install --dry-run --debug <release-name> <chart>
       ```
     - Inspect Kubernetes events.  
   - **Fix:** Resolve values.yaml errors or chart misconfigurations.

192. **A pod using a projected volume fails to start. How would you debug this issue?**  
   - **Commands to check:**
     - Inspect volume configuration in the pod spec.
   - **Fix:** Verify permissions or volume type compatibility.

193. **A cluster upgrade breaks a custom admission controller. How would you debug and resolve this issue?**  
   - **Commands to check:**
     - Review admission controller logs.
     - Test API server webhook communication.  
   - **Fix:** Update the controller to be compatible with the new Kubernetes version.

194. **A service mesh is causing connectivity issues between pods. How would you identify and fix the root cause?**  
   - **Commands to check:**
     - Verify Envoy/sidecar logs.
     - Inspect service mesh configuration for misapplied policies.  
   - **Fix:** Adjust policies or restart mesh components.

195. **A container runtime upgrade fails. What steps would you take to troubleshoot this issue?**  
   - **Commands to check:**
     - Inspect runtime logs (e.g., `containerd` or `dockerd`).
     - Verify configuration files in `/etc/docker/` or `/etc/containerd/`.  
   - **Fix:** Roll back or reinstall the runtime properly.

196. **A pod's readiness probe depends on a remote service that is unavailable. How would you handle this dependency?**  
   - **Commands to check:**
     - Ping the remote service from the pod:  
       ```bash
       kubectl exec <pod-name> -- curl <remote-service-url>
       ```
   - **Fix:** Adjust readiness probe retries or implement fallback logic.

197. **A custom scheduler fails to assign pods to nodes. How would you debug this?**  
   - **Commands to check:**
     - Inspect custom scheduler logs.
     - Check pod events for scheduling errors.  
   - **Fix:** Debug the custom scheduler code or correct pod affinity rules.

198. **A Kubernetes webhook configuration is misbehaving. How would you identify and fix the issue?**  

   - **Commands to check:**
     - Inspect webhook logs and API server logs.
     - Validate webhook certificates and endpoints.  
   - **Fix:** Update the webhook configuration and retry.

199. **A pod using CSI storage is failing to mount the volume. How would you debug this issue?**  

   - **Commands to check:**
     - Inspect CSI driver logs:  
       ```bash
       kubectl logs <csi-driver-pod>
       ```
     - Check pod events for mount errors.  
   - **Fix:** Reapply CSI configurations or debug driver compatibility.

200. **How would you debug a cluster-wide performance degradation issue?**  
   - **Steps:**
     - Check for high resource usage across nodes: `kubectl top node`.
     - Inspect etcd and API server latencies.  
   - **Fix:** Scale the cluster, resolve bottlenecks, or optimize workloads.

---

Good luck!
