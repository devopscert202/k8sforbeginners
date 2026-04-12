# WordPress and MySQL on Kubernetes

## Introduction

**WordPress** is a widely used open-source CMS for websites and blogs. **MySQL** is a common relational database for WordPress content, users, and configuration.

On Kubernetes, a minimal lab-style stack usually includes:

- **Deployments** for MySQL and WordPress (each runs in Pods).
- **Services** so WordPress can resolve the database by **DNS name** (for example `mysql`) and so users can reach the web tier (often **NodePort** or **Ingress** in labs).

This page explains the **architecture and manifest shape**. Applying manifests, choosing node addresses, and completing the WordPress install wizard are covered in the linked lab.

---

## Architecture (conceptual)

1. **MySQL Deployment** — one replica is typical in introductory examples; production would address storage, backups, and high availability separately.
2. **MySQL Service** — stable cluster DNS name and port **3306** for the WordPress Pod.
3. **WordPress Deployment** — web tier Pods with environment variables pointing at the MySQL Service and database credentials.
4. **WordPress Service** — exposes HTTP (port **80**) to the cluster or externally depending on `type` (NodePort, LoadBalancer, or ClusterIP + Ingress).

**Security note**: Example manifests often embed passwords in `env` for clarity. Prefer **Secrets** (or external secret management) for real clusters.

---

## Illustrative manifests

### MySQL Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mysql
  labels:
    app: mysql
spec:
  replicas: 1
  selector:
    matchLabels:
      app: mysql
  template:
    metadata:
      labels:
        app: mysql
    spec:
      containers:
      - name: mysql
        image: mysql:5.6
        env:
        - name: MYSQL_ROOT_PASSWORD
          value: k8slearning
        - name: MYSQL_DATABASE
          value: database1
```

- **`replicas`**: Pod count for the database tier (tutorials often use `1`).
- **`MYSQL_ROOT_PASSWORD` / `MYSQL_DATABASE`**: Bootstrap credentials and schema name for WordPress to use.

### MySQL Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: mysql
spec:
  type: NodePort
  selector:
    app: mysql
  ports:
    - protocol: TCP
      port: 3306
      targetPort: 3306
```

- **`type`**: `NodePort` is common in labs for direct browser or host access; **ClusterIP** is typical when only in-cluster workloads talk to MySQL.

### WordPress Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: wordpress
  labels:
    app: wordpress
spec:
  replicas: 1
  selector:
    matchLabels:
      app: wordpress
  template:
    metadata:
      labels:
        app: wordpress
    spec:
      containers:
      - name: wordpress
        image: wordpress
        env:
        - name: WORDPRESS_DB_HOST
          value: mysql
        - name: WORDPRESS_DB_PASSWORD
          value: k8slearning
        - name: WORDPRESS_DB_USER
          value: root
        - name: WORDPRESS_DB_NAME
          value: database1
```

- **`WORDPRESS_DB_HOST`**: Kubernetes **Service** name for MySQL; the cluster DNS name resolves to the Service VIP.
- Other variables must **match** the credentials and database name configured for MySQL.

### WordPress Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: wordpress-service
spec:
  type: NodePort
  selector:
    app: wordpress
  ports:
    - protocol: TCP
      port: 80
      targetPort: 80
```

---

## Operations and limitations

- **Persistence**: Without **PersistentVolumeClaims**, database data lives in the container filesystem and is lost if the Pod is rescheduled unless the platform adds implicit storage. Treat lab YAML as **ephemeral**.
- **Scaling**: Scaling WordPress replicas without shared file storage breaks uploaded media unless you add object storage or a shared volume pattern.
- **Exposure**: Prefer **Ingress** or cloud **LoadBalancer** in production instead of ad hoc NodePort URLs.

---

## Conclusion

WordPress on Kubernetes demonstrates **multi-tier applications**: stable naming via Services, environment-based configuration, and separate controllers for the web and data tiers. Guided steps to apply these resources and validate the site are in the lab manual.

---

## Hands-On Labs

Practice these concepts with guided lab exercises:

| Lab | Description |
|-----|-------------|
| [Lab 41: WordPress on Kubernetes](../../labmanuals/lab41-adv-wordpress-on-kubernetes.md) | Deploy MySQL and WordPress, expose Services, and complete setup with hands-on verification. |
