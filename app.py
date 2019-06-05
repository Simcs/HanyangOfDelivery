from flask import Flask, render_template, redirect, request, flash, url_for
from math import cos, asin, sqrt
from datetime import datetime
import json, ast, operator, time
import psycopg2 as pg
import psycopg2.extras

t_seller = "seller"
t_customer = "customer"
t_delivery = "delivery"

status = {'login':False, 'type':"", 'user':{}}

db_connect = {
    'user': 'db3',
    'password': '1234'
}
conn_str = "user={user} password={password}".format(**db_connect)

app = Flask(__name__)
app.secret_key = "secret_key"
account = []

@app.route("/")
def index():
    if not status['login']:
        return render_template("index.html")
    
    conn = pg.connect(conn_str)
    conn.autocommit = True
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    if status['type'] == t_seller:
        seller_id = status['user']['seller_id']
        sql = f"SELECT * FROM stores WHERE seller_id='{seller_id}'"
        cur.execute(sql)
        stores = cur.fetchall()
        conn.close()
        return render_template("seller.html", user=status['user'], stores=stores)
        
    elif status['type'] == t_customer:
        conn.close()
        return render_template("customer.html", user=status['user'])

    else:
        did = status['user']['did']
        sql = f"SELECT S.sname, C.name AS cname, D.name AS dname, C.phone AS cphone, S.address AS saddress, O.oid, O.ordertime, O.menu "
        sql += f"FROM stores S, customers C, t_order O, orderservice OS, delivery D "
        sql += f"WHERE D.did={did} and O.sid=S.sid and O.cid=C.cid and OS.did=D.did and O.oid=OS.oid"
        cur.execute(sql)
        orders = cur.fetchall()
        conn.close()
        return render_template("delivery.html", user=status['user'], orders=orders)

@app.route("/login")
def showLogin():
    if status['login']:
        return redirect('/')
    return render_template("login.html")
 
@app.route("/login", methods=['POST'])
def login():
    if status['login']:
        return redirect('/')

    conn = pg.connect(conn_str)
    conn.autocommit = True
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    account[:] = []
    email = request.form.get('email')
    passwd = request.form.get('passwd')

    sql = f"SELECT * FROM sellers WHERE email='{email}' and passwd='{passwd}'"
    cur.execute(sql)
    sellers = cur.fetchall()
    for row in sellers:
        account.append({'type':t_seller, 'info':row})
    
    sql = f"SELECT * FROM customers WHERE email='{email}' and passwd='{passwd}'"
    cur.execute(sql)
    customers = cur.fetchall()
    for row in customers:
        account.append({'type':t_customer, 'info':row})
    
    sql = f"SELECT * FROM delivery WHERE email='{email}' and passwd='{passwd}'"
    cur.execute(sql)
    delivery = cur.fetchall()
    for row in delivery:
        account.append({'type':t_delivery, 'info':row})

    conn.close()

    if len(account) == 0:
        return render_template('error.html', type="Login Failed", msg="이메일과 패스워드를 확인해주세요!")
    if len(account) == 1:
        status.update({ 'login':True, 'type':account[0]['type'], 'user':account[0]['info'] })
        return redirect("/")
    return render_template("account.html", accounts=account)

@app.route("/login2", methods=['POST'])
def login2():
    if status['login']:
        return redirect('/')

    _type = request.form.get('type')
    user = {}
    for row in account:
        if row['type'] == _type:
            user = row['info']
            break

    status.update({ 'login':True, 'type':_type, 'user':user })
    return redirect('/')

@app.route("/logout")
def logout():
    status.update({'login':False, 'type':'', 'user':{}})
    return redirect("/")

@app.route("/mybaehan", methods=['GET'])
def showChangeInformation():
    if not status['login']:
        return render_template("error.html", type="Access Denied", msg="로그인이 필요합니다")
    return render_template("info.html")

