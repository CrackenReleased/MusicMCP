# CODEX FOUNDING BUILD DIRECTIVE
## Music MCP: Open Musical Intelligence Infrastructure

You are being given responsibility for beginning the implementation of a long-lived open-source project currently referred to by the working name **Music MCP**.

Read this entire directive before creating, deleting, moving, renaming, or modifying anything.

Do not treat this as a request to rapidly generate an MVP.

Do not optimize for the largest amount of visible functionality in the shortest amount of time.

Do not create a monolithic proof of concept that will later require architectural reconstruction.

The project is deliberately being built from the foundation outward.

Stability, explicit contracts, interoperability, replaceability, documentation, failure containment, testability, reversibility, and preservation of human musical authority take priority over development speed.

The engineering metaphor governing this project is:

> We are building a 30-foot-tall, 12-foot-thick stone wall broad enough for chariots to race side by side across the top without a pebble on the ground rattling.

That metaphor has technical consequences.

Build accordingly.

---

# 0. CANONICAL REPOSITORY AND SYNC AUTHORITY

The canonical remote repository for this project is:

`https://github.com/CrackenReleased/MusicMCP.git`

The default branch is currently:

`main`

Local agents MUST treat this GitHub repository as the source of truth for determining what is synchronized, what exists remotely, and whether local work is ahead of, behind, diverged from, or otherwise inconsistent with the canonical project state.

Before beginning significant work, a local agent SHOULD:

1. verify that the configured `origin` points to `https://github.com/CrackenReleased/MusicMCP.git`;
2. fetch the latest remote refs;
3. identify the current local branch;
4. compare the local branch HEAD against the corresponding remote branch;
5. detect uncommitted and untracked work;
6. detect whether the local branch is ahead, behind, or diverged from the remote;
7. read the project handoff and governing documentation before making changes;
8. avoid destructive synchronization operations unless explicitly authorized.

Do NOT assume local disk state is current merely because the repository exists locally.

Do NOT assume remote state is identical to the local checkout.

When reporting project state, distinguish clearly between:

- local working tree;
- local committed state;
- remote canonical state;
- unpushed commits;
- remote commits not present locally;
- divergence;
- untracked files.

Agents MUST NOT silently discard local work in order to match GitHub.

If local and remote history diverge, report the divergence clearly and preserve both sides until an intentional reconciliation is performed.

This repository currently exists and should be inspected rather than recreated.

At the time this directive was prepared, the root of `main` contained at least:

- `LICENSE`
- `README.md`

Inspect current remote state again at the beginning of work because the repository may have changed since this directive was written.

---

# 1. FOUNDING PHILOSOPHY

The governing principle of Music MCP is:

> **The musician stays the artist. The machine does the notation, calculation, and clerical work.**

This does not prohibit AI-generated musical suggestions when a human explicitly requests them.

It establishes authority.

The machine assists.

The human determines what the music should ultimately be.

Four additional constitutional statements govern the system:

> **Human intent is authoritative. Machine inference is provisional. Machine creation is identifiable. Machine modification is authorized.**

> **No model directly controls authoritative musical state.**

> **Every consequential change must be attributable, constrained, inspectable, and reversible.**

> **Failure must be contained. Dependencies must be replaceable. Errors must be explainable. Behavior must be documented.**

These are architectural requirements, not marketing language.

---

# 2. WHAT THIS PROJECT IS

Music MCP is intended to become an open, model-agnostic, application-agnostic framework through which artificial intelligence systems can responsibly work with human-created music.

It is not primarily a notation application.

It is not primarily an AI music generator.

It is not intended to replace Dorico, MuseScore, Sibelius, DAWs, MusicXML, MIDI, or future professional musical software.

It is infrastructure connecting:

- human musical intention;
- authoritative musical state;
- AI reasoning;
- musical analysis;
- deterministic musical operations;
- validation;
- existing musical formats;
- existing musical applications;
- future musical applications.

MCP is an integration mechanism for exposing appropriate capabilities to models.

Do not confuse MCP itself with the musical semantic architecture.

Music MCP should conceptually contain distinct layers for:

1. human authority and permissions;
2. intent and constraints;
3. authoritative musical state;
4. provenance and revision history;
5. musical operations;
6. analysis and interpretation;
7. suggestions and generation;
8. policy and rights evaluation;
9. adapters and interoperability;
10. error handling and diagnostics;
11. MCP exposure;
12. conformance and testing.

The system must remain useful as individual AI models and external applications change.

A future GPT, Gemini, Claude, open-source model, specialized music model, or other computational system should be capable of using the framework without changing its fundamental philosophy.

---

# 3. THE CENTRAL PROBLEM

Musicians frequently know what they want musically before they know, or before they have time, to communicate that intention through notation software.

Examples:

A singer knows a melody but has not entered the notes.

An arranger knows how a chord should function but must manually manipulate notation.

A choir director wants an arrangement transposed while respecting specific vocal ranges.

A violinist performs a phrase containing vibrato and expressive timing that should become meaningful notation rather than a literal stream of pitch fluctuations.

A professional transcriber repeatedly rewinds recordings, identifies pitches and rhythms, enters notation, corrects spelling, validates ranges, and cleans engraving.

The machine should remove unnecessary translation and clerical labor without quietly becoming the author.

The central conceptual problem is therefore not simply:

> audio → notes

It is:

> **human evidence → musical understanding → explicitly governed assistance → authoritative musical artifact**

---

# 4. DO NOT PUT THE AI MODEL AT THE CENTER

The model must not own authoritative state.

The model must not be the ultimate permission system.

The model must not be trusted to enforce architectural policy merely because a prompt told it to.

The conceptual architecture should resemble:

