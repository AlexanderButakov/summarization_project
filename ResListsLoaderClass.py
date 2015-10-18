# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import codecs, json


# stopwords - содержит список стоп-слов.
# titled_stopwords - содержит список стоп-слов с повышенной первой бувой (необходим для разбиения на предлоежния)
# abbreviations - соержит список аббревиатур с точкой, после которых не разбивать на предлоежния.


class LoadExternalLists(object):
    
    """
    Загружаем в память файл стоп-слов (+ с ББ), файл с неправ. формами глаголов 
    и файл с неправ. формами множ. числа сущ-х., файл сокращений для сплиттера,
    лексикон для немецкого и корпуса для tfidf.
    """

    def __init__(self):

        self.stopwords_common = set()
        self.stopwords_en = set()
        self.stopwords_ru = set()
        self.stopwords_de = set()

        self.titled_stopwords = set()
        self.abbreviations = set()

        self.ger_nn = set()
        self.ger_ne = set()

        self.verbtransforms = {}
        self.nountransforms = {}

        self.lexicon_de = {}

        self.corpus_EN = {}
        self.corpus_RU = {}
        self.corpus_DE = {}

        
    def loadCommonStopWords(self):
        # print "Loading stopwords"
        with codecs.open(r".\txt_resources\stopwords_common.txt",'r','utf-16') as file_openstopw:
            self.stopwords_common = set(file_openstopw.read().split('\r\n'))

        return self.stopwords_common


    def loadStopWordsEN(self):
        print "Loading stopwordsEN"
        with codecs.open(r".\txt_resources\stopwords_en.txt",'r','utf-16') as file_openstopw:
            self.stopwords_en = set(file_openstopw.read().split('\r\n'))

        return self.stopwords_en


    def loadStopWordsRU(self):
        print "Loading stopwordsRU"
        with codecs.open(r".\txt_resources\stopwords_ru.txt",'r','utf-16') as file_openstopw:
            self.stopwords_ru = set(file_openstopw.read().split('\r\n'))

        return self.stopwords_ru


    def loadStopWordsDE(self):
        print "Loading stopwordsDE"
        with codecs.open(r".\txt_resources\stopwords_de.txt",'r','utf-16') as file_openstopw:
            self.stopwords_de = set(file_openstopw.read().split('\r\n'))

        return self.stopwords_de


    def loadTitledStopwords(self):
        print 'Making titled stopwords'        
        self.titled_stopwords = tuple([word.title() for word in self.loadCommonStopWords()])

        return self.titled_stopwords


    def loadAbbreviations(self):
        print 'Loading abbreviations'
        with codecs.open(r'.\txt_resources\abbrevs_common.txt','r', 'utf-16') as file_openabbrev:
            self.abbreviations = set(file_openabbrev.read().split('\r\n'))

        return self.abbreviations


    def loadVerbForms(self):
        print 'Loading Verbs'
        with codecs.open(r'.\txt_resources\verbforms_en.txt','r','utf-16') as verbforms:
            for line in verbforms:
                line_part = line.strip().split('\t')
                if line_part[0] not in self.verbtransforms:
                    self.verbtransforms[line_part[0]] = line_part[1]

        return self.verbtransforms


    def loadNounforms(self):
        print 'Loading Nouns'
        with codecs.open(r'.\txt_resources\nounforms_en.txt','r','utf-16') as nounforms:
            for line in nounforms:
                line_part = line.strip().split('\t')
                if line_part[0] not in self.nountransforms:
                    self.nountransforms[line_part[0]] = line_part[1]

        return self.nountransforms


    def loadLexiconDE(self):

        with open(r'.\lexicon\lexicon_de_49289.json', 'r') as infile:

            self.lexicon_de = json.load(infile)

        return self.lexicon_de


    def loadCorpusEN(self):
        print 'Loading EN Corpus'
        with open(r".\corpus\ENCorpusDict_13963.json", 'r') as infile:
            self.corpus_EN = json.load(infile)

        return self.corpus_EN


    def loadCorpusRU(self):
        print 'Loading RU Corpus'
        with open(r".\corpus\RUCorpusDict_158099.json", 'r') as infile:
            self.corpus_RU = json.load(infile)

        return self.corpus_RU


    def loadCorpusDE(self):
        print 'Loading DE Corpus'
        with open(r".\corpus\DECorpusDict_106363.json", 'r') as infile:
            self.corpus_DE = json.load(infile)

        return self.corpus_DE

    def loadGermanNN(self):
        print 'Loading German NN'
        with codecs.open(r".\txt_resources\cat_NN.txt", 'r', 'utf-16') as infile:
            self.ger_nn = set(infile.read().split('\n'))

        return self.ger_nn

    def loadGermanNE(self):
        print 'Loading German NE'
        with codecs.open(r".\txt_resources\cat_NE.txt", 'r', 'utf-16') as infile:
            self.ger_ne = set(infile.read().split('\n'))

        return self.ger_ne
        