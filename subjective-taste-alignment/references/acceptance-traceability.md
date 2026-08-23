# Acceptance traceability

The canonical catalog contains `AC-001` through `AC-079`, in governing-spec order. See [final-acceptance-criteria.md](final-acceptance-criteria.md). Callers cannot substitute a smaller catalog.

Map each identifier to one or more checks with these fields:

| Field | Requirement |
| --- | --- |
| `id` | Stable check identifier |
| `criterion_id` | Exact stable acceptance-criterion identifier |
| `kind` | `scenario` or `structural` |
| `target` | Executable test path or observable structural target |
| `oracle` | Explicit condition that distinguishes pass from fail |
| `passed` | Actual result of executing or observing the check |

Use `TraceabilityCheck` and `assess_traceability` from `scripts/alignment_harness.py` to validate a machine-readable mapping. A canonical criterion without a valid check, an unknown or duplicate identifier, a check without a target or oracle, or a check that has not passed keeps the mapping incomplete.

## Ticket 01 mappings

| Criterion | Check | Kind | Target | Oracle |
| --- | --- | --- | --- | --- |
| `AC-001` | `capability-supported-or-constrained` | scenario | `tests/test_capability_contract.py` | Every required capability resolves through direct evidence or an enforced, capability-appropriate fallback. |
| `AC-078` | `traceability-validation` | scenario | `tests/test_traceability.py` | The canonical 79-criterion catalog cannot be replaced by a caller-supplied subset. |
| `AC-079` | `alignment-scenario-substrate` | scenario | `tests/test_scenario_harness.py` | User paths expose state, retry, interruption, restart, and cross-feature behavior through the public seam. |

Ticket-local checks also cover unknown authorship, proxy rejection, actual-host declaration, retry isolation, and unsupported-operation blockers. Later tickets must extend the final mapping when they implement their criteria. Until every canonical criterion has a passing mapped check, `assess_traceability` returns incomplete and the skill reports itself incomplete.

## Ticket 02 mappings

| Criterion | Check | Kind | Target | Oracle |
| --- | --- | --- | --- | --- |
| `AC-002` | `canonical-alignment-result` | scenario | `tests/test_alignment_contract.py` | Every material dimension resolves through one result that retains each semantic source and exposes governing source, unresolved state, materiality, checkpoints, provenance, dependencies, and revision identity. |
| `AC-003` | `stale-alignment-guard` | scenario | `tests/test_alignment_contract.py` | A changed decision-bearing input makes the old result stale and `authorize_propagation` rejects it until re-resolution. |
| `AC-004` | `unresolved-material-gate` | scenario | `tests/test_alignment_contract.py` | An unresolved material dimension produces a checkpoint and cannot propagate. |
| `AC-006` | `delegation-is-not-taste` | scenario | `tests/test_alignment_contract.py` | In-scope delegated judgment resolves execution while reusable taste remains unresolved. |
| `AC-007` | `semantic-source-separation` | scenario | `tests/test_alignment_contract.py` | Constraints, ownership, intent, taste, authority, experimental state, and craft priors retain separate fields and governing-source labels. |
| `AC-008` | `dimension-scoped-intent` | scenario | `tests/test_alignment_contract.py` | Intent governs only its named dimension while taste governs unconstrained dimensions. |
| `AC-010` | `known-indifference` | scenario | `tests/test_alignment_contract.py` | Known indifference permits an authorized craft decision without preference calibration or invented taste. |
| `AC-074` | `craft-prior-is-not-taste` | scenario | `tests/test_alignment_contract.py` | Delegated craft detail can resolve execution without creating preference knowledge. |

## Ticket 03 mappings

