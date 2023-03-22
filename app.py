from flask import Flask, jsonify, redirect, url_for, request
from flask_cors import CORS
from flask_jwt_extended import  create_access_token, get_jwt, get_jwt_identity \
                                ,unset_jwt_cookies, jwt_required, JWTManager
from datetime import datetime, timedelta, timezone, date
import json
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import base64
from flask_mysqldb import MySQL


import io

app = Flask(__name__)
CORS(app)

app.config["JWT_SECRET_KEY"] = "0d51f3ad3f5aw0da56sa"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
jwt = JWTManager(app)
 
#Frontend API connection tests begin here

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'lab_eq'
mysql = MySQL(app)

image_folder = os.path.abspath("static/images")

mock_users_data = {"5":{"name":"Supakorn","lastname":"Pholsiri","major":"Cpr.E","year":2,"password":generate_password_hash("123456")}}
mock_admins_data = {"08spn491324619":{"name":"Supa","lastname":"Phol","depart":"Cpr.E","password":generate_password_hash("4567")}}
mock_equipment_data = [
    ("456135461451","GRCD-4658131-4616","Generator","Electrical source","Unavailable","Robotic lab","456135461451.jpg"), 
    ("545196164665","SUNWA-1962","Multimeter","Measurement","Available","Electrical lab","545196164665.jpeg")]
mock_material_data = []
mock_borrow_data = [("456135461451","5", date(2023,3,19).strftime('%Y-%m-%d'), date(2023,4,19).strftime('%Y-%m-%d'), "08spn491324619")]

def find_account(user, password):
    #หา user ที่มี user_id ตรงกับ input โดยเรียกข้อมูล id และ รหัส
    cursor = mysql.connection.cursor()
    cursor.execute('''SELECT s_id,password,role FROM user WHERE s_id=(%s) ''',(user,))
    data = cursor.fetchall()
    account= {}
    if data and check_password_hash(data[0][1],password) :
        account = {
            "sid" :data[0][0],
            "role" : "user" if data[0][-1] else "admin"
            }
    cursor.close()
    return account

@app.after_request
def refresh_expiring_jwts(response):
    try:
        exp_timestamp = get_jwt()["exp"]
        now = datetime.now(timezone.utc)
        target_timestamp = datetime.timestamp(now + timedelta(minutes=30))
        if target_timestamp > exp_timestamp:
            access_token = create_access_token(identity=get_jwt_identity())
            data = response.get_json()
            if type(data) is dict:
                data["access_token"] = access_token 
                response.data = json.dumps(data)
        return response
    except (RuntimeError, KeyError):
        # Case where there is not a valid JWT. Just return the original respone
        return response

@app.route('/login', methods=["POST"])
def login():
    if request.method == "POST" and "sid" in request.form and "password" in request.form:
        user = request.form["sid"]
        password = request.form["password"]
        account = find_account(user, password)
        if account:
            access_token = create_access_token(identity=account)
            return {"access_token":access_token, "role":account["role"], "id":account["sid"]}
    return {"msg":"Wrong user ID or password."}

@app.route('/register', methods=['POST'])
def register():
    name = request.form['name']
    lastname = request.form['surname']
    major = request.form['depart']
    year = request.form['year']
    student_id = request.form['sid']
    req_password = request.form['password']
    if name == "" or lastname == "" or major == "" or year == "" \
        or student_id == "" or req_password == "":
        return {"msg":"There are some fields that you have left blank."}
    password = generate_password_hash(req_password)
    #ดึง user_id และ admin_id ทั้งหมด เพื่อหาว่าลงทะเบียนไปแล้วหรือไม่
    cursor = mysql.connection.cursor()
    cursor.execute('''SELECT s_id FROM user ''')
    data = cursor.fetchall()
    u_id = [ temp[0] for temp in data ]
    if student_id not in u_id :
        #เพิ่ม user คนใหม่
        cursor.execute('''INSERT INTO user(s_id,password,f_name,s_name,major,year,role) VALUES(%s,%s,%s,%s,%s,%s,'1')''',(student_id,password,name,lastname,major,year))
        mysql.connection.commit()
        userinfo = {"sid":student_id, "role":"user"}
        access_token = create_access_token(identity=userinfo)
        return {"access_token":access_token, "role":"user", "id":userinfo["sid"]}
    else:
        cursor.close()
        return {"msg":"This id is already registered."}