@app.route("/mybaehan", methods=['POST'])
def changeInformation():
    if not status['login']:
        return render_template("error.html", type="Access Denied", msg="로그인이 필요합니다")

    conn = pg.connect(conn_str)
    conn.autocommit = True
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    name = request.form.get('name')
    passwd = request.form.get('passwd')
    if status['type'] == t_seller:
        dbname = "sellers"
    elif status['type'] == t_customer:
        dbname = "customers"
    else:
        dbname = "delviery"

    sql = f"UPDATE {dbname} SET name='{name}', passwd='{passwd}'"
    sql += f" WHERE email='{status['user']['email']}' AND passwd='{status['user']['passwd']}'"
    status['user']['name'] = name
    status['user']['passwd'] = passwd
    cur.execute(sql)

    conn.close()
    flash('정보가 성공적으로 변경되었습니다')
    return redirect('/')

@app.route("/store/<sid>", methods=['GET'])
def store(sid):
    if not status['login'] or not status['type'] == t_seller:
        return render_template("error.html", type="Access Denied", msg="접근할 수 없습니다")

    day = ["월", "화", "수", "목", "금", "토", "일"]

    conn = pg.connect(conn_str)
    conn.autocommit = True
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    sql = f"SELECT sid FROM stores WHERE sid={sid} and seller_id={status['user']['seller_id']}"
    cur.execute(sql)
    if len(cur.fetchall()) == 0:
        return redirect('/')

    sql = f"SELECT * from stores WHERE sid={sid}"
    cur.execute(sql)
    store = cur.fetchall()
    
    phone_nums = ast.literal_eval(ast.literal_eval(store[0]['phone_nums']))
    schedules = json.loads(json.loads(store[0]['schedules']))

    sql = f"SELECT * from menu WHERE sid={sid}"
    cur.execute(sql)
    menu = cur.fetchall()
    
    for row in schedules:
        row['day'] = day[row['day']] + "요일"
        if not row['holiday']:
            row['open'] = getFormalTime(row['open'])
            row['closed'] = getFormalTime(row['closed'])
    
    sql = f"SELECT O.oid, C.email, C.phone, O.menu, O.quantity, O.payment, O.delivering, O.complete, O.ordertime "
    sql += f"FROM t_order O, customers C "
    sql += f"WHERE O.sid={sid} and O.cid=C.cid"
    cur.execute(sql)
    orders = cur.fetchall()
    for row in orders:
        order = json.loads(row['payment'])
        if order['type'] == 'account':
            row['payment'] = '계좌, ' + order['data']['bank'] + ', 계좌번호 : ' + order['data']['acc_num']
        else:
            row['payment'] = '카드, 카드번호 : ' + order['data']['card_num']
    orders = sorted(orders, key=operator.itemgetter('ordertime'), reverse=True)

    sql = f"SELECT * FROM tag WHERE sid={sid}"
    cur.execute(sql)
    tags = cur.fetchall()

    conn.close()
    return render_template("store_seller.html", store=store[0], phone_nums=phone_nums, schedules=schedules, menu=menu, orders=orders, tags=tags)

def getFormalTime(time):
    result = ''
    hour = int(time[:2])
    minute = time[2:]
    if hour % 24 >= 12:
        result += "오후 "
    else:
        result += "오전 "
    if hour != 12:
        hour %= 12
    result += str(hour) + "시" + minute + "분"
    return result

@app.route("/store/<sid>/menu/edit", methods=["GET"])
def showEditMenu(sid):
    if not status['login'] or not status['type'] == t_seller:
        return redirect('/')

    conn = pg.connect(conn_str)
    conn.autocommit = True
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    sql = f"SELECT sid FROM stores WHERE sid={sid} and seller_id={status['user']['seller_id']}"
    cur.execute(sql)
    if len(cur.fetchall()) == 0:
        return redirect('/')
    
    if 'menu' in request.args:
        return render_template("editMenu.html", menu=request.args.get('menu'), sid=sid)
    else :
        return render_template("editMenu.html", menu="", sid=sid)

