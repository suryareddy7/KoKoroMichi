"""
Arena queue for managing concurrent battle simulations.

Prevents race conditions, manages queue depth, and provides result caching
for immediate retrieval.
"""

import asyncio
import logging
from typing import Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime

from core.battle_models import BattleMatch, BattleResult, QueuedMatch
from core.battle_engine import BattleEngine

logger = logging.getLogger(__name__)


@dataclass
class ArenaMetrics:
    """Arena queue performance metrics."""
    total_processed: int = 0
    avg_duration_ms: float = 0.0
    max_queue_depth: int = 0
    current_queue_depth: int = 0
    failed_matches: int = 0
    last_updated: datetime = field(default_factory=datetime.now)


class ArenaQueue:
    """
    Manages a queue of battles to prevent race conditions and overload.
    
    Spawns multiple worker tasks that pull matches from queue, simulate,
    and cache results.
    """

    def __init__(
        self,
        engine: Optional[BattleEngine] = None,
        num_workers: int = 3,
        max_queue_size: int = 100,
    ):
        """
        Initialize arena queue.

        Args:
            engine: BattleEngine to use (creates new if None)
            num_workers: Number of concurrent simulation workers
            max_queue_size: Maximum pending matches
        """
        self.engine = engine or BattleEngine()
        self.num_workers = num_workers
        self.max_queue_size = max_queue_size

        # Queue and result cache
        self.queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self.results_cache: Dict[str, BattleResult] = {}
        self.pending_futures: Dict[str, asyncio.Future] = {}

        # Metrics
        self.metrics = ArenaMetrics()
        self.lock = asyncio.Lock()

        # Worker tasks
        self.workers: list = []
        self.running = False

    async def start(self) -> None:
        """Start worker tasks."""
        if self.running:
            return

        self.running = True
        self.workers = [
            asyncio.create_task(self._worker(i))
            for i in range(self.num_workers)
        ]
        logger.info(f"Arena queue started with {self.num_workers} workers")

    async def stop(self) -> None:
        """Stop worker tasks and process remaining queue."""
        self.running = False

        # Wait for workers to finish
        await asyncio.gather(*self.workers, return_exceptions=True)
        logger.info("Arena queue stopped")

    async def queue_match(
        self, match: BattleMatch, priority: int = 0
    ) -> asyncio.Future:
        """
        Queue a match for simulation.

        Args:
            match: BattleMatch to simulate
            priority: Higher = earlier execution (default 0)

        Returns:
            Future that resolves when match completes

        Raises:
            RuntimeError: If queue is full
            ValueError: If match_id already queued
        """
        async with self.lock:
            if match.match_id in self.pending_futures:
                raise ValueError(f"Match {match.match_id} already queued")

            if self.queue.qsize() >= self.max_queue_size:
                raise RuntimeError(
                    f"Arena queue full ({self.queue.qsize()}/{self.max_queue_size})"
                )

            # Create future for result
            future: asyncio.Future = asyncio.Future()
            self.pending_futures[match.match_id] = future

            # Enqueue match
            queued = QueuedMatch(match, priority)
            await self.queue.put(queued)

            # Update metrics
            self.metrics.current_queue_depth = self.queue.qsize()
            self.metrics.max_queue_depth = max(
                self.metrics.max_queue_depth,
                self.metrics.current_queue_depth,
            )

            logger.info(
                f"Match {match.match_id} queued (priority={priority}, depth={self.queue.qsize()})"
            )

        return future

    async def get_result(
        self, match_id: str, timeout: float = 60.0
    ) -> Optional[BattleResult]:
        """
        Get result of a queued match.

        Args:
            match_id: Match ID to retrieve
            timeout: Max seconds to wait

        Returns:
            BattleResult if found, None if not yet complete

        Raises:
            asyncio.TimeoutError: If result not available within timeout
        """
        # Check cache first
        if match_id in self.results_cache:
            return self.results_cache[match_id]

        # Check pending
        if match_id not in self.pending_futures:
            return None

        # Wait for result
        future = self.pending_futures[match_id]
        try:
            result = await asyncio.wait_for(future, timeout=timeout)
            return result
        except asyncio.TimeoutError:
            raise

    async def cancel_match(self, match_id: str) -> bool:
        """
        Cancel a pending match.

        Args:
            match_id: Match to cancel

        Returns:
            True if cancelled, False if not found/already processed
        """
        if match_id not in self.pending_futures:
            return False

        future = self.pending_futures[match_id]
        cancelled = future.cancel()

        if cancelled:
            del self.pending_futures[match_id]
            logger.info(f"Match {match_id} cancelled")

        return cancelled

    async def _worker(self, worker_id: int) -> None:
        """Worker task that processes matches from queue."""
        logger.info(f"Arena worker {worker_id} started")

        while self.running:
            try:
                # Get next match with timeout to allow graceful shutdown
                queued_match = await asyncio.wait_for(
                    self.queue.get(), timeout=1.0
                )
            except asyncio.TimeoutError:
                # Queue empty, check if still running
                if not self.running:
                    break
                continue

            match_id = queued_match.match.match_id

            try:
                # Simulate match
                result = await self.engine.simulate(queued_match.match)

                # Cache result
                async with self.lock:
                    self.results_cache[match_id] = result
                    self.metrics.current_queue_depth = self.queue.qsize()
                    self.metrics.total_processed += 1
                    self.metrics.avg_duration_ms = (
                        self.metrics.avg_duration_ms * 0.9
                        + result.duration_ms * 0.1
                    )

                # Resolve pending future
                if match_id in self.pending_futures:
                    future = self.pending_futures[match_id]
                    if not future.done():
                        future.set_result(result)

                logger.debug(
                    f"Match {match_id} completed in {result.duration_ms:.2f}ms"
                )

            except Exception as e:
                logger.error(f"Match {match_id} failed: {e}", exc_info=True)
                async with self.lock:
                    self.metrics.failed_matches += 1

                # Reject pending future
                if match_id in self.pending_futures:
                    future = self.pending_futures[match_id]
                    if not future.done():
                        future.set_exception(e)

        logger.info(f"Arena worker {worker_id} stopped")

    def get_metrics(self) -> ArenaMetrics:
        """Get current queue metrics."""
        self.metrics.last_updated = datetime.now()
        return self.metrics

    def clear_cache(self, older_than_seconds: Optional[float] = None) -> int:
        """
        Clear result cache.

        Args:
            older_than_seconds: Only clear results older than this (None = clear all)

        Returns:
            Number of results cleared
        """
        if older_than_seconds is None:
            cleared = len(self.results_cache)
            self.results_cache.clear()
            return cleared

        # Note: Would need timestamp tracking on results for age-based clearing
        return 0
