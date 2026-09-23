"""Host-Held Interactive Review Shell and Command Line Interface for Music MCP.

Adheres strictly to Python 3.11+ standard library only: argparse, sys, pathlib, json, fractions.
This CLI is designed for direct host execution by human musicians and producers.
It holds privileged AuthoritySessions that are NEVER exposed over network or MCP transports.
"""
import argparse
from fractions import Fraction
from pathlib import Path
import sys
from typing import Sequence

from reference.adapters.midi import midi_to_phrase, phrase_to_midi
from reference.adapters.musicxml import musicxml_to_phrase, phrase_to_musicxml
from reference.analyzer import analyze_monophonic_wav
from reference.core import (
    Grant,
    LockConstraint,
    MusicError,
    Note,
    Producer,
    create_workspace,
    phrase,
)
from reference.spectrum import BAND_LIMITS, watch_audio_bytes
from reference.storage.sqlite_store import SqliteStorageEngine, StorageError

CLI_PRODUCER = Producer("host-musicmcp-cli", "0.1.01")


def parse_notes_string(s: str) -> tuple[Note, ...]:
    """Parses user input string like 'C4 1, E4 1/2, G4 1/2, rest 1' into validated phrase."""
    if "," in s:
        items = [item.strip() for item in s.split(",") if item.strip()]
    else:
        parts = s.split()
        if len(parts) % 2 != 0:
            raise ValueError("Notes string must consist of pitch and duration pairs (e.g. 'C4 1 E4 1/2').")
        items = [f"{parts[i]} {parts[i+1]}" for i in range(0, len(parts), 2)]

    notes_list = []
    for item in items:
        toks = item.split()
        if len(toks) != 2:
            raise ValueError(f"Invalid note token '{item}'. Expected format 'Pitch Duration' (e.g. 'C4 1').")
        pitch, dur_str = toks[0], toks[1]
        try:
            dur = Fraction(dur_str)
        except ValueError:
            raise ValueError(f"Invalid duration fraction '{dur_str}' in note '{item}'.")
        notes_list.append(Note(pitch=pitch, duration=dur))

    return phrase(notes_list)


def format_phrase(notes: Sequence[Note]) -> str:
    return ", ".join(f"{n.pitch} ({n.duration})" for n in notes)


# CLI Subcommand handlers

def cmd_init(args: argparse.Namespace) -> int:
    path = Path(args.project)
    if path.exists() and not args.force:
        print(f"Error: Project file already exists at {path}. Use --force to overwrite.", file=sys.stderr)
        return 1

    artist = args.artist or "lead-artist"
    default_scopes = set(args.scopes.split(",")) if args.scopes else {"melody"}

    grants = [Grant(actor=artist, scopes=default_scopes, operations={"confirm", "correct", "restore"})]
    constraints = tuple(LockConstraint(scope=s.strip(), origin=artist, reason="Initial project constraint")
                        for s in args.lock.split(",")) if args.lock else ()

    ws, _ = create_workspace(grants=grants, constraints=constraints)
    report = SqliteStorageEngine.save_workspace(ws, path, force=args.force)
    print(f"[OK] Initialized new Music MCP project: {path}")
    print(f"     Artist: {artist} | Scopes: {sorted(default_scopes)}")
    if constraints:
        print(f"     Locked scopes: {[c.scope for c in constraints]}")
    return 0


def cmd_info(args: argparse.Namespace) -> int:
    path = Path(args.project)
    if not path.exists():
        print(f"Error: Project file not found at {path}", file=sys.stderr)
        return 1

    # Run integrity audit
    integ = SqliteStorageEngine.verify_integrity(path)
    if not integ.valid:
        print(f"[WARNING] Database integrity check failed: {integ.errors}", file=sys.stderr)

    ws, sessions = SqliteStorageEngine.load_workspace(path)
    snap = ws.snapshot()

    print(f"=== Project Information: {path.name} ===")
    print(f"  Schema Version:      {integ.schema_version}")
    print(f"  Integrity Valid:     {integ.valid}")
    print(f"  Current Revision:    {snap.revision}")
    print(f"  Stored Evidence:     {len(ws._evidence)}")
    print(f"  Stored Observations: {len(ws._observations)}")
    print(f"  Stored Proposals:    {len(ws._proposals)}")
    print(f"  Active Phrases:      {len(snap.phrases)}")

    if snap.phrases:
        print("\n--- Active Published Phrases ---")
        for r in snap.phrases:
            print(f"  Scope: '{r.scope}' (Rev {r.number}, Origin: {r.origin})")
            print(f"    Notes: {format_phrase(r.notes)}")
            print(f"    Reason: {r.reason}")

    return 0


