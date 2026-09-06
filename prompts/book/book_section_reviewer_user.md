TASK
Review the new section and propose required fixes.

INPUTS
- Section:
title: {section_title}
node_key: {node_key}
latex_body: {section_latex}

- Context memory excerpt:
{context_memory_excerpt}

- Previous sections excerpt:
{previous_sections}

- Outline context:
{toc_and_summary}

RETRIEVED EXCERPTS:
{retrieved_context}

OUTPUT CONTRACT (JSON ONLY)
{
  "ok_to_keep": true|false,
  "issues": [
    {
      "type": "grounding|consistency|latex|clarity|pedagogy",
      "severity": "major|minor",
      "description": "...",
      "required_fix": "..."
    }
  ],
  "suggested_edits": [
    {
      "target": "paragraph hint",
      "edit_instruction": "..."
    }
  ],
  "retrieval_queries": ["...if you need more evidence to fix grounding"]
}

RULES
- If there are unsupported claims, set ok_to_keep=false unless they can be trivially qualified/removed.


COMPULSORY STYLE & EXAMPLES
- Write in a fluent, academic-expository style with natural sentence architecture: use compound sentences, connectives and logical transitions that bind sentences and paragraphs into a continuous argument.
- Each paragraph MUST develop a complete thought across several sentences. A paragraph must never consist of a single short sentence.
- STRICTLY FORBIDDEN: choppy single-sentence paragraphs, short fragmented sentences, terse bullet-like one-liners written as prose, and note/list-style writing.
- Every theoretical idea or concept MUST be illustrated IMMEDIATELY in the same paragraph with a concrete, worked example drawn from digital services, B2B/B2C SaaS, IT platforms, or software applications. If a genuinely adequate example is not available, still provide the closest realistic IT/SaaS/digital-services illustration; never leave a theory without an application example.
- Keep the text flowing: end paragraphs so they connect to the next one, and avoid abrupt topic jumps.

