## 🧩 Introduction to Kubernetes APIs

Kubernetes (K8s) is built entirely around a **powerful, declarative API**. Every object in Kubernetes — whether it’s a Pod, Deployment, Service, or Namespace — is represented and managed through the **Kubernetes API Server**, which acts as the *central communication hub* of the cluster.

### 🔹 What is the Kubernetes API?

The **Kubernetes API** is the core interface that allows users, tools, and internal components (like the scheduler or controller manager) to interact with the cluster.
It exposes RESTful HTTP endpoints, enabling clients (e.g., `kubectl`, client libraries, or custom controllers) to **create, read, update, and delete (CRUD)** Kubernetes objects.

### 🔹 Key Concepts

* **Resource:**
  A Kubernetes object type, such as `Pod`, `Deployment`, or `Service`.

* **API Group:**
  A logical collection of related resources.
  Example:

  * Core group (no prefix): `v1` → includes Pods, Services, ConfigMaps.
  * Named groups: `apps/v1`, `batch/v1`, `networking.k8s.io/v1`.

* **Version:**
  Each API group can have multiple versions (e.g., `v1alpha1`, `v1beta1`, `v1`).
  Versions indicate the **stability** of the API and possible schema evolution.

* **Kind:**
  The specific object type within a resource definition.
  Example: `apiVersion: apps/v1`, `kind: Deployment`.

* **apiVersion field:**
  Every YAML manifest starts with `apiVersion` and `kind` — these tell Kubernetes which version of the API to use for that object.

### 🔹 How it Works

1. A user (or automation) sends a request to the **API Server** — directly or through `kubectl`.
2. The **API Server validates and authenticates** the request.
3. It stores or retrieves the object definition in **etcd** (the cluster’s database).
4. Controllers, schedulers, and other control plane components **watch the API** for changes and act accordingly to reach the desired state.

### 🔹 Why It Matters

* All Kubernetes components — even `kubectl` — communicate through this API.
* It enables **automation**, **extensibility**, and **customization** (via CRDs and API aggregation).
* The API model allows **declarative management** — you describe *what* you want, and Kubernetes ensures it happens.

---

**In short:**

> The Kubernetes API is the backbone of the entire system — every operation, from deploying an app to scaling a cluster, goes through it.

---

# How to determine `apiVersion` for a Kubernetes resource

1. **Check the object itself**

   * If an object already exists, its YAML includes the `apiVersion` field:

     ```
     kubectl get <kind> <name> -n <namespace> -o yaml
     # e.g.
     kubectl get deployment my-app -n default -o yaml
     ```

     The top of the returned YAML contains `apiVersion: ...`.

2. **Query the API-discovery with `kubectl api-resources`**

   * This shows resource names and the preferred API group/version:

     ```
     kubectl api-resources -o wide
     ```

     Look at the `APIVERSION` (or `GROUP`) column for the preferred `group/version`. Example line might show:

     ```
     NAME       SHORTNAMES   APIGROUP   NAMESPACED   KIND        VERBS
     pods       po                       true        Pod         [create list ...]   (APIVERSION column shows `v1`)
     deployments        apps      true        Deployment  (APIVERSION column: `apps/v1`)
     ```
   * To find a specific resource quickly:

     ```
     kubectl api-resources | grep -i deployment
     ```

3. **Use `kubectl explain` for schema & field info**

   * `kubectl explain <resource>` shows the API doc and can imply the API group/version; it also shows field docs and deprecation notes for fields:

     ```
     kubectl explain deployment
     kubectl explain deployment.spec.replicas
     ```

4. **When using CRDs (CustomResourceDefinitions)**

   * CRDs define their own `group` and one or more `versions`. Inspect CRDs:

     ```
     kubectl get crd <crd-name> -o yaml
     # or list CRDs:
     kubectl get crd
     ```
   * The CRD YAML shows `.spec.versions[].name` (e.g., `v1`, `v1beta1`) — that is the version you use in `apiVersion: <group>/<version>`.

5. **Discovery endpoints (if you need programmatic confirmation)**

   * Core group (no group): `/api` (example for v1)
   * Named groups: `/apis` and `/apis/<group>/<version>`
   * Example (using kubectl to call API directly — no proxy required if kubectl has kubeconfig):

     ```
     kubectl get --raw /api          # lists core API versions (e.g., v1)
     kubectl get --raw /apis         # lists API groups served by the cluster
     kubectl get --raw /apis/apps    # lists versions for apps group
     kubectl get --raw /apis/apps/v1
     ```
   * Or with a local proxy:

     ```
     kubectl proxy &       # starts proxy at http://127.0.0.1:8001
     curl http://127.0.0.1:8001/apis
     ```

