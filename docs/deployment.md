# Deployment Guide

This guide covers deploying the Dagster Crypto Data Extraction pipeline using Docker and Kubernetes. For local development, please see the main `GETTING_STARTED.md` file.

## Prerequisites

- Kubernetes cluster (v1.24+)
- PostgreSQL database (v13+)
- kubectl configured with cluster access
- Docker for building images
- Helm 3+ (optional, for simplified deployment)

## Docker Deployment

### 1. Build Docker Image

```bash
docker build -t crypto-extraction:latest .

# Tag for registry
docker tag crypto-extraction:latest your-registry/crypto-extraction:v1.0.0

# Push to registry
docker push your-registry/crypto-extraction:v1.0.0
```

### 2. Test Docker Image Locally

```bash
docker run -it --rm \
  -e POSTGRES_HOST=host.docker.internal \
  -e POSTGRES_USER=crypto_user \
  -e POSTGRES_PASSWORD=your_password \
  -e POSTGRES_DB=crypto_data \
  -p 4000:4000 \
  crypto-extraction:latest
```

## Kubernetes Deployment

**Note**: The Dagster image versions used in these manifests (`dagster/dagster-k8s:1.8.0`) may be outdated. Please check the [Dagster Helm Chart repository](https://github.com/dagster-io/helm) for the latest compatible versions.

### 1. Create Namespace

```bash
kubectl create namespace dagster-crypto
```

### 2. Create Secrets

Create `k8s/secrets.yaml`:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: postgres-credentials
  namespace: dagster-crypto
type: Opaque
stringData:
  host: "postgres.database.svc.cluster.local"
  port: "5432"
  user: "crypto_user"
  password: "your_secure_password"
  database: "crypto_data"
---
apiVersion: v1
kind: Secret
metadata:
  name: s3-credentials
  namespace: dagster-crypto
type: Opaque
stringData:
  bucket_name: "my-crypto-data-bucket"
  endpoint_url: "http://minio.minio.svc.cluster.local:9000"
  access_key_id: "minioadmin"
  secret_access_key: "minioadmin"
```

Apply secrets:

```bash
kubectl apply -f k8s/secrets.yaml
```

### 3. Deploy Dagster Code Location

Create `k8s/code-location.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dagster-code-location
  namespace: dagster-crypto
spec:
  replicas: 2
  selector:
    matchLabels:
      app: dagster-code-location
  template:
    metadata:
      labels:
        app: dagster-code-location
    spec:
      containers:
      - name: user-code
        image: your-registry/crypto-extraction:v1.0.0
        command: ["dagster", "api", "grpc", "-h", "0.0.0.0", "-p", "4000", "-f", "app/definitions.py"]
        ports:
        - containerPort: 4000
        env:
        - name: POSTGRES_HOST
          valueFrom:
            secretKeyRef:
              name: postgres-credentials
              key: host
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: postgres-credentials
              key: user
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-credentials
              key: password
        - name: POSTGRES_DB
          valueFrom:
            secretKeyRef:
              name: postgres-credentials
              key: database
        - name: S3_BUCKET_NAME
          valueFrom:
            secretKeyRef:
              name: s3-credentials
              key: bucket_name
        - name: S3_ENDPOINT_URL
          valueFrom:
            secretKeyRef:
              name: s3-credentials
              key: endpoint_url
        - name: S3_ACCESS_KEY_ID
          valueFrom:
            secretKeyRef:
              name: s3-credentials
              key: access_key_id
        - name: S3_SECRET_ACCESS_KEY
          valueFrom:
            secretKeyRef:
              name: s3-credentials
              key: secret_access_key
---
apiVersion: v1
kind: Service
metadata:
  name: dagster-code-location
  namespace: dagster-crypto
spec:
  selector:
    app: dagster-code-location
  ports:
  - port: 4000
    targetPort: 4000
  type: ClusterIP
```

### 4. Deploy Dagster Webserver and Daemon

You can find example manifests for the Dagster webserver and daemon in the official Dagster documentation. They will need to be configured to connect to your code location and PostgreSQL database.

### 5. Apply All Manifests

```bash
kubectl apply -f k8s/
```

## Helm Deployment (Alternative)

### 1. Install Dagster Helm Chart

```bash
helm repo add dagster https://dagster-io.github.io/helm
helm repo update
```

### 2. Create Values File

Create `helm-values.yaml`:

```yaml
dagsterWebserver:
  replicaCount: 2

dagsterDaemon:
  replicaCount: 1

runLauncher:
  type: K8sRunLauncher

postgresql:
  enabled: false
  postgresqlHost: "your-postgres-host"
  postgresqlUsername: "crypto_user"
  postgresqlPassword: "your_password"
  postgresqlDatabase: "dagster"

workspace:
  enabled: true
  servers:
  - host: "dagster-code-location"
    port: 4000

userDeployments:
  enabled: true
  deployments:
  - name: "crypto-extraction"
    image:
      repository: "your-registry/crypto-extraction"
      tag: "v1.0.0"
      pullPolicy: Always
    dagsterApiGrpcArgs:
    - "-f"
    - "app/definitions.py"
    port: 4000
    env:
    - name: POSTGRES_HOST
      valueFrom:
        secretKeyRef:
          name: postgres-credentials
          key: host
    - name: POSTGRES_USER
      valueFrom:
        secretKeyRef:
          name: postgres-credentials
          key: user
    - name: POSTGRES_PASSWORD
      valueFrom:
        secretKeyRef:
          name: postgres-credentials
          key: password
    - name: POSTGRES_DB
      valueFrom:
        secretKeyRef:
          name: postgres-credentials
          key: database
    - name: S3_BUCKET_NAME
      valueFrom:
        secretKeyRef:
          name: s3-credentials
          key: bucket_name
    - name: S3_ENDPOINT_URL
      valueFrom:
        secretKeyRef:
          name: s3-credentials
          key: endpoint_url
    - name: S3_ACCESS_KEY_ID
      valueFrom:
        secretKeyRef:
          name: s3-credentials
          key: access_key_id
    - name: S3_SECRET_ACCESS_KEY
      valueFrom:
        secretKeyRef:
          name: s3-credentials
          key: secret_access_key
```

### 3. Install Helm Release

```bash
helm install dagster dagster/dagster \
  -n dagster-crypto \
  --create-namespace \
  -f helm-values.yaml
```

