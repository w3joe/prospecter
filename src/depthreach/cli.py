"""DepthReach CLI entry point."""

from __future__ import annotations

import argparse
import os
import signal
import sys
import time
from typing import List, Optional

from .cache import ResearchCache
from .checkpoint import Checkpoint
from .emailer import generate_email
from .input_parser import load_prospects
from .models import EmailResult, Prospect
from .output_writer import OutputWriter
from .researcher import RateLimiter, research_prospect
from .worker_pool import run_workers

_VALID_TONES = ("professional", "casual", "direct")


def _get_api_keys() -> tuple[str, str]:
    tavily_key = os.environ.get("TAVILY_API_KEY", "")
    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    return tavily_key, gemini_key


def _print_progress(msg: str) -> None:
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", file=sys.stderr)


def _process_single(
    prospect: Prospect,
    tavily_key: str,
    gemini_key: str,
    tone: str,
    rate_limiter: RateLimiter,
    cache: ResearchCache,
    checkpoint: Checkpoint,
    writer: OutputWriter,
    verbose: bool,
) -> None:
    """Research and generate an email for one prospect, then write the result."""
    ck_key = Checkpoint.make_key(prospect.name, prospect.email)
    if checkpoint.is_done(ck_key):
        _print_progress(f"Skipping (already done): {prospect.display_name()}")
        return

    _print_progress(f"Processing: {prospect.display_name()}")

    # --- Research ---
    cache_key = ResearchCache.make_key(prospect.name, prospect.company)
    cached = cache.get(cache_key)
    if cached:
        _print_progress(f"  Using cached research for: {prospect.display_name()}")
        research_notes = cached["notes"]
    else:
        result = research_prospect(
            prospect,
            api_key=tavily_key,
            rate_limiter=rate_limiter,
            verbose=verbose,
        )
        if result.error:
            _print_progress(f"  Research error: {result.error}")
        research_notes = result.notes or result.error or ""
        if not result.error:
            cache.set(cache_key, research_notes, result.raw_results)

    # --- Email generation ---
    email_result = generate_email(
        prospect,
        research_notes=research_notes,
        api_key=gemini_key,
        tone=tone,
        verbose=verbose,
    )
    if email_result.error:
        _print_progress(f"  Email generation error: {email_result.error}")

    writer.write(email_result)
    checkpoint.mark_done(ck_key)
    _print_progress(f"  Done: {prospect.display_name()}")


def run_batch(
    prospects: List[Prospect],
    tavily_key: str,
    gemini_key: str,
    tone: str = "professional",
    num_workers: int = 2,
    output_path: Optional[str] = None,
    verbose: bool = False,
) -> None:
    """Process a list of prospects in parallel."""
    cache = ResearchCache()
    checkpoint = Checkpoint()
    writer = OutputWriter(output_path)
    total = len(prospects)

    # Each worker gets its own rate limiter so they operate independently
    worker_rate_limiters: List[RateLimiter] = [
        RateLimiter() for _ in range(max(1, min(3, num_workers)))
    ]

    # Assign prospects to workers (round-robin) so each worker keeps its own limiter
    worker_queues: List[List[Prospect]] = [[] for _ in worker_rate_limiters]
    for i, p in enumerate(prospects):
        worker_queues[i % len(worker_queues)].append(p)

    _print_progress(
        f"Starting batch: {total} prospects, {num_workers} worker(s), tone={tone!r}"
    )
    if output_path:
        _print_progress(f"Output file: {output_path}")

    interrupted = False

    def handle_sigint(signal_num: int, stack_frame: object) -> None:  # noqa: ANN001
        nonlocal interrupted
        interrupted = True
        _print_progress("Interrupted – checkpoint saved. Re-run to resume.")
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_sigint)

    def make_worker_fn(rate_limiter: RateLimiter):
        def fn(prospect: Prospect) -> None:
            _process_single(
                prospect,
                tavily_key=tavily_key,
                gemini_key=gemini_key,
                tone=tone,
                rate_limiter=rate_limiter,
                cache=cache,
                checkpoint=checkpoint,
                writer=writer,
                verbose=verbose,
            )
        return fn

    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = []
        for queue, rl in zip(worker_queues, worker_rate_limiters):
            worker_fn = make_worker_fn(rl)
            for p in queue:
                futures.append(executor.submit(worker_fn, p))
        for future in concurrent.futures.as_completed(futures):
            exc = future.exception()
            if exc is not None:
                _print_progress(f"Worker error: {exc}")

    writer.close()
    _print_progress(f"Batch complete. {total} prospects processed.")


