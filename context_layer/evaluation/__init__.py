"""Evaluation layer for the Context Layer prototype — see docs/evaluation.md."""

import os

# deepeval phones home to PostHog by default on nearly every operation
# (metric construction, `measure()`, even import in some versions). That's
# an unexpected outbound call for a governed enterprise system's own test
# suite to make, so opt out before anything else in this package can
# import deepeval. `setdefault` so an operator who explicitly wants
# telemetry can still override it.
os.environ.setdefault("DEEPEVAL_TELEMETRY_OPT_OUT", "YES")
