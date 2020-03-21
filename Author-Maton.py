import discord
import re
import mysql.connector
from mysql.connector import Error
import subprocess
import time
import requests
import random
from discord.utils import get
import discord.utils
from datetime import datetime

client = discord.Client()
quiz_event = { }
quiz_answer = { }
poetry_tag_event = { }
poetry_tag_users = { }
poetry_tag_mode = { }
poetry_tag_current_user = {}
poetry_tag_tandem_poem = {}
poetry_tag_topic = { }
quiz_scores = {}
word_of_the_day_score = 20
entry_limit = 5

def log_message(log_entry):
    current_time_obj = datetime.now()
    current_time_string = current_time_obj.strftime("%b %d, %Y-%H:%M:%S.%f")
    print(current_time_string + " - " + log_entry, flush = True)
    
def commit_sql(sql_query, params = None):
    try:
        connection = mysql.connector.connect(host='localhost', database='AuthorMaton', user='REDACTED', password='REDACTED')    
        cursor = connection.cursor()
        result = cursor.execute(sql_query, params)
        connection.commit()
        return True
    except mysql.connector.Error as error:
        log_message("Database error! " + str(error))
        return False
    finally:
        if(connection.is_connected()):
            cursor.close()
            connection.close()
            
                
def select_sql(sql_query, params = None):
    try:
        connection = mysql.connector.connect(host='localhost', database='AuthorMaton', user='REDACTED', password='REDACTED')
        cursor = connection.cursor()
        result = cursor.execute(sql_query, params)
        records = cursor.fetchall()
        return records
    except mysql.connector.Error as error:
        log_message("Database error! " + str(error))
        return None
    finally:
        if(connection.is_connected()):
            cursor.close()
            connection.close()

def execute_sql(sql_query):
    try:
        connection = mysql.connector.connect(host='localhost', database='AuthorMaton', user='REDACTED', password='REDACTED')
        cursor = connection.cursor()
        result = cursor.execute(sql_query)
        return True
    except mysql.connector.Error as error:
        log_message("Database error! " + str(error))
        return False
    finally:
        if(connection.is_connected()):
            cursor.close()
            connection.close()
            
            
async def send_message(message, response):
    log_message("Message sent back to server " + message.guild.name + " channel " + message.channel.name + " in response to user " + message.author.name + "\n\n" + response)
    message_chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
    for chunk in message_chunks:
        await message.channel.send(">>> " + chunk)
        time.sleep(1)

