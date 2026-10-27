"""
Main Launcher: Smart Code Analyzer and Execution Simulator
Provides unified entry point for Web UI Server, CLI tool, and Test Suite.
"""

import sys
import argparse
from src.server import run_server


def main():
    parser = argparse.ArgumentParser(description="Smart Code Analyzer and Execution Simulator")
    parser.add_argument("--cli", action="store_true", help="Launch in Command-Line Interface mode")
    parser.add_argument("--test", action="store_true", help="Run automated test suite")
    parser.add_argument("--port", "-p", type=int, default=8000, help="Port for Web Dashboard server (default: 8000)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host address for Web Dashboard (default: 0.0.0.0)")

    args, unknown = parser.parse_known_args()

    if args.test:
        import unittest
        print("Running full test suite for FLAT, COA, and DAA modules...\n")
        suite = unittest.defaultTestLoader.discover("tests")
        runner = unittest.TextTestRunner(verbosity=2)
        res = runner.run(suite)
        sys.exit(0 if res.wasSuccessful() else 1)

    if args.cli:
        from cli import main as cli_main
        sys.argv = [sys.argv[0]] + unknown
        cli_main()
        return

    # Default: launch web server
    run_server(port=args.port, host=args.host)


if __name__ == "__main__":
    main()
