import csv, json
import psycopg2 as pg
import psycopg2.extras

db_connect = {
    'user': 'db3',
    'password': '1234'
}
conn_str = "user={user} password={password}".format(**db_connect)

def readBank():
    conn = pg.connect(conn_str)
    conn.autocommit = True
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    with open('bank.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            bid = row['bid']
            code = row['code']
            name = row['name']
            sql = f"INSERT INTO bank VALUES({bid}, {code}, '{name}')"
            cur.execute(sql)
    conn.close()

def readCustomers():
    conn = pg.connect(conn_str)
    conn.autocommit = True
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cid = 0
    with open('customers.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row['name']
            phone = row['phone']
            email = row['local'] + '@' + row['domain']
            passwd = row['passwd']
            payments = json.loads(row['payments'])
            lat = row['lat']
            lng = row['lng']
            sql = f"INSERT INTO customers VALUES('{email}', '{name}', '{phone}', '{passwd}', '{payments}', {lat}, {lng}, {cid})"
            cid += 1
            cur.execute(sql)
    conn.close()

def readDelivery():
    conn = pg.connect(conn_str)
    conn.autocommit = True
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    with open('delivery.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            did = row['did']
            name = row['name']
            phone = row['phone']
            email = row['local'] + '@' + row['domain']
            passwd = row['passwd']
            lat = row['lat']
            lng = row['lng']
            stock = row['stock']
            sql = f"INSERT INTO delivery VALUES({did}, '{name}', '{phone}', '{email}', '{passwd}', {lat}, {lng}, {stock})"
            cur.execute(sql)
    conn.close()

def readMenu():
    conn = pg.connect(conn_str)
    conn.autocommit = True
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    with open('menu.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            menu = row['menu']
            sid = row['sid']
            sql = f"INSERT INTO menu VALUES('{menu}', {sid})"
            cur.execute(sql)
    conn.close()

def readSellers():
    conn = pg.connect(conn_str)
    conn.autocommit = True
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    with open('sellers.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            seller_id = row['seller_id']
            name = row['name']
            phone = row['phone']
            email = row['local'] + '@' + row['domain']
            passwd = row['passwd']
            sql = f"INSERT INTO sellers VALUES({seller_id}, '{name}', '{phone}', '{email}', '{passwd}')"
            cur.execute(sql)
    conn.close()

def readStores():
    conn = pg.connect(conn_str)
    conn.autocommit = True
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    with open('stores.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sid = row['sid']
            address = row['address']
            sname = row['sname']
            lat = row['lat']
            lng = row['lng']
            phone_nums = row['phone_nums']
            schedules = row['schedules']
            seller_id = row['seller_id']
            sql = f"INSERT INTO stores VALUES({sid}, '{address}', '{sname}', {lat}, {lng}, '{phone_nums}', '{schedules}', {seller_id})"
            cur.execute(sql)
    conn.close()

if __name__ == "__main__":
    print('')
    # readBank()
    readCustomers()
    # readDelivery()
    # readSellers()
    # readStores()
    # readMenu()