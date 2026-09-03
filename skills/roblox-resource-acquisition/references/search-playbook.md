# DevForum Resource Search Playbook

Use this when broad discovery is required after checking built-ins/project dependencies and the external user/project curated registry described in [curated-registry.md](curated-registry.md). The objective is a small set of credible candidates, not exhaustive browsing. Curated resources are already trusted by policy; broad discovery is for needs the curated registry does not adequately cover, material contradiction checks, or explicit alternative/comparison requests.

## 1. Translate the need into search terms

Start with the capability, then expand only with terms Roblox authors commonly use for the same kind of resource.

Examples:

- networking -> networking, RemoteEvent, replication, packet, serialization;
- pathfinding -> pathfinding, NPC movement, navigation;
- projectiles -> projectile, raycast, FastCast, ballistics;
- state/data replication -> replication, state, replica, synchronized table;
- persistence -> datastore, player data, profile, persistence;
- UI -> UI framework, component, interface, GUI;
- signals/events -> signal, event, RBXScriptSignal alternative;
- cleanup -> cleanup, maid, janitor, trove;
- hit detection -> hitbox, raycast hitbox, spatial query.

Do not let synonyms silently broaden the requirement. They are discovery terms only.

## 2. Search Community Resources directly

Prefer results from:

- [Roblox DevForum Resources](https://devforum.roblox.com/c/resources/71)
- Community Resources topics beneath that category;
- relevant DevForum tag pages;
- domain-restricted web search targeting `devforum.roblox.com` when forum search is insufficient.

Useful query shapes:

- `site:devforum.roblox.com <capability> "Community Resources" Roblox`
- `site:devforum.roblox.com/t <capability> module Roblox`
- `<capability> site:devforum.roblox.com/c/resources`

Search both current/recent results and established resources when maturity matters. Recency alone is not quality; age alone is not obsolescence.

## 3. Open the actual thread

For every serious candidate, inspect the thread rather than relying on a search card.

Extract:

- the original post's actual claims;
- edit/update markers;
- install/source/docs links;
- resource status such as old, deprecated, rewrite, successor, beta, paid, or abandoned;
- maintainer replies that materially change setup or limitations;
- recent reports of breakage or incompatibility.

Do not read every reply. Search within long threads for terms such as:

`deprecated`, `obsolete`, `old`, `rewrite`, `successor`, `bug`, `broken`, `security`, `exploit`, `license`, `github`, `docs`, `release`, `version`, `update`.

Read surrounding context before treating a hit as evidence.

## 4. Follow canonical links

If the thread points to GitHub, Wally, Pesde, documentation, a package/model, or another canonical release source, inspect that source before selection.

Prefer canonical source for:

- current version/release;
- installation;
- API names and signatures;
- dependencies;
- source behavior;
- tests;
- license;
- open issues and release notes.

The DevForum thread remains useful for provenance, developer discussion, migration warnings, and real-world failure reports.

## 5. Search for alternatives deliberately

After finding one plausible resource, run at least one alternative-oriented query unless the need is truly unique.

Use:

- same capability + `library` / `module` / `framework`;
- candidate name + `alternative` or `vs`;
- relevant DevForum tag page;
- the same capability sorted mentally across recent and established resources.

Stop once you have enough evidence to show that additional candidates are unlikely to change the decision. Usually 2-5 serious candidates is sufficient.

## 6. Search against the candidate

Before establishing verified-acquisition trust for a newly discovered resource, perform a short adversarial search around the selected resource:

- `<resource> deprecated`
- `<resource> broken`
- `<resource> security`
- `<resource> exploit`
- `<resource> bug`
- `<resource> successor`
- `<resource> Roblox update`

Only findings relevant to the required behavior matter. Do not reject a library because unrelated users have unrelated problems.

## 7. Evidence discipline

For each material selection claim, be able to point to one of:

- executed proof;
- source code;
- canonical docs/release notes/issues;
- DevForum maintainer statement/discussion;
- current Roblox Creator Hub platform documentation.

If the search yields only marketing claims and no evaluable implementation, downgrade or reject the candidate rather than filling gaps with assumptions.