@app.route("/store/<sid>/menu/edit", methods=["POST"])
def editMenu(sid):
    if not status['login'] or not status['type'] == t_seller:
        return render_template("error.html", msg="접근할 수 없습니다")
    
    conn = pg.connect(conn_str)
    conn.autocommit = True
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    prev = request.form.get('prev')
    menu = request.form.get('menu')

    if 'delete' in request.form:
        sql = f"DELETE FROM menu WHERE menu='{menu}' and sid={sid}"
        cur.execute(sql)

    elif 'save' in request.form:
        if prev == "":
            sql = f"INSERT INTO menu VALUES('{menu}', {sid})"
            cur.execute(sql)
        else :
            sql = f"UPDATE menu SET menu='{menu}' WHERE menu='{prev}' and sid={sid}"
            cur.execute(sql)

    flash("메뉴가 성공적으로 변경되었습니다")
    conn.close()
    return redirect(url_for('store', sid=sid))

@app.route("/store/<sid>/order", methods=["POST"])
def checkOrder(sid):
    if not status['login'] or not status['type'] == t_seller:
        return render_template("error.html", msg="접근할 수 없습니다")

    conn = pg.connect(conn_str)
    conn.autocommit = True
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    oid = request.form['oid']
    if 'delete' in request.form:
        sql = f"DELETE FROM t_order WHERE oid={oid}"
        cur.execute(sql)
        conn.close()
        return redirect(url_for('store', sid=sid))
    else:
        sql = f"SELECT * FROM t_order WHERE oid={oid}"
        cur.execute(sql)
        order = cur.fetchall()[0]

        sql = f"SELECT * FROM stores WHERE sid={order['sid']}"
        cur.execute(sql)
        store = cur.fetchall()[0]
        s_lat = store['lat']
        s_lng = store['lng']

        delivery = []
        sql = f"SELECT * FROM delivery"
        cur.execute(sql)
        rows = cur.fetchall()
        for row in rows:
            if row['stock'] > 4:
                continue
            tmp = {}
            tmp.update(row)
            tmp.update({'distance':distance(s_lat, s_lng, row['lat'], row['lng'])})
            delivery.append(tmp)

        delivery = sorted(delivery, key=operator.itemgetter('distance'))
        delivery = delivery[:5]
        conn.close()
        return render_template("checkOrder.html", delivery=delivery, oid=oid, sid=sid)

def distance(lat1, lon1, lat2, lon2):
    p = 0.017453292519943295
    a = 0.5 - cos((lat2 - lat1) * p) / 2 + cos(lat1 * p) * cos(lat2 * p) * (1 - cos((lon2 - lon1) * p)) / 2
    return 12742 * asin(sqrt(a))

@app.route("/store/<sid>/order/confirm", methods=['POST'])
def confirmOrder(sid):
    if not status['login'] or not status['type'] == t_seller:
        return render_template("error.html", msg="접근할 수 없습니다")
    
    conn = pg.connect(conn_str)
    conn.autocommit = True
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    oid = request.form['oid']
    did = request.form['did']
    sql = f"UPDATE t_order SET delivering={True} WHERE oid={oid}"
    cur.execute(sql)

    sql = f"INSERT INTO orderService VALUES({oid}, {did})"
    cur.execute(sql)

    sql = f"UPDATE delivery SET stock = stock + 1 WHERE did={did}"
    cur.execute(sql)

    conn.close()
    return redirect(url_for('store', sid=sid))

@app.route("/address/<cid>", methods=["GET"])
def address(cid):
    if not status['login'] or not status['type'] == t_customer or not status['user']['cid'] == int(cid):
        return render_template("error.html", msg="접근할 수 없습니다")

    conn = pg.connect(conn_str)
    conn.autocommit = True
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    cid = status['user']['cid']
    sql = f"SELECT * FROM address WHERE cid={cid}"
    cur.execute(sql)
    address = cur.fetchall()

    conn.close()
    return render_template("address.html", customer=status['user'], address=address)

@app.route("/address/<cid>/edit", methods=["GET"])
def showEditAddress(cid):
    if not status['login'] or not status['type'] == t_customer or not status['user']['cid'] == int(cid):
        return render_template("error.html", msg="접근할 수 없습니다")
    return render_template("editAddress.html", address=request.args.get('address'), cid=cid)

