# Fence Quote Agent 🪚

An AI-assisted tool that helps a handyperson quickly generate accurate, consistent fence-building quotes.

Given a small set of inputs (number of 6-foot sections, labor hours, hourly rate, and materials markup), the agent:

1. Computes a bill of materials (posts, rails, pickets, concrete, fasteners).
2. Compares prices between Home Depot and Lowe’s.
3. Picks the cheaper store.
4. Combines materials + labor into a structured quote.
5. Uses an LLM to generate a customer-friendly quote you can send as-is.

This repo is part of a capstone assignment for the **UW Specialization in AI Product Management**.

---

## ✨ Features

- **Bill of Materials (BOM) Calculation**
  - Posts, rails, pickets, concrete bags, and fasteners estimated from number of 6' sections.
  - Config-driven quantities (easy to adjust as the contractor refines their approach).

- **Price Comparison**
  - Per-material prices for Home Depot and Lowe’s.
  - Automatically chooses the cheaper store for the whole job.

- **Structured Quote Calculation**
  - Materials base cost + markup.
  - Labor cost (hours × hourly rate).
  - Grand total (tax currently set to 0, but easy to parameterize).

- **Customer-Ready Quote (via LLM)**
  - Friendly greeting.
  - Simple explanation of scope (e.g., “6 sections of 6-foot fence”).
  - Clear breakdown of materials and labor.
  - Total cost, scheduling note, and quote validity period.

---

## 🧱 Project Structure

```text
fence_agent/
├─ fence_agent.py      # Main script: BOM, pricing, quote logic, and LLM call
├─ requirements.txt    # Python dependencies
├─ .gitignore          # Ignore venv, __pycache__, etc.
└─ venv/               # Local virtual environment (not committed)
