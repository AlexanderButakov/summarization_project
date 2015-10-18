# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from SentenceSplitterClass import *
import re


class TextSegmentor(object):

    """
    Разделение текста на абзацы, предложения и заголовок, если он есть.
    """
    def __init__(self, titled_stopwords, ABBREVIATIONS, language):

        self.language = language
        
        self.titled_stopwords = titled_stopwords
        self.ABBREVIATIONS = ABBREVIATIONS
        self.punctuation = "∙!‼¡\"#£€$¥%&'()*+±×÷·,-./:;<=>?¿@[\]^ˆ¨_`—–­{|}~≈≠→↓¬’“”«»≫‘…¦›🌼′″¹§¼⅜½¾⅘©✩✒•►●★❤➡➜➚➘➔✔➓➒➑➐➏➎➍➌➋➊❸❷■†✝✌￼️³‎²‚„ ​"    # знаки для обрезания вокруг слов
        # знаки, по которым разбивать на слова
        self.punctsplit = re.compile(r'[\s\(\"\'\’\“\”\«\»\‘\[\{\<~…#` �⌂ ∞½¾►=\;\:\—\′\″ „-]+')

        if self.language == 'de':
            self.normalizer = NormalizerDE()
        elif self.language == 'ru':
            self.normalizer = NormalizerRU()
        else:
            self.normalizer = NormalizerEN()


    def splitToParagraphs(self, text):

        """
        Функция разбивает текст на абзацы по новой строке (\n)
        и определяет заголовок текста.
        У строки не должно быть точки слева от первого \n, при этом 
        такая строка должна быть не длинее 17 слов (разбиение по пробелам)
        или не длиннее 65 символов. Тогда это считается заголовком.

        Если точка все таки стоит, то проверяется, нет ли слева от точки акронима
        (acronim) или сокращения (abbrev). Если есть, то это заголовок,
        если нет - абзац.

        """
        paragraphs = []
        title = []
        acronim = re.compile(r'([a-zA-ZА-Яа-я0-9ÄÖÜäöüß]\.([a-zA-ZА-Яа-я0-9ÄÖÜäöüß]\.)*)')                        # title ends with acronim like A.S.A.P. or i.e.
        abbrev= re.compile(r'(etc\.|Jr\.)')                                                # title ends with abbreviations like etc.
        newline = text.find('\n')
        splitted_line = text[:newline].split(' ')
        acronim_match = acronim.match(splitted_line[len(splitted_line)-1])
        abbrev_match = abbrev.match(splitted_line[len(splitted_line)-1])
        
        if len(splitted_line) <= 17 or len(text[:newline]) <= 65:
            if (newline != -1 and text[newline-1] != '.') and (newline != -1 and text[newline-2] != '.'):
                title.append(text[:newline])
                paragraphs = re.split(r'[\r\n]+', text[newline+1:])
            else:
                if acronim_match or abbrev_match:
                    title.append(text[:newline])
                    paragraphs = re.split(r'[\r\n]+', text[newline+1:])
                else:
                    paragraphs = re.split(r'[\r\n]+', text)
                    title = []
        else:
            paragraphs = re.split(r'[\r\n]+', text)
            title = []

        return paragraphs, title

    
    def splitToSents(self, paragraphs):
        """
        Первичное разбиение на предложения. Функция принимает на вход
        список абзацев, возвращает список с вложенными списками предложений.
        """

        set_of_sentences = []

        # для прохода finditer()
        re_terminators = re.compile(r'[\.\!\?\:\;\…]')
                

                                    # Для rightcontext: если после терминатора стоит:
                                    # далее
                                    # 1) просто пробел ( +) --> ( "...конец. Начало..." )
                                    # 2) один из знаков в скобках плюс возможный \s\.\!\? и пробел ([\"\'\’\“\”\„\«\»\‘\)\]\}\>\`\′\″\*¹³²]+[\s\.\!\?]*\s) --> ( "...конец.")! Начало..." )
                                    # 3) возможный пробел плюс конструкция [1] или (Автор:2000) плюс пробел (\[ *[a-zA-Zа-яА-Я0-9,\.\-\:]+ *\]+\s+) --> ("... конец.[1] Начало...")
                                    # 4) возможный знак из скобок + Слово с Большой буквы или цифра [•\"\'\’\„\“\«\‘\(\[\<\{\`\′\″]*[A-ZА-Я\d]
        rightcontext = re.compile(r'( +|[\"\'\’\“\”\„\«\»\‘\)\]\}\>\`\′\″\*¹³²]+[\s\.\!\?]*\s|\[ *[a-zA-Zа-яА-ЯÄÖÜäöüß0-9,\.\-\:]+ *\]+\s+)[•\"\'\’\„\“\«\‘\(\[\<\{\`\′\″]*[A-ZА-ЯÄÖÜ\d]')
        
                                    # если левое от терминатора слово начинается ББ(опционно) + слово с _ или \'
        leftcontext_2 = re.compile(r'[A-ZА-ЯÄÖÜ]?[a-zа-яäöüß_\'»\)\]\}\>]+')
                                    # если правый от терминатора контекст(слово) = (опционно скобка или кавычка)+
                                    # ББ + слово(опционно) или цифра
        rightcontext_2 = re.compile(r'[\"\“\„\«\‘\(\[\<\{\`]?[A-ZА-Я]([A-Za-zА-Яа-яÄÖÜäöüß\.\']+)?')
        
        # new_sent = re.compile(r'\s+[\(\[\<\{\"«“„]')

        # для обработки случаев с двоеточием. Если после ':' 
        # идет цифра или слово с лат. буквы (для русск.)
        for_colon = re.compile(r'[0-9]+([\.\,\:][0-9]+)*') #|[a-zA-ZÄÖÜäöüß]+')
        
        for paragraph in paragraphs:

            begin = 0
            start = 0
            sentences = []

            num_of_sents = 0
            
            # удаление висячих знаков в конце и начале абзаца
            paragraph = paragraph.strip()

            # проверка, если нет знаков препинания --> скинуть в список
            if not re_terminators.search(paragraph):
                sentences.append(paragraph[start:])
                # print 'noterminator'
            
            else:

                # список всех терминаторов абзаца
                all_terminators = re_terminators.finditer(paragraph)

                for terminator in all_terminators:

                     # начальная позиция re-объекта - это индекс в абзаце
                    i = terminator.start()

                    # если совпадает контекст справа от терминатора, запоминаем его
                    if rightcontext.match(paragraph[i+1:]):
                        match = rightcontext.match(paragraph[i+1:])
                        # ищем индекс пробела как разделителя между предложениями,
                        # чтобы по нему складывать предложения и устанавливать итератор start
                        space_index = match.group().index(' ')

                        if paragraph[i] == '.':
                                
                            # список слов абзаца от start до
                            # первого терминатора. Фильт не пускает пустые строки в список
                            s = filter(None, self.punctsplit.split(paragraph[start:i]))

                            # если последнее слово слева от точки не аббревиатура, складываем:
                            if len(s)>0 and self.normalizer.normalizeLetters(s[len(s)-1]) not in self.ABBREVIATIONS:
                                sentences.append(paragraph[start:i+space_index+1])
                                start = i + space_index+2
                                # print "last word not in abbrev"
                            
                            # иначе:
                                # если слева слово из аббрев. (H.), а справа стоп-слово с ББ, складываем предложение
                            else:
                               
                                # отфильтровываем, т.к. в списке первым может стоять пустая строка
                                sentence_to_right = filter(None, self.punctsplit.split(paragraph[i+2:]))
                                if len(sentence_to_right)>0 and self.normalizer.normalizeLetters(sentence_to_right[0].strip(self.punctuation)) in self.titled_stopwords:
                                    sentences.append(paragraph[start:i+space_index+1])
                                    start = i + space_index+2
                                    # print 'abbrev: next word in upper stop'
                        
                        # если не точка:
                        else:
                            # а двоеточие
                            if paragraph[i] == ':':
                                # если справа цифры или латинская буква - не разбивать
                                if not for_colon.match(self.punctsplit.split(paragraph[i+2:])[0].strip(self.punctuation)):
                                    sentences.append(paragraph[start:i+space_index+1])
                                    start = i + space_index+2
                                    # print 'colomn+digit/latin'
                                
                            else:

                                sentences.append(paragraph[start:i+space_index+1])
                                start = i + space_index+2
                                # print 'not period and not colomn'

                    # rightcontext не совпал
                    else:

                        k = filter(None, self.punctsplit.split(paragraph[start:i]))
                        lastword = len(k[len(k)-1])

                        # обработка случаев, когда между предложениями пропущен пробел. (.. in it.The...)
                        if leftcontext_2.match(paragraph[i-lastword:i]) and rightcontext_2.match(paragraph[i+1:]):
                            match = rightcontext_2.match(paragraph[i+1:])
                                
                            if paragraph[i] == '.':
                                                                   
                                if k[len(k)-1] not in self.ABBREVIATIONS:
                                    sentences.append(paragraph[start:i+1])
                                    start = i + 1
                                    # print 'dot: nospace and not in abbrevs'
                            else:
                                sentences.append(paragraph[start:i+1])
                                start = i + 1
                                # print 'nospace+not dot'
            
                sentences.append(paragraph[start:])
                # print 'last sent in par'

            set_of_sentences.append(sentences)

        return set_of_sentences


    def glueWrongSplittedSents(self, set_of_sentences):
        """
        Склеивание предложений, которые были ошибочно разделены.
        Функция принимает на вход список вложенных списков с предложениями,
        возвращает список вложенных списков со склеенными предложениями. 
        """

        acronim = re.compile(r'[\"\'\“\«\‘\(\[\{\<\`]?[A-ZА-ЯÄÖÜ][a-z]{0,1}\.[A-ZА-ЯÄÖÜ]\.$')
        time_pm = re.compile(r'[ap]\.\m\.$')
        chicago_time = re.compile(r'^[A-Z][a-z]+\s[Tt]ime')
        
        time_abbrev = set([
            'EST', 'ET', 'PST', 'EDT',
            'AMC','PST', 'PDT', 'ET/PT',
            'Eastern', 'CT', 'Western',
            'CST', 'EST/PST', 'PT'
        ])
        week_days = set([
            "Monday", "Tuesday", "Wednesday", "Thursday",
            "Friday", "Saturday", "Sunday", "Mondays",
            "Tuesdays", "Wednesdays", "Thursdays",
            "Fridays", "Saturdays", "Sundays"
        ])

        glued_sentence = ""
        last_sentence_in_glued = ""
        set_of_gluedsentences = []

        for sentences in set_of_sentences:

            all_sentences = []

            for s in range(len(sentences)):

                if len(sentences[s]) > 0:

                    ########
                    # Склейка через точку, которая не конец предложения + если текущее предложение не последнее в абзаце,
                    # чтобы не искать s+1 и не выходить за рейнджи.
                    ########
                    if sentences[s][len(sentences[s])-1] == '.' and s != len(sentences)-1:

                        # находим в левом от точки предложении последнее слово
                        left_sent_split = self.punctsplit.split(sentences[s])
                        first_word_to_left = left_sent_split[len(left_sent_split)-1].lstrip(self.punctuation)

                        # находим первое слово правого предложения
                        first_word_to_right = self.normalizer.normalizeLetters(self.punctsplit.split(sentences[s+1])[0].rstrip(self.punctuation))
                        
                        # если уже произошла склейка, идем сюда.
                        # если текущее предложение уже приклеено
                        if sentences[s] == last_sentence_in_glued:
                            # и если его последнее слово не аббрев. или время, то бросаем его и переходим к следующему
                            if not acronim.match(first_word_to_left) and not time_pm.match(first_word_to_left):
                                continue
                            else:
                                
                                # first_word_to_right = punctsplit.split(sentences[s+1])[0].rstrip(punctuation)

                                # если в конце предлож. аббрев. (U.S.)
                                if acronim.match(first_word_to_left):
                                    # и если правое предложение начинается не со слова из стоп-слов 
                                    # - приклеиваем к уже склеенному предложению в списке правое предлоежние от тукущего
                                    if first_word_to_right not in self.titled_stopwords:
                                        glued_sentence = all_sentences[len(all_sentences)-1] + ' ' + sentences[s+1]
                                        all_sentences[len(all_sentences)-1] = glued_sentence
                                        last_sentence_in_glued = sentences[s+1]
                                        # print "glue0"
                                        continue
                                    else:
                                        continue
                                
                                # если в конце время (p.m.)        
                                elif time_pm.match(first_word_to_left):
                                    # и если первое слово следующего предлоежния в списке time-abbrev или дней недели или Chicago Time = true,
                                    # приклеиваем к уже склеенному предложению в списке правое предлоежние от тукущего
                                    if first_word_to_right in time_abbrev or first_word_to_right in week_days or chicago_time.match(sentences[s+1]):
                                        glued_sentence = all_sentences[len(all_sentences)-1] + ' ' + sentences[s+1]
                                        all_sentences[len(all_sentences)-1] = glued_sentence
                                        last_sentence_in_glued = sentences[s+1]
                                        continue
                                    else:
                                        continue

                        ########
                        # Первая часть склейки: U.S. + Post Office.
                        ########
                        if acronim.match(first_word_to_left):

                            # если первое слово в предложении справа не из списка стоп-слов, склеиваем текущее и след. предложения
                            # запоминаем приклеенное предложение в last_sentence_in_glued, чтобы не скидывать его в след. итерации
                            if first_word_to_right not in self.titled_stopwords:
                                glued_sentence = sentences[s] + ' ' + sentences[s+1]
                                last_sentence_in_glued = sentences[s+1]
                                all_sentences.append(glued_sentence)
                                # print "glue U.S."
                            else:
                                all_sentences.append(sentences[s])
                        
                        ########
                        # Вторая часть склейки: 8 p.m. + Chicago Time. / 9 a.m. + EST / 10 p.m. + Monday.
                        ########                 
                        elif time_pm.match(first_word_to_left):

                            # first_word_to_right = punctsplit.split(sentences[s+1])[0].rstrip(punctuation)

                            # если первое слово из правого предложения в списке time-abbrev или дней недели
                            if first_word_to_right in time_abbrev or first_word_to_right in week_days:
                                glued_sentence = sentences[s] + ' ' + sentences[s+1]
                                last_sentence_in_glued = sentences[s+1]
                                all_sentences.append(glued_sentence)
                            # или если право предложения начинается "word" + T(t)ime 
                            elif chicago_time.match(sentences[s+1]):
                                glued_sentence = sentences[s] + ' ' + sentences[s+1]
                                last_sentence_in_glued = sentences[s+1]
                                all_sentences.append(glued_sentence)
                            else:
                                all_sentences.append(sentences[s])

                        else:
                            all_sentences.append(sentences[s])

                    ########
                    # Склейка через двоеточие, если слева от двоеточия не больше 3 слов
                    ########
                    elif sentences[s][len(sentences[s])-1] == ':' and s != len(sentences)-1:
                    
                        if sentences[s] == last_sentence_in_glued:
                            continue
                        
                        if len(sentences[s].split()) <= 3 or len(sentences[s+1].split()) <= 3:
                            glued_sent = sentences[s] + ' ' + sentences[s+1]
                            last_sentence_in_glued = sentences[s+1]
                            all_sentences.append(glued_sent)
                            # print 'glue:1'
                        
                        else:
                            all_sentences.append(sentences[s])

                    else:
                        if sentences[s] != last_sentence_in_glued:
                            all_sentences.append(sentences[s])

            set_of_gluedsentences.append(all_sentences)
            

        return set_of_gluedsentences


    def glueSpecialDE(self, set_of_sentences):

        digits = re.compile(r'[0-9]+')

        glued_sentence = ""
        last_sentence_in_glued = ""
        set_of_gluedsentences = []

        for sentences in set_of_sentences:

            all_sentences = []

            for s in range(len(sentences)):

                if len(sentences[s]) > 0:

                    ########
                    # Склейка через точку, которая не конец предложения + если текущее предложение не последнее в абзаце,
                    # чтобы не искать s+1 и не выходить за рейнджи.
                    ########
                    if sentences[s][len(sentences[s])-1] == '.' and s != len(sentences)-1:

                        # находим в левом от точки предложении последнее слово
                        left_sent_split = self.punctsplit.split(sentences[s])
                        first_word_to_left = left_sent_split[len(left_sent_split)-1].lstrip(self.punctuation)

                        # находим первое слово правого предложения
                        first_word_to_right = self.normalizer.normalizeLetters(self.punctsplit.split(sentences[s+1])[0].rstrip(self.punctuation))
                        
                        # если уже произошла склейка, идем сюда.
                        # если текущее предложение уже приклеено
                        if sentences[s] == last_sentence_in_glued:
                            # и если его последнее слово не аббрев. или время, то бросаем его и переходим к следующему
                            if not digits.match(first_word_to_left):
                                continue
                            else:

                                # если в конце предлож. цифры
                                if digits.match(first_word_to_left):
                                    # и если правое предложение начинается не со слова из стоп-слов 
                                    # - приклеиваем к уже склеенному предложению в списке правое предлоежние от тукущего
                                    if first_word_to_right not in self.titled_stopwords:
                                        glued_sentence = all_sentences[len(all_sentences)-1] + ' ' + sentences[s+1]
                                        all_sentences[len(all_sentences)-1] = glued_sentence
                                        last_sentence_in_glued = sentences[s+1]
                                        # print "glue_de"
                                        continue
                                    else:
                                        continue

                        ########
                        # Первая часть склейки: 5. November
                        ########
                        if digits.match(first_word_to_left):

                            # если первое слово в предложении справа не из списка стоп-слов, склеиваем текущее и след. предложения
                            # запоминаем приклеенное предложение в last_sentence_in_glued, чтобы не скидывать его в след. итерации
                            if first_word_to_right not in self.titled_stopwords:
                                glued_sentence = sentences[s] + ' ' + sentences[s+1]
                                last_sentence_in_glued = sentences[s+1]
                                all_sentences.append(glued_sentence)
                                # print "glue 5. November"
                            else:
                                all_sentences.append(sentences[s])

                        else:
                            all_sentences.append(sentences[s])

                    else:
                        if sentences[s] != last_sentence_in_glued:
                            all_sentences.append(sentences[s])

            set_of_gluedsentences.append(all_sentences)

        return set_of_gluedsentences


    def segment(self,text):
        """
        Функция вызывает последовательно три функции: 
        1) разбивка на абзацы и заголовок,
        2) разбивка на предложения, 
        3) склейка предложений.
        Возвращает заголовок и список вида [[[],[]],[[],[]],[[]]].
        Вторая вложенность - абзацы, внутренние списки - предложения.
        """

        # заменяем множественные пробелы на один.
        paragraphs, title = self.splitToParagraphs(re.sub(r' {2,}',' ', text))
        set_of_sentences = self.splitToSents(paragraphs)

        if self.language == 'de':
            set_of_readysents = self.glueSpecialDE(self.glueWrongSplittedSents(set_of_sentences))
        else:
            set_of_readysents = self.glueWrongSplittedSents(set_of_sentences)


        return set_of_readysents, title
