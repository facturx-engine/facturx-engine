# Factur-X API - Build & Deploy Guide

## Version: 1.0.0

---

## 🏗️ Architecture & Build Rules (CRITICAL)

This project follows a strict **"Open Core"** architecture with security invariants. It contains two editions:

### 1. Community Edition (Public)

* **Source**: Fully open-source in `app/`.
* **Build**: Can be built anywhere (Local or Cloud/GitHub Actions).
* **Target**: `docker build --target community` (or default).
* **CI/CD**: Managed by `.github/workflows/publish-community.yml`.

### 2. Pro Edition (Private/Commercial)

* **Source**: Contains proprietary logic (`*_pro.py`) which is **gitignored**.
* **Security**: Since the source code is NOT in the repo, **it CANNOT be built on GitHub Actions**.
* **Build**: MUST be built **LOCALLY** on a secure admin machine.
* **Tooling**: Use `.\publish_release.ps1` to build the Pro artifact.
* **Artifact**: `facturx-engine-pro-*.tar.gz` (uploaded manually to Lemon Squeezy).

> **⚠️ IMPORTANT NOTE FOR MAINTAINERS:**
> Never attempt to configure GitHub Actions to build the `pro` target. It will fail or produce a hollow image. The Pro build process is strictly **Local & Manual**.

---

```bash
# Build
docker build -t facturx-api:1.0.0 .

# Run (development)
uvicorn app.main:app --reload --port 8000

# Run (production - Docker)
cd deploy/selfhosted
docker-compose up -d

# Test
pytest tests/ -v

# Generate support bundle
python -m tools.support_bundle
```

---

## Detailed Build Instructions

### 1. Development Environment

```bash
# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn app.main:app --reload --port 8000

# Run tests
pytest tests/ -v

# Access docs
# http://localhost:8000/docs
```

### 2. Docker Build

```bash
# Build image
docker build -t facturx-api:1.0.0 .

# Tag as latest
docker tag facturx-api:1.0.0 facturx-api:latest

# Run standalone
docker run -p 8000:8000 facturx-api:1.0.0
```

### 3. Production Deployment (Docker Compose)

```bash
# Navigate to deploy directory
cd deploy/selfhosted

# Copy environment file
cp .env.example .env

# Edit configuration (optional)
nano .env

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

---

## Testing

### Unit & Integration Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_extract.py::test_end_to_end_convert_validate_extract -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

### Manual API Testing

```bash
# Health check
curl http://localhost:8000/health

# Diagnostics
curl http://localhost:8000/diagnostics | jq

# Convert test (see README.md for full example)

# Extract test
# (upload a Factur-X PDF via /docs UI)
```

---

## Support Bundle Generation

```bash
# From project root
python -m tools.support_bundle

# From Docker container
docker exec facturx-api python -m tools.support_bundle
docker cp facturx-api:/app/support_bundle_*.zip .
```

---

## Docker Registry Push (Optional)

```bash
# Tag for registry
docker tag facturx-api:1.0.0 your-registry.com/facturx-api:1.0.0
docker tag facturx-api:1.0.0 your-registry.com/facturx-api:latest

# Push
docker push your-registry.com/facturx-api:1.0.0
docker push your-registry.com/facturx-api:latest
```

---

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `API_PORT` | 8000 | API listening port |
| `APP_MODE` | production | Runtime mode (dev/production) |
| `WORKERS` | 4 | Number of worker processes |
| `MEM_LIMIT` | 512m | Memory limit for container |
| `CPU_LIMIT` | 1.0 | CPU limit for container |
| `MAX_UPLOAD_SIZE_MB` | 10 | Maximum PDF upload size |
| `LICENSE_KEY` | (empty) | License key for paid features |
| `DISABLE_CONVERT` | false | Di sable /v1/convert endpoint |

---

## Verification Checklist

After deployment, verify:

* [ ] `GET /health` returns `200 OK`
* [ ] `GET /diagnostics` shows correct version
* [ ] `GET /docs` loads Swagger UI
* [ ] `POST /v1/convert` works with test PDF
* [ ] `POST /v1/validate` works
* [ ] `POST /v1/extract` works
* [ ] Memory usage < 512MB (check `/diagnostics`)
* [ ] Logs are clean (`docker logs facturx-api`)

---

## Troubleshooting Build Issues

### Issue: "pip: command not found"

**Solution:** Install Python 3.11+ first

### Issue: "docker: command not found"

**Solution:** Install Docker Desktop

### Issue: "Port 8000 already in use"

**Solution:** Change `API_PORT` in `.env` or stop conflicting service

### Issue: Tests fail

**Solution:**

1. Install test dependencies: `pip install -r requirements.txt`
2. Check Python version: `python --version` (need 3.11+)

---

## CI/CD Integration Example (GitHub Actions)

```yaml
name: Build and Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v
      
  build:
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v3
      - run: docker build -t facturx-api:latest .
```

---

## Next Steps

1. **Deploy**: Follow `deploy/selfhosted/README_SELF_HOSTED.md`
2. **Configure**: Edit `.env` for your environment
3. **Monitor**: Check `/diagnostics` regularly
4. **Upgrade**: See `deploy/selfhosted/UPGRADE.md`

---

**For support:** See `deploy/selfhosted/SUPPORT_POLICY.md`
