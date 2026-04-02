"""Worker pool for parallel prospect processing."""

from __future__ import annotations

import concurrent.futures
import sys
import threading
from typing import Callable, Iterable, Iterator, TypeVar

T = TypeVar("T")


def run_workers(
    items: Iterable[T],
    worker_fn: Callable[[T], None],
    num_workers: int = 2,
) -> None:
    """Process *items* in parallel using a thread pool of *num_workers* threads.

    Args:
        items: Iterable of items to process.
        worker_fn: Callable that processes a single item (may raise).
        num_workers: Number of parallel worker threads (1–3).
    """
    num_workers = max(1, min(3, num_workers))
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = {executor.submit(worker_fn, item): item for item in items}
        for future in concurrent.futures.as_completed(futures):
            exc = future.exception()
            if exc is not None:
                item = futures[future]
                print(
                    f"[worker] Unhandled error processing {item!r}: {exc}",
                    file=sys.stderr,
                )