```text
                         HUMAN AUTHORITY
                               |
                    INTENT + PERMISSIONS
                         + CONSTRAINTS
                               |
                               v
                    +--------------------+
                    |   MUSIC MCP CORE   |
                    +--------------------+
                               |
          +--------------------+--------------------+
          |                    |                    |
          v                    v                    v
       MODELS               ANALYZERS              TOOLS
      reasoning              evidence             operations
     suggestions            extraction            validation
          |                    |                    |
          +--------------------+--------------------+
                               |
                               v
                       PROPOSED OPERATION
                               |
                        AUTHORITY CHECK
                               |
                         POLICY CHECK
                               |
                       CONSTRAINT CHECK
                               |
                           EXECUTION
                               |
                         VALIDATION
                               |
                      COMMIT OR ROLLBACK
                               |
                               v
                 AUTHORITATIVE MUSICAL STATE
                               |
                        REVISION HISTORY
                               |
                +--------------+--------------+
                |              |              |
                v              v              v
             MusicXML       Applications     MIDI
             Adapters        / Computer      Adapters
                               Use
```

This is conceptual, not a command to implement every box immediately.

Preserve the separation.

---

# 5. EVIDENCE IS NOT OBSERVATION

The project must distinguish at least the following conceptual stages:

```text
SOURCE
  ↓
EVIDENCE
  ↓
OBSERVATION
  ↓
INTERPRETATION
  ↓
SUGGESTION / PROPOSAL
  ↓
HUMAN CONFIRMATION OR AUTHORIZED ACTION
  ↓
AUTHORITATIVE INTENT
  ↓
MUTATION
  ↓
NEW AUTHORITATIVE STATE
```

These stages must not be silently collapsed.

## Evidence

Evidence is what the system actually received.

Examples:

- audio samples;
- MIDI events;
- MusicXML;
- pixels from a score image;
- existing notation;
- explicit human instructions.

## Observation

Observation is a machine-derived description of evidence.

Examples:

- estimated fundamental frequency;
- detected onset;
- detected duration;
- existing written pitch;
- apparent note event;
- apparent parallel motion.

Observation is not necessarily objective truth.

Signal processing itself can involve inference.

## Interpretation

Interpretation assigns probable musical meaning.

Examples:

- singer likely intended A4;
- timing deviation appears to be rubato;
- event appears to be a grace note;
- chord appears to function as V7/vi.

Interpretation remains provisional until appropriately confirmed or incorporated into authoritative state.

## Suggestion

Suggestion introduces something not asserted to be the musician's existing intention.

Examples:

- alternate harmony;
- alternate voicing;
- range correction;
- different cadence;
- orchestration idea.

## Change

Change modifies authoritative musical state.

A change requires appropriate authorization.

---

# 6. CONFIRMED HUMAN INTENT OVERRIDES MACHINE INFERENCE

This rule is fundamental.

If the machine interprets a passage as triplets and the musician says:

> No. Those are straight eighth notes. I performed them poorly.

the system may preserve the original performance evidence and machine interpretation for provenance.

It must not continue treating the triplet interpretation as authoritative.

Human correction establishes authoritative intent for that scope unless the musician explicitly reopens the question.

The machine may remember:

- what was performed;
- what it originally inferred;
- what the musician corrected;
- what became authoritative.

It may not repeatedly overwrite confirmed human intention merely because the original evidence continues to support another interpretation.

---

# 7. AUTHORITY MUST BE SCOPED

Do not assume there is always one undifferentiated "musician."

Possible participants include:

- composer;
- arranger;
- performer;
- conductor;
- editor;
- engraver;
- educator;
- rights holder;
- project owner.

Music MCP does not need to adjudicate legal ownership.

It does need an architecture capable of representing scoped authorization.

Example conceptual permissions:

```text
melody:
  modify: forbidden

lyrics:
  modify: forbidden

engraving:
  modify: automatic

accidental_spelling:
  modify: automatic

harmony:
  suggest: allowed
  modify: confirmation_required

orchestration:
  suggest: allowed
  modify: forbidden
```

The architecture must eventually support session-level and operation-level delegation.

A professional user should be capable of saying:

> Automatically fix engraving and notation normalization. Ask before changing pitch or rhythm. Suggest harmony changes but never apply them automatically.

Do not hard-code the artistic/clerical distinction solely according to operation type.

Context matters.

---

# 8. AUTHORIZED OPERATIONS DO NOT IMPLY AUTHORIZATION FOR CONSEQUENTIAL OPERATIONS

This is mandatory.

Example:

The user authorizes:

> Transpose the entire score down a whole step.

The resulting tenor line exceeds a configured range.

The system is authorized to transpose.

It is not automatically authorized to rewrite the tenor line.

Correct behavior:

1. perform or preview the authorized transposition;
2. detect the resulting range violation;
3. report the violation;
4. suggest remedies if permitted;
5. require additional authority before artistically modifying the line.

Never silently broaden authority because doing so produces a more aesthetically pleasing result.

---

# 9. AUTHORITATIVE MUSICAL STATE

Do not treat an external format or application as the unquestioned source of truth.

The project requires the concept of **Authoritative Musical State**, abbreviated conceptually as AMS.

AMS represents what the project currently understands the authorized musical work to be.

This does NOT mean immediately inventing a giant proprietary music file format.

Do not prematurely design one.

The conceptual distinction is nevertheless mandatory.

Possible representations surrounding AMS include:

- source audio;
- MIDI;
- observations;
- interpretations;
- confirmed musical intent;
- MusicXML;
- application-specific state;
- rendered notation;
- exported files.

These are not automatically equivalent.

External formats should generally be treated as adapters or representations.

---

# 10. MUSICXML AND MIDI ARE ADAPTERS, NOT THE CONSTITUTION

Prefer established open standards whenever they adequately represent the required information.

MusicXML should be a major interoperability target.

MIDI should be supported where appropriate.

Neither should define the limits of what Music MCP considers music.