| Criterion | Check | Kind | Target | Oracle |
| --- | --- | --- | --- | --- |
| `AC-024` | `applicability-not-narrowness` | scenario | `tests/test_profile_composition.py` | Requested scope, exact active scope identity, context, evidence, ownership, and explicit overrides determine applicability; a narrower claim does not win automatically. |
| `AC-025` | `scope-lifetime-and-transition` | scenario | `tests/test_profile_composition.py` | Expired session knowledge and authority, unrelated project, represented-subject, and non-target local state remain excluded, while duplicate, branch, copy, and move preserve identity, create a new identity, or surface ambiguity explicitly. |
| `AC-026` | `profile-application-levels` | scenario | `tests/test_profile_composition.py` | Full-profile, section-level, and exact-property selections return only exposed requested properties. |
| `AC-027` | `profile-semantic-conflicts` | scenario | `tests/test_profile_composition.py` | Compatible knowledge composes with provenance and relationships; incompatible directions and cross-property requirements unsatisfied by full resolved semantic state remain explicit unresolved conflicts. |
| `AC-036` | `confidence-reduced-transfer` | scenario | `tests/test_profile_composition.py` | Cross-domain or distant-context reuse requires an explicit transfer policy and returns reduced effective confidence without mutating canonical knowledge. |

Ticket 03 also verifies that contextual and relational knowledge survives applicability and composition. The Ticket 04 mapping below completes `AC-028` through persistence retrieval.

## Ticket 04 mappings

| Criterion | Check | Kind | Target | Oracle |
| --- | --- | --- | --- | --- |
| `AC-028` | `context-survives-storage-retrieval` | scenario | `tests/test_profile_persistence.py::test_canonical_round_trip_preserves_all_current_profile_semantics` | Canonical serialize/deserialize restores contextual and relational knowledge byte-for-byte; loaded state equals saved state including scope, owner, freshness, and relationships. |
| `AC-029` | `canonical-round-trip-without-reinterpretation` | scenario | `tests/test_profile_persistence.py::test_canonical_round_trip_preserves_all_current_profile_semantics`; `tests/test_profile_lifecycle.py::test_export_import_round_trip_preserves_semantics_and_boundaries` | Round-tripped profiles, events, claims, and branches compare equal to their sources; nothing strengthens, flattens, broadens, or reinterprets semantics. |
| `AC-030` | `stale-snapshot-and-interrupted-write-safety` | scenario | `tests/test_profile_persistence.py::test_stale_save_surfaces_valid_external_state_without_overwriting_it`, `::test_failed_atomic_write_recovers_exactly_the_old_or_new_complete_state`, `::test_interrupted_write_recovers_old_or_new_state_and_cleans_abandoned_temp` | A stale expected revision raises RevisionConflictError without overwriting newer external state; injected write failures and interruptions recover exactly the old or new complete valid state with no epistemic corruption and no leftover temp files. |

## Ticket 05 mappings

| Criterion | Check | Kind | Target | Oracle |
| --- | --- | --- | --- | --- |
| `AC-039` | `quality-controls-confidence-not-count` | scenario | `tests/test_evidence_reconciliation.py::test_conflicting_evidence_resolves_by_quality_not_vote_count`, `::test_repeated_near_equivalent_observations_do_not_manufacture_certainty` | One strong explicit correction defeats three weak inferred votes with the reason citing quality; five near-equivalent observations sharing an independence key cap confidence while genuine corroboration lifts it modestly. |
| `AC-042` | `silence-and-delegation-non-evidence` | scenario | `tests/test_evidence_reconciliation.py::test_silence_and_delegation_never_become_preference_evidence`, `::test_acceptance_execution_rejection_and_success_do_not_become_taste` | Silence, continued progress, delegated execution success, approval, execution-quality rejection, and implementation success journal zero preference claims with exact non-evidence reasons. |
| `AC-044` | `bundle-evidence-not-over-decomposed` | scenario | `tests/test_evidence_reconciliation.py::test_comparisons_preserve_bundle_range_boundary_and_relationship_claims` | Bundle, range, boundary, and relationship comparisons persist as structured composite claims with encoded directions and relationship metadata instead of per-item claims. |
| `AC-045` | `ranges-and-boundaries-learnable` | scenario | `tests/test_evidence_reconciliation.py::test_comparisons_preserve_bundle_range_boundary_and_relationship_claims`, `::test_none_of_these_narrows_only_the_explored_region` | Supported ranges and boundaries become established structured knowledge; rejection narrows exactly the explored region without inventing directions outside it. |
| `AC-046` | `none-of-these-bounded-evidence` | scenario | `tests/test_evidence_reconciliation.py::test_none_of_these_narrows_only_the_explored_region` | “None of these” yields one rejected range-kind claim over exactly the explored region and no alternative direction. |
| `AC-047` | `observable-actions-need-inferable-meaning` | scenario | `tests/test_evidence_reconciliation.py::test_material_ambiguity_preserves_unresolved_property_for_clarification`, `::test_conflicting_evidence_resolves_by_quality_not_vote_count` | Observable actions contribute only weak inferred support; materially ambiguous observations produce no claim and instead request clarification listing plausible dimensions. |

