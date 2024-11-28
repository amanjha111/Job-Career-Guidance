from flask import Flask,render_template,redirect,request,session,url_for
from flask_mysqldb import MySQL
import pandas as pd
import json
import pickle
import random
from datetime import datetime
import joblib

from werkzeug.routing import BuildError
from jinja2.exceptions import TemplateNotFound

model_path = 'random_forest_model.pkl'
with open(model_path,'rb') as file:
    model = pickle.load(file)

app= Flask(__name__)

# Configure MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'akshar'
app.config['MYSQL_DB'] = 'careerguidance'


mysql = MySQL(app)

app.secret_key = 'ekdjo39ijdowdpwmdo39'



#student login page
@app.route('/')
@app.route('/student_login', methods=['GET', 'POST'])
def student_login():
    msg = ''
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM student_accounts WHERE email = %s AND password = %s", (email, password))
        result = cursor.fetchone()
        cursor.close()
        
        if result:
            session['email'] = email
            session['password'] = result[3]
            
            #redirect the user to choose_data page if he has already filled data
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT email FROM student_data where email = %s",(email,))
            existing_data = cursor.fetchone()
            cursor.close()
            
            if existing_data:
                return redirect(url_for('choose_data'))
            else:
                return redirect(url_for('home'))
        
        else:
            msg = 'Incorrect email or password!'
            
    return render_template('student_login.html', msg=msg)

# Student registration page
@app.route('/student_register', methods=['GET', 'POST'])
def student_register():
    if request.method == 'POST' and 'email' in request.form and 'name' in request.form and 'student_class' in request.form and 'password' in request.form:
        email = request.form['email']
        
        name = request.form['name']
        student_class = request.form['student_class']  
        password = request.form['password']
        
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO student_accounts (email, name, student_class, password) VALUES (%s, %s, %s, %s)", (email, name, student_class, password))
        mysql.connection.commit()
        cursor.close()

        return redirect(url_for('student_login'))
    
    return render_template('student_register.html')

# Choose data option page
@app.route('/choose_data', methods=['GET','POST'])
def choose_data():
    
    if 'email' in session:
        
        data_option = request.form.get('data_option')
        
        #if user wants to use the previous data redirect to quiz page
        if data_option == 'use_previous':
            session['data_option'] = data_option
            return redirect(url_for('quiz'))
        
        #if user wants to use new data redirect to home page
        elif data_option == 'fill_new':
            session['data_option'] = data_option
            return redirect(url_for('home'))
    
        return render_template('choose_data.html')
    else:
        return redirect(url_for('student_login'))

# Home page
@app.route('/home', methods=['GET', 'POST'])
def home():
    if 'email' in session:
        email = session.get('email')
        
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT name FROM student_accounts WHERE email= %s",(email,))
        student_name = cursor.fetchone()[0]
        cursor.close()

        return render_template('home.html', student_name=student_name)
    else:
        return redirect(url_for('student_login'))

# Quiz page
@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if 'email' in session:
        email = session.get('email')
        
        if request.method == 'POST':
            # retrieve data from the form 
            interest = ', '.join(request.form.getlist('interest'))
            maths = request.form.get('maths')
            science = request.form.get('science')
            socialScience = request.form.get('socialScience')
            english = request.form.get('english')
            computer = request.form.get('computer')
         
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT email FROM student_data WHERE email = %s ",(email,))
            existing_data = cursor.fetchone()
                
            if existing_data:
                cursor.execute("UPDATE student_data SET interest = %s, grades_math = %s, grades_sci = %s, grades_eng = %s, grades_ss = %s, grades_comp = %s WHERE email = %s ", (interest, maths, science, english, socialScience, computer, email))
                mysql.connection.commit()
            else:
                cursor.execute("INSERT INTO student_data (email, interest, grades_math, grades_sci, grades_eng, grades_ss, grades_comp) VALUES (%s, %s, %s, %s, %s, %s, %s)", (email, interest, maths, science, english, socialScience, computer))
                mysql.connection.commit() 
                
                
            cursor.close()
            
            
            
        return render_template('quiz.html')
            
    else:
        return redirect(url_for('student_login'))


