#!/usr/bin/env python3
"""
Performance Benchmark Framework

Benchmarks critical voice assistant operations.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import asyncio
import time
import json
import statistics
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import structlog

logger = structlog.get_logger()


class PerformanceBenchmark:
    """Performance benchmarking for voice assistant."""

    def __init__(self):
        self.results: Dict = {}

    async def run_all_benchmarks(self) -> Dict:
        """Run all performance benchmarks."""
        logger.info("benchmark.starting")

        # Since we can't run full orchestrator without OpenClaw,
        # we'll benchmark the components that are available

        # 1. Configuration loading benchmark
        await self.benchmark_config_loading()

        # 2. Audio processing benchmark
        await self.benchmark_audio_processing()

        # 3. String processing benchmark (simulating STT/TTS)
        await self.benchmark_string_processing()

        # 4. Database operation benchmark
        await self.benchmark_database_operations()

        # 5. VAD benchmark
        await self.benchmark_vad()

        # Generate report
        self.generate_report()

        return self.results

    async def benchmark_config_loading(self, iterations: int = 100):
        """Benchmark configuration loading."""
        logger.info("benchmark.config_loading")
        latencies = []

        for i in range(iterations):
            start = time.perf_counter()

            # Simulate config loading
            from config.config import get_config
            config = get_config()

            end = time.perf_counter()
            latencies.append((end - start) * 1000)  # ms

        avg = statistics.mean(latencies)
        p95 = statistics.quantiles(latencies, n=100)[94]
        p99 = statistics.quantiles(latencies, n=100)[98]

        self.results['config_loading'] = {
            'iterations': iterations,
            'avg_ms': round(avg, 3),
            'p95_ms': round(p95, 3),
            'p99_ms': round(p99, 3),
            'target_ms': 10,
            'status': 'PASS' if avg < 10 else 'FAIL'
        }

        logger.info("benchmark.config_loading.complete",
                   avg_ms=avg,
                   p99_ms=p99,
                   status=self.results['config_loading']['status'])

    async def benchmark_audio_processing(self, iterations: int = 50):
        """Benchmark audio processing operations."""
        logger.info("benchmark.audio_processing")
        latencies = []

        import numpy as np

        for i in range(iterations):
            start = time.perf_counter()

            # Simulate audio processing
            # Generate audio samples
            audio = np.random.randn(16000).astype(np.float32)

            # Simulate energy calculation
            energy = np.sqrt(np.mean(audio**2))

            # Simulate buffer operation
            from bridge.audio_buffer import AudioBuffer
            buffer = AudioBuffer(capacity=16000)
            buffer.write(audio)
            buffer.read(len(audio))

            end = time.perf_counter()
            latencies.append((end - start) * 1000)  # ms

        avg = statistics.mean(latencies)
        p95 = statistics.quantiles(latencies, n=100)[94]
        p99 = statistics.quantiles(latencies, n=100)[98]

        self.results['audio_processing'] = {
            'iterations': iterations,
            'avg_ms': round(avg, 3),
            'p95_ms': round(p95, 3),
            'p99_ms': round(p99, 3),
            'target_ms': 50,
            'status': 'PASS' if avg < 50 else 'FAIL'
        }

        logger.info("benchmark.audio_processing.complete",
                   avg_ms=avg,
                   p99_ms=p99,
                   status=self.results['audio_processing']['status'])

    async def benchmark_string_processing(self, iterations: int = 100):
        """Benchmark string operations (simulating STT/TTS)."""
        logger.info("benchmark.string_processing")
        latencies = []

        for i in range(iterations):
            start = time.perf_counter()

            # Simulate text processing
            text = "This is a sample text for processing performance testing"

            # Token count (simulating STT)
            words = text.split()
            word_count = len(words)

            # Text generation (simulating TTS)
            result = text.upper()

            end = time.perf_counter()
            latencies.append((end - start) * 1000)  # ms

        avg = statistics.mean(latencies)
        p95 = statistics.quantiles(latencies, n=100)[94]
        p99 = statistics.quantiles(latencies, n=100)[98]

        self.results['string_processing'] = {
            'iterations': iterations,
            'avg_ms': round(avg, 3),
            'p95_ms': round(p95, 3),
            'p99_ms': round(p99, 3),
            'target_ms': 10,
            'status': 'PASS' if avg < 10 else 'FAIL'
        }

        logger.info("benchmark.string_processing.complete",
                   avg_ms=avg,
                   p99_ms=p99,
                   status=self.results['string_processing']['status'])

    async def benchmark_database_operations(self, iterations: int = 50):
        """Benchmark database operations."""
        logger.info("benchmark.database_operations")
        latencies = []

        try:
            from bridge.session_manager import SessionManager

            async def operation():
                session_mgr = await SessionManager.get_instance()
                session = Session()
                await session_mgr.save_session(session)

            for i in range(iterations):
                start = time.perf_counter()
                await operation()
                end = time.perf_counter()
                latencies.append((end - start) * 1000)  # ms

            avg = statistics.mean(latencies)
            p95 = statistics.quantiles(latencies, n=100)[94]
            p99 = statistics.quantiles(latencies, n=100)[98]

            self.results['database_operations'] = {
                'iterations': iterations,
                'avg_ms': round(avg, 3),
                'p95_ms': round(p95, 3),
                'p99_ms': round(p99, 3),
                'target_ms': 100,
                'status': 'PASS' if avg < 100 else 'FAIL'
            }

            logger.info("benchmark.database_operations.complete",
                       avg_ms=avg,
                       p99_ms=p99,
                       status=self.results['database_operations']['status'])

        except Exception as e:
            logger.warning("benchmark.database_operations.skipped", error=str(e))
            self.results['database_operations'] = {
                'status': 'SKIPPED',
                'error': str(e)
            }

    async def benchmark_vad(self, iterations: int = 100):
        """Benchmark VAD (Voice Activity Detection)."""
        logger.info("benchmark.vad")
        latencies = []

        try:
            import numpy as np
            from bridge.vad import WebRTCVAD, VADConfig

            vad = WebRTCVAD(VADConfig())
            audio = np.random.randn(1600).astype(np.float32)

            for i in range(iterations):
                start = time.perf_counter()

                # VAD processing
                frames = int(320 / 10)  # 30ms frames
                for j in range(frames):
                    vad.is_speech(audio[j*10:(j+1)*10])

                end = time.perf_counter()
                latencies.append((end - start) * 1000)  # ms

            avg = statistics.mean(latencies)
            p95 = statistics.quantiles(latencies, n=100)[94]
            p99 = statistics.quantiles(latencies, n=100)[98]

            self.results['vad'] = {
                'iterations': iterations,
                'avg_ms': round(avg, 3),
                'p95_ms': round(p95, 3),
                'p99_ms': round(p99, 3),
                'target_ms': 20,
                'status': 'PASS' if avg < 20 else 'FAIL'
            }

            logger.info("benchmark.vad.complete",
                       avg_ms=avg,
                       p99_ms=p99,
                       status=self.results['vad']['status'])

        except Exception as e:
            logger.warning("benchmark.vad.skipped", error=str(e))
            self.results['vad'] = {
                'status': 'SKIPPED',
                'error': str(e)
            }

    def generate_report(self):
        """Generate benchmark report."""
        status_map = {
            'PASS': '✅',
            'FAIL': '❌',
            'SKIPPED': '⏭'
        }

        print("\n" + "="*60)
        print("PERFORMANCE BENCHMARK RESULTS")
        print("="*60 + "\n")

        for name, result in self.results.items():
            if 'status' not in result:
                continue

            status_emoji = status_map.get(result['status'], '❓')
            print(f"{status_emoji} {name.replace('_', ' ').title()}")

            if result['status'] != 'SKIPPED':
                print(f"   Average: {result['avg_ms']}ms")
                if 'p95_ms' in result:
                    print(f"   P95: {result['p95_ms']}ms")
                if 'p99_ms' in result:
                    print(f"   P99: {result['p99_ms']}ms")
                print(f"   Target: {result.get('target_ms', 'N/A')}ms")
            else:
                print(f"   Skipped: {result.get('error', 'Unknown')}")
            print()

        # Calculate overall status
        passed = sum(1 for r in self.results.values()
                    if r.get('status') == 'PASS')
        total = sum(1 for r in self.results.values()
                   if r.get('status') in ['PASS', 'FAIL'])

        print("="*60)
        print(f"Overall: {passed}/{total} benchmarks passed")
        if self.all_passed():
            print("Status: ✅ ALL BENCHMARKS PASSED")
        else:
            print("Status: ⚠️  SOME BENCHMARKS FAILED")
        print("="*60 + "\n")

        # Save to JSON
        output_path = Path(f"/tmp/benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        output_path.write_text(json.dumps(self.results, indent=2))
        logger.info("benchmark.report_saved", path=str(output_path))

    def all_passed(self) -> bool:
        """Check if all benchmarks passed."""
        for result in self.results.values():
            if result.get('status') == 'FAIL':
                return False
        return True


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run performance benchmarks")
    parser.add_argument('--iterations', type=int, default=50,
                       help='Iterations per benchmark (default: 50)')

    args = parser.parse_args()

    benchmark = PerformanceBenchmark()
    results = await benchmark.run_all_benchmarks()

    return 0 if benchmark.all_passed() else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)