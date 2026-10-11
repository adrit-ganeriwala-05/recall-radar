"""Recall Radar v2 code owned by B. It lives outside `recall_radar/method/` on purpose.

`freeze-v1` covers the whole `recall_radar/method/` directory (evaluate.check_freeze), and that
directory is a pipeline input (evaluate.PIPELINE_PATHS). A file added there would make the
held-out evaluation refuse to run and would change the run ids in every result file. Nothing in
this package is imported by the detector, the matcher or the evaluation.
"""
