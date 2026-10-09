#!/usr/bin/env python3
"""Tax calculator: progressive income tax and VAT / sales tax.

Run it with:  python tax_calculator.py
The bracket rates below are placeholders. Edit them from the menu (option 3)
and they are saved to tax_config.json next to the script.
"""

import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

CONFIG_FILE = Path(__file__).with_name("tax_config.json")
CENT = Decimal("0.01")
HUNDRED = Decimal(100)

# (upper limit, rate %). An upper limit of None means "no limit" (last bracket).
SAMPLE_BRACKETS = [(10000, 0), (30000, 10), (80000, 20), (None, 30)]


@dataclass
class Bracket:
    upper: Decimal | None
    rate: Decimal


@dataclass
class Slice:
    lower: Decimal
    upper: Decimal | None
    amount: Decimal
    rate: Decimal
    tax: Decimal


@dataclass
class IncomeResult:
    taxable: Decimal
    slices: list[Slice]
    total_tax: Decimal
    take_home: Decimal
    effective_rate: Decimal
    marginal_rate: Decimal


def q(x: Decimal) -> Decimal:
    """Round to cents."""
    return x.quantize(CENT, rounding=ROUND_HALF_UP)


def validate_brackets(brackets: list[Bracket]) -> None:
    if not brackets:
        raise ValueError("Add at least one bracket.")
    if brackets[-1].upper is not None:
        raise ValueError("The last bracket must have no upper limit.")
    previous = Decimal(0)
    for b in brackets[:-1]:
        if b.upper is None or b.upper <= previous:
            raise ValueError("Each upper limit must be higher than the one above it.")
        previous = b.upper
    if any(b.rate < 0 or b.rate > 100 for b in brackets):
        raise ValueError("Rates must be between 0 and 100.")


def calc_income_tax(income: Decimal, deductions: Decimal,
                    brackets: list[Bracket]) -> IncomeResult:
    validate_brackets(brackets)
    taxable = max(Decimal(0), income - deductions)
    lower = Decimal(0)
    slices: list[Slice] = []
    total = Decimal(0)
    marginal = Decimal(0)

    for b in brackets:
        top = taxable if b.upper is None else min(taxable, b.upper)
        amount = max(Decimal(0), top - lower)
        tax = q(amount * b.rate / HUNDRED)
        if taxable > lower:
            marginal = b.rate
        slices.append(Slice(lower, b.upper, amount, b.rate, tax))
        total += tax
        if b.upper is not None:
            lower = b.upper

    effective = (total / income * HUNDRED) if income > 0 else Decimal(0)
    return IncomeResult(taxable, slices, total, income - total, effective, marginal)


def calc_vat(amount: Decimal, rate: Decimal, include: bool) -> tuple[Decimal, Decimal, Decimal]:
    """Return (net, tax, gross). include=True means `amount` already includes tax."""
    r = rate / HUNDRED
    if include:
        gross = amount
        net = q(amount / (1 + r))
        return net, gross - net, gross
    tax = q(amount * r)
    return amount, tax, amount + tax




def load_config() -> dict:
    cfg = {"currency": "$", "brackets": SAMPLE_BRACKETS}
    try:
        data = json.loads(CONFIG_FILE.read_text())
        if isinstance(data.get("brackets"), list) and data["brackets"]:
            cfg.update(data)
    except (OSError, ValueError):
        pass
    return cfg


def save_config(cfg: dict) -> None:
    try:
        CONFIG_FILE.write_text(json.dumps(cfg, indent=2))
    except OSError as e:
        print(f"Could not save settings: {e}")


def to_brackets(raw: list) -> list[Bracket]:
    return [Bracket(None if u is None else Decimal(str(u)), Decimal(str(r))) for u, r in raw]


# 

def ask_decimal(prompt: str, default: Decimal | None = None) -> Decimal:
    while True:
        suffix = f" [{default}]" if default is not None else ""
        text = input(f"{prompt}{suffix}: ").strip().replace(",", "")
        if not text and default is not None:
            return default
        try:
            value = Decimal(text)
            if value >= 0:
                return value
        except InvalidOperation:
            pass
        print("Enter a number that is zero or more.")


