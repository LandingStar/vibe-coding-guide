# Conversation Progression Contract

## Purpose

Use this reference when the workflow reaches a point where the user must confirm, choose, approve, or steer the next step.

The goal is to keep the conversation moving without collapsing into a terminal summary or a passive "please choose" handoff.

## Core Contract

- Do not end the conversation unless the user explicitly allows ending or pausing.
- Default reply shape: analysis or recommendation first, then a forward question.
- The closing question must contain the AI's own judgment, recommendation, or tentative direction.
- If the user must make a structured decision, use `askQuestions` after presenting the recommendation.

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