async def load_words(message):
    xml_file = "/home/REDACTED/enwiktionary-latest-pages-articles.xml"
    
    f = open(xml_file, 'r')
    word_count = 0
    definition = " "
    word = " "
    synonyms = " "
    antonyms = " "
    rhymes = " "
    part_of_speech = "unknown"
    syn_flag = False
    ant_flag = False
    etym_flag = False
    sample_sentence_re = re.compile(r"#\*.*|#:")
    divider_re = re.compile(r"----")
    part_of_speech_re = re.compile(r"Adjective|Noun|Verb|Adverb|Pronoun|Conjunction|Preposition|Interjection")
    english_re = re.compile("=English=")
    etym_re = re.compile(r"=Etymology.*?=")
    adj_re = re.compile(r"=Adjective=")
    noun_re = re.compile(r"=Noun=")
    verb_re = re.compile(r"=Verb=")
    adverb_re = re.compile(r"=Adverb=")
    rhyme_replace_re = re.compile(r"begin rhyme list|end rhyme list", re.MULTILINE | re.S)
    translations_re = re.compile(r"=Translations=", re.MULTILINE | re.S)
    
    pronoun_re = re.compile(r"=Pronoun=")
    conj_re = re.compile(r"=Conjunction=")
    prep_re = re.compile(r"=Preposition=")
    intj_re = re.compile(r"=Interjection=")
    wiki_re = re.compile(r"[\[|\]|\{|\}|\||\|\|]")
    extra_clear_re = re.compile(r"\s+lb\s+|", re.MULTILINE | re.S)
    extra_extra_clear_re = re.compile("\s+en\s+|;en\s+|^en\s+|\|en\s+|\|en", re.MULTILINE | re.S)
    title_re = re.compile(r"<title>(?P<word>.*)</title>")
    text_begin_re = re.compile(r"<text")
    text_end_re = re.compile(r"</text>", re.MULTILINE | re.S)
    symbol_re = re.compile(r"ref.+?;|&.+?;", re.MULTILINE | re.S)
    definition_re = re.compile(r"^\#+\s+.*", re.MULTILINE | re.S)
    synonym_re = re.compile(r"=Synonyms=")
    antonym_re = re.compile(r"=Antonyms=")
    remove_first_separator_re = re.compile(r"^\s*?[;,]\s+?")
    syn_word_re = re.compile(r"\{\{(?:.+\|)+.+?\}\}")
    ant_word_re = re.compile(r"\{\{(?:.+\|)+.+?\}\}")
    page_end_re = re.compile(r"</page>")
    def_exclude_re = re.compile(r"infl of|inflection of|verb form|verb-form|imperative of")
    blank_re = re.compile(r"^\s+$")
    sentence_re = re.compile(r"\{\{ux\|en\|(?P<sentence>.*)\}", re.MULTILINE)
    sentence2_re = re.compile("#: ''(?P<sentence>.*)''", re.MULTILINE)
    rhyme_re = re.compile(r"=Rhymes=")
    derived_re = re.compile(r"=Derived terms=", re.IGNORECASE)
    user_re = re.compile(r"User:")
    rhyme_page_end_re = re.compile(r"</page>")
    space_clear_re = re.compile(r"\s+", re.MULTILINE | re.S)
    rhyme_pro_re = re.compile(r"\{\{rhymes\|en\|(?P<rhymepro>.*)\}\}", re.MULTILINE | re.S)
    rhyme_page_re = re.compile(r"title>Rhymes:English.(?P<pro>.*?)</title", re.MULTILINE | re.S)
    skip_stuff_re = re.compile(r"Index:|Category:|Appendix:|Wiktionary:|Esperanto|[^A-Z-a-z]+")
    thesaurus_re = re.compile(r"Thesaurus:")
    language_re = re.compile(r"==.+?==")
    rhyme_pronunciation = " "
    sample_sentences = " "
    rhyme_pro = " "
    rhyme_page_content = " "
    etymology = " " 
    rhyme_list = " "
    derived_terms = " "
    skip_page = False
    rhyme_list_flag = False
    text_line_counter = 0
    text_flag = False
    skip_rest_of_page = False
    rhyme_flag = False
    rhyme_page_flag = False
    thesaurus_flag = False
    language = " "
    new_word = True
    derived_flag = False
    language_dict = {
            'en': 'English',
            'enm': 'Middle English',
            'ang': 'Old English',
            'gem-pro': 'Proto-Germanic',
            'ine-pro': 'Proto-Indo-European',
            'sco': 'scots',
            'fy': 'West Frisian',
            'nl': 'Dutch',
            'nds': 'Low German',
            'de': 'German',
            'sv': 'Swedish',
            'is': 'Icelandic',
            'la': 'Latin',
            'ru': 'Russian',
            'hy': 'Armenian',
            'grc': 'Ancient Greek',
            'xno': 'Anglo-Norman',
            'fro': 'Old French',
            'fr': 'French',
            'frm': 'Middle French',
            'ar': 'Arabic',
            'cmn': 'Chinese Mandarin',
            'da': 'Danish',
            'el': 'Greek',
            'he': 'Hebrew',
            'hi': 'Hindi',
            'id': 'Indonesian',
            'il': 'Italian',
            'ko': 'Korean',
            'ms': 'Malay',
            'mn': 'Mongolian',
            'nrf': 'Norman',
            'nb': 'Norweigian',
            'nn': 'Norweigian',
            'fa': 'Persian',
            'pl': 'Polish',
            'pt': 'Portugeuse',
            'ro': 'Romanian',
            'sa': 'Sanskrit',
            'gd': 'Scottish Gaelic',
            'es': 'Spanish',
            'esm': 'Middle Spanish',
            'eso': 'Old Spanish',
            'th': 'Thai',
            'ja': 'Japanese',
            'ca': 'Catalan',
            'fi': 'Finnish',
            
            }
    for line in f:
        if user_re.search(line):
            continue
            
        p = etym_re.search(line)
        n = rhyme_page_re.search(line)
        m = title_re.search(line)
        if p:
            skip_page = False
        if n:
            rhmye_pronunciation = " "
            rhyme_base = n.group('pro')
            rhyme_pronunciation = rhmye_pronunciation.join(rhyme_base)
            rhyme_pronunciation = re.sub(wiki_re," ",rhyme_pronunciation)
            log_message("Processing rhyme " + rhyme_pronunciation + "...")
            rhyme_page_flag = True
            skip_page = True
            rhyme_page_content = " "

              
        elif m:
                 
            word = m.group('word')
            if skip_stuff_re.search(word):
                skip_page = True
                
            else:
                skip_page = False
                skip_rest_of_page = False
                log_message("Processing " + word + "...")
                definition = " "
                synonyms = " "
                antonyms = " "
                rhyme_list = " "
                rhyme_pro = " "
                etymology = " "
                sample_sentences = " "
                part_of_speech = "unknown"
                new_word = True
                syn_flag = False
                ant_flag = False
                rhyme_flag = False
                derived_flag = False
                etym_flag = False
                skip_page = False
                derived_terms = " "
                thesaurus_flag = False
                skip_rest_of_page = False
                language = " "


        else:
            new_word = False
            
        if text_begin_re.search(line) and language_re.search(line):
            language = re.search(r"==(.+?)==",line)
            language = language.group(1)
            text_flag = False        
        elif text_begin_re.search(line):
            text_flag = True
  
        elif text_flag and language_re.search(line):
            language = re.search(r"==(.+?)==",line)
            language = language.group(1)
            text_flag = False
   
        if (translations_re.search(line)):
            skip_rest_of_page = True
        elif (skip_rest_of_page and re.search("==",line)):
            skip_rest_of_page = False
        else:
            pass

            




  
        if not skip_page and not skip_rest_of_page:    
            if thesaurus_re.search(word):
                if (antonym_re.search(line)):
                    syn_flag = False
                    ant_flag = True
                    
                if (syn_flag and re.search(r"==",line)):
                    syn_flag = False

                    
                if (synonym_re.search(line)):
                    syn_flag = True
                    

                if (syn_flag):
                    syns = re.finditer(syn_word_re,line)
                    for syn in syns:
                        temp_syn = re.sub("#+"," ",line)
                        temp_syn = temp_syn.replace("*","")
                        temp_syn = re.sub(r"\{\{(?:.+\|)+(.+?)\}\}",r"*\1*", temp_syn)
                        temp_syn = temp_syn.replace("of|","of ")
                        temp_syn = temp_syn.replace("|of"," of")
                        temp_syn = re.sub(wiki_re," ",temp_syn)
                        temp_syn = re.sub(extra_clear_re,"",temp_syn)
                        while(extra_extra_clear_re.search(temp_syn)):
                            temp_syn = re.sub(extra_extra_clear_re,"",temp_syn)
                        temp_syn = re.sub(text_end_re, " ",temp_syn)
                        temp_syn = temp_syn.replace("\n","")
                        temp_syn = re.sub(symbol_re,"",temp_syn)
                        temp_syn = re.sub(r"^\s*;\s+"," ",temp_syn)
                        temp_syn = re.sub("ref.*?;"," ",temp_syn)
                        temp_syn = re.sub(space_clear_re," ",temp_syn)
                        temp_syn = temp_syn.replace(" ws "," ")
                        temp_syn = re.sub(r"_"," ",temp_syn)
                        temp_syn = re.sub(r"\s+\.",".",temp_syn)
                        temp_syn = re.sub(r"\s+.*?=.*?\s+"," ",temp_syn)
                        temp_syn = temp_syn.replace(" ws "," ")
                        temp_syn = temp_syn.replace("*","")
                        
                        synonyms = synonyms + ", " + temp_syn
                if (ant_flag):
                    ants = re.finditer(ant_word_re,line)
                    for ant in ants:
                        temp_ant = re.sub("#+","",line)
                        temp_ant = temp_ant.replace("*","")
                        temp_ant = re.sub(r"\{\{(?:.+\|)+(.+?)\}\}",r"*\1*", temp_ant)
                        temp_ant = temp_ant.replace("of|","of ")
                        temp_ant = temp_ant.replace("|of"," of")
                        temp_ant = re.sub(wiki_re," ",temp_ant)
                        
                        temp_ant = re.sub(extra_clear_re,"",temp_ant)
                        while(extra_extra_clear_re.search(temp_ant)):
                            temp_ant = re.sub(extra_extra_clear_re,"",temp_ant)
                        temp_ant = re.sub(text_end_re, " ",temp_ant)
                        temp_ant = temp_ant.replace("\n","")
                        temp_ant = re.sub(symbol_re,"",temp_ant)
                        temp_ant = re.sub(r"^\s*;\s+"," ",temp_ant)
                        temp_ant = re.sub("ref.*?;"," ",temp_ant)
                        temp_ant = re.sub(space_clear_re," ",temp_ant)

                        temp_ant = re.sub(r"_"," ",temp_ant)
                        temp_ant = re.sub(r"\s+\.",".",temp_ant)
                        temp_ant = re.sub(r"\s+.+?=.+?\s+"," ",temp_ant)
                        temp_ant = re.sub(r"l\s+","",temp_ant)
                        temp_ant = temp_ant.replace(" ws "," ")
                        temp_ant = temp_ant.replace("*","")
                        antonyms = antonyms + ", " + temp_ant
                if (ant_flag and re.search(r"==",line)):
                    ant_flag = False
                    thesaurus_flag = False
                    create_also_entry = """INSERT INTO SeeAlsoThesaurus (Word, Synonyms, Antonyms) VALUES (%s, %s, %s);"""
                    also_word = word.replace("Thesaurus:","")
                    also_entry = (also_word, synonyms, antonyms)
                    result = commit_sql(create_also_entry, also_entry)
                    if not result:
                        log_message("Database error!")

                    


                
            m = rhyme_pro_re.search(line)
            if m:
                rhyme_pro = m.group('rhymepro')
                
            if (part_of_speech_re.search(line) and not new_word and not def_exclude_re.search(definition) and not skip_rest_of_page and not definition == ' '):
                try:

                    connection = mysql.connector.connect(host='localhost', database='AuthorMaton', user='REDACTED', password='REDACTED')    
                    definition = re.sub(remove_first_separator_re,"",definition)
                    create_dictionary_entry = """INSERT INTO DictionaryDefs (Word, PartOfSpeech, Language, Definitions, Pronunciation) VALUES( %s, %s, %s, %s, %s);"""   
                    dictionary_entry = (word, part_of_speech, language, definition, rhyme_pro)
                    cursor = connection.cursor()
                    result = cursor.execute(create_dictionary_entry, dictionary_entry)
                    connection.commit()
                except mysql.connector.Error as error:
                    await message.channel.send("Database error! " + str(error))   
                finally:
                    if(connection.is_connected()):
                        cursor.close()
                        connection.close()
                
                definition = " "

            if (adj_re.search(line)):
                part_of_speech = "adjective"
                
            if (noun_re.search(line)):
                part_of_speech = "noun"
                
            if (verb_re.search(line)):
                part_of_speech = "verb"
                
            if (adverb_re.search(line)):
                part_of_speech = "adverb"
                
            if (pronoun_re.search(line)):
                part_of_speech = "pronoun"
                
            if (conj_re.search(line)):
                part_of_speech = "conjunction"
                
            if (prep_re.search(line)):
           
                part_of_speech = "preposition"
                
            if (intj_re.search(line)):
                part_of_speech = "interjection"
                
            if etym_flag and re.search(r"==",line):
                etym_flag = False
                
            if etym_flag and not re.search(r"==",line):
                etym_sentence = line
                etym_sentence = re.sub(r"\{\{.+?\|.+?\|","",etym_sentence)
                etym_sentence = re.sub(r"<.*>","",etym_sentence)
                for key in language_dict:
                    etym_sentence = etym_sentence.replace(str(key) + "|",str(language_dict[key]) + " ")
                etym_sentence = re.sub(wiki_re," ",etym_sentence)
                etym_sentence = re.sub(extra_clear_re,"",etym_sentence)
                while(extra_extra_clear_re.search(etym_sentence)):
                    etym_sentence = re.sub(extra_extra_clear_re,"",etym_sentence)
                etym_sentence = re.sub(text_end_re, "",etym_sentence)
                etym_sentence = etym_sentence.replace("\n","")
                etym_sentence = re.sub(symbol_re,"",etym_sentence)
                etym_sentence = re.sub("ref.*?;","",etym_sentence)
                etym_sentence = re.sub(space_clear_re," ",etym_sentence)
                etym_sentence = re.sub(r"_","",etym_sentence)
                etym_sentence = re.sub(r"\s+\.",".",etym_sentence)
                etym_sentence = re.sub(r" .+?=.+ "," ",etym_sentence)
                etymology = etymology + "; " + etym_sentence
                
            if etym_re.search(line):
                etym_flag = True
                

            if derived_flag and re.search("==",line):
                derived_flag = False
     

                
            if derived_flag and (not re.search("==",line)):
                line_formatted = line.replace("*","").replace("#","").replace('\n','').replace('\r','')
                if re.search(r"\{\{.+\|.+\|.+\}\}", line_formatted):
                    terms = re.sub(r"\{\{.+\|.+\|","",line_formatted)
                    terms = terms.replace("}}","")
                elif re.search(r"\[\[.+\|.+\|.+\]\]", line_formatted):
                    terms = re.sub(r"\[\[.+\|.+\|","",line_formatted)
                    terms = terms.replace("]]","")                    
                elif re.search(r"[^\|]",line_formatted):
                    terms = line_formatted.replace("[","").replace("]","").replace("{","").replace("}","")
                elif re.search(r"\{\{(?:.+\|)+.+\}\}",line_formatted):
                    terms = re.findall(r"\|(.+?)\|", line_formatted)
                elif re.search(r"\[\[(?:.+\|)+.+\]\]",line_formatted):
                    terms = re.findall(r"\|(.+?)\|", line_formatted)
                else:
                    pass
                if isinstance(terms, list):
                    for temp_term in terms:
                    
                        temp_term2 = temp_term.replace("|",", ")
                                       
                        derived_terms = derived_terms + ", " + temp_term2.replace(r"\n","")
                else:
                    derived_terms = derived_terms + ", " + terms.replace(r"\n","")
            elif derived_re.search(line):
                derived_flag = True
            else:
                pass
                

                
            m = definition_re.search(line)
            if m and not sample_sentence_re.search(line):
                temp_def = re.sub("#+","",line)
                temp_def = temp_def.replace("<sup>","")
                temp_def = temp_def.replace("</sup>"," ")
                temp_def = temp_def.replace("of|","of ")
                temp_def = temp_def.replace("|of"," of")
                
                temp_def = re.sub(r"\{\{(?:.+\|)+(.+?)\}\}",r"*(\1)*", temp_def)
                temp_def = re.sub(wiki_re," ",temp_def)
                temp_def = temp_def.replace("defdate","")
                temp_def = re.sub(extra_clear_re,"",temp_def)
                while(extra_extra_clear_re.search(temp_def)):
                    temp_def = re.sub(extra_extra_clear_re,"",temp_def)
                temp_def = re.sub(text_end_re, "",temp_def)
                temp_def = temp_def.replace("\n","")
                temp_def = re.sub(symbol_re,"",temp_def)
                temp_def = re.sub("ref.+?;|&.+?;","",temp_def)
                temp_def = re.sub(space_clear_re," ",temp_def)
                temp_def = re.sub(r"_","",temp_def)
                temp_def = re.sub(r"\s+\.",".",temp_def)
                temp_def = re.sub(r"\s+.+?=.+?\s+"," ",temp_def)
                temp_def = temp_def.replace("|","")
                

                definition = definition + "; " + temp_def


            if sentence_re.search(line):
                sentence = sentence_re.search(line).group('sentence')
                sentence = re.sub(wiki_re," ",sentence)
                sentence = re.sub("'''","*",sentence)
                sentence = sentence.replace("\n","")
                sentence = re.sub(space_clear_re," ",sentence)
                sample_sentences = sample_sentences + "; " + sentence
            if (syn_flag and re.search(r"==",line)):
                syn_flag = False

                
            if (synonym_re.search(line)):
                syn_flag = True
                
            if (antonym_re.search(line)):
                syn_flag = False
                ant_flag = True
                
                
            if (syn_flag):
                syns = re.finditer(syn_word_re,line)
                for syn in syns:
                    temp_syn = re.sub("#+"," ",line)
                    temp_syn = temp_syn.replace("*","")
                    temp_syn = re.sub(r"\{\{(?:.+\|)+(.+?)\}\}",r"*\1*", temp_syn)
                    temp_syn = temp_syn.replace("of|","of ")
                    temp_syn = temp_syn.replace("|of"," of")
                    temp_syn = re.sub(wiki_re," ",temp_syn)
                    temp_syn = re.sub(extra_clear_re,"",temp_syn)
                    while(extra_extra_clear_re.search(temp_syn)):
                        temp_syn = re.sub(extra_extra_clear_re,"",temp_syn)
                    temp_syn = re.sub(text_end_re, " ",temp_syn)
                    temp_syn = temp_syn.replace("\n","")
                    temp_syn = re.sub(symbol_re,"",temp_syn)
                    temp_syn = re.sub(r"^\s*;\s+"," ",temp_syn)
                    temp_syn = re.sub("ref.*?;"," ",temp_syn)
                    temp_syn = re.sub(space_clear_re," ",temp_syn)
                    temp_syn = temp_syn.replace(" ws "," ")
                    temp_syn = re.sub(r"_"," ",temp_syn)
                    temp_syn = re.sub(r"\s+\.",".",temp_syn)
                    temp_syn = re.sub(r" .+?=.+? "," ",temp_syn)
                    temp_syn = temp_syn.replace("*","")
                    synonyms = synonyms + ", " + temp_syn
            if (ant_flag):
                ants = re.finditer(ant_word_re,line)
                for ant in ants:
                    temp_ant = re.sub("#+","",line)
                    temp_ant = temp_ant.replace("*","")
                    temp_ant = re.sub(r"\{\{(?:.+\|)+(.+?)\}\}",r"*\1*", temp_ant)
                    temp_ant = temp_ant.replace("of|","of ")
                    temp_ant = temp_ant.replace("|of"," of")
                    temp_ant = re.sub(wiki_re," ",temp_ant)
                    
                    temp_ant = re.sub(extra_clear_re,"",temp_ant)
                    while(extra_extra_clear_re.search(temp_ant)):
                        temp_ant = re.sub(extra_extra_clear_re,"",temp_ant)
                    temp_ant = re.sub(text_end_re, " ",temp_ant)
                    temp_ant = temp_ant.replace("\n","")
                    temp_ant = re.sub(symbol_re,"",temp_ant)
                    temp_ant = re.sub(r"^\s*;\s+"," ",temp_ant)
                    temp_ant = re.sub("ref.*?;"," ",temp_ant)
                    temp_ant = re.sub(space_clear_re," ",temp_ant)
                    temp_ant = temp_ant.replace(" ws "," ")
                    temp_ant = re.sub(r"_"," ",temp_ant)
                    temp_ant = re.sub(r"\s+\.",".",temp_ant)
                    temp_ant = re.sub(r" .+?=.+? "," ",temp_ant)
                    temp_ant = re.sub(r"l\s+","",temp_ant)
                    antonyms = antonyms + ", " + temp_ant
            if (ant_flag and re.search(r"==",line)):
                ant_flag = False

                



            if (rhyme_re.search(line)):
                rhyme_flag = True
                
            if (text_end_re.search(line)):
                rhyme_flag = False
            
            if (rhyme_flag and wiki_re.search(line)):
                rhyme_list = rhyme_list + ", " + line
                rhyme_list = re.sub(wiki_re," ",rhyme_list)
                rhyme_list = re.sub(extra_clear_re,"",rhyme_list)
                while(extra_extra_clear_re.search(rhyme_list)):
                        temp_rhyme = re.sub(extra_extra_clear_re,"",temp_rhyme)
                rhyme_list = re.sub(space_clear_re," ",rhyme_list)
                
            
            if (page_end_re.search(line) and not definition == ' '):
                try:

                    connection = mysql.connector.connect(host='localhost', database='AuthorMaton', user='REDACTED', password='REDACTED')                
                    create_dictionary_entry = """INSERT INTO DictionaryDefs (Word, PartOfSpeech, Language, Definitions, Pronunciation) VALUES(%s, %s, %s, %s, %s);"""   
                    create_thesaurus_entry = """INSERT INTO Thesaurus (Word, Synonyms, Antonyms) VALUES ( %s, %s, %s);"""
                    create_rhyme_entry = """INSERT INTO Rhyming (Word, RhymesWith) VALUES (%s, %s);"""
                    create_sentence_entry = """INSERT INTO SampleSentences (Word, Sentences) VALUES (%s, %s);"""
                    create_etymology_entry = """INSERT INTO Etymology (Word, Etymology) VALUES (%s, %s);"""
                    create_derived_entry = """INSERT INTO DerivedWords (Word, DerivedTerms) VALUES (%s, %s);"""
                    definition = re.sub(remove_first_separator_re,"",definition)
                    synonyms = re.sub(remove_first_separator_re,"",synonyms)
                    antonyms = re.sub(remove_first_separator_re,"",antonyms)
                    rhyme_list = re.sub(remove_first_separator_re,"",rhyme_list)
                    sample_sentences = re.sub(remove_first_separator_re,"",sample_sentences)
                    etymology = re.sub(remove_first_separator_re,"",etymology)
                    derived_terms = re.sub(remove_first_separator_re,"",derived_terms)
                    dictionary_entry = (word, part_of_speech, language, definition, rhyme_pro)
                    thesaurus_entry = (word, synonyms, antonyms)
                    rhyme_entry = (word, rhyme_list)
                    sentences_entry = (word, sample_sentences)
                    etym_entry = (word, etymology)
                    derived_entry = (word, derived_terms)
                    cursor = connection.cursor()
                    result = cursor.execute(create_dictionary_entry, dictionary_entry)
                    result = cursor.execute(create_thesaurus_entry, thesaurus_entry)
                    result = cursor.execute(create_rhyme_entry, rhyme_entry)
                    result = cursor.execute(create_sentence_entry, sentences_entry)
                    result = cursor.execute(create_etymology_entry, etym_entry)
                    result = cursor.execute(create_derived_entry, derived_entry)
                    connection.commit()
                    word_count = word_count + 1
                except mysql.connector.Error as error:
                    log_message("Error: " + str(error))
                    #await message.channel.send("Database error! " + str(error))   
                finally:
                    if(connection.is_connected()):
                        cursor.close()
                        connection.close()

        if rhyme_page_flag:
            if rhyme_re.search(line):
                rhyme_list_flag = True
            
            if rhyme_list_flag and not re.search(r"<.+>",line) and not re.search(r"IPA",line) and not re.search(r"Rhymes:",line):
            
                rhymes = re.search(r"(?:\[\[.+?\]\])|(?:\{\{.+?\}\})",line.replace('*',''))

                if rhymes:
                    
                    temp_rhyme = line.replace('*','')
                    if re.search(r"\|",line):
                        temp_rhyme = re.sub(r"\{\{(?:.+?\|)+(.+?)\}\}",r"\1",temp_rhyme)
                        temp_rhyme = re.sub(r"\[\[(?:.+?\|)+(.+?)\]\]",r"\1",temp_rhyme)
                    temp_rhyme = re.sub(wiki_re," ",temp_rhyme, re.MULTILINE)
                    temp_rhyme = re.sub(extra_clear_re,"",temp_rhyme, re.MULTILINE)
                    temp_rhyme = re.sub(space_clear_re," ",temp_rhyme)
                    temp_rhyme = temp_rhyme.replace(" len","",re.MULTILINE)
                    temp_rhyme = re.sub(r"l ","",temp_rhyme, re.MULTILINE)
                    rhyme_page_content = rhyme_page_content + ", " + temp_rhyme
            
            elif (rhyme_page_end_re.search(line)):
                rhyme_page_flag = False
                rhyme_list_flag = False
                try:
                    rhyme_pronunciation = re.sub("\s+","",rhyme_pronunciation)
                    create_rhyme_entry= """INSERT INTO RhymeWords (Pronunciation, RhymesWith) VALUES (%s, %s);"""
                    rhyme_table_entry = (rhyme_pronunciation, rhyme_page_content)
                    connection = mysql.connector.connect(host='localhost', database='AuthorMaton', user='REDACTED', password='REDACTED')
                    cursor = connection.cursor()
                    result = cursor.execute(create_rhyme_entry, rhyme_table_entry)
                    connection.commit()
                except mysql.connector.Error as error:
                    log_message("error: " + str(error))
                finally:
                    if(connection.is_connected()):
                        cursor.close()
                        connection.close()
                    rhyme_page_flag = False
                    rhyme_page_content = " "
                    rhyme_pronunciation = " "
            else:
                pass
    await send_message(message, "Word load complete! " + str(word_count) + " words loaded!")

    
