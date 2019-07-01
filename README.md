# Hanyang Of Delivery

- Application which connects seller, customer, delivery.

***

### Seller
- Seller has at least one **store** and store sells at least one **menu**.
### Customer
- Customer can search store and purchase various menus.
- By purchasing, customer creates **order** and seller can check the order and send menu.
### Delivery
- Seller selects delivery for each order.
- After delivery succesfully deliver the order, customer can confirm and the order terminates.
<br>

***

## Implementation Environment
- Back-end : Flask 1.0.2, Python 3.7.0
- Front-end : JQuery 3.3.1, Jinja2 2.10
- DB : PostgreSQL 10.5, psycopg2 module

***

## How can I restore beahan.sql dump file?
1. Connect to postgres using 'psql'.
2. Create user name 'db3' with password '1234'.
```
Postgres=# create user db3 with password ‘1234’;
```
3. Restore 'beahan.sql' file using 'psql'.
```
PS C:\program files\postgresql\10\bin> ./psql.exe -U postgres -f <baehan.sql경로> db3
```

***

## How can I execute HanyangOfDelivery?
- Execute server by running 'app.py'.
```
python app.py
```
- Connect to '127.0.0.1:5000'.
