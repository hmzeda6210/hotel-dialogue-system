#policy.py
#dialogue policy, decides what action to take next based on the current state.
# GUS-style rule-based policy.

import json
from src.domain import SLOTS, SLOT_QUESTIONS

#slots to ask about first (search slots), then booking slots
SLOT_PRIORITY = [
    "area", "pricerange",
    "book_people", "book_nights", "book_day"
]

def query_database(slots):
    #load hotel database and return hotels matching all filled slots
    with open("data/hotels.json") as f:
        hotels = json.load(f)

    results = []
    for hotel in hotels:
        match = True
        for slot, val in slots.items():
            if val is not None:
                #only check slots that exist in the hotel record
                if slot in hotel and hotel.get(slot) != val:
                    match = False
        if match:
            results.append(hotel)
    return results

class DialoguePolicy:
    def __init__(self):
        self.results = []
        self.informed = False  #tracks if we already showed results

    def decide(self, state):
        slots = state.slots

        #1.ask for missing slots
        for slot in SLOT_PRIORITY:
            if slots.get(slot) is None:
                return {
                    "action": "ask",
                    "slot": slot,
                    "question": SLOT_QUESTIONS[slot]
                }

        #2.query database
        self.results = query_database(slots)

        if not self.results:
            return {"action": "no_match", "results": []}

        #3.if not yet informed, show results
        if not self.informed:
            self.informed = True
            return {"action": "inform", "results": self.results}

        #4.already informed, confirm booking
        return {
            "action": "book_confirm",
            "hotel": self.results[0],
            "nights": slots.get("book_nights"),
            "day": slots.get("book_day"),
            "people": slots.get("book_people")
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