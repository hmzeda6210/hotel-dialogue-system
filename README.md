# Task-Oriented Dialogue System
### A fully modular, end-to-end restaurant and hotel booking dialogue agent — built from scratch.

This project implements a complete task-oriented dialogue system following the dialogue-state architecture. Every component of the pipeline was built independently, from raw text understanding to response generation, without relying on any pre-built dialogue framework.

---

## Evaluation Results

| Metric | Score |
|--------|-------|
| Intent Classification Accuracy | 89% |
| Intent Macro F1 | 0.87 |
| Slot Filling Micro F1 | 0.62 |
| Slot Filling Macro F1 | 0.63 |
| Task Completion Rate | 80% |

> Evaluated on the [MultiWOZ v2.2](https://huggingface.co/datasets/tuetschek/multi_woz_v22) dataset — one of the largest and most challenging multi-domain task-oriented dialogue benchmarks, covering hotel, restaurant, taxi, train, and attraction domains.

---

## What This Is

A task-oriented dialogue system is built to help users complete a specific goal — like booking a restaurant or finding a hotel — through natural conversation. Unlike a general chatbot, every component of the system has a precise job: understand what the user wants, remember it across turns, decide what to ask next, and respond naturally.

This system covers the full pipeline:

- **NLU** — understands what the user said (intent + slot extraction)
- **DST** — remembers everything across the conversation
- **Policy** — decides what the system should do next
- **NLG** — turns that decision into a natural response
- **Database** — queries a knowledge base to find matching results
- **DialogueManager** — orchestrates all of the above on every turn

---

## Architecture

```
User utterance
      |
      v
+-------------+
|     NLU     |  BERT intent classifier + BIO slot tagger
+-------------+
      |  intent + slots
      v
+-------------+
|     DST     |  Updates and maintains the belief state frame
+-------------+
      |  current state
      v
+-------------+
|   Policy    |  GUS-style rule-based decision making
+-------------+
      |  dialogue act
      v
+-------------+
|     NLG     |  Template-based response generation
+-------------+
      |
      v
 System response
```

Each component is a separate Python module. They communicate through clean, structured interfaces — no raw text passes between components after the NLU stage.

---

## Example Conversations

**Happy path — all slots filled in one turn:**
```
You:    I'm looking for a cheap Italian restaurant in the north.
System: I found 2 restaurants matching your criteria:
        - Frankie & Benny's (Italian, cheap, north)
        - Pizza Express (Italian, cheap, north)
        Would you like more details about either of these?

You:    Yes, tell me about the first one.
System: Frankie & Benny's is located in the north of the city.
        It serves Italian food at a cheap price range.
        Is there anything else you'd like to know?
```

**Multi-turn slot filling:**
```
You:    I need a hotel.
System: What area would you like the hotel to be in?

You:    Somewhere in the centre.
System: What is your price range — cheap, moderate, or expensive?

You:    Moderate is fine.
System: How many stars would you like?

You:    3 stars please.
System: I found 1 hotel matching your request:
        - The Citadel (centre, moderate, 3 stars)
```

**No results found:**
```
You:    I want a cheap 5-star hotel in the centre.
System: I'm sorry, I couldn't find any hotels matching those criteria.
        Would you like me to try relaxing some of the requirements?
```

---

## Installation

```bash
git clone https://github.com/hmzeda6210/task-oriented-dialogue-system
cd task-oriented-dialogue-system
pip install -r requirements.txt
```

Requirements: Python 3.10+, PyTorch, HuggingFace Transformers, spaCy, scikit-learn, seqeval

---

## Run a Conversation

```bash
python src/dialogue_manager.py
```

To run with full debug trace (shows internal state at every layer):

```bash
python src/dialogue_manager.py --debug
```

---

## Project Structure

```
task-oriented-dialogue-system/
|
|-- README.md
|-- requirements.txt
|
|-- src/
|   |-- domain.py              # ontology: slots, valid values, questions
|   |-- nlu.py                 # intent classifier + BIO slot tagger
|   |-- dst.py                 # dialogue state tracker
|   |-- policy.py              # GUS-style dialogue policy
|   |-- nlg.py                 # template-based response generation
|   |-- database.py            # MultiWOZ knowledge base queries
|   `-- dialogue_manager.py    # end-to-end orchestrator
|
|-- models/
|   `-- intent_classifier/     # saved BERT fine-tune weights
|
|-- data/
|   |-- raw/                   # original MultiWOZ v2.2 files
|   `-- processed/             # preprocessed training data
|
|-- notebooks/
|   |-- 01_data_exploration.ipynb
|   |-- 02_nlu_training.ipynb
|   `-- 03_evaluation.ipynb
|
|-- evaluation/
|   |-- test_dialogues.json    # 30 scripted test conversations
|   |-- results.json           # full evaluation metrics
|   `-- human_eval.csv         # human evaluation scores
|
`-- docs/
    `-- report.pdf             # full project write-up
```

---

## Error Analysis

Understanding where the system fails is as important as knowing where it succeeds.

**Hotel name extraction is weak (F1 = 0.16)**
The slot tagger struggles with multi-word hotel names like "The Gonville Hotel" or "Cityroomz". These are rare, highly specific entities that appear infrequently in training data. The BIO tagger correctly identifies the B token but mispredicts O instead of I for continuation tokens — resulting in partial or missed extractions. Fix: oversample multi-word entity examples and apply data augmentation during training.

**Limited database coverage causes no-match failures**
The MultiWOZ database has finite entries. When users specify constraints that do not match any record exactly — such as a cheap 5-star hotel — the system fails rather than relaxing constraints gracefully. Fix: implement constraint relaxation in the policy, dropping the least critical slot and retrying before returning a failure response.

**Mid-conversation corrections are not handled reliably**
When a user corrects a previously filled slot ("actually make it French, not Italian"), the system occasionally fails to overwrite the old value. The correction is extracted correctly by the NLU but not always persisted by the DST. Fix: strengthen the DST update method to explicitly handle overwrite cases and add test coverage for correction turns.

---

## Limitations

This project has known boundaries worth being transparent about:

- Domain coverage is primarily tuned for hotel and restaurant booking within MultiWOZ
- System initiative only — the system leads the conversation and mixed initiative is not supported
- Negation is not handled — "I don't want Italian food" may incorrectly fill food = italian
- Template NLG produces repetitive responses over long conversations
- Text input only — no speech or ASR integration

---

## Future Work

**Fix multi-word slot extraction (highest priority)**
Oversampling and data augmentation targeting compound entity names would directly address the biggest gap in the current system. Hotel name extraction at F1 = 0.16 is the single metric with the most room for improvement.

**Neural NLG upgrade**
Replacing template-based generation with a fine-tuned T5 model trained on (dialogue act, response) pairs from MultiWOZ would produce more natural, varied responses and eliminate template repetitiveness over long conversations.

**Constraint relaxation in policy**
Adding a relaxation step before returning a failure response — dropping the least critical slot and retrying the database query — would recover many conversations currently ending in no-match failures.

---

## Tech Stack

| Component | Tool |
|-----------|------|
| Intent Classification | BERT fine-tune (HuggingFace Transformers) |
| Slot Filling | BIO token classifier (HuggingFace) |
| Baseline NLU | TF-IDF + Logistic Regression (scikit-learn) |
| State Tracking | Custom Python dataclass |
| Database | SQLite / JSON (MultiWOZ KB) |
| NLG | Template-based generation |
| Evaluation | seqeval, sklearn, manual rubric |
| Dataset | MultiWOZ v2.2 |

---

## References

- Jurafsky & Martin — [Speech and Language Processing, Chapter 15](https://web.stanford.edu/~jurafsky/slp3/)
- MultiWOZ v2.2 — [tuetschek/multi_woz_v22](https://huggingface.co/datasets/tuetschek/multi_woz_v22)
- Bobrow et al. (1977) — GUS, a frame-driven dialog system
- Louvan & Magnini (2020) — Recent Neural Methods on Slot Filling and Intent Classification

---