def cmd_inspect_audio(args: argparse.Namespace) -> int:
    wav_path = Path(args.wav_file)
    if not wav_path.exists():
        print(f"Error: WAV file not found: {wav_path}", file=sys.stderr)
        return 1

    data = wav_path.read_bytes()
    tempo = args.tempo or 120

    print(f"=== Audio Inspection: {wav_path.name} ({len(data)} bytes) ===")

    # 1. 10 Hz - 28 kHz Spectrum Inspection & Anomaly Watcher
    spectrum = watch_audio_bytes(data)
    print(f"\n--- 10-Band Acoustic Spectrum (Sample Rate: {spectrum.sample_rate} Hz, Nyquist: {spectrum.nyquist_hz:.0f} Hz) ---")
    for band_name, (low_hz, high_hz) in BAND_LIMITS.items():
        energy_frac = spectrum.band_energies.get(band_name, 0.0)
        energy_pct = energy_frac * 100.0
        bar = "#" * int(min(energy_pct, 100) / 4)
        high_str = f"{high_hz:5.0f}" if high_hz != float('inf') else ">28k"
        print(f"  {band_name:<20} {energy_pct:>5.1f}% [{bar:<25}] ({low_hz:5.0f} - {high_str} Hz)")

    print(f"\n--- Non-Musical Anomaly Watcher Report (Total: {len(spectrum.anomalies)}) ---")
    if not spectrum.anomalies:
        print("  [OK] No non-musical acoustic anomalies detected.")
    else:
        for a in spectrum.anomalies:
            freq_str = f" at {a.frequency_hz:.1f} Hz" if a.frequency_hz is not None else ""
            print(f"  ! [{a.severity:<8}] {a.kind:<20}{freq_str}: {a.description}")

    # 2. Monophonic Pitch & Rational Quantization Analysis
    report = analyze_monophonic_wav(data, tempo_bpm=tempo)
    print(f"\n--- Monophonic Pitch Analysis (Tempo: {tempo} BPM) ---")
    print(f"  Qualitative Uncertainty: {report.uncertainty}")
    print(f"  Duration:                {report.duration_seconds:.2f}s")
    print(f"  Inferred Phrase:         {format_phrase(report.notes)}")

    return 0


def cmd_propose_audio(args: argparse.Namespace) -> int:
    proj_path = Path(args.project)
    wav_path = Path(args.wav_file)
    scope = args.scope or "melody"
    tempo = args.tempo or 120

    if not proj_path.exists():
        print(f"Error: Project file not found: {proj_path}", file=sys.stderr)
        return 1
    if not wav_path.exists():
        print(f"Error: WAV file not found: {wav_path}", file=sys.stderr)
        return 1

    ws, _ = SqliteStorageEngine.load_workspace(proj_path)
    data = wav_path.read_bytes()

    # Ingest evidence
    ev = ws.add_evidence(data, "audio/wav")
    obs = ws.observe(ev.id, f"Audio performance take from {wav_path.name}", producer=CLI_PRODUCER)

    # Analyze
    report = analyze_monophonic_wav(data, tempo_bpm=tempo)
    prop = ws.propose(
        obs.id,
        scope,
        report.notes,
        mode="intended",
        uncertainty=report.uncertainty,
        origin="interpreted",
        producer=report.producer,
    )

    SqliteStorageEngine.save_workspace(ws, proj_path)
    print(f"[OK] Ingested and proposed audio in scope '{scope}':")
    print(f"     Evidence ID:   {ev.id}")
    print(f"     Proposal ID:   {prop.id}")
    print(f"     Uncertainty:   {report.uncertainty}")
    print(f"     Proposed Notes: {format_phrase(prop.notes)}")
    return 0