## Ticket 06 mappings

| Criterion | Check | Kind | Target | Oracle |
| --- | --- | --- | --- | --- |
| `AC-040` | `evidence-replay-idempotent` | scenario | `tests/test_evidence_reconciliation.py::test_replay_is_idempotent_while_distinct_observations_stay_separate` | Replaying one operation returns REPLAYED with unchanged state; distinct events apply separately; identity reuse with altered content raises OperationIdentityConflictError or EvidenceIdentityConflictError. |
| `AC-041` | `promotion-attributable-and-applicable` | scenario | `tests/test_evidence_reconciliation.py::test_promotion_is_proportionate_to_consequence`, `::test_newer_strong_explicit_evidence_replaces_established_claim` | Promotion requires attributable, applicable, sufficiently represented evidence proportionate to consequence; replacement carries new provenance and marks superseded support. |
| `AC-043` | `conflicts-resolve-by-strength` | scenario | `tests/test_evidence_reconciliation.py::test_incomparable_conflicting_evidence_returns_unresolved_without_averaging`, `::test_conflict_checkpoint_requests_resolution_of_the_disagreement` | Incomparable conflicts stay UNRESOLVED with both supports referenced and no averaging; comparable conflicts checkpoint resolution scoped to the disputed dimension. |
| `AC-070` | `contradictions-reopen-alignment` | scenario | `tests/test_evidence_reconciliation.py::test_later_material_contradiction_demotes_established_knowledge`, `::test_branch_inapplicable_support_excludes_one_implication_only` | A later material contradiction demotes established knowledge and stales prior support; applicability exclusion removes exactly its own implication while siblings survive. |

## Ticket 07 mappings

| Criterion | Check | Kind | Target | Oracle |
| --- | --- | --- | --- | --- |
| `AC-005` | `provisional-execution-under-active-authority` | scenario | `tests/test_alignment_contract.py::test_delegated_judgment_resolves_execution_without_becoming_taste` | An in-scope provisional judgment resolves as authorized judgment with unresolved taste retained and propagation eligible; taste stays unresolved rather than strengthened. |
| `AC-009` | `authority-changes-prospective` | scenario | `tests/test_decision_policy.py::test_runtime_autonomy_change_is_prospective_and_preserves_completed_decision` | Completed decisions keep their alignment, provenance, and route after an autonomy change; later sequences gain the stricter preset's checkpoints and lose eligibility. |
| `AC-011` | `established-taste-skips-discovery` | scenario | `tests/test_decision_policy.py::test_established_direction_bypasses_gratuitous_discovery`, `::test_established_taste_routes_propagation_without_bypassing_checkpoints` | Established intent-governed direction skips discovery and select-direction checkpoints; propagation routes via established evidence without bypassing stricter preset checkpoints. |
| `AC-014` | `five-presets-distinct-behavior` | scenario | `tests/test_decision_policy.py::test_five_presets_share_controls_but_produce_distinct_checkpoint_contracts` | All five presets share identical controls yet produce distinct checkpoint contracts, and only agent-led grants delegated-authority propagation. |
| `AC-015` | `autonomy-selection-changes-controls-only` | scenario | `tests/test_decision_policy.py::test_five_presets_share_controls_but_produce_distinct_checkpoint_contracts`, `::test_runtime_autonomy_change_is_prospective_and_preserves_completed_decision` | Preset selection changes authority scope, intervention threshold, and checkpoint granularity while alignment_request.taste stays empty for every preset. |
| `AC-016` | `propagation-eligibility-gate` | scenario | `tests/test_alignment_contract.py::test_active_authority_checkpoint_blocks_material_propagation`, `tests/test_decision_policy.py::test_hypothesis_taste_does_not_claim_the_established_route` | Unresolved load-bearing dimensions and hypothesis-grade routes yield propagation_eligible False and blocked authorization until resolved. |
| `AC-017` | `load-bearing-classification` | scenario | `tests/test_decision_policy.py::test_aggregate_provisional_direction_is_load_bearing` | Shared/reused/default signals and aggregate direction classify a private cheap implementation load-bearing with recorded reasons and aggregate choice ids. |
| `AC-018` | `aggregate-materiality` | scenario | `tests/test_decision_policy.py::test_aggregate_provisional_direction_is_load_bearing`, `::test_aggregate_uncertainty_outranks_equal_weight_single_choice` | Interacting minor assumptions form a load-bearing aggregate with recorded choice ids, and aggregate uncertainties outrank equal-weight singles when targeting probes. |
| `AC-019` | `checkpoints-cannot-be-bypassed` | scenario | `tests/test_decision_policy.py::test_established_taste_routes_propagation_without_bypassing_checkpoints`, `tests/test_stakeholder_ownership.py::test_materially_ambiguous_ownership_checkpoints_before_propagation` | Eligible routing still reports checkpoint obligations and stays ineligible under high intervention; ownership holds block authorization until resolved. |
| `AC-020` | `delegated-authority-in-scope-propagation` | scenario | `tests/test_alignment_contract.py::test_delegated_judgment_resolves_execution_without_becoming_taste`, `tests/test_decision_policy.py::test_delegated_selection_stays_authorized_judgment_not_taste` | In-scope delegated authority propagates authorized judgment while reusable taste remains unresolved and never enters taste fields. |
| `AC-021` | `ambiguous-delegation-narrowest-scope` | scenario | `tests/test_decision_policy.py::test_ambiguous_delegation_expands_only_to_the_narrowest_supported_scope`, `::test_unambiguous_delegation_applies_without_extension_checkpoint` | Ambiguous delegation adopts only the narrowest option plus an extend-authority checkpoint with eligible False; unambiguous delegations apply without one. |
| `AC-022` | `cheap-choice-reevaluated-load-bearing` | scenario | `tests/test_integrated_scenarios.py::test_checkpoint_heavy_authority_with_delegation_and_aggregates`, `tests/test_reconciliation.py::test_correction_atomically_creates_pending_work_for_exact_dependents` | A bundle of individually cheap choices classifies load-bearing solely through aggregate-provisional-direction, and dependency-forming corrections enqueue exactly the affected dependents for reevaluation. |

