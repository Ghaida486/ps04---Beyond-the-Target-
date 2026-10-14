#!/usr/bin/env bash
# A receipt for each coordination invocation, preserved across retries.
workflow_receipt() {
  python3 - "$1" "$2" "$3" "$4" <<'PY'
import sys
sys.path.insert(0,'lib')
from common import *
s=Stage(sys.argv[1],sys.argv[2]); s.start=sys.argv[4]
if sys.argv[3]!='0': s.error('One or more coordinated components failed; inspect component receipts')
s.finish(int(sys.argv[3]))
PY
}
