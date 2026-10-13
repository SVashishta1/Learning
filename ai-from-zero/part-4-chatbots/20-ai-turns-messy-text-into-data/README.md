# 20 · AI turns messy text into data

**What it does:** reads 3 messy receipts (one in Italian, one an informal note, one an email) and fills in the **same tidy form** for each, then saves a spreadsheet (`receipts.csv`).

## Run it
```bash
cd part-4-chatbots/20-ai-turns-messy-text-into-data
python extract.py
```

## The idea in one sentence
You describe the form you want (`class Receipt`), and the AI is **forced to answer in exactly that shape**, so your code gets clean data instead of a chatty paragraph. This is one of the most common paid uses of AI in businesses.

## Try this
1. Add a field `category: str` (food, home, services...) to `Receipt` and run it again.
2. Paste in a real email or receipt of your own.
3. Make a `JobPost` form (title, company, salary, skills) and feed it job adverts.
