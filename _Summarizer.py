# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from ResListsLoaderClass import LoadExternalLists
from TextSegmentorClass import TextSegmentor
from SentenceSplitterClass import SentenceSplitter
from SymmetricalSummarizingClass import *
import codecs, itertools, subprocess, json



class SUMMARIZER(object):

    def __init__(self, language):
        
        self.language = language

        print "Loading external word lists..."
        print
        self.external_lst = LoadExternalLists()
        self.titled_stopwords = self.external_lst.loadTitledStopwords()
        self.ABBREVIATIONS = self.external_lst.loadAbbreviations()

        if self.language == 'en':
            self.stopwords = self.external_lst.loadStopWordsEN()
            self.VERBTRANSFORMS = self.external_lst.loadVerbForms()
            self.NOUNTRANSFORMS = self.external_lst.loadNounforms()
            self.terms_dict = self.external_lst.loadCorpusEN()
            self.lexicon_de = ''
            self.ger_nn = ''
            self.ger_ne = ''
        
        if self.language == 'ru':
            self.stopwords = self.external_lst.loadStopWordsRU()
            self.terms_dict = self.external_lst.loadCorpusRU()
            self.VERBTRANSFORMS = ''
            self.NOUNTRANSFORMS = ''
            self.lexicon_de = ''
            self.ger_nn = ''
            self.ger_ne = ''
        
        if self.language == 'de':
            self.lexicon_de = self.external_lst.loadLexiconDE()
            self.stopwords = self.external_lst.loadStopWordsDE()
            self.ger_nn = self.external_lst.loadGermanNN()
            self.ger_ne = self.external_lst.loadGermanNE()
            self.terms_dict = self.external_lst.loadCorpusDE()
            self.VERBTRANSFORMS = ''
            self.NOUNTRANSFORMS = ''

        # стеммируются предложения
        self.stem_sents = SentenceSplitter(self.stopwords, self.VERBTRANSFORMS, self.NOUNTRANSFORMS, self.lexicon_de, self.language)


    def summarize(self, text):

        # статья для обработки
        OPENTEXT = text

        # разбиваем в LIST_OF_SENTENCES входной текст
        textsegmentor = TextSegmentor(self.titled_stopwords, self.ABBREVIATIONS, self.language)
        LIST_OF_SENTENCES, TTL = textsegmentor.segment(OPENTEXT)
        
        # склеиваем все списки в один простой список ALLSENTENCES для статистики по предложениям
        ALLSENTENCES = list(itertools.chain.from_iterable(LIST_OF_SENTENCES))

        # для методики симметричного реф-я нужно не менее 3-х предложений
        if len(ALLSENTENCES) >= 3:
            
            # стеммируются предложения
            # список предложений из основ слов, предложения сгруппированны по абзацам
            STEMMED_SENTENCES = self.stem_sents.tokenizeListParagraphs(LIST_OF_SENTENCES)

            # стеммируется заголовок
            if len(TTL) > 0:
                TITLE_PAIRS = list(itertools.chain.from_iterable(self.stem_sents.tokenizeListSentences(TTL)))
                TITLE = [pair[0] for pair in TITLE_PAIRS]

            else:
                TITLE = []
            
            # список предложений без границ абзацев, предложения разбиты на основы
            NO_PARAGRAPHS = list(itertools.chain.from_iterable(STEMMED_SENTENCES))
            # большой список всех основ слов для подсчета частотности (TF/IDF)
            BIG_LIST_OF_PAIRS = list(itertools.chain.from_iterable(itertools.chain.from_iterable(STEMMED_SENTENCES)))
            BIG_LIST_OF_STEMS = [pair1[0] for pair1 in BIG_LIST_OF_PAIRS]


            # общее количество стем в тексте
            TOTAL_STEMS_IN_TEXT = len(BIG_LIST_OF_STEMS)
            # общее количество предложений в тексте
            TOTAL_SENTS_IN_TEXT = len(ALLSENTENCES)


            if len(BIG_LIST_OF_STEMS) > 0:

                w_count = CountTermWeights(self.language)
                
                # список кортежей (слово, его частота), усечённый по средней частоте
                TOTAL_STEM_COUNT, ABSOLUTE_COUNT = w_count.simpleTermFreqCount(BIG_LIST_OF_STEMS)

                # список "имён собственных"
                PROPER_NOUNS, STEMMED_PNN = FindProperNouns(self.language).lookForProper(ALLSENTENCES, self.stopwords, self.VERBTRANSFORMS, self.NOUNTRANSFORMS, self.lexicon_de, self.ger_nn, self.ger_ne)

                # список терминов с весовыми коэффициентами (кортежи)
                SORTED_TFIDF = w_count.countPureTFIDF(TOTAL_STEM_COUNT, self.terms_dict)
                FINAL_SORTED_TFIDF = w_count.countFinalWeights(SORTED_TFIDF, TITLE, STEMMED_SENTENCES, ALLSENTENCES, TOTAL_STEMS_IN_TEXT, TOTAL_SENTS_IN_TEXT, self.stopwords, self.VERBTRANSFORMS, self.NOUNTRANSFORMS, STEMMED_PNN, self.lexicon_de)
                KEYWORDS = w_count.showKeywords(BIG_LIST_OF_PAIRS, FINAL_SORTED_TFIDF, ABSOLUTE_COUNT, PROPER_NOUNS)
                
                
                # объект класса для вычисления симметричной связи предложений
                # вычисляем вес каждого предложения
                symmetry = SymmetricalSummarizationWeightCount()
                # словари каждого предложения с частотностью по словам
                S_with_termfreqs = symmetry.countTermsInsideSents(NO_PARAGRAPHS)
                SYMMETRICAL_WEIGHTS = symmetry.countFinalSymmetryWeight(FINAL_SORTED_TFIDF, S_with_termfreqs, TOTAL_STEMS_IN_TEXT, TOTAL_SENTS_IN_TEXT, STEMMED_PNN)
                ORIGINAL_SENTENCES = symmetry.convertSymmetryToOrdinary(SYMMETRICAL_WEIGHTS, ALLSENTENCES)

                q, rate = symmetry.selectFinalSents(ORIGINAL_SENTENCES)

                # KWIS = KeywordsInSummary()
                # kwis = KWIS.showKWIS(q, KEYWORDS)

            else:
                print "There are no words to process!"

        else:
            q = ''

            print "Text should be at least 3 sentences long."


        #### saving #####
        kw = True
        with codecs.open(r"output.html",'w','utf-16') as outfile:
            outfile.write("<html><body>" +'\n')
            outfile.write("<style>.beta{position:absolute;left:42px;right:42px;top:10px;}</style>" +'\n')
            outfile.write("<div class='beta'>" +'\n')
            outfile.write("<p style='font-family:verdana'><b>"+"Summary of the given article </b>")
            for ttl in TTL:
                outfile.write("<b>"+"'" + ttl + "'" + "</b></p>" + '\n'+'\n')
            outfile.write("<table style='font-family:Calibri' align='justify'><td>"+'\n')
            for sent3 in range(len(q)):
                outfile.write("<tr>")
                outfile.write("<td>")
                outfile.write(q[sent3][0])
                outfile.write("</td>")
                outfile.write("<td>")
                outfile.write(str(round(q[sent3][1], 3)) +'\t')
                outfile.write(str(q[sent3][2]))
                outfile.write("</td>")
                outfile.write("</tr>"+'\n')
                outfile.write('\n' + '\n')
            outfile.write("</td></table>"+'\n')
            outfile.write("<p style='font-family:Calibri'><b>Number of sentences in the text: </b>" + str(TOTAL_SENTS_IN_TEXT) + "</p>" + '\n'+'\n')
            outfile.write("<p style='font-family:Calibri'><b>The rate of original text compression: </b>" + str(rate) + " sentences</p>" + '\n')
            
            if kw:
                outfile.write("<p style='font-family:Calibri'><b>Keywords of the artice: </b></p>")
                outfile.write("<table style='font-family:Calibri'><td>"+'\n')
                for key, rel, weight in KEYWORDS:
                    outfile.write("<tr>")
                    outfile.write("<td>")
                    outfile.write(", ".join(key))
                    outfile.write("</td>")
                    outfile.write("<td>")
                    outfile.write(str(rel))
                    outfile.write("</td>")
                    outfile.write("<td>")
                    outfile.write(str(round(weight, 3)))
                    outfile.write("</td>")
                    outfile.write("</tr>"+'\n')
                outfile.write("</td></table>"+'\n')
            outfile.write("</div>")
            outfile.write("</body></html>")
        
        # subprocess.call([r"..\AppData\Local\Google\Chrome\Application\chrome.exe", "output.html"])

def main():

    language = ''
    text_read = codecs.open(r"",'r','utf-16')
    
    print "Loading text to summarize..."
    
    OPENTEXT = text_read.read().strip()
    text_read.close()

    summ = SUMMARIZER(language)
    summ.summarize(OPENTEXT)


if __name__ == '__main__':
    main()