@app.route('/equipments', methods=["GET"])
def equipments_lists():
    response = []
    cursor = mysql.connection.cursor()
    cursor.execute('''SELECT equipment.eq_id, equipment.eq_name, equipment.eq_type, equipment.category, equipment.status,
                    equipment.location, user.major, user.year, user.s_id, equipment.img 
                    FROM equipment LEFT JOIN eq_borrow ON equipment.eq_id = eq_borrow.eq_id 
                    LEFT JOIN user ON eq_borrow.s_id = user.s_id   ''')
    data = cursor.fetchall()
    #ดึงข้อมูล equipment ทั้งหมด และข้อมูล ID, Major/depart, ปี ของผู้ที่ยืมอยู่ ถ้ามี
    for eqm in data:
        image_data = eqm[9]  # assuming that the image data is at index 7
        if image_data:
            encoded_image = base64.b64encode(image_data).decode('utf-8')
        else:
            encoded_image = None
        response.append({   
                            "id":eqm[0],
                            "title":eqm[1],
                            "type":eqm[2],
                            "category":eqm[3],
                            "status": eqm[4],
                            "location": eqm[5],
                            "department":eqm[6] if eqm[6] else "-",
                            "year": eqm[7] if eqm[7] else "-" ,
                            "studentid": eqm[8] if eqm[8] else "-",
                            "image": encoded_image
                        })
    return jsonify(response)

@app.route('/<string:sid>/borrowing', methods=["GET"])
@jwt_required()
def borrowed_equipments(sid):
    try:
        decoded = get_jwt()
        if "sub" in decoded:
            if decoded["sub"]["sid"] == sid and decoded["sub"]["role"] == "user":
                response = []
                cursor = mysql.connection.cursor()
                #ดึงข้อมูล equipment ทุก equipment ที่ user (ID) คนนี้ยืม
                cursor.execute('''SELECT equipment.eq_id, equipment.eq_name, equipment.eq_type, equipment.category,
                                    equipment.location, equipment.status, equipment.img
                                    FROM eq_borrow INNER JOIN equipment ON eq_borrow.eq_id = equipment.eq_id 
                                    WHERE eq_borrow.s_id = (%s) ''',(sid,))
                data = cursor.fetchall()
                for borrow in data:
                    image_data = borrow[6]  # assuming that the image data is at index 7
                    if image_data:
                        encoded_image = base64.b64encode(image_data).decode('utf-8')
                    else:
                        encoded_image = None
                    response.append( { "id":borrow[0],
                                        "title":borrow[1],
                                        "type":borrow[2],
                                        "category":borrow[3],
                                        "status": borrow[4],
                                        "location": borrow[5],
                                        "image": encoded_image
                                        })
                return jsonify(response)
            return {"msg":"Wrong User"}, 404
        return {"msg":"Unauthorized access"}, 401
    except:
        return {"msg": "Internal server error"}, 500

