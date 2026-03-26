#nlg.py
#natural language generation, converts policy actions into human-readable responses.
#uses template-based generation.

class NLG:
    def generate(self, action):
        action_type = action["action"]

        #ask user to fill a slot
        if action_type == "ask":
            return action["question"]

        #inform user of matching hotels
        elif action_type == "inform":
            hotels = action["results"]
            if len(hotels) == 1:
                h = hotels[0]
                return (f"I found a hotel for you: {h['name']}. "
                        f"It is {h['pricerange']}, located in the {h['area']}, "
                        f"and has {h['stars']} stars.")
            else:
                names = ", ".join([h["name"] for h in hotels])
                return f"I found {len(hotels)} hotels matching your request: {names}."

        #no hotels matched
        elif action_type == "no_match":
            return "I'm sorry, I couldn't find any hotels matching your criteria."
            
        #booking confirmed
        elif action_type == "book_confirm":
            h = action["hotel"]
            return (f"Great! I've booked {h['name']} for you. "
                    f"Staying {action['nights']} nights from {action['day']} "
                    f"for {action['people']} people. "
                    f"Thank you for using our service. Goodbye!")
        #fallback
        else:
            return "I'm sorry, I didn't understand that. Could you rephrase?"


if __name__ == "__main__":
    nlg = NLG()

    #test all action types
    print(nlg.generate({"action": "ask", "slot": "area", 
                         "question": "What area would you like to stay in?"}))
    
    print(nlg.generate({"action": "inform", "results": [
        {"name": "Budget Inn", "area": "north", "pricerange": "cheap", "stars": "2"}
    ]}))
    
    print(nlg.generate({"action": "no_match", "results": []}))
    
    print(nlg.generate({"action": "book_confirm", 
                         "hotel": {"name": "Budget Inn"},
                         "nights": "3", "day": "monday", "people": "2"}))