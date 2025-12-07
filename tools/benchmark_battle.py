"""
Battle engine performance benchmarks.

Measures single match simulation speed, batch processing, and resource usage.
Run with: python -m tools.benchmark_battle
"""

import asyncio
import time
import sys
import logging
from typing import List, Dict
from statistics import mean, stdev

from core.battle_models import (
    Character, CharacterStats, Skill, SkillType, TargetType, BattleConfig
)
from core.battle_engine import BattleEngine
from core.arena_queue import ArenaQueue

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# TEST DATA
# ============================================================================


def create_test_character(char_id: int, stats_mult: float = 1.0) -> Character:
    """Create a test character with optional stats multiplier."""
    return Character(
        id=f"bench_char_{char_id}",
        name=f"Benchmark Character {char_id}",
        element=["fire", "water", "grass"][char_id % 3],
        rarity="rare",
        stats=CharacterStats(
            hp=int(100 * stats_mult),
            atk=int(20 * stats_mult),
            def_=int(10 * stats_mult),
            spd=int(15 * stats_mult),
            elem_atk=int(18 * stats_mult),
            elem_def=int(8 * stats_mult),
        ),
        skills=[
            Skill(
                id="basic_attack",
                name="Basic Attack",
                skill_type=SkillType.PHYSICAL,
                power=int(10 * stats_mult),
                accuracy=1.0,
                target_type=TargetType.SINGLE,
                priority=0,
            )
        ],
    )


# ============================================================================
# BENCHMARKS
# ============================================================================


async def benchmark_single_match(
    num_iterations: int = 50,
) -> Dict[str, float]:
    """
    Benchmark single match simulation.
    
    Args:
        num_iterations: Number of matches to simulate
    
    Returns:
        Dict with timing statistics
    """
    print(f"\n{'=' * 70}")
    print(f"BENCHMARK: Single Match Simulation ({num_iterations} iterations)")
    print(f"{'=' * 70}")

    engine = BattleEngine()
    char1 = create_test_character(1)
    char2 = create_test_character(2)

    times = []

    for i in range(num_iterations):
        config = BattleConfig(rng_seed=i, max_rounds=50)
        match = engine.create_match(
            [char1],
            [char2],
            f"bench_single_{i}",
            config,
        )

        start = time.time()
        result = await engine.simulate(match)
        elapsed = time.time() - start

        times.append(elapsed * 1000)  # Convert to ms
        print(f"  Iteration {i+1:2d}: {elapsed*1000:6.2f}ms", end="")
        if (i + 1) % 5 == 0:
            print()
        else:
            print(" ", end="")

    print("\n")

    stats = {
        "count": num_iterations,
        "total_ms": sum(times),
        "mean_ms": mean(times),
        "min_ms": min(times),
        "max_ms": max(times),
        "stdev_ms": stdev(times) if len(times) > 1 else 0,
    }

    print(f"Results:")
    print(f"  Mean:   {stats['mean_ms']:7.2f} ms")
    print(f"  Min:    {stats['min_ms']:7.2f} ms")
    print(f"  Max:    {stats['max_ms']:7.2f} ms")
    print(f"  StdDev: {stats['stdev_ms']:7.2f} ms")
    print(f"  Total:  {stats['total_ms']:7.2f} ms")

    return stats


async def benchmark_batch_processing(
    batch_size: int = 100,
    num_workers: int = 4,
) -> Dict[str, float]:
    """
    Benchmark batch processing with arena queue.
    
    Args:
        batch_size: Number of matches to process
        num_workers: Number of concurrent workers
    
    Returns:
        Dict with throughput metrics
    """
    print(f"\n{'=' * 70}")
    print(f"BENCHMARK: Batch Processing (batch_size={batch_size}, workers={num_workers})")
    print(f"{'=' * 70}\n")

    engine = BattleEngine()
    queue = ArenaQueue(engine=engine, num_workers=num_workers, max_queue_size=200)
    await queue.start()

    try:
        char1 = create_test_character(1)
        char2 = create_test_character(2)

        start_time = time.time()

        # Queue all matches
        print(f"Queueing {batch_size} matches...")
        futures = []
        for i in range(batch_size):
            config = BattleConfig(rng_seed=i, max_rounds=30)
            match = engine.create_match(
                [char1],
                [char2],
                f"bench_batch_{i}",
                config,
            )
            future = await queue.queue_match(match, priority=0)
            futures.append(future)

        # Wait for all to complete
        print(f"Processing batch...")
        results = await asyncio.gather(*futures, return_exceptions=True)
        
        elapsed = time.time() - start_time

        successful = sum(1 for r in results if not isinstance(r, Exception))
        failed = len(results) - successful

        stats = {
            "batch_size": batch_size,
            "num_workers": num_workers,
            "successful": successful,
            "failed": failed,
            "total_seconds": elapsed,
            "throughput_per_sec": batch_size / elapsed if elapsed > 0 else 0,
            "avg_per_match_ms": (elapsed * 1000) / batch_size if batch_size > 0 else 0,
        }

        print(f"\nResults:")
        print(f"  Total Time:          {stats['total_seconds']:7.2f}s")
        print(f"  Successful:          {stats['successful']:7d} matches")
        print(f"  Failed:              {stats['failed']:7d} matches")
        print(f"  Throughput:          {stats['throughput_per_sec']:7.2f} matches/sec")
        print(f"  Avg per Match:       {stats['avg_per_match_ms']:7.2f} ms")

        # Print queue metrics
        metrics = queue.get_metrics()
        print(f"\nQueue Metrics:")
        print(f"  Max Queue Depth:     {metrics.max_queue_depth:7d}")
        print(f"  Avg Duration:        {metrics.avg_duration_ms:7.2f} ms")

        return stats

    finally:
        await queue.stop()