def fmt(x: Decimal, cur: str) -> str:
    return f"{cur} {q(x):,.2f}".strip()


def show_brackets(brackets: list[Bracket], cur: str) -> None:
    lower = Decimal(0)
    for i, b in enumerate(brackets, 1):
        upto = "no limit" if b.upper is None else fmt(b.upper, cur)
        print(f"  {i}. {fmt(lower, cur)} to {upto} at {b.rate}%")
        if b.upper is not None:
            lower = b.upper


# ---------- menu actions ----------

def income_tax_menu(cfg: dict) -> None:
    cur = cfg["currency"]
    income = ask_decimal("Annual income")
    deductions = ask_decimal("Allowances and deductions", Decimal(0))
    try:
        r = calc_income_tax(income, deductions, to_brackets(cfg["brackets"]))
    except ValueError as e:
        print(f"Bracket problem: {e}")
        return

    print(f"\n{'Bracket':<34}{'Taxed amount':>16}{'Rate':>8}{'Tax':>16}")
    for s in r.slices:
        upto = "and above" if s.upper is None else f"to {fmt(s.upper, cur)}"
        label = f"{fmt(s.lower, cur)} {upto}"
        print(f"{label:<34}{fmt(s.amount, cur):>16}{str(s.rate) + '%':>8}{fmt(s.tax, cur):>16}")
    print(f"\nTaxable income : {fmt(r.taxable, cur)}")
    print(f"Tax payable    : {fmt(r.total_tax, cur)}")
    print(f"Take-home      : {fmt(r.take_home, cur)}")
    print(f"Effective rate : {q(r.effective_rate)}%")
    print(f"Marginal rate  : {r.marginal_rate}%\n")


def vat_menu(cfg: dict) -> None:
    cur = cfg["currency"]
    mode = input("Add tax to a price (a) or remove it from a price (r)? [a]: ").strip().lower()
    include = mode.startswith("r")
    rate = ask_decimal("Tax rate %", Decimal(18))
    amount = ask_decimal("Price including tax" if include else "Price before tax")
    net, tax, gross = calc_vat(amount, rate, include)
    print(f"\nPrice before tax : {fmt(net, cur)}")
    print(f"Tax              : {fmt(tax, cur)}")
    print(f"Price with tax   : {fmt(gross, cur)}\n")


def edit_brackets(cfg: dict) -> None:
    cur = cfg["currency"]
    print("\nCurrent brackets:")
    show_brackets(to_brackets(cfg["brackets"]), cur)
    print("\nEnter new brackets, one per line, as: upper_limit rate")
    print("Use '-' as the upper limit for the last bracket. Example: 30000 10")
    print("Press Enter on an empty line to finish, or type 'sample' to restore the samples.")
    raw: list = []
    while True:
        line = input("> ").strip()
        if line.lower() == "sample":
            raw = list(SAMPLE_BRACKETS)
            break
        if not line:
            break
        try:
            upper, rate = line.split()
            raw.append((None if upper == "-" else float(upper), float(rate)))
        except ValueError:
            print("Use the form: upper_limit rate (for example: 30000 10)")
    if not raw:
        print("No changes made.\n")
        return
    try:
        validate_brackets(to_brackets(raw))
    except ValueError as e:
        print(f"Not saved: {e}\n")
        return
    cfg["brackets"] = raw
    save_config(cfg)
    print("Brackets saved.\n")


def main() -> None:
    cfg = load_config()
    actions = {"1": income_tax_menu, "2": vat_menu, "3": edit_brackets}
    print("Tax calculator (estimates only, not tax advice)")
    while True:
        print("1) Income tax   2) VAT / sales tax   3) Edit brackets   4) Currency   q) Quit")
        choice = input("Choose: ").strip().lower()
        if choice in ("q", "quit", "exit"):
            break
        if choice == "4":
            cfg["currency"] = input("Currency symbol or code: ").strip()
            save_config(cfg)
        elif choice in actions:
            try:
                actions[choice](cfg)
            except (EOFError, KeyboardInterrupt):
                print()
                break
        else:
            print("Pick 1, 2, 3, 4 or q.")


if __name__ == "__main__":
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        print()