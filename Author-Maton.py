import discord
import re
import mysql.connector
from mysql.connector import Error
import subprocess
import time
import requests
import random
import xml.etree.ElementTree as ET
import nltk

client = discord.Client()

@client.event
async def on_ready():
    print("Logged in!")
    

   
@client.event
async def on_message(message):
    if message.author.bot:
        return
    if message.content.startswith('.'):
        command_string = message.content.split(' ')
        command = command_string[0].replace('.','',1)
        
        if (command == 'sayhi'):
            await message.channel.send("Hello there!")
            
        elif (command == 'info' or command == 'help'):
            response = "**This is the Author-Maton bot, the writer help bot!**\n\n*Written by Ninja Nerd*\n\n**Available comamnds:**\n\n>>> **.info or .help** this help command\n\n**.sayhi** Say hello!\n\n**.savepost** -title *title* -perm *number* -post *post*: Save a post with the selected title to the database! Supports Discord formatting!\n\n**.getpost** *title*: Get a post with the selected title\n\n**.define** *word or phrase* Look in the dictionary database for a word definition.\n\n**.definelike** *word or phrase*  Find words that contain the text and print their definitions.\n\n**.synonyms** *word or phrase* Get words that mean similarly to this word.\n\n**.antonyms** *word or phrase* Get words that mean the opposite of this word.\n\n**.rhymes** *word or phrase* Get words that rhyme with this one.\n\n**.slang** *word or phrase* Get the first definition on UrbanDictionary for this word.\n\n.**randomslang** *word or phrase* Get a random definition from UrbanDictionary for this word."
            await message.channel.send(response)
            
        elif (command == 'initialize'):
            await message.channel.send("Creating databases...")
            try:
                connection = mysql.connector.connect(host='localhost', database='AuthorMaton', user='REDACTED', password='REDACTED')
                
                
                create_literature_store_table = """CREATE TABLE Literature (Id int NOT NULL, Title varchar(400), Author varchar(100), Permissions int, PostContent varchar(2000));"""
                
                create_dictionary_table = """CREATE TABLE DictionaryDefs (Id int NOT NULL, Word varchar(300), PartOfSpeech varchar(30), Definitions varchar(14000), Pronunciation varchar(100));"""
                
                create_thesaurus_table = """CREATE TABLE Thesaurus (Id int NOT NULL, Word varchar(300), Synonyms varchar(4000), Antonyms varchar(4000));"""
                
                create_rhyming_table = """CREATE TABLE Rhyming (Id int NOT NULL, Word varchar(300), RhymesWith varchar(4000));"""
                
                create_rhyme_database = """CREATE TABLE RhymeWords (Pronunciation varchar(500), RhymesWith varchar(10000));"""
                
                cursor = connection.cursor()
                result = cursor.execute(create_literature_store_table)
                result = cursor.execute(create_dictionary_table)
                result = cursor.execute(create_thesaurus_table)
                result = cursor.execute(create_rhyming_table)
                result = cursor.execute(create_rhyme_database)
                
                await message.channel.send("Database created successfully.")
            except mysql.connector.Error as error:
                await message.channel.send("Database error! " + str(error))
            finally:
                if(connection.is_connected()):
                    cursor.close()
                    connection.close()
        elif(command == 'writingprompt'):
            await message.channel.send("Coming soon!")
        elif (command == "savepost"):
            parsed_string = message.content
            title_re = re.compile("-title (.*) -perm", re.MULTILINE | re.S)
            post_re = re.compile("-post (.*)", re.MULTILINE | re.S)
            perm_re = re.compile("-perm (\d)", re.MULTILINE | re.S)
            
            m = title_re.search(parsed_string)
            if not m:
                await message.channel.send("No title tag specified!")
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
                await message.channel.send("No post specified!")
                return
                
            post = m.group()
            post = post.replace("-post ","")
            
            author = message.author.name
            
            print("Title: " + title + "\nAuthor: " + author + "\n Post Content: " + post)
            
            get_last_id_query = """SELECT MAX(Id) FROM Literature;"""
            
            try:
                connection = mysql.connector.connect(host='localhost', database='AuthorMaton', user='REDACTED', password='REDACTED')
                cursor = connection.cursor()
                result = cursor.execute(get_last_id_query)
                records = cursor.fetchall()
                if not records[0][0]:
                    id = 1
                else: 
                    id = int(str(records[0][0])) + 1
                await message.channel.send("Assigning ID " + str(id))
            except mysql.connector.Error as error:
                await message.channel.send("Database error!" + str(error))
            finally:
                if(connection.is_connected()):
                    cursor.close()
                    connection.close()  
            
            save_post_query = """INSERT INTO Literature (Id, Title, Author, Permissions, PostContent) VALUES (%s, %s, %s, %s, %s);"""
            post_to_save = (id, title, author, perm, post)
            try:
                connection = mysql.connector.connect(host='localhost', database='AuthorMaton', user='REDACTED', password='REDACTED')
                cursor = connection.cursor()
                result = cursor.execute(save_post_query, post_to_save)
                connection.commit()
                await message.channel.send("Post " + str(title) + " saved successfully.")
            except mysql.connector.Error as error:
                await message.channel.send("Database error!" + str(error))
            finally:
                if(connection.is_connected()):
                    cursor.close()
                    connection.close()          
        elif (command == 'getpost'):
            parsed_string = message.content.replace('.getpost ','')
            print("Title: " + parsed_string)
            
            get_post_query = """SELECT Title,Author,PostContent FROM Literature WHERE Title=%s;"""
            
            try:
                connection = mysql.connector.connect(host='localhost', database='AuthorMaton', user='REDACTED', password='REDACTED')
                cursor = connection.cursor()
                result = cursor.execute(get_post_query, (parsed_string,))
                records = cursor.fetchall()
                for row in records:
                    await message.channel.send(">>> **" + str(row[0]) + "**\n*By " + row[1] + "*\n\n" + row[2])
                    time.sleep(3)
            except mysql.connector.Error as error:
                await message.channel.send("Database error!" + str(error))
            finally:
                if(connection.is_connected()):
                    cursor.close()
                    connection.close() 
        elif (command == 'resetall'):
            clear_all_query = """DROP TABLE Literature; CREATE TABLE Literature (Id int NOT NULL, Title varchar(400), Author varchar(100), Permissions int, PostContent varchar(2000));"""
            try:
                connection = mysql.connector.connect(host='localhost', database='AuthorMaton', user='REDACTED', password='REDACTED')          
                cursor = connection.cursor()
                result = cursor.execute(clear_all_query)
                await message.channel.send("Database created successfully.")
            except mysql.connector.Error as error:
                await message.channel.send("Database error! " + str(error))
            finally:
                if(connection.is_connected()):
                    cursor.close()
                    connection.close()
        elif (command == 'rhymes'):
            parsed_string = message.content.replace('.rhymes ','')
            if parsed_string == "":
                await message.channel.send("No word specified!")
                return
            get_rhyme_entry = """SELECT RhymesWith FROM RhymeWords WHERE Pronunciation IN (SELECT Pronunciation FROM DictionaryDefs WHERE Word=%s);"""
            try:
                connection = mysql.connector.connect(host='localhost', database='AuthorMaton', user='REDACTED', password='REDACTED')
                cursor = connection.cursor()
                result = cursor.execute(get_rhyme_entry, (parsed_string,))
                records = cursor.fetchall()
                if cursor.rowcount == 0:
                    await message.channel.send("No rhymes found for " + parsed_string)
                    return
                response = "**" + parsed_string + "** *Rhymes with*\n\n"
                for row in records:
                    response = response + " " + str(row[0]) + "\n\n"
                
                message_chunks = [response[i:i+1500] for i in range(0, len(response), 2000)]
                for chunk in message_chunks:
                    await message.channel.send(">>> " + chunk)
                    time.sleep(3)

            except mysql.connector.Error as error:
                await message.channel.send("Database error!" + str(error))
            finally:
                if(connection.is_connected()):
                    cursor.close()
                    connection.close()       
        if (command == 'define'):
            parsed_string = message.content.replace('.define ','')
            if parsed_string == "":
                await message.channel.send("No word specified!")
                return
            get_dictionary_entry = """SELECT PartOfSpeech,Definitions FROM DictionaryDefs WHERE Word=%s AND Definitions IS NOT NULL;"""
            try:
                connection = mysql.connector.connect(host='localhost', database='AuthorMaton', user='REDACTED', password='REDACTED')
                cursor = connection.cursor()
                result = cursor.execute(get_dictionary_entry, (parsed_string,))
                records = cursor.fetchall()
                if cursor.rowcount == 0:
                    await message.channel.send("No definitions found for " + parsed_string)
                    return
                response = "**" + parsed_string + "**\n\n "
                for row in records:
                    response = response + "*" + str(row[0]) + "* " + row[1] + "\n\n"
                
                message_chunks = [response[i:i+1500] for i in range(0, len(response), 2000)]
                for chunk in message_chunks:
                    await message.channel.send(">>> " + chunk)
                    time.sleep(3)

            except mysql.connector.Error as error:
                await message.channel.send("Database error!" + str(error))
            finally:
                if(connection.is_connected()):
                    cursor.close()
                    connection.close()

        elif (command == 'definelike'):
            parsed_string = "%" + message.content.replace('.definelike ','') + "%"
            if parsed_string == "":
                await message.channel.send("No word specified!")
                return
            get_dictionary_entry = """SELECT Word,PartOfSpeech,Definitions FROM DictionaryDefs WHERE Word LIKE %s AND Definitions IS NOT NULL;"""
            try:
                connection = mysql.connector.connect(host='localhost', database='AuthorMaton', user='REDACTED', password='REDACTED')
                cursor = connection.cursor()
                result = cursor.execute(get_dictionary_entry, (parsed_string,))
                records = cursor.fetchall()
                if cursor.rowcount == 0:
                    await message.channel.send("No words found that matched " + parsed_string.replace('%',''))
                    return
                response = "**" + parsed_string.replace('%','') + "**\n\n"
                for row in records:
                    response = response + "**" + str(row[0]) + "** *" + row[1] + "* " + row[2] + "\n\n"
                
                message_chunks = [response[i:i+1500] for i in range(0, len(response), 2000)]
                for chunk in message_chunks:
                    await message.channel.send(">>> " + chunk)
                    time.sleep(3)

            except mysql.connector.Error as error:
                await message.channel.send("Database error!" + str(error))
            finally:
                if(connection.is_connected()):
                    cursor.close()
                    connection.close()                     