## Ticket 08 mappings

| Criterion | Check | Kind | Target | Oracle |
| --- | --- | --- | --- | --- |
| `AC-012` | `direction-before-refinement` | scenario | `tests/test_decision_policy.py::test_unresolved_direction_compares_candidates_before_refinement`, `::test_first_plausible_candidate_does_not_silently_define_the_search_space` | Unresolved direction compares materially distinct candidates before refinement and defers to user selection under checkpoint presets; missing or single-candidate spaces force discovery instead of silently defining the space. |
| `AC-013` | `selection-through-evidence-model-only` | scenario | `tests/test_exploration.py::test_promotion_enters_the_normal_evidence_model_at_its_own_quality`, `::test_delegated_selection_records_delegation_without_taste_status` | Promoted selections enter the evidence model at their own strength/basis, and delegated selections record attribution without taste status. |
| `AC-023` | `promotion-provenance-or-reresolve` | scenario | `tests/test_decision_policy.py::test_non_reconstructable_provisional_basis_is_reresolved_not_fabricated`, `::test_aggregate_provisional_direction_is_load_bearing` | Provisional choices lacking reconstructable provenance are dropped and rediscovery required rather than fabricated; intact choices resolve as authorized judgment and aggregates record dependency ids. |
| `AC-038` | `probe-fidelity-matches-consequence` | scenario | `tests/test_decision_policy.py::test_probe_must_match_shape_and_fidelity_of_the_uncertainty`, `::test_probe_selection_targets_the_highest_value_uncertainty_cheaply`, `::test_uncovered_top_uncertainty_requests_a_resolution_checkpoint` | Probes must cover the uncertainty's full shape at minimum fidelity or fall back to clarification; selection picks the cheapest sufficient probe for the highest-value uncertainty. |

## Ticket 09 mappings

