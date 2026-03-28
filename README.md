# Information Retrieval - Boolean Retrival Model - Retrive Trump Speeches

This project implements a simple IR system over the speech files inside the Speeches folder.

It supports:
- Inverted index and positional index creation
- Boolean queries: AND, OR, NOT
- Proximity queries such as trump biden /3
- Implicit phrase-style proximity: two adjacent terms are treated like /0
- A command-line search mode in Main.py
- A web UI in frontend.py using Gradio


## Project Structure

- Main.py: Builds/loads indexes and evaluates queries
- frontend.py: Gradio interface that calls search_speeches from Main.py
- Speeches/: Speech documents (speech_0.txt, speech_1.txt, ...)
- stopwords.txt: Stopword list used during indexing
- PositionalIndex.txt: Saved positional index (auto-generated if missing)
- InvertedIndex.txt: Saved inverted index (auto-generated if missing)
- queries.txt: Optional test queries/expected outputs
- requirments.txt: Python dependencies


## Prerequisites

- Python 3.10+ recommended
- Internet access on first run (Main.py downloads NLTK punkt_tab)


## Installation

From the project root folder:

1. Create and activate a virtual environment (optional but recommended):

	 Windows PowerShell:
	 .venv-1\Scripts\Activate.ps1

2. Install dependencies:

	 pip install -r requirments.txt


## How Main.py Works

When Main.py starts:

1. It checks if PositionalIndex.txt and InvertedIndex.txt already exist.
2. If both exist, it loads them directly.
3. Otherwise, it reads all files in Speeches/, preprocesses and tokenizes text, stems terms, removes stopwords, then builds both indexes and saves them.

Processing details:
- Text normalization and cleanup use textacy + regex
- Tokenization uses NLTK word_tokenize
- Stemming uses NLTK SnowballStemmer (English)
- Document IDs are taken from file names (speech_12.txt -> doc id 12)


## Run Main.py (CLI)

Command:

python Main.py

Then type a query at the prompt.

To quit:

exit


## Supported Query Syntax

Boolean operators:
- term1 AND term2
- term1 OR term2
- NOT term
- Parentheses are supported, for example: (economy OR jobs) AND tax

Proximity queries:
- term1 term2 /k
- Example: border security /3
- Meaning: term1 and term2 appear within k words (according to the implementation in Main.py)

Implicit adjacency:
- Two adjacent terms without an operator are treated as a proximity query with /0
- Example: hillary clinton behaves like hillary clinton /0

Implicit AND insertion:
- If two operands are adjacent in parsing context, AND is inserted automatically


## Run frontend.py (Gradio UI)

Command:

python frontend.py

Behavior:
- Starts a local Gradio app
- Opens your browser automatically (demo.launch(inbrowser=True))
- Search box sends query to Main.search_speeches
- Results are shown as expandable cards containing speech text

Notes:
- frontend.py expects speeches under Speeches/
- You can change SPEECHES_FOLDER in frontend.py if needed


## Example Queries

- immigration
- economy AND jobs
- (china OR trade) AND tariff
- NOT taxes
- make america /2
- hillary clinton


## Troubleshooting

- If dependency errors occur:
	- Make sure your virtual environment is activated
	- Reinstall with pip install -r requirments.txt

- If NLTK tokenizer errors occur:
	- Run Main.py once with internet access so punkt_tab can be downloaded

- If no results appear in frontend:
	- Verify Speeches/ exists and contains speech_*.txt files
	- Check query spelling and try simpler terms


## Optional Test Mode in Main.py

Main.py contains a commented test runner for queries.txt.

If you want to use it:
1. Uncomment the test runner block near the end of Main.py.
2. Run python Main.py.

