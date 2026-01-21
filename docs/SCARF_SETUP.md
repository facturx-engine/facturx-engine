# Setup Guide: Scarf Gateway (Telemetry)

This guide explains how to set up **Scarf Gateway** to track Docker pulls by company/domain without compromising user privacy. This satisfies the "Telemetry" recommendation from the Strategy Report.

## 1. Why Scarf?

* **Privacy-Friendly**: Scarf sits in front of Docker Hub. It sees the IP address of the pull request, resolves it to a Company Name (e.g., "BNP Paribas"), and discards the IP. It does *not* track individual users.
* **Actionable Data**: You get a dashboard showing which companies are using your software. This is critical for B2B sales (Account Based Marketing).

## 2. Setup Steps

1. **Create Account**: Go to [scarf.sh](https://scarf.sh) and sign up.
2. **Create a Package**:
    * Select **"Docker"** as the package type.
    * Name: `facturx-engine`.
    * Upstream URL: `facturxengine/facturx-engine` (Your actual Docker Hub image).
3. **Get Your Gateway URL**:
    * Scarf will generate a URL like: `facturx-engine.docker.scarf.sh/facturx-engine`.

## 3. Update Documentation

Once you have your Scarf URL, you must update your `README.md` to direct users to pull from Scarf instead of Docker Hub directly.

**In `README.md`:**

```markdown
### Option 1: Docker (Recommended)

Run the container in 1 command:

```bash
docker run -p 8000:8000 facturx-engine.docker.scarf.sh/facturx-engine:latest
```

```

**In `docker-compose.yml`:**

```yaml
services:
  facturx-api:
    image: facturx-api.docker.scarf.sh/facturx-api:1.0.0 # <--- Update this
```

## 4. Verify

1. Run a `docker pull` using the new Scarf URL.
2. Check your Scarf Dashboard. You should see "1 Pull" appear shortly.
