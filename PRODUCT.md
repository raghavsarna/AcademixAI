# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Next.js (App Router) + TypeScript + Tailwind CSS in `web/`, consuming the FastAPI JSON API in `app/` (accepted by the user as part of the revamp plan; deploy target planned as Vercel for the frontend, a Python host for the API).

## Users

Three audiences reading the same material:

- **Students and new researchers** who need dense AI papers explained and want to keep up with the field.
- **AI practitioners** (engineers, researchers) who skim new arXiv work and want fast, trustworthy summaries of what is new.
- **Curious non-experts** who follow AI but cannot read papers.

## Product Purpose

AcademixAI tells you what changed in AI research today, and explains every paper at your level. Each day it reads new arXiv papers in AI, ML, NLP and computer vision, picks the ones that moved the field, and says what each one changes. Every paper, whether from the daily feed or uploaded by the reader as a PDF, can be read at three depths (Plain, Student, Expert) and questioned in a chat. Success: a reader opens it daily, understands what moved in a few minutes, and goes deeper on the papers that matter to them at the depth they can follow.

## Positioning

Two mechanisms together, which a general chatbot or a newsletter cannot copy:

1. **What changed in AI today**: a daily changelog of the field, not a newsletter of summaries. Each entry states what the paper claims is new and what earlier work it builds on or challenges.
2. **Every paper, at your level**: one switch re-explains the same paper as Plain, Student or Expert, so one product serves all three audiences.

## Operating Context

- Daily rhythm: a new edition per day generated from arXiv (categories cs.AI, cs.LG, cs.CL, cs.CV).
- Readers also upload their own paper PDFs; uploads are private to the uploader, the analysis is shareable by link.
- Chat about a paper or an edition requires an account.

## Capabilities and Constraints

- Existing: arXiv fetch, PDF text extraction, model analysis (Gemini 3.1 Flash-Lite, Gemma fallback), chat, accounts with JWT, rate limits.
- Being built in this phase: per-paper "what changed" and "builds on" fields, three explanation depths, daily editions made of individual paper entries.
- Free-tier model budget: generation must stay within roughly a few hundred model requests per day.
- Analysis reads abstracts for the daily feed and full text for uploads; "builds on" is limited to what the paper itself states.
- Undecided: email delivery of editions, topic following/personalisation, cross-paper library memory (later phases).

## Brand Commitments

- Name: **AcademixAI** (kept).
- The previous logo, purple palette and space theme are not binding; the identity is open for redesign.

## Evidence on Hand

- Real content: generated digests and paper analyses in `data/seed.json`; real arXiv papers fetched daily.
- No users, testimonials, usage numbers, press or partnerships exist. Never invent them, and never invent paper results, benchmarks or citations.

## Product Principles

1. **Change over coverage.** Lead with what moved, not a list of everything published.
2. **One paper, three readers.** Depth is a switch on the same page, never a different product.
3. **Traceable to the source.** Every claim links back to the paper; nothing is stated that the paper does not support.
4. **Respect reading time.** Scannable first, depth on demand.
