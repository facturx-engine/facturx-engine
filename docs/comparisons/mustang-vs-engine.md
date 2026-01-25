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
3. **Security (Privacy)**: You need an air-gapped solution that works 100% offline without leaking data to SaaS providers.
4. **DevOps Simplicity**: You want to avoid "Dependency Hell" (Ghostscript, versions of lxml, Java JRE conflicts).

## Performance Comparison

- **MustangProject**: JVM startup overhead can be an issue for short-lived tasks (Lambda/Functions). Continuous memory usage is higher due to JVM.
- **Factur-X Engine**: Optimized for high-throughput REST calls. Stateless architecture means memory is released immediately after each request.

## Summary

Factur-X Engine is designed as **Infrastructure-as-Code**. It provides a "black box" that handles the painful parts of EN 16931 compliance, allowing your developers to focus on your core business logic rather than PDF/A-3 specification details.
