"""Provider-Neutral Evaluation Contract and Types for Music MCP.

Adheres strictly to Python 3.11+ standard library only: dataclasses, enum, uuid, time, typing.
Defines atomic evaluation requests, results, probability distributions, provenance,
and incremental evidence windows.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
import time
from typing import Any, Mapping, Sequence
from uuid import uuid4

from reference.core import Diagnostic, MusicError, Note

VERSION = "0.1.01"


class EvaluationType(Enum):
    """Supported provider-neutral evaluation types."""
    BOOLEAN = "BOOLEAN"
    CHOICE = "CHOICE"
    SCORE = "SCORE"
    ALIGNMENT = "ALIGNMENT"


class EvaluationStatus(Enum):
    """Outcome status of an evaluation."""
    SUCCESS = "SUCCESS"
    CAPABILITY_UNAVAILABLE = "CAPABILITY_UNAVAILABLE"
    AMBIGUOUS = "AMBIGUOUS"
    UNRESOLVED = "UNRESOLVED"
    ERROR = "ERROR"


@dataclass(frozen=True)
class ProbabilityDistribution:
    """Explicit probability distribution across candidates with calibration status."""
    probabilities: Mapping[str, float]
    calibrated: bool = False

    def __post_init__(self):
        total = sum(self.probabilities.values())
        if not (0.95 <= total <= 1.05):
            raise ValueError(f"Probabilities must sum to approximately 1.0 (got {total:.4f}).")


@dataclass(frozen=True)
class EvaluationProvenance:
    """Immutable audit trail for every external or deterministic judgment."""
    provider: str
    model: str
    timestamp: float = field(default_factory=time.time)
    latency_ms: float = 0.0
    credentials_configured: bool = False
    contract_version: str = VERSION


@dataclass(frozen=True)
class EvaluationRequest:
    """Atomic, provider-neutral evaluation request."""
    question: str
    evaluation_type: EvaluationType
    candidates: tuple[str, ...] = ()
    context: Mapping[str, Any] = field(default_factory=dict)
    request_id: str = field(default_factory=lambda: uuid4().hex)

    def __post_init__(self):
        if not self.question.strip():
            raise ValueError("Evaluation question must be non-empty text.")
        if self.evaluation_type in (EvaluationType.CHOICE, EvaluationType.ALIGNMENT) and not self.candidates:
            raise ValueError(f"Candidates are required for evaluation type '{self.evaluation_type.value}'.")


@dataclass(frozen=True)
class EvaluationResult:
    """Normalized evaluation result with provenance and qualitative uncertainty."""
    request_id: str
    provenance: EvaluationProvenance
    status: EvaluationStatus
    decision: Any  # bool, str, or float
    probabilities: ProbabilityDistribution | None = None
    uncertainty: str = "LOW"
    explanation: str = ""


@dataclass(frozen=True)
class DetectedEvent:
    """Incremental detected acoustic musical event within an evidence window."""
    event_id: str
    onset_seconds: float
    duration_seconds: float
    pitch_candidates: tuple[tuple[str, str], ...]  # Tuple of (pitch, evidence_strength)
    magnitude: float = 1.0


@dataclass(frozen=True)
class EvidenceWindow:
    """Bounded temporal evidence window for incremental listening and live score following."""
    source_id: str
    start_seconds: float
    end_seconds: float
    detected_events: tuple[DetectedEvent, ...] = ()
    score_context: Mapping[str, Any] = field(default_factory=dict)
    window_id: str = field(default_factory=lambda: uuid4().hex)

    def __post_init__(self):
        if self.end_seconds <= self.start_seconds:
            raise ValueError("EvidenceWindow end_seconds must be strictly greater than start_seconds.")


class EvaluationProvider(ABC):
    """Abstract provider-neutral boundary for musical evaluation and interpretation."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier."""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Provider implementation version."""
        pass

    @abstractmethod
    def capabilities(self) -> dict[str, bool]:
        """Declared provider capabilities."""
        pass

    @abstractmethod
    def evaluate(self, request: EvaluationRequest) -> EvaluationResult:
        """Execute an atomic evaluation request."""
        pass