def cmd_review(args: argparse.Namespace) -> int:
    proj_path = Path(args.project)
    if not proj_path.exists():
        print(f"Error: Project file not found: {proj_path}", file=sys.stderr)
        return 1

    ws, sessions = SqliteStorageEngine.load_workspace(proj_path)
    if not sessions:
        print("Error: No AuthoritySession available for this project.", file=sys.stderr)
        return 1
    session = sessions[0]

    proposals = list(ws._proposals.values())
    if not proposals:
        print("No uncommitted proposals found in this workspace.")
        return 0

    target_prop = None
    if args.proposal_id:
        target_prop = ws.proposal(args.proposal_id)
    else:
        target_prop = proposals[-1]  # Latest proposal by default

    print(f"=== Human Authority Review: Proposal {target_prop.id[:12]}... ===")
    print(f"  Scope:       '{target_prop.scope}'")
    print(f"  Uncertainty: {target_prop.uncertainty}")
    print(f"  Origin:      {target_prop.origin} ({target_prop.producer.identity} v{target_prop.producer.version})")
    print(f"  Notes:       {format_phrase(target_prop.notes)}")

    # Non-interactive CLI action
    action = args.action
    if action == "confirm":
        reason = args.reason or "Human confirmation via CLI review"
        rev = session.confirm(target_prop.id, ws.snapshot().revision, reason)
        SqliteStorageEngine.save_workspace(ws, proj_path)
        print(f"[AUTHORITY OK] Confirmed and published Revision {rev.number} for scope '{rev.scope}'.")
        return 0
    elif action == "correct":
        if not args.notes:
            print("Error: --notes required when action is 'correct'.", file=sys.stderr)
            return 1
        corrected_notes = parse_notes_string(args.notes)
        reason = args.reason or "Human correction via CLI review"
        rev = session.correct(target_prop.id, corrected_notes, ws.snapshot().revision, reason)
        SqliteStorageEngine.save_workspace(ws, proj_path)
        print(f"[AUTHORITY OK] Corrected and published Revision {rev.number} for scope '{rev.scope}'.")
        print(f"               Published Notes: {format_phrase(rev.notes)}")
        return 0
    elif action is None:
        print("\nAction choices: [C]onfirm, [E]dit/Correct, [Q]uit (specify via --action in batch/headless)")
        return 0
    else:
        print(f"Error: Unknown action '{action}'. Use 'confirm' or 'correct'.", file=sys.stderr)
        return 1


def cmd_export(args: argparse.Namespace) -> int:
    proj_path = Path(args.project)
    out_path = Path(args.out)
    scope = args.scope
    fmt = args.format.lower()

    if not proj_path.exists():
        print(f"Error: Project file not found: {proj_path}", file=sys.stderr)
        return 1

    ws, _ = SqliteStorageEngine.load_workspace(proj_path)
    matching = [r for r in ws.snapshot().phrases if r.scope == scope]
    if not matching:
        print(f"Error: No published phrase found for scope '{scope}'.", file=sys.stderr)
        return 1

    published_notes = matching[0].notes

    if fmt == "musicxml":
        xml_str, report = phrase_to_musicxml(published_notes, tempo_bpm=args.tempo or 120, title=args.title or scope)
        out_path.write_text(xml_str, encoding="utf-8")
    elif fmt == "midi":
        midi_bytes, report = phrase_to_midi(published_notes, tempo_bpm=args.tempo or 120)
        out_path.write_bytes(midi_bytes)
    else:
        print(f"Error: Unsupported format '{fmt}'. Choose 'musicxml' or 'midi'.", file=sys.stderr)
        return 1

    print(f"[OK] Exported {len(published_notes)} notes to {out_path} ({fmt.upper()})")
    print(f"\n--- SPECIFICATION REP-1 Loss Disclosure Report ---")
    print(f"  Summary: {report.summary}")
    for loss in report.disclosed_losses:
        print(f"  - Disclosed: {loss}")

    return 0


