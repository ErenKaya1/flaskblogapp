from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators,BooleanField
from passlib.hash import sha256_crypt
from functools import wraps
import sys

sys.setrecursionlimit(1500)

# Kullanıcı Giriş Kontrolü için Decorator
# logged_in = True olması gereken kısımlarda kullanılacak
def login_required(function):
    @wraps(function)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return function(*args, **kwargs)
        else:
            flash("Bu sayfayı görüntülemek için lütfen giriş yapın.","danger")
            return redirect(url_for("Login"))
    return decorated_function

# Kullanıcı Kayıt Formu
class registerForm(Form):
    name = StringField("İsim Soyisim",validators=[validators.Length(min=4, max=25,message="4-25 uzunluğunda olmalıdır.")])
    username = StringField("Kullanıcı Adı",validators=[validators.Length(min=5, max=35,message="4-25 uzunluğunda olmalıdır.")])
    email = StringField("E-mail adresi",validators=[validators.Email(message="Lütfen geçerli bir e-mail adresi giriniz.")])
    password = PasswordField("Parola",validators=[
        validators.Length(min=6,max=24,message="6-24 uzunluğunda parola giriniz."),
        validators.DataRequired(message="Parola alanı boş bırakılamaz."),
        validators.EqualTo(fieldname="confirm",message="Parolalar uyuşmuyor.")
        ])
    confirm = PasswordField("Parola doğrula")

# Giriş Yapma Formu
class loginForm(Form):
    username = StringField("Kullanıcı adınız",validators=[validators.DataRequired(message="Lütfen kullanıcı adınızı giriniz.")])
    password = PasswordField("Parolanız",validators=[validators.DataRequired(message="Lütfen parolanızı giriniz.")])

# Makale Oluşturma Formu
class articleForm(Form):
    title = StringField("Makale başlığı",validators=[validators.Length(min=5,max=100,message="5-100 karakter aralığında bir başlık giriniz.")])
    content = TextAreaField("Makale içeriği",validators=[validators.Length(min=10,message="En az 10 karakter uzunluğunda içerik girmelisiniz.")])
    anasayfa = BooleanField("Makale anasayfaya eklensin mi?")

# Makale Güncelleme Formu
class editArticleForm(Form):
    title = StringField("Makale başlığı",validators=[validators.Length(min=5, max=100, message="5-100 karakter aralığında bir başlık giriniz.")])
    content = TextAreaField("Makele içeriği",validators=[validators.Length(min=10,message="En az 10 karakter uzunluğunda bir içerik girmelisiniz.")])
    onay = BooleanField("Makale onaylansın mı?")
    anasayfa = BooleanField("Makale anasayfaya eklensin mi?")


# Parola Değiştirme Formu
class passwordForm(Form):
    currentPassword = PasswordField("Eski Parola",validators=[validators.DataRequired(message="Eski parola alanı boş bırakılamaz.")])
    password = PasswordField("Yeni Parola",validators=[
        validators.Length(min=6,max=24,message="6-24 uzunluğunda parola giriniz."),
        validators.DataRequired(message="Parola alanı boş bırakılamaz."),
        validators.EqualTo(fieldname="confirm",message="Parolalar uyuşmuyor.")
        
        ])
    confirm = PasswordField("Yeni Parola doğrula")

app = Flask(__name__)
app.secret_key = "database"
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "blogdatabase"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"
app.config["UPLOAD_FOLDER"] = "UPLOAD_FOLDER"

mysql = MySQL(app)

# Anasayfa
@app.route("/")
def index():
    cursor = mysql.connection.cursor()
    result = cursor.execute("SELECT * FROM articles WHERE anasayfa=1")

    if result > 1:
        data = cursor.fetchall()
        return render_template("index.html",data = data)
    else:
        return render_template("index.html")

# Hakkımızda
@app.route("/About")
def About():
    return render_template("about.html")

# Makaleler
@app.route("/Articles")
def Articles():
    try:
        cursor = mysql.connection.cursor()
        result = cursor.execute("SELECT * FROM articles WHERE onay=1")
        
        if result > 0:
            data = cursor.fetchall()
            return render_template("articles.html",data = data)
        else:
            return render_template("articles.html")
    except:
        flash("Veri tabanı ile bağlantınızı kontrol edin.","danger")
        return redirect(url_for("index"))

