# Comparison: MustangProject vs Factur-X Engine

Choosing the right tool for e-invoicing (Factur-X / ZUGFeRD) is critical for long-term maintenance. This guide compares **MustangProject** (Java Library) with **Factur-X Engine** (Docker API).

## Technical Overview

| Feature | MustangProject | Factur-X Engine |
| :--- | :--- | :--- |
| **Language** | Java | Agnostic (REST API) |
| **Delivery** | JAR / Maven Dependency | Docker Image |
| **PDF Engine** | PDFBox / Apache | Internal C++ Engine |
| **Validation** | Java Validator | Native Schematron (EN 16931) |
| **Dependencies** | Requires JRE / JVM | Zero system dependencies |

## When to choose MustangProject?

Choose Mustang if:

1. You are building a **Desktop Application** in Java (Swing/JavaFX).
2. You want to embed the logic directly into a legacy Java monolith.
3. You do not have access to Docker/Container orchestration.

## When to choose Factur-X Engine?

Choose Factur-X Engine if:

1. **Multi-language stack**: You need to generate invoices from Node.js, PHP, Python, or Go.
2. **Cloud-Native / Microservices**: You want to scale the e-invoicing logic independently from your main application.
3. **Local processing**: You need invoice processing that can run without sending invoice data to a hosted SaaS API; network isolation remains your deployment responsibility.
4. **DevOps Simplicity**: You want to avoid "Dependency Hell" (Ghostscript, versions of lxml, Java JRE conflicts).

## Performance Comparison

- **MustangProject**: An in-process Java library avoids an HTTP service boundary and fits naturally in JVM applications.
- **Factur-X Engine**: A long-running container provides a language-neutral HTTP boundary. Measure latency and memory with your own documents and deployment settings.

## Summary

Factur-X Engine packages invoice generation, validation and extraction tooling behind a local HTTP API. Its results are technical evidence, not a guarantee of regulatory conformity or recipient acceptance.