def admin_check(userid):
    if (userid != 610335542780887050):
        log_message(str(userid) + " tried to call an admin message!")
        return False
    else:
        return True
        
async def show_info(message):
    response = "**This is the Author-Maton bot, the writer help bot!**\n\n*Written by Ninja Nerd*\n\n**Available comamnds:**\n\n>>> ***BASIC COMMANDS***\n\n**.info or .help** this help command\n\n**.sayhi** Say hello!\n\n***LITERATURE COMMANDS***\n\n**.savepost** -title *title* -perm *number* -post *post*: Save a post with the selected title to the database! Supports Discord formatting! Permission = 0 for only you can retrieve it, permissions = 1 for anyone to be able to retrieve it.\n\n**.getpost** *title*: Get a post with the selected title\n\n**.wordcount** *post* Get the number of words in the post.\n\n**.writingprompt** Get a randomized scenario to write about! If it doesn't make sense, try another one!\n\n"
    await message.channel.send(response)
    time.sleep(3)
    response = ">>> ***DICTIONARY AND THESAURUS COMMANDS***\n\n**.define** *word or phrase* Look in the dictionary database for a word definition.\n\n**.definelike** *word or phrase*  Find words that contain the text and print their definitions.\n\n**.synonyms** *word or phrase* Get words that mean similarly to this word.\n\n**.antonyms** *word or phrase* Get words that mean the opposite of this word.\n\n**.rhymes** *word or phrase* Get words that rhyme with this one.\n\n**.sentences** *word or phrase* Use this word in a sentence.\n\n**.derivedterms** *word or phrase* See other words and phrases based on this one.\n\n**.slang** *word or phrase* Get the first definition on UrbanDictionary for this word.\n\n.**randomslang** *word or phrase* Get a random definition from UrbanDictionary for this word.\n\n**.translate** *language* *word* Search the dictionary for an English word in the specified language.\n\n"
    await message.channel.send(response)
    time.sleep(3)
    response = ">>> ***POETRY TAG COMMANDS***\n\n**.poetrytag** *user mentions* -topic *topic* -mode *mode*\nStart a poetry tag on your server. Mention the users participating, then specify a topic and mode. Any topic is valid, but specifiying *random* will pick a topic from the database. Valid modes are *tag*, where each poet writes an entire poem, and *tandem* where each poet writes one line.\n\n**.tag** *post* Submit your poem or line for poetry tag.\n\n**.finishtag** Stop the poetry tag and print the tandem poem if in tandem mode. Poems can be saved using .savepost.\n\n"
    await message.channel.send(response)
    time.sleep(3)
    response = ">>> ***QUIZ COMMANDS***\n\n**.quiz** Get a random definition from the database and the first one to answer with **.answer** *word or phrase* gets it right!\n\n**.answer** *word or phrase* Answer a quiz question.\n\n**.hint** Get a hint for the quiz word.\n\n**.myscore** See your current score.\n\n**.leaderboard** See the current server scoreboard.\n\n"
    await message.channel.send(response)
    time.sleep(3)
    response = ">>> ***WORD SEARCH COMMANDS***\n\n**.randomword** *minimum score* Get a random word and definition from the dictionary. Specifiy the minimum word score, or leave it blank for any score.\n\n**.wordsearch** *start letter*    *number of letters between*   *end letter* Search the dictionary for words starting and ending with the specified letters and the specified number of letters in between.\n\n**.wordpattern** *pattern*\nFind all words with the specified pattern. Represent unknown lettters as underscores (_) and known letters with their letter.\n\n**.wordscore** *word or phrase* Get the calculated word score for the specified word in the dictionary.\n\n**.wordoftheday** Get a word of the day from the dictionary with a score higher than the set limit."
    await message.channel.send(response)