@app.route("/address/<cid>/edit", methods=["POST"])
def editAddress(cid):
    if not status['login'] or not status['type'] == t_customer:
        return render_template("error.html", msg="접근할 수 없습니다")
    
    conn = pg.connect(conn_str)
    conn.autocommit = True
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    prev = request.form.get('prev')
    address = request.form.get('address')

    if 'delete' in request.form:
        sql = f"DELETE FROM address WHERE address='{address}' and cid={cid}"
        cur.execute(sql)

    elif 'save' in request.form:
        if prev == "":
            sql = f"INSERT INTO address VALUES({cid}, '{address}')"
            cur.execute(sql)
        else :
            sql = f"UPDATE address SET address='{address}' WHERE address='{prev}' and cid={cid}"
            cur.execute(sql)

    conn.close()
    return redirect(url_for('address', cid=cid))

@app.route("/customer/shopping", methods=['GET'])
def getGeolocation():
    if not status['login'] or not status['type'] == t_customer:
        return render_template("error.html", msg="접근할 수 없습니다")
    return render_template("geo.html")

@app.route("/customer/shopping", methods=['POST'])
def shopping():
    if not status['login'] or not status['type'] == t_customer:
        return render_template("error.html", msg="접근할 수 없습니다")

    conn = pg.connect(conn_str)
    conn.autocommit = True
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cid = status['user']['cid']
    today = time.localtime().tm_wday

    if 'lat' in request.form and 'lng' in request.form:
        lat = float(request.form['lat'])
        lng = float(request.form['lng'])
    else:
        sql = f"SELECT * FROM customers WHERE cid={cid}"
        cur.execute(sql)
        customer = cur.fetchall()[0]
        lat = customer['lat']
        lng = customer['lng']

    stores = []
    sql = f"SELECT * FROM stores"
    cur.execute(sql)
    rows = cur.fetchall()

    for row in rows:
        schedules = json.loads(json.loads(row['schedules']))
        if schedules[today]['holiday']:
            continue

        tmp = {}
        tmp.update(row)
        tmp.update({'distance':distance(lat, lng, row['lat'], row['lng'])})
        stores.append(tmp)

    stores = sorted(stores, key=operator.itemgetter('distance'))
    stores = stores[:10]
    conn.close()

    return render_template("shopping.html", stores=stores, cid=cid)

@app.route("/customer/search", methods=["GET"])
def searchStore():
    if not status['login'] or not status['type'] == t_customer:
        return render_template("error.html", msg="접근할 수 없습니다")

    conn = pg.connect(conn_str)
    conn.autocommit = True
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cid = status['user']['cid']
    if 'address' in request.args or 'tag' in request.args or 'name' in request.args:
        if 'address' in request.args:
            address = request.args.get('address')
            sql = f"SELECT * FROM stores WHERE address LIKE '%{address}%' GROUP BY sid"
        elif 'tag' in request.args:
            tag = request.args.get('tag')
            sql = f"SELECT * FROM stores S, tag T WHERE T.tag LIKE '%{tag}%' and S.sid = T.sid"
        elif 'name' in request.args:
            name = request.args.get('name')
            sql = f"SELECT * FROM stores WHERE sname LIKE '%{name}%' GROUP BY sid"

        cur.execute(sql)
        result = cur.fetchall()
        result = result[:500]
        conn.close()
        return render_template("searchResult.html", result=result, cid=cid)
    else:
        conn.close()
        return redirect('/')

@app.route("/customer/shopping/<sid>", methods=['GET'])
def showStore(sid):
    if not status['login'] or not status['type'] == t_customer:
        return render_template("error.html", msg="접근할 수 없습니다")

    day = ["월", "화", "수", "목", "금", "토", "일"]

    conn = pg.connect(conn_str)
    conn.autocommit = True
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    sql = f"SELECT sid FROM stores WHERE sid={sid}"
    cur.execute(sql)
    if len(cur.fetchall()) == 0:
        return redirect('/')

    sql = f"SELECT * from stores WHERE sid={sid}"
    cur.execute(sql)
    store = cur.fetchall()[0]
    
    phone_nums = ast.literal_eval(ast.literal_eval(store['phone_nums']))
    schedules = json.loads(json.loads(store['schedules']))

    sql = f"SELECT * from menu WHERE sid={sid}"
    cur.execute(sql)
    menu = cur.fetchall()
    
    for row in schedules:
        row['day'] = day[row['day']] + "요일"
        if not row['holiday']:
            row['open'] = getFormalTime(row['open'])
            row['closed'] = getFormalTime(row['closed'])

    sql = f"SELECT * FROM tag WHERE sid={sid}"
    cur.execute(sql)
    tags = cur.fetchall()

    cid = status['user']['cid']

    conn.close()
    return render_template("store_customer.html", store=store, phone_nums=phone_nums, schedules=schedules, menu=menu, tags=tags, cid=cid)

