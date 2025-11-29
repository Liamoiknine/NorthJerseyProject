## Dataset Breakdown

| Category                      | Count |
| ----------------------------- | ----- |
| **soprano_dpo_pairs dataset** | 500   |
| **Multi-turn dialog**         | 210   |
| **Emotional variation**       | 210   |
| **Everyday topics**           | 300   |
| **Guardrails**                | 90    |
| **Environmental grounding**   | 75    |

## Category Descriptions

- **soprano_dpo_pairs dataset**: Teaches the model to answer logical, conceptual, and factual questions in Tony's voice so it can handle structured prompts reliably.

- **Multi-turn dialog**: Trains the model to sustain conversation across multiple exchanges, maintaining context and persona without resetting each turn.

- **Emotional variation**: Gives the model the ability to shift tone—angry, tired, reflective, amused—so responses feel alive rather than flat or repetitive.

- **Everyday topics**: Builds natural conversational range (food, sports, advice, small talk) so Tony feels like a real person instead of a narrow Q&A filter.

- **Guardrails**: Ensures the model refuses unsafe or inappropriate requests in-character without breaking persona or reverting to generic assistant tone.

- **Environmental grounding**: Teaches the model how to handle contradictions, follow-ups, corrections, and shifts in context so replies stay coherent and adaptive.

## Data Sources

- **Base dataset**: `rsilveira79/soprano_dpo_pairs` (HuggingFace)
- **Synthetic data**: Generated using prompts documented in `prompts.md`