def random_que(tag, df, difficulty):
    df['difficulty'] = df['difficulty'].astype(int)
    
    if tag != 0:
        tag_df = df[(df['tag'] == tag) & (df['difficulty'] == difficulty)]
        return tag_df.sample(n=1).iloc[0]
    else:
        tag_df = df[df['difficulty'] == difficulty]
        return tag_df.sample(n=1).iloc[0]
    
        
        

tag_difficulty_levels = {
    'Computer': 3,
    'CivilServices': 3,
    'MarketingSales': 3,
    'Science': 3,
    'Mathematics': 3,
    'SocialSciencesHumanities': 3,
    'PerformingFineArts': 3,
    'Business': 3,
    'FinanceAccounting': 3,
    'Healthcare': 3
}

academic_scores = {
    'Computer': 0,
    'CivilServices': 0,
    'MarketingSales': 0,
    'Science': 0,
    'Mathematics': 0,
    'SocialSciencesHumanities': 0,
    'PerformingFineArts': 0,
    'Business': 0,
    'FinanceAccounting': 0,
    'Healthcare': 0
}

aptitude_score = 0
academic_result = 0
aptitude_result = 0 


# Start Quiz
@app.route('/quiz/start_quiz/<section>/<int:question_number>', methods=['GET', 'POST'])
def start_quiz(section, question_number):
    if 'email' in session:
        

        email = session.get('email')
        
        
        ques_set_academic = pd.read_csv("Datasets//academic_que.csv")
        ques_set_aptitude = pd.read_csv("Datasets//aptitude_que.csv")
        
    
        if section == 'academic':
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT interest FROM student_data WHERE email= %s", (email,))
            student_interest = cursor.fetchone()
            cursor.close()
        
            student_interest = student_interest[0].split(', ')
        
            interested_questions_df = pd.DataFrame(ques_set_academic[ques_set_academic['tag'].isin(student_interest)])
            noninterested_questions_df = pd.DataFrame(ques_set_academic[~ques_set_academic['tag'].isin(student_interest)])
        
            if question_number <=8:
                que_tag = interested_questions_df['tag'].unique()[question_number % len(interested_questions_df['tag'].unique())]
                difficulty = tag_difficulty_levels.get(que_tag)
                selected_question = random_que(que_tag, interested_questions_df, difficulty)
                
            else:
                
                que_tag = random.choice(noninterested_questions_df['tag'].unique())
                difficulty = tag_difficulty_levels.get(que_tag)
                selected_question = random_que(que_tag, noninterested_questions_df, difficulty)
                
            
            selected_question_json = selected_question.to_json()
            session['selected_question'] = selected_question_json 
            session['question_number'] = question_number
            session['section'] = section
                
        
            options = [{'index': i, 'text': selected_question[f'option{i}']} for i in range(1, 5)]
                
                
            next_question_number = question_number + 1
        
            if next_question_number == 16:
                return redirect(url_for('start_quiz', section='aptitude', question_number=0))
        
            return render_template('start_quiz.html', question=selected_question, options=options, section='academic',
                                   question_number=next_question_number)

        
        elif section == 'aptitude':
            
            if question_number < 5:
                app.logger.info("Que: %s", question_number)
                
                difficulty = question_number + 1  # Set difficulty to question_number + 1
                app.logger.info("Difficulty: %s", difficulty)
                
                selected_question = random_que(0, ques_set_aptitude, difficulty) 
                
                selected_question_json = selected_question.to_json()
                session['selected_question'] = selected_question_json 
                session['question_number'] = question_number
                session['section'] = section
                
                image_path = selected_question['image']
                
                if pd.notna(image_path):
                    image = image_path
                else:
                    image = None 
                
                options = [{'index': i, 'text': selected_question[f'option{i}']} for i in range(1, 5)]
                
            else:
                return redirect(url_for('quiz_complete'))


        
        return render_template('start_quiz.html', question=selected_question, options=options, section='aptitude',
                                       question_number=difficulty, image=image)
    
    else:
        return redirect(url_for('student_login'))
 

