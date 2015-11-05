# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from collections import defaultdict
from SentenceSplitterClass import SentenceSplitter
import itertools, math, re


class FindProperNouns(object):

    def __init__(self, language):

        self.language = language

    def lookForProper(self, lst_of_sents, stopwords, VERBTRANSFORMS, NOUNTRANSFORMS, lexicon_de, ger_nn, ger_ne):
        '''
        Наивный метод поиска имен собственных. 
        Они нужны при добавлении дополнительных весов предложениям и словам.
        Для англ. и русск. выбираются все слова с большой буквы, если они
        стоят не в начале предложения.
        В немецком все сущ. пишутся с большой буквы, поэтому ищем слово с большой буквы
        в списке имен собственных и геоназваний.
        '''

        proper_nouns = set([])
        proper_nouns_de = []
        sp_object = SentenceSplitter(stopwords, VERBTRANSFORMS, NOUNTRANSFORMS, lexicon_de, self.language)
        s_set = sp_object.tokenizeSentencesWithCaseKeeping(lst_of_sents)

        for s in range(len(s_set)):
            for w in range(len(s_set[s])):
                if s_set[s][w][0].istitle() and w != 0:
                    proper_nouns.add(s_set[s][w])

        if self.language == 'ru':
            stemmed_pnn = set([sp_object.stemmer.stem(sp_object.lemmatizer_ru.parse(pnn.lower())[0].normal_form) for pnn in proper_nouns])
        elif self.language == 'de':
            
            for candidate in proper_nouns:
                got_candidat = False
                for l in range(len(candidate)):
                    candidate_no_prefix = candidate[l:]
                    if candidate_no_prefix.title() in ger_nn:
                        got_candidat = True
                        if candidate in ger_ne:
                            proper_nouns_de.append(candidate)
                            break
                if not got_candidat:
                    proper_nouns_de.append(candidate)

            stemmed_pnn = set([sp_object.stemmer.stem(pnn.lower()) for pnn in proper_nouns_de])

        else:
            stemmed_pnn = set([sp_object.stemmer.stem(pnn.lower(), 0, len(pnn)-1) for pnn in proper_nouns])

        return proper_nouns, stemmed_pnn

class CalculateExtraWeights(object):
    '''
    Методы класса возвращают списки, которые нужны для подсчета дополнительных весов словам
    '''

    def collectFirstLastSents(self, lst_of_paragraphs):
        '''
        Формируется список первых и последних предложений абзацев
        '''

        first_last_sents = []

        for par in range(len(lst_of_paragraphs)):
            if len(lst_of_paragraphs[par]) > 0:
                if len(lst_of_paragraphs[par]) > 1:
                    first_last_sents.append(lst_of_paragraphs[par][0]) 
                    first_last_sents.append(lst_of_paragraphs[par][len(lst_of_paragraphs[par])-1])
                else:
                    first_last_sents.append(lst_of_paragraphs[par][0])

        return first_last_sents

    def collectQuestionSents(self, lst_of_sents):
        '''
        Формируется список вопросительных предложений
        '''

        lst_of_quest_exclum_sents = []

        for s in range(len(lst_of_sents)):
            if lst_of_sents[s][len(lst_of_sents[s])-1] == '?' or lst_of_sents[s][len(lst_of_sents[s])-1] == '!':
                lst_of_quest_exclum_sents.append(lst_of_sents[s])

        return lst_of_quest_exclum_sents

