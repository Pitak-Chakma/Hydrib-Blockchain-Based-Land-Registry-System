bugs = [
    {"id": 1, "desc": "Login button not working", "status": "Open"},
    {"id": 2, "desc": "Price not updating on cart", "status": "Open"},
    {"id": 3, "desc": "Slow dashboard loading", "status": "Open"}
]

def show_bugs():
    for b in bugs:
        print(f"[{b['id']}] {b['desc']} - {b['status']}")

def fix_bug(bug_id):
    for b in bugs:
        if b["id"] == bug_id:
            b["status"] = "Fixed"
            print(f"✅ Bug {bug_id} marked as Fixed")

print("📋 User Reported Bugs")
show_bugs()
fix_bug(2)  # Owner fixes bug #2
print("\n🔄 Updated Bug List")
show_bugs()