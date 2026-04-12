# **Lab: Deploying a Flask Application with Redis in Kubernetes**

This page describes the **architecture and Kubernetes objects** typically used when running a small web application (Flask) backed by Redis for session or counter state. The pattern applies to many “app + cache/database” deployments.

---

## **Objective (conceptual)**

You run **two logical tiers** in the cluster:

1. **Redis** — data store (ephemeral or persistent depending on how you operate it).
2. **Flask** — HTTP service that talks to Redis over the cluster network.

Each tier is usually modeled as a **Deployment** (desired Pod replicas) and a **ClusterIP Service** (stable DNS name and port for in-cluster clients). Building container images, pushing to a registry, and applying manifests step by step are covered in the linked lab.

---

## **Why Deployments and Services**

- **Deployment**: Declares the container image, environment, and replica count for stateless app Pods; the controller reconciles actual state.
- **Service**: Gives Redis and Flask **stable names** (for example `redis` on port `6379`) so the Flask Pod does not hardcode Pod IPs.

The Flask app code typically connects to `redis:6379` when `REDIS_HOST` (or equivalent) is set to the Service name.

---

## **Illustrative manifests**

### **Redis Deployment (concept)**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis
```

### **Redis Service**

A **ClusterIP** Service is enough for in-cluster access from Flask; **NodePort** or **Ingress** is only needed if something outside the cluster must reach Redis directly (uncommon).

```yaml
apiVersion: v1
kind: Service
metadata:
  name: redis
spec:
  ports:
  - port: 6379
    targetPort: 6379
  selector:
    app: redis
```

### **Flask Deployment**

The image reference points at **your** registry image after you build and push it (placeholder shown as `example/flask-app:tag`).

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: flask
spec:
  replicas: 1
  selector:
    matchLabels:
      app: flask
  template:
    metadata:
      labels:
        app: flask
    spec:
      containers:
      - name: flask
        image: example/flask-app:tag
```

### **Flask Service**

Expose the container port your process listens on (often `5000` for Flask in examples):

```yaml
apiVersion: v1
kind: Service
metadata:
  name: flask
spec:
  ports:
  - port: 5000
    targetPort: 5000
  selector:
    app: flask
```

---

## **Configuration and secrets**

- Prefer **Secrets** (or external secret stores) for database passwords and Redis credentials instead of plain `env` literals in tracked YAML.
- Non-sensitive settings can live in **ConfigMaps**; see the ConfigMaps doc and lab.

---

## **Operations notes**

- **Scaling**: Flask Deployments scale horizontally; Redis as a single replica is a **single point of failure** unless you adopt HA Redis or a managed cache.
- **Persistence**: The illustrative Redis Deployment uses empty container storage; production setups use **PersistentVolumes** or managed data services.
- **Networking**: ClusterIP Services are reachable only inside the cluster unless you add Ingress, Gateway API, or `NodePort`/`LoadBalancer` for external users.

---

## Hands-On Labs

Practice these concepts with guided lab exercises:

| Lab | Description |
|-----|-------------|
| [Lab 24: Frontend deployment](../../labmanuals/lab24-deploy-frontend-deployment.md) | Build and push an image, deploy app and backing service, and verify connectivity with guided steps. |