@app.route("/<string:admin_id>/admin_equipment", methods=["GET", "PUT", "POST"])
@jwt_required()
def admin_eqm_detail(admin_id):
    try:
        decoded = get_jwt()
        if "sub" in decoded:
            if decoded["sub"]["sid"] == admin_id and decoded["sub"]["role"] == "admin":
                if request.method == "GET":
                    response = []
                    cursor = mysql.connection.cursor()
                    cursor.execute('''SELECT equipment.eq_id, equipment.eq_name, equipment.eq_type, equipment.category, equipment.status,
                    equipment.location, user.major, user.year, user.s_id , user.f_name, name.s_name
                    FROM equipment LEFT JOIN eq_borrow ON equipment.eq_id = eq_borrow.eq_id 
                    LEFT JOIN user ON eq_borrow.s_id = user.s_id   ''')
                    data = cursor.fetchall()
                    #ดึงข้อมูล equipment ทั้งหมด และข้อมูล ID, Major/depart, ปี ของผู้ที่ยืมอยู่ ถ้ามี และวันที่ให้ยืม กับวันที่คืน ถ้ามี
                    for eqm in data:
                        image_name = os.path.abspath(os.path.join(image_folder,mock_equipment_data[0][6])) #mock
                        with open(image_name, 'rb') as image_file:
                            encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
                        response.append({   
                                            "id":eqm[0],
                                            "title":eqm[1],
                                            "type":eqm[2],
                                            "category":eqm[3],
                                            "status": eqm[4],
                                            "location": eqm[5],
                                            "department":eqm[6],
                                            "year":eqm[7],
                                            "studentid": eqm[8],
                                            "image": encoded_image,
                                            "borrow_date":"borrow_date",
                                            "expiredate":"return_date"
                                            "name": eqm[9] + " " + eqm[10]
                                        })
                    return jsonify(response)
                
                if request.method == "PUT":
                    #ช่างหัวมันเรื่องรูป
                    print("PUT")
                    title = request.form["title"]
                    eqm_id = request.form["id"]
                    status = request.form["status"]
                    eqm_type = request.form["type"]
                    category = request.form["category"]
                    location = request.form["location"]
                    if status == "Available":
                        #ดึงข้อมูล eqm มา-------------------------------------------
                        for num in range(len(mock_equipment_data)):
                            if mock_equipment_data[num][0] == eqm_id:
                                #ดึงข้อมูลการยืม eqm นี้มา (ใช้ ID เรียก)---------------------------
                                #ถ้ามีให้ลบข้อมูลการยืมออก--------------------------------------
                                if mock_equipment_data[num][4] == "Unavailable":
                                    copy_borrow_data = mock_borrow_data.copy()  
                                    for borrow in copy_borrow_data:
                                        if borrow[0] == mock_equipment_data[num][0]:
                                            mock_borrow_data.remove(borrow)
                                    del copy_borrow_data

                                #อัปเดทรายละเอียด equipment
                                mock_equipment_data[num] = (eqm_id, title, category, eqm_type, status, location, "placeholder.png")
                                return {"msg":"Updated successfully"}
                            return {"msg":"The equipment doesn't exists"}
                    elif status == "Unavailable":
                        student_id = request.form["sid"]
                        student_name = request.form["name"]
                        borrow_date = request.form["Borrow_date"]
                        return_date = request.form["Return_date"]
                        #ดึง Student_id นี้จาก Database ถ้ามีทำงานต่อ ถ้าไม่มี return message
                        if student_id not in mock_users_data:
                            return {"msg":"This user doesn't exist."}
                        #ดึงข้อมูล eqm มา-------------------------------------------
                        for num in range(len(mock_equipment_data)):
                            if mock_equipment_data[num][0] == eqm_id:
                                #ดึงข้อมูลการยืม eqm นี้มา (ใช้ ID เรียก)---------------------------
                                if mock_equipment_data[num][4] == "Available":
                                    #เพิ่มข้อมูลการยืม (E_ID, S_ID, borrow_date, return_date, A_ID)
                                    mock_borrow_data.append((mock_equipment_data[num][0], student_id, borrow_date, return_date, admin_id))
                                elif mock_equipment_data[num][4] == "Unavailable":
                                    #เปลี่ยนรายละเอียดการยืม
                                    for i in range(len(mock_borrow_data)):
                                        if mock_borrow_data[i][0] == mock_equipment_data[num][0]:
                                            mock_borrow_data[i] = (mock_equipment_data[num][0], student_id, borrow_date, return_date, admin_id)
                                #อัปเดทรายละเอียด equipment
                                mock_equipment_data[num] = (eqm_id, title, category, eqm_type, status, location, "placeholder.png")
                                return {"msg":"Update successfully"}
                            return {"msg":"The equipment doesn't exists"}

                if request.method == "POST":
                    title = request.form['title']
                    eqm_id = request.form['eqm_id']
                    eqm_type = request.form['eqm_type']
                    category = request.form['category']
                    location = request.form['location']

                    #---------------------------------------------------------
                    cursor = mysql.connection.cursor()
                    cursor.execute('''SELECT eq_id FROM equipment ''')
                    data = cursor.fetchall()
                    eq_id = [ temp[0] for temp in data ]

                    if not eqm_id in eq_id:
                        cursor.execute('''INSERT INTO `equipment`(`eq_type`, `eq_name`, `eq_id`, `category`, `location`, `status`) 
                        VALUES (%s,%s,%s,%s,%s,'Available')''',(eqm_type,title,eqm_id,category,location,))
                        mysql.connection.commit()
                        cursor.close()
                        return {"msg":"This equipment added successfully."}
                    else:
                        cursor.close()
                        return {"msg":f"This {eqm_id} has been already registered."}
      
    except:
        return {"msg": "Internal server error"}, 500