| Criterion | Check | Kind | Target | Oracle |
| --- | --- | --- | --- | --- |
| `AC-062` | `dependency-aware-reevaluation` | scenario | `tests/test_reconciliation.py::test_correction_atomically_creates_pending_work_for_exact_dependents`, `::test_dependents_reresolve_current_state_and_only_invalid_work_gets_repair` | Committing a correction atomically enqueues exactly dependents whose input dependencies include the corrected input; dependents reresolve against current state and only invalid ones need repair. |
| `AC-063` | `incomplete-until-repaired-and-verified` | scenario | `tests/test_reconciliation.py::test_resume_preserves_completed_pending_and_unverified_without_duplication`, `::test_propagation_blocks_stale_or_incomplete_affected_work_but_not_unrelated` | Interrupted reconciliation resumes with statuses preserved and no duplicated work; propagation blocks while affected work is stale or incomplete and permits unrelated dependents untouched. |
| `AC-064` | `correction-obligation-crash-safe` | scenario | `tests/test_reconciliation.py::test_reconciliation_state_round_trips_as_a_canonical_aggregate_value`, `::test_resume_preserves_completed_pending_and_unverified_without_duplication` | Canonical JSON round trips restore pending work, statuses, and attempt history identically, so committed corrections retain downstream obligations across restart. |
| `AC-065` | `superseded-pending-reresolves-current` | scenario | `tests/test_reconciliation.py::test_newer_correction_merges_work_and_remaining_repairs_use_current_basis` | Newer corrections merge into existing pending work and supersede basis revisions so remaining repairs target the current direction. |
| `AC-066` | `ordinary-authority-change-prospective` | scenario | `tests/test_reconciliation.py::test_ordinary_authority_change_is_prospective_and_does_not_reopen_work` | Authority-dimension corrections record prospectively without reopening completed work and replay idempotently. |
| `AC-067` | `whole-system-coherence-separate-check` | scenario | `tests/test_profile_composition.py::test_whole_system_check_catches_drift_that_local_approvals_miss` | Two individually approved decisions compose locally clean, yet the periodic whole-system sweep surfaces the relational conflict, unresolved dimension, blocked propagation, and a resolve-relation checkpoint. |
| `AC-068` | `regression-expectations-established-only` | scenario | `tests/test_reconciliation.py::test_approved_artifacts_challenge_taste_only_when_comparison_is_supported`, `tests/test_profile_composition.py::test_whole_system_check_catches_drift_that_local_approvals_miss` | Consistency expectations draw only from sufficiently established comparable direction: unsupported challenges conclude not-comparable, and sweeps flag drift against composed established taste. |
| `AC-069` | `challenges-require-comparability` | scenario | `tests/test_reconciliation.py::test_approved_artifacts_challenge_taste_only_when_comparison_is_supported`, `::test_materially_contradicting_artifact_reopens_alignment_as_stale_model`, `::test_contradiction_outcomes_distinguish_exceptions_from_context_change`, `::test_matching_or_incomparable_challenges_do_not_reopen_alignment`, `::test_challenge_replay_is_idempotent_and_conflicting_reuse_raises` | Challenges reopen alignment only when representation, approval semantics, context, scope, and ownership are comparable; contradictions queue dependent work, exceptions and context changes classify distinctly, matches conclude cleanly, and replay is idempotent. |

## Ticket 10 mappings

| Criterion | Check | Kind | Target | Oracle |
| --- | --- | --- | --- | --- |
| `AC-048` | `references-scoped-not-personal-taste` | scenario | `tests/test_reference_style.py::test_derived_intent_governs_without_becoming_user_taste`, `::test_multi_reference_composition_stays_intent_and_never_taste` | Derived reference directives govern alignment as intent with empty taste, keeping per-reference dependencies and instruction provenance. |
| `AC-049` | `explicit-properties-distinct-from-inferred` | scenario | `tests/test_reference_style.py::test_user_selected_reference_governs_only_the_requested_scope`, `::test_whole_style_request_includes_only_sufficiently_represented_properties` | Explicitly requested properties govern exactly those dimensions; inferred similarities require strong representation and unobserved dimensions are never manufactured. |
| `AC-050` | `reference-scope-follows-requested-work` | scenario | `tests/test_reference_style.py::test_derivation_retains_the_instruction_scope_on_directives`, `::test_classify_rejects_non_reference_requests` | Derivations carry the instruction's project scope onto every directive, and non-reference requests are rejected from reference derivation. |
| `AC-051` | `reference-provenance-narrow-rederivation` | scenario | `tests/test_reference_lifecycle.py::test_derivation_records_the_observed_source_state_per_property`, `::test_only_actual_dependents_are_flagged_for_reference_rework` | Each property records source identity, revision, provenance, and dependency keys so changes flag only actual dependents for narrow rework. |
| `AC-052` | `derived-profiles-supplement-source` | scenario | `tests/test_reference_style.py::test_whole_style_request_includes_only_sufficiently_represented_properties`, `::test_multi_reference_composition_stays_intent_and_never_taste` | Whole-style inclusion admits only sufficiently represented properties and composes multiple references without displacing their sources or becoming taste. |

