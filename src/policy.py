# policy.py
# Dialogue Policy — decides what action to take next based on the current state.
# GUS-style rule-based policy.

import json
from domain import SLOTS, SLOT_QUESTIONS

# Slots to ask about first (search slots), then booking slots
SLOT_PRIORITY = [
    "area", "pricerange", "type", "stars", "internet", "parking",
    "book_people", "book_nights", "book_day"
]

def query_database(slots):
    # Load hotel database and return hotels matching all filled slots
    with open("data/hotels.json") as f:
        hotels = json.load(f)

    results = []
    for hotel in hotels:
        match = True
        for slot, val in slots.items():
            if val is not None:
                # Only check slots that exist in the hotel record
                if slot in hotel and hotel.get(slot) != val:
                    match = False
        if match:
            results.append(hotel)
    return results


class DialoguePolicy:
    def __init__(self):
        self.results = []

    def decide(self, state):
        # Get the current slot values
        slots = state.slots

        # Step 1 — find the next unfilled slot in priority order and ask for it
        for slot in SLOT_PRIORITY:
            if slots.get(slot) is None:
                return {
                    "action": "ask",
                    "slot": slot,
                    "question": SLOT_QUESTIONS[slot]
                }

        # Step 2 — all slots filled, query the database
        self.results = query_database(slots)

        # Step 3 — return results or no match
        if self.results:
            return {
                "action": "inform",
                "results": self.results
            }
        else:
            return {
                "action": "no_match",
                "results": []
            }


if __name__ == "__main__":
    class FakeState:
        slots = {
            "area": "north",
            "pricerange": "cheap",
            "stars": "2",
            "internet": "yes",
            "parking": "yes",
            "type": "hotel",
            "book_people": "2",
            "book_nights": "3",
            "book_day": "monday"
        }

    policy = DialoguePolicy()
    action = policy.decide(FakeState())
    print("Policy decision:", action)