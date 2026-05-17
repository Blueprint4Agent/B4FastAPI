# GitHub Actions Build Pipeline

- commit title: github actions build pipeline
- changed file scope: GitHub Actions workflow, deployment docs, Korean deployment docs
- reason: automate PR quality checks, nightly image publishing, manual ref builds, and release/tag-based image publishing
- impact: pull requests run backend/frontend checks without image builds; nightly `main`, releases, and `v*` tags build and publish Docker images to GHCR; manual runs can build a selected ref or PR and optionally publish an image