The architecture must not assume:

- 12-tone equal temperament is universal;
- Western common-practice notation is universal;
- meter is always present;
- conventional pitches are always present;
- every musical concept can be represented losslessly by MusicXML;
- every performance can be meaningfully represented by MIDI.

Future support may include:

- microtonality;
- non-Western tuning systems;
- unmetered music;
- graphic notation;
- extended techniques;
- aleatoric structures;
- unconventional temporal structures.

Version 0.1 does not need to implement these.

The architecture must not make them impossible.

Adapters should eventually be capable of declaring results such as:

```text
LOSSLESS
LOSSY
UNSUPPORTED
AMBIGUOUS
```

Representation limitations must never be silently presented as musical limitations.

---

# 11. SILO EVERYTHING THAT CAN FAIL INDEPENDENTLY

This requirement is exceptionally important.

Each major capability must be architecturally isolated.

Examples:

- audio analysis;
- transcription;
- rhythm interpretation;
- pitch interpretation;
- harmony analysis;
- MusicXML;
- MIDI;
- optical music recognition;
- computer-use integration;
- Dorico integration;
- MuseScore integration;
- other notation integrations;
- model providers;
- rendering;
- policy/rights handling.

A module must not become structurally necessary merely because using it is convenient.

If optical music recognition is disabled tomorrow, transcription should continue functioning.

If a computer-use provider changes its API, MusicXML operations should continue functioning.

If a copyright or security policy requires disabling one ingestion pathway, unrelated capabilities should continue functioning.

If a model provider disappears, authoritative musical state must survive.

If Dorico changes its UI, MuseScore integration and structured score operations must survive.

If a transcription dependency becomes insecure, the transcription silo should be removable without destabilizing the core.

A broken stone must not shake the wall.

---

# 12. NO SECRET TUNNELS BETWEEN SILOS

Separate directories are not sufficient isolation.

Modules communicate through explicit, documented contracts.

No module may reach into another module's private implementation because doing so is convenient.

Every significant silo should eventually declare:

- identity;
- version;
- capabilities;
- required inputs;
- guaranteed outputs;
- permissions required;
- state access;
- external dependencies;
- network requirements;
- side effects;
- failure modes;
- security boundary;
- policy/rights considerations;
- data retention behavior;
- rollback guarantees;
- compatibility;
- deprecation behavior.

A competent developer unfamiliar with the original implementation should be capable of replacing a module using its documented contract.

That is a design requirement.

---

# 13. POLICY MUST BE SEPARATE FROM CAPABILITY

Do not scatter copyright, security, provider, or rights-policy logic throughout unrelated musical operations.

Conceptually:

```text
REQUEST
   ↓
CAPABILITY CHECK
   ↓
AUTHORITY CHECK
   ↓
POLICY / RIGHTS CHECK
   ↓
CONSTRAINT CHECK
   ↓
OPERATION
   ↓
POST-VALIDATION
   ↓
COMMIT
```

A capability answers:

> Can this operation technically be performed?

Authority answers:

> Has this actor authorized the operation?

Policy answers:

> Is this operation permitted under applicable configured policy?

Constraints answer:

> What musical or project rules govern the operation?

These questions must remain separable.

---

# 14. CONSTRAINTS ARE FIRST-CLASS OBJECTS

Do not bury musical constraints inside prompts.

The system should eventually support explicit constraints such as:

```text
Soprano range: C4-G5
Alto range: G3-D5
Tenor range: C3-G4
Bass range: E2-C4

Melody: locked
Lyrics: locked

Harmony:
  suggestions_allowed

Voice crossing:
  prohibited

Parallel fifths:
  warn

Ruleset:
  traditional SATB
```

Constraints should have provenance.

A constraint may originate from:

- user;
- composer;
- arranger;
- institution;
- imported project;
- selected style profile;
- AI suggestion.

A theoretical rule must not be silently presented as universal musical law.

For example:

Correct:

> Parallel perfect fifth motion detected. This violates the currently enabled traditional SATB rule.

Incorrect:

> Your music contains an error.

Separate observation from ruleset evaluation.

---

# 15. CHANGES MUST BE TRANSACTIONAL

Consequential modifications should conceptually follow:

```text
PRECONDITIONS
     ↓
AUTHORITY
     ↓
POLICY
     ↓
CONSTRAINTS
     ↓
TRANSACTION
     ↓
POSTCONDITIONS
     ↓
VALIDATION
     ↓
COMMIT OR ROLLBACK
```

A partially modified authoritative score must not be casually left behind after an operation fails.

Where technically practical:

- preview;
- apply;
- validate;
- commit;
- rollback;
- compare;
- restore

must be supported.

"Undo" alone is not sufficient architecture.

---

# 16. REVISION HISTORY AND PROVENANCE

Authoritative musical state should eventually support immutable or equivalently trustworthy revision history.

The system should be able to answer questions such as:

- What did the AI change?
- What did the human change?
- Which material came from the original performance?
- Which material was inferred?
- Which material was generated?
- Which suggestion was accepted?
- When did this note change?
- Why did it change?
- Under whose authority?
- What constraints were active?
- Can the prior state be restored?

Do not throw away provenance merely because the current score looks correct.

---

# 17. MACHINE-GENERATED MUSIC MUST BE IDENTIFIABLE

Music MCP is not categorically anti-generation.

A musician may explicitly request:

> Suggest three alternate cadences.

or:

> Generate four possible alto lines.

or:

> Reharmonize these eight measures.

That is allowed conceptually.

However, generated musical material must remain distinguishable from:

- source material;
- observed material;
- interpreted human intention;
- explicit human-authored modifications.

Human acceptance of a generated suggestion may promote it into authoritative musical state.

Its provenance should remain knowable.

---

# 18. ERROR HANDLING IS A FIRST-CLASS PRODUCT FEATURE

