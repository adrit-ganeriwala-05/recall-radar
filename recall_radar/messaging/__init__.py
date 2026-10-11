"""PRD v2 F9: opt-in iMessage updates and answers via Photon Spectrum (hosted iMessage, Stable docs).

A separate service (`recall_radar.messaging.app:app`) with its own SQLite file; never imported by the analysis
API. Off unless RR_MESSAGING_ENABLED=1, and live only after D's Gate P. Provider facts:
docs/handoffs/20261011-0110-A-to-D-sources-v2.md.
"""
