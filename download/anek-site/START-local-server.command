#!/bin/sh
cd "$(dirname "$0")/site" || exit 1
echo "Serving the Anak website at http://localhost:8000"
echo "Press Ctrl+C to stop."
(sleep 1; (command -v xdg-open >/dev/null && xdg-open http://localhost:8000) \
  || (command -v open >/dev/null && open http://localhost:8000)) >/dev/null 2>&1 &
python3 -m http.server 8000 2>/dev/null || python -m http.server 8000
