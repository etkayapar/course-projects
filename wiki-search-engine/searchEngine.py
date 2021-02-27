#! /usr/bin/env python3

### Wrote the program using f strings, so appropriate python3 version
### might be necessary



from sys import exit
import re
import os
import time
import sys
import readline

readline.parse_and_bind("tab: complete")

doc_id_pat = r"doc id\=\"(\w+)\""
title_pat  = r"title\=\"(.+)\""
url_pat    = r"url\=\"(.+)\" "

nonAlphN_pat = r"[^\w\s]"


words = {}

docs = {} #document info dictionary
          # {doc_id: [title, wordCount]}

loadedFiles = {}#loaded files and modif. dates


messages = {'greet': '''
Welcome to my search engine.

Usage:

    load <filename.txt>     load a document dump to corpus, with TAB completion
                            for filenames

    search <keywords>       will perform the search on entire corpus

    exit                    exit the program
''',
'fileLoaded':  '''
File you entered is already loaded in program corpus in current session.
It has not been changed since last loading. Skipping file.
''',
'searchFail': "Search word not found. Please try again.",
'commandNotFound': 'not recognized as a command.'
           }

def documentParser(fName):

    '''
    this function appends to the global
    variables regarding words and documents
    '''

    try:
        test = open(fName)
    except FileNotFoundError:
        print('No such file. Please try again.')
        return

    wordCount = 0
    mt = os.path.getmtime(fName)
    s = time.time()
    for l in test:
        l = l.strip()
        if l.startswith('<doc id'):
            doc_id = int(re.findall(doc_id_pat, l)[0])
            title  = re.findall(title_pat, l)[0]
            url    = re.findall(url_pat, l)[0]
            wordCount = 0
            docs[doc_id] = [title, wordCount, url]
            continue
        elif l.startswith('</doc'):
            docs[doc_id][1] = wordCount
            continue
        else:
            chunked = re.sub(nonAlphN_pat, "", l).lower().encode('utf-8').split()
            for word in chunked:
                wordCount += 1
                if word in words:
                    if doc_id in words[word]:
                        words[word][doc_id] += 1
                    else:
                        words[word][doc_id] = 1
                else:
                    words[word] = {}
                    words[word][doc_id] = 1
    e = time.time()
    elapsed = round(e-s, 2)
    perDoc = round(elapsed / len(docs) * 1000, 2)
    retval = f"loaded {len(docs)} documents in {elapsed} seconds ({perDoc} ms"
    retval += " per document)."
    print(retval)
    loadedFiles[fName] = mt


def wordStats(w, wDic, dDic):

    '''
    Calculates the tf-idf fow a given word and returns a sorted list based on
    tf-idf, suggesting a relevance sorted search result.
    '''

    from math import log, log2
    w = wDic[w]
    res = []

    for doc in w:
        res.append([doc,
                   w[doc]/dDic[doc][1] * log2(len(dDic) / len(w))])

    if len(res) < 0:
        raise KeyError

    res.sort(key = lambda x: x[1], reverse=True)
    res = [x[0] for x in res]
    return res


def wordStats_l(w, wordDic, docDic):

    '''
    works on list of words as a query. Treates the whole query as a single word
    then calculates the tf-idf, since it only return for the documents that
    contain all of the search words.
    '''

    from math import log, log2
    commonDocs = wordDic[w[0]].keys() &  wordDic[w[1]].keys()
    if len(w) > 2:
        for i in range(2,len(w)):
            commonDocs = commonDocs & wordDic[w[i]].keys()
    total = 0
    res = []

    for doc in commonDocs:
        total = 0
        for i in w:
            #print(str(i) + "   " + str(doc))
            total += wordDic[i][doc]
        tf = total / docDic[doc][1]
        idf = log2(len(docDic) / len(commonDocs))
        res.append([doc, tf * idf])

    if len(res) < 0:
        raise KeyError

    res.sort(key = lambda x: x[1], reverse=True)
    res = [x[0] for x in res]
    return res

def queryFromList(query):

    '''
    Handles the query that is passed to it from the UI function, and calls
    appropriate functions depending on the type of the query.
    '''

    s = time.time()
    #query = list(query)
    if len(query) == 1:
        queryb  = query[0].lower().encode('utf-8')
        results = wordStats(queryb, words, docs)
    else:
        queryb = [x.lower().encode('utf-8') for x in query]
        results = wordStats_l(queryb, words, docs)
    e = time.time()
    elapsed = round((e-s) * 1000, 2)
    query = " ".join(query)
    print(f"search completed in {elapsed} miliseconds.")

    sep = "=" * 20
    print(f"\n{sep} Results for \"{query}\" {sep}\n")
    for i,res in enumerate(results,1):
        if i % 50 == 0:
            input('\rpress ENTER to see the rest of results')
            print("\033[F                                         ",end='\r')
        print(f"{docs[res][0]}\t->\t{docs[res][2]}")
    print(f"\n{sep} End of results {sep}\n")

    #return results


def fileHandler(fName):

    '''
    Handles the load file request, preventing loading the same document dump
    file twice to the corpus, if the file has not been changed since last load
    during the same session of this program.
    '''

    is_loaded = fName in loadedFiles
    if is_loaded:
        current_mt = os.path.getmtime(fName)
        loaded_mt  = loadedFiles[fName]
        if current_mt == loaded_mt:
            print(messages['fileLoaded'])
        else:
            documentParser(fName)
    else:
        documentParser(fName)

def commandHandler(args):
    if args[0] == 'search':
        try:
            queryFromList(args[1:])
        except KeyError:
            print(messages['searchFail'])

    elif args[0] == 'load':
        fileHandler(args[1])

    elif args[0] == 'exit':
        exit()

    else:
        print(f"{args[0]} " + messages['commandNotFound'])

# def cli_ui():
#     print(messages['greet'])
#     commands = {'load': lambda x: fileHandler(x),
#                 'search': lambda x: queryFromList(x)}
#     while True:
#         req = input('command> ').split()
#         if req == []:
#             continue
#         if req[0] == 'exit':
#             break
#         try:
#             commands[req[0]](req[1])
#         except KeyError:
#             if req[0] == 'search':
#                 print(messages['searchFail'])
#             if req[0] not in commands:
#                 print(f"{req[0]} not recognized as a command.")
#             continue
#     return None


def cli_ui():

    '''
    User interface of the program
    '''

    print(messages['greet'])
    while True:
        req = input('command> ').split()
        if req == []:
            continue
        else:
            commandHandler(req)
    return None

cli_ui()