@app.route("/customer/shopping/<sid>/order", methods=['GET'])
def showOrderMenu(sid):
    if not status['login'] or not status['type'] == t_customer:
        return render_template("error.html", msg="접근할 수 없습니다")

    conn = pg.connect(conn_str)
    conn.autocommit = True
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    today = time.localtime().tm_wday
    sql = f"SELECT sid FROM stores WHERE sid={sid}"
    cur.execute(sql)
    if len(cur.fetchall()) == 0:
        conn.close()
        return render_template("error.html", msg="존재하지 않는 가게입니다")

    sql = f"SELECT * FROM stores WHERE sid={sid}"
    cur.execute(sql)
    store = cur.fetchall()[0]
    schedules = json.loads(json.loads(store['schedules']))
    if schedules[today]['holiday']:
        flash("현재 영업중이 아닙니다")
        return redirect(url_for('showStore', sid=sid))

    sql = f"SELECT * FROM menu WHERE sid={sid}"
    cur.execute(sql)
    menu = cur.fetchall()

    sql = f"SELECT payments FROM customers WHERE cid={status['user']['cid']}"
    cur.execute(sql)
    payments = cur.fetchall()

    sql = f"SELECT count(*) as cnt FROM address WHERE cid={status['user']['cid']}"
    cur.execute(sql)
    address_cnt = cur.fetchall()[0]['cnt']

    conn.close()
    return render_template("orderMenu.html", store=store, menu=menu, payments=payments, addr_cnt=address_cnt)

@app.route("/customer/shopping/<sid>/order", methods=['POST'])
def orderMenu(sid):
    if not status['login'] or not status['type'] == t_customer:
        return render_template("error.html", msg="접근할 수 없습니다")

    conn = pg.connect(conn_str)
    conn.autocommit = True
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    sql = f"SELECT * FROM menu WHERE sid={sid}"
    cur.execute(sql)
    menu = cur.fetchall()

    sql = f"SELECT * FROM stores WHERE sid={sid}"
    cur.execute(sql)
    store = cur.fetchall()[0]

    order = []
    for row in menu:
        attr = 'q_' + row['menu']
        if request.form[attr] == '' or int(request.form[attr]) <= 0:
            continue
        quantity = request.form[attr]
        menu = row['menu']
        order.append({'menu':menu, 'quantity':quantity})

    sql = f"SELECT payments FROM customers WHERE cid={status['user']['cid'] }"
    cur.execute(sql)
    payments = json.loads(cur.fetchall()[0]['payments'])
    for row in payments:
        if row['type'] == 'account':
            sql = f"SELECT name FROM bank WHERE bid={row['data']['bid']}"
            cur.execute(sql)
            row['data']['bid'] = cur.fetchall()[0]['name']
    
    conn.close()
    return render_template("payment.html", store=store, orders=order, payments=payments)

