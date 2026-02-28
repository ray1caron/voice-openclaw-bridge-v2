#!/usr/bin/env python3
"""
Stability Testing Framework

Runs 8-hour stability test with monitoring and health checks.
"""

import asyncio
import time
import json
import signal
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import structlog

from bridge.voice_orchestrator import VoiceOrchestrator, OrchestratorConfig

logger = structlog.get_logger()


class StabilityTest:
    """Long-running stability test with monitoring."""

    def __init__(self, duration_hours: int = 8):
        self.duration_hours = duration_hours
        self.duration_seconds = duration_hours * 3600
        self.start_time: float = 0
        self.checkpoints: List[Dict] = []
        self.errors: List[Dict] = []
        self.crashes: int = 0

    async def run_test(self):
        """Run stability test."""
        self.start_time = time.time()
        end_time = self.start_time + self.duration_seconds

        logger.info("stability_test.starting",
                   duration_hours=self.duration_hours,
                   end_time=datetime.fromtimestamp(end_time).isoformat())

        # Initialize orchestrator
        logger.info("stability_test.initializing_orchestrator")
        config = OrchestratorConfig(
            wake_word_keyword="computer",
            wake_word_sensitivity=0.85,
            barge_in_enabled=True,
        )
        orchestrator = VoiceOrchestrator(config=config)

        # Shutdown handler
        shutdown_event = asyncio.Event()

        def signal_handler(signum, frame):
            logger.info("stability_test.shutdown_requested")
            shutdown_event.set()
            orchestrator.stop()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        try:
            # Start monitoring task
            monitor_task = asyncio.create_task(self.monitor(orchestrator, shutdown_event))

            # Run orchestrator (simulated or real)
            logger.info("stability_test.running_orchestrator")
            await orchestrator.run()

            # Wait for test completion or shutdown
            await shutdown_event.wait()

        except Exception as e:
            logger.error("stability_test.error", error=str(e), exc_info=True)
            self.errors.append({
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'type': type(e).__name__
            })

        finally:
            monitor_task.cancel()
            orchestrator.stop()

        # Generate report
        self.generate_report()

    async def monitor(self, orchestrator: VoiceOrchestrator, shutdown_event: asyncio.Event):
        """Monitor system health periodically."""
        logger.info("stability_test.monitoring_started")

        next_checkpoint = self.start_time
        checkpoint_interval = 300  # 5 minutes (for testing, use 3600 for production)

        while not shutdown_event.is_set():
            current_time = time.time()

            # Check if we should take a checkpoint
            if current_time >= next_checkpoint:
                await self.take_checkpoint(orchestrator, current_time)
                next_checkpoint = checkpoint_interval

            # Check if test duration reached
            if (current_time - self.start_time) >= self.duration_seconds:
                logger.info("stability_test.duration_reached")
                shutdown_event.set()
                break

            # Sleep until next check
            await asyncio.sleep(10)

    async def take_checkpoint(self, orchestrator: VoiceOrchestrator, current_time: float):
        """Take a periodic health checkpoint."""
        try:
            stats = orchestrator.get_stats()

            checkpoint = {
                'timestamp': datetime.now().isoformat(),
                'elapsed_seconds': current_time - self.start_time,
                'elapsed_hours': (current_time - self.start_time) / 3600,
                'statistics': {
                    'total_interactions': stats.total_interactions,
                    'successful_interactions': stats.successful_interactions,
                    'interrupted_interactions': stats.interrupted_interactions,
                    'failed_interactions': stats.failed_interactions,
                    'wake_word_detections': stats.wake_word_detections,
                    'transcriptions': stats.transcriptions,
                    'tts_syntheses': stats.tts_syntheses,
                    'total_time_ms': stats.total_time_ms,
                    'average_interaction_time_s': stats.average_interaction_time_s,
                },
            }

            self.checkpoints.append(checkpoint)

            logger.info("stability_test.checkpoint",
                       checkpoint_number=len(self.checkpoints),
                       elapsed_hours=checkpoint['elapsed_hours'],
                       total_interactions=stats.total_interactions)

        except Exception as e:
            logger.error("stability_test.checkpoint_error", error=str(e))
            self.errors.append({
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'type': type(e).__name__,
                'context': 'checkpoint'
            })

    def generate_report(self):
        """Generate test report."""
        end_time = time.time()
        duration_seconds = end_time - self.start_time
        duration_hours = duration_seconds / 3600

        # Calculate metrics
        total_interactions = max([c['statistics']['total_interactions']
                                for c in self.checkpoints]) if self.checkpoints else 0

        successful_interactions = max([c['statistics']['successful_interactions']
                                     for c in self.checkpoints]) if self.checkpoints else 0

        failed_interactions = max([c['statistics']['failed_interactions']
                                 for c in self.checkpoints]) if self.checkpoints else 0

        avg_latency = max([c['statistics']['average_interaction_time_s']
                         for c in self.checkpoints]) if self.checkpoints else 0

        error_rate = (len(self.errors) / total_interactions * 100) if total_interactions > 0 else 0

        report = {
            'test_info': {
                'start_time': datetime.fromtimestamp(self.start_time).isoformat(),
                'end_time': datetime.fromtimestamp(end_time).isoformat(),
                'duration_seconds': duration_seconds,
                'duration_hours': duration_hours,
            },
            'summary': {
                'total_interactions': total_interactions,
                'successful_interactions': successful_interactions,
                'failed_interactions': failed_interactions,
                'crashes': self.crashes,
                'errors_count': len(self.errors),
                'error_rate_percent': round(error_rate, 2),
                'average_latency_s': round(avg_latency, 3),
            },
            'checkpoints': self.checkpoints,
            'errors': self.errors,
        }

        # Save report
        output_path = Path(f"/tmp/stability_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        output_path.write_text(json.dumps(report, indent=2))

        logger.info("stability_test.report_saved", path=str(output_path))

        # Print summary
        print("\n" + "="*60)
        print("STABILITY TEST SUMMARY")
        print("="*60)
        print(f"Duration: {duration_hours:.2f} hours")
        print(f"Total Interactions: {total_interactions}")
        print(f"Successful: {successful_interactions}")
        print(f"Failed: {failed_interactions}")
        print(f"Crashes: {self.crashes}")
        print(f"Errors: {len(self.errors)}")
        print(f"Error Rate: {error_rate:.2f}%")
        print(f"Average Latency: {avg_latency:.3f}s")
        print("\nStatus: ✅ PASSED" if self.is_passed(report) else "❌ FAILED")
        print("="*60 + "\n")

        return report

    def is_passed(self, report: Dict) -> bool:
        """Check if test passed criteria."""
        summary = report['summary']

        # Criteria:
        # - No crashes
        # - Error rate < 1%
        # - At least some interactions (test actually ran)
        return (
            summary['crashes'] == 0 and
            summary['error_rate_percent'] < 1.0 and
            summary['total_interactions'] > 0
        )


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Run stability test")
    parser.add_argument('--duration', type=int, default=8,
                       help='Test duration in hours (default: 8)')
    parser.add_argument('--quick', action='store_true',
                       help='Run quick test (5 minutes)')

    args = parser.parse_args()

    duration = args.quick * (5/3600) if args.quick else args.duration

    test = StabilityTest(duration_hours=duration)
    await test.run_test()


if __name__ == "__main__":
    asyncio.run(main())