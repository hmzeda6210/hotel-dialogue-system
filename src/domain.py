# domain.py
# Central config file — defines all slots the system needs to fill for a hotel booking.

DOMAIN = "hotel"

# All slots the system needs to collect
SLOTS = {
    "area":         {"type": "categorical", "values": ["north", "south", "east", "west", "centre"]},
    "pricerange":   {"type": "categorical", "values": ["cheap", "moderate", "expensive"]},
    "stars":        {"type": "categorical", "values": ["1", "2", "3", "4", "5"]},
    "internet":     {"type": "boolean",     "values": ["yes", "no"]},
    "parking":      {"type": "boolean",     "values": ["yes", "no"]},
    "type":         {"type": "categorical", "values": ["hotel", "guesthouse"]},
    "book_people":  {"type": "integer",     "values": None},
    "book_nights":  {"type": "integer",     "values": None},
    "book_day":     {"type": "categorical", "values": ["monday", "tuesday", "wednesday",
                                                        "thursday", "friday", "saturday", "sunday"]},
}

# Questions the system asks to fill each slot
SLOT_QUESTIONS = {
    "area":         "What area of the city would you like to stay in?",
    "pricerange":   "What is your budget? (cheap, moderate, or expensive)",
    "stars":        "How many stars would you like the hotel to have?",
    "internet":     "Do you need free internet?",
    "parking":      "Do you need parking?",
    "type":         "Are you looking for a hotel or a guesthouse?",
    "book_people":  "How many people is the booking for?",
    "book_nights":  "How many nights will you be staying?",
    "book_day":     "What day will you be checking in?",
}