from flask import Flask,render_template, request
from flask_mysqldb import MySQL


app = Flask(__name__) 
#1

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'testjiw1'

mysql = MySQL(app)

@app.route('/register', methods = ['POST'])
def register():
    if request.method == 'POST':
        F_name = request.form['F_name']
        L_name = request.form['L_name']
        major = request.form['Major']
        year = request.form['Year']
        std_id = request.form['std_id']
        password = hash(request.form['password'])
        cursor = mysql.connection.cursor()
        #INSERT TO DB just tried, should renovate VVV
        cursor.execute(''' INSERT INTO jiwjiw(name, lastname) VALUES(%s,%s)''',(F_name,password))
        mysql.connection.commit()
        cursor.close()
        return f"Registered!!"

@app.route('/equipment',methods=['GET'])
def equipment():
    if request.method == 'GET':
        total_data = 'Just prevent from Error' #Query [ID,Title_EQ, Cate,StuID,Major,Year,Type,Status ,location, img]
        results = [
                {
                    "ID": each_data.ID,
                    "Title_EQ": each_data.Title_EQ,
                    "Cate": each_data.Cate,
                    "StuID": each_data.StuID,
                    "Major": each_data.Major,
                    "Year": each_data.Year,
                    "Type": each_data.Type,
                    "Status": each_data.Status ,
                    "location": each_data.location,
                    "img": each_data.img,
                } for each_data in total_data]
        return {"data": results}

if __name__ == '__main__':
    app.run()