from pathlib import Path
import re
import nltk
import textacy.preprocessing as pp
from nltk.tokenize import word_tokenize
from nltk.stem import SnowballStemmer
import ast


"""I have purposelt tried to elobarately comment the code by myself (and a little help from editor AI)
   code isnt copied from LLM's"""


nltk.download("punkt_tab")

stemmer = SnowballStemmer("english")

def PreProcessing(content):
    content = pp.normalize.unicode(content) # makes the text encoding normalized
    content = pp.remove.brackets(content)   # removes any brackets and their content from the text
    content = pp.normalize.hyphenated_words(content)    # normalizes hyphenated words by removing the hyphen (e.g., "well-known" becomes "wellknown")
    content = pp.normalize.whitespace(content)  # replaces multiple consecutive whitespace characters with a single space

    content = re.sub(r"[^\w\s]", " ", content)  # removes any punctuation by replacing non-word and non-space characters with a space

    return content


directory_path = Path("Speeches")

directory = {}
InvertedIndex = {}
PositionalIndex = {}
all_docs = set()

positional_file = Path("PositionalIndex.txt")
inverted_file = Path("InvertedIndex.txt")

"""Here we make the positional and inverted index. If the files already exist, we load them into memory.
    If they dont exist, we build the indexes from the documents and save them to files"""