#            dictionary_entry = dictionary.meaning(word)
            

#            for part_of_speech in dictionary_entry:
#                response = response + "*" + str(part_of_speech) + "* :"
 #               counter = 1
#                for definition in dictionary_entry[part_of_speech]:
#                    definition = definition.replace("(","*")
#                    definition = definition.replace(")","*")
#                    response = response + str(counter) + ". " + definition + "\n\n"
#                    counter = counter + 1
            
        elif (command == 'synonyms'):
            parsed_string = message.content.replace('.synonyms ','')
            if parsed_string == "":
                await message.channel.send("No word specified!")
                return
#            output = subprocess.run(["/home/REDACTED/MyThes-1.0/thesaurus","/home/REDACTED/MyThes-1.0/th_en_US_new.idx","/home/REDACTED/MyThes-1.0/th_en_US_new.dat",word], universal_newlines=True, stdout=subprocess.PIPE)
            
#            message_chunks = [output.stdout[i:i+1500] for i in range(0, len(output.stdout), 2000)]
#            for chunk in message_chunks:
#                await message.channel.send(">>> " + chunk)
#                time.sleep(3)
            get_synonym_entry = """SELECT Synonyms FROM Thesaurus WHERE Word=%s AND Synonyms IS NOT NULL;"""
            try:
                connection = mysql.connector.connect(host='localhost', database='AuthorMaton', user='REDACTED', password='REDACTED')
                cursor = connection.cursor()
                result = cursor.execute(get_synonym_entry, (parsed_string,))
                records = cursor.fetchall()
                if cursor.rowcount == 0:
                    await message.channel.send("No synonyms found for " + parsed_string)
                    return
                response = "**" + parsed_string + "** *Synonyms*\n\n "
                for row in records:
                    response = response + str(row[0]) + "\n\n"
                
                message_chunks = [response[i:i+1500] for i in range(0, len(response), 2000)]
                for chunk in message_chunks:
                    await message.channel.send(">>> " + chunk)
                    time.sleep(3)

            except mysql.connector.Error as error:
                await message.channel.send("Database error!" + str(error))
            finally:
                if(connection.is_connected()):
                    cursor.close()
                    connection.close()             
            
            
            
        elif (command == 'antonyms'):
            parsed_string = message.content.replace('.antonyms ','')
            if parsed_string == "":
                await message.channel.send("No word specified!")
                return
            get_antonym_entry = """SELECT Antonyms FROM Thesaurus WHERE Word=%s AND Antonyms IS NOT NULL;"""
            try:
                connection = mysql.connector.connect(host='localhost', database='AuthorMaton', user='REDACTED', password='REDACTED')
                cursor = connection.cursor()
                result = cursor.execute(get_antonym_entry, (parsed_string,))
                records = cursor.fetchall()
                if cursor.rowcount == 0:
                    await message.channel.send("No antonyms found for " + parsed_string)
                    return
                response = "**" + parsed_string + "** *Antonyms*\n\n"
                for row in records:
                    response = response + str(row[0]) + "\n\n"
                
                message_chunks = [response[i:i+1500] for i in range(0, len(response), 2000)]
                for chunk in message_chunks:
                    await message.channel.send(">>> " + chunk)
                    time.sleep(3)

            except mysql.connector.Error as error:
                await message.channel.send("Database error!" + str(error))
            finally:
                if(connection.is_connected()):
                    cursor.close()
                    connection.close()                 