## Ticket 11 mappings

| Criterion | Check | Kind | Target | Oracle |
| --- | --- | --- | --- | --- |
| `AC-053` | `live-vs-pinned-distinct` | scenario | `tests/test_reference_lifecycle.py::test_verify_pinned_state_rejects_live_references`, `::test_observe_live_state_rejects_pinned_references`, `::test_pinned_reference_stays_bound_when_the_locator_serves_new_content` | Mode-mismatched observation raises; pinned bindings ignore served content changes by turning freshness unknown and flagging derived claims stale. |
| `AC-054` | `source-identity-and-freshness-preserved` | scenario | `tests/test_reference_lifecycle.py::test_derivation_records_the_observed_source_state_per_property`, `::test_unverifiable_pinned_source_becomes_explicitly_unknown`, `::test_live_reference_without_revision_signal_requires_revalidation` | Material derivations bind identity and revision; unverifiable or revision-less sources become explicitly unknown and reject material reuse without revalidation. |
| `AC-055` | `changes-stale-only-affected-knowledge` | scenario | `tests/test_reference_lifecycle.py::test_live_change_marks_only_its_own_derived_claims_stale`, `::test_pinned_style_never_tracks_the_evolved_project_style`, `::test_project_consistency_origin_keeps_tracking_through_a_live_binding` | A live change stales exactly its own derived claims leaving unrelated references current; pinned heritage never adopts evolved style while project-consistency origins keep tracking live bindings. |

## Ticket 12 mappings

| Criterion | Check | Kind | Target | Oracle |
| --- | --- | --- | --- | --- |
| `AC-037` | `sandbox-leaves-profiles-unchanged` | scenario | `tests/test_exploration.py::test_deliberate_divergence_never_learns_and_rejection_stays_out_of_taste`, `::test_start_isolates_meaningfully_different_representative_alternatives` | Non-learning divergence forbids learning mode, emits no evidence transitions, and rejects never become taste; exploration state stays frozen. |
| `AC-056` | `exploration-no-contamination` | scenario | `tests/test_exploration.py::test_pick_reject_and_combine_change_only_the_production_selection`, `::test_cleanup_abandons_dead_ends_without_selection_or_taste_effects` | Pick, reject, combine, and cleanup mutate only exploration selection and usability; none emit evidence transitions or taste effects. |
| `AC-057` | `novelty-budgets-generation-only` | scenario | `tests/test_exploration.py::test_preserve_and_riff_uses_novelty_only_for_candidate_generation` | Novelty budgets steer riff candidate generation only; appending candidates produces no evidence or profile semantic effects. |
| `AC-077` | `temporary-state-cleaned-up` | scenario | `tests/test_exploration.py::test_cleanup_abandons_dead_ends_without_selection_or_taste_effects`, `tests/test_profile_persistence.py::test_interrupted_write_recovers_old_or_new_state_and_cleans_abandoned_temp` | Abandoned dead ends cannot be picked, delegated, combined, or riffed afterward; interrupted writes leave no abandoned temp files after recovery. |

## Ticket 13 mappings