Error handling must be designed to an unusually high standard.

The ambition is for Music MCP's error-handling model to become an example other projects would want to imitate.

Do not implement generic errors where meaningful domain-specific information is available.

Avoid useless results such as:

```text
Error 500
Operation failed
Something went wrong
```

Every significant failure should answer:

1. What happened?
2. Why did it happen?
3. What was affected?
4. Was authoritative state changed?
5. Is the musical state currently safe?
6. Was rollback attempted?
7. Did rollback succeed?
8. What should the human do next?
9. What technical information does a developer need?
10. What event/trace identifier can connect the user-facing event to technical diagnostics?

Errors should have two complementary representations.

## Human-facing representation

Example:

> I couldn't confidently determine the rhythm in measure 14. Two interpretations fit the performance closely. Nothing was changed. Review the alternatives or leave this passage unresolved.

## Technical representation

Example:

```text
MUSICMCP-INTERPRET-RHYTHM-AMBIGUOUS

Severity: REVIEW
Module: rhythm.interpretation
Operation: interpret_performance
Scope: measure 14

Authoritative State Modified: NO
Rollback Required: NO
State Safe: YES

Reason:
Timing evidence does not sufficiently distinguish
between two plausible rhythmic interpretations.

Candidate A:
dotted-quarter + eighth

Candidate B:
quarter + quarter

Recommended Action:
Request human selection.

Trace:
event-8392
source-audio-014
revision-22
```

Both describe the same event.

The human message must not lie or hide relevant consequences.

The technical message must not require the user to understand implementation internals.

---

# 19. ERROR TAXONOMY

Begin designing a formal taxonomy around categories such as:

```text
SUCCESS
SUCCESS_WITH_WARNINGS

REVIEW_REQUIRED
AMBIGUOUS
INSUFFICIENT_EVIDENCE

UNAUTHORIZED
CONSTRAINT_CONFLICT
AUTHORITY_CONFLICT

UNSUPPORTED
CAPABILITY_UNAVAILABLE
DEPENDENCY_UNAVAILABLE

LOSSY_OPERATION
LOSSY_EXPORT

VALIDATION_FAILED
TRANSACTION_FAILED
ROLLBACK_FAILED

SECURITY_BLOCKED
POLICY_BLOCKED
RIGHTS_RESTRICTED

INTERNAL_FAILURE
```

Do not assume this list is final.

Refine it deliberately.

Failure is a legitimate result.

`PARTIAL` behavior, if supported, must explicitly identify what succeeded, what failed, and the resulting state.

Never silently report partial success as success.

---

# 20. FAILURE CONTAINMENT

Every module must fail as locally as practical.

A transcription crash should not corrupt authoritative musical state.

A Dorico adapter failure should not disable MusicXML.

An unavailable AI provider should not make deterministic score transformations unavailable.

A broken harmony analyzer should not prevent score reading.

A security block in one adapter should not automatically disable unrelated adapters.

Dependency failures must propagate through explicit error contracts rather than unpredictable cascading behavior.

---

# 21. CAPABILITY DISCOVERY

Implementations will not all support identical capabilities.

A connected model must not guess.

Music MCP should eventually expose discoverable information describing:

- supported operations;
- supported formats;
- supported MusicXML versions;
- tuning capabilities;
- available analyzers;
- available adapters;
- read/write capabilities;
- transactional guarantees;
- validation capabilities;
- model-dependent capabilities;
- network-dependent capabilities;
- disabled modules;
- degraded modules;
- policy restrictions.

The system should be capable of answering:

> What can you safely do right now?

---

# 22. DETERMINISM AND IDEMPOTENCY

Where operations are fundamentally deterministic and clerical, prefer reproducibility.

Examples may include:

- deterministic transposition;
- part extraction;
- deterministic format normalization;
- validation;
- range checking.

Where appropriate:

same authoritative state  
+ same operation  
+ same parameters  
+ same constraints  
= same result.

Operations should be idempotent where the semantics permit it.

AI interpretation and generation do not need to pretend to be deterministic.

Do not blur these categories.

---

# 23. UNCERTAINTY

Do not introduce arbitrary numeric confidence values into the core specification.

A value such as:

```text
confidence: 0.9137
```

is meaningless unless its semantics and calibration are defined.

Prefer structured uncertainty.

Potential dimensions include:

- evidence quality;
- signal confidence;
- interpretive ambiguity;
- model confidence;
- constraint certainty;
- review requirement.

Useful states may include:

```text
HIGH
MEDIUM
LOW
AMBIGUOUS
UNRESOLVED
INSUFFICIENT_EVIDENCE
```

Implementations may eventually provide calibrated numerical values, but the protocol must not institutionalize fake precision.

"I don't know" is a valid and useful result.

---

# 24. FIRST REFERENCE USE CASE

Do not begin by attempting to build the entire vision.

The first reference use case is:

> **A human performs a monophonic musical phrase and the system assists in converting that performance into intended symbolic notation while preserving evidence, interpretation, uncertainty, human correction, and provenance.**

Conceptually:

```text
PERFORMANCE
     ↓
EVIDENCE
     ↓
OBSERVATION
     ↓
PITCH / TIMING / EVENT ANALYSIS
     ↓
INTERPRETATION
     ↓
UNCERTAINTY IDENTIFICATION
     ↓
HUMAN CONFIRMATION / CORRECTION
     ↓
AUTHORITATIVE MUSICAL INTENT
     ↓
STRUCTURED SCORE REPRESENTATION
```

Do not initially attempt:

- complete orchestration;
- arbitrary polyphonic transcription;
- full optical music recognition;
- full Dorico automation;
- full MuseScore automation;
- autonomous composition;
- giant GUI;
- complete professional engraving;
- every music-theory system;
- every historical notation system.