# Check if the files exist. if they do then load them.
if positional_file.exists() and inverted_file.exists():
    PositionalIndex = {}
    InvertedIndex = {}

    # PositionalIndex
    with open(positional_file, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if not line.strip():
                continue
            term, docs = line.split(":", 1)
            PositionalIndex[term.strip()] = ast.literal_eval(docs.strip())

    # InvertedIndex
    with open(inverted_file, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if not line.strip():
                continue
            term, docs = line.split(":", 1)
            InvertedIndex[term.strip()] = set(ast.literal_eval(docs.strip()))

    print("Loaded PositionalIndex and InvertedIndex")

# Files dont exist, Build the indexes
else:
    with open("stopwords.txt", "r", encoding="utf-8", errors="replace") as stopwords_file:
        stopwords = {
            stemmer.stem(word.strip().lower())
            for word in stopwords_file
            if word.strip()
        }

    pos_output = open("PositionalIndex.txt", "w", encoding='utf-8', errors='replace')
    inv_output = open("InvertedIndex.txt", "w", encoding='utf-8', errors='replace')

    for file_path in sorted(directory_path.iterdir(), key=lambda p: p.name):
        speech_id = int(file_path.stem.split('_')[1])
        
        with file_path.open(mode='r', encoding='utf-8', errors='replace') as f:
            all_docs.add(speech_id)
            content = f.read()
            
            # do preprocessing on the file content
            content = PreProcessing(content)
            directory[speech_id] = content

            # Break sentences into tokens
            tokens = word_tokenize(content.lower())
            
            j = 0
            for token in tokens:
                
                #check if token is alphanumeric to remove any leftover punchuation or special characters
                if not token.isalnum():
                    j += 1
                    continue
                
                # use stemmization to reduce the token to its root form using ntlk library stemmer
                stemmed = stemmer.stem(token)

                if stemmed in stopwords:
                    j += 1
                    continue
                
                # make the actual inverted and positional index
                if stemmed not in InvertedIndex:
                    InvertedIndex[stemmed] = set([speech_id])
                    PositionalIndex[stemmed] = {speech_id: [j]}
                else:
                    InvertedIndex[stemmed].add(speech_id)

                    if speech_id not in PositionalIndex[stemmed]:
                        PositionalIndex[stemmed][speech_id] = []

                    PositionalIndex[stemmed][speech_id].append(j)

                j += 1

    # Save PositionalIndex
    for term, docs in PositionalIndex.items():
        print(f"{term}: {docs}", file=pos_output)

    # Save InvertedIndex
    for term, docs in InvertedIndex.items():
        print(f"{term}: {list(docs)}", file=inv_output)

    pos_output.close()
    inv_output.close()

    print("Built and saved PositionalIndex and InvertedIndex")


def normalize_query_term(term: str):
    term = PreProcessing(term)
    tokens = word_tokenize(term.lower())
    tokens = [stemmer.stem(t) for t in tokens if t.isalnum()]
    return tokens[0] if tokens else None

# We didnt merge the above and below functions as for proximity queries are using Proximity_query function 
# which will need normalized queries seperately, if we used merged function,
# then we would have to do the normalization inside the Proximity_query function as well

def get_ii_docs_for_term(raw_term: str):    #Normalize and look up a term in the inverted index.
    norm=raw_term.split("_")[0]
    norm = normalize_query_term(norm)
    if not norm:
        return set()
    return InvertedIndex.get(norm, set())


def positional_query(l1, l2, k):
    
    # If any term is not in Positional index then we dont need to check other
    if l1 not in PositionalIndex or l2 not in PositionalIndex:
        return set()

    result = set()
    common_docs = set(PositionalIndex[l1].keys()) & set(PositionalIndex[l2].keys())

    # For every document that contains both terms,
    # we check if they are within k words of each other.
    for doc_id in common_docs:
        positions1 = sorted(PositionalIndex[l1][doc_id])
        positions2 = sorted(PositionalIndex[l2][doc_id])

        i, j = 0, 0
        
        while i < len(positions1) and j < len(positions2):
            if abs(positions1[i] - positions2[j]) == k+1: 
                result.add(doc_id)
                break
            elif positions1[i] < positions2[j]:
                i += 1
            else:
                j += 1

    return result


given_operators = {'AND', 'OR', 'NOT'}
OP_precidence     = {'NOT': 3, 'AND': 2, 'OR': 1}

def tokenize(query):
    tokens = re.compile(r'\(|\)|AND|OR|NOT|/\d+|[^\s()]+', re.IGNORECASE).findall(query)
    return [t.upper() if t.upper() in given_operators else t for t in tokens]

#Function to check if a token is a proximity operator (e.g., /3)
def is_prox_op(t): return isinstance(t, str) and bool(re.fullmatch(r'/\d+', t))
#Function to check if a token is a term (not an operator, parenthesis, or proximity operator)
def is_term(t):    return isinstance(t, str) and t not in given_operators and t not in ('(', ')') and not is_prox_op(t)


def parse_and_execute(query):
    raw = tokenize(query)

    """We are differentiatng Boolean queries and proximity queries
    Proximity queries are itself of 2 types, one which has /k mentioned explicitly,
    and the other which is implicit (e.g. "Hillary Clinton" is treated as "Hillary Clinton /0")"""
    

    """Here we are scanning the token list once and looking for patterns that match proximity queries."""
    def make_prox(a, b, k=0):
        return ('PROX', a, b, k)
    
    tokens = []
    i = 0
    while i < len(raw):
        t = raw[i]

        # if statements checks if the query contains a proximity operator (e.g., /3) between two terms.
        # If it does, it collapses the three tokens (term, term, /N) into a single tuple ('PROX', term1, term2, N)
        # and appends it to the collapsed list.
        if (i + 2 < len(raw)
                and is_term(raw[i])
                and is_term(raw[i + 1])
                and is_prox_op(raw[i + 2])):
            tokens.append(make_prox(raw[i], raw[i + 1], int(raw[i + 2][1:])))
            i += 3
            continue

        # if the query dosent contain a proximity operator but has two adjacent terms (e.g Hillary Clinton), then
        # it adds a /0 ahead of it so that it later is treated as a proximity query with k=0,
        # meaning the two terms must be adjacent in the document to match.
        if (i + 1 < len(raw)
                and is_term(raw[i])
                and is_term(raw[i + 1])):
            tokens.append(make_prox(raw[i], raw[i + 1], 0))
            i += 2
            continue

        tokens.append(t)
        i += 1


    # If it finds an operand followed by another operand that is not a plain term, it inserts an 'AND' operator between them.
    # This ensures that queries like "Hillary Clinton" are treated as "Hillary Clinton /0" 
    # and queries like "Hillary (Clinton)" are treated as "Hillary AND Clinton".
    def is_operand(x):
        return isinstance(x, tuple) or is_term(x) or x == ')'

    def starts_operand(x):
        return isinstance(x, tuple) or is_term(x) or x == '('

    final = []
    for i, t in enumerate(tokens):
        final.append(t)
        if i + 1 < len(tokens) and is_operand(t) and starts_operand(tokens[i + 1]):
            final.append('AND')


    """From here we are starting to actually parse the query and
    execute it using a stack-based approach similar to the Shunting Yard algorithm."""

    output = [] # final set of documetns
    ops = [] # operator stack

    
    def apply_op(op):   #Function to apply an operator (AND, OR, NOT) to the top elements of the output stack.
        if op == 'NOT':
            output.append(all_docs - output.pop())
        else:
            b, a = output.pop(), output.pop()
            output.append(a & b if op == 'AND' else a | b)

    def flush(stop=None):   #Function to flush operators from the ops stack to the output stack until a certain stop operator is reached.
        while ops and ops[-1] != '(':
            top = ops[-1]
            if stop and not (OP_precidence[top] > OP_precidence[stop] or (OP_precidence[top] == OP_precidence[stop] and stop != 'NOT')):
                break
            apply_op(ops.pop())

    # The loop iterates through the final tokens and processes them based on their type
    for t in final:
        
        #First we are checking if the token is a proximity query.
        # If it is,then call the positional_query function to get the set of documents that match the proximity condition.
        # Proximity queries we put in a tuple above so we just have to check if the token is a tuple,
        # and if it is, we know its a proximity query
        if isinstance(t, tuple):
            _, l, r, k = t
            l = normalize_query_term(l)
            r = normalize_query_term(r)
            output.append(positional_query(l, r, k) if l and r else set())

        # now we parse any other boolean combination using a stack.
        elif t == '(':
            ops.append(t)

        elif t == ')':
            flush()
            if not ops:
                raise ValueError("Mismatched parentheses")
            ops.pop()

        elif t in given_operators:
            flush(stop=t)
            ops.append(t)

        elif is_term(t):
            # we are getting the documents matching the term and appending them to the output.
            output.append(get_ii_docs_for_term(t))

        else:
            raise ValueError(f"Unexpected token: {t}")

    flush()

    return output[0]




#               OUTPUTS


"""  Interactive loop"""

if __name__ == "__main__":
    while True:
        query = input("\nEnter query: ").strip()
        if query.lower() == 'exit':
            break
        if not query:
            continue
        try:
            results = parse_and_execute(query)
            print(f"\nQuery : {query}")
            if results:
                print(f"Matched {len(results)} document(s): {sorted(results)}")
            else:
                print("No documents matched.")
        except ValueError as e:
            print(f"Error: {e}")



"""Script to run tests from query.txt"""

# def run_tests_from_file(file_path):
#     with open(file_path, 'r', encoding='utf-8') as f:
#         lines = [line.strip() for line in f if line.strip() != ""]

#     i = 0
#     test_num = 1

#     while i < len(lines):
#         query = lines[i]
#         expected_str = lines[i + 1]

#         expected_result = {int(x) for x in ast.literal_eval(expected_str)}

#         actual_result = parse_and_execute(query)

#         if set(actual_result) == expected_result:
#             print(f"[PASS] Test {test_num}: {query}")
#             print(f"  Got     : {sorted(set(actual_result))}\n")
#         else:
#             print(f"[FAIL] Test {test_num}: {query}")
#             print(f"  Expected: {sorted(expected_result)}")
#             print(f"  Got     : {sorted(set(actual_result))}")
#             print(f"  Extra   : {sorted(set(actual_result) - expected_result)}\n")

#         i += 2
#         test_num += 1

# if __name__ == "__main__":
#     run_tests_from_file("queries.txt")



"""Function for frontend"""
def search_speeches(query, speeches_folder):
    doc_ids = parse_and_execute(query)

    speeches = {}

    for doc_id in doc_ids:
        file_path = Path(speeches_folder) / f"speech_{doc_id}.txt"

        try:
            speeches[doc_id] = file_path.read_text(encoding='utf-8')
        except FileNotFoundError:
            print(f"[WARNING] File not found for doc_id {doc_id}: {file_path}")
        except Exception as e:
            print(f"[ERROR] Could not read file for doc_id {doc_id}: {e}")

    return speeches