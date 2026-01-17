import json
import csv
import os
from datetime import datetime
from collections import defaultdict

class FinanceTracker:
    def __init__(self):
        self.file = "finance_data.json"
        self.data = self.load_data()
    
    def load_data(self):
        if os.path.exists(self.file):
            with open(self.file, 'r') as f:
                return json.load(f)
        return {"transactions": [], "goals": []}
    
    def save_data(self):
        with open(self.file, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def add_transaction(self):
        print("\n=== Add Transaction ===")
        t_type = input("Type (income/expense): ").lower()
        
        # Validate amount input
        while True:
            try:
                amount = float(input("Amount: $"))
                if amount <= 0:
                    print("❌ Amount must be greater than 0. Please try again.")
                    continue
                break
            except ValueError:
                print("❌ Invalid amount. Please enter a valid number.")
        
        desc = input("Description: ")
        category = input("Category: ")
        date = input("Date (YYYY-MM-DD) or Enter for today: ") or datetime.now().strftime("%Y-%m-%d")
        
        self.data["transactions"].append({
            "type": t_type, "amount": amount, "description": desc,
            "category": category, "date": date
        })
        self.save_data()
        print(f"✅ Added {t_type}: ${amount:.2f}")
    
    def view_summary(self):
        if not self.data["transactions"]:
            print("No transactions yet.")
            return
        
        # Current month
        current_month = datetime.now().strftime("%Y-%m")
        month_trans = [t for t in self.data["transactions"] if t["date"].startswith(current_month)]
        
        income = sum(t["amount"] for t in month_trans if t["type"] == "income")
        expenses = sum(t["amount"] for t in month_trans if t["type"] == "expense")
        
        print(f"\n=== {datetime.now().strftime('%B %Y')} Summary ===")
        print(f"Income:  ${income:.2f}")
        print(f"Expenses: ${expenses:.2f}")
        print(f"Net:     ${(income - expenses):.2f}")
        
        # Category breakdown
        print(f"\n--- Expenses by Category ---")
        cat_totals = defaultdict(float)
        for t in month_trans:
            if t["type"] == "expense":
                cat_totals[t["category"]] += t["amount"]
        
        for cat, amount in sorted(cat_totals.items(), key=lambda x: x[1], reverse=True):
            percent = (amount / expenses * 100) if expenses > 0 else 0
            print(f"{cat}: ${amount:.2f} ({percent:.0f}%)")
        
        # Recent transactions
        print(f"\n--- Recent Transactions ---")
        recent = sorted(self.data["transactions"], key=lambda x: x["date"], reverse=True)[:5]
        for t in recent:
            sign = "+" if t["type"] == "income" else "-"
            print(f"{t['date']} {sign}${t['amount']:.2f} - {t['description']}")
    
    def add_goal(self):
        print("\n=== Add Savings Goal ===")
        name = input("Goal name: ")
        
        # Validate target amount input
        while True:
            try:
                target = float(input("Target amount: $"))
                if target <= 0:
                    print("❌ Target amount must be greater than 0. Please try again.")
                    continue
                break
            except ValueError:
                print("❌ Invalid target amount. Please enter a valid number.")
        
        # Validate current amount input
        while True:
            current_input = input("Current amount: $") or "0"
            try:
                current = float(current_input)
                if current < 0:
                    print("❌ Current amount cannot be negative. Please try again.")
                    continue
                break
            except ValueError:
                print("❌ Invalid current amount. Please enter a valid number.")
        
        # Update existing or add new
        for goal in self.data["goals"]:
            if goal["name"] == name:
                goal["target"] = target
                goal["current"] = current
                self.save_data()
                print(f"✅ Updated goal: {name}")
                return
        
        self.data["goals"].append({"name": name, "target": target, "current": current})
        self.save_data()
        print(f"✅ Added goal: {name}")
    
    def view_goals(self):
        if not self.data["goals"]:
            print("No savings goals yet.")
            return
        
        print("\n=== Savings Goals ===")
        for goal in self.data["goals"]:
            progress = (goal["current"] / goal["target"]) * 100
            bar_length = 15
            filled = int(bar_length * progress / 100)
            bar = "█" * filled + "░" * (bar_length - filled)
            
            print(f"\n{goal['name']}")
            print(f"[{bar}] {progress:.0f}% - ${goal['current']:.0f}/${goal['target']:.0f}")
            print(f"Remaining: ${goal['target'] - goal['current']:.0f}")
    
    def export_csv(self):
        filename = f"finance_{datetime.now().strftime('%Y%m%d')}.csv"
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Date", "Type", "Category", "Description", "Amount"])
            for t in self.data["transactions"]:
                writer.writerow([t['date'], t['type'], t['category'], t['description'], t['amount']])
        print(f"✅ Exported to {filename}")
    
    def run(self):
        print("💰 Personal Finance Tracker")
        
        while True:
            print("\n1. Add Transaction")
            print("2. View Summary")
            print("3. Add Goal")
            print("4. View Goals")
            print("5. Export CSV")
            print("6. Exit")
            
            choice = input("Choice (1-6): ").strip()
            
            if choice == "1":
                self.add_transaction()
            elif choice == "2":
                self.view_summary()
            elif choice == "3":
                self.add_goal()
            elif choice == "4":
                self.view_goals()
            elif choice == "5":
                self.export_csv()
            elif choice == "6":
                print("Goodbye! 💰")
                break
            else:
                print("Invalid choice.")

if __name__ == "__main__":
    FinanceTracker().run()