Architect for expansion.

Implement narrowly.

---

# 25. ADVERSARIAL MUSICAL TEST CASES

The architecture and eventual reference implementation must account for cases including:

## Vibrato

A sustained note contains periodic pitch modulation.

The system must not blindly turn every pitch excursion into separate notes.

## Pitch drift

A singer performs slightly above or below a target pitch.

Measured performance and probable intended pitch must remain distinguishable.

## Deliberately inaccurate performance

A musician intentionally sings an unreachable melody imperfectly while asking for intended notation.

The system must support task context.

## Literal transcription

The same musician may instead request exact transcription of performed pitch deviations.

The system must not assume every transcription request means "correct me."

## Rubato

Expressive timing must not automatically become bizarre rhythmic notation or unnecessary meter changes.

## Breath

A vocal breath does not automatically equal a written rest.

## Grace notes and ornaments

Short expressive events should not automatically become ordinary equal-status notes.

## Ambiguous rhythm

Multiple plausible notations may exist.

Expose ambiguity.

## Enharmonic ambiguity

C-sharp and D-flat may sound equivalent under a tuning system while carrying different harmonic meaning.

Use context without pretending uncertainty does not exist.

## Pickup measures

Do not force an anacrusis into an inappropriate complete opening measure.

## Human correction

Once the musician establishes intended notation, subsequent analysis must not silently overwrite it.

## Transposition with consequences

A requested transposition may create range violations.

Do not silently revoice without authorization.

## Multiple model disagreement

Different analyzers or models may disagree.

Do not establish model supremacy merely because one provider produced the answer.

Preserve competing interpretations when necessary.

---

# 26. DOCUMENTATION IS PART OF THE ARCHITECTURE

This project has unusually strong documentation requirements.

Documentation is not cleanup performed after implementation.

It is part of implementation.

The project owner deliberately uses documentation as external working memory and as a continuity mechanism between human work sessions and AI agents.

No important architectural decision may exist solely inside a chat transcript.

No agent may rely upon its current conversation context as the sole repository of project state.

If information matters tomorrow, persist it appropriately today.

---

# 27. REQUIRED ROOT DOCUMENTATION

Establish and maintain the following root documents.

## README.md

Project introduction.

Explain:

- what Music MCP is;
- what it is not;
- current status;
- architecture at a high level;
- how to navigate the repository;
- how to begin contributing.

## PHILOSOPHY.md

The constitution.

Preserve:

- human artistic authority;
- model agnosticism;
- application agnosticism;
- provenance;
- reversibility;
- explicit authorization;
- distinction between evidence, interpretation, generation, and change.

Do not casually modify founding principles.

## SPECIFICATION.md

Normative behavioral requirements for Music MCP.

Use clear normative language where appropriate:

- MUST;
- MUST NOT;
- SHOULD;
- SHOULD NOT;
- MAY.

Keep philosophy and implementation detail appropriately separated.

## ARCHITECTURE_PRINCIPLES.md

Define the stone-wall engineering rules.

Include:

- silo architecture;
- dependency direction;
- state ownership;
- module contracts;
- failure containment;
- transactions;
- rollback;
- authority;
- policy separation;
- constraint handling;
- adapter boundaries;
- replaceability;
- versioning;
- compatibility;
- security isolation;
- deprecation;
- documentation requirements.

## AGENTS.md

Instructions every AI coding agent must read before modifying the repository.

Include:

- required reading order;
- architectural prohibitions;
- documentation responsibilities;
- testing expectations;
- handoff requirements;
- rules against undocumented shortcuts;
- rules against cross-silo coupling;
- requirement to update decision logs when architectural reasoning changes;
- requirement to leave exact continuation information before stopping;
- canonical GitHub sync rules from Section 0.

## whats_and_hows_log.md

This is institutional memory.

Record significant decisions and, most importantly, **why they were made**.

Entries should capture:

- date;
- decision;
- context;
- alternatives considered;
- why the chosen approach won;
- consequences;
- relevant files/modules;
- unresolved concerns.

The purpose is to prevent future humans or agents from unknowingly reopening settled architectural battles without understanding why previous decisions were made.

Do not turn this into a noisy commit log.

Significant reasoning belongs here.

## handoff.md

This is working memory.

It acts like a time card and work-state transfer between agents and sessions.

Every agent beginning significant work should read it.

Every agent stopping incomplete work should update it.

Include:

- current milestone;
- current task;
- agent/session identifier if available;
- start time;
- stop time;
- objective;
- work completed;
- current work;
- files modified;
- tests executed;
- passing tests;
- failing tests;
- known problems;
- decisions made;
- decisions still needed;
- do-not-repeat information;
- last known good state;
- exact next action;
- reason work stopped;
- local branch;
- remote tracking branch;
- local HEAD commit;
- remote HEAD commit observed at session start/end;
- sync state: clean / ahead / behind / diverged / dirty;
- whether unpushed commits or untracked files remain.

"Continue working on transcription" is unacceptable.

Prefer:

> Open `X`. Test `Y` currently fails because `Z`. Inspect `A` before changing fixture `B`.

A new agent with no conversational context should be able to resume.

## goals_and_dreams.md

This is the idea vault.

Capture:

- rabbit holes;
- ambitious future capabilities;
- experimental ideas;
- possible integrations;
- wild ideas;
- long-term possibilities;
- features that may become important later;
- interesting discoveries that should not be forgotten.

Sacred rule:

> **Nothing in goals_and_dreams.md is a commitment. Nothing valuable gets forgotten.**

Do not allow speculative ideas in this file to silently become requirements.

Ideas graduate into specifications or roadmaps only through deliberate decision.

## ERRORS.md

Define the canonical error-handling system.

Include:

- taxonomy;
- error identifiers;
- severities;
- human-facing requirements;
- technical diagnostic requirements;
- state-safety reporting;
- recovery guidance;
- traceability;
- module attribution;
- transaction status;
- rollback status;
- examples;
- requirements for adding new errors.

## error_history_log.md

Record significant historical failures.

Include:

- error identifier;
- date discovered;
- affected version/module;
- symptom;
- root cause;
- user impact;
- state impact;
- fix;
- regression test;
- lessons learned;
- whether architectural/documentation changes resulted.

This is not merely a bug list.

It is institutional memory about failure.

## CONTRIBUTING.md

Explain safe contribution procedures for humans and agents.

## CHANGELOG.md

Track released behavioral changes.

Do not substitute this for `whats_and_hows_log.md`.

CHANGELOG answers:

> What changed?

The decision log answers:

> Why did we choose this?

## SECURITY.md

Document:

- trust boundaries;
- vulnerability reporting;
- secrets handling;
- dependency security;
- module isolation;
- permissions;
- external provider risks;
- security-related module disabling;
- authoritative-state protection.

## CONFORMANCE.md

Define what a server, module, adapter, or implementation must prove before claiming compatibility.

## DEPRECATION.md

Define how:

- modules;
- tools;
- contracts;
- schemas;
- error codes;
- adapters;
- capabilities

are deprecated and retired without destabilizing dependent systems.

---

# 28. MODULE-LEVEL DOCUMENTATION

Major silos should carry local documentation rather than forcing root documentation to contain implementation trivia.

A typical significant module may contain:

```text
README.md
CONTRACT.md
AGENTS.md
whats_and_hows_log.md
handoff.md
```

and module-specific error documentation/history when warranted.

Root documentation contains project-wide truth.

Module documentation contains local truth.

Do not duplicate large amounts of information unnecessarily.

Link upward to governing requirements.

---

# 29. DOCUMENTATION PROMOTION MODEL

Use this conceptual information lifecycle:

```text
ACTIVE SESSION
     ↓
handoff.md
     ↓
whats_and_hows_log.md
     ↓
ARCHITECTURE_PRINCIPLES.md
     ↓
SPECIFICATION.md
```

Not every thought travels through every stage.

The idea is that information becomes increasingly authoritative as it matures.

Separately:

```text
RABBIT HOLE / FUTURE IDEA
          ↓
goals_and_dreams.md
          ↓
 deliberate evaluation
          ↓
specification / roadmap / rejection
```

Do not allow temporary conversational thinking to become accidental architecture.

---

# 30. DOCUMENTATION QUALITY GATE

A feature is not complete merely because the code works.

A stable feature must be understandable, operable, diagnosable, replaceable, and maintainable by someone other than its original developer.

Before a significant module or capability reaches stable status, require appropriate documentation of:

- purpose;
- contract;
- inputs;
- outputs;
- dependencies;
- permissions;
- state access;
- side effects;
- error modes;
- recovery;
- security implications;
- policy implications;
- known limitations;
- compatibility;
- migration;
- deprecation;
- tests.

Where practical, automated checks should detect documentation omissions associated with contract or behavioral changes.

---

# 31. CONFORMANCE TESTING

Examples are not tests.

Build toward a formal conformance suite.

Potential mandatory failures include:

- modifying locked melody;
- losing required provenance;
- performing unauthorized mutation;
- silently performing lossy conversion;
- reporting failed rollback as successful;
- leaving authoritative state partially mutated after transaction failure;
- representing machine-generated material as original human material;
- ignoring explicit human correction;
- allowing one silo failure to corrupt unrelated state;
- introducing undeclared cross-module dependencies.

A future third-party implementation claiming Music MCP compatibility should be testable against published behavior.

---

# 32. ERROR HISTORY MUST INFORM ARCHITECTURE

When a significant bug occurs, do not merely patch it.

Ask:

1. Why was this possible?
2. Which architectural assumption permitted it?
3. Could another module contain the same class of defect?
4. Should a contract change?
5. Should a conformance test be added?
6. Should an error code be added or refined?
7. Should documentation change?
8. Should an architecture principle be established?

The purpose of `error_history_log.md` is partly to ensure that the same class of failure becomes progressively harder to repeat.

---

# 33. DEPENDENCY DISCIPLINE

Treat external dependencies as replaceable infrastructure.

For each meaningful dependency, know:

- why it exists;
- what capability requires it;
- what version assumptions exist;
- what happens when it is unavailable;
- what happens when it changes behavior;
- whether it accesses the network;
- whether it handles user data;
- whether licensing restrictions exist;
- whether policy restrictions may affect it;
- what alternative could replace it.

Do not allow an optional external dependency to leak throughout the core architecture.

Wrap it behind the appropriate silo contract.

---

# 34. SECURITY AND COPYRIGHT/POLICY CHANGE RESILIENCE

Assume that external conditions will change.

A dependency may develop a vulnerability.

A provider may change terms.

An API may disappear.

A security policy may prohibit a capability.

Copyright interpretation or platform policy may change.

A jurisdiction may impose different requirements.

The system must be capable of disabling or replacing affected capabilities without collapsing unrelated functionality.

Do not architect the system around today's policy assumptions as if they are immutable technical truths.

---

# 35. AGENT CONTINUITY

This repository is expected to be developed with significant assistance from AI coding agents.

Agents have finite context.

Sessions end.

Models change.

Different agents may approach problems differently.

Therefore repository state must be sufficient to reconstruct development state.

Before an agent performs significant work:

1. verify repository remote/sync state against `https://github.com/CrackenReleased/MusicMCP.git`;
2. read root `AGENTS.md`;
3. read `PHILOSOPHY.md`;
4. read relevant portions of `SPECIFICATION.md`;
5. read `ARCHITECTURE_PRINCIPLES.md`;
6. read root `handoff.md`;
7. read relevant module `AGENTS.md`;
8. read relevant module `handoff.md`;
9. inspect relevant `whats_and_hows_log.md` entries;
10. inspect tests and contracts before modifying behavior.