#Next que page
@app.route('/quiz/start_quiz/next_que', methods=['GET', 'POST'])
def next_que():
    if 'email' in session:
        global aptitude_score
        global academic_result
        global aptitude_result
       
        selected_question_json = session.get('selected_question')
        selected_question = json.loads(selected_question_json)
        
        
        question_number = session.get('question_number')
        section= session.get('section')
        
        question = selected_question['question']
        
        selected_option = int(request.form.get('selected_option'))
        correct_option = int(selected_question['answer'])
        
        selected_option_text = selected_question['option{}'.format(selected_option)]
        correct_option_text = selected_question['option{}'.format(correct_option)]
        
        
        if section == 'academic':
            
            que_tag = selected_question['tag']
            difficulty = selected_question['difficulty']
            
            
            app.logger.info("Que_tag: %s, Difficulty: %s", que_tag, difficulty)
            
            
            if selected_option == correct_option:
                
                academic_scores[que_tag] = (academic_scores[que_tag]+difficulty)
                academic_result +=1
                app.logger.info(academic_scores)
                
                tag_difficulty_levels[que_tag] = min(difficulty + 1, 5)
                
                
            else:
               
                academic_scores[que_tag] = (academic_scores[que_tag]+0)
                app.logger.info(academic_scores)
                
                tag_difficulty_levels[que_tag] = max(difficulty - 1, 1)
                
        
        if section == 'aptitude':
            
            if selected_option == correct_option:
                aptitude_score = aptitude_score + int(selected_question['difficulty'])
                aptitude_result +=1
                app.logger.info(aptitude_score)
                
            else:
                aptitude_score = aptitude_score + 0
                app.logger.info(aptitude_score)
                
            
        session.pop('selected_question')
        session.pop('question_number')
        session.pop('section')
    
        return render_template('next_que.html', question=question, selected_option=selected_option, 
                               correct_option=correct_option, selected_option_text=selected_option_text,
                               correct_option_text=correct_option_text,
                               section=section, question_number=question_number)
            
    else:
        return redirect(url_for('student_login'))
    


@app.route('/quiz_complete', methods=['GET', 'POST'])
def quiz_complete():
    if 'email' in session:
        global aptitude_score
        
            
        email = session.get('email')
        quiz_date = datetime.now().strftime('%Y-%m-%d')
        quiz_id = f'Q_{quiz_date}_1'
        cursor = mysql.connection.cursor()
        
        
        cursor.execute("SELECT email FROM student_scores WHERE email = %s AND quiz_id = %s", (email, quiz_id))
        result = cursor.fetchone()

        if result:
                
            cursor.execute("SELECT MAX(SUBSTRING_INDEX(quiz_id, '_', -1)) FROM student_scores WHERE email = %s AND quiz_id LIKE %s", (email, f'Q_{quiz_date}_%'))
            prev_num = int(cursor.fetchone()[0]) or 0 
            next_num = prev_num + 1
            quiz_id = f'Q_{quiz_date}_{next_num}'

            cursor.execute("INSERT INTO student_scores (email, quiz_id) VALUES (%s, %s)", (email, quiz_id))
        else:
                
            cursor.execute("INSERT INTO student_scores (email, quiz_id) VALUES (%s, %s)", (email, quiz_id))

        session['quiz_id'] = quiz_id
        
        mysql.connection.commit()

           
        for key, value in academic_scores.items():
            academic_scores[key] = (value / 12) * 100

        aptitude_score = (aptitude_score / 15) * 100

            
        cursor.execute("""
                UPDATE student_scores 
                SET 
                    scores_computer = %s, 
                    scores_civilservices = %s,
                    scores_marketingsales = %s,
                    scores_science = %s,
                    scores_mathematics = %s,
                    scores_socialscienceshumanities = %s,
                    scores_performingfinearts = %s,
                    scores_business = %s,
                    scores_financeaccounting = %s,
                    scores_healthcare = %s,
                    scores_aptitude = %s
                WHERE 
                    email = %s 
                    AND quiz_id = %s
            """, (
                academic_scores['Computer'],
                academic_scores['CivilServices'],
                academic_scores['MarketingSales'],
                academic_scores['Science'],
                academic_scores['Mathematics'],
                academic_scores['SocialSciencesHumanities'],
                academic_scores['PerformingFineArts'],
                academic_scores['Business'],
                academic_scores['FinanceAccounting'],
                academic_scores['Healthcare'],
                aptitude_score,
                email,
                quiz_id
        ))

           
        mysql.connection.commit()
        cursor.close()

        return render_template('quiz_complete.html')    
    else:
        return redirect(url_for('student_login'))
    
