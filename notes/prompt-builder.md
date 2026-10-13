# Guided prompt builder

[한국어](ko/prompt-builder.md)

The pinned frontend exposes **Prompt builder** immediately after Home in all three
layouts, including production. `/prompt-builder` is available to guests and members
under the existing configuration/readiness gates; no backend endpoint or environment
switch is added.

The central capsule opens a feature/project chooser. Both paths ask for a feature name
and multiple implementation areas and elements, then capabilities/RBAC and delivery in four questions,
review and localized Markdown output with copy/download. This is a client-side template
builder: it performs no AI call, repository scan, remote write or deployment. Answers
remain in page memory and reset on leaving/reloading.

See the child [usage and verification guide](../src/frontend/notes/prompt-builder.md).
Frontend source and tests are owned by B4React; the parent pins its merged revision
and verifies contracts, packaging and branding. Publish through the normal frontend
image build/deploy workflow; production availability is not a claim of live deployment.
