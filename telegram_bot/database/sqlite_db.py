import sqlite3 as sql
from create_bot import bot

def sql_start():
    global db, cur
    db = sql.connect('tech.db')
    cur = db.cursor()
    if db:
        print('Data base connected')
    db.execute('CREATE TABLE IF NOT EXISTS type_problem(id integer primary key autoincrement, name TEXT)')
    db.commit()
    db.execute('CREATE TABLE IF NOT EXISTS problem(id integer primary key autoincrement, id_type integer, name TEXT, decision TEXT)')
    db.commit()

async def sql_read(message):
    for item in cur.execute('SELECT * FROM problem').fetchall():
        await bot.send_photo(message.from_user.id, item[0], f'{item[1]}\nОписание: {item[2]}\nЦена {item[-1]} руб')

async def sql_read2():
    return cur.execute('SELECT * FROM problem').fetchall()

async def sql_read_categories():
    return cur.execute('SELECT * FROM type_problem').fetchall()

async def sql_read_problems(data):
    return cur.execute('SELECT * FROM problem WHERE id_type == ?', (data,)).fetchall()

async def sql_read_decision(data):
    return cur.execute('SELECT decision FROM problem WHERE id == ?', (data,)).fetchone()

async def sql_delete_command(data):
    cur.execute('DELETE FROM problem WHERE name == ?', (data,))
    db.commit()