from flask import Flask, make_response, render_template, url_for, redirect, flash, session
from routes.routes import bp as my_blueprint
from routes.geneticAlgorithm import bp as algorithm
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, HiddenField, SelectField
from wtforms.validators import DataRequired, Email, ValidationError, EqualTo
import bcrypt
from flask_mysqldb import MySQL
from flask import g
from flask_wtf.csrf import CSRFProtect

salt = bcrypt.gensalt()
    

def create_app():
    app = Flask(__name__)
    

    app.config['MYSQL_HOST'] = 'localhost'
    app.config['MYSQL_USER'] = 'root'
    app.config['MYSQL_PASSWORD'] = ''
    app.config['MYSQL_DB'] = 'thesis_project'
    app.secret_key = 'mindyourownbusiness'

    app.register_blueprint(my_blueprint)
    app.register_blueprint(algorithm)


    with app.app_context():
        mysql = MySQL(app)
        @app.before_request
        def before_request():
            g.mysql = mysql

    def validate_email_unique(form, field):
        # Assuming the database connection is available globally or passed as an argument
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM users WHERE email = %s", (field.data,))
        result = cursor.fetchone()
        count = result[0]
        if count > 0:
            raise ValidationError('Email already registered.')
    
    def validate_username_unique(form, field):
        # Assuming the database connection is available globally or passed as an argument
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = %s", (field.data,))
        result = cursor.fetchone()
        count = result[0]
        if count > 0:
            raise ValidationError('Username already exist.')

    class RegisterForm(FlaskForm):
        username = StringField("Name", validators=[DataRequired(), validate_username_unique])
        email = StringField("Email", validators=[DataRequired(), Email(),  validate_email_unique])
        password = PasswordField("Password", validators=[DataRequired()])
        confirmPassword = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo('password')])
        department = SelectField("Department", choices=[
            ('SOECS', 'SOECS'),
            ('SON', 'SON'),
            ('SBMA', 'SBMA'),
            ('SHOM', 'SHOM'),
            ('SEAS', 'SEAS')
        ], validators=[DataRequired()])
        submit = SubmitField("Submit") 

    class RegistrarRegisterForm(FlaskForm):
        username = StringField("Name", validators=[DataRequired(), validate_username_unique])
        email = StringField("Email", validators=[DataRequired(), Email(),  validate_email_unique])
        password = PasswordField("Password", validators=[DataRequired()])
        confirmPassword = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo('password')])
        submit = SubmitField("Submit") 

    class LoginForm(FlaskForm):
        email = StringField("Email", validators=[DataRequired(), Email()])
        password = PasswordField("Password", validators=[DataRequired()])
        submit = SubmitField("Submit") 



# ==============================DEPARTMENT HEAD SIGNUP==============================================



    @app.route('/signup/dept-head', methods=['GET', 'POST'])
    def deptSignup():
        if 'user_id' in session or 'user_role' in session:
            # Redirect to home if the user is already signed in
            return redirect(url_for('my_blueprint.home'))
        dept_head_form = RegisterForm()
        if dept_head_form.validate_on_submit():
            username = dept_head_form.username.data
            email = dept_head_form.email.data
            password = dept_head_form.password.data
            role = 'dept-head'
            department = dept_head_form.department.data
            isVerified = False

            hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)

            try:
                cursor = mysql.connection.cursor()
                insert_query = """
                INSERT INTO users (username, email, password, role, department, is_verified) VALUES (%s, %s, %s, %s, %s, %s)
                """
                cursor.execute(insert_query, (username, email, hashed_password.decode('utf-8'), role, department, isVerified))
                mysql.connection.commit()
                print("=======User added=========")
                return redirect(url_for('signin'))
            except Exception as e:
                print(f"Database operation failed: {e}")
                cursor.close()
        else:
            print("Form validation failed:", dept_head_form.errors)

        return render_template('dept_headsignup.html', dept_head_form=dept_head_form)






# ===================================REGISTRAR SIGNUP====================================





    @app.route('/signup/registrar', methods=['GET', 'POST'])
    def registrarSignup():
        if 'user_id' in session or 'user_role' in session:
            # Redirect to home if the user is already signed in
            return redirect(url_for('my_blueprint.home'))
        registrar_form = RegistrarRegisterForm()
        if registrar_form.validate_on_submit():
            username = registrar_form.username.data
            email = registrar_form.email.data
            password = registrar_form.password.data
            role = 'registrar'
            department = 'registrar'
            isVerified = False

            hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)

            try:
                cursor = mysql.connection.cursor()
                insert_query = """
                INSERT INTO users (username, email, password, role, department, is_verified) VALUES (%s, %s, %s, %s, %s, %s)
                """
                cursor.execute(insert_query, (username, email, hashed_password.decode('utf-8'), role, department, isVerified))
                mysql.connection.commit()
                print("=======User added=========")
                return redirect(url_for('signin'))
            except Exception as e:
                print(f"Database operation failed: {e}")
                cursor.close()
        else:
            print("Form validation failed:", registrar_form.errors)

        return render_template('registrar_signup.html', registrar_form=registrar_form)



# ====================SIGN IN===============



    @app.route('/signin', methods=['GET','POST'])
    def signin():
        if 'user_id' in session or 'user_role' in session:
            # Redirect to home if the user is already signed in
            return redirect(url_for('my_blueprint.home'))

        form = LoginForm()
        if form.validate_on_submit():
            email = form.email.data
            password = form.password.data

            cursor = mysql.connection.cursor()
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            if user and bcrypt.checkpw(password.encode('utf-8'), user[5].encode('utf-8')):
                session['user_id'] = user[0]
                user_role = user[3]  # Adjust the index based on your actual database schema
                isVerified = user[6]
                email = user[2]
                username = user[1]
                department = user[4]
                # Store the user's role in the session for later use
                session['user_role'] = user_role
                session['isVerfied'] = isVerified
                session['email'] = email
                session['username'] = username
                session['department'] = department
                
                if isVerified:
                # Redirect based on user role
                    if user_role == 'registrar':
                        return redirect(url_for('my_blueprint.registrar'))  # Assuming you have a route named 'registrar_dashboard' for registrars
                    elif user_role == 'admin':
                        return redirect(url_for('my_blueprint.admin'))  # Assuming you have a route named 'admin_dashboard' for admins
                    elif user_role == 'dept-head':  # Assuming 'dept-head' is the role for department heads
                        return redirect(url_for('my_blueprint.program'))  # Assuming 'program' is the route for department heads
                    else:
                        flash('Invalid user role')
                        return redirect(url_for('signin'))  # Redirect back to signin if role is unknown
                else:
                    return redirect(url_for('my_blueprint.new_user'))
            else:
                flash('Login Failed. Please check your email and password')
                return redirect(url_for('signin'))

        return render_template('signin.html', form=form)



# ====================LOG OUT====================
    @app.route('/signout')
    def logout():
        session.clear()
        response = make_response(redirect(url_for('signin')))
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return redirect(url_for('signin'))
    
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    @app.route('/')
    def none():
        return redirect(url_for('signin'))

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)


