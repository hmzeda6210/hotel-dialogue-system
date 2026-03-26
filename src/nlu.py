#nlu.py
#natural language understanding module, takes raw user input and returns the intent and extracted slots.
import pickle
class IntentClassifier:
    def __init__(self,
                 model_path="data/models/intent_classifier.pkl",
                 vectorizer_path="data/models/tfidf_vectorizer.pkl"):
        #load saved intent classifier and vectoriser
        with open(model_path, "rb") as f:
            self.classifier = pickle.load(f)
        with open(vectorizer_path, "rb") as f:
            self.vectorizer = pickle.load(f)

    def predict(self, text):
        #convert text to TF-IDF vector and predict intent
        X = self.vectorizer.transform([text])
        intent = self.classifier.predict(X)[0]
        confidence = float(self.classifier.predict_proba(X).max())
        return {"intent": intent, "confidence": round(confidence, 2)}

class SlotFiller:
    def __init__(self,
                 model_path="data/models/slot_classifier.pkl",
                 vectorizer_path="data/models/slot_vectorizer.pkl"):
        #load saved slot classifier and vectoriser
        with open(model_path, "rb") as f:
            self.classifier = pickle.load(f)
        with open(vectorizer_path, "rb") as f:
            self.vectorizer = pickle.load(f)

    def extract_token_features(self, tokens, i):
        #build feature string for token i using context window
        word = tokens[i].lower()
        features = [
            f"word={word}",
            f"is_digit={word.isdigit()}",
            f"prefix2={word[:2]}",
            f"suffix2={word[-2:]}",
            f"prev={tokens[i-1].lower() if i > 0 else 'BOS'}",
            f"next={tokens[i+1].lower() if i < len(tokens)-1 else 'EOS'}"
        ]
        return " ".join(features)

    def predict(self, text):
        #tokenise and extract features for each token
        tokens = text.lower().split()
        features = [self.extract_token_features(tokens, i) for i in range(len(tokens))]
        
        #vectorise and predict labels
        X = self.vectorizer.transform(features)
        labels = self.classifier.predict(X)
        
        #extract slot values from BIO labels
        slots = {}
        current_slot = None
        current_value = []
        
        for token, label in zip(tokens, labels):
            if label.startswith("B-"):
                #save previous slot if exists
                if current_slot:
                    slots[current_slot] = " ".join(current_value)
                current_slot = label[2:]
                current_value = [token]
            elif label.startswith("I-") and current_slot:
                current_value.append(token)
            else:
                if current_slot:
                    slots[current_slot] = " ".join(current_value)
                current_slot = None
                current_value = []
        
        #save last slot if exists
        if current_slot:
            slots[current_slot] = " ".join(current_value)
        
        return slots
    
class NLU:
    def __init__(self):
        #combine intent classifier and slot filler into one interface
        self.intent_classifier = IntentClassifier()
        self.slot_filler = SlotFiller()

    def parse(self, text):
        #run both models and return combined result
        intent_result = self.intent_classifier.predict(text)
        slots = self.slot_filler.predict(text)
        return {
            "intent": intent_result["intent"],
            "confidence": intent_result["confidence"],
            "slots": slots
        }

if __name__ == "__main__":
    nlu = NLU()
    tests = [
        "I need a cheap hotel in the north",
        "Can you book it for 2 nights for 3 people",
        "I want a 4 star guesthouse with free parking"
    ]
    for t in tests:
        print(f"\nInput: {t}")
        print(f"Output: {nlu.parse(t)}")