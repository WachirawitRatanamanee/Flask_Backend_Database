from flask import Flask,render_template, request
from flask_mysqldb import MySQL

app = Flask(__name__) 

mysql = MySQL(app)

@app.route('/admin_control', methods = ['POST','DELETE'])
def admin_control():
    if request.method == 'POST':
        name = request.form['name']
        lastName = request.form['lastName']
        adminId = request.form['adminId']
        password = hash(request.form['password'])
        cursor = mysql.connection.cursor()
        #INSERT TO DB just tried, should renovate VVV
        cursor.execute(''' INSERT INTO jiwjiw(name, lastname) VALUES(%s,%s)''',(adminId,password))
        mysql.connection.commit()
        cursor.close()
        return f"add admin success!!"
    if request.method == 'DELETE':
        deleteAdminId = request.form['deleteAdminId']
        cursor = mysql.connection.cursor()
        #DELETE FROM DB just tried, should renovate VVV
        cursor.execute(''' DELETE FROM jiwjiw WHERE id = (%s)''',(deleteAdminId))
        mysql.connection.commit()
        cursor.close()
        return f"delete admin success!!"

@app.route('/admin_equipment',methods=['GET','DELETE'])
def admin_equipment():
    if request.method == 'GET':
        total_data = 'Just prevent from Error' #Query [equipmentID,Title_eq, Status , img ,sid,department,year,expiredate ]
        results = [
                {
                    "equipmentID": 1,
                    "Title_eq": 1,
                    "Status": 1,
                    "img": 1,
                    "sid": 1,
                    "department": 1,
                    "year": 1,
                    "expiredate": 1,
                } for each_data in total_data]
        return {"data": results}
    if request.method == 'DELETE':
        equipmentID = request.form['equipmentID']
        Title_eq = request.form['Title_eq']
        Status = request.form['Status']
        img = request.form['img']
        sid = request.form['sid']
        department = request.form['department']
        year = request.form['year']
        cursor = mysql.connection.cursor()
        #DELETE FROM DB just tried, should renovate VVV
        cursor.execute(''' DELETE FROM jiwjiw WHERE id = (%s)''',(equipmentID))
        mysql.connection.commit()
        cursor.close()
        return f"delete equipment success!!"
       
    if request.method == 'PUT': 
        EQ_Title = request.form['EQ_Title']
        EQ_ID = request.form['EQ_ID']
        Img = request.form['Img']
        cursor = mysql.connection.cursor()
        #edit equipment VVV
        cursor.execute(''' UPDATE FROM jiwjiw WHERE id = (%s)''',(EQ_ID))
        mysql.connection.commit()
        cursor.close()
        return f"update status equipment success!!"
    
    if request.method == 'POST':
        EQ_Title = request.form['EQ_Title']
        EQ_ID = request.form['EQ_ID']
        Status = request.form['Status']
        Borrow_date = request.form['Borrow_date']
        Return_date = request.form['Return_date']
        cursor = mysql.connection.cursor()
        #INSERT EQUIPMENT
        cursor.execute(''' INSERT INTO jiwjiw ''')
        mysql.connection.commit()
        cursor.close()
        return f"update status equipment success!!"
    
@app.route('/admin-request',methods=['GET','PUT','POST','DELETE'])
def request_equipment():
    if request.method == 'GET':
        total_data = 'Just prevent from Error' #Query [ID,Title ,std_id,EQID , img,expiredate ]
        results = [
                {
                    "ID": 1,
                    "Title": 1,
                    "std_id": 1,
                    "EQID": 1,
                    "img": 1,
                    "expiredate": 1,
                } for each_data in total_data]
        return {"data": results}
    if request.method == 'PUT':
        ID = request.form['ID']
        Title = request.form['Title']
        std_idEQ = request.form['std_idEQ']
        img = request.form['img']
        expiredate = request.form['expiredate']
        cursor = mysql.connection.cursor()
        #UPDATE to borrowed from available VVV
        cursor.execute(''' UPDATE FROM jiwjiw WHERE id = (%s)''',(ID))
        mysql.connection.commit()
        cursor.close()
        return f"update status equipment success!!"
    
    if request.method == 'POST': 
        EQ_ID = request.form['EQ_ID']
        Tittle_EQ = request.form['Tittle_EQ']
        Status = request.form['Status']
        cursor = mysql.connection.cursor()
        #UPDATE status to notav VVV
        cursor.execute(''' UPDATE FROM jiwjiw WHERE id = (%s)''',(EQ_ID))
        mysql.connection.commit()
        cursor.close()
        return f"update status equipment success!!"
    
    if request.method == 'DELETE':
        EQ_ID = request.form['EQ_ID']
        Tittle_EQ = request.form['Tittle_EQ']
        Status = request.form['Status']
        Expireddate = request.form['Expireddate']
        Returndate = request.form['Returndate']
        cursor = mysql.connection.cursor()
        #UPDATE status to av VVV
        cursor.execute(''' UPDATE FROM jiwjiw WHERE id = (%s)''',(EQ_ID))
        mysql.connection.commit()
        cursor.close()
        return f"update status equipment success!!"

if __name__ == '__main__':
    app.run()