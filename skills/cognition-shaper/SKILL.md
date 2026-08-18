---
name: cognition-shaper
description: Use when the user explicitly asks for Cognition Shaper, 认知塑形, 认知框架共建, or a multi-turn living cognitive model that grows beside the conversation. Do not use for ordinary explanations, one-shot analysis, translation, or publishing.
---

# Cognition Shaper

## Core contract

Maintain two coordinated surfaces:

1. **Chat** — short, concrete, Socratic prompts that move the user's thinking.
2. **Living Surface** — one continuously updated cognitive model that the user can keep open beside the chat.

The Living Surface is not a transcript or a summary. It is the single structured model. Expand nodes in place as resolution increases, without losing confirmed details.

Do not turn an ordinary question into this workflow. Use it only when the user explicitly invokes Cognition Shaper/认知塑形 or clearly requests multi-turn co-construction of a living cognitive framework.

## Lock the Living Surface first

Choose exactly one runtime adapter before substantive modeling.

### Chat AI with a native side document

- Create one native side document (for example, a Canvas or Artifact) and keep updating that same document.
- Use the side document as the sole model; keep chat short.
- If no side-document feature exists, say so plainly and ask whether to use the full-document-in-chat fallback. Do not pretend that hidden state is a visible Living Surface.

### Local Agent

- Use one Markdown file at the path supplied by the user.
- If the user has not supplied a path, do not write any file yet. Do not infer a path from the current directory, repository, home directory, or OS conventions. Do not create a dedicated directory.
- While waiting for a path, begin with one concrete probe and ask for the destination path in the same short response.
- After the user supplies a path, create or open that exact file and keep updating it. A path inside a repository is allowed only when the user chose it.

### Cloud Agent

- The source of truth is one Markdown file in the runtime-provided temporary or scratch directory. Do not create a permanent dedicated directory.
- The visible Living Surface uses a remote publishing adapter. The bundled and verified default is one **secret GitHub Gist** synchronized from the source file.
- Any replacement adapter must create once, update the same remote document, verify exact content, return a stable visible URL, and state who refreshes the view.
- A secret Gist is unlisted, not access-controlled private storage. State this once before publishing sensitive material; if the topic is sensitive, obtain confirmation first.
- On the first turn, create the temporary source file, publish it once, give the URL to the user, and ask them to keep it open.
- After every substantive model change, write the source file first, then update the same remote document and verify its content. Never create a new remote document per turn.
- With the bundled Gist adapter, tell the user to refresh the Gist tab after a sync. Never imply that the Agent can refresh the user's browser.
- Do not use a worktree, repository file, PR, or Review as the Living Surface.

Use the bundled `scripts/gist_sync.py`, resolved relative to this `SKILL.md`, with the runtime's Python 3.10+ interpreter. It uses only the Python standard library. Never pass a token value on the command line.

- First sync: invoke the script with the temporary source-file path and omit `--gist-id`.
- Save the returned `gist_id`.
- Later syncs: invoke the same script and source path with `--gist-id` set to that saved ID.
- Token discovery order: `COGNITION_SHAPER_GITHUB_TOKEN`, `GH_TOKEN`, then `GITHUB_TOKEN`.
- The script also reads an explicitly supplied `--env-file`, the path in `COGNITION_SHAPER_ENV_FILE`, or a `.env` discovered from the current/script directory ancestry.
- If exactly one custom `GITHUB_*_TOKEN` exists, the script uses it for backward compatibility. If several exist, select one by variable name with `--token-env`.

The GitHub token needs permission to create and edit Gists. If publishing fails, keep the temporary Markdown as the source of truth, paste the current full document into chat, and label this as a presentation-layer fallback. Never fail silently.

## Initialize without a macro dump

Start from one microscopic scene, friction, decision, or visible phenomenon. Ask at most one causal question at a time.

Use the first few turns to discover:

- who will use the model;
- the concrete goal or decision;
- the real application scene;
- physical, social, time, and resource constraints.

Do not ask these as a questionnaire. Infer them through short probes. Do not fill the Living Surface with confident conclusions before the context boundary is known.

Initialize this topology:

```markdown
# <topic>

## 【Meta】前提与约束边界

## 【Layer 0】终极物理／地缘／人类底座

## 【Layer 1...N】垂直演化与跨域网络

## 【Action】传导方法论与待验证假设
```

Add layers only when the causal structure requires them. Keep concrete cases in the node where they provide evidence; do not move them into a chat-history appendix.

## Cognitive method

Apply all six principles:

1. **User context first** — knowledge serves a specific user, goal, scene, and constraint.
2. **First-principles bedrock** — zoom out beyond the topic's internal vocabulary to physical, geographic, biological, psychological, or institutional variables.
3. **Networked causality** — preserve a clear backbone while marking variables that act across layers.
4. **Bottom-up hook** — reason top-down internally, but enter the conversation through a concrete micro-phenomenon.
5. **Falsification loop** — record testable hypotheses, transmission mechanisms, counterexamples, and observable signals.
6. **Lossless resolution upgrade** — replace a brief node with a richer version in place. Expansion may make the document longer; it may not erase prior information.

## Update loop

For each user turn:

1. Detect whether it adds a constraint, causal relation, example, counterexample, hypothesis, decision, or falsification signal.
2. If it does, update the Living Surface **before** replying in chat. The user does not need to request an update.
3. Rewrite the affected node in place; do not append a chronological change log.
4. Persist and, in cloud mode, synchronize and verify the presentation layer.
5. Reply in one to four short sentences:
   - enter through one concrete detail;
   - ask at most one causal question;
   - naturally mention the exact module updated.

If the turn contains no substantive model change, continue the micro-dialogue without manufacturing a document update.

## Lossless edit invariant

Before rewriting an existing node, account for:

- every confirmed detail;
- every concrete case;
- every cross-layer causal edge;
- every open question;
- every pending hypothesis and its status.

After rewriting, each item must remain independently identifiable unless the user explicitly asked to delete, merge, or compress it. Grouping is allowed; information loss is not. Preserve uncertainty labels rather than silently promoting a hypothesis to a conclusion.

If restructuring multiple nodes, map every old item to a new location before replacing the old structure. When context is tight, narrow the edit scope instead of summarizing away evidence.

## Example

Existing node:

```markdown
### 指标异化
绩效指标会改变行为。
```

After the user describes knowingly cooperating with a broken metric, expand the same node:

```markdown
### 指标异化
- 已确认现象：工作者同时承担完成任务与压制质疑的双重消耗。
- 机制：代理指标从测量工具变成资源分配目标，行为开始服务数字而非原目标。
- 用户案例：明知指标失真，仍必须配合表演其有效性。
- 跨层边：资源分配制度 → 团队叙事 → 个体认知失调。
- 待验证假设：疲惫更多来自无效动作，还是被迫表达认同？
```

Chat:

> 最磨人的可能不是多做几步，而是还得把怀疑藏起来。我已把“双重消耗”展开进【Layer 2：指标异化】；你更累的是无效动作，还是被迫假装认同？

## Common failures

- Dumping a comprehensive framework into the first chat response.
- Waiting for the user to say “update the document.”
- Writing the Living Surface as a conversation log.
- Using a local repository or default directory without a user-supplied path.
- Using a cloud worktree or invisible sandbox file as if the user could watch it.
- Creating a new Gist on every turn.
- Claiming a sync succeeded without verification.
- Saying the Agent refreshed the user's browser.
- Compressing old examples, edges, or hypotheses to save tokens.
- Posting the full Living Surface in chat when the visible side document is working.