#            antonyms = dictionary.antonym(word)
            
#            response = ">>> **" + word + "**\n\n"
#            for antonym in antonyms:
#                response = response + antonym + "\n"
            
        elif (command == 'randomslang'):
            word = message.content.replace(".randomslang ","")
            if not word:
                await message.channel.send("No word specified!")
                return
            
            URL = "http://api.urbandictionary.com/v0/define?term=" + word
            r = requests.get(url = URL)
            data = r.json()
            
            if not data:
                await message.channel.send("No slang definition found for " + word)
                return
            
            definition = data["list"][random.randint(0,len(data["list"])-1)]["definition"]
            definition = definition.replace("[","")
            definition = definition.replace(']',"")
            
            await message.channel.send("**" + word + "**\n\n>>> " + definition)
        
        elif (command == 'slang'):
            word = message.content.replace(".slang ","")
            if not word:
                await message.channel.send("No word specified!")
                return
            
            URL = "http://api.urbandictionary.com/v0/define?term=" + word
            r = requests.get(url = URL)
            data = r.json()
            if not data:
                await message.channel.send("No definition found for " +word)
                return
            
            definition = data["list"][0]["definition"]
            definition = definition.replace("[","")
            definition = definition.replace(']',"")
            
            await message.channel.send("**" + word + "**\n\n>>> " + definition)
        
        elif (command == 'loadwords'):
            await message.channel.send("Starting dictionary database load...\nBot will be unavailable until complete.")
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
            english_words = set(nltk.corpus.words.words())
            sample_sentence_re = re.compile(r"#\*.*")
            part_of_speech_re = re.compile(r"Adjective|Noun|Verb|Adverb|Pronoun|Conjunction|Preposition|Interjection")
            etym_re = re.compile(r"=Etymology")
            adj_re = re.compile(r"=Adjective=")
            noun_re = re.compile(r"=Noun=")
            verb_re = re.compile(r"=Verb=")
            adverb_re = re.compile(r"=Adverb=")
            rhyme_replace_re = re.compile("begin rhyme list|end rhyme list")
            pronoun_re = re.compile(r"=Pronoun=")
            conj_re = re.compile(r"=Conjunction=")
            prep_re = re.compile(r"=Preposition=")
            intj_re = re.compile(r"=Interjection=")
            wiki_re = re.compile(r"[\[|\]|\{|\}]")
            usage_re = re.compile(r"\{\{.*?\}\}")
            title_re = re.compile(r"<title>(?P<word>.*)</title>")
            text_begin_re = re.compile(r"<text>")
            text_end_re = re.compile(r"</text>")
            id_re = re.compile(r"<id>(?P<id>.*)</id>")
            symbol_re = re.compile("ref.*?;|&.+?;", re.MULTILINE | re.S)
            definition_re = re.compile(r"^\#\s+.*")
            synonym_re = re.compile(r"=Synonyms=")
            antonym_re = re.compile(r"=Antonyms=")
            syn_word_re = re.compile(r"\|.*?\}\}")
            ant_word_re = re.compile(r"\|.*?\}\}")
            page_end_re = re.compile(r"</page>")
            line_skip_re = re.compile(r"[A-Za-z]")
            def_exclude_re = re.compile(r"infl of|inflection of|verb form|verb-form|imperative of")
            blank_re = re.compile(r"^\s+$")
            rhyme_re = re.compile(r"=Rhymes=")
            rhyme_page_end_re = re.compile(r"</page>")
            definition_clear_re = re.compile("\[\[.+?\|",  re.MULTILINE | re.S)
            super_def_clear_re = re.compile("l*?\|.+\|", re.MULTILINE | re.S)
            rhyme_pro_re = re.compile(r"\{\{rhymes\|en\|(?P<rhymepro>.*)\}\}")
            rhyme_page_re = re.compile(r"title>Rhymes:English.(?P<pro>.*?)</title")
            skip_stuff_re = re.compile(r"Index:|Category:|Appendix:|Wiktionary:|Esperanto|[^A-Z-a-z]+")
            rhyme_pronunciation = " "
            rhyme_pro = " "
            rhyme_page_content = " "
            skip_page = False
            rhyme_flag = False
            rhyme_page_flag = False
            new_word = True
            for line in f:
                n = rhyme_page_re.search(line)
                m = title_re.search(line)
                if n:
                    rhmye_pronunciation = " "
                    rhyme_base = n.group('pro')
                    rhyme_pronunciation = rhmye_pronunciation.join(rhyme_base)
                    rhyme_pronunciation = re.sub(wiki_re,"",rhyme_pronunciation)
                    print("Processing rhyme " + rhyme_pronunciation + "...")
                    rhyme_page_flag = True
                    skip_page = True
                    rhyme_page_content = " "
                    continue  
                elif m:
                         
                    word = m.group('word')
                    if not line_skip_re.search(word) or skip_stuff_re.search(word):
                        skip_page = True
                        continue
                    else:
                        skip_page = False
                    print("Processing " + word + "...")
                    definition = " "
                    synonyms = " "
                    antonyms = " "
                    rhymes = " "
                    rhyme_pro = " "
                    part_of_speech = "unknown"
                    new_word = True
                    syn_flag = False
                    ant_flag = False
                    rhyme_flag = False
                else:
                    new_word = False
                if not skip_page:    
                    m = id_re.search(line)
                    if m:
                        id = m.group('id')
                    
                    m = rhyme_pro_re.search(line)
                    if m:
                        rhyme_pro = m.group('rhymepro')
                        
                    if (part_of_speech_re.search(line) and not new_word and definition != "" and not blank_re.match(line) and not def_exclude_re.search(definition) and not "unknown" in part_of_speech):
                        try:

                            connection = mysql.connector.connect(host='localhost', database='AuthorMaton', user='REDACTED', password='REDACTED')                
                            create_dictionary_entry = """INSERT INTO DictionaryDefs (Id, Word, PartOfSpeech, Definitions, Pronunciation) VALUES(%s, %s, %s, %s, %s);"""   
                            dictionary_entry = (id, word, part_of_speech, definition, rhyme_pro)
                            cursor = connection.cursor()
                            result = cursor.execute(create_dictionary_entry, dictionary_entry)
                            connection.commit()
                        except mysql.connector.Error as error:
                            await message.channel.send("Database error! " + str(error))   
                        finally:
                            if(connection.is_connected()):
                                cursor.close()
                                connection.close()
                        id = str(int(id) + 1)
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
                        
                    m = definition_re.search(line)
                    if m and not sample_sentence_re.search(line):
                        temp_def = re.sub("#+","",line)
                       
                        temp_def = re.sub(definition_clear_re,"",temp_def)
                        temp_def = re.sub("#\w+\s","",temp_def)
                        temp_def = re.sub("\|lb\|.+?\|","",temp_def)
                        temp_def = re.sub(wiki_re,"",temp_def)
                        temp_def = re.sub(usage_re,"",temp_def)   
                        temp_def = re.sub(text_end_re, "",temp_def)
                        temp_def = temp_def.replace("\n","")
                        temp_def = re.sub(symbol_re,"",temp_def)
                        temp_def = re.sub(r"^\s*;\s+","",temp_def)
                        temp_def = re.sub("lben.*?\s","",temp_def)
                        temp_def = re.sub("ref.*?;","",temp_def)
                        temp_def = re.sub(super_def_clear_re,"",temp_def)

                        definition = definition + "; " + temp_def

                        
                    if (syn_flag and "==" in line):
                        syn_flag = False           
                        
                    if (synonym_re.search(line)):
                        syn_flag = True

                    if (syn_flag):
                        syns = re.findall(syn_word_re,line)
                        for syn in syns:
                            temp_syn = syn
                            temp_syn = re.sub(definition_clear_re,"",temp_syn)
                            temp_syn = re.sub(super_def_clear_re,"",temp_syn)
                            temp_syn = re.sub(symbol_re,"",temp_syn)
                            temp_syn =  re.sub(r"(.*?\|)+\|","",temp_syn)
                            temp_syn = re.sub(r"^\s*,\s*","",temp_syn)
                            temp_syn = re.sub(wiki_re,"",temp_syn)
                            synonyms = synonyms = synonyms + ", " + temp_syn
                        
                    if (ant_flag):
                        ants = re.findall(ant_word_re,line)
                        for ant in ants:
                            temp_ant = ant
                            temp_ant =  re.sub(r"(.*?\|)+\|","",temp_ant)
                            temp_ant = re.sub(definition_clear_re,"", temp_ant)
                            temp_ant = re.sub(symbol_re,"", temp_ant)
                            temp_ant  = re.sub(super_def_clear_re,"",temp_ant)
                            temp_ant = re.sub(r"^\s*,\s*","",temp_ant)
                            temp_ant = re.sub(wiki_re,"",temp_ant)
                            antonyms = antonyms = antonyms + ", " + temp_ant
                    if (ant_flag and "==" in line):
                        ant_flag = False      
                        

                    if (antonym_re.search(line)):
                        syn_flag = False
                        ant_flag = True

                    if (rhyme_re.search(line)):
                        rhyme_flag = True
                    if (text_end_re.search(line)):
                        rhyme_flag = False
                    
                    if (rhyme_flag and wiki_re.search(line)):
                        rhymes = rhymes + ", " + line
                        rhymes = re.sub(wiki_re,"",rhymes)
                        
                    
                    if (page_end_re.search(line) and definition != "" and not blank_re.match(definition) and not def_exclude_re.search(definition) and not "unknown" in part_of_speech ):
                        try:

                            connection = mysql.connector.connect(host='localhost', database='AuthorMaton', user='REDACTED', password='REDACTED')                
                            create_dictionary_entry = """INSERT INTO DictionaryDefs (Id, Word, PartOfSpeech, Definitions, Pronunciation) VALUES(%s, %s, %s, %s, %s);"""   
                            create_thesaurus_entry = """INSERT INTO Thesaurus (Id, Word, Synonyms, Antonyms) VALUES (%s, %s, %s, %s);"""
                            create_rhyme_entry = """INSERT INTO Rhyming (Id, Word, RhymesWith) VALUES (%s, %s, %s);"""
                            dictionary_entry = (id, word, part_of_speech, definition, rhyme_pro)
                            thesaurus_entry = (id, word, synonyms, antonyms)
                            rhyme_entry = (id, word, rhymes)
                            cursor = connection.cursor()
                            result = cursor.execute(create_dictionary_entry, dictionary_entry)
                            result = cursor.execute(create_thesaurus_entry, thesaurus_entry)
                            result = cursor.execute(create_rhyme_entry, rhyme_entry)
                            connection.commit()
                            word_count = word_count + 1
                        except mysql.connector.Error as error:
                            pass
                            #await message.channel.send("Database error! " + str(error))   
                        finally:
                            if(connection.is_connected()):
                                cursor.close()
                                connection.close()

                if rhyme_page_flag:
                    rhymes = re.findall(r"\[\[.+?\]\]|\{\{.+?\}\}",line)
                    rhyme_master = " "
                    if rhymes:
                        for rhyme in rhymes:
                            temp_rhyme = str(rhyme)
                            print("Found rhyme: " + rhyme)
                            temp_rhyme = re.sub(wiki_re,"",temp_rhyme)
                            temp_rhyme = re.sub(r"(.*?\|)+","",temp_rhyme)
                            temp_rhyme = re.sub("rhyme list begin","",temp_rhyme)
                            temp_rhyme = re.sub("rhyme list end","",temp_rhyme)
                            print("Transformed to temp: " + temp_rhyme) 
                            rhyme_page_content = rhyme_page_content + ", " + temp_rhyme
                    
                    if (rhyme_page_end_re.search(line)):
                        rhyme_page_flag = False
                        try:
                            rhyme_pronunciation = re.sub("\s+","",rhyme_pronunciation)
                            create_rhyme_entry= """INSERT INTO RhymeWords (Pronunciation, RhymesWith) VALUES (%s, %s);"""
                            rhyme_table_entry = (rhyme_pronunciation, rhyme_page_content)
                            connection = mysql.connector.connect(host='localhost', database='AuthorMaton', user='REDACTED', password='REDACTED')
                            cursor = connection.cursor()
                            result = cursor.execute(create_rhyme_entry, rhyme_table_entry)
                            connection.commit()
                        except mysql.connector.Error as error:
                            print("error: " + str(error))
                        finally:
                            if(connection.is_connected()):
                                cursor.close()
                                connection.close()
                            rhyme_page_flag = False
                            rhyme_page_content = " "
                            rhyme_pronunciation = " "
                            
            await message.channel.send("Word load complete! Word count: " + str(word_count))    
        else:
            await message.channel.send("Invalid command.\n\nType **.info** for a list of available commands.")
            
client.run('REDACTED')    
