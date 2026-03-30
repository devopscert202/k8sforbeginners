# **Lab: Deploying a Multi-Port Service in Kubernetes**

This example demonstrates deploying a pod with multiple non-SSL ports and exposing them via a `NodePort` service. We'll configure the pod to serve on two ports: **8080 (HTTP)** and **9090 (Custom Port)**.

---

## **Objective**
- Deploy a pod exposing multiple non-SSL ports.
- Expose the pod using a `NodePort` service to make both ports accessible externally.

---

## **Prerequisites**
1. A functional Kubernetes cluster.
2. `kubectl` CLI installed and configured.

---

## **1. Creating a Pod with Multiple Ports**

### **YAML File for the Pod**
1. Create a file named `multi-port-pod.yaml`:
   ```bash
   nano multi-port-pod.yaml
   ```

2. Add the following content:
   ```yaml
   apiVersion: v1
   kind: Pod
   metadata:
     name: multi-port-pod
     labels:
       app: multi-port-app
   spec:
     containers:
     - name: multi-port-container
       image: hashicorp/http-echo
       args:
       - "-text=Hello, Multi-Port Service!"
       ports:
       - containerPort: 8080
         name: http
       - containerPort: 9090
         name: custom
   ```

### **Explanation of Fields**
- **`apiVersion`**: Kubernetes API version for Pod objects.
- **`kind`**: Defines this object as a `Pod`.
- **`metadata`**: Contains metadata about the pod:
  - **`name`**: The name of the pod (`multi-port-pod`).
  - **`labels`**: Key-value pairs for identifying the pod (`app=multi-port-app`).
- **`spec`**: Defines the pod specification:
  - **`containers`**: List of containers inside the pod.
  - **`image`**: Docker image to use (`hashicorp/http-echo`).
  - **`args`**: Command-line arguments to serve custom text.
  - **`ports`**: Ports exposed by the container:
    - `containerPort: 8080`: For HTTP traffic.
    - `containerPort: 9090`: For custom traffic.

3. Apply the YAML file to create the pod:
   ```bash
   kubectl apply -f multi-port-pod.yaml
   ```

4. Verify the pod is running:
   ```bash
   kubectl get pods
   ```

---

## **2. Creating a Multi-Port Service**

### **YAML File for the Service**
1. Create a file named `multi-port-service.yaml`:
   ```bash
   nano multi-port-service.yaml
   ```

2. Add the following content:
   ```yaml
   apiVersion: v1
   kind: Service
   metadata:
     name: multi-port-service
   spec:
     selector:
       app: multi-port-app
     type: NodePort
     ports:
     - protocol: TCP
       port: 8080
       targetPort: 8080
       nodePort: 30080
       name: http
     - protocol: TCP
       port: 9090
       targetPort: 9090
       nodePort: 30090
       name: custom
   ```

### **Explanation of Fields**
- **`apiVersion`**: Kubernetes API version for Service objects.
- **`kind`**: Defines this object as a `Service`.
- **`metadata`**: Contains metadata about the service:
  - **`name`**: The name of the service (`multi-port-service`).
- **`spec`**: Defines the service specification:
  - **`selector`**: Matches pods with the label `app=multi-port-app`.
  - **`type`**: Specifies the service type as `NodePort`.
  - **`ports`**: Exposes multiple ports:
    - `port: 8080`: The service port for HTTP traffic.
    - `targetPort: 8080`: Maps to the pod's container port 8080.
    - `nodePort: 30080`: Exposes HTTP on node port 30080.
    - `port: 9090`: The service port for custom traffic.
    - `targetPort: 9090`: Maps to the pod's container port 9090.
    - `nodePort: 30090`: Exposes custom traffic on node port 30090.

3. Apply the YAML file to create the service:
   ```bash
   kubectl apply -f multi-port-service.yaml
   ```

4. Verify the service is created:
   ```bash
   kubectl get svc
   ```

   Example Output:
   ```
   NAME                 TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)               AGE
   multi-port-service   NodePort    10.96.123.45     <none>        8080:30080/TCP,9090:30090/TCP   10s
   ```

---

## **3. Testing the Multi-Port Service**

1. **Access the Service**:
   Use the node's IP address and the `NodePort` values to access the service:
   - For HTTP traffic on port 8080:
     ```bash
     curl <node-ip>:30080
     ```
   - For custom traffic on port 9090:
     ```bash
     curl <node-ip>:30090
     ```

2. **Expected Output**:
   Both requests should return:
   ```
   Hello, Multi-Port Service!
   ```

---

## **4. Clean Up**

To delete the resources created in this lab:
```bash
kubectl delete -f multi-port-pod.yaml
kubectl delete -f multi-port-service.yaml
```

---

## **Summary**

| **Resource**        | **Description**                                                                 |
|---------------------|-------------------------------------------------------------------------------|
| **Pod**             | Runs a container exposing two ports: 8080 (HTTP) and 9090 (Custom Port).     |
| **Service**         | Routes traffic to the pod's two ports using NodePort (30080, 30090).         |
| **NodePort Access** | Makes both ports accessible externally via the node's IP.                   |

---

By following this tutorial, you've successfully deployed and exposed a multi-port service in Kubernetes, demonstrating how to manage multiple ports in a real-world scenario without requiring SSL configuration.
