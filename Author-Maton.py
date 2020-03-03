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
from discord.utils import get

client = discord.Client()
quiz_event = False
quiz_answer = " "
quiz_scores = {}
word_of_the_day_score = 30
entry_limit = 5

@client.event
async def on_ready():
    global quiz_scores
    print("Logged in!")
    for guild in client.guilds:
        for member in guild.members:
            quiz_scores[member.id] = 0

   
@client.event
async def on_message(message):
    global word_of_the_day_score
    global quiz_answer
    global quiz_event
    global quiz_scores
    global entry_limit
    if message.author.bot:
        return
    if message.content.startswith('.'):

        command_string = message.content.split(' ')
        command = command_string[0].replace('.','')
        username = message.author.name
        print("Command " + message.content + " called by " + username)
        if (command == 'sayhi'):
            print("Command sayhi called by " + username)
            await message.channel.send("Hello there!")
            
        elif (command == 'info' or command == 'help'):
            response = "**This is the Author-Maton bot, the writer help bot!**\n\n*Written by Ninja Nerd*\n\n**Available comamnds:**\n\n>>> **.info or .help** this help command\n\n**.sayhi** Say hello!\n\n**.savepost** -title *title* -perm *number* -post *post*: Save a post with the selected title to the database! Supports Discord formatting!\n\n**.getpost** *title*: Get a post with the selected title\n\n**.define** *word or phrase* Look in the dictionary database for a word definition.\n\n**.definelike** *word or phrase*  Find words that contain the text and print their definitions.\n\n**.synonyms** *word or phrase* Get words that mean similarly to this word.\n\n**.antonyms** *word or phrase* Get words that mean the opposite of this word.\n\n**.rhymes** *word or phrase* Get words that rhyme with this one.\n\n**.sentences** *word or phrase* Use this word in a sentence.\n\n**.slang** *word or phrase* Get the first definition on UrbanDictionary for this word.\n\n.**randomslang** *word or phrase* Get a random definition from UrbanDictionary for this word.\n\n**.quiz** Get a random definition from the database and the first one to answer with **.answer** *word or phrase* gets it right!\n\n**.answer** *word or phrase* Answer a quiz question.\n\n**.hint** Get a hint for the quiz word.\n\n**.randomword** Get a random word and definition from the dictionary.\n\n**.wordcount** *post* Get the number of words in the post.\n\n**.wordsearch** *start letter*    *number of letters between*   *end letter* Search the dictionary for words starting and ending with the specified letters and the specified number of letters in between.\n\n**.wordpattern** *pattern*\nFind all words with the specified pattern. Represent unknown lettters as underscores (_) and known letters with their letter.\n\n**.wordscore** *word or phrase* Get the calculated word score for the specified word in the dictionary."
            await message.channel.send(response)
            
        elif (command == 'initialize'):
            print("initialize called by " + username)
            if (message.author.id != 610335542780887050):
                await message.channel.send("Admin command only!")
                return
            await message.channel.send("Creating databases...")
            try:
                connection = mysql.connector.connect(host='localhost', database='AuthorMaton', user='REDACTED', password='REDACTED')
                
                create_literature_store_table = """CREATE TABLE Literature (Id int NOT NULL, Title varchar(400), Author varchar(100), Permissions int, PostContent varchar(1900));"""
                
                create_dictionary_table = """CREATE TABLE DictionaryDefs (Id int NOT NULL, Word varchar(300), PartOfSpeech varchar(30), Definitions varchar(14000), Pronunciation varchar(100));"""
                
                create_thesaurus_table = """CREATE TABLE Thesaurus (Id int NOT NULL, Word varchar(300), Synonyms varchar(4000), Antonyms varchar(4000));"""
                
                create_rhyming_table = """CREATE TABLE Rhyming (Id int NOT NULL, Word varchar(300), RhymesWith varchar(4000));"""
                
                create_rhyme_database = """CREATE TABLE RhymeWords (Pronunciation varchar(500), RhymesWith varchar(10000));"""
                
                create_sentence_database = """CREATE TABLE SampleSentences (Word varchar(300), Sentences varchar(10000));"""
                
                cursor = connection.cursor()
                result = cursor.execute(create_literature_store_table)
                result = cursor.execute(create_dictionary_table)
                result = cursor.execute(create_thesaurus_table)
                result = cursor.execute(create_rhyming_table)
                result = cursor.execute(create_rhyme_database)
                result = cursor.execute(create_sentence_database)
                
                await message.channel.send("Database created successfully.")
            except mysql.connector.Error as error:
                await message.channel.send("Database error! " + str(error))
            finally:
                if(connection.is_connected()):
                    cursor.close()
                    connection.close()
        elif (command == 'clearwords'):
            print("initialize called by " + username)
            if (message.author.id != 610335542780887050):
                await message.channel.send("Admin command only!")
                return
            await message.channel.send("Dropping databases...")
            try:
                connection = mysql.connector.connect(host='localhost', database='AuthorMaton', user='REDACTED', password='REDACTED')
                
                drop_all_tables = """DROP TABLE Literature; DROP TABLE DictionaryDefs; DROP TABLE Thesaurus; DROP TABLE Rhyming; DROP TABLE RhymeWords; DROP TABLE SampleSentences; DROP TABLE WordValues"""
                
                cursor = connection.cursor()
                result = cursor.execute(drop_all_tables)
                
                await message.channel.send("Databases all cleared successfully.")
            except mysql.connector.Error as error:
                await message.channel.send("Database error! " + str(error))
            finally:
                if(connection.is_connected()):
                    cursor.close()
                    connection.close()
        elif(command == 'writingprompt'):
            print("writingprompt called by " + username)
            await message.channel.send("Coming soon!")
        elif (command == "savepost"):
            print("savepost called by " + username)
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
            printf("getpost called by " + username)
            parsed_string = message.content.replace('.getpost ','')
            print("Title: " + parsed_string)
            
            get_post_query = """SELECT Title,Author,PostContent FROM Literature WHERE Title=%s;"""
            if (entry_limit > 0):
                get_post_query = get_post_query.replace(";"," LIMIT " + str(entry_limit) + ";")
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
            print("resetall called by " + username)
            if (message.author.id != 610335542780887050):
                await message.channel.send("Admin command only!")
                return
            clear_all_query = """DROP TABLE Literature; CREATE TABLE Literature (Id int NOT NULL, Title varchar(400), Author varchar(100), Permissions int, PostContent varchar(1900));"""
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
            print("rhymes called by " + username)
            parsed_string = message.content.replace('.rhymes ','')
            if not parsed_string:
                await message.channel.send("No word specified!")
                return
            
            get_rhyme_list = """SELECT RhymesWith FROM Rhyming WHERE Word=%s AND RhymesWith!=' ';"""
            get_rhyme_entry = """SELECT RhymesWith FROM RhymeWords WHERE Pronunciation IN (SELECT Pronunciation FROM DictionaryDefs WHERE Word=%s);"""
            get_rhyme_pro_list = False
            try:
                connection = mysql.connector.connect(host='localhost', database='AuthorMaton', user='REDACTED', password='REDACTED')
                cursor = connection.cursor()
                result = cursor.execute(get_rhyme_list, (parsed_string,))
                records = cursor.fetchall()
                if cursor.rowcount > 0:
                    for row in records:
                        response = response + " " + str(row[0]) + "\n\n"
                else:
                    result = cursor.execute(get_rhyme_entry, (parsed_string,))
                    records = cursor.fetchall()
                    if cursor.rowcount == 0:
                        await message.channel.send("No rhymes found for " + parsed_string)
                        return
                    response = "**" + parsed_string + "** *Rhymes with*\n\n"
                    for row in records:
                        response = response + " " + str(row[0]) + "\n\n"
                if cursor.rowcount < 1:
                    await message.channel.send("No rhymes found for " + parsed_string)
                    return
                message_chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
                for chunk in message_chunks:
                    await message.channel.send(">>> " + chunk)
                    time.sleep(3)

            except mysql.connector.Error as error:
                await message.channel.send("Database error!" + str(error))
            finally:
                if(connection.is_connected()):
                    cursor.close()
                    connection.close()       
        elif (command == 'define'):
            print("define called by " +username)
            parsed_string = message.content.replace('.define ','')
            if parsed_string == "":
                await message.channel.send("No word specified!")
                return
            get_dictionary_entry = """SELECT PartOfSpeech,Definitions FROM DictionaryDefs WHERE Word=%s AND Definitions !=' ';"""
            if (entry_limit > 0):
                get_dictionary_entry = get_dictionary_entry.replace(";"," LIMIT " + str(entry_limit) + ";")
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
                
                message_chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
                for chunk in message_chunks:
                    await message.channel.send(">>> " + chunk)
                    time.sleep(3)

            except mysql.connector.Error as error:
                await message.channel.send("Database error!" + str(error))
            finally:
                if(connection.is_connected()):
                    cursor.close()
                    connection.close()
        elif (command == 'randomword'):
            print("randomword called by " + username)
            parsed_string = message.content.replace('.randomword ','')
            get_dictionary_entry = """SELECT Word,PartOfSpeech,Definitions FROM DictionaryDefs ORDER BY RAND( ) LIMIT 1;"""
            
            try:
                connection = mysql.connector.connect(host='localhost', database='AuthorMaton', user='REDACTED', password='REDACTED')
                cursor = connection.cursor()
                result = cursor.execute(get_dictionary_entry)
                records = cursor.fetchall()
                if cursor.rowcount == 0:
                    
                    await message.channel.send("No definitions found for " + parsed_string)
                    return
                for row in records:
                    response = "**" + str(row[0]) + "** *" + str(row[1]) + "* " + row[2] + "\n\n"
                
                message_chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
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
            print("definelike called by " + username)
            parsed_string = "%" + message.content.replace('.definelike ','') + "%"
            if parsed_string == "":
                await message.channel.send("No word specified!")
                return
            get_dictionary_entry = """SELECT Word,PartOfSpeech,Definitions FROM DictionaryDefs WHERE Word LIKE %s AND Definitions !=' ';"""
            if (entry_limit > 0):
                get_dictionary_entry = get_dictionary_entry.replace(";"," LIMIT " + str(entry_limit) + ";")
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
                
                message_chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
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
            print("synonyms called by " + username)
            parsed_string = message.content.replace('.synonyms ','')
            if parsed_string == "":
                await message.channel.send("No word specified!")
                return
