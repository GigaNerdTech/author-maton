import discord
import re
import mysql.connector
from mysql.connector import Error
from PyDictionary import PyDictionary
import subprocess
import time

dictionary = PyDictionary()
client = discord.Client()

@client.event
async def on_ready():
    print("Logged in!")
    

   
@client.event
async def on_message(message):

    if message.content.startswith('.'):
        command_string = message.content.split(' ')
        command = command_string[0].replace('.','',1)
        
        if (command == 'sayhi'):
            await message.channel.send("Hello there!")
            
        if (command == 'initialize'):
            await message.channel.send("Creating databases...")
            try:
                connection = mysql.connector.connect(host='localhost', database='AuthorMaton', user='REDACTED ', password='REDACTED ')
                
                
                create_literature_store_table = """CREATE TABLE Literature (Id int NOT NULL, Title varchar(400), Author varchar(100), Permissions int, PostContent varchar(2000));"""
                
                cursor = connection.cursor()
                result = cursor.execute(create_literature_store_table)
                await message.channel.send("Database created successfully.")
            except mysql.connector.Error as error:
                await message.channel.send("Database error! " + str(error))
            finally:
                if(connection.is_connected()):
                    cursor.close()
                    connection.close()
        if(command == 'writingprompt'):
            await message.channel.send("Coming soon!")
        if (command == "savepost"):
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
            
            get_last_id_query = """SELECT MAX(Id) FROM Literature"""
            
            try:
                connection = mysql.connector.connect(host='localhost', database='AuthorMaton', user='REDACTED ', password='REDACTED ')
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
                connection = mysql.connector.connect(host='localhost', database='AuthorMaton', user='REDACTED ', password='REDACTED ')
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
        if (command == 'getpost'):
            parsed_string = message.content.replace('.getpost ','')
            print("Title: " + parsed_string)
            
            get_post_query = """SELECT Title,Author,PostContent FROM Literature WHERE Title=%s;"""
            
            try:
                connection = mysql.connector.connect(host='localhost', database='AuthorMaton', user='REDACTED ', password='REDACTED ')
                cursor = connection.cursor()
                result = cursor.execute(get_post_query, (parsed_string,))
                records = cursor.fetchall()
                for row in records:
                    await message.channel.send(">>> **" + str(row[0]) + "**\n*By " + row[1] + "*\n\n" + row[2])
            except mysql.connector.Error as error:
                await message.channel.send("Database error!" + str(error))
            finally:
                if(connection.is_connected()):
                    cursor.close()
                    connection.close() 
        if (command == 'resetall'):
            clear_all_query = """DROP TABLE Literature; CREATE TABLE Literature (Id int NOT NULL, Title varchar(400), Author varchar(100), Permissions int, PostContent varchar(2000));"""
            try:
                connection = mysql.connector.connect(host='localhost', database='AuthorMaton', user='REDACTED ', password='REDACTED ')          
                cursor = connection.cursor()
                result = cursor.execute(clear_all_query)
                await message.channel.send("Database created successfully.")
            except mysql.connector.Error as error:
                await message.channel.send("Database error! " + str(error))
            finally:
                if(connection.is_connected()):
                    cursor.close()
                    connection.close()
        if (command == 'define'):
            word = command_string[1]
            dictionary_entry = dictionary.meaning(word)
            
            response = ">>> **" + word +"**\n\n"
            for part_of_speech in dictionary_entry:
                response = response + "*" + str(part_of_speech) + "* :"
                for definition in dictionary_entry[part_of_speech]:
                    response = response + definition + "\n\n"
            
            await message.channel.send(response)
        if (command == 'synonym'):
            word = command_string[1]
            output = subprocess.run(["/home/REDACTED /MyThes-1.0/thesaurus","/home/REDACTED /MyThes-1.0/th_en_US_new.idx","/home/REDACTED /MyThes-1.0/th_en_US_new.dat",word], universal_newlines=True, stdout=subprocess.PIPE)
            
            message_chunks = [output.stdout[i:i+1500] for i in range(0, len(output.stdout), 2000)]
            for chunk in message_chunks:
                await message.channel.send(">>> " + chunk)
                time.sleep(3)
            
            
            
            
        if (command == 'antonym'):
            word = command_string[1]
            antonyms = dictionary.antonym(word)
            
            response = ">>> **" + word + "**\n\n"
            for antonym in antonyms:
                response = response + antonym + "\n"
            await message.channel.send(response)
            
            
client.run('CLIENT KEY')    