# Kayıt Olma İşlemi
@app.route("/Register",methods = ["GET","POST"])
def Register():
    form = registerForm(request.form)

    if request.method == "POST" and form.validate():
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)
        cursor = mysql.connection.cursor()
        result = cursor.execute("SELECT * FROM users WHERE username=%s",(username,))
        result_2 = cursor.execute("SELECT * FROM users WHERE email=%s",(email,))

        if result > 0 or result_2 > 0:
            if result > 0:
                flash("Bu kullanıcı adı daha önce alınmış. Lütfen farklı bir kullanıcı adı deneyin.","danger")

            if result_2>0:
                flash("Bu e-mail adresi ile daha önce kayıt olunmuş. Lütfen farklı bir e-mail adresi deneyin.","danger")

            return redirect(url_for("Register"))
        else:
            cursor.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)",(name,email,username,password))
            mysql.connection.commit()
            cursor.close()
            flash("Başarıyla kayıt olundu.","success")
            return redirect(url_for("Login"))
    else:
        return render_template("register.html",form = form)

# Login işlemi
@app.route("/Login", methods = ["GET", "POST"])
def Login():
    form = loginForm(request.form)
    if request.method == "POST" and form.validate():
        username = form.username.data
        password_entered = form.password.data
        cursor = mysql.connection.cursor()
        result = cursor.execute("SELECT * FROM users WHERE username=%s",(username,))
        if result > 0:
            # Kullanıcı adı veri tabanında kayıtlı ise burası çalışacak
            data = cursor.fetchone()
            real_password = data["password"]
            if sha256_crypt.verify(password_entered,real_password):
                # Parola doğru girilmişse burası çalışacak
                flash("Başarıyla giriş yapıldı.","success")

                session["logged_in"] = True
                session["username"] = username

                return redirect(url_for("index"))
            else:
                # Parola yanlış girilmişse burası çalışacak
                flash("Giriş bilgileri hatalı","danger")
                return redirect(url_for("Login"))
        else:
            # Kullanıcı adı veri tabanında kayıtlı değilse burası çalışacak
            flash("Giriş bilgileri hatalı","danger")
            return redirect(url_for("Login"))
    else:
        return render_template("login.html", form = form)

# Logout İşlemi
@app.route("/Logout")
def Logout():
    session.clear()
    return redirect(url_for("index"))

# Kontrol Paneli
@app.route("/Dashboard")
@login_required
def Dashboard():
    cursor = mysql.connection.cursor()
    result = cursor.execute("SELECT * FROM articles WHERE author=%s",(session["username"],))

    if result > 0:
        data = cursor.fetchall()
        return render_template("dashboard.html",data = data)
    else:
        return render_template("dashboard.html")

# Makale Oluşturma
@app.route("/addArticle",methods = ["GET","POST"])
@login_required
def addArticle():
    form = articleForm(request.form)
    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data
        anasayfa = form.anasayfa.data
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO articles(title,content,author,anasayfa) VALUES(%s,%s,%s,%s)",(title,content,session["username"],anasayfa))
        mysql.connection.commit()
        cursor.close()
        flash("Makale başarıyla eklendi.","success")
        return redirect(url_for("Dashboard"))
    else:
        return render_template("addArticle.html",form = form)

# Makale Detayları
@app.route("/Article/<string:id>")
def Details(id):
    cursor = mysql.connection.cursor()
    result = cursor.execute("SELECT * FROM articles WHERE id=%s",(id,))

    if result > 0:
        data = cursor.fetchone()
        return render_template("article.html",data = data)
    else:
        return render_template("article.html")

# Makale Silme
@app.route("/Delete/<string:id>")
@login_required
def Delete(id):
    cursor = mysql.connection.cursor()
    result = cursor.execute("SELECT * FROM articles WHERE author=%s AND id=%s",(session["username"],id))

    if result > 0:
        cursor.execute("DELETE FROM articles WHERE author=%s AND id=%s",(session["username"],id))
        mysql.connection.commit()
        flash("Makale başarıyla silindi.","success")
        return redirect(url_for("Dashboard"))
    else:
        flash("Makale bulunamadı.","danger")
        return redirect(url_for("Dashboard"))