##### TF-IDF #####
class CountTermWeights(object):

    """
    Вычисление tf-idf для терминов текста.
    """

    def __init__(self, language):

        self.language = language

    def simpleTermFreqCount(self, big_lst):

        """
        Метод получает на вход список стем.
        В словаре stemfreqs считаются частотности стем.
        Подсчитывается общее количество стем в словаре (total_stems_in_text).
        Вычисляется среднее арифметическое (mean_freq).
        Стемы с частотностью выше среднего арифм. выбираются в список termsfreq.
        Список termsfreq - это кортежи с парами (слово, относительная частота)
        [(word1, 0.34646),(word2, 0.46785),(word3, 0.09786)]

        """

        stemfreqs = defaultdict(int)
        
        for stem in big_lst:
            stemfreqs[stem] += 1

        total_stems_in_text = float(len(big_lst))

        mean_freq = sum(stemfreqs.values()) / total_stems_in_text

        termsfreq = [(word, freq / total_stems_in_text) for word, freq in stemfreqs.iteritems() if freq >= mean_freq]
        termsfreq_0 = [(word, freq) for word, freq in stemfreqs.iteritems() if freq >= mean_freq]

        return termsfreq, termsfreq_0

    def countPureTFIDF(self, stems, corpus):

        """
        На вход ф-я получает список стем с частотами и словарь корпуса текстов 
        для вычисления tf-idf.
        
        """

        weighted_terms = []

        if self.language == 'ru':
            N = 158099
        if self.language == 'en':
            N = 13963
        if self.language == 'de':
            N = 106363

        for st in range(len(stems)):
            if stems[st][0] in corpus:
                d = stems[st][1] * math.log(N / corpus[stems[st][0]], 2)
                weighted_terms.append((stems[st][0], d))
            else:
                weighted_terms.append((stems[st][0], stems[st][1]))


        sorted_tfidf = sorted(((term, tfidf) for term, tfidf in weighted_terms), key = lambda w:w[1], reverse = True)
        
        return sorted_tfidf

    def countFinalWeights(self, tfidf_list, title, lst_of_paragraphs, lst_of_plain_sents, total_stems_in_text, total_sents_in_text, stopwords, VERBTRANSFORMS, NOUNTRANSFORMS, stemmed_pnn, lexicon_de):

        """
        Подсчитывается финальный вес стемы с накруткой дополнительных коэффициентов.
        """

        weighted_terms2 = []
        weighted_terms3 = []
        weighted_terms4 = []
        weighted_terms5 = []
        
        # список первых и последних предложений
        collection_of_first_last_sents = CalculateExtraWeights().collectFirstLastSents(lst_of_paragraphs)
        # список слов первых и последних предложений абзацев
        pairs_collection_of_first_last_sents = list(itertools.chain.from_iterable(collection_of_first_last_sents))
        stems_collection_of_first_last_sents = [pair[0] for pair in pairs_collection_of_first_last_sents]
        # количество слов в первых и последних предложениях
        total_stems_in_first_last = len(stems_collection_of_first_last_sents)
        # количество слов из словаря в первых и последних предложениях
        total_dictwords_in_first_last = 0

        for t0 in range(len(tfidf_list)):
            for s1 in stems_collection_of_first_last_sents:
                if tfidf_list[t0][0] == s1:
                    total_dictwords_in_first_last += 1
                
        # среднее количество слов из словаря в первых и последних предложениях абзацев
        avg_dictwords_in_first_last = total_dictwords_in_first_last/float(total_stems_in_first_last)
        # среднее количество слов в первых и последних предложениях абзацев
        avg_stems_in_first_last = total_stems_in_first_last/float(total_stems_in_text)
        
        # список вопросительных и восклиц. предложений
        collection_of_q_excl_sents = CalculateExtraWeights().collectQuestionSents(lst_of_plain_sents)
        # список слов из вопросительных и восклицательных предложений
        sp_object = SentenceSplitter(stopwords, VERBTRANSFORMS, NOUNTRANSFORMS, lexicon_de, self.language)
        pairs_collection_of_q_excl_sents = list(itertools.chain.from_iterable(sp_object.tokenizeListSentences(collection_of_q_excl_sents)))
        stems_collection_of_q_excl_sents = set([pair[0] for pair in pairs_collection_of_q_excl_sents])
        # количество вопросительных и восклицательных предложений в тексте
        num_of_q_excl_sents = len(collection_of_q_excl_sents)

        # если термины из словаря есть в заголовке, то удваиваем их вес
        for t1 in range(len(tfidf_list)):
            if tfidf_list[t1][0] in title:
                m = tfidf_list[t1][1] * 2
                weighted_terms2.append((tfidf_list[t1][0], m))
            else:
                weighted_terms2.append((tfidf_list[t1][0], tfidf_list[t1][1]))
        
        # если термины есть в первых и последн. предложениях абзацев, то вес термина
        # умножаем на частное среднего кол-ва терминов из словаря в первых и посл. предл.
        # и среднего кол-ва терминов в первых и последн. предл-х.
        for t2 in range(len(weighted_terms2)):
            if weighted_terms2[t2][0] in set(stems_collection_of_first_last_sents):
                m2 = weighted_terms2[t2][1] * (avg_dictwords_in_first_last / avg_stems_in_first_last)
                weighted_terms3.append((weighted_terms2[t2][0], m2))
            else:
                weighted_terms3.append((weighted_terms2[t2][0], weighted_terms2[t2][1]))
        
        # если термины есть в вопросительных и восклицательных предложениях,
        # то умножаем вес термина на частное от кол-ва таких предложений
        # и общего кол-ва предложений текста
        for t3 in range(len(weighted_terms3)):
            if weighted_terms3[t3][0] in stems_collection_of_q_excl_sents:
                m3 = weighted_terms3[t3][1] * (num_of_q_excl_sents / float(total_sents_in_text))
                weighted_terms4.append((weighted_terms3[t3][0], m3))
            else:
                weighted_terms4.append((weighted_terms3[t3][0], weighted_terms3[t3][1]))
        
        # если термины из словаря - это "имена собственные", то умножаем вес
        # термина на частное среднего кол-ва терминов из словаря в первых и посл. предл.
        # и среднего кол-ва терминов в первых и последн. предл-х.
        for t4 in range(len(weighted_terms4)):
            if weighted_terms4[t4][0] in stemmed_pnn:
                m4 = weighted_terms4[t4][1] * (avg_dictwords_in_first_last / avg_stems_in_first_last)
                weighted_terms5.append((weighted_terms4[t4][0], m4))
            else:
                weighted_terms5.append((weighted_terms4[t4][0], weighted_terms4[t4][1]))
        
        mean_weight = sum([(weighted_terms5[s][1]) for s in range(len(weighted_terms5))]) / float(len(weighted_terms5))
        
        sorted_tfidf2 = sorted(((term, weight) for term, weight in weighted_terms5 if weight > mean_weight), key = lambda w:w[1], reverse = True)

        return sorted_tfidf2

    def showKeywords(self, lst_of_pairs, tfidf_list, rel_freq_lst, lst_pnn):
        
        """
        Функция сопоставляет стеммы ключевых слов непосредственно со словами,
        чтобы вывести их в резултат.
        На вход принимает список пар (стемма, слово), список весов, список 
        относительных частот (для web) и список имен собственных. 
        Список имен собственных нужен для правильного вывода слов 
        с заглавной буквы и аббревиатур. Возвращает список кортежей 
        ключевых слов и их весов.
        """

        keywords = []
        # на входе это set, а set не поддерживает индексацию.
        lst_pnn = list(lst_pnn)
        # понижаем регистр имён
        lst_pnn_lowered = [name.lower() for name in lst_pnn]

        # добавляем в список ключевых слов абсолютные частоты
        # список теперь выглядит как [(слово, абс.част, tf-idf), (...)]
        freq_lst = []

        for w in tfidf_list:
            for rel_f in rel_freq_lst:
                if w[0] == rel_f[0]:
                    freq_lst.append((w[0], rel_f[1], w[1]))


        # если термин из словаря встретился в списке пар,
        # и если второй элемент пары есть в списке имен lower,
        # то взять соответствующий ему элемент в списке без
        # понижения регистра.
        for term in freq_lst:
            kw = []
            for pair in set(lst_of_pairs):
                if term[0] == pair[0]:
                    if pair[1] in lst_pnn_lowered:
                        for n in range(len(lst_pnn_lowered)):
                            if pair[1] == lst_pnn_lowered[n]:
                                kw.append(lst_pnn[n])
                    else:
                        kw.append(pair[1])
            keywords.append((kw, term[1], term[2]))

                
        return keywords