#            output = subprocess.run(["/home/REDACTED/MyThes-1.0/thesaurus","/home/REDACTED/MyThes-1.0/th_en_US_new.idx","/home/REDACTED/MyThes-1.0/th_en_US_new.dat",word], universal_newlines=True, stdout=subprocess.PIPE)
#     message_chunks = [output.stdout[i:i+1500] for i in range(0, len(output.stdout), 1900)]
#            for chunk in message_chunks:
#                await message.channel.send(">>> " + chunk)
#                time.sleep(3)
            get_synonym_entry = """SELECT Synonyms FROM Thesaurus WHERE Word=%s AND Synonyms != ' ';"""
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
                
                message_chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
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
            print("antonyms called by " + username)
            parsed_string = message.content.replace('.antonyms ','')
            if parsed_string == "":
                await message.channel.send("No word specified!")
                return
            get_antonym_entry = """SELECT Antonyms FROM Thesaurus WHERE Word=%s AND Antonyms != ' ';"""
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
                
                message_chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
                for chunk in message_chunks:
                    await message.channel.send(">>> " + chunk)
                    time.sleep(3)

            except mysql.connector.Error as error:
                await message.channel.send("Database error!" + str(error))
            finally:
                if(connection.is_connected()):
                    cursor.close()
                    connection.close()                 
        elif (command == 'randomslang'):
            print("randomslang called by " + username)
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
        elif (command == 'sentences'):
            parsed_string = message.content.replace(".sentences ","")
            get_sentences = """SELECT Sentences FROM SampleSentences WHERE Word=%s AND Sentences IS NOT NULL;"""
            try:
                connection = mysql.connector.connect(host='localhost', database='AuthorMaton', user='REDACTED', password='REDACTED')
                cursor = connection.cursor()
                result = cursor.execute(get_sentences, (parsed_string,))
                records = cursor.fetchall()
                if cursor.rowcount == 0:
                    await message.channel.send("No sample sentences found for " + parsed_string)
                    return
                response = "**" + parsed_string + "** *Used in a sentence*\n\n"
                for row in records:
                    response = response + str(row[0]) + "\n\n"
                
                message_chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
                for chunk in message_chunks:
                    await message.channel.send(">>> " + chunk)
                    time.sleep(3)

            except mysql.connector.Error as error:
                await message.channel.send("Database error!" + str(error))
            finally:
                if(connection.is_connected()):
                    cursor.close()
                    connection.close()                 
        elif (command == 'slang'):
            print("slang called by " + username)
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
        
 
        elif (command == 'quiz'):
            print("quiz called by " + username)
            get_dictionary_entry = """SELECT Word,PartOfSpeech,Definitions FROM DictionaryDefs ORDER BY RAND( ) LIMIT 1;"""
            quiz_event = True
            try:
                connection = mysql.connector.connect(host='localhost', database='AuthorMaton', user='REDACTED', password='REDACTED')
                cursor = connection.cursor()
                result = cursor.execute(get_dictionary_entry)
                records = cursor.fetchall()
                response = "What word means "
                for row in records:
                    response = response +  row[2] + "\n\n"
                quiz_answer = row[0]
                message_chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
                for chunk in message_chunks:
                    await message.channel.send(">>> " + chunk)
                    time.sleep(3)
            except mysql.connector.Error as error:
                print("error: " + str(error))
            finally:
                if(connection.is_connected()):
                    cursor.close()
                    connection.close()
                rhyme_page_flag = False
                rhyme_page_content = " "
                rhyme_pronunciation = " "
        elif (command == 'answer'):
            print("answer called by " + username) 
            if not quiz_event:
                await message.channel.send("No quiz currently active! Type **.quiz** to start a word quiz.\n")
                return    
            parsed_string = message.content.replace(".answer ","")
            if (quiz_answer.lower() == parsed_string.lower()):
                await message.channel.send("Yes, the answer was " + quiz_answer + "! Correct!")
                quiz_scores[message.author.id] = quiz_scores[message.author.id] + 1
            else:
                await message.channel.send("Sorry, the answer was " + quiz_answer + ".")
            quiz_event = False
            quiz_answer = " "
        elif (command == 'myscore'):
            await message.channel.send("Your score is **" + str(quiz_scores[message.author.id]) + "**.")
        elif (command == 'leaderboard'):
            leaderboard = sorted(quiz_scores.items(), key = lambda x: x[1])
            response = "**Quiz Leaderboard:**\n\n"
            for user in sorted(quiz_scores, key=quiz_scores.get, reverse=True):
                id_num = str(user)
                id_num = id_num.split(',')
                id_int = int(id_num[0].replace("(",""))
                username = get(client.get_all_members(), id=user)
                response = response + str(username.name) + " - " + str(quiz_scores[user]) + "\n"
            await message.channel.send(response)
        elif (command == 'hint'):
            print("hint called by " + username)
            if not quiz_event:
                await message.channel.send("No quiz currently active! Type **.quiz** to start a word quiz.\n")
            hint = quiz_answer[0]
            letters = len(quiz_answer)
            await message.channel.send("The first letter of the word is " + hint + " and it has " + str(letters) + " letters.")
        elif (command == 'wordcount'):
            print("wordcount called by " + username)
            parsed_string = message.content.replace(".wordcount ","")
            words_in_post = parsed_string.split()
            word_count = len(words_in_post)
            await message.channel.send("The word count is " + str(word_count) + ".")
        elif (command == 'mysql'):
            print("mysql called by " + username)
            if (message.author.id != 610335542780887050):
                await message.channel.send("Admin command only!")
                return
            mysql_command = message.content.replace(".mysql ","")
            try:
                connection = mysql.connector.connect(host='localhost', database='AuthorMaton', user='REDACTED', password='REDACTED')
                cursor = connection.cursor()
                result = cursor.execute(mysql_command)
                records = cursor.fetchall()
                response = "Results:\n\n "
                for row in records:
                    for column in range(len(row)):
                        response = response + ", " + str(row[column])
                    response = response + "\n"
                message_chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
                for chunk in message_chunks:
                    await message.channel.send(">>> " + chunk)
                    time.sleep(3)
            except mysql.connector.Error as error:
                print("error: " + str(error))
            finally:
                if(connection.is_connected()):
                    cursor.close()
                    connection.close()
        elif (command == 'restartbot'):
            print("restartbot called by " + username)
            if (message.author.id != 610335542780887050):
                await message.channel.send("Admin command only!")
                return
            await message.channel.send("Restarting bot...")
            output = subprocess.run(["/home/REDACTED/restartbot.sh"], universal_newlines=True, stdout=subprocess.PIPE)
            await message.channel.send("Output from restart: " + str(output.stdout))
        elif (command == 'wordsearch'):
            print("wordsearch called by " + username)
            start_letter = command_string[1]
            number_of_letters = command_string[2]
            end_letter = command_string[3]
            
            if not start_letter:
                await channel.message.send("No start letter specified!")
                return
            if not number_of_letters:
                await channel.message.send("No number of letters specified!")
                return
            if not end_letter:
                await channel.message.send("No end letters specified!")
                return
            word_search_query = """SELECT Word FROM DictionaryDefs WHERE Word LIKE %s;"""
            if (entry_limit > 0):
                word_search_query = word_search_query.replace(";"," LIMIT " + str(entry_limit) + ";")
            word_pattern = start_letter
            for i in range(int(number_of_letters)):
                word_pattern = word_pattern + "_"
            word_pattern = word_pattern + end_letter
            try:
                connection = mysql.connector.connect(host='localhost', database='AuthorMaton', user='REDACTED', password='REDACTED')
                cursor = connection.cursor()
                result = cursor.execute(word_search_query, (word_pattern,))
                records = cursor.fetchall()
                if cursor.rowcount == 0:
                    await message.channel.send("No words found for the specified patern.")
                    return
                response = "**Words that start with " + start_letter + ", end with " +end_letter + ", with " + number_of_letters + " in between:**\n\n"
                for row in records:
                    response = response + str(row[0]) + ", "
                
                message_chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
                for chunk in message_chunks:
                    await message.channel.send(">>> " + chunk)
                    time.sleep(3)
            except mysql.connector.Error as error:
                print("error: " + str(error))
            finally:
                if(connection.is_connected()):
                    cursor.close()
                    connection.close()
        elif (command == 'wordpattern'):
            print("wordpattern called by " + username)
            parsed_string = message.content.replace(".wordpattern ","")
            parsed_string = parsed_string.replace(" ","")
            
            if not parsed_string:
                await message.channel.send("No pattern specified!")
                return
            
            word_pattern_query = """SELECT Word FROM DictionaryDefs WHERE Word LIKE %s;"""
            if (entry_limit > 0):
                word_pattern_query = word_pattern_query.replace(";"," LIMIT " + str(entry_limit) + ";")
            try:
                connection = mysql.connector.connect(host='localhost', database='AuthorMaton', user='REDACTED', password='REDACTED')
                cursor = connection.cursor()
                result = cursor.execute(word_pattern_query, (parsed_string,))
                records = cursor.fetchall()
                if cursor.rowcount == 0:
                    await message.channel.send("No words found for the specified patern.")
                    return
                response = "**Words that have the pattern " + parsed_string + ":**\n\n"
                for row in records:
                    response = response + str(row[0]) + ", "
                
                message_chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
                for chunk in message_chunks:
                    await message.channel.send(">>> " + chunk)
                    time.sleep(3)
            except mysql.connector.Error as error:
                print("error: " + str(error))
            finally:
                if(connection.is_connected()):
                    cursor.close()
                    connection.close()
        elif (command == 'wordscore'):
            parsed_string = message.content.replace(".wordscore ","")
            get_word_score = """SELECT WordValue FROM WordValues WHERE Word=%s LIMIT 1;"""
            try:
                connection = mysql.connector.connect(host='localhost', database='AuthorMaton', user='REDACTED', password='REDACTED')
                cursor = connection.cursor()
                result = cursor.execute(get_word_score, (parsed_string,))
                records = cursor.fetchall()
                if cursor.rowcount == 0:
                    await message.channel.send("No score found for the specified word.")
                    return
                response = "The word score of **" + parsed_string + "** is ```"
                for row in records:
                    response = response + str(row[0]) + "```"
                
                message_chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
                for chunk in message_chunks:
                    await message.channel.send(">>> " + chunk)
                    time.sleep(3)
            except mysql.connector.Error as error:
                print("error: " + str(error))
            finally:
                if(connection.is_connected()):
                    cursor.close()
                    connection.close()
        elif (command == 'setminscore'):
            if (message.author.id != 610335542780887050):
                await message.channel.send("Admin command only!")
                return
            word_of_the_day_score = int(message.content.replace('.setminscore ',""))
            await message.channel.send("Word of the day score minimum set to " + str(word_of_the_day_score))
        elif (command == 'wordoftheday'):
            get_word_of_the_day = """SELECT Word FROM WordValues WHERE WordValue>=%s ORDER BY RAND( ) LIMIT 1;"""
            try:
                connection = mysql.connector.connect(host='localhost', database='AuthorMaton', user='REDACTED', password='REDACTED')
                cursor = connection.cursor()
                result = cursor.execute(get_word_of_the_day, (word_of_the_day_score,))
                records = cursor.fetchall()
                for row in records:
                    word = row[0]
                get_word_based_on_score = """SELECT Word,PartOfSpeech,Definitions FROM DictionaryDefs WHERE Word=%s;"""
                result = cursor.execute(get_word_based_on_score, (word,))
                records = cursor.fetchall()
                response = "**WORD OF THE DAY**\n\nThe word of the day is **"
                for row in records:
                    response = response + str(row[0]) + "** *" + row[1] + "*\n\n" + row[2] + "\n\n"
                
                message_chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
                for chunk in message_chunks:
                    await message.channel.send(">>> " + chunk)
                    time.sleep(3)
            except mysql.connector.Error as error:
                print("error: " + str(error))
            finally:
                if(connection.is_connected()):
                    cursor.close()
                    connection.close()
        elif (command == 'calculatevalues'):
            print("calculatevalues by " + username)
            if (message.author.id != 610335542780887050):
                await message.channel.send("Admin command only!")
                return
            word_scores = {}   
            await message.channel.send("Calculating word values. Bot will be unavailable until word values calculated.")
            get_all_words_query = """SELECT Word FROM DictionaryDefs;"""
            try:
                connection = mysql.connector.connect(host='localhost', database='AuthorMaton', user='REDACTED', password='REDACTED')
                cursor = connection.cursor()
                result = cursor.execute(get_all_words_query)
                records = cursor.fetchall()
                letter_values = { "E" : 1, "A" : 1, "I" : 1, "O" : 1, "N" : 1, "R" : 1, "T" : 1, "L" : 1, "S" : 1, "U" : 1, "D" : 2, "G" : 2, "B" : 3, "C" : 2, "M" : 3, "P" : 2, "F" : 4, "H" : 4, "V" : 4, "W" : 4, "Y" : 4, "K" : 5, "J" : 8, "X" : 8, "Q" : 10, "Z" : 10, "-": 0, " " : 0}
                 
                for row in records:
                    print("Processing " + str(row[0]) + "...")
                    length_score = len(str(row[0]))
                    letter_score = 0
                    for x in str(row[0]).upper():
                        letter_score = letter_score + letter_values[x]
                    word_scores[str(row[0])] = letter_score + length_score
                    print("Word score: " + str(word_scores[str(row[0])]))

            except mysql.connector.Error as error:
                print("error: " + str(error))
            finally:
                if(connection.is_connected()):
                    cursor.close()
                    connection.close()
            create_word_value_table = """CREATE TABLE WordValues (Word varchar(300), WordValue Int);"""
            try:
                connection = mysql.connector.connect(host='localhost', database='AuthorMaton', user='REDACTED', password='REDACTED')
                cursor = connection.cursor()
                result = cursor.execute(create_word_value_table)
            except mysql.connector.Error as error:
                print("error: " + str(error))
            finally:
                if(connection.is_connected()):
                    cursor.close()
                    connection.close()
            create_word_value_entry = """INSERT INTO WordValues (Word, WordValue) VALUES (%s, %s);"""
            for word in word_scores:
                try:
                    word_value_entry = (word, word_scores[word])
                    connection = mysql.connector.connect(host='localhost', database='AuthorMaton', user='REDACTED', password='REDACTED')
                    cursor = connection.cursor()
                    result = cursor.execute(create_word_value_entry, word_value_entry)
                    connection.commit()
                except mysql.connector.Error as error:
                    print("Error: " + str(error))
                    #await message.channel.send("Database error! " + str(error))   
                finally:
                    if(connection.is_connected()):
                        cursor.close()
                        connection.close()
        elif (command == 'setentrylimit'):
            print("calculatevalues by " + username)
            if (message.author.id != 610335542780887050):
                await message.channel.send("Admin command only!")
                return
            entry_limit = int(command_string[1])
            await message.channel.send("Entry limit set to " + str(entry_limit) + ".")
        elif (command == 'loadwords'):
            print("loadwords called by " + username)
            if (message.author.id != 610335542780887050):
                await message.channel.send("Admin command only!")
                return
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
            sample_sentence_re = re.compile(r"#\*.*|#:")
            part_of_speech_re = re.compile(r"Adjective|Noun|Verb|Adverb|Pronoun|Conjunction|Preposition|Interjection")
            english_re = re.compile(r"=English=")
            etym_re = re.compile(r"=Etymology")
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
            wiki_re = re.compile(r"[\[|\]|\{|\}|\|]")
            extra_clear_re = re.compile(r"\s+lb\s+|", re.MULTILINE | re.S)
            extra_extra_clear_re = re.compile("\s+en\s+|;en\s+|^en\s+|\|en\s+|\|en", re.MULTILINE | re.S)
            title_re = re.compile(r"<title>(?P<word>.*)</title>")
            text_begin_re = re.compile(r"<text", re.MULTILINE | re.S)
            text_end_re = re.compile(r"</text>", re.MULTILINE | re.S)
            id_re = re.compile(r"<id>(?P<id>.*)</id>")
            symbol_re = re.compile(r"ref.*?;|&.+?;", re.MULTILINE | re.S)
            definition_re = re.compile(r"^\#+\s+.*", re.MULTILINE | re.S)
            synonym_re = re.compile(r"=Synonyms=")
            antonym_re = re.compile(r"=Antonyms=")
            remove_first_separator_re = re.compile(r"^\s*?[;,]\s+?")
            syn_word_re = re.compile(r"\|.*?\}\}", re.MULTILINE | re.S)
            ant_word_re = re.compile(r"\|.*?\}\}", re.MULTILINE | re.S)
            page_end_re = re.compile(r"</page>")
            line_skip_re = re.compile(r"[A-Za-z]")
            def_exclude_re = re.compile(r"infl of|inflection of|verb form|verb-form|imperative of")
            blank_re = re.compile(r"^\s+$")
            sentence_re = re.compile(r"\{\{ux\|en\|(?P<sentence>.*)\}", re.MULTILINE)
            sentence2_re = re.compile("#: ''(?P<sentence>.*)''", re.MULTILINE)
            rhyme_re = re.compile(r"=Rhymes=")
            rhyme_page_end_re = re.compile(r"</page>")
            space_clear_re = re.compile(r"\s+", re.MULTILINE | re.S)
            rhyme_pro_re = re.compile(r"\{\{rhymes\|en\|(?P<rhymepro>.*)\}\}", re.MULTILINE | re.S)
            rhyme_page_re = re.compile(r"title>Rhymes:English.(?P<pro>.*?)</title", re.MULTILINE | re.S)
            skip_stuff_re = re.compile(r"Index:|Category:|Appendix:|Wiktionary:|Esperanto|[^A-Z-a-z]+")
            rhyme_pronunciation = " "
            sample_sentences = " "
            rhyme_pro = " "
            rhyme_page_content = " "
            rhyme_list = " "
            skip_page = False
            text_line_counter = 0
            text_flag = False
            skip_rest_of_page = False
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
                        skip_rest_of_page = False
                    print("Processing " + word + "...")
                    definition = " "
                    synonyms = " "
                    antonyms = " "
                    rhyme_list = " "
                    rhyme_pro = " "
                    sample_sentences = " "
                    part_of_speech = "unknown"
                    new_word = True
                    syn_flag = False
                    ant_flag = False
                    rhyme_flag = False


                else:
                    new_word = False
                if (text_begin_re.search(line)):
                    text_flag = True
                    text_line_counter = 0

                    
                if english_re.search(line):
                    print("FOund English tag!")
                    text_flag = False
                    text_line_counter = 0

                if text_end_re.search(line):
                    text_flag = False
                    text_line_counter = 0
                    
                if (text_flag and not english_re.search(line)):
                    text_line_counter = text_line_counter + 1
                if (text_line_counter > 2 and text_flag):
                    skip_page = True


          
                if not skip_page:    
                    m = id_re.search(line)
                    if m:
                        id = m.group('id')
                    
                    m = rhyme_pro_re.search(line)
                    if m:
                        rhyme_pro = m.group('rhymepro')
                        
                    if (part_of_speech_re.search(line) and not new_word and not def_exclude_re.search(definition) and not skip_rest_of_page and not definition == ' '):
                        try:

                            connection = mysql.connector.connect(host='localhost', database='AuthorMaton', user='REDACTED', password='REDACTED')    
                            definition = re.sub(remove_first_separator_re,"",definition)
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
                        continue
                        id = str(int(id) + 1)
                        definition = " "
                    if (translations_re.search(line)):
                        skip_rest_of_page = True
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
                        temp_def = re.sub(wiki_re," ",temp_def)
                        temp_def = re.sub(extra_clear_re,"",temp_def)
                        while(extra_extra_clear_re.search(temp_def)):
                            temp_def = re.sub(extra_extra_clear_re,"",temp_def)
                        temp_def = re.sub(text_end_re, "",temp_def)
                        temp_def = temp_def.replace("\n","")
                        temp_def = re.sub(symbol_re,"",temp_def)
                        temp_def = re.sub(r"^\s*;\s+","",temp_def)
                        temp_def = re.sub("ref.*?;","",temp_def)
                        temp_def = re.sub(space_clear_re," ",temp_def)
                        temp_def = re.sub(r"_","",temp_def)
                        temp_def = re.sub(r"\s+\.",".",temp_def)
                        temp_def = re.sub(r"\s+.*?=.*?\s+","",temp_def)
                        

                        definition = definition + "; " + temp_def


                    if sentence_re.search(line):
                        sentence = sentence_re.search(line).group('sentence')
                        sentence = re.sub(wiki_re," ",sentence)
                        sentence = re.sub("'''","*",sentence)
                        sentence = sentence.replace("\n","")
                        sentence = re.sub(space_clear_re," ",sentence)
                        sample_sentences = sample_sentences + "; " + sentence
                    elif sentence_re.search(line):
                        sentence = sentence_re.search(line).group('sentence')
                        sentence = re.sub(wiki_re," ",sentence)
                        sentence = re.sub("'''","*",sentence)
                        sentence = sentence.replace("\n","")
                        sentence = re.sub(space_clear_re," ",sentence)
                        sample_sentences = sample_sentences + "; " + sentence 
                    else:
                        pass                        
                    if (syn_flag and "==" in line):
                        syn_flag = False           
                        
                    if (synonym_re.search(line)):
                        syn_flag = True

                    if (syn_flag):
                        syns = re.findall(syn_word_re,line)
                        for syn in syns:
                            temp_syn = re.sub("#+","",line)
                            temp_syn = re.sub(wiki_re," ",temp_syn)
                            temp_syn = re.sub(extra_clear_re,"",temp_syn)
                            while(extra_extra_clear_re.search(temp_syn)):
                                temp_syn = re.sub(extra_extra_clear_re,"",temp_syn)
                            temp_syn = re.sub(text_end_re, "",temp_syn)
                            temp_syn = temp_syn.replace("\n","")
                            temp_syn = re.sub(symbol_re,"",temp_syn)
                            temp_syn = re.sub(r"^\s*;\s+","",temp_syn)
                            temp_syn = re.sub("ref.*?;","",temp_syn)
                            temp_syn = re.sub(space_clear_re," ",temp_syn)
                            temp_syn = temp_syn.replace(" len ","")
                            temp_syn = re.sub(r"_","",temp_syn)
                            temp_syn = re.sub(r"\s+\.",".",temp_syn)
                            temp_syn = re.sub(r"\s+.*?=.*?\s+","",temp_syn)
                            synonyms = synonyms + ", " + temp_syn
                    if (ant_flag and not skip_rest_of_page):
                        ants = re.findall(ant_word_re,line)
                        for ant in ants:
                            temp_ant = re.sub("#+","",line)
                            temp_ant = re.sub(wiki_re," ",temp_ant)
                            temp_ant = re.sub(extra_clear_re,"",temp_ant)
                            while(extra_extra_clear_re.search(temp_ant)):
                                temp_ant = re.sub(extra_extra_clear_re,"",temp_ant)
                            temp_ant = re.sub(text_end_re, "",temp_ant)
                            temp_ant = temp_ant.replace("\n","")
                            temp_ant = re.sub(symbol_re,"",temp_ant)
                            temp_ant = re.sub(r"^\s*;\s+","",temp_ant)
                            temp_ant = re.sub("ref.*?;","",temp_ant)
                            temp_ant = re.sub(space_clear_re," ",temp_ant)
                            temp_ant = temp_ant.replace(" len ","")
                            temp_ant = re.sub(r"_","",temp_ant)
                            temp_ant = re.sub(r"\s+\.",".",temp_ant)
                            temp_ant = re.sub(r"\s+.*?=.*?\s+","",temp_ant)
                            antonyms = antonyms + ", " + temp_ant
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
                        rhyme_list = rhyme_list + ", " + line
                        rhyme_list = re.sub(wiki_re," ",rhyme_list)
                        rhyme_list = re.sub(extra_clear_re,"",rhyme_list)
                        while(extra_extra_clear_re.search(temp_rhyme)):
                                temp_rhyme = re.sub(extra_extra_clear_re,"",temp_rhyme)
                        rhyme_list = re.sub(space_clear_re," ",rhyme_list)
                        
                    
                    if (page_end_re.search(line) and not definition == ' '):
                        try:

                            connection = mysql.connector.connect(host='localhost', database='AuthorMaton', user='REDACTED', password='REDACTED')                
                            create_dictionary_entry = """INSERT INTO DictionaryDefs (Id, Word, PartOfSpeech, Definitions, Pronunciation) VALUES(%s, %s, %s, %s, %s);"""   
                            create_thesaurus_entry = """INSERT INTO Thesaurus (Id, Word, Synonyms, Antonyms) VALUES (%s, %s, %s, %s);"""
                            create_rhyme_entry = """INSERT INTO Rhyming (Id, Word, RhymesWith) VALUES (%s, %s, %s);"""
                            create_sentence_entry = """INSERT INTO SampleSentences (Word, Sentences) VALUES (%s, %s);"""
                            
                            definition = re.sub(remove_first_separator_re,"",definition)
                            synonyms = re.sub(remove_first_separator_re,"",synonyms)
                            antonyms = re.sub(remove_first_separator_re,"",antonyms)
                            rhyme_list = re.sub(remove_first_separator_re,"",rhyme_list)
                            sample_sentences = re.sub(remove_first_separator_re,"",sample_sentences)
                            dictionary_entry = (id, word, part_of_speech, definition, rhyme_pro)
                            thesaurus_entry = (id, word, synonyms, antonyms)
                            rhyme_entry = (id, word, rhyme_list)
                            sentences_entry = (word, sample_sentences)
                            cursor = connection.cursor()
                            result = cursor.execute(create_dictionary_entry, dictionary_entry)
                            result = cursor.execute(create_thesaurus_entry, thesaurus_entry)
                            result = cursor.execute(create_rhyme_entry, rhyme_entry)
                            result = cursor.execute(create_sentence_entry, sentences_entry)
                            connection.commit()
                            word_count = word_count + 1
                        except mysql.connector.Error as error:
                            print("Error: " + str(error))
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
                            temp_rhyme = re.sub(wiki_re," ",temp_rhyme)
                            temp_rhyme = re.sub(extra_clear_re,"",temp_rhyme)
                            temp_rhyme = re.sub("rhyme list begin","",temp_rhyme)
                            temp_rhyme = re.sub("rhyme list end","",temp_rhyme)
                            temp_rhyme = re.sub(space_clear_re," ",temp_rhyme)
                            temp_rhyme = temp_rhyme.replace(" len ","")
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
            print("No command recognized by " + username)
            await message.channel.send("Invalid command.\n\nType **.info** for a list of available commands.")
    else:
        pass
client.run('REDACTED')    
