# Hotel Booking Dialogue System

A modular, task-oriented dialogue system for hotel booking, built from scratch in Python. It covers the full pipeline: natural language understanding (NLU), dialogue state tracking (DST), dialogue policy, natural language generation (NLG) and a dialogue manager that ties them together in a terminal conversation loop.

Built as coursework for ECS763U/P Natural Language Processing at Queen Mary University of London. The NLU models are trained on the hotel portion of MultiWOZ 2.2. The rest of the pipeline is hand-written.

---

## Results at a glance

| Component | Metric | Score | How it was measured |
|---|---|---|---|
| Intent classifier | Accuracy | 0.89 | Random 80/20 split of hotel user turns from the MultiWOZ 2.2 train split (2,945 test turns) |
| Intent classifier | Macro F1 | 0.87 | Same as above |
| Slot filler | Micro F1 (seqeval) | 0.62 | Sentence-level 80/20 split of auto-generated BIO data (2,747 test sentences). See the leakage note below |
| Slot filler | Macro F1 (seqeval) | 0.63 | Same as above |
| Full system | Task completion | 4/5 (80%) | 5 scripted conversations run against the 8-hotel JSON database |

These numbers come with caveats, set out in [Evaluation](#evaluation). None of them are on the official MultiWOZ test split, and the task completion figure is based on a very small, hand-written test set.

---

## Architecture

```
User input
    |
    v
NLU  (src/nlu.py)              intent: find_hotel / book_hotel
    |                          slots:  BIO token tagger
    v
DST  (src/dst.py)              keeps a slot -> value frame across turns
    |
    v
Policy  (src/policy.py)        rule-based (GUS-style): ask for the next missing slot,
    |                          query the database, inform, confirm booking
    v
NLG  (src/nlg.py)              template-based responses
    |
    v
System response
```

`src/dialogue_manager.py` runs these four steps on every user turn and prints a debug trace (`[NLU]`, `[DST]`, `[Policy]`) so the state at each stage is visible.

---

## Example conversation

A real run of the system, with the debug trace removed:

```
You:    i want a cheap hotel
System: What area of the city would you like to stay in?
You:    north
System: How many people is the booking for?
You:    3
System: How many nights will you be staying?
You:    2
System: What day will you be checking in?
You:    Friday
System: I found a hotel for you: Budget Inn. It is cheap, located in the north, and has 2 stars.
You:    book it
System: Great! I've booked Budget Inn for you. Staying 2 nights from friday for 3 people.
        Thank you for using our service. Goodbye!
```

The same first turn with the trace switched on:

```
[NLU]    {'intent': 'find_hotel', 'confidence': 0.83, 'slots': {'pricerange': 'cheap', 'type': 'hotel'}}
[DST]    {'area': None, 'pricerange': 'cheap', ..., 'type': 'hotel', 'book_people': None, ...}
[Policy] ask
```

---

## How it works

### 1. Domain (`src/domain.py`)

Defines the 9 slots the system knows about, their types and valid values, and the question asked for each one.

| Slot | Type | Values |
|---|---|---|
| `area` | categorical | north, south, east, west, centre |
| `pricerange` | categorical | cheap, moderate, expensive |
| `stars` | categorical | 1–5 |
| `internet` | boolean | yes, no |
| `parking` | boolean | yes, no |
| `type` | categorical | hotel, guesthouse |
| `book_people` | integer | any |
| `book_nights` | integer | any |
| `book_day` | categorical | monday–sunday |

### 2. Data (`notebooks/01_explore.ipynb`)

- MultiWOZ 2.2 is loaded from the Hugging Face Hub (`pfb30/multi_woz_v22`): 8,437 train / 1,000 validation / 1,000 test dialogues.
- Dialogues where `hotel` appears in `services` are kept: 3,369 train / 418 validation / 395 test.
- These are saved to `data/multiwoz/` as JSON.

### 3. NLU (`src/nlu.py`, trained in `notebooks/02_nlu.ipynb`)

**Intent classification**
- Training examples are user turns where the hotel frame's `active_intent` is `find_hotel` or `book_hotel`. Turns of 3 words or fewer are dropped.
- This leaves 14,723 examples: 10,389 `find_hotel` and 4,334 `book_hotel`.
- Model: TF-IDF (5,000 features) + Logistic Regression with `class_weight="balanced"` to offset the class imbalance.

**Slot filling (BIO tagging)**
- MultiWOZ gives slot values per turn, not token-level tags. BIO labels were therefore generated automatically: each utterance is lowercased and split on whitespace, and each hotel slot value from that turn's dialogue state is string-matched against the tokens. The first matching token gets `B-slot` and following tokens get `I-slot`.
- This gives 13,731 tagged turns and 178,419 tokens.
- Each token is represented by a context-window feature string: the word, `is_digit`, a 2-character prefix and suffix, and the previous and next word (`BOS`/`EOS` at the edges).
- Model: TF-IDF over those feature strings + Logistic Regression (`class_weight="balanced"`), predicting one label per token.
- At inference, consecutive `B-`/`I-` labels are merged back into slot values.

The `NLU` class wraps both models and returns `{"intent", "confidence", "slots"}`.

### 4. Dialogue state tracking (`src/dst.py`)

`DialogueState` holds a dictionary of all 9 slots, initialised to `None`.

- `update()` overwrites any known slot with a new value. This is how corrections work: the latest value wins.
- `get_missing_slots()` and `is_complete()` report what is still unfilled.
- `reset()` clears the frame for a new conversation.

### 5. Policy (`src/policy.py`)

A rule-based, frame-driven policy in the style of GUS:

1. Walk through `SLOT_PRIORITY` (`area`, `pricerange`, `book_people`, `book_nights`, `book_day`) and ask for the first slot that is still `None`.
2. Once those are filled, query `data/hotels.json`. A hotel matches if it agrees with every filled slot that exists as a field in the hotel record. Booking slots are not hotel fields, so they are ignored in the query.
3. If nothing matches, the action is `no_match`.
4. On the first successful query, the action is `inform`.
5. On the next turn, the action is `book_confirm` for the first matching hotel.

`stars`, `internet`, `parking` and `type` are never asked for. They only filter results if the user volunteers them.

### 6. NLG (`src/nlg.py`)

Template strings for each policy action:
- `ask` returns the slot question from `domain.py`.
- `inform` describes one hotel, or lists the names if there are several.
- `no_match` apologises that nothing matched.
- `book_confirm` confirms the booking and says goodbye.

A fallback message exists for unknown actions.

### 7. Dialogue manager (`src/dialogue_manager.py`)

Runs NLU, then DST, then Policy, then NLG on each turn.

- **Answering a question.** After the system asks for a slot, it records that slot in `last_asked_slot`. The user's next reply is then written directly into that slot, bypassing the NLU slot output. Number words are normalised to digits (`"two"` becomes `"2"`). This was added because the slot tagger, with no knowledge of the question, tagged a bare `"2"` as `stars` instead of `book_people`.
- **Ending the conversation.** After `book_confirm`, the state is reset and the loop exits.

### 8. Database (`data/hotels.json`)

8 hand-written hotel records, for example Budget Inn, North Star Guesthouse and City Centre Lodge. Each record has `name`, `area`, `pricerange`, `stars`, `internet`, `parking` and `type`. These are not the MultiWOZ hotels.

---

## Evaluation

All evaluation is in `notebooks/04_evaluation.ipynb`.

### Intent classification

| Class | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| book_hotel | 0.78 | 0.86 | 0.82 | 860 |
| find_hotel | 0.94 | 0.90 | 0.92 | 2,085 |
| Accuracy | | | 0.89 | 2,945 |
| Macro avg | 0.86 | 0.88 | 0.87 | 2,945 |

Confusion matrix (rows are actual, columns are predicted):

| | find_hotel | book_hotel |
|---|---|---|
| **find_hotel** | 1,871 | 214 |
| **book_hotel** | 121 | 739 |

The labels are noisy. In multi-domain dialogues, the hotel frame's `active_intent` carries over across turns. That means some restaurant or taxi utterances end up labelled as hotel intents, for example "i need a place to dine in the center thats expensive" labelled `find_hotel`.

### Slot filling (seqeval, entity level)

| Slot | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| area | 0.58 | 1.00 | 0.74 | 237 |
| bookday | 0.86 | 1.00 | 0.92 | 157 |
| bookpeople | 0.74 | 0.96 | 0.83 | 317 |
| bookstay | 0.75 | 0.88 | 0.81 | 395 |
| internet | 0.16 | 0.79 | 0.27 | 38 |
| name | 0.09 | 0.60 | 0.16 | 203 |
| parking | 0.09 | 0.28 | 0.13 | 43 |
| pricerange | 0.82 | 1.00 | 0.90 | 255 |
| stars | 0.93 | 0.82 | 0.87 | 347 |
| type | 0.52 | 0.99 | 0.68 | 372 |
| **Micro avg** | 0.47 | 0.90 | 0.62 | 2,364 |
| **Macro avg** | 0.55 | 0.83 | 0.63 | 2,364 |

Observations:
- **Recall is high and precision is low across most slots.** The balanced class weights push the model away from `O`, so it over-predicts slot labels.
- **`name`, `parking` and `internet` are weakest.** Hotel names are open-ended strings. Parking and internet have very few training examples (43 and 38 in the test set). They are also often expressed indirectly ("free parking", "wifi"), so string matching may fail to label them in the first place.
- **The scores are optimistic, because of leakage.** The slot classifier was trained on a token-level random split of the BIO data, but evaluated on a sentence-level split of the same data. Most tokens in the "test" sentences were seen during training. Re-training on the sentence-level split is needed for a clean figure.

### Task completion

5 scripted conversations, written to match records in the database, were run through the full system. A conversation counts as complete if it reaches `book_confirm`.

**Result: 4/5 completed.**

The failure was "I need a cheap hotel in the east". The NLU filled `type=hotel` from the word "hotel". The only cheap hotel in the east is a guesthouse, so the query returned `no_match`.

This test set is small and was designed around the database. It is a smoke test, not a performance estimate.

### Human evaluation

A rubric has been defined but not yet applied to real users. It has 5 criteria, each scored 0–2, for a maximum of 10:
- Task completion
- Slot accuracy
- Response quality
- Error recovery
- Overall experience

---

## Known issues and limitations

**Policy and dialogue manager**
- **The intent classifier does not drive any decisions.** The policy uses only the slot state. Intent is predicted and logged, but ignored.
- **Any reply after `inform` confirms the booking** ("ok", "location?", anything). The system always books the first matching hotel, so the user cannot choose between several results.
- **Answers to questions are not validated.** The raw reply goes straight into the slot. For example, "thansk" was stored as `area`, and "bye" as `pricerange`.
- **Extra information in an answer is lost.** On turns where a question was just asked, the NLU slot output is ignored, so a reply like "2 people, actually in the south" will not update `area`.
- **Optional slots are never asked for.** `stars`, `internet`, `parking` and `type` only apply if the user volunteers them.

**NLU and DST**
- **Slot-name mismatch.** The tagger outputs MultiWOZ names (`bookday`, `bookpeople`, `bookstay`), but the state uses `book_day`, `book_people` and `book_nights`. `DialogueState.update()` silently drops unknown names. As a result, booking details given in free text are only captured when the system explicitly asks for them.
- **`type=hotel` is filled whenever the user says "hotel".** This excludes guesthouses even when the user meant "somewhere to stay".
- **No negation handling.** "not in the centre" can still fill `area=centre`.
- **Tokenisation is a plain whitespace split**, so punctuation stays attached to words ("north?" is a different token from "north").

**Data and engineering**
- The database is 8 fictional hotels, so many reasonable requests return no match.
- File paths are relative, so the system must be run from the project root.
- The debug trace is always on.
- There are no automated tests yet. The `tests/` folder is empty.

---

## Future work

- **Map slot names.** Map MultiWOZ slot names to the `domain.py` names in the NLU output, so volunteered booking details reach the state.
- **Validate slot values.** Check values against `domain.py` before updating the state, and re-ask on invalid input.
- **Use intent and affirmation in the policy.** Only confirm a booking on an explicit yes or `book_hotel`, and let the user pick from multiple results.
- **Add constraint relaxation.** Drop the least important constraint and re-query before returning `no_match`.
- **Use the real MultiWOZ hotel database.** Replace the hand-written JSON with the hotel database from the original MultiWOZ release.
- **Re-evaluate cleanly.** Re-train the slot tagger on a sentence-level split, and evaluate both models on the official MultiWOZ test split.
- **Try neural NLU.** Fine-tune BERT for intent classification and a transformer token classifier for slot filling, and compare against the TF-IDF baselines.
- **Run the human evaluation** with the rubric above.
- **Add unit tests** for the DST, policy and dialogue manager.

---

## Setup

Requires Python 3.10+ (developed on Python 3.14).

```bash
git clone https://github.com/hmzeda6210/hotel-dialogue-system.git
cd hotel-dialogue-system

python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

Main dependencies: `numpy`, `pandas`, `scikit-learn`, `datasets`, `seqeval`, `matplotlib`, `seaborn`, `jupyter`.

If `data/models/` is empty, run `notebooks/01_explore.ipynb` and then `notebooks/02_nlu.ipynb` to download the data and train the models.

## Running the system

From the project root:

```bash
python -m src.dialogue_manager
```

Type `quit` to exit. It must be run as a module (`-m`) from the root so that the `src.` imports and the `data/` paths resolve.

---

## Project structure

```
hotel-dialogue-system/
├── src/
│   ├── __init__.py
│   ├── domain.py              # slots, valid values, slot questions
│   ├── nlu.py                 # IntentClassifier, SlotFiller, NLU
│   ├── dst.py                 # DialogueState
│   ├── policy.py              # DialoguePolicy + query_database()
│   ├── nlg.py                 # template-based NLG
│   └── dialogue_manager.py    # pipeline orchestration + terminal loop
├── data/
│   ├── multiwoz/              # filtered hotel splits + BIO training data
│   ├── models/                # trained .pkl models and vectorisers
│   └── hotels.json            # 8-hotel database
├── notebooks/
│   ├── 01_explore.ipynb       # data loading, filtering, exploration
│   ├── 02_nlu.ipynb           # intent + slot model training
│   ├── 03_dst.ipynb           # DST experiments
│   └── 04_evaluation.ipynb    # metrics, confusion matrix, task completion
├── tests/
├── requirements.txt
└── README.md
```

---

## Tech stack

| Component | Tool |
|---|---|
| Intent classification | TF-IDF + Logistic Regression (scikit-learn) |
| Slot filling | Token-level TF-IDF + Logistic Regression over context-window features |
| State tracking | Custom Python class |
| Policy | Rule-based, frame-driven (GUS-style) |
| Database | JSON flat file |
| NLG | Template strings |
| Evaluation | scikit-learn metrics, seqeval, scripted task completion |
| Dataset | MultiWOZ 2.2 (hotel domain), via Hugging Face `datasets` |

---

## References

- Jurafsky, D. & Martin, J. H. *Speech and Language Processing* (3rd ed. draft), chapter on chatbots and dialogue systems. https://web.stanford.edu/~jurafsky/slp3/
- Bobrow, D. G. et al. (1977). GUS, a frame-driven dialog system. *Artificial Intelligence*, 8(2).
- Budzianowski, P. et al. (2018). MultiWOZ: A Large-Scale Multi-Domain Wizard-of-Oz Dataset for Task-Oriented Dialogue Modelling. *EMNLP*.
- Zang, X. et al. (2020). MultiWOZ 2.2: A Dialogue Dataset with Additional Annotation Corrections and State Tracking Baselines. *NLP4ConvAI Workshop*.

---

Author: Hamza ([@hmzeda6210](https://github.com/hmzeda6210))