def cmd_import(args: argparse.Namespace) -> int:
    proj_path = Path(args.project)
    in_path = Path(args.file)
    scope = args.scope or "imported"

    if not proj_path.exists():
        print(f"Error: Project file not found: {proj_path}", file=sys.stderr)
        return 1
    if not in_path.exists():
        print(f"Error: Input file not found: {in_path}", file=sys.stderr)
        return 1

    ws, sessions = SqliteStorageEngine.load_workspace(proj_path)
    raw_bytes = in_path.read_bytes()

    if in_path.suffix.lower() in (".xml", ".musicxml"):
        xml_str = raw_bytes.decode("utf-8")
        imported_notes, report = musicxml_to_phrase(xml_str)
    elif in_path.suffix.lower() in (".mid", ".midi"):
        imported_notes, report = midi_to_phrase(raw_bytes)
    else:
        print(f"Error: Unrecognized format for file '{in_path.name}'.", file=sys.stderr)
        return 1

    print(f"[OK] Parsed {len(imported_notes)} notes from {in_path.name}")
    print(f"\n--- SPECIFICATION REP-1 Loss Disclosure Report ---")
    print(f"  Summary: {report.summary}")
    for loss in report.disclosed_losses:
        print(f"  - Disclosed: {loss}")

    # Record evidence, observation, and proposal
    ev = ws.add_evidence(raw_bytes, "application/octet-stream")
    obs = ws.observe(ev.id, f"Imported from {in_path.name}", producer=CLI_PRODUCER)
    prop = ws.propose(obs.id, scope, imported_notes, "intended", "HIGH", "interpreted", producer=CLI_PRODUCER)

    if args.confirm:
        if not sessions:
            print("Error: No AuthoritySession available to confirm import.", file=sys.stderr)
            return 1
        rev = sessions[0].confirm(prop.id, ws.snapshot().revision, f"Import confirmed from {in_path.name}")
        print(f"\n[AUTHORITY OK] Immediately confirmed as Revision {rev.number} in scope '{scope}'.")

    SqliteStorageEngine.save_workspace(ws, proj_path)
    print(f"Saved project update to {proj_path}")
    return 0


def cmd_history(args: argparse.Namespace) -> int:
    proj_path = Path(args.project)
    if not proj_path.exists():
        print(f"Error: Project file not found: {proj_path}", file=sys.stderr)
        return 1

    ws, _ = SqliteStorageEngine.load_workspace(proj_path)
    history = ws.snapshot().history

    if not history:
        print("No revisions published in this workspace.")
        return 0

    print(f"=== Revision History: {proj_path.name} (Total: {len(history)}) ===")
    for rev in history:
        if args.scope and rev.scope != args.scope:
            continue
        restored_str = f" (restored from Rev {rev.restored_from})" if rev.restored_from else ""
        print(f"  Rev {rev.number:3d} | Scope: '{rev.scope}' | Op: {rev.operation:<7} | Actor: {rev.actor:<12}{restored_str}")
        print(f"          Notes:  {format_phrase(rev.notes)}")
        print(f"          Reason: {rev.reason}")
    return 0


def cmd_restore(args: argparse.Namespace) -> int:
    proj_path = Path(args.project)
    target_rev = args.revision
    reason = args.reason or f"Restored revision {target_rev} via CLI"

    if not proj_path.exists():
        print(f"Error: Project file not found: {proj_path}", file=sys.stderr)
        return 1

    ws, sessions = SqliteStorageEngine.load_workspace(proj_path)
    if not sessions:
        print("Error: No AuthoritySession available for this project.", file=sys.stderr)
        return 1

    rev = sessions[0].restore(target_rev, ws.snapshot().revision, reason)
    SqliteStorageEngine.save_workspace(ws, proj_path)
    print(f"[AUTHORITY OK] Restored Revision {target_rev} as new Revision {rev.number} in scope '{rev.scope}'.")
    print(f"               Current Notes: {format_phrase(rev.notes)}")
    return 0