def run_single(
    name: str,
    company: str,
    email: str,
    tavily_key: str,
    gemini_key: str,
    tone: str = "professional",
    verbose: bool = False,
) -> None:
    """Research and email a single prospect, printing to stdout."""
    prospect = Prospect(name=name, company=company, email=email)
    rate_limiter = RateLimiter()
    cache = ResearchCache()
    writer = OutputWriter(path=None)  # stdout

    _print_progress(f"Researching: {prospect.display_name()}")

    cache_key = ResearchCache.make_key(prospect.name, prospect.company)
    cached = cache.get(cache_key)
    if cached:
        research_notes = cached["notes"]
    else:
        result = research_prospect(
            prospect,
            api_key=tavily_key,
            rate_limiter=rate_limiter,
            verbose=verbose,
        )
        research_notes = result.notes or result.error or ""
        if not result.error:
            cache.set(cache_key, research_notes, result.raw_results)

    email_result = generate_email(
        prospect,
        research_notes=research_notes,
        api_key=gemini_key,
        tone=tone,
        verbose=verbose,
    )
    writer.write(email_result)
    writer.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="depthreach",
        description="AI-powered prospect research and cold email generation",
    )

    # Batch mode
    parser.add_argument(
        "--input", metavar="FILE", help="CSV or JSON file with prospect list"
    )
    parser.add_argument(
        "--output", metavar="FILE", help="Output CSV file (default: stdout)"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=2,
        choices=[1, 2, 3],
        metavar="{1,2,3}",
        help="Number of parallel workers (default: 2, max: 3)",
    )

    # Single-prospect mode
    parser.add_argument("--name", metavar="NAME", help="Prospect name (single mode)")
    parser.add_argument(
        "--company", metavar="COMPANY", default="", help="Prospect company (single mode)"
    )
    parser.add_argument(
        "--email", metavar="EMAIL", default="", help="Prospect email (single mode)"
    )

    # Shared options
    parser.add_argument(
        "--tone",
        choices=_VALID_TONES,
        default="professional",
        help="Email tone (default: professional)",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Enable verbose progress output"
    )

    return parser


def main(argv: Optional[List[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    tavily_key, gemini_key = _get_api_keys()

    if not tavily_key:
        print(
            "Error: TAVILY_API_KEY environment variable is not set.", file=sys.stderr
        )
        sys.exit(1)
    if not gemini_key:
        print(
            "Error: GEMINI_API_KEY environment variable is not set.", file=sys.stderr
        )
        sys.exit(1)

    if args.input:
        # Batch mode
        try:
            prospects = load_prospects(args.input)
        except (FileNotFoundError, ValueError) as exc:
            print(f"Error loading input file: {exc}", file=sys.stderr)
            sys.exit(1)

        if not prospects:
            print("No prospects found in input file.", file=sys.stderr)
            sys.exit(0)

        run_batch(
            prospects=prospects,
            tavily_key=tavily_key,
            gemini_key=gemini_key,
            tone=args.tone,
            num_workers=args.workers,
            output_path=args.output,
            verbose=args.verbose,
        )
    elif args.name:
        # Single-prospect mode
        run_single(
            name=args.name,
            company=args.company,
            email=args.email,
            tavily_key=tavily_key,
            gemini_key=gemini_key,
            tone=args.tone,
            verbose=args.verbose,
        )
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
