import sys
from .cli import main

try:
    main()
except (ValueError, FileNotFoundError, RuntimeError, ImportError) as exc:
    print(f"MiniSense error: {exc}", file=sys.stderr)
    sys.exit(1)
