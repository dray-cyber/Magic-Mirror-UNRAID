#!/usr/bin/env python3
"""Launch the dashboard on your trusted local network by default."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent/'app'))
from mirror import main
if __name__=='__main__':
    if '--local' in sys.argv:sys.argv.remove('--local')
    elif '--lan' not in sys.argv:sys.argv.append('--lan')
    main()