##### Symmetrical Summarizing #####

class SymmetricalSummarizationWeightCount(object):

    """
    Проводится начисление весов предложениям по методике симметричного реферирования
    (Яцко В.А. Симметричное реферирование: теоретические основы и методика
     // Научно-техническая информация. Сер.2. - 2002. -  № 5).
    """

    def countTermsInsideSents(self, sents_lst):

        """
        Метод получает список предложений вида [[sentence1],[sentence2]].
        Для каждого предложения подсчитывается частота входящих в него стем.
        Возвращается список, содержащий в себе словари стем с их частотами в каждом
        предложении [{word1:2, word2:5, wordn:c},{word1:5, word2:6, wordn:c}]
        """

        sents_with_termsfreqs = []
        
        for sentence in sents_lst:
            stem_f = defaultdict(int)
            for pair in sentence:
                stem_f[pair[0]] +=1

            sents_with_termsfreqs.append(stem_f)
        
        return sents_with_termsfreqs

    def rightLinksCount(self, tfidf_terms, sents_with_termsfreqs):

        """
        Метод производит поиск связей между предложениями вправо.
        Принимает на вход список tf-idf, и список словарей с частотами
        для каждого предложения. Берется предложение (словарь), если в нем есть
        термин из tf-idf, то ищется вхождение этого термина в предложениях справа.
        Если термин встретился в предложении справа, то выбирается его наибольшая
        частота (т.е. либо из исходного предложения, либо из правого), эта
        частота суммируется с общим весом предложения. Последнее предложение
        скидывается в список с нулевым весом, т.к. справа от него ничего нет.
        Возвращается список кортежей, в котором предложениям (словараям)
        приписаны веса [({sentence1}, вес), ({sentence2}, вес)]
        
        Параллельно для текущего предложения суммируются веса входящих 
        в него ключевых слов, сумма прибавляется к весу предложения.
        
        Дополнительно вычисляется позиционный коэффициент, т.е. чем выше
        предложение, тем больше вес. Тоже прибавляется к общему весу.
        """
        
        w_sent_r = []
        line = 0

        for s in range(len(sents_with_termsfreqs)):
            c = 0
            cw = 0
            line += 1
            # позиционный коэффициент
            pscore = (1/line)*10
            if s != len(sents_with_termsfreqs)-1:
                slice1 = sents_with_termsfreqs[s+1:]
                for t in range(len(tfidf_terms)):
                    if tfidf_terms[t][0] in sents_with_termsfreqs[s]:
                        cw += tfidf_terms[t][1]
                        for s2 in range(len(slice1)):
                            if tfidf_terms[t][0] in slice1[s2]:
                                if sents_with_termsfreqs[s][tfidf_terms[t][0]] > slice1[s2][tfidf_terms[t][0]]:
                                    c += sents_with_termsfreqs[s][tfidf_terms[t][0]]
                                else:
                                    c += slice1[s2][tfidf_terms[t][0]]
                
                w_sent_r.append((sents_with_termsfreqs[s],c+cw+pscore))

            else:
                for t in range(len(tfidf_terms)):
                    if tfidf_terms[t][0] in sents_with_termsfreqs[len(sents_with_termsfreqs)-1]:
                        cw += tfidf_terms[t][1]
                    else:
                        cw = 0
                
                w_sent_r.append((sents_with_termsfreqs[s],cw+pscore))

        return w_sent_r

    def leftLinksCount(self, tfidf_terms,sents_with_termsfreqs):

        """
        Метод производит поиск связей между предложениями влево.
        Тот же алгоритм, что и при поиске вправо, только с нулевым
        весом скидывается первое предложение. Чтобы реализовать 
        поиск влево, список предложений переворачивается.
        Возвращается список кортежей, в котором предложениям (словараям)
        приписаны веса [({sentence1}, вес), ({sentence2}, вес)]
        """

        w_sent_l = []
                    
        for s in reversed(range(len(sents_with_termsfreqs))):
            c = 0
            slice1 = sents_with_termsfreqs[:s]
            if s != 0:
                for t in range(len(tfidf_terms)):
                    if tfidf_terms[t][0] in sents_with_termsfreqs[s]:
                        for s2 in reversed(range(len(slice1))):
                            if tfidf_terms[t][0] in slice1[s2]:
                                if sents_with_termsfreqs[s][tfidf_terms[t][0]] > slice1[s2][tfidf_terms[t][0]]:
                                    c += sents_with_termsfreqs[s][tfidf_terms[t][0]]
                                else:
                                    c += slice1[s2][tfidf_terms[t][0]]
                        
                w_sent_l.append((sents_with_termsfreqs[s],c))
        
            else:
                w_sent_l.append((sents_with_termsfreqs[0], 0))
        

        return w_sent_l

    def countSymmetry(self,tfidf_terms,sents_with_termsfreqs):

        """
        Метод складывает два списка, полученных при поиске
        вправо и влево. Принимает на вход так же список tf-idf,
        и список предложений-словарей. Внутри явно вызываются 
        функции установления правых и левых связенй, порядок 
        предложений в двух списках выравнивается и их веса складываются.
        Возвращается список кортежей предлоежний-словарей с весами.
        """
    
        w_sent = []
                
        right_links = self.rightLinksCount(tfidf_terms, sents_with_termsfreqs)
        left_links = self.leftLinksCount(tfidf_terms, sents_with_termsfreqs)

        for s_r, s_l in zip(range(len(right_links)), reversed(range(len(left_links)))):

            w_sent.append((right_links[s_r][0], right_links[s_r][1] + left_links[s_l][1]))
        
        return w_sent

    
    def countFinalSymmetryWeight(self,tfidf_terms,sents_with_termsfreqs, total_stems_in_text, total_sents_in_text, stemmed_pnn):

        """
        Метод добавляет к весам предложения дополнительный 
        коэффициент ASL (average sentence length), чтобы 
        длинные предложения не набрали большой вес.
        Принимает на вход список tf-idf, список предложений-словарей,
        общее кол-во стем в текте и общее количество предлоежний в тексте.
        Явно вычисляется функция countSymmetry(), затем asl и в цикле
        весу каждого предложения добавляется доп. коэффициент.
        (Вес первого предложения удваивается.???)

        Также каждый вес умножается на кол-во имен собственных и цифр.
        """

        w_sent = self.countSymmetry(tfidf_terms,sents_with_termsfreqs)
        w_sent2 = []
        w_sent3 = []
        w_sent4 = []
        # average sentence length
        asl = total_stems_in_text / total_sents_in_text
        
        # список для хранения частот "имен собственных" в каждом предложении
        n_p = []

        f_digits = re.compile(r'[0-9]+([\.\,\:][0-9]+)*')
        digits = []

        for s in range(len(w_sent)):
            p = 0
            for pnn in stemmed_pnn:
                if pnn in w_sent[s][0]:
                    p += 1
            n_p.append(p)
                
        for sd in range(len(w_sent)):
            dig = []
            dig = len(f_digits.findall(' '.join([sk for sk in w_sent[sd][0]])))
            digits.append(dig)
                        
        for s0 in range(len(w_sent)):
            if len(w_sent[s0][0]) > 0:
                if n_p[s0] != 0:
                    score0 = w_sent[s0][1] * (1+math.log(n_p[s0], 2))
                    w_sent2.append((w_sent[s0][0], score0))
                    
                else:
                    w_sent2.append((w_sent[s0][0], w_sent[s0][1]))
            else:
                w_sent2.append((w_sent[s0][0], w_sent[s0][1]))

        for s_0 in range(len(w_sent2)):
            if len(w_sent2[s_0][0]) > 0:
                if digits[s_0] != 0:
                    score_0 = w_sent2[s_0][1] * (1+math.log(digits[s_0], 2))
                    w_sent3.append((w_sent2[s_0][0], score_0))
                    
                else:
                    w_sent3.append((w_sent2[s_0][0], w_sent2[s_0][1]))
            else:
                w_sent3.append((w_sent2[s_0][0], w_sent2[s_0][1]))

        for s1 in range(len(w_sent3)):
            if len(w_sent3[s1][0]) > 5:
                word_count = len(w_sent3[s1][0])
                score = (asl * w_sent3[s1][1]) / word_count
                if s1 != 0:
                    w_sent4.append((w_sent3[s1][0], score))
                else:
                    w_sent4.append((w_sent3[s1][0], score*1))
            else:
                w_sent4.append((w_sent3[s1][0], w_sent3[s1][1]))
                
        return w_sent4

    def convertSymmetryToOrdinary(self, symm_weights, ordinary_sents):

        """
        Метод получает на вход список кортежей предложений-словарей с весами
        и список оригинальных предложений, т.е. неподвергшихся токенизации
        и стеммингу. Из последнего списка выбираются предложения, которые
        соответствуют словарям с весами. Стоит ограничение на длину показываемого
        предложения. Она должна быть не меньше 6 (и не больше 50 токенов) (UPD:
        если выходной список пустой, то берутся все предложения, вне зависимости
        от длины).
        Возвращается отсортированный по убыванию список предложений
        из оригинального текста с весом и его позицией в тексте.
        [(sentence, weight), (sentence, weight)]
        """

        prefinal_sentences = []
                        
        ordinary_sents_with_freqs = [(ordinary_sents[s], symm_weights[s][1], s) for s in range(len(symm_weights))] #if symm_weights[s][1] > mean_weight]

        s_ordinary_sents_with_freqs = sorted(ordinary_sents_with_freqs, key = lambda w:w[1], reverse = True)

        for sent in range(len(s_ordinary_sents_with_freqs)):
            # if 6 < len(s_ordinary_sents_with_freqs[sent][0].split()) < 50:
            if len(s_ordinary_sents_with_freqs[sent][0].split()) > 6:
                prefinal_sentences.append((s_ordinary_sents_with_freqs[sent][0], s_ordinary_sents_with_freqs[sent][1], s_ordinary_sents_with_freqs[sent][2]))

        if len(prefinal_sentences) == 0:
            for sent in range(len(s_ordinary_sents_with_freqs)):
                prefinal_sentences.append((s_ordinary_sents_with_freqs[sent][0], s_ordinary_sents_with_freqs[sent][1], s_ordinary_sents_with_freqs[sent][2]))
        
        return prefinal_sentences                
                
                
    def selectFinalSents(self, converted_sents, percentage=20):

        """
        Метод выбирает n первых предложений из списка.
        n определяется указанным процентом. Список сортируется
        по позиции предложения в оригинальном тексте, таким образом
        возвращается оригинальная последовательность, чтобы хоть
        как-то сохранить связность. Возвращается список кортежей:
        [(предложение, вес, порядковый номер), ()]
        """

        salient_sentences = []

        compression_rate = int(round(((len(converted_sents) * percentage) / 100) + 0.5))

        salient_sentences = converted_sents[:compression_rate]
        
        sorted_salient_sentences = sorted(salient_sentences, key = lambda w:w[2])
        
        return sorted_salient_sentences, compression_rate

class KeywordsInSummary(object):

    def showKWIS(self, summary, keywords):
        '''
        Грубый метод для 'подсвечивания' ключевых слов в html-выдаче.
        '''

        only_keywords = list(itertools.chain.from_iterable([kw[0] for kw in keywords]))

        only_sentences = [sent[0] for sent in summary]

        kwis = []

        for sentence in only_sentences:
            for kw in only_keywords:
                if kw in sentence:
                    sentence = sentence.replace(kw, '<b>'+kw+'</b>')
            kwis.append((sentence, 0, 0))


        return kwis
