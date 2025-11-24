import os
from openai import OpenAI

client = OpenAI()

# ----- CONFIG: materials + prices (per unit) -----
# Replace the price numbers with real Home Depot / Lowe's prices if you want.
MATERIALS = {
    "posts_4x4x8": {
        "label": "4x4x8 pressure-treated posts",
        "qty_per_section": 1.0,      # e.g., 1 post per 6' section (simplified)
        "qty_per_project_extra": 1.0, # one extra post for the ends
        "home_depot_price": 9.25,
        "lowes_price": 9.10,
    },
    "rails_2x4": {
        "label": "2x4 rails (8ft)",
        "qty_per_section": 2.0,       # top + bottom rail
        "qty_per_project_extra": 0.0,
        "home_depot_price": 4.50,
        "lowes_price": 4.30,
    },
    "pickets": {
        "label": "1x6 fence boards",
        "qty_per_section": 10.0,      # e.g. 10 pickets per 6' section
        "qty_per_project_extra": 0.0,
        "home_depot_price": 3.80,
        "lowes_price": 3.70,
    },
    "concrete_bags": {
        "label": "80lb concrete mix",
        "qty_per_section": 0.5,       # half a bag per post
        "qty_per_project_extra": 1.0, # one extra bag buffer
        "home_depot_price": 5.25,
        "lowes_price": 5.15,
    },
    "nails_screws": {
        "label": "Exterior nails / screws (box)",
        "qty_per_section": 0.05,      # small fraction of a box per section
        "qty_per_project_extra": 1.0, # 1 full box for the job
        "home_depot_price": 65.00,
        "lowes_price": 60.00,
    },
}


def compute_bom(num_sections: int) -> dict:
    """
    Compute bill of materials based on number of 6' sections.
    Returns a dict keyed by material key with quantities.
    """
    bom = {}
    for key, cfg in MATERIALS.items():
        qty = (
            cfg["qty_per_section"] * num_sections
            + cfg.get("qty_per_project_extra", 0)
        )
        bom[key] = {
            "label": cfg["label"],
            "quantity": round(qty, 2),
        }
    return bom


def price_bom(bom: dict) -> dict:
    """
    Compare Home Depot vs Lowe's for the given BOM.
    Returns totals and per-item breakdown.
    """
    hd_total = 0.0
    lowes_total = 0.0
    line_items = []

    for key, item in bom.items():
        cfg = MATERIALS[key]
        qty = item["quantity"]

        hd_cost = qty * cfg["home_depot_price"]
        lowes_cost = qty * cfg["lowes_price"]

        hd_total += hd_cost
        lowes_total += lowes_cost

        line_items.append({
            "material_key": key,
            "label": cfg["label"],
            "quantity": qty,
            "home_depot_unit_price": cfg["home_depot_price"],
            "lowes_unit_price": cfg["lowes_price"],
            "home_depot_total": hd_cost,
            "lowes_total": lowes_cost,
        })

    if hd_total <= lowes_total:
        chosen_store = "Home Depot"
        chosen_total = hd_total
    else:
        chosen_store = "Lowe's"
        chosen_total = lowes_total

    return {
        "line_items": line_items,
        "home_depot_total": hd_total,
        "lowes_total": lowes_total,
        "chosen_store": chosen_store,
        "chosen_materials_total": chosen_total,
    }


def compute_quote(num_sections: int,
                  labor_hours: float,
                  labor_rate: float,
                  materials_markup_pct: float = 15.0):
    """
    End-to-end: compute BOM, price it, and build a structured quote object.
    """
    bom = compute_bom(num_sections)
    pricing = price_bom(bom)

    labor_cost = labor_hours * labor_rate
    materials_base = pricing["chosen_materials_total"]
    materials_markup = materials_base * (materials_markup_pct / 100.0)
    materials_total_with_markup = materials_base + materials_markup

    subtotal = materials_total_with_markup + labor_cost
    # You could add tax, travel fee, etc. later.
    tax_rate = 0.0
    tax_amount = subtotal * tax_rate
    grand_total = subtotal + tax_amount

    quote = {
        "num_sections": num_sections,
        "chosen_store": pricing["chosen_store"],
        "materials": {
            "base_total": round(materials_base, 2),
            "markup_pct": materials_markup_pct,
            "total_with_markup": round(materials_total_with_markup, 2),
            "line_items": pricing["line_items"],
        },
        "labor": {
            "hours": labor_hours,
            "rate": labor_rate,
            "total": round(labor_cost, 2),
        },
        "tax": {
            "rate": tax_rate,
            "amount": round(tax_amount, 2),
        },
        "grand_total": round(grand_total, 2),
    }
    return quote


def make_customer_friendly_quote(quote: dict, customer_name: str | None = None) -> str:
    """
    Use the LLM to turn the structured quote into a nice customer-facing text.
    """
    system_prompt = (
        "You are a professional fence contractor writing clear, "
        "friendly quotes for homeowners. Be concise, avoid jargon, "
        "and explain what is included in the price. Do NOT change the numbers."
    )

    user_prompt = f"""
Create a customer-facing quote based on this structured data.

Customer name: {customer_name or "Customer"}

Quote data (JSON-like):
{quote}

Requirements:
- Start with a short friendly greeting.
- Clearly state the fence length (number of 6' sections).
- Mention the store you’re sourcing materials from and that you’re using current prices as of today.
- Summarize materials and labor in plain language (no need to list every item unless it's helpful).
- Show a simple price breakdown: materials (with markup), labor, and total.
- End with a short note about timing and how long the quote is valid.
"""
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.4,
    )

    return response.choices[0].message.content


def run_interactive():
    print("Fence Quote Agent\n------------------")
    num_sections = int(input("Number of 6-foot sections: ").strip())
    labor_hours = float(input("Estimated labor hours: ").strip())
    labor_rate = float(input("Hourly labor rate (e.g., 75): ").strip())
    markup_pct = float(input("Materials markup % (e.g., 15): ").strip() or "15")
    customer_name = input("Customer name (optional): ").strip() or None

    quote_struct = compute_quote(
        num_sections=num_sections,
        labor_hours=labor_hours,
        labor_rate=labor_rate,
        materials_markup_pct=markup_pct,
    )

    print("\n--- Internal Quote Data (for you) ---")
    print(quote_struct)

    print("\n--- Customer Quote ---")
    pretty_quote = make_customer_friendly_quote(quote_struct, customer_name)
    print(pretty_quote)


if __name__ == "__main__":
    run_interactive()