@app.route("/customer/shopping/<sid>/order/confirm", methods=["POST"])
def selectPayment(sid):
    if not status['login'] or not status['type'] == t_customer:
        return render_template("error.html", msg="접근할 수 없습니다")

    conn = pg.connect(conn_str)
    conn.autocommit = True
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    sql = f"SELECT max(oid) AS max FROM t_order"
    cur.execute(sql)
    tmp = cur.fetchall()
    if tmp[0]['max'] == None:
        idx = 0
    else:
        idx = tmp[0]['max'] + 1

    payment = {}
    payment["type"] = request.form['type']
    if payment["type"] == 'account':
        payment["data"] = {'bank':request.form['bank'], 'acc_num':request.form['acc_num']}
    elif payment["type"] == 'card':
        payment["data"] = {'card_num':request.form['card_num']}

    order = ast.literal_eval(request.form['order'])
    for row in order:
        oid = idx
        cid = status['user']['cid']
        menu = row['menu']
        quantity = row['quantity']
        ordertime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        sql = f"INSERT INTO t_order VALUES({oid}, {sid}, {cid}, '{menu}', {quantity}, '{ordertime}', false, false, '{json.dumps(payment)}')"
        cur.execute(sql)        
        idx += 1
    
    flash("주문이 성공적으로 접수되었습니다")
    conn.close()
    return redirect(url_for('showStore', sid=sid))

@app.route("/customer/order")
def showOrder():
    if not status['login'] or not status['type'] == t_customer:
        return render_template("error.html", msg="접근할 수 없습니다")

    conn = pg.connect(conn_str)
    conn.autocommit = True
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cid = status['user']['cid']
    sql = f"SELECT O.oid, O.menu, O.payment, O.ordertime, O.quantity, S.sname "
    sql += f"FROM t_order O, stores S "
    sql += f"WHERE O.complete=true and O.cid={cid} and S.sid=O.sid"
    cur.execute(sql)
    complete = cur.fetchall()

    sql = f"SELECT O.oid, O.menu, O.payment, O.ordertime, O.quantity, S.sname, D.name, D.phone, D.did "
    sql += f"FROM t_order O, delivery D, orderservice OS, stores S "
    sql += f"WHERE O.delivering=true and complete=false and OS.oid=O.oid and S.sid=O.sid and D.did=OS.did and O.cid={cid}"
    cur.execute(sql)
    ondelivery = cur.fetchall()

    sql = f"SELECT O.oid, O.menu, O.payment, O.ordertime, O.quantity, S.sname "
    sql += f"FROM t_order O, stores S "
    sql += f"WHERE O.delivering=false and O.cid={cid} and S.sid=O.sid"
    cur.execute(sql)
    notcheck = cur.fetchall()

    for row in complete:
        tmp = json.loads(row['payment'])
        if tmp['type'] == 'account':
            row['payment'] = '계좌, ' + tmp['data']['bank'] + ', 계좌번호 : ' + tmp['data']['acc_num']
        else:
            row['payment'] = '카드, 카드번호 : ' + tmp['data']['card_num']
    complete = sorted(complete, key=operator.itemgetter('ordertime'), reverse=True)

    for row in ondelivery:
        tmp = json.loads(row['payment'])
        if tmp['type'] == 'account':
            row['payment'] = '계좌, ' + tmp['data']['bank'] + ', 계좌번호 : ' + tmp['data']['acc_num']
        else:
            row['payment'] = '카드, 카드번호 : ' + tmp['data']['card_num']
    ondelivery = sorted(ondelivery, key=operator.itemgetter('ordertime'), reverse=True)

    for row in notcheck:
        tmp = json.loads(row['payment'])
        if tmp['type'] == 'account':
            row['payment'] = '계좌, ' + tmp['data']['bank'] + ', 계좌번호 : ' + tmp['data']['acc_num']
        else:
            row['payment'] = '카드, 카드번호 : ' + tmp['data']['card_num']
    notcheck = sorted(notcheck, key=operator.itemgetter('ordertime'), reverse=True)

    sql = f"SELECT payments FROM customers WHERE cid={status['user']['cid'] }"
    cur.execute(sql)
    rows = json.loads(cur.fetchall()[0]['payments'])
    payments = []
    for row in rows:
        tmp = {}
        tmp.update(row)
        if row['type'] == 'account':
            sql = f"SELECT name FROM bank WHERE bid={row['data']['bid']}"
            cur.execute(sql)
            tmp['data'].update({'bname':cur.fetchall()[0]['name']})
        payments.append(tmp)

    conn.close()
    return render_template("order.html", complete=complete, ondelivery=ondelivery, notcheck=notcheck, payments=payments)
    