Before stopping incomplete work:

1. return repository to the safest practical state;
2. run appropriate tests;
3. document failures honestly;
4. update relevant logs;
5. update `handoff.md`;
6. identify the exact next action;
7. record local and remote commit/sync state;
8. clearly state whether unpushed work remains.

Do not leave critical reasoning only inside the agent's response to the human.

---

# 36. NO HERO DEVELOPERS

The project should not require one particular developer, agent, founder, or model to remain maintainable.

Design toward this standard:

> **Nobody should be indispensable to Music MCP, including its founders.**

If replacing a module requires asking its original developer how it secretly works, the module is insufficiently documented or insufficiently isolated.

If understanding an architectural choice requires finding an old chat conversation, project memory has failed.

If a new agent cannot determine where work stopped, handoff discipline has failed.

---

# 37. INITIAL REPOSITORY SHAPE

Do not treat this as permanently fixed, but begin with a clean structure approximately like:

```text
music-mcp/
│
├── README.md
├── PHILOSOPHY.md
├── SPECIFICATION.md
├── ARCHITECTURE_PRINCIPLES.md
├── AGENTS.md
├── whats_and_hows_log.md
├── handoff.md
├── goals_and_dreams.md
├── ERRORS.md
├── error_history_log.md
├── CONTRIBUTING.md
├── CHANGELOG.md
├── SECURITY.md
├── CONFORMANCE.md
├── DEPRECATION.md
│
├── docs/
│
├── spec/
│   ├── authority/
│   ├── permissions/
│   ├── evidence/
│   ├── observations/
│   ├── interpretations/
│   ├── suggestions/
│   ├── changes/
│   ├── uncertainty/
│   ├── provenance/
│   ├── constraints/
│   ├── transactions/
│   └── errors/
│
├── modules/
│   └── [future isolated capabilities]
│
├── adapters/
│   └── [future external format/application adapters]
│
├── tests/
│   ├── conformance/
│   ├── architecture/
│   └── musical_intention/
│
└── reference/
    └── [future reference MCP implementation]
```

Do not create empty directory theater merely to make the repository look impressive.

Create directories when they have meaningful content or immediate architectural value.

---

# 38. IMPLEMENTATION LANGUAGE

Do not choose implementation language merely because it is convenient for the current agent.

Before establishing the reference implementation language, evaluate:

- MCP ecosystem maturity;
- audio/music library ecosystem;
- schema validation;
- type safety;
- testing;
- packaging;
- cross-platform support;
- maintainability;
- contributor accessibility;
- security;
- long-term ecosystem stability.

Document the decision in `whats_and_hows_log.md`.

If the repository already contains a documented language decision, obey it unless explicitly authorized to reconsider it.

---

# 39. DO NOT PREMATURELY BUILD AN INTERNAL MUSIC FORMAT

The project likely requires richer internal semantics than MusicXML or MIDI alone can provide.

That does not authorize immediate invention of a giant custom notation format.

Begin by defining the concepts the system must preserve:

- identity;
- evidence;
- musical events;
- provenance;
- interpretation;
- authoritative intent;
- constraints;
- uncertainty;
- revisions;
- operations.

Only create representation structures necessary for the current reference use case.

Allow the representation to grow through demonstrated requirements and adversarial tests.

Document every expansion.

---

# 40. FIRST BUILD PHASE

Your initial task is NOT to implement every capability described above.

Your initial task is to turn these founding requirements into a coherent repository that another competent developer or AI agent could understand and continue.

Proceed approximately in this order:

1. Inspect the current repository completely before changing anything.
2. Compare local state against the canonical GitHub repository.
3. Preserve existing useful work.
4. Identify conflicts between existing implementation and this directive.
5. Establish the documentation hierarchy.
6. Draft/refine `PHILOSOPHY.md`.
7. Draft/refine `SPECIFICATION.md`.
8. Create `ARCHITECTURE_PRINCIPLES.md`.
9. Create `AGENTS.md`.
10. Establish `whats_and_hows_log.md`.
11. Establish `handoff.md`.
12. Establish `goals_and_dreams.md`.
13. Establish `ERRORS.md`.
14. Establish `error_history_log.md`.
15. Establish security, conformance, contribution, change, and deprecation documentation.
16. Define the first architectural contracts.
17. Define the initial error model.
18. Define initial authority/permission concepts.
19. Define initial provenance concepts.
20. Define initial transaction semantics.
21. Create adversarial/conformance tests around architectural invariants.
22. Only then begin the smallest useful reference implementation necessary to exercise those contracts.

Do not blindly perform these steps if the repository already contains mature equivalents.

Inspect first.

Integrate rather than duplicate.

---

# 41. BEFORE WRITING SUBSTANTIAL CODE

Produce an architectural assessment.

Record:

## Existing State

What currently exists locally and remotely?

## Sync State

Is local state synchronized with the canonical GitHub repository?

Identify:

- local branch;
- local HEAD;
- remote branch;
- remote HEAD;
- ahead/behind/diverged status;
- uncommitted changes;
- untracked files;
- unpushed commits.

## Conflicts

What contradicts the founding principles?

## Missing Foundations

What must exist before safe implementation?

## Proposed First Milestone

What is the smallest coherent slice that proves the architecture?

## Risks

What decisions would be expensive to reverse?

## Open Questions

What genuinely requires human judgment?

Do not ask the human to decide trivial implementation details that can safely be researched, tested, documented, and reversed.

Do ask before making decisions that materially change:

- project philosophy;
- authority model;
- canonical state philosophy;
- public compatibility;
- security model;
- licensing;
- irreversible repository structure;
- major scope.

---