| Criterion | Check | Kind | Target | Oracle |
| --- | --- | --- | --- | --- |
| `AC-058` | `edits-preserve-target-scope` | scenario | `tests/test_profile_control.py::test_correction_preserves_exactly_the_requested_scope` | Corrections emit instruction events carrying exactly the requested project, session, or global scope with user attribution. |
| `AC-059` | `direct-edits-cannot-manufacture-certainty` | scenario | `tests/test_profile_control.py::test_direct_edit_separates_editable_assertions_from_protected_state`, `::test_unsupported_edits_cannot_resurrect_or_suppress_evidence` | Direct edits produce user-attributed instruction events, reject protected-field edits such as confidence, and cannot resurrect or suppress evidence outside validated management. |
| `AC-060` | `actor-provenance-preserved` | scenario | `tests/test_profile_control.py::test_agent_and_unknown_edits_never_become_user_evidence` | Agent and unknown-authorship edits persist as inspectable history but never form preference knowledge or user evidence. |
| `AC-061` | `instruction-is-single-evidence` | scenario | `tests/test_profile_control.py::test_instruction_is_the_evidence_and_persistence_is_not_a_second_observation` | One correction yields exactly one instruction event and one established claim at single-observation confidence; persistence adds no second observation. |
| `AC-076` | `inspect-and-control-profiles` | scenario | `tests/test_profile_control.py::test_inspection_exposes_facets_without_flattening_conditionals`, `::test_inspection_reports_unresolved_and_excluded_knowledge`, `::test_management_requests_route_without_manual_representation_edits` | Inspection exposes facets, relationships, provenance, excluded, and unresolved knowledge verbatim; RESET/VERSION/UNDO route through validated management without manual representation edits. |

## Ticket 14 mappings

| Criterion | Check | Kind | Target | Oracle |
| --- | --- | --- | --- | --- |
| `AC-031` | `lifecycle-ops-preserve-invariants` | scenario | `tests/test_profile_lifecycle.py::test_targeted_reset_excludes_only_typography_and_keeps_history`, `::test_retraction_recomputes_claims_while_preserving_provenance`, `::test_undo_restores_profile_and_applicability_without_touching_artifacts`, `::test_operations_replay_identically_and_identity_reuse_raises`, `::test_consolidation_merges_near_duplicates_and_keeps_distinctions`, `::test_migrate_document_maps_missing_epistemic_fields_to_unknown` | Reset, retract, undo, consolidation, migration, and replay preserve epistemic and provenance invariants: history persists, provenance is retained, undo restores exactly, duplicates consolidate conservatively, legacy fields default unknown, and identity reuse conflicts. |
| `AC-032` | `targeted-lifecycle-narrowness` | scenario | `tests/test_profile_lifecycle.py::test_unrelated_valid_evidence_survives_a_targeted_reset`, `::test_reingesting_the_same_event_cannot_resurrect_excluded_support`, `::test_relearning_after_reset_derives_only_from_genuinely_new_evidence` | Exclusions remove only supported links while retaining audit history and unrelated implications; reingestion cannot resurrect excluded support and relearning cites genuinely new evidence. |
| `AC-033` | `branches-explicit-activation` | scenario | `tests/test_profile_lifecycle.py::test_created_branch_stays_inapplicable_until_explicitly_selected`, `::test_selecting_a_branch_makes_exactly_that_alternative_applicable`, `::test_branch_references_are_validated_against_the_registry` | Created branches stay inert until SelectBranch; selection activates exactly that branch deterministically; registry validates branch scopes, parents, and provenance. |
| `AC-034` | `branch-scoped-evidence-isolation` | scenario | `tests/test_profile_lifecycle.py::test_branch_specific_evidence_is_isolated_from_parent_and_siblings`, `::test_broader_evidence_keeps_scope_and_records_origin_branch` | Branch-originated claims stay invisible to parent and sibling views while broader evidence keeps applying across switches and records its origin branch. |
| `AC-035` | `external-edits-cannot-manufacture-certainty` | scenario | `tests/test_profile_lifecycle.py::test_import_downgrades_tampered_confidence_and_provenance`, `::test_import_rejects_structurally_tampered_documents`, `tests/test_profile_control.py::test_agent_and_unknown_edits_never_become_user_evidence` | Imported inflated confidence recomputes from evidence, fabricated provenance drops with explained downgrades, structurally tampered documents are rejected, and agent-authored edits stay non-evidence. |

## Ticket 15 mappings