@app.route("/customer/order/confirm", methods=["POST"])
def confirmDelivery():
    if not status['login'] or not status['type'] == t_customer:
        return render_template("error.html", msg="접근할 수 없습니다")
    
    conn = pg.connect(conn_str)
    conn.autocommit = True
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    oid = request.form['oid']
    did = request.form['did']

    sql = f"DELETE FROM orderservice WHERE oid={oid} and did={did}"
    cur.execute(sql)

    sql = f"UPDATE t_order SET complete=true WHERE oid={oid}"
    cur.execute(sql)

    sql = f"UPDATE delivery SET stock = stock - 1 WHERE did={did}"
    cur.execute(sql)
    conn.close()

    return redirect("/customer/order")

@app.route("/customer/order/payment", methods=["GET"])
def showEditPayment():
    if not status['login'] or not status['type'] == t_customer:
        return render_template("error.html", msg="접근할 수 없습니다")
    
    payment = {'type':''}
    if 'type' in request.args:
        if request.args['type'] == 'account':
            payment['type'] = 'account'
            payment['bid'] = request.args['bid']
            payment['acc_num'] = request.args['acc_num']
        elif request.args['type'] == 'card':
            payment['type'] = 'card'
            payment['card_num'] = request.args['card_num']

    conn = pg.connect(conn_str)
    conn.autocommit = True
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    sql = f"SELECT * FROM bank"
    cur.execute(sql)
    bank = cur.fetchall()

    conn.close()
    return render_template("editPayment.html", bank=bank, payment=payment)

@app.route("/customer/order/payment", methods=["POST"])
def editPayment():
    conn = pg.connect(conn_str)
    conn.autocommit = True
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cid = status['user']['cid']
    sql = f"SELECT payments FROM customers WHERE cid={cid}"
    cur.execute(sql)
    payments = json.loads(cur.fetchall()[0]['payments'])

    if 'ntype' in request.form:
        ntype = request.form['ntype']
        if ntype == 'account':
            nbid = int(request.form['nbid'])
            nacc_num = int(request.form['nacc_num'])
            npayment = {'type':ntype, 'data':{'bid':nbid, 'acc_num':nacc_num}}
        elif ntype == 'card':
            ncard_num = int(request.form['ncard_num'])
            npayment = {'type':ntype, 'data':{'card_num':ncard_num}}

    if 'delete' in request.form:
        dtype = request.form['type']
        if dtype == 'account':
            dbid = request.form['bid']
            dacc_num = request.form['acc_num']

        elif dtype == 'card':
            dcard_num = request.form['card_num']

        for i in range(len(payments)):
            p = payments[i]
            if p['type'] == 'account' and dtype == 'account':
                if p['data']['bid'] == int(dbid) and p['data']['acc_num'] == int(dacc_num):
                    del payments[i]
                    break
            elif p['type'] == 'card' and dtype == 'card':
                if p['data']['card_num'] == int(dcard_num):
                    del payments[i]
                    break

        result = json.dumps(payments)
        sql = f"UPDATE customers SET payments='{result}' WHERE cid={cid}"
        cur.execute(sql)

    elif 'ptype' in request.form:
        ptype = request.form['ptype']
        if ptype == 'account':
            pbid = int(request.form['pbid'])
            pacc_num = int(request.form['pacc_num'])
            for p in payments:
                if p['type'] == 'account' and p['data']['bid'] == pbid and p['data']['acc_num'] == pacc_num:
                    p['type'] = npayment['type']
                    p['data'] = npayment['data']
                    break

        elif ptype == 'card':
            pcard_num = int(request.form['pcard_num'])
            for p in payments:
                if p['type'] == 'card' and p['data']['card_num'] == pcard_num:
                    p['type'] = npayment['type']
                    p['data'] = npayment['data']
                    break

        result = json.dumps(payments)
        sql = f"UPDATE customers SET payments='{result}' WHERE cid={cid}"
        cur.execute(sql)
    else:
        payments.append(npayment)
        result = json.dumps(payments)
        sql = f"UPDATE customers SET payments='{result}' WHERE cid={cid}"
        cur.execute(sql)

    conn.close()
    return redirect('/customer/order')

if __name__ == "__main__":
    app.run()