# 42. WHEN YOU DISAGREE WITH THIS DIRECTIVE

Do not blindly obey an architectural instruction you can demonstrate is technically unsound.

Challenge it.

But challenge it explicitly.

Document:

```text
CURRENT REQUIREMENT:
...

PROBLEM:
...

EVIDENCE:
...

PROPOSED ALTERNATIVE:
...

TRADEOFFS:
...

MIGRATION CONSEQUENCES:
...
```

Do not quietly replace the requirement with your preferred design.

The human project owner retains authority over architectural direction.

---

# 43. WHEN YOU DISCOVER A GOOD IDEA OUTSIDE CURRENT SCOPE

Do not implement it because it is exciting.

Put it in:

`goals_and_dreams.md`

Include enough information that another person can understand why the idea mattered.

Then return to the current milestone.

This project deliberately preserves rabbit holes without allowing them to steer construction accidentally.

---

# 44. WHEN YOU DISCOVER WHY SOMETHING WAS DONE

If you discover reasoning that future agents are likely to question, preserve it in:

`whats_and_hows_log.md`

Do not merely document:

> We used X.

Document:

> We used X because Y. We considered Z. Z was rejected because A and B. This decision may need reconsideration if C changes.

That is the standard.

---

# 45. WHEN YOU STOP WORK

Before ending a work session, update `handoff.md`.

Do this even if you expect the same model or developer to return.

Assume they will not.

Leave breadcrumbs good enough that an unfamiliar competent agent can resume without guessing.

The final entry must contain an **exact next action** whenever work remains incomplete.

Also record sync state against the canonical GitHub repository so the next agent can distinguish:

- work that exists only locally;
- work already committed locally;
- work already pushed remotely;
- remote work not yet incorporated locally.

---

# 46. DEFINITION OF DONE

"Works on my machine" is not done.

"Demo succeeds" is not done.

"Tests pass" alone is not done.

For stable work, Done means the relevant combination of:

- behavior implemented;
- contract defined;
- authority respected;
- constraints respected;
- failure modes defined;
- state protected;
- rollback considered;
- errors understandable;
- tests passing;
- adversarial tests passing;
- documentation current;
- provenance preserved;
- security implications considered;
- dependency boundaries respected;
- handoff current;
- local/remote sync state known;
- architectural reasoning recorded where necessary.

The exact burden should remain proportional to the feature.

Do not turn a three-line internal helper into a bureaucratic ceremony.

Apply rigor where failure matters.

---

# 47. QUALITY STANDARD

Favor boring reliability over cleverness.

Favor explicit contracts over implicit behavior.

Favor small replaceable components over sprawling convenience abstractions.

Favor observable failures over silent recovery.

Favor preserved evidence over destructive interpretation.

Favor reversible changes over irreversible mutation.

Favor human-readable diagnostics over opaque error codes.

Favor machine-readable diagnostics over prose-only errors.

Favor compatibility over unnecessary reinvention.

Favor documented decisions over tribal knowledge.

Favor tests that attack assumptions over tests that merely demonstrate happy paths.

Favor graceful degradation over cascading failure.

Favor refusing an unsafe operation over corrupting authoritative state.

Favor explicit local/remote sync reporting over assumptions.

And when forced to choose between shipping quickly and weakening a foundational invariant:

**protect the invariant.**

---

# 48. THE TEST FOR EVERY ARCHITECTURAL DECISION

Before introducing a dependency, module, abstraction, data structure, or capability, ask:

> If this component disappears, breaks, becomes insecure, changes its API, changes its license, becomes legally unusable, or is replaced five years from now, how much of Music MCP moves with it?

The preferred answer is:

> **Only its silo.**

Then ask:

> If an AI model behaves incorrectly, can it corrupt authoritative musical state?

The preferred answer is:

> **No.**

Then:

> If an operation fails halfway through, can we determine exactly what happened and whether the user's music is safe?

The answer must be:

> **Yes.**

Then:

> If every person currently working on this project disappears tomorrow, can competent strangers understand why the system was built this way and continue responsibly?

The answer should eventually be:

> **Yes.**

Then:

> Can a new local agent determine whether its checkout matches the canonical GitHub repository without guessing?

The answer must be:

> **Yes.**

That is the wall.

---

# 49. THE FIRST PRINCIPLE TO REMEMBER WHEN EVERYTHING ELSE GETS COMPLICATED

There will eventually be thousands of decisions.

There will be new models.

New music software.

New standards.

New contributors.

New policies.

New security problems.

New musical edge cases.

New capabilities nobody involved today can anticipate.

When complexity makes the correct decision unclear, return here:

> **The musician stays the artist. The machine does the notation, calculation, and clerical work.**

Then apply:

> **Human intent is authoritative. Machine inference is provisional. Machine creation is identifiable. Machine modification is authorized.**

Then protect:

> **Evidence. Authority. Provenance. Reversibility. Isolation. Explainability.**

Build outward from there.

---

# 50. BEGIN

Read the repository.

Confirm the canonical remote is:

`https://github.com/CrackenReleased/MusicMCP.git`

Fetch and compare local state to remote before significant work.

Do not immediately generate the full implementation.

First determine what already exists and what state it is in.

Then create or refine the foundational documentation and architecture required by this directive.

Record important reasoning in `whats_and_hows_log.md`.

Record speculative ideas in `goals_and_dreams.md`.

Maintain `handoff.md` throughout the work.

When uncertainty affects foundational architecture, surface it rather than silently inventing policy.

When an implementation decision is safely reversible and consistent with the documented architecture, make the decision, test it, and document why.

When you find a weakness in this architecture, attack it before building on top of it.

Do not protect the proposal from criticism.

Protect the project from the proposal's mistakes.

We are not trying to prove that the founders were right.

We are trying to build something that remains right after the founders are gone.

**Build the wall.**
