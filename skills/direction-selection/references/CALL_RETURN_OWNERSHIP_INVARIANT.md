# Call/Return Ownership Invariant

Comparison owns the direction decision lifecycle.

Discovery is a bounded call/return subroutine that temporarily serves the owning comparison stage (or the standalone applicability router when explicitly allowed). Discovery gathers only the evidence needed for its defined uncertainty and then returns control to the recorded owner.

For the applicability router exception, "explicitly allowed" means the applicability routing logic invokes discovery only to resolve applicability-specific uncertainty. This does not transfer decision ownership to discovery.

The applicability router remains responsible for determining whether the skill applies. Discovery may gather bounded evidence required for that determination, then must return the evidence and control flow to the applicability router.

Discovery must not become a parallel decision owner, general research router, project-state controller, planning system, persistence layer, or verification authority.

The ownership rule is:

`owner identifies uncertainty -> discovery performs bounded work -> owner resumes decision lifecycle`

Any implementation change that causes discovery to retain ownership after its bounded task completes violates this invariant.
