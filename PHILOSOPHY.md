# Music MCP philosophy

Founding constitution · v0.1.0 · 2026-09-18

> The musician stays the artist. The machine does the notation, calculation, and clerical work.

Music MCP exists to reduce the labor between musical intention and a usable musical artifact. A person may know a melody, a phrasing, or an arrangement without having the time or notation skills to enter it. Assistance should preserve that person's authorship and choices.

## Authority belongs to people

**Human intent is authoritative. Machine inference is provisional. Machine creation is identifiable. Machine modification is authorized.**

An authorized human correction takes precedence over competing machine interpretations within its scope. A poorly sung phrase can mean straight eighth notes even when an analyzer favors triplets. The performance remains evidence; the correction establishes intended notation. Reanalysis must not silently reverse that decision.

Authority is scoped. A performer, arranger, editor, and project owner may have different permissions. Permission to transpose does not grant permission to rewrite a resulting out-of-range part. Models propose; the trusted host enforces authority. No model directly controls authoritative musical state.

## Keep the distinctions

Evidence is what was received. Observations describe it and may be mistaken. Interpretations assign possible meaning. Suggestions introduce alternatives or new material. Confirmation establishes authorized intent. Mutation changes authoritative state. None of these stages may masquerade as another.

Generated music is welcome when requested and permitted. Acceptance does not erase its origin. Uncertainty and disagreement are useful information, not defects to conceal with arbitrary confidence numbers.

## Preserve the work and its history

Consequential changes must be attributable, constrained, inspectable, and reversible. Preserve original evidence and the reasoning needed to distinguish performance, inference, generated material, and human correction. Explain what failed, whether anything changed, and how the musician can proceed safely.

Reversibility must describe real guarantees. An in-memory revision is not a durable backup; an external application's undo command is not proof of a complete transaction.

## Remain open and replaceable

The project is model-agnostic and application-agnostic. MCP exposes capabilities; it does not define musical truth. MusicXML, MIDI, notation applications, and model providers belong behind replaceable contracts. Musical meaning must not be reduced to the limits of a particular format or to Western notation alone.

Failures should stay within their capability's boundary. The project must survive changing providers, policies, licenses, maintainers, and models. Documentation and executable contracts make continuity possible without an indispensable founder or developer.

## Apply the constitution deliberately

[SPECIFICATION.md](SPECIFICATION.md) defines normative behavior; [ARCHITECTURE_PRINCIPLES.md](ARCHITECTURE_PRINCIPLES.md) translates these principles into engineering obligations. This constitution is not a claim that every intended capability exists. v0.1.0 is an experimental in-process reference core, not an audio transcription product or MCP server.

Changes to these principles require an explicit proposal, consequences, and the project owner's decision recorded in [whats_and_hows_log.md](whats_and_hows_log.md). Convenience and a convincing model response do not amend the constitution.
