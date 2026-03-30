# kubectl Command Reference

## Quick Reference for Common kubectl Commands

This guide provides practical kubectl commands with explanations to help you work effectively with Kubernetes.

---

## Table of Contents

- [Cluster Information](#cluster-information)
- [Nodes](#nodes)
- [Pods](#pods)
- [Deployments](#deployments)
- [Services](#services)
- [ConfigMaps & Secrets](#configmaps--secrets)
- [Logs & Debugging](#logs--debugging)
- [Resource Management](#resource-management)
- [Namespaces](#namespaces)
- [Common Flags Explained](#common-flags-explained)

---

## Cluster Information

```bash
# Get cluster information
kubectl cluster-info

# Get cluster dump for diagnostics
kubectl cluster-info dump

# Get cluster dump for specific namespace
kubectl cluster-info dump -n <namespace>

# Check cluster component health
kubectl get componentstatuses
# Note: Deprecated in v1.19+, use component-specific health endpoints instead
```

---

## Nodes

```bash
# List all nodes
kubectl get nodes

# List nodes with additional details (IP, OS, etc.)
kubectl get nodes -o wide

# Describe a specific node (detailed information)
kubectl describe node <node-name>

# Check node resource usage (requires metrics-server)
kubectl top nodes

# Cordon a node (mark as unschedulable)
kubectl cordon <node-name>

# Uncordon a node (mark as schedulable)
kubectl uncordon <node-name>

# Drain a node (safely evict pods before maintenance)
kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data

# Label a node
kubectl label nodes <node-name> <label-key>=<label-value>

# Remove a label from a node
kubectl label nodes <node-name> <label-key>-
```

---

## Pods

### Listing Pods

```bash
# List pods in current namespace
kubectl get pods

# List pods in all namespaces
kubectl get pods -A
# -A is shorthand for --all-namespaces

# List pods in specific namespace
kubectl get pods -n <namespace>

# List pods with additional details
kubectl get pods -o wide

# List pods with labels
kubectl get pods --show-labels

# List pods by label selector
kubectl get pods -l app=myapp

# List pods sorted by creation time
kubectl get pods --sort-by=.metadata.creationTimestamp

# Get pods in specific phase
kubectl get pods --field-selector=status.phase=Running
kubectl get pods --field-selector=status.phase=Failed
```

### Pod Details

```bash
# Describe a pod (detailed info, events, status)
kubectl describe pod <pod-name>

# Describe pod in specific namespace
kubectl describe pod <pod-name> -n <namespace>

# Get pod YAML definition
kubectl get pod <pod-name> -o yaml

# Get pod JSON definition
kubectl get pod <pod-name> -o json

# Get specific field using jsonpath
kubectl get pod <pod-name> -o jsonpath='{.status.podIP}'

# Watch pod status in real-time
kubectl get pods -w
# -w means --watch, updates in real-time
```

### Creating & Deleting Pods

```bash
# Create a pod from YAML file
kubectl apply -f pod.yaml

# Create a simple pod imperatively
kubectl run nginx --image=nginx

# Create a pod with specific command
kubectl run busybox --image=busybox --command -- sleep 3600

# Delete a pod
kubectl delete pod <pod-name>

# Delete a pod forcefully (immediate, no graceful shutdown)
kubectl delete pod <pod-name> --force --grace-period=0

# Delete all pods in a namespace
kubectl delete pods --all -n <namespace>

# Delete pods by label
kubectl delete pods -l app=myapp
```

### Pod Resource Usage

```bash
# Get pod resource usage (requires metrics-server)
kubectl top pods

# Get pod resource usage in specific namespace
kubectl top pods -n <namespace>

# Get pod resource usage sorted by CPU
kubectl top pods --sort-by=cpu

# Get pod resource usage sorted by memory
kubectl top pods --sort-by=memory
```

---

## Deployments

### Listing & Viewing

```bash
# List deployments
kubectl get deployments

# List deployments with replicas info
kubectl get deployments -o wide

# Describe a deployment
kubectl describe deployment <deployment-name>

# Get deployment YAML
kubectl get deployment <deployment-name> -o yaml
```

### Creating & Updating

```bash
# Create deployment from YAML
kubectl apply -f deployment.yaml

# Create deployment imperatively
kubectl create deployment nginx --image=nginx --replicas=3

# Update deployment image
kubectl set image deployment/<deployment-name> <container-name>=<new-image>

# Edit deployment in editor
kubectl edit deployment <deployment-name>

# Scale deployment
kubectl scale deployment <deployment-name> --replicas=5

# Autoscale deployment (HPA)
kubectl autoscale deployment <deployment-name> --min=2 --max=10 --cpu-percent=80
```

### Rollouts

```bash
# Check rollout status
kubectl rollout status deployment/<deployment-name>

# View rollout history
kubectl rollout history deployment/<deployment-name>

# View specific revision
kubectl rollout history deployment/<deployment-name> --revision=2

# Undo rollout (rollback to previous revision)
kubectl rollout undo deployment/<deployment-name>

# Rollback to specific revision
kubectl rollout undo deployment/<deployment-name> --to-revision=2

# Pause rollout
kubectl rollout pause deployment/<deployment-name>

# Resume rollout
kubectl rollout resume deployment/<deployment-name>

# Restart deployment (rolling restart)
kubectl rollout restart deployment/<deployment-name>
```

---

## Services

```bash
# List services
kubectl get services
kubectl get svc  # shorthand

# Describe a service
kubectl describe service <service-name>

# Create a service from YAML
kubectl apply -f service.yaml

# Expose a deployment as a service
kubectl expose deployment <deployment-name> --port=80 --type=LoadBalancer

# Expose a deployment with NodePort
kubectl expose deployment <deployment-name> --port=80 --type=NodePort

# Expose a deployment with ClusterIP
kubectl expose deployment <deployment-name> --port=80 --type=ClusterIP

# Get service endpoints
kubectl get endpoints <service-name>

# Delete a service
kubectl delete service <service-name>
```

---

## ConfigMaps & Secrets

### ConfigMaps

```bash
# Create ConfigMap from literal values
kubectl create configmap <name> --from-literal=key1=value1 --from-literal=key2=value2

# Create ConfigMap from file
kubectl create configmap <name> --from-file=<path-to-file>

# Create ConfigMap from directory
kubectl create configmap <name> --from-file=<path-to-directory>/

# List ConfigMaps
kubectl get configmaps
kubectl get cm  # shorthand

# Describe ConfigMap
kubectl describe configmap <name>

# Get ConfigMap data
kubectl get configmap <name> -o yaml

# Delete ConfigMap
kubectl delete configmap <name>
```

### Secrets

```bash
# Create secret from literal values
kubectl create secret generic <name> --from-literal=key1=value1

# Create secret from file
kubectl create secret generic <name> --from-file=<path-to-file>

# Create TLS secret
kubectl create secret tls <name> --cert=<path-to-cert> --key=<path-to-key>

# Create Docker registry secret
kubectl create secret docker-registry <name> \
  --docker-server=<server> \
  --docker-username=<username> \
  --docker-password=<password> \
  --docker-email=<email>

# List secrets
kubectl get secrets

# Describe secret (doesn't show values)
kubectl describe secret <name>

# Get secret data (base64 encoded)
kubectl get secret <name> -o yaml

# Decode a secret value
kubectl get secret <name> -o jsonpath='{.data.key1}' | base64 --decode

# Delete secret
kubectl delete secret <name>
```

---

## Logs & Debugging

### Logs

```bash
# View pod logs
kubectl logs <pod-name>

# View logs for specific container in pod
kubectl logs <pod-name> -c <container-name>

# Follow logs in real-time (like tail -f)
kubectl logs -f <pod-name>
# -f means --follow

# View previous container logs (after restart)
kubectl logs <pod-name> --previous

# View last N lines of logs
kubectl logs <pod-name> --tail=100

# View logs since specific time
kubectl logs <pod-name> --since=1h
kubectl logs <pod-name> --since=2024-01-01T10:00:00Z

# View logs for all pods with a label
kubectl logs -l app=myapp --all-containers=true

# View logs from all containers in a pod
kubectl logs <pod-name> --all-containers=true
```

### Exec & Port-Forward

```bash
# Execute command in pod
kubectl exec <pod-name> -- <command>

# Execute command in specific container
kubectl exec <pod-name> -c <container-name> -- <command>

# Get interactive shell in pod
kubectl exec -it <pod-name> -- /bin/bash
# -i means --stdin (keep stdin open)
# -t means --tty (allocate a terminal)

# Get shell in specific container
kubectl exec -it <pod-name> -c <container-name> -- /bin/sh

# Port-forward to pod
kubectl port-forward pod/<pod-name> 8080:80

# Port-forward to service
kubectl port-forward service/<service-name> 8080:80

# Port-forward to deployment
kubectl port-forward deployment/<deployment-name> 8080:80
```

### Debugging

```bash
# Describe resource (shows events)
kubectl describe <resource-type> <resource-name>

# Get events in current namespace
kubectl get events

# Get events sorted by time
kubectl get events --sort-by='.lastTimestamp'

# Get events for specific pod
kubectl get events --field-selector involvedObject.name=<pod-name>

# Check resource definitions
kubectl explain pod
kubectl explain pod.spec
kubectl explain deployment.spec.template

# Dry-run to validate YAML without creating
kubectl apply -f <file.yaml> --dry-run=client
kubectl apply -f <file.yaml> --dry-run=server

# Validate resource creation
kubectl create --dry-run=client -o yaml -f <file.yaml>
```

---

## Resource Management

### Applying & Deleting

```bash
# Apply a configuration file
kubectl apply -f <file.yaml>

# Apply all YAML files in a directory
kubectl apply -f <directory>/

# Apply from URL
kubectl apply -f https://example.com/manifest.yaml

# Delete resources from file
kubectl delete -f <file.yaml>

# Delete all resources in a namespace
kubectl delete all --all -n <namespace>

# Delete resource by name
kubectl delete <resource-type> <resource-name>

# Delete resources by label
kubectl delete <resource-type> -l app=myapp
```

### Editing

```bash
# Edit resource in default editor
kubectl edit <resource-type> <resource-name>

# Edit with specific editor
KUBE_EDITOR="nano" kubectl edit <resource-type> <resource-name>

# Patch a resource (JSON patch)
kubectl patch <resource-type> <resource-name> -p '{"spec":{"replicas":3}}'

# Patch a resource (merge patch)
kubectl patch <resource-type> <resource-name> --type=merge -p '{"spec":{"replicas":3}}'
```

### Labels & Annotations

```bash
# Add label to resource
kubectl label <resource-type> <resource-name> env=production

# Update existing label (requires --overwrite)
kubectl label <resource-type> <resource-name> env=staging --overwrite

# Remove label
kubectl label <resource-type> <resource-name> env-

# Add annotation
kubectl annotate <resource-type> <resource-name> description="My resource"

# Remove annotation
kubectl annotate <resource-type> <resource-name> description-
```

---

## Namespaces

```bash
# List namespaces
kubectl get namespaces
kubectl get ns  # shorthand

# Create namespace
kubectl create namespace <namespace-name>

# Delete namespace
kubectl delete namespace <namespace-name>

# Set default namespace for current context
kubectl config set-context --current --namespace=<namespace-name>

# Get current namespace
kubectl config view --minify | grep namespace:

# Run command in specific namespace
kubectl get pods -n <namespace-name>
```

---

## Common Flags Explained

### Output Flags

```bash
-o wide          # Show additional information (Node IP, etc.)
-o yaml          # Output in YAML format
-o json          # Output in JSON format
-o jsonpath=     # Custom output using JSONPath
-o name          # Output resource names only
--show-labels    # Show labels
--no-headers     # Don't show column headers
```

### Selection Flags

```bash
-n <namespace>          # Specify namespace
-A, --all-namespaces    # Show resources across all namespaces
-l <label-selector>     # Filter by label (e.g., -l app=myapp)
--field-selector=       # Filter by field (e.g., --field-selector=status.phase=Running)
```

### Action Flags

```bash
--force                 # Force operation (dangerous!)
--grace-period=0        # Immediate termination (no graceful shutdown)
--dry-run=client        # Validate locally without server request
--dry-run=server        # Validate on server without creating
-w, --watch             # Watch for changes in real-time
-f, --follow            # Follow logs (like tail -f)
```

### Resource Flags

```bash
--replicas=N            # Set number of replicas
--image=<image>         # Specify container image
--port=<port>           # Specify port
--restart=Always        # Set restart policy (Always, OnFailure, Never)
--command               # Use command instead of entrypoint
```

---

## Context & Configuration

```bash
# View current context
kubectl config current-context

# List all contexts
kubectl config get-contexts

# Switch context
kubectl config use-context <context-name>

# Set default namespace for context
kubectl config set-context --current --namespace=<namespace>

# View kubeconfig
kubectl config view

# Set credentials
kubectl config set-credentials <user> --client-certificate=<cert> --client-key=<key>

# Set cluster
kubectl config set-cluster <cluster-name> --server=<server-url>

# Create context
kubectl config set-context <context-name> --cluster=<cluster> --user=<user> --namespace=<namespace>
```

---

## Advanced Usage

### JSONPath Examples

```bash
# Get pod IP
kubectl get pod <pod-name> -o jsonpath='{.status.podIP}'

# Get all pod names
kubectl get pods -o jsonpath='{.items[*].metadata.name}'

# Get pod and node names together
kubectl get pods -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.nodeName}{"\n"}{end}'

# Get container images
kubectl get pods -o jsonpath='{.items[*].spec.containers[*].image}'
```

### Sorting

```bash
# Sort pods by creation time
kubectl get pods --sort-by=.metadata.creationTimestamp

# Sort pods by name
kubectl get pods --sort-by=.metadata.name

# Sort nodes by CPU capacity
kubectl get nodes --sort-by=.status.capacity.cpu
```

### Resource Quotas

```bash
# List resource quotas
kubectl get resourcequota

# Describe resource quota
kubectl describe resourcequota <quota-name>

# List limit ranges
kubectl get limitrange

# Describe limit range
kubectl describe limitrange <limitrange-name>
```

---

## Quick Tips

1. **Use shortcuts**: `po` for pods, `svc` for services, `deploy` for deployments, `ns` for namespaces
   ```bash
   kubectl get po  # same as kubectl get pods
   ```

2. **Tab completion**: Enable kubectl autocomplete
   ```bash
   source <(kubectl completion bash)
   ```

3. **Alias for efficiency**:
   ```bash
   alias k=kubectl
   alias kg='kubectl get'
   alias kd='kubectl describe'
   alias kl='kubectl logs'
   ```

4. **Use `--help`**: Every command has help
   ```bash
   kubectl <command> --help
   ```

5. **Dry run before apply**: Always validate first
   ```bash
   kubectl apply -f manifest.yaml --dry-run=server
   ```

---

## Troubleshooting Checklist

When something goes wrong:

1. Check pod status: `kubectl get pods`
2. Describe pod: `kubectl describe pod <pod-name>`
3. Check logs: `kubectl logs <pod-name>`
4. Check events: `kubectl get events --sort-by='.lastTimestamp'`
5. Check resource limits: `kubectl top pods`
6. Check node status: `kubectl get nodes`
7. Check service endpoints: `kubectl get endpoints <service-name>`

---

## Additional Resources

- [Official kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)
- [kubectl Command Reference](https://kubernetes.io/docs/reference/generated/kubectl/kubectl-commands)
- [JSONPath Support](https://kubernetes.io/docs/reference/kubectl/jsonpath/)

---

**Last Updated**: March 2026 (Kubernetes v1.32)