# Makale Güncelleme
@app.route("/Edit/<string:id>", methods = ["GET", "POST"])
@login_required
def Edit(id):
    if request.method == "GET":
        # GET REQUEST
        # Güncelle seçeneğine tıklandıktan sonra bu satırlar çalışacak (form template)
        cursor = mysql.connection.cursor()
        result = cursor.execute("SELECT * FROM articles WHERE id=%s and author=%s",(id, session["username"]))

        if result == 0:
            # Kullanıcıya ait makale yoksa bu kodlar çalışacak
            flash("Makale bulunamadı.","danger")
            return redirect(url_for("Dashboard"))
        else:
            # Kullanıcıya ait makale varsa bu kodlar çalışacak
            data = cursor.fetchone()
            form = editArticleForm()
            form.title.data = data["title"]
            form.content.data = data["content"]
            form.anasayfa.data = data["anasayfa"]
            return render_template("edit.html",form = form)

    else:
        # POST REQUEST
        # Güncellemeleri kaydete tıkladıktan sonra bu satırla çalışacak
        form = editArticleForm(request.form)
        newTitle = form.title.data
        newContent = form.content.data
        newAnasayfa = form.anasayfa.data
        newOnay = form.onay.data
        cursor = mysql.connection.cursor()
        cursor.execute("UPDATE articles SET title=%s, content=%s, anasayfa=%s, onay=%s WHERE id=%s and author=%s",(newTitle,newContent,newAnasayfa,newOnay,id,session["username"]))
        mysql.connection.commit()
        flash("Makale başarıyla güncellendi","success")
        return redirect(url_for("Dashboard"))

# Site İçi Makale Arama (Search)
@app.route("/Search", methods = ["GET", "POST"])
def Search():
    if request.method == "GET":
        return redirect(url_for("index"))
    
    else:
        # POST REQUEST
        keyword = request.form.get("keyword")
        cursor = mysql.connection.cursor()
        result = cursor.execute("SELECT * FROM articles WHERE title LIKE '%"+keyword+"%'")
        
        if result == 0:
            flash("Aranan kelimeye uygun makale bulunamadı.","info")
            return redirect(url_for("Articles"))
        else:
            data = cursor.fetchall()
            flash(keyword+" için arama sonuçları gösteriliyor.","info")
            return render_template("articles.html",data = data)

# Profil Güncelleme
@app.route("/Profile",methods = ["GET","POST"])
@login_required
def Profile():
    if request.method == "POST":
        # POST REQUEST
        # Güncelle'ye tıkladıktan sonra bu kodlar çalışacak
        form = registerForm(request.form)
        newName = form.name.data
        newUsername = form.username.data
        newEmail = form.email.data
        cursor = mysql.connection.cursor()
        cursor.execute("UPDATE users SET name=%s,username=%s,email=%s WHERE username=%s",(newName, newUsername, newEmail, session["username"]))
        mysql.connection.commit()
        cursor.close()
        flash("Değişiklikler başarıyla kaydedildi.","success")
        return redirect(url_for("index"))
    else:
        # GET REQUEST
        #Profil'e tıklanınca açılacak olan form
        form = registerForm()
        cursor = mysql.connection.cursor()
        result = cursor.execute("SELECT * FROM users WHERE username=%s",(session["username"],))

        if result > 0:
            data = cursor.fetchone()
            form.name.data = data["name"]
            form.username.data = data["username"]
            form.email.data = data["email"]
            return render_template("profile.html",form = form)
        else:
            flash("Bir hata oluştu.","danger")
            return redirect(url_for("index"))

# Parola Güncelleme
@app.route("/changePassword",methods = ["GET","POST"])
@login_required
def changePassword():
    form = passwordForm(request.form)
    if request.method == "POST" and form.validate():
        # POST REQUEST
        # Parolayı Güncelle butonuna tıklandıktan sonra bu kodları çalışacak.
        cursor = mysql.connection.cursor()
        result = cursor.execute("SELECT * FROM users WHERE username=%s",(session["username"],))

        if result > 0:
            # Kullanıcı veri tabanında kayıtlıysa bu kodlar çalışacak
            newPassword = sha256_crypt.encrypt(form.password.data)
            currentPassword = form.currentPassword.data
            data = cursor.fetchone()
            realPassword = data["password"]

            if sha256_crypt.verify(currentPassword, realPassword):
                # Eski parola doğruysa bu kodlar çalışacak
                cursor.execute("UPDATE users SET password=%s WHERE username=%s",(newPassword, session["username"]))
                mysql.connection.commit()
                flash("Parolanız başarıyla güncellendi.","success")
                return redirect(url_for("Profile"))
            else:
                # Eski parola yanlışsa bu kodlar çalışacak
                flash("Bilgilerinizi kontrol ediniz.","danger")
                return redirect(url_for("changePassword"))
        else:
            # Kullanıcı veri tabanında kayıtlı değilse bu kodlar çalışacak
            flash("Beklenmedik bir hata oluştu.","danger")
            return redirect(url_for("Profile"))
    else:
        # GET REQUEST
        # Parolayı Güncelleme Sayfası
        return render_template("changePassword.html", form = form)        
        
if(__name__ == "__main__"):
    app.run(debug=True)