@app.route("/<string:admin_id>/admin_equipment/delete/<string:eqm_id>", methods=["DELETE"])
@jwt_required()
def delete_equipment(admin_id, eqm_id):
    try:
        decoded = get_jwt()
        if "sub" in decoded:
            if decoded["sub"]["sid"] == admin_id and decoded["sub"]["role"] == "admin":
                cursor = mysql.connection.cursor()
                cursor.execute('''DELETE equipment.*,eq_borrow.* FROM `equipment` 
                LEFT JOIN eq_borrow ON eq_borrow.eq_id = equipment.eq_id 
                WHERE equipment.eq_id=(%s)  ''',(eqm_id,))
                mysql.connection.commit()
                #----------------------------------------------------------------------------
                    #ลบเสร็จสิ้น
                return {"msg":f"Equipment of id {eqm_id} is deleted successfully."}
            return {"msg": "Unauthorized access"} , 401
    except:
        return {"msg": "Internal server error"}, 500

@app.route('/<string:admin_id>/admin_control/add_admin', methods=["POST"])
@jwt_required()
def add_admin_member(admin_id):
    try:
        decoded = get_jwt()
        if "sub" in decoded:
            if decoded["sub"]["sid"] == admin_id and decoded["sub"]["role"] == "admin":
                name = request.form['name']
                lastname = request.form['surname']
                newadmin_id = request.form['sid']
                password = generate_password_hash(request.form['password'])
                cursor = mysql.connection.cursor()
                #ดึงข้อมูล equipment ทุก equipment ที่ user (ID) คนนี้ยืม
                cursor.execute('''SELECT s_id, password, role  
                                    FROM user 
                                    WHERE s_id = (%s) ''',(newadmin_id,))
                data = cursor.fetchall()
                if not data :
                    cursor.execute('''INSERT INTO `user`(`s_id`, `password`, `f_name`, `s_name`, `role`) 
                                        VALUES (%s,%s,%s,%s,'0') ''',(newadmin_id,password,name,lastname,))
                    mysql.connection.commit()
                    return {"msg":f"Admin {newadmin_id} is added successfully"}
                return {"msg":f"{newadmin_id} has been already registered"}
            return {"msg": "Unauthorized access"} , 401
    except:
        return {"msg": "Internal server error"}, 500

@app.route("/<string:admin_id>/admin_control/delete_admin/<string:delete_id>", methods=["DELETE"])
@jwt_required()
def delete_admin(admin_id, delete_id):
    try:
        decoded = get_jwt()
        if "sub" in decoded:
            if decoded["sub"]["sid"] == admin_id and decoded["sub"]["role"] == "admin":
                #ลบ Admin ที่มี id ตรงกับ delete_id
                cursor = mysql.connection.cursor()
                #ดึงข้อมูล equipment ทุก equipment ที่ user (ID) คนนี้ยืม
                cursor.execute('''SELECT s_id, role  
                                    FROM user 
                                    WHERE s_id = (%s) and role='0' ''',(delete_id,))
                data = cursor.fetchall()
                
                if data and data[0][0] != "admin" :
                    cursor.execute('''DELETE FROM user WHERE s_id =(%s) ''',(delete_id,))
                    mysql.connection.commit()
                    return {"msg":f"Deletion of admin {delete_id} is successful."}, 200

                return {"msg":f"No admin {delete_id} exists."}, 404
            return {"msg":"Unauthorized address"}, 403
        return {"msg":"Unauthorized address"}, 403
    except:
        return {"msg": "Internal server error"}, 500

@app.route('/sid', methods=["POST"])
def sid():
    response = []
    s_id = request.form['sid']
    cursor = mysql.connection.cursor()
    cursor.execute('''SELECT s_id, f_name,s_name,year,major  
                        FROM user 
                        WHERE s_id = (%s) ''',(s_id,))
    data = cursor.fetchall()
    if data:
        response.append({   
                            "Name":data[0][1] + " "+ data[0][2] ,
                            "year":data[0][3],
                            "major":data[0][4],
                        })
        return jsonify(response)
    else:
        return {"msg": "no user"}, 404

    

@app.route("/logout", methods=["POST"])
def logout():
    response = jsonify({"msg": "logout successful"})
    unset_jwt_cookies(response)
    return response

if __name__ == "__main__":
    app.run(host='localhost', debug = True, port=5000)
