# An AI customer-support TEAM for a pretend pizza company:
#   a RECEPTIONIST AI reads each message and sends it to the right SPECIALIST AI, each with its own tools.
#   Refunds need YOUR approval (y/N) before they happen.
from typing import Literal

from pydantic import BaseModel

import ai
from agent import run_agent, tool

# ---------- pretend company data ----------
ORDERS = {
    "A100": {"customer": "Priya", "items": "Large Margherita", "price": 14.0, "status": "delivered 40 min late"},
    "A101": {"customer": "Tom", "items": "2x Pepperoni, Garlic bread", "price": 31.5, "status": "out for delivery"},
    "A102": {"customer": "Ana", "items": "Veggie Supreme", "price": 16.0, "status": "delivered"},
}
MENU = "Margherita $12/$14, Pepperoni $13/$15, Veggie Supreme $14/$16, Garlic bread $4.50. Gluten-free base +$2. Vegan cheese available."


# ---------- tools ----------
def look_up_order(order_id):
    return str(ORDERS.get(order_id.upper(), "No order with that number"))


def refund_order(order_id, amount):
    order = ORDERS.get(order_id.upper())
    if not order:
        return "No order with that number"
    if not 0 < float(amount) <= order["price"]:          # a rule in CODE: the AI can't talk its way past it
        return f"Refused: a refund must be more than $0 and at most the order price (${order['price']})"
    order["status"] += f", refunded ${amount}"
    return f"Refunded ${amount} for {order_id}"


def read_menu():
    return MENU


# ---------- the team ----------
class Route(BaseModel):
    team: Literal["orders", "menu", "complaints"]
    mood: Literal["happy", "neutral", "upset"]


SPECIALISTS = {
    "orders": ("You handle order status questions. Look orders up before answering.",
               [tool(look_up_order, "Find an order by its number", {"order_id": ("string", "e.g. A100")})]),
    "menu": ("You answer menu, price and allergy questions using the menu tool only.",
             [tool(read_menu, "Get the full menu with prices", {})]),
    "complaints": ("You handle complaints kindly. Look up the order, apologise, and offer a fair refund (max 50% for lateness).",
                   [tool(look_up_order, "Find an order by its number", {"order_id": ("string", "e.g. A100")}),
                    tool(refund_order, "Refund money for an order", {"order_id": ("string", "order number"), "amount": ("number", "dollars")})]),
}


def handle(message):
    route = ai.ask_for_data(f"Customer message: {message}", Route,
                            system="You are a receptionist at a pizza company. Pick the team that should handle this message.")
    print(f"📬 Receptionist → {route.team} team (customer seems {route.mood})")
    instructions, tools = SPECIALISTS[route.team]
    return run_agent(message, tools, name=route.team.title(), needs_approval={"refund_order"},
                     system=instructions + " Be friendly and brief.")


if __name__ == "__main__":
    inbox = ["Where is my order A101?",
             "Do you have a vegan option and how much is a large one?",
             "My pizza (order A100) arrived 40 minutes late and cold. Not happy!"]
    for message in inbox:
        print(f"\n{'=' * 60}\n💬 Customer: {message}")
        print(f"🤖 Reply: {handle(message)}")
