from flask import Flask, render_template, request, flash, url_for, redirect
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:0899791240@localhost/test'
# engine:[//[user[:password]@][host]/[dbname]]
# engine -> postgresql
# user -> postgres (see `owner` field in previous screenshot)
# password -> password (my db password is the string, `password`)
# host -> localhost (because we are running locally on out machine)
# dbname -> flasksql (this is the name I gave to the db in the previous step)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = 'secret string'

db = SQLAlchemy(app)

class test1(db.Model): #Create Table name 'test1'
    name = db.Column(db.String(255), nullable=False) #Create Attribute name 'name'
    lastname = db.Column(db.String(255), nullable=False)
    major = db.Column(db.String(255), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    student_id = db.Column(db.String(255), nullable=False, primary_key=True)
    password = db.Column(db.String(255), nullable=False)
    img = db.Column(db.LargeBinary, nullable=True)

    def __init__(self, name, lastname, major, year, student_id, password, img):
        self.name = name
        self.lastname = lastname
        self.major = major
        self.year = year
        self.student_id = student_id
        self.password = password
        self.img = img
    
    def __repr__(self):
        return f'<People {self.student_id}>'

@app.before_first_request #do before first request
def create_database():
     db.create_all()

@app.route('/')
def index():
    return '<a href="/register"><button> Click here </button></a>'

# @app.route("/registers")
# def registers():
#     return render_template("index.html")

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        lastname = request.form['surname']
        major = request.form['depart']
        year = request.form['year']
        student_id = request.form['sid']
        password = hash(request.form['password'])
        image = request.files['fileimg'].read()
        entry = test1(name,lastname,major,year,student_id,hash(password))
        db.session.add(entry)
        db.session.commit()
        return redirect(url_for('index'))
    
    if request.method == 'GET': 
        datas = test1.query.all()
        results = [
            {
                "name": data.name,
                "lastname": data.lastname,
                "major": data.major,
                "year": data.year,
                "student_id": data.student_id,
                "password": data.password,
                "img" :data.img
                
            } for data in datas]
        return {"count": len(results), "data": results}
    
    return render_template("index.html")

@app.route('/re',methods=['GET'])
def re():
    datas = test1.query.all()
    results = [
            {
                "name": data.name,
                "lastname": data.lastname,
                "major": data.major,
                "year": data.year,
                "student_id": data.student_id,
                "password": data.password,
            } for data in datas]

    return {"count": len(results), "data": results}

if __name__ == '__main__':
    db.create_all()
    app.run()

# class test2(db.Model):
#     ID = db.Column(db.String(255), nullable=False, primary_key=True)
#     Title_EQ = db.Column(db.String(255), nullable=False)
#     Cate = db.Column(db.String(255), nullable=False)
#     StuID = db.Column(db.Integer, nullable=False)
#     Major = db.Column(db.String(255), nullable=False)
#     Year = db.Column(db.Integer, nullable=False)
#     Type = db.Column(db.String(255), nullable=False)
#     Status = db.Column(db.String(255), nullable=False)
#     location = db.Column(db.String(255), nullable=False)
#     img = db.Column(db.LargeBinary, nullable=True)

#     def __init__(self, ID, Title_EQ, Cate, StuID, Major, Year, Type, Status, location, img):
#         self.ID = ID
#         self.Title_EQ = Title_EQ
#         self.Cate = Cate
#         self.StuID = StuID
#         self.Major = Major
#         self.Year = Year
#         self.Type = Type
#         self.Status = Status
#         self.location = location
#         self.img = img
    
#     def __repr__(self):
#         return f'<People {self.StuID}>'
    
# @app.route('/equipment',methods=['GET'])
# def equipment():
#     datas = test2.query.all()
#     results = [
#             {
#                 "ID": data.ID,
#                 "Title_EQ": data.Title_EQ,
#                 "Cate": data.Cate,
#                 "StuID": data.StuID,
#                 "Major": data.Major,
#                 "Year": data.Year,
#                 "Type": data.Type,
#                 "Status": data.Status ,
#                 "location": data.location,
#                 "img": data.img,

#             } for data in datas]
#     return {"count": len(results), "data": results}
