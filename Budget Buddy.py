import csv
import os
from datetime import datetime

TRANSACTIONS_FILE = "transactions.csv"
BUDGETS_FILE = "budgets.csv"
GOALS_FILE = "goals.csv"


class BudgetBuddy:
    def __init__(self):
        self.transactions = []  # List of dicts: id, type, amount, category, description, date
        self.budgets = {}       # Dict of {category: monthly_limit}
        self.goals = {}         # Dict of {goal_name: {"target": float, "saved": float}}
        self._init_files()
        self.load_data()

    def _init_files(self):
        if not os.path.exists(TRANSACTIONS_FILE):
            with open(TRANSACTIONS_FILE, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["id", "type", "amount", "category", "description", "date"])

        if not os.path.exists(BUDGETS_FILE):
            with open(BUDGETS_FILE, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["category", "monthly_limit"])

        if not os.path.exists(GOALS_FILE):
            with open(GOALS_FILE, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["goal_name", "target", "saved"])

    def load_data(self):
        self.transactions = []
        if os.path.exists(TRANSACTIONS_FILE):
            try:
                with open(TRANSACTIONS_FILE, mode="r", newline="", encoding="utf-8") as f:
                    for row in csv.DictReader(f):
                        try:
                            self.transactions.append({
                                "id": int(row["id"]),
                                "type": row["type"].strip(),
                                "amount": float(row["amount"]),
                                "category": row["category"].strip(),
                                "description": row["description"].strip(),
                                "date": row["date"].strip(),
                            })
                        except (ValueError, KeyError, TypeError):
                            continue
            except IOError:
                print("⚠️ Warning: Could not read transactions CSV file. Starting fresh.")

        self.budgets = {}
        if os.path.exists(BUDGETS_FILE):
            try:
                with open(BUDGETS_FILE, mode="r", newline="", encoding="utf-8") as f:
                    for row in csv.DictReader(f):
                        try:
                            cat = row["category"].strip()
                            if cat:
                                self.budgets[cat] = float(row["monthly_limit"])
                        except (ValueError, KeyError, TypeError):
                            continue
            except IOError:
                print("⚠️ Warning: Could not read budgets CSV file. Starting fresh.")

        self.goals = {}
        if os.path.exists(GOALS_FILE):
            try:
                with open(GOALS_FILE, mode="r", newline="", encoding="utf-8") as f:
                    for row in csv.DictReader(f):
                        try:
                            name = row["goal_name"].strip()
                            if name:
                                self.goals[name] = {
                                    "target": float(row["target"]),
                                    "saved": float(row["saved"]),
                                }
                        except (ValueError, KeyError, TypeError):
                            continue
            except IOError:
                print("⚠️ Warning: Could not read goals CSV file. Starting fresh.")

    def save_transactions(self):
        with open(TRANSACTIONS_FILE, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "type", "amount", "category", "description", "date"])
            for t in self.transactions:
                writer.writerow([
                    t["id"],
                    t["type"],
                    f"{t['amount']:.2f}",
                    t["category"],
                    t["description"],
                    t["date"],
                ])

    def save_budgets(self):
        with open(BUDGETS_FILE, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["category", "monthly_limit"])
            for cat, limit in sorted(self.budgets.items()):
                writer.writerow([cat, f"{limit:.2f}"])

    def save_goals(self):
        with open(GOALS_FILE, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["goal_name", "target", "saved"])
            for name, info in sorted(self.goals.items()):
                writer.writerow([name, f"{info['target']:.2f}", f"{info['saved']:.2f}"])

    def save_data(self):
        self.save_transactions()
        self.save_budgets()
        self.save_goals()

    def add_transaction(self, t_type, amount, category, description=""):
        if amount <= 0:
            print("❌ Amount must be greater than zero.")
            return

        category = category.strip().title()
        next_id = max([t["id"] for t in self.transactions], default=0) + 1
        transaction = {
            "id": next_id,
            "type": t_type,  # "income" or "expense"
            "amount": round(float(amount), 2),
            "category": category,
            "description": description.strip(),
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        self.transactions.append(transaction)
        self.save_transactions()
        print(f"✅ Recorded {t_type}: ${amount:,.2f} under [{category}]")

        if t_type == "expense":
            self.check_budget_alert(category)

    def set_budget(self, category, limit):
        if limit < 0:
            print("❌ Budget limit cannot be negative.")
            return
        category = category.strip().title()
        self.budgets[category] = round(float(limit), 2)
        self.save_budgets()
        print(f"🎯 Monthly budget for [{category}] set to ${limit:,.2f}")

    def check_budget_alert(self, category):
        if category not in self.budgets:
            return
        limit = self.budgets[category]
        spent = sum(
            t["amount"] for t in self.transactions
            if t["type"] == "expense" and t["category"] == category
        )
        if limit > 0 and spent > limit:
            print(f"🚨 ALERT: You exceeded your [{category}] budget! (${spent:,.2f} / ${limit:,.2f})")
        elif limit > 0 and spent >= limit * 0.85:
            print(f"⚠️ WARNING: You have used {spent / limit * 100:.0f}% of your [{category}] budget (${spent:,.2f} / ${limit:,.2f})")

    def manage_goal(self, name, target=None, add_funds=0.0):
        name = name.strip().title()
        if name not in self.goals:
            if target is None or target <= 0:
                print("❌ New goals require a positive target amount.")
                return
            self.goals[name] = {"target": round(float(target), 2), "saved": 0.0}
            print(f"🌟 Created savings goal '{name}' with target ${target:,.2f}")

        if add_funds > 0:
            self.goals[name]["saved"] = round(
                self.goals[name]["saved"] + float(add_funds), 2
            )
            saved = self.goals[name]["saved"]
            goal_target = self.goals[name]["target"]
            pct = min((saved / goal_target) * 100, 100) if goal_target > 0 else 0
            print(f"💰 Added ${add_funds:,.2f} to '{name}'. Progress: ${saved:,.2f} / ${goal_target:,.2f} ({pct:.1f}%)")

        self.save_goals()

    def show_dashboard(self):
        total_income = sum(t["amount"] for t in self.transactions if t["type"] == "income")
        total_expense = sum(t["amount"] for t in self.transactions if t["type"] == "expense")
        net_balance = total_income - total_expense
        savings_rate = ((net_balance / total_income) * 100) if total_income > 0 else 0.0

        print("\n" + "=" * 50)
        print("📊 BUDGET BUDDY — FINANCIAL DASHBOARD")
        print("=" * 50)
        print(f"Total Income:    ${total_income:>12,.2f}")
        print(f"Total Expenses:  ${total_expense:>12,.2f}")
        print(f"Net Balance:     ${net_balance:>12,.2f}")
        print(f"Savings Rate:    {savings_rate:>12.1f}%")
        print("-" * 50)

        # Spending by Category
        print("📂 EXPENSE BREAKDOWN & BUDGET STATUS:")
        category_totals = {}
        for t in self.transactions:
            if t["type"] == "expense":
                cat = t["category"]
                category_totals[cat] = category_totals.get(cat, 0.0) + t["amount"]

        all_cats = set(category_totals.keys()).union(self.budgets.keys())
        if not all_cats:
            print("  No expenses or budgets recorded yet.")
        else:
            for cat in sorted(all_cats):
                spent = category_totals.get(cat, 0.0)
                if cat in self.budgets:
                    limit = self.budgets[cat]
                    status = "OVER" if spent > limit else "OK"
                    print(f"  • {cat:<15} ${spent:>9,.2f} / ${limit:>9,.2f} [{status}]")
                else:
                    print(f"  • {cat:<15} ${spent:>9,.2f} (No limit set)")

        # Savings Goals
        print("-" * 50)
        print("🎯 SAVINGS GOALS:")
        if not self.goals:
            print("  No savings goals created yet.")
        else:
            for name, info in sorted(self.goals.items()):
                pct = (info["saved"] / info["target"]) * 100 if info["target"] > 0 else 0
                bar_filled = min(int(pct // 5), 20)
                bar = "█" * bar_filled + "░" * (20 - bar_filled)
                print(f"  • {name:<15} [{bar}] {pct:>5.1f}% (${info['saved']:,.2f} / ${info['target']:,.2f})")
        print("=" * 50 + "\n")

    def show_history(self, limit=10):
        print(f"\n📜 RECENT TRANSACTIONS (Last {limit}):")
        print("-" * 65)
        recent = self.transactions[-limit:]
        if not recent:
            print("  No transactions found.")
        for t in reversed(recent):
            sign = "+" if t["type"] == "income" else "-"
            desc = f" ({t['description']})" if t["description"] else ""
            print(f"[{t['date']}] {sign}${t['amount']:>8,.2f} | {t['category']:<12}{desc}")
        print("-" * 65 + "\n")


def main():
    app = BudgetBuddy()

    while True:
        print("=== 💵 BUDGET BUDDY MENU ===")
        print("1. Add Income")
        print("2. Add Expense")
        print("3. Set Category Budget")
        print("4. Manage Savings Goal")
        print("5. View Financial Dashboard")
        print("6. View Transaction History")
        print("7. Exit")

        choice = input("\nSelect an option (1-7): ").strip()

        try:
            if choice == "1":
                amt = float(input("Enter income amount: $"))
                cat = input("Source/Category (e.g., Salary, Freelance): ")
                desc = input("Description (optional): ")
                app.add_transaction("income", amt, cat, desc)

            elif choice == "2":
                amt = float(input("Enter expense amount: $"))
                cat = input("Category (e.g., Food, Rent, Transport): ")
                desc = input("Description (optional): ")
                app.add_transaction("expense", amt, cat, desc)

            elif choice == "3":
                cat = input("Category name: ")
                limit = float(input(f"Monthly budget limit for {cat.title()}: $"))
                app.set_budget(cat, limit)

            elif choice == "4":
                name = input("Goal name (e.g., Emergency Fund, Vacation): ")
                if name.strip().title() not in app.goals:
                    target = float(input("Target amount: $"))
                    initial = float(input("Initial deposit (0 if none): $"))
                    app.manage_goal(name, target=target, add_funds=initial)
                else:
                    deposit = float(input("Amount to add to this goal: $"))
                    app.manage_goal(name, add_funds=deposit)

            elif choice == "5":
                app.show_dashboard()

            elif choice == "6":
                app.show_history()

            elif choice == "7":
                print("👋 Goodbye! Your financial data has been saved.")
                break

            else:
                print("❌ Invalid option. Please enter a number from 1 to 7.")

        except ValueError:
            print("❌ Invalid input. Please enter a valid number for amounts.")
        print()


if __name__ == "__main__":
    main()
    