#Interest Survey
@app.route('/interest-survey', methods=['GET','POST'])
def interest_survey():
    if 'email' in session:
        
        ques_set_interest_survey = pd.read_csv("Datasets/interest_survey_que.csv")
        questions = ques_set_interest_survey['question'].tolist()
        options = ques_set_interest_survey[['option1', 'option2', 'option3', 'option4', 'option5']].values.tolist()
        streams = ques_set_interest_survey['stream'].tolist()
        
        if request.method == 'POST':
            
            science = request.form.get('science')
            commerce = request.form.get('commerce')
            arts = request.form.get('arts')
            general1 = request.form.get('general1')
            general2 = request.form.get('general2')
            
            quiz_id = session.get('quiz_id')
            
            cursor = mysql.connection.cursor()
            cursor.execute("UPDATE student_scores SET science=%s, commerce=%s, arts=%s, general1=%s, general2=%s where quiz_id =%s",(science,commerce,arts,general1,general2,quiz_id))
            result = cursor.rowcount
            mysql.connection.commit()
            
            cursor.close()
            
            if result:
                return redirect(url_for('show_results'))
        
        return render_template('interest_survey.html', questions = questions, options =options, streams = streams)
    else:
        return redirect(url_for('student_login'))



#Show Results page
@app.route('/show_results', methods=['GET', 'POST'])
def show_results():
    if 'email' in session:
        global academic_result
        global aptitude_result
      
        return render_template('show_results.html', academic_result = academic_result, aptitude_result = aptitude_result)
            
    else:
        return redirect(url_for('student_login'))

#Show predictions
@app.route('/show_prediction')
def show_prediction():
    if 'email' in session: 
        email = session.get('email')
        quiz_id = session.get('quiz_id')
        
        
        
        feature_names = ['grades_math', 'grades_sci', 'grades_eng', 'grades_ss', 'grades_comp',
                         'Computer', 'CivilServices', 'MarketingSales', 'Science', 'Mathematics',
                         'SocialSciencesHumanities', 'PerformingFineArts', 'Business', 'FinanceAccounting',
                         'Healthcare', 'Aptitude', 'science', 'commerce', 'arts', 'general1', 'general2']
        
        feature_values = []
        
        cursor = mysql.connection.cursor()
        
        cursor.execute("SELECT * FROM student_data WHERE email=%s", (email,))
        grades = cursor.fetchone()
        
        if grades:
            feature_values.extend([grades[2], grades[3], grades[4], grades[5], grades[6]])

        cursor.execute("SELECT * FROM student_scores WHERE quiz_id=%s", (quiz_id,))
        scores = cursor.fetchone()
        
        if scores:
            feature_values.extend([scores[3], scores[4], scores[5], scores[6], scores[7], scores[8],
                                    scores[9], scores[10], scores[11], scores[12], scores[13], 
                                    scores[14], scores[15], scores[16], scores[17], scores[18]])
        
        cursor.close()
        
        feature_df = pd.DataFrame([feature_values], columns=feature_names)
        
        model = joblib.load("random_forest_model.pkl")
        
        prediction = model.predict(feature_df)
        print(prediction)
        if prediction < 1.5:
            stream = "Science"
            content="1"
        elif prediction < 2.5:
            stream = "Commerce"
            content= "2"
        else:
            stream = "Arts"
            content= "3"
        
        email=session.get('email')
        session.clear()
        session['email'] = email
        
        return render_template('show_prediction.html', stream=stream, content=content)
    else:
        return redirect(url_for('student_login'))

@app.errorhandler(404)
@app.errorhandler(500)
@app.errorhandler(505)
def handle_errors(error):
    return render_template('error.html'), error.code

@app.errorhandler(BuildError)
def handle_build_error(error):
    return render_template('error.html'), 500  

@app.errorhandler(TemplateNotFound)
def template_not_found(error):
    return render_template('error.html'), 404

   
   
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)