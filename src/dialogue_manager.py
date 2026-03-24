from src.nlu import NLU
from src.dst import DialogueState
from src.policy import DialoguePolicy
from src.nlg import NLG

class DialogueManager:
    def __init__(self):
        self.nlu = NLU()
        self.state = DialogueState()
        self.policy = DialoguePolicy()
        self.nlg = NLG()
        self.last_asked_slot = None  # track which slot we just asked about
        self.finished = False

    def process(self, user_input):
        # Step 1 — NLU
        nlu_result = self.nlu.parse(user_input)
        print(f"  [NLU] {nlu_result}")

        # Step 2 — DST: if we just asked for a specific slot, assign directly
        if self.last_asked_slot:
            slot_value = user_input.strip().lower()
            self.state.update({self.last_asked_slot: slot_value})
            self.last_asked_slot = None
        else:
            self.state.update(nlu_result["slots"])

        print(f"  [DST] {self.state.slots}")

        # Step 3 — Policy
        action = self.policy.decide(self.state)
        print(f"  [Policy] {action['action']}")

        # Remember which slot we just asked about
        if action["action"] == "ask":
            self.last_asked_slot = action["slot"]
            
        if action["action"] == "book_confirm":
            self.reset()
            self.finished = True

        # Step 4 — NLG
        response = self.nlg.generate(action)
        return response

    def reset(self):
        self.state.reset()
        self.last_asked_slot = None
        self.policy.informed = False

if __name__ == "__main__":
    dm = DialogueManager()
    print("Hotel Booking System — type 'quit' to exit\n")
    while True:
        user_input = input("You: ")
        if user_input.lower() == "quit":
            break
        response = dm.process(user_input)
        print(f"System: {response}\n")
        if dm.finished:
            break