---

# How to query **all available APIs** in a cluster

Use the built-in discovery tools:

1. **Quick list of API versions**

   ```
   kubectl api-versions
   ```

   This prints each `group/version` the API server serves (e.g., `v1`, `apps/v1`, `networking.k8s.io/v1`).

2. **List all resources (with the group/version they belong to)**

   ```
   kubectl api-resources -o wide
   ```

   `NAME`, `SHORTNAMES`, `APIGROUP`, `NAMESPACED`, `KIND`, and `VERBS` are shown; the `APIGROUP` + the cluster’s default version for that group tells you which `apiVersion` to use (e.g., `apps/v1`).

3. **Programmatic discovery (raw HTTP)**

   ```
   kubectl get --raw /apis | jq .
   kubectl get --raw /api | jq .
   ```

   * `/api` lists core group versions (e.g., `v1`).
   * `/apis` lists all API groups and the versions each group serves.

4. **List APIService objects (aggregated APIs served by extension API servers)**

   ```
   kubectl get apiservices
   ```

   `APIService` objects represent APIs registered via the aggregation layer (e.g., metrics.k8s.io).

---

# Beta vs Stable (v1) APIs — what's the difference?

Kubernetes uses version suffixes like `alpha`, `beta`, and `v1` to indicate maturity and stability. Key differences:

1. **Naming convention**

   * `v1` (stable / GA)
   * `v1beta1`, `v1beta2`, etc. (beta)
   * `v1alpha1`, etc. (alpha)

2. **Stability & guarantees**

   * **Stable (GA, e.g., `v1`)**

     * Strong compatibility guarantees.
     * Fields and behaviour are expected to be stable across minor releases (backwards compatible).
     * Deprecated fields or APIs get a deprecation notice first and are removed only after a transition period described in release notes.
     * Prefer using GA APIs in production.
   * **Beta (`v1betaN`)**

     * Feature is mostly complete and usable; generally enabled by default.
     * More likely to change than GA: fields or semantics can be adjusted, though removal normally requires deprecation first (but historically beta may move faster).
     * Beta APIs are less risky than alpha but not as safe as GA.
   * **Alpha (`v1alphaN`)**

     * Experimental. May be behind feature gates.
     * May change or be removed without formal deprecation; not recommended for production.

3. **Feature-gates and defaults**

   * Alpha features often require explicit feature gates to enable.
   * Beta features are typically enabled by default (but confirm for your cluster).

4. **Deprecation and removal process**

   * Kubernetes publishes deprecation notices in release notes and Kubernetes API deprecation policy.
   * Typically: API moves from `alpha` → `beta` → `stable` (GA). When an API is deprecated, it will be announced and removed in a future release—check release notes.

5. **Practical guidance**

   * Prefer `v1` / GA resources in production.
   * If using `beta`, be prepared to test on upgrades and read the Kubernetes release notes for deprecation warnings.
   * For automation and long-term code, design for migration (i.e., avoid pinning to deprecated fields, test upgrades).

---

# Useful quick commands summary

* Show supported API group/versions:

  ```
  kubectl api-versions
  ```
* Show resources and their API groups/versions:

  ```
  kubectl api-resources -o wide
  ```
* Inspect a specific resource’s expected schema & docs:

  ```
  kubectl explain deployment
  ```
* Get an object's `apiVersion` from live object YAML:

  ```
  kubectl get deployment my-app -n default -o yaml
  ```
* Raw discovery (programmatic):

  ```
  kubectl get --raw /apis
  kubectl get --raw /api
  kubectl get apiservices
  ```
* List CRDs:

  ```
  kubectl get crd
  kubectl get crd <name> -o yaml
  ```

---

# Tips & gotchas

* `apiVersion` is always `<group>/<version>` for grouped APIs (e.g., `apps/v1`) and `v1` for core (no-group) resources like Pod and Service.
* `kubectl api-resources -o wide` is the single most practical command to map *resource name → apiVersion* quickly.
* When writing manifests, explicitly set `apiVersion` (don’t rely on server defaults).
* Before upgrading Kubernetes clusters or your manifests, scan for deprecated API versions (there are tools and admission webhooks that can help detect deprecated usages).
* Use `kubectl explain` to see if fields are marked `DEPRECATED` in the schema.

---

If you want, I can:

* give examples for **specific resources** (e.g., `Ingress` changed group/versions across releases — show how to find the current one), or
* provide a **short checklist** for migrating manifests from `v1beta1` → `v1` for common APIs like `Ingress` and `DaemonSet`. Which would help you more?
