# HANDOFF B→D: Gate B evidence map for B's parts (PRD_v2 §9: every criterion needs a named test or a recorded inspection)
- From: B · To: D (docs/GATE_B.md, docs/LEDGER.md) · Contract 1.1.0 · Snapshot e808281f001a · freeze-v1 → dd6b439
- All tests below are in `tests/method/`. "real" = marked `real_data`: run with `RR_DATA_DIR=<dir with the DB>`.
- One command for the frozen-science suite and all of these: `uv run pytest tests/method` (and `-m real_data` for the real ones).
- Statuses are B's view of B's part only; "verified" is yours to give after the deploy check.

## Protection (PRD §1)
| What | Evidence |
| --- | --- |
| Baseline tables checksum-identical in the v2 DB | `uv run python -m recall_radar.b_v2.protect <baseline> <v2>` → `PROTECTED TABLES: IDENTICAL`; tool tests `test_v2_protect.py` (4 functions) |
| Results files byte-identical | `test_committed_result_files_still_have_their_baseline_hashes`; `make protected` (yours) |
| Frozen inputs unchanged | `uv run python -c "from recall_radar.method import evaluate as E; print(E.check_freeze('config.yaml','.'))"` → `freeze-v1`; frozen-science tests `test_freeze_*`, `test_held_out_refuses_*` |
| Reproducibility | `git checkout baseline-v1 && RR_RAW_DIR=… make repro` → MATCH ×4 (record: `20261010-2145-B-to-D-b10-repro.md`) |

## F2 — status `fallback(no GEMINI_API_KEY; google-genai not installed; no model name)`
| Criterion | Evidence |
| --- | --- |
| F2.1 table with a row per campaign, default fallback | `test_table_has_one_fallback_row_per_campaign_by_default`; real: `recall_explanation` 13,673 rows, all fallback (command prints "fallback only (13673 campaigns)") |
| F2.2 generation only with key + working call; bounded | `test_timeout_quota_and_missing_credentials_all_fall_back`, `test_generation_is_bounded_and_campaigns_without_text_never_reach_the_model`, `test_generate_without_credentials_still_writes_every_row_as_fallback` |
| F2.3 input fields, JSON output, ≤ 2 sentences, ≤ 45 words, fields + spans | `test_grounded_output_is_accepted_and_fits_the_contract`, `test_validator_rejects` (29 cases) |
| F2.4 validator rejections | `test_validator_rejects`, `test_if_equipped_must_be_kept`, `test_citing_a_field_the_record_does_not_have_is_rejected`, `test_text_hidden_in_the_official_record_is_data_not_an_instruction` |
| F2.5 cache key | `test_cache_key_changes_with_source_model_and_prompt_version`, `test_cache_is_used_and_a_changed_source_is_generated_again` |
| F2.6 B reads every accepted explanation | recorded inspection: none exists (METHOD_NOTES §12.5) |
| F2.7 UI label | C's `RecallCard` tests (not B's) |
| F2.8 status wording | `test_status_line_and_no_frozen_import` |

## F3 (B's part: linkage and bundle) — implemented; UI is C's
| Criterion | Evidence |
| --- | --- |
| F3.1 issue = family campaigns, vehicle = same make/model/year, never by component | `test_issue_links_come_from_the_family_and_vehicle_links_from_the_exact_vehicle`, `test_component_is_never_read`, `test_committed_replays_carry_link_kinds_on_recall_markers_only` |
| F3.2 date = report date; no dated record → no marker | same first test (undated and missing campaigns); `test_replay_without_a_family_or_without_campaigns`; basis RCDATE recorded in METHOD_NOTES §12.2 |
| F3.5 only replay markers change | `test_rewrite_changes_only_the_recall_markers_and_is_idempotent`, `test_apply_touches_replays_and_their_manifest_lines_only`, `test_apply_refuses_a_bundle_whose_results_do_not_match_the_manifest`, real: `test_real_bundle_keeps_frames_results_and_issue_markers`; `make protected` |
| On-demand replays (not in the PRD, same rule) | A's `test_replay_built_from_the_database_gets_f3_recall_links` (PR #44); B's real-data check: 709 markers on 100 episodes, 0 rule violations |
| Known data fact for the drawer | 66 of 81 issue-linked markers name a campaign that does not list the replay's own vehicle; C's drawer says so (PR #36) |

## F7 (B's part: index, rules, evaluation) — implemented; API is A's, UI is C's
| Criterion | Evidence |
| --- | --- |
| F7.1 ≥ 40 reviewed alias rows incl. the four examples | `test_alias_file_is_reviewed_and_covers_the_prd_examples` (52 rows, reviewer B) |
| F7.2 pairs never merge | `test_distinct_concepts_do_not_merge` (4 pairs, as queries and as complaint texts), `test_queries_map_to_exactly_one_concept` |
| F7.3 30 queries committed before tuning; precision at 5 on 3 vehicles, measured | commit d1a6130 precedes every rule; `test_committed_evaluation_set_passes`; real: `test_real_judgments_cover_the_current_top_results`; command `python -m recall_radar.b_v2.symptom_eval --db <baseline>` (output in METHOD_NOTES §12.4) |
| F7.4 (index contents) | A's endpoint tests; B's check: aliases and concepts served equal the review files, served docs = the judged documents |
| F7.5–F7.7 | C's tests; parity: `test_parity_file_for_the_browser_port_is_current` + C's `symptoms.test.ts`; B's real-index comparison (26,185 hits identical) |
| F7.8 not in replay, never read by the detector | `test_frozen_pipeline_and_replay_never_touch_the_symptom_index`, `test_no_model_or_embedding_dependency`, `test_search_sees_only_the_documents_it_is_given` |

## F8 (B's part: selection) — implemented; endpoint is A's, render is D's
| Criterion | Evidence |
| --- | --- |
| F8.1 counts equal `/api/vehicle` | real: `test_real_report_counts_equal_the_vehicle_endpoint` (40 vehicles); B's endpoint comparison on 200 vehicles (PR #30 review) |
| F8.2 top 5 groups with tie-break; ≤ 5 investigations newest first; ≤ 6 campaigns newest first; n of m | `test_top_five_issue_groups_with_ties_in_alphabetical_order`, `test_investigations_newest_first_one_per_action_and_only_this_model_year`, `test_campaigns_one_per_campno_newest_first_at_most_six`, `test_vehicle_without_data_gives_an_empty_report_not_an_error` |
| F8.3 date range, counting basis, selection rule sentence | `test_counts_and_complaint_date_range`, `test_selection_rule_states_the_limits_and_makes_no_banned_claim` |
