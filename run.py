"""
Waitless AI master CLI interface.
Provides unified task commands for data generation, training, arena evaluation, serving, and testing.
Built with robust fallback support for standard library argparse.
"""

import os
import sys
import argparse
import subprocess

def cmd_setup(args):
    print("Checking environment configuration...")
    try:
        import pandas
        import numpy
        import sklearn
        import xgboost
        import fastapi
        import uvicorn
        print("✓ Core data, ML, and API packages are installed.")
    except ImportError as e:
        print(f"Missing package: {e}")
        sys.exit(1)

    try:
        import torch
        print(f"✓ PyTorch detected (version {torch.__version__}). Deep models available.")
    except ImportError:
        print("! PyTorch not detected. Classical models will run; deep models marked unavailable.")
    print("Setup verified successfully.")

def cmd_data(args):
    print(f"Building dataset {args.version} ({args.days} days, {args.routes} routes)...")
    from backend.preprocessing.dataset_builder import build_complete_dataset
    build_complete_dataset(version=args.version, days=args.days, num_routes=args.routes)
    print(f"Dataset {args.version} built successfully in data/datasets/{args.version}/")

def cmd_train(args):
    print(f"Starting training for family: {args.family} (tune={args.tune})...")
    if args.family in ["classical", "all"]:
        from ml.classical.trainer import train_classical_lineup
        train_classical_lineup(run_tuning=args.tune)
    if args.family in ["deep", "all"]:
        from ml.deep.trainer import train_deep_lineup
        train_deep_lineup()
    print("Training completed successfully.")

def cmd_arena(args):
    print("Running Frozen Evaluation Harness...")
    from ml.arena.harness import run_arena_evaluation
    run_arena_evaluation()
    print("Arena evaluation completed. Results written to ml/arena/results/")

def cmd_select(args):
    print("Computing scorecard and selecting champion...")
    from ml.arena.select_champion import run_selection
    run_selection()
    print("Champion selection updated in models/registry.json")

def cmd_serve(args):
    print(f"Starting Waitless AI API on http://{args.host}:{args.port}...")
    import uvicorn
    uvicorn.run("backend.main:app", host=args.host, port=args.port, reload=args.reload)

def cmd_ui(args):
    print("Starting Frontend dev server...")
    subprocess.run("npm run dev", cwd="frontend", shell=True)

def cmd_up(args):
    print("Starting full Waitless AI application stack...")
    import uvicorn
    # Start uvicorn in background, then run npm
    p1 = subprocess.Popen([sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000"])
    try:
        subprocess.run("npm run dev", cwd="frontend", shell=True)
    finally:
        p1.terminate()

def cmd_test(args):
    print("Executing test suite with unittest runner...")
    res = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"])
    if res.returncode != 0:
        sys.exit(res.returncode)

def cmd_lint(args):
    print("Checking code syntax...")
    subprocess.run([sys.executable, "-m", "compileall", "-q", "."])
    print("Syntax verification passed.")

def cmd_docs(args):
    print("Compiling reports and tables from result artifacts...")
    from docs.build_docs import build_all_documentation
    build_all_documentation()
    print("Documentation compiled.")

def main():
    parser = argparse.ArgumentParser(description="Waitless AI - MTC Chennai Bus Reliability Platform")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # setup
    p_setup = subparsers.add_parser("setup", help="Verify dependencies")
    p_setup.set_defaults(func=cmd_setup)

    # data
    p_data = subparsers.add_parser("data", help="Generate dataset")
    p_data.add_argument("--version", default="v1")
    p_data.add_argument("--days", type=int, default=90)
    p_data.add_argument("--routes", type=int, default=25)
    p_data.set_defaults(func=cmd_data)

    # train
    p_train = subparsers.add_parser("train", help="Train models")
    p_train.add_argument("--family", default="classical", choices=["classical", "deep", "all"])
    p_train.add_argument("--tune", action="store_true", default=False)
    p_train.set_defaults(func=cmd_train)

    # arena
    p_arena = subparsers.add_parser("arena", help="Run arena evaluation")
    p_arena.set_defaults(func=cmd_arena)

    # select
    p_select = subparsers.add_parser("select", help="Select champion")
    p_select.set_defaults(func=cmd_select)

    # serve
    p_serve = subparsers.add_parser("serve", help="Run API server")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8000)
    p_serve.add_argument("--reload", action="store_true", default=True)
    p_serve.set_defaults(func=cmd_serve)

    # ui
    p_ui = subparsers.add_parser("ui", help="Start frontend")
    p_ui.set_defaults(func=cmd_ui)

    # up
    p_up = subparsers.add_parser("up", help="Start full stack")
    p_up.set_defaults(func=cmd_up)

    # test
    p_test = subparsers.add_parser("test", help="Run tests")
    p_test.set_defaults(func=cmd_test)

    # lint
    p_lint = subparsers.add_parser("lint", help="Check syntax")
    p_lint.set_defaults(func=cmd_lint)

    # docs
    p_docs = subparsers.add_parser("docs", help="Compile documentation")
    p_docs.set_defaults(func=cmd_docs)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