@client.event
async def on_ready():
    global quiz_scores
    global quiz_event
    global poetry_tag_event
    global poetry_tag_users
    global poetry_tag_topic
    global poetry_tag_mode

    log_message("Logged in!")
    for guild in client.guilds:
        quiz_event[guild.id] = False
        poetry_tag_event[guild.id] = False
        
            
@client.event
async def on_guild_join(guild):
    global quiz_event
    log_message("Joined guild " + guild.name)
    quiz_event[guild.id] = False
    log_message("Creating leaderboard...")
    for member in guild.members:
        try:
            connection = mysql.connector.connect(host='localhost', database='AuthorMaton', user='REDACTED', password='REDACTED')    
            create_score_entry = """INSERT INTO QuizScores (ServerId, UserId, Score) VALUES(%s, %s, %s);"""   
            score_entry = (str(guild.id), str(member.id), str(0))
            cursor = connection.cursor()
            result = cursor.execute(create_score_entry, score_entry)
            connection.commit()
        except mysql.connector.Error as error:
            await message.channel.send("Database error! " + str(error))   
        finally:
            if(connection.is_connected()):
                cursor.close()
                connection.close()
    log_message("Done!")
   
@client.event
async def on_message(message):
    global word_of_the_day_score
    global quiz_answer
    global quiz_event
    global quiz_scores
    global entry_limit
    global poetry_tag_event
    global poetry_tag_users
    global poetry_tag_topic
    global poetry_tag_mode
    global poetry_tag_current_user
    global poetry_tag_tandem_poem

    if message.author == client.user:
        return

            
    if message.content.startswith('.'):

        command_string = message.content.split(' ')
        command = command_string[0].replace('.','')
        parsed_string = message.content.replace("." + command + " ","")
        username = message.author.name
        server_name = message.guild.name

        log_message("Command " + message.content + " called by " + username + " from " + server_name)
        if (command == 'sayhi'):
            await message.channel.send("Hello there, " + username + "!")
                
        elif (command == 'info' or command == 'help'):
            await show_info(message)
            
        elif (command == 'initialize'):
            if not admin_check(message.author.id):
                await send_message("Admin command only!")
                return
            await send_message(message, "Dropping databases...")
                
            result = execute_sql("""DROP TABLE IF EXISTS Literature; DROP TABLE IF EXISTS DictionaryDefs; DROP TABLE IF EXISTS Thesaurus; DROP TABLE IF EXISTS Rhyming; DROP TABLE IF EXISTS RhymeWords; DROP TABLE IF EXISTS SampleSentences; DROP TABLE IF EXISTS Etymology; DROP TABLE IF EXISTS DerivedWords; DROP TABLE IF EXISTS SeeAlsoThesaurus;""")
            if result:    
                await send_message(message, "Databases all cleared successfully.")
            else:    
                await send_message(message, "Database error!")   
                
            await send_message(message, "Creating databases...")
               
            result = execute_sql("""CREATE TABLE Literature (Id int auto_increment, Title varchar(400), Author varchar(100), Permissions int, PostContent varchar(1900), PRIMARY KEY (Id));""")
            if not result:
                await send_message(message, "Database error creating Literature database!")
            
            result = execute_sql("""CREATE TABLE DictionaryDefs (Id int auto_increment, Word varchar(300), PartOfSpeech varchar(30), Language varchar(70), Definitions TEXT, Pronunciation varchar(100), PRIMARY KEY (Id));""")
            
            if not result:
                await send_message(message, "Database error creating DictionaryDefs database!")
                
            result = execute_sql("""CREATE TABLE Thesaurus (Id int auto_increment, Word varchar(300), Synonyms TEXT, Antonyms TEXT, PRIMARY KEY (Id));""")
            if not result:
                await send_message(message, "Database error creating Thesaurus database!")
                
            result = execute_sql("""CREATE TABLE Rhyming (Id int auto_increment, Word varchar(300), RhymesWith varchar(4000), PRIMARY KEY (Id));""")
            if not result:
                await send_message(message, "Database error creating Literature database!")
                
            result = execute_sql("""CREATE TABLE RhymeWords (Id int auto_increment, Pronunciation varchar(500), RhymesWith varchar(10000), PRIMARY KEY (Id));""")
            if not result:
                await send_message(message, "Database error creating Literature database!")
                
            result = execute_sql("""CREATE TABLE SampleSentences (Id int auto_increment, Word varchar(300), Sentences varchar(10000), PRIMARY KEY (Id));""")
            if not result:
                await send_message(message, "Database error creating Literature database!")
              
            result = execute_sql("""CREATE TABLE Etymology (Id int auto_increment, Word varchar(300), Etymology varchar(10000), PRIMARY KEY (Id));""")
            if not result:
                await send_message(message, "Database error creating Literature database!")
                
            result = execute_sql("""CREATE TABLE DerivedWords (Id int auto_increment, Word varchar(300), DerivedTerms TEXT, PRIMARY KEY (Id));""")
            if not result:
                await send_message(message, "Database error creating Literature database!")
            result = execute_sql("""CREATE TABLE SeeAlsoThesaurus (Id Int auto_increment, Word varchar(300), Synonyms TEXT, Antonyms TEXT, PRIMARY KEY (Id));""")
            if not result:
                await send_message(message, "Database error creating SeeAlso Database!")
                
            if result:    
                await send_message(message, "Database created successfully.")
        elif(command == 'writingprompt'):
            response = " "
            records = select_sql("""SELECT WritingPromptText FROM WritingPromptTexts ORDER BY RAND( ) LIMIT 1;""")
            for row in records:
                tokenized_prompt = str(row[0]).split(" ")

            for token in tokenized_prompt:
                log_message("Token: " + token)
                if re.search(r"-(.+?)-",token):
                    search_term = re.sub(r"[^A-Za-z]","",token, re.S | re.MULTILINE)
                    search_term = search_term.strip()
                    log_message("Search term: " + search_term)
                    if (search_term == 'Characters'):
                        search_term_2 = search_term
                    else:
                        search_term_2 = search_term.replace("s","")
                    get_blank = """SELECT """ + search_term_2 + """ FROM """ + search_term + """ ORDER BY RAND( ) LIMIT 1;"""
                    blank_records = select_sql(get_blank)
                    for blank_row in blank_records:
                        response = response + " " + re.sub("[^A-Za-z\s/]","",str(blank_row),re.S)
                else:
                    response = response + " " + re.sub(r"[^A-Za-z\s/]","",str(token), re.S)
            await send_message(message, "**WRITING PROMPT:**\n\n " + response)

        elif (command == "savepost"):
            title_re = re.compile("-title (.*) -perm", re.MULTILINE | re.S)
            post_re = re.compile("-post (.*)", re.MULTILINE | re.S)
            perm_re = re.compile("-perm (\d)", re.MULTILINE | re.S)
            
            m = title_re.search(parsed_string)
            if not m:
                await send_message(message, "No title tag specified!")
                return
            title = m.group()
            title = title.replace("-title ","")
            title = title.replace("-perm","")
            title = title.strip()
            
            
            m = perm_re.search(parsed_string)
            perm = m.group()
            perm = perm.replace("-perm ","")
            
            m = post_re.search(parsed_string)
            if not m:
                await send_message(message, "No post specified!")
                return
                
            post = m.group()
            post = post.replace("-post ","")
            
            author = message.author.id
            
            log_message("Title: " + title + "\nAuthor: " + str(author) + "\n Post Content: " + post)
            
            save_post_query = """INSERT INTO Literature (Title, Author, Permissions, PostContent) VALUES (%s, %s, %s, %s);"""
            post_to_save = (title, str(author), perm, post)
            result = commit_sql(save_post_query, post_to_save)
            if result:
                await send_message(message, "Post " + str(title) + " saved successfully.")
            else:
                await send_message(message, "Database error!")
        
        elif (command == 'getpost'):
            parsed_string = parsed_string.replace("-title ","").strip()
            log_message("Title: " + parsed_string)
            
            get_post_query = """SELECT Title,Author,PostContent,Permissions FROM Literature WHERE Title=%s;"""
            records = select_sql(get_post_query, (parsed_string,))
            
            for row in records:
                author_name = get(client.get_all_members(), id=int(row[1]))
                if (row[3] == 0 and message.author.id != row[1]):
                    await send_message(message, "This author has not granted permission for this post to be retrieved.")
                    return                        
                else:
                    await send_message(message, "**" + str(row[0]) + "**\n*By " + author_name.name + "*\n\n" + row[2])

        elif (command == 'resetliterature'):
            if not admin_check(message.author.id):
                await send_message("Admin command only!")
                return
            clear_all_query = """DROP TABLE IF EXISTS Literature; CREATE TABLE Literature (Id int auto_increment, Title varchar(400), Author varchar(100), Permissions int, PostContent varchar(1900), PRIMARY KEY (Id));"""
            result = execute_sql(clear_all_query)
            if result:
                await send_message(message, "Database created successfully.")
            else:
                await send_message(message, "Database error!")

        elif (command == 'rhymes'):
            if not parsed_string:
                await send_message(message, "No word specified!")
                return
            
            get_rhyme_list = """SELECT RhymesWith FROM Rhyming WHERE Word=%s AND RhymesWith!=' ';"""
            get_rhyme_entry = """SELECT RhymesWith FROM RhymeWords WHERE Pronunciation IN (SELECT Pronunciation FROM DictionaryDefs WHERE Word=%s);"""
            get_rhyme_pro_list = False
            async with message.channel.typing():
                records = select_sql(get_rhyme_list,(parsed_string,))
            response = " "
            if len(records) > 0:
                for row in records:
                    if not (re.search(r"Category:",row) and re.search(r"English:",row)):
                        response = response + ", " + str(row[0]) + "\n\n"
            async with message.channel.typing():            
                records = select_sql(get_rhyme_entry, (parsed_string,))
            if len(records) == 0:
                await send_message(message, "No rhymes found for " + parsed_string)
                return
            response = response + "\n\n**" + parsed_string + "** *Rhymes with*\n\n"
            for row in records:
                response = response + " " + str(row[0]) + "\n\n"

            await send_message(message, response)
        elif (command == 'define'):
            if parsed_string == "":
                await send_message(message, "No word specified!")
                return
            get_dictionary_entry = """SELECT DISTINCT Language,PartOfSpeech,Definitions FROM DictionaryDefs WHERE Word=%s AND Definitions !=' ';"""
            if (entry_limit > 0):
                get_dictionary_entry = get_dictionary_entry.replace(";"," LIMIT " + str(entry_limit) + ";")
            async with message.channel.typing():
                records = select_sql(get_dictionary_entry, (parsed_string,))
            if len(records) == 0:
                await send_message(message, "No definitions found for " + parsed_string)
                return
            response = "**" + parsed_string + "**\n\n "
            for row in records:
                response = response + "(" + str(row[0]) + ") *" + row[1] + "*  " + row[2] + "\n\n"
                
            await send_message(message, response)
        elif (command == 'randomword'):
            if not parsed_string:
                parsed_string = "0"
            acceptable_word = False
            async with message.channel.typing():
                while not acceptable_word:
                    records = select_sql(get_word_of_the_day,(parsed_string,))
                    for row in records:
                        word = row[0]
                    get_word_based_on_score = """SELECT Word,PartOfSpeech,Definitions FROM DictionaryDefs WHERE Word=%s;"""
                    records = select_sql(get_word_based_on_score, (word,))
                    if len(records) > 0 and not re.search(r"past|future|form|plural|singular|^\(.*\)$",row[2]):
                        response = "**Random word:**\n\n**"
                        for row in records:
                            response = response + str(row[0]) + "** *" + row[1] + "*\n\n" + row[2] + "\n\n"
                            
                            await send_message(message, response)
                            acceptable_word = True

        elif (command == 'definelike'):

            parsed_string = "%" + parsed_string + "%"
            if parsed_string == "":
                await send_message(message, "No word specified!")
                return
            get_dictionary_entry = """SELECT DISTINCT Word,PartOfSpeech,Definitions FROM DictionaryDefs WHERE Word LIKE %s AND Definitions !=' ';"""
            if (entry_limit > 0):
                get_dictionary_entry = get_dictionary_entry.replace(";"," LIMIT " + str(entry_limit) + ";")
                async with message.channel.typing():
                    records = select_sql(get_dictionary_entry, (parsed_string,))
                if len(records) == 0:
                    await send_message(message, "No words found that matched " + parsed_string.replace('%',''))
                    return
                response = "**" + parsed_string.replace('%','') + "**\n\n"
                for row in records:
                    response = response + "**" + str(row[0]) + "** *" + row[1] + "* " + row[2] + "\n\n"
                
                await send_message(message, response)
            
        elif (command == 'synonyms'):
            if parsed_string == "":
                await send_message(message, "No word specified!")
                return

            get_synonym_entry = """SELECT Synonyms FROM Thesaurus WHERE Word=%s AND Synonyms != ' ';"""
            async with message.channel.typing():
                records = select_sql(get_synonym_entry, (parsed_string,))
            if len(records) == 0:
                await send_message(message, "No synonyms found for " + parsed_string)
                return
            response = "**" + parsed_string + "** *Synonyms*\n\n "
            for row in records:
                response = response + str(row[0]) + "\n\n"
            if re.search(r"Thesaurus:.+ ,", response, re.MULTILINE | re.S | re.IGNORECASE):
                m = re.search(r"Thesaurus:([\w\s]+?) ,.*", response.replace("*",""), re.MULTILINE | re.S | re.IGNORECASE)
                if m:
                    word = m.group(1)
                log_message("See also: " + word)
                see_also_records = select_sql("""SELECT Synonyms FROM SeeAlsoThesaurus WHERE Word=%s;""", (word,))
                more_syns = " "
                for also_record in see_also_records:
                    log_message(str(also_record))
                    more_syns = more_syns + ", " + str(also_record)
                response = re.sub(r" .*?see.*? Thesaurus:.+? ,",more_syns,response, re.MULTILINE | re.S | re.IGNORECASE)
            response = response.replace(" ws ","")
            await send_message(message, response)
           
        elif (command == 'antonyms'):
            if parsed_string == "":
                await send_message("No word specified!")
                return
            get_antonym_entry = """SELECT Antonyms FROM Thesaurus WHERE Word=%s AND Antonyms != ' ';"""
            async with message.channel.typing():
                records = select_sql(get_antonym_entry, (parsed_string,))
            if len(records) == 0:
                await send_message(message, "No antonyms found for " + parsed_string)
                return
            response = "**" + parsed_string + "** *Antonyms*\n\n"
            for row in records:
                response = response + str(row[0]) + "\n\n"
            if re.search(r"Thesaurus:.+ ,", response, re.MULTILINE | re.S | re.IGNORECASE):
                m = re.search(r"Thesaurus:([\w\s]+?) ,.*", response.replace("*",""), re.MULTILINE | re.S | re.IGNORECASE)
                if m:
                    word = m.group(1)
                log_message("See also: " + word)
                async with message.channel.typing():
                    see_also_records = select_sql("""SELECT Antonyms FROM SeeAlsoThesaurus WHERE Word=%s;""", (word,))
                more_syns = " "
                for also_record in see_also_records:
                    log_message(str(also_record))
                    more_syns = more_syns + ", " + str(also_record)
                response = re.sub(r" .*?see.*? Thesaurus:.+? ,",more_syns,response, re.MULTILINE | re.S | re.IGNORECASE)
            response = response.replace(" ws ","")
            await send_message(message, response)

        elif (command == 'derivedterms'):
            if parsed_string == "":
                await send_message(message, "No word specified!")
                return
            get_derived_entry = """SELECT DerivedTerms FROM DerivedWords WHERE Word=%s AND DerivedTerms != ' ';"""
            async with message.channel.typing():
                records = select_sql(get_derived_entry,(parsed_string,))
            if len(records) == 0:
                await send_message(message,"No derived terms found for " + parsed_string)
                return
            response = "**" + parsed_string + "** *Derived Terms*\n\n"
            for row in records:
                response = response + str(row[0]) + "\n\n"
            await send_message(message, response)    

        elif (command == 'randomslang'):

            if (message.channel.nsfw):
                word = parsed_string
                if not word:
                    await send_message(message,"No word specified!")
                    return
                
                URL = "http://api.urbandictionary.com/v0/define?term=" + word
                r = requests.get(url = URL)
                data = r.json()
                
                if not data:
                    await send_message(message, "No slang definition found for " + word)
                    return
                
                definition = data["list"][random.randint(0,len(data["list"])-1)]["definition"]
                definition = definition.replace("[","")
                definition = definition.replace(']',"")
                
                await send_message(message, "**" + word + "**\n\n" + definition)
            else:
                await send_message(message, "This is not a NSFW channel. Please issue slang commands in a NSFW channel.")
        elif (command == 'sentences'):

            get_sentences = """SELECT Sentences FROM SampleSentences WHERE Word=%s AND Sentences IS NOT NULL;"""
            async with message.channel.typing():
                records = select_sql(get_sentences, (parsed_string,))

            if len(records) == 0:
                await send_message(message, "No sample sentences found for " + parsed_string)
                return
            response = "**" + parsed_string + "** *Used in a sentence*\n\n"
            for row in records:
                response = response + str(row[0]) + "\n\n"
                
            await send_message(message, response)

                
        elif (command == 'slang'):
            if(message.channel.nsfw):
                word = message.content.replace(".slang ","")
                if not word:
                    await send_message(message, "No word specified!")
                    return
                
                URL = "http://api.urbandictionary.com/v0/define?term=" + word
                r = requests.get(url = URL)
                data = r.json()
                if not data:
                    await send_message(message, "No definition found for " +word)
                    return
                
                definition = data["list"][0]["definition"]
                definition = definition.replace("[","")
                definition = definition.replace(']',"")
                
                await send_message(message, "**" + word + "**\n\n" + definition)
            else:
                await send_message(message, "This is not a NSFW channel. Please issue slang commands in a NSFW channel.")            
 
        elif (command == 'quiz'):
            async with message.channel.typing():
                acceptable_word = False
                while not acceptable_word:
                    get_dictionary_entry = """SELECT Word,PartOfSpeech,Definitions FROM DictionaryDefs WHERE Definitions !=' ' AND Language='English' ORDER BY RAND( ) LIMIT 1;"""
                    quiz_event[message.guild.id] = True
                    records = select_sql(get_dictionary_entry)
                    for row in records:
                        if not re.search(r"plural|singular|past|future|^\(.*\)$|(?:\(.*\);)+", row[2]):
                            acceptable_word = True
                part_of_speech = " "
                question = " "
                response = "What word is a "
                for row in records:
                    question = row[2]
                    part_of_speech = row[1]
                quiz_answer[message.guild.id] = row[0]
                response = response + part_of_speech + " and means " + question.lower().replace(quiz_answer[message.guild.id],"----")
                await send_message(message, response)

        elif (command == 'answer'):

            quiz_score = 0
            if not quiz_event[message.guild.id]:
                await send_message(message, "No quiz currently active! Type **.quiz** to start a word quiz.\n")
                return    
            if (quiz_answer[message.guild.id].lower() == parsed_string.lower()):
                await send_message(message, "Yes, the answer was " + str(quiz_answer[message.guild.id]) + "! Correct!")
                id_num = message.author.id
                guild_id = message.guild.id
                get_current_score = """SELECT Score FROM QuizScores WHERE ServerId=%s AND UserId=%s;"""
                records = select_sql(get_current_score, (str(guild_id), str(id_num)))
                if len(records) == 0:
                    await send_message(message, "No score found for the specified user.")
                    return
                for row in records:
                    quiz_score = int(row[0])
                                  
                quiz_score = quiz_score + 1
                await send_message(message, "Your new quiz score is **"  + str(quiz_score) + "**.")
  
                update_score_entry = """UPDATE QuizScores Set Score=%s WHERE ServerId=%s AND UserId=%s;"""   
                score_entry = (str(quiz_score), str(guild_id), str(id_num))

                result = commit_sql(update_score_entry, score_entry)
                if not result:
                    await send_message(message, "Database error! " + str(error))   
            
            else:
                await send_message(message, "Sorry, the answer was " + str(quiz_answer[message.guild.id]) + ".")
            quiz_event[message.guild.id] = False
            quiz_answer[message.guild.id] = " "
            
        elif (command == 'myscore'):
            my_id = message.author.id
            guild_id = message.guild.id
            get_my_score = """SELECT Score FROM QuizScores WHERE ServerId=%s AND UserId=%s;"""
            async with message.channel.typing():
                records = select_sql(get_my_score, (str(guild_id), str(my_id)))
            if len(records) == 0:
                await send_message(message, "No score found for the specified user.")
                return
            response = "Your current quiz score is **"
            for row in records:
                score = str(row[0])
            response = response + score + "**."
            await send_message(message, response)
        elif (command == 'leaderboard'):
            get_leaderboard = """SELECT UserId,Score FROM QuizScores WHERE ServerId=%s ORDER BY Score DESC;"""
            guild_id = message.guild.id
            async with message.channel.typing():
                records = select_sql(get_leaderboard, (str(guild_id),))

            if len(records) == 0:
                await send_message(message, "No score found for the specified server.")
                return
            response = "**Quiz Leaderboard:**\n\n"
            for row in records:
                username = get(client.get_all_members(), id=int(row[0]))
                response = response + str(username.name) + " - " + str(row[1]) + "\n"
            await send_message(message, response)
            
        elif (command == 'hint'):

            if not quiz_event[message.guild.id]:
                await send_message(message, "No quiz currently active! Type **.quiz** to start a word quiz.\n")
            hint = quiz_answer[message.guild.id][0]
            letters = len(quiz_answer[message.guild.id])
            await send_message(message, "The first letter of the word is " + hint + " and it has " + str(letters) + " letters.")
            
        elif (command == 'wordcount'):
            if not parsed_string:
                await send_message(message, "No words to count!")
                return
            words_in_post = parsed_string.split()
            word_count = len(words_in_post)
            await send_message(message, "The word count is " + str(word_count) + ".")

        elif (command == 'restartbot'):

            if not admin_check(message.author.id):
                await send_message(message, "Admin command only!")
                return
            await send_message(message, "Restarting bot...")
            output = subprocess.run(["/home/REDACTED/restartbot.sh"], universal_newlines=True, stdout=subprocess.PIPE)

        elif (command == 'wordsearch'):

            start_letter = command_string[1]
            number_of_letters = command_string[2]
            end_letter = command_string[3]
            
            if not start_letter:
                await send_message(message, "No start letter specified!")
                return
            if not number_of_letters:
                await send_message(message, "No number of letters specified!")
                return
            if not end_letter:
                await send_message(message, "No end letters specified!")
                return
            word_search_query = """SELECT Word FROM DictionaryDefs WHERE Word LIKE %s AND Langage='English';"""
            if (entry_limit > 0):
                word_search_query = word_search_query.replace(";"," LIMIT " + str(entry_limit) + ";")
            word_pattern = start_letter
            for i in range(int(number_of_letters)):
                word_pattern = word_pattern + "_"
            word_pattern = word_pattern + end_letter

            async with message.channel.typing():
                records = select_sql(word_search_query, (word_pattern,))

            if len(records) == 0:
                await send_message(message, "No words found for the specified patern.")
                return
            response = "**Words that start with " + start_letter + ", end with " +end_letter + ", with " + number_of_letters + " in between:**\n\n"
            for row in records:
                response = response + str(row[0]) + ", "
                
            await send_message(message, response)

        elif (command == 'wordpattern'):

            parsed_string = parsed_string.replace(" ","")
            
            if not parsed_string:
                await send_message(message, "No pattern specified!")
                return
            
            word_pattern_query = """SELECT Word FROM DictionaryDefs WHERE Word LIKE %s and Language='English';"""
            if (entry_limit > 0):
                word_pattern_query = word_pattern_query.replace(";"," LIMIT " + str(entry_limit) + ";")
                async with message.channel.typing():
                    records = select_sql(word_pattern_query, (parsed_string,))

            if len(records) == 0:
                await send_message(message, "No words found for the specified patern.")
                return
            response = "**Words that have the pattern " + parsed_string + ":**\n\n"
            for row in records:
                response = response + str(row[0]) + ", "
                
            await send_message(message, response)
            
        elif (command == 'etymology'):

            get_etymology = """SELECT DISTINCT Etymology FROM Etymology WHERE Word=%s;"""
            if not parsed_string:
                await send_message(message, "No word specified!")
                return
            async with message.channel.typing():
                records = select_sql(get_etymology, (parsed_string,))

            if len(records) == 0:
                await send_message(message, "No etymology found for the specified word.")
                return
            response = "**ETYMOLOGY**\n\n*" + parsed_string + "*\n\n"
            for row in records:
                response = response + str(row[0]) + "; "
             
            await send_message(message, response)

        elif (command == 'wordscore'):

            get_word_score = """SELECT WordValue FROM WordValues WHERE Word=%s LIMIT 1;"""
            async with message.channel.typing():
                records = select_sql(get_word_score, (parsed_string,))
            if len(records) == 0:
                await send_message(message, "No score found for the specified word.")
                return
            response = "The word score of **" + parsed_string + "** is ```"
            for row in records:
                response = response + str(row[0]) + "```"
                
            await send_message(message, response)
        elif (command == 'setminscore'):
            if not admin_check(message.author.id):
                await send_message(message, "Admin command only!")
                return
            word_of_the_day_score = int(message.content.replace('.setminscore ',""))
            await send_message(message, "Word of the day score minimum set to " + str(word_of_the_day_score))
            
        elif (command == 'wordoftheday'):
            async with message.channel.typing():
                get_word_of_the_day = """SELECT Word FROM WordValues WHERE WordValue>=%s ORDER BY RAND( ) LIMIT 1;"""

                records = select_sql(get_word_of_the_day, (word_of_the_day_score,))
                for row in records:
                    word = row[0]
                get_word_based_on_score = """SELECT Word,PartOfSpeech,Definitions FROM DictionaryDefs WHERE (Word=%s AND Definitions !=' ') LIMIT 1;"""
                records = select_sql(get_word_based_on_score, (word,))

                if len(records) > 0:
                    response = "**WORD OF THE DAY**\n\nThe word of the day is **"
                    for row in records:
                        response = response + str(row[0]) + "** *" + row[1] + "*\n\n" + row[2] + "\n\n"
                        
                    await send_message(message, response)
                else:
                    await send_message(message, "Database error.")

        elif (command == 'resetscores'):
            set_score_to_zero = """UPDATE QuizScores Set Score=0 WHERE ServerId=%s;"""
            server_id = message.guild.id
            result = commit_sql(set_score_to_zero, (server_id,))
            if result:
                await send_message(message, "Leaderboard reset to zero for all members.")
            else:
                await send_message(message, "Database error!")
            
        elif (command == 'initializeleaderboard'):
            if not admin_check(message.author.id):
                await send_message(message, "Admin command only!")
                return
            result = execute_sql("""DROP TABLE IF EXISTS QuizScores; CREATE TABLE QuizScores (ServerId VarChar(40), UserId VarChar(30), Score Int);""")
            if not result:
                await send_message(message,"Could not create Quiz Scores!")
            for guild in client.guilds:
                for member in guild.members:
                    create_score_entry = """INSERT INTO QuizScores (ServerId, UserId, Score) VALUES(%s, %s, %s);"""   
                    score_entry = (str(guild.id), str(member.id), str(0))
                    result = commit_sql(create_score_entry, score_entry)
                    if not result:
                        await send_message(message, "Database error!")   

            await send_message(message, "Leaderboard initialized.") 
                        
        elif (command == 'calculatevalues'):

            if not admin_check(message.author.id):
                await send_message(message, "Admin command only!")
                return
            word_scores = {}   
            await send_message(message, "Calculating word values. Bot will be unavailable until word values calculated.")
            get_all_words_query = """SELECT Word,Definitions FROM DictionaryDefs WHERE Language='English';"""
            records = select_sql(get_all_words_query)
            letter_values = { "E" : 1, "A" : 1, "I" : 1, "O" : 1, "N" : 1, "R" : 1, "T" : 1, "L" : 1, "S" : 1, "U" : 1, "D" : 2, "G" : 2, "B" : 3, "C" : 2, "M" : 3, "P" : 2, "F" : 4, "H" : 4, "V" : 4, "W" : 4, "Y" : 4, "K" : 5, "J" : 8, "X" : 8, "Q" : 10, "Z" : 10, "-": 0, " " : 0, "'": 0, "À": 1,"Â":1, "Ä":1, "È":1, "Ê":1, "Ì":1, "É":1, "Í":1, "Î":1, "Ò":1, "Ô":1, "Ó":1, "Õ":1, "Ø":1, "Ù":1, "Û":1, "Ü":1, "Ú": 1, "Ã": 1, "Ï": 1, "Ñ": 2, "Ç": 2, "Á": 1, ".":0, ":":0, ",":0, "`":0, "?":0, "Ö": 1, "Å": 1, "Ń": 2, "Ā": 1, "1": 1, "2": 1, "3":1, "4":1, "5":1, "6":1, "7":1, "8":1, "9":1, "0":1, "Æ": 2, "ʻ":0, "Œ":2, "/":0, "\\":0, "<": 0, ">":0, "ǃ":0, "Ū": 1, '*':0, '+':0, "Ł": 2, "Ź":10, "Č":2, "Ć": 2, "Ë": 1, "Α":1, '£':2, "Ể":1, '&': 0, ';':0, "Ō": 1, '!':0, "Ő":1, "Þ": 2, "Ð": 2, "Ș": 2, '♨':30, "Ộ": 1, "Ý": 1,"Þ": 1,"ß": 1,"Ă": 1,"Ą": 1,"Ć": 1,"Ĉ": 1,"Ċ": 1,"Č": 1,"Ď": 1,"Ē": 1,"Ĕ": 1,"Ė": 1,"Ę": 1,"Ě": 1,"Ĝ": 1,"Ġ": 1,"Ģ": 1,"Ĥ": 1,"Ħ": 1,"Ĩ": 1,"Ī": 1,"Ĭ": 1,"Į": 1,"İ": 1,"Ĳ": 1,"Ĵ": 1,"Ķ": 1,"Ĺ": 1,"Ļ": 1,"Ľ": 1,"Ŀ": 1,"Ł": 1,"Ń": 1,"Ņ": 1,"Ň": 1,"Ŋ": 1,"Ō": 1,"Ŏ": 1,"Ő": 1,"Œ": 1,"Ŕ": 1,"Ŗ": 1,"Ř": 1,"Ś": 1,"Ŝ": 1,"Ş": 1,"Š": 1,"Ţ": 1,"Ť": 1,"Ŧ": 1,"Ũ": 1,"Ū": 1,"Ŭ": 1,"Ů": 1,"Ű": 1,"Ų": 1,"Ŵ": 1,"Ŷ": 1,"Ÿ": 1,"Ż": 1,"Ź": 1,"Ž": 1,"Ɓ": 1,"Ƈ": 1,"Ƌ": 1,"Ə": 1,"Ƒ": 1,"Ɠ": 1,"Ɨ": 1,"Ɯ": 1,"Ɲ": 1,"Ɵ": 1,"Ƣ": 1,"Ƥ": 1,"Ʀ": 1,"Ƨ": 1,"Ʃ": 1,"ƪ": 1,"Ƭ": 1,"Ʈ": 1,"Ư": 1,"Ʊ": 1,"Ʋ": 1,"Ƴ": 1,"Ƶ": 1,"Ʒ": 1,"Ƹ": 1,"ƻ": 1,"Ƽ": 1,"ƾ": 1,"ƿ": 1,"ǀ": 1,"ǁ": 1,"ǂ": 1,"ǃ": 1,"Ǆ": 1,"ǅ": 1,"Ǉ": 1,"Ǌ": 1,"Ǎ": 1,"Ǐ": 1,"Ǒ": 1,"Ǔ": 1,"Ǖ": 1,"Ǘ": 1,"Ǚ": 1,"Ǜ": 1,"Ǟ": 1,"Ǡ": 1,"Ǣ": 1,"Ǥ": 1,"Ǧ": 1,"Ǩ": 1,"Ǫ": 1,"Ǭ": 1,"Ǯ": 1,"Ǳ": 1,"Ǵ": 1,"Ǻ": 1,"Ǽ": 1,"Ǿ": 1,"Ȁ": 1,"Ȃ": 1,"Ȅ": 1,"Ȇ": 1,"Ȉ": 1,"Ȋ": 1,"Ȍ": 1,"Ȏ": 1,"Ȑ": 1,"Ȓ": 1,"Ȕ": 1,"Ȗ": 1,"Ḁ": 1,"Ḃ": 1,"Ḅ": 1,"Ḇ": 1,"Ḉ": 1,"Ḋ": 1,"Ḍ": 1,"Ḏ": 1,"Ḑ": 1,"Ḓ": 1,"Ḕ": 1,"Ḗ": 1,"Ḙ": 1,"Ḛ": 1,"Ḝ": 1,"Ḟ": 1,"Ḡ": 1,"Ḣ": 1,"Ḥ": 1,"Ḧ": 1,"Ḩ": 1,"Ḫ": 1,"Ḭ": 1,"Ḯ": 1,"Ḱ": 1,"Ḳ": 1,"Ḵ": 1,"Ḷ": 1,"Ḹ": 1,"Ḻ": 1,"Ḽ": 1,"Ḿ": 1,"Ṁ": 1,"Ṃ": 1,"Ṅ": 1,"Ṇ": 1,"Ṉ": 1,"Ṋ": 1,"Ṍ": 1,"Ṏ": 1,"Ṑ": 1,"Ṓ": 1,"Ṕ": 1,"Ṗ": 1,"Ṙ": 1,"Ṛ": 1,"Ṝ": 1,"Ṟ": 1,"Ṡ": 1,"Ṣ": 1,"Ṥ": 1,"Ṧ": 1,"Ṩ": 1,"Ṫ": 1,"Ṭ": 1,"Ṯ": 1,"Ṱ": 1,"Ṳ": 1,"Ṵ": 1,"Ṷ": 1,"Ṹ": 1,"Ṻ": 1,"Ṽ": 1,"Ṿ": 1,"Ẁ": 1,"Ẃ": 1,"Ẅ": 1,"Ẇ": 1,"Ẉ": 1,"Ẋ": 1,"Ẍ": 1,"Ẏ": 1,"Ẑ": 1,"Ẓ": 1,"Ẕ": 1,"Ạ": 1,"Ả": 1,"Ấ": 1,"Ầ": 1,"Ẩ": 1,"Ẫ": 1,"Ậ": 1,"Ắ": 1,"Ằ": 1,"Ẳ": 1,"Ẵ": 1,"Ặ": 1,"Ẹ": 1,"Ẻ": 1,"Ẽ": 1,"Ế": 1,"Ề": 1,"Ể": 1,"Ễ": 1,"Ệ": 1,"Ỉ": 1,"Ị": 1,"Ọ": 1,"Ỏ": 1,"Ố": 1,"Ồ": 1,"Ổ": 1,"Ỗ": 1,"Ộ": 1,"Ớ": 1,"Ờ": 1,"Ở": 1,"Ỡ": 1,"Ợ": 1,"Ụ": 1,"Ủ": 1,"Ứ": 1,"Ừ": 1,"Ự": 1,"Ỳ": 1,"Ỵ": 1,"Ỷ": 1,"Ỹ": 1,"Ữ": 1, "$": 0, "#": 0, "%": 0, "^":0, "(": 0, ")":0, "_":0, "=":0, "+":0, "@":0, "~":0, ",":0, '"':0, "|":0, '³':0, 'ʼ': 0, '℞': 0, "Σ": 2 }
             
            for row in records:
                log_message("Processing " + str(row[0]) + "...")
                acceptable_word = True
                parsed_definition = row[1]
                possible_word = row[0].strip()
                multiple_definitions = parsed_definition.split(";")
                first_definition = multiple_definitions[0]
                tokenized_definition = first_definition.split(" ")
                for token in tokenized_definition:
                    
                    if re.search("singular|plural|past|future|relating",token, re.IGNORECASE):
                        acceptable_word = False
                        log_message("Skipping " + possible_word + "...")
                if acceptable_word:
                    length_score = len(str(row[0]))
                    letter_score = 0
                    for x in str(row[0]).upper():
                        if x in letter_values:
                            letter_score = letter_score + letter_values[x]
                        else:
                            pass
                    word_scores[str(row[0])] = letter_score * length_score
                    log_message("Word score: " + str(word_scores[str(row[0])]))

            create_word_value_table = """CREATE TABLE WordValues (Word varchar(300), WordValue Int);"""
            result = execute_sql(create_word_value_table)
            if not result:
                log_message("Database error!")

            create_word_value_entry = """INSERT INTO WordValues (Word, WordValue) VALUES (%s, %s);"""
            for word in word_scores:
                word_value_entry = (word, word_scores[word])
                result = commit_sql(create_word_value_entry, word_value_entry)
                if not result:
                    log_message("Database error!")
                    
        elif (command == 'setentrylimit'):
            if not admin_check(message.author.id):
                await send_message(message, "Admin command only!")
                return
            entry_limit = int(command_string[1])
            await send_message(message, "Entry limit set to " + str(entry_limit) + ".")
            
        elif (command == 'poetrytag'):
            if poetry_tag_event[message.guild.id]:
                await send_message(message, "Poetry event already started!")
                return
                
            parsed_string = message.content.replace(".poetrytag ","")
            
            users_re = re.compile(r"-users (.+?) -", re.MULTILINE | re.S)
            topic_re = re.compile(r"-topic (.+?) -", re.MULTILINE | re.S)
            mode_re = re.compile(r"-mode (.+)", re.MULTILINE | re.S)
            user_id = message.author.id

            users = message.mentions
            if not users:
                await send_message(message, "No users specified!")
                return
                
            m = topic_re.search(parsed_string)
            if not m:
                await send_message(message, "No topic specified!")
                return
            topic = m.group().replace("-topic ","").replace(" -","").strip()
            
            m = mode_re.search(parsed_string)
            if not m:
                await send_message(message, "No mode specified!")
                return
            mode = m.group().replace("-mode ","").strip()
            if not re.search(r"tag|tandem",mode):
                await send_message(message, "Valid modes are tag and tandem!")
                return
            
            if re.search("random",topic):
                topic = random.choice(["Night-time", "A particular color", "Being underwater", "A person whose life you're curious about", "Your mother's perfume", "Falling asleep or waking up", "Growing older", "The feeling of getting lost in a book", "How to know if you're in love", "A bad dream", "A ghost", "Your city; town; or neighborhood", "An important life choice you've made", "Spring; summer; fall; or winter", "Something most people see as ugly but which you see as beautiful", "Jealousy", "Becoming a parent", "An event that changed you", "A place you visited -- how you imagined it beforehand; and what it was actually like", "The ocean", "Forgetting", "The speed of light", "A voodoo doll", "Reflections on a window", "A newspaper headline", "Your greatest fear", "Your grandmother's hands", "A particular toy you had as a child", "Being invisible", "A time you felt homesick", "Having an affair; or discovering your partner is having one", "Birthdays", "A favorite food and a specific memory of eating it", "An imaginary city", "Driving with the radio on", "Life in an aquarium", "Dancing", "Walking with your eyes closed", "What a computer might daydream about", "Time travel", "Brothers or sisters", "Your job; or a job you've had", "Weddings", "Leaving home", "Camping", "A zoo", "A historical event from the perspective of someone who saw it firsthand (You will have to do some research for this).", "Holding your breath", "Intimacy and privacy", "A time you were tempted to do something you feel is wrong", "Physical attraction to someone", "A superstition you have", "Someone you admire", "Write about the taste of: an egg; an orange; medicine; cinnamon", "Write about the smell of: burning food; melting snow; the ocean; your grandparents' home; the inside of a bus; pavement after the rain", "Write about the sound of: a radio changing channels; a dog howling; a football or baseball game; your parents talking in another room", "Write about the sight of: lit windows in a house when you're standing outside at night; someone you love when he or she doesn't know you're watching; a dying plant; shadows on snow", "Write about the feeling of: grass under bare feet; a really bad kiss; the headrush when you stand up too fast; sore muscles; falling asleep in the back seat of a moving car.", "a dessert; a memory; and someone in your family", "dancing; a pitch-black room; and the smell of lilacs", "a balloon; smoke; and a keyhole", "a secret box; an ice cube tray; and a velvet ribbon", "a betrayal; soap; and a plane ticket", "Rain; snow; or a storm", "An animal you think is beautiful or strange",  "Your parents or children",  "How a kiss feels",  "The house where you were born",  "A smell that brings back memories",  "Being a teenager; becoming an adult; middle age; old age",  "Feeling lonely",  "The moon",  "Getting lost",  "Marriage or divorce",  "An imaginary friend",  "Life in the future",  "The hottest; coldest; or most exhausted you have ever felt", "Having a fever",  "A new version of a fairy-tale",  "The shapes you see in clouds",  "Format: A letter",  "Format: A recipe",  "Format: A horoscope",  "Format: A fragment from an unusual dictionary",  "Format: A prayer",  "Format: A shopping list",  "Format: A magic spell.",  "Point of view: One of your parents",  "Point of view: Your child (real or imagined)",  "Point of view: A historical figure",  "Point of view: A very old person",  "Point of view: An athlete who has just lost the big game",  "Point of view: The most popular/unpopular kid from your school",  "Point of view: An inanimate object in your home.",  "Three wishes",  "Traveling to an unknown place",  "Getting a haircut",  "A scientific fact (real or invented)",  "An insect that got into your home",  "The sound of a specific language",  "Death",  "The number 3",  "The ocean",  "Missing someone",  "Something that makes you angry",  "The feeling of writing; why you want to be a writer",  "The ups and downs of love",  "The view out your window",  "City lights at night",  "A particular work of art",  "Having a superpower",  "Being in an airplane",  "Playing a sport",  "A shadow",  "A person transformed into an animal",  "Daydream",  "Cry",  "Kiss well",  "Find happiness",  "Peel a peach",  "Silky; gigantic; and puzzle.",  "Leaf; accelerating; and sticky.",  "Skin; drastic; and dusty.",  "Interrupt; nutmeg; and crystalline.",  "Exacting; oxygen; and delicate.",  "Reptilian; arched; and honey."])
            poetry_tag_event[message.guild.id] = True
            poetry_tag_users[message.guild.id] = users
            poetry_tag_topic[message.guild.id] = topic
            poetry_tag_mode[message.guild.id] = mode
            await send_message(message, "Poetry tag event started with topic of **" + str(topic) + "** in mode **" + str(mode) + "**")
            if re.search('tag', mode):
                await send_message(message, "<@" + str(users[0].id) + ">, you are first! Type .tag and your poem!")
            if re.search('tandem', mode):
                await send_message(message, "<@" + str(users[0].id) + ">, you are first! Type .tag and your line!")
                poetry_tag_tandem_poem[message.guild.id] = " "
            poetry_tag_current_user[message.guild.id] = 0
        elif (command == 'tag'):
            if not poetry_tag_event[message.guild.id]:
                await send_message(message, "No poetry tag currently running!")
                return
            if message.author.id != poetry_tag_users[message.guild.id][poetry_tag_current_user[message.guild.id]].id:
                await send_message(message, "It's not your turn!")
                return
            if (re.search('tag',poetry_tag_mode[message.guild.id])):
                await send_message(message, "Thank you for your poem!")
                poetry_tag_current_user[message.guild.id] = poetry_tag_current_user[message.guild.id] + 1
                if poetry_tag_current_user[message.guild.id] >= len(poetry_tag_users[message.guild.id]):
                    poetry_tag_current_user[message.guild.id] = 0
                next_user = poetry_tag_users[message.guild.id][poetry_tag_current_user].id
                await send_message(message, "You're up next, <@" + next_user + ">! Type .tag followed by your poem!")
            if (re.search('tandem', poetry_tag_mode[message.guild.id])):
                await send_message(message, "Thank you for your line!")
                poetry_tag_current_user[message.guild.id] = poetry_tag_current_user[message.guild.id] + 1
                if poetry_tag_current_user[message.guild.id] >= len(poetry_tag_users[message.guild.id]):
                    poetry_tag_current_user[message.guild.id] = 0
                poetry_tag_tandem_poem[message.guild.id] = poetry_tag_tandem_poem[message.guild.id] + message.content.replace(".tag ","") + "\n"
                next_user = poetry_tag_users[message.guild.id][poetry_tag_current_user[message.guild.id]].id
                await send_message(message, "You're up next, <@" + str(next_user) + ">! Type .tag followed by your line!")
        elif (command == 'finishtag'):
            if not poetry_tag_event[message.guild.id]:
                await send_message(message, "No poetry tag currently running!")
                return
            if (re.search('tandem', poetry_tag_mode[message.guild.id])):
                await send_message(message, "Awesome! Here is your completed poem!\n\n" + poetry_tag_tandem_poem[message.guild.id])
            if (re.search('tag', poetry_tag_mode[message.guild.id])):
                await send_message(message, "Awesome! Use .savepost if you'd like to save your poem!")
            poetry_tag_users[message.guild.id] = " "
            poetry_tag_event[message.guild.id] = False
            poetry_tag_topic[message.guild.id] = " "
            poetry_tag_current_user[message.guild.id] = 0
            poetry_tag_mode[message.guild.id] = " "
            poetry_tag_tandem_poem[message.guild.id] = " " 
        elif (command == 'loadwords'):
            if not admin_check(message.author.id):
                await send_message(message, "Admin command only!")
                return
            await send_message(message, "Starting dictionary database load...\nBot will be available until complete, but not all functions will work.")
            await load_words(message)
 
        elif (command == 'translate'):
            language = command_string[1]
            parsed_string = message.content.replace(".translate ","")
            parsed_string = parsed_string.replace(command_string[1] + " ","")
            get_translation = "SELECT DISTINCT Word,PartOfSpeech,Language,Definitions FROM DictionaryDefs WHERE (Language=%s AND Definitions LIKE '% " + parsed_string + " %') OR (Language=%s AND Definitions LIKE '" + parsed_string + "%') OR (Language=%s AND Definitions=%s);"
            translation_term = (language, language, language, parsed_string)
            async with message.channel.typing():
                records = select_sql(get_translation, translation_term)
            response = "**" + parsed_string + "** *Translated to " + language + "*\n\n"
            if len(records) == 0:
                await send_message(message, "No translation found in " + language + " for " + parsed_string + ".")
                return
            for row in records:
                response = response + "**" + row[0] + "** *" + row[1] + "* (" + row[2] + ") " + row[3] + "\n"
            await send_message(message, response)
        elif (command == 'loadkazen'):
            await send_message(message, "Loading Kazenperia...")
            xml_file = "/home/REDACTED/kazen.csv"
    
            f = open(xml_file, 'r')
            for line in f:
                tokens = re.sub(r"\(.*\)","",line)
                tokens = tokens.split(',')
                kazen_word = tokens[len(tokens) - 1].strip()
                enter_kazen = "INSERT INTO DictionaryDefs (Word,PartOfSpeech,Language,Definitions) VALUES (%s, 'unknown', 'Kazenperia', %s);"
                kazen_entry = (kazen_word, line.replace(",",";").replace(kazen_word,""))
                result = commit_sql(enter_kazen, kazen_entry)
            await send_message(message,"Complete!")        
        else:
            log_message("No command recognized by " + username)
            await send_message(message, "Invalid command.\n\nType **.info** for a list of available commands.")
    else:
        pass
client.run('NREDACTED')    