| Criterion | Check | Kind | Target | Oracle |
| --- | --- | --- | --- | --- |
| `AC-071` | `stakeholder-separate-from-user-taste` | scenario | `tests/test_stakeholder_ownership.py::test_stakeholder_profiles_never_merge_into_user_taste`, `tests/test_profile_lifecycle.py::test_consolidation_refuses_different_represented_subjects` | Stakeholder-owned properties stay excluded from the user profile by represented-subject mismatch, and consolidation refuses merging different represented subjects. |
| `AC-072` | `ownership-resolves-conflicts` | scenario | `tests/test_stakeholder_ownership.py::test_explicit_ownership_resolves_competing_directions`, `::test_resolution_follows_agreements_not_a_universal_precedence`, `::test_signal_without_ownership_cannot_override_the_applicable_owner`, `::test_hard_constraints_bound_the_space_before_ownership_resolves`, `::test_materially_ambiguous_ownership_checkpoints_before_propagation` | Granted owners' directives govern under OWNERSHIP, identical roles resolve by agreements rather than precedence, ungranted signals cannot override, hard constraints bound first, and ambiguous grants checkpoint before load-bearing work. |
| `AC-073` | `stakeholder-profiles-do-not-mutate-taste` | scenario | `tests/test_stakeholder_ownership.py::test_approval_of_stakeholder_work_is_not_personal_taste_evidence`, `::test_ownership_correction_reconciles_only_actual_dependents` | Approving stakeholder-owned artifacts cannot challenge user taste (not comparable), and grant corrections reconcile only decisions actually depending on the revoked input. |

## Ticket 16 mappings

| Criterion | Check | Kind | Target | Oracle |
| --- | --- | --- | --- | --- |
| `AC-075` | `adapters-share-one-core` | scenario | `tests/test_domain_adapters.py::test_three_domains_run_one_call_pattern_with_distinct_vocabularies`, `::test_adapter_local_metadata_and_input_order_cannot_change_core_outcomes`, `::test_adapter_propagation_authority_is_exactly_the_canonical_guard`, `::test_constraints_outrank_intent_and_intent_outranks_craft`, `::test_medium_probes_are_selected_by_the_shared_contract`, `::test_motion_walkthrough_existence_purpose_build_feelcheck_review_none` | UI, writing, and motion run one call pattern preserving medium-specific vocabularies; local metadata and ordering cannot move core outcomes; adapter authorization mirrors the canonical guard exactly, governing precedence and shared-contract probes hold, and the six-stage walkthrough ends in a clean no-animation outcome. |

## Ticket 17 integrated mappings

| Criterion | Check | Kind | Target | Oracle |
| --- | --- | --- | --- | --- |
| `AC-078` | `traceability-completeness-executable` | scenario | `tests/test_acceptance_traceability.py` | Parsing this document yields exactly the canonical catalog with no missing or unknown criteria, and every cited `tests/…` target resolves to a real file and test function. |
| `AC-079` | `integrated-scenarios-pass` | scenario | `tests/test_integrated_scenarios.py` | Cross-feature scenarios pass covering reference freshness repair, stakeholder revocation reconciliation, contradiction plus targeted reset, checkpoint-heavy authority with ambiguous delegation and aggregates, branch isolation across export/import/undo, and adapters routing reference intent and craft through one core. |
| `AC-079` | `scenario-substrate-cross-feature` | scenario | `tests/test_scenario_harness.py` | User paths expose state, retry, interruption, restart, and cross-feature behavior through the public seam. |

## Review follow-up mappings

Hardening from the import-semantics review (issue 19); these strengthen
already-mapped criteria rather than introduce new ones.

| Criterion | Check | Kind | Target | Oracle |
| --- | --- | --- | --- | --- |
| `AC-029` | `import-merge-preserves-local-state` | scenario | `tests/test_profile_lifecycle.py::test_stale_exchange_import_into_moved_on_state_preserves_local_claims`, `::test_import_rejects_divergent_event_id_collision_instead_of_merging` | Importing into a moved-on state union-merges ledgers without reinterpreting local knowledge: locally excluded supports keep suppressing imported properties that cite them, and an event id reused with divergent content raises instead of building a hybrid state. |
| `AC-031` | `import-marker-collision-keeps-identity` | scenario | `tests/test_profile_lifecycle.py::test_import_marker_id_collision_keeps_local_and_surfaces_on_replay` | A cross-device applied-operation id collision keeps the retained local marker, and a later replay against it raises the identity conflict instead of silently re-applying. |

With these sections every canonical criterion `AC-001` through `AC-079` has at least one passing mapped check.
