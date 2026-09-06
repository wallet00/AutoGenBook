TASK
Revise the section Markdown body so that it satisfies the reviewer feedback and reads like a finished academic monograph section.

INPUTS
- Section title: {section_title}
- Node key: {node_key}

- Original markdown_body:
{section_latex}

- Reviewer feedback JSON:
{review_json}

- Previous sections excerpt:
{previous_sections}

- Outline context:
{toc_and_summary}

- Context memory excerpt:
{context_memory_excerpt}

RETRIEVED EXCERPTS:
{retrieved_context}

REVISION GOALS
- Resolve every major reviewer issue.
- Improve continuity, paragraph structure, and scholarly tone.
- Replace outline-like fragments with continuous prose.
- Remove raw scaffold labels, meta comments, and the literal phrase "general background knowledge".
- Keep the section aligned with the outline and surrounding sections.
- Preserve supported technical claims and existing valid citations; add citations only when supported by the retrieved excerpts.

STRICT RULES
- Do not invent facts or citations.
- Do not add claims that are not supported by the evidence pack.
- If evidence for a claim is insufficient, remove it or rewrite it cautiously.
- Prefer compact, well-structured paragraphs over bullet-heavy formatting.
- Do not hard-wrap prose line by line.

OUTPUT
Return only the revised Markdown body, with no code fences.


COMPULSORY STYLE & EXAMPLES
- Write in a fluent, academic-expository style with natural sentence architecture: use compound sentences, connectives and logical transitions that bind sentences and paragraphs into a continuous argument.
- Each paragraph MUST develop a complete thought across several sentences. A paragraph must never consist of a single short sentence.
- STRICTLY FORBIDDEN: choppy single-sentence paragraphs, short fragmented sentences, terse bullet-like one-liners written as prose, and note/list-style writing.
- Every theoretical idea or concept MUST be illustrated IMMEDIATELY in the same paragraph with a concrete, worked example drawn from digital services, B2B/B2C SaaS, IT platforms, or software applications. If a genuinely adequate example is not available, still provide the closest realistic IT/SaaS/digital-services illustration; never leave a theory without an application example.
- Keep the text flowing: end paragraphs so they connect to the next one, and avoid abrupt topic jumps.