async def benchmark_scaling(
) -> None:
    """
    Benchmark scaling with different worker counts.
    """
    print(f"\n{'=' * 70}")
    print(f"BENCHMARK: Scaling Analysis")
    print(f"{'=' * 70}\n")

    batch_size = 20
    worker_counts = [1, 2, 4, 8]
    results = []

    for num_workers in worker_counts:
        engine = BattleEngine()
        queue = ArenaQueue(engine=engine, num_workers=num_workers)
        await queue.start()

        try:
            char1 = create_test_character(1)
            char2 = create_test_character(2)

            start = time.time()
            futures = []

            for i in range(batch_size):
                config = BattleConfig(rng_seed=i, max_rounds=20)
                match = engine.create_match(
                    [char1],
                    [char2],
                    f"bench_scale_{num_workers}_{i}",
                    config,
                )
                future = await queue.queue_match(match, priority=0)
                futures.append(future)

            await asyncio.gather(*futures, return_exceptions=True)
            elapsed = time.time() - start

            throughput = batch_size / elapsed if elapsed > 0 else 0
            results.append({
                "workers": num_workers,
                "time_sec": elapsed,
                "throughput": throughput,
            })

            print(f"  {num_workers} workers: {elapsed:6.2f}s ({throughput:6.2f} matches/sec)")

        finally:
            await queue.stop()

    print(f"\nScaling Summary:")
    if results:
        baseline = results[0]["throughput"]
        for r in results:
            efficiency = (r["throughput"] / baseline) / r["workers"]
            print(f"  {r['workers']} workers: {efficiency*100:5.1f}% efficiency")


async def benchmark_large_party(
) -> None:
    """
    Benchmark battles with larger parties.
    """
    print(f"\n{'=' * 70}")
    print(f"BENCHMARK: Large Party Impact")
    print(f"{'=' * 70}\n")

    party_sizes = [1, 2, 3, 5]

    for size in party_sizes:
        engine = BattleEngine()
        player_party = [create_test_character(i) for i in range(size)]
        npc_party = [create_test_character(1000 + i) for i in range(size)]

        times = []
        for i in range(10):
            config = BattleConfig(rng_seed=i, max_rounds=20)
            match = engine.create_match(
                player_party,
                npc_party,
                f"bench_party_{size}_{i}",
                config,
            )

            start = time.time()
            result = await engine.simulate(match)
            times.append((time.time() - start) * 1000)

        avg_ms = mean(times)
        print(f"  Party size {size}: {avg_ms:7.2f} ms (avg)")


# ============================================================================
# MAIN
# ============================================================================


async def main():
    """Run all benchmarks."""
    print("\n" + "=" * 70)
    print("BATTLE ENGINE PERFORMANCE BENCHMARKS")
    print("=" * 70)

    # Single match benchmark
    single_stats = await benchmark_single_match(num_iterations=50)

    # Batch processing benchmarks
    batch_stats_4w = await benchmark_batch_processing(batch_size=100, num_workers=4)
    batch_stats_2w = await benchmark_batch_processing(batch_size=100, num_workers=2)

    # Scaling analysis
    await benchmark_scaling()

    # Large party impact
    await benchmark_large_party()

    # Summary
    print(f"\n{'=' * 70}")
    print("BENCHMARK SUMMARY")
    print(f"{'=' * 70}")
    print(f"\nSingle Match (avg):          {single_stats['mean_ms']:7.2f} ms")
    print(f"Batch (4 workers):           {batch_stats_4w['throughput_per_sec']:7.2f} matches/sec")
    print(f"Batch (2 workers):           {batch_stats_2w['throughput_per_sec']:7.2f} matches/sec")
    print(f"\nRecommended Configuration:")
    print(f"  - Single matches: < 200 ms (acceptable for user-facing)")
    print(f"  - Batch processing: > 5 matches/sec (with 4 workers)")
    print(f"  - Max batch size: 100 matches (prevent queue overflow)")


if __name__ == "__main__":
    asyncio.run(main())