def cmd_serve(args: argparse.Namespace) -> int:
    path = Path(args.project)
    if not path.exists():
        print(f"Error: Project file not found at {path}", file=sys.stderr)
        return 1
    from reference.preview.server import PreviewServer
    ws, sessions = SqliteStorageEngine.load_workspace(path)
    server = PreviewServer(ws, sessions, port=args.port, project_path=path)
    print(f"=== Music MCP Visualizer Preview Server ===")
    print(f"  Project:  {path}")
    print(f"  URL:      http://127.0.0.1:{args.port}")
    print(f"  Bound to: Loopback (127.0.0.1) ONLY")
    print(f"  Press Ctrl+C to terminate server.")
    if args.open:
        import webbrowser
        webbrowser.open(f"http://127.0.0.1:{args.port}")
    try:
        server.start(background=False)
    except KeyboardInterrupt:
        print("\nStopping preview server...")
        server.stop()
    return 0

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="musicmcp",
        description="Music MCP: Host-Held Interactive Review Shell & Authority Interface",
    )
    subparsers = parser.add_subparsers(dest="subcommand", help="Command to execute")

    # init
    p_init = subparsers.add_parser("init", help="Initialize a new .musicmcp project file")
    p_init.add_argument("project", help="Path to .musicmcp project file")
    p_init.add_argument("--artist", help="Lead artist identity name")
    p_init.add_argument("--scopes", help="Comma-separated scopes to authorize (default: 'melody')")
    p_init.add_argument("--lock", help="Comma-separated scopes to lock")
    p_init.add_argument("--force", action="store_true", help="Overwrite existing project file")

    # info
    p_info = subparsers.add_parser("info", help="Display project summary and integrity audit")
    p_info.add_argument("project", help="Path to .musicmcp project file")

    # inspect-audio
    p_insp = subparsers.add_parser("inspect-audio", help="Inspect WAV audio spectrum and pitch without mutating project")
    p_insp.add_argument("wav_file", help="Path to 16-bit PCM mono WAV file")
    p_insp.add_argument("--tempo", type=int, help="Reference tempo in BPM (default: 120)")

    # propose-audio
    p_prop = subparsers.add_parser("propose-audio", help="Ingest audio evidence and record machine pitch proposal")
    p_prop.add_argument("project", help="Path to .musicmcp project file")
    p_prop.add_argument("wav_file", help="Path to WAV audio file")
    p_prop.add_argument("--scope", default="melody", help="Target scope for proposal (default: 'melody')")
    p_prop.add_argument("--tempo", type=int, default=120, help="Tempo in BPM")

    # review
    p_rev = subparsers.add_parser("review", help="Human authority review and confirmation of proposals")
    p_rev.add_argument("project", help="Path to .musicmcp project file")
    p_rev.add_argument("--proposal-id", help="Specific proposal ID to review")
    p_rev.add_argument("--action", choices=["confirm", "correct"], help="Action to take")
    p_rev.add_argument("--notes", help="Corrected notes (required if action is 'correct')")
    p_rev.add_argument("--reason", help="Explanation/reason for human decision")

    # export
    p_exp = subparsers.add_parser("export", help="Export authoritative published phrase to MusicXML or MIDI")
    p_exp.add_argument("project", help="Path to .musicmcp project file")
    p_exp.add_argument("--scope", required=True, help="Scope of published phrase to export")
    p_exp.add_argument("--format", required=True, choices=["musicxml", "midi"], help="Output format")
    p_exp.add_argument("--out", required=True, help="Output destination path")
    p_exp.add_argument("--tempo", type=int, default=120, help="Tempo in BPM")
    p_exp.add_argument("--title", help="Piece title for MusicXML")

    # import
    p_imp = subparsers.add_parser("import", help="Import MusicXML or MIDI file as a proposal")
    p_imp.add_argument("project", help="Path to .musicmcp project file")
    p_imp.add_argument("--file", required=True, help="Input MusicXML or MIDI file")
    p_imp.add_argument("--scope", default="imported", help="Target scope")
    p_imp.add_argument("--confirm", action="store_true", help="Immediately confirm as authoritative revision")

    # history
    p_hist = subparsers.add_parser("history", help="Show published revision history")
    p_hist.add_argument("project", help="Path to .musicmcp project file")
    p_hist.add_argument("--scope", help="Filter history by scope")

    # restore
    p_rest = subparsers.add_parser("restore", help="Restore a historical revision as current")
    p_rest.add_argument("project", help="Path to .musicmcp project file")
    p_rest.add_argument("--revision", type=int, required=True, help="Revision number to restore")
    p_rest.add_argument("--reason", help="Reason for restoration")

    # serve
    p_srv = subparsers.add_parser("serve", help="Launch the local visualizer and authority review deck in browser")
    p_srv.add_argument("project", help="Path to .musicmcp project file")
    p_srv.add_argument("--port", type=int, default=8765, help="Port to bind (default: 8765)")
    p_srv.add_argument("--open", action="store_true", help="Automatically open browser")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.subcommand:
        parser.print_help()
        return 0

    dispatch = {
        "init": cmd_init,
        "info": cmd_info,
        "inspect-audio": cmd_inspect_audio,
        "propose-audio": cmd_propose_audio,
        "review": cmd_review,
        "export": cmd_export,
        "import": cmd_import,
        "history": cmd_history,
        "restore": cmd_restore,
        "serve": cmd_serve,
    }

    handler = dispatch.get(args.subcommand)
    if not handler:
        parser.print_help()
        return 1

    try:
        return handler(args)
    except MusicError as e:
        print(f"MusicMCP Diagnostic [{e.diagnostic.code}]: {e.diagnostic.message}", file=sys.stderr)
        print(f"Next Action: {e.diagnostic.next_action}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
