# Conversation Progression Contract

## Purpose

Use this reference when the workflow reaches a point where the user must confirm, choose, approve, or steer the next step.

The goal is to keep the conversation moving without collapsing into a terminal summary or a passive "please choose" handoff.

## Core Contract

- Do not end the conversation unless the user explicitly allows ending or pausing.
- Default reply shape: analysis or recommendation first, then a forward question.
- The closing question must contain the AI's own judgment, recommendation, or tentative direction.
- Before asking the closing question, provide links to the most relevant documents so the user can jump directly to the review surface.
- If the user must make a structured decision, use `askQuestions` after presenting the recommendation.

## Positive Template

Every reply must end with this structure (sole exception: exemption conditions below):

```
[AI's analysis / judgment / inclination] → [forward question based on that analysis, using askQuestions tool]
```

## Pre-Send Checklist

Before composing the final paragraph, verify:

1. ✅ Does the reply ending contain the AI's own analysis or inclination?
2. ✅ Does it end with a forward question via `askQuestions`? (At minimum, a textual forward question.)
3. ✅ Does the question advance the work (clear next step after user answers), rather than waiting for permission?
4. ✅ If direction choices are involved, does each option reference a concrete document?
5. ✅ Did you provide links to the most relevant documents before the question?

If any item is ❌, reorganize the final paragraph before sending.

## When To Use Structured Questions

Prefer `askQuestions` when the user needs to:

- choose between concrete next slices
- approve or reject a design direction
- confirm a phase transition or write-back follow-up
- select among bounded implementation options

## Anti-Patterns

Avoid these patterns:

- ending with a plain summary and no next-step question
- asking "Which direction do you want?" without first stating a recommendation
- treating review or approval checkpoints as a reason to stop talking
- pushing the full decision burden back to the user without analysis

## Allowed Exceptions

It is acceptable not to end with a forward question only when the user explicitly:

- allows the conversation to end
- asks to pause
- asks not to continue with follow-up questions in the current turn