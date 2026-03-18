
# Dialogue State Tracker — keeps track of all slot values across the conversation.
from domain import SLOTS

class DialogueState:
    def __init__(self):
        self.slots = {slot: None for slot in SLOTS} #Initialise all slots to None at the start of a conversation

    def update(self, new_slots):
        for slot, value in new_slots.items(): #Overwrite slot values with anything the NLU just extracted
            if slot in self.slots:
                self.slots[slot] = value

    def reset(self):
        self.slots = {slot: None for slot in SLOTS} # Wipe all slots back to None at the end of a conversation

    def get_missing_slots(self):
        return [slot for slot, value in self.slots.items() if value is None]# Return list of slots that haven't been filled yet

    def is_complete(self):
        return all(value is not None for value in self.slots.values())#Return True if all slots are filled

    def __repr__(self):
        return f"DialogueState({self.slots})" #print the state


if __name__ == "__main__":
    state = DialogueState()
    print("Initial state:")
    print(state)

    print("\nAfter first user turn:")
    state.update({"area": "north", "pricerange": "cheap"})
    print(state)

    print("\nMissing slots:")
    print(state.get_missing_slots())

    print("\nAfter correction:")
    state.update({"pricerange": "expensive"})
    print(state)

    print("\nIs complete?", state.is_complete())
    