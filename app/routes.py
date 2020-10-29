from app import app,forms,db,socketio
from flask_socketio import emit,leave_room,join_room
from flask import request,redirect,url_for,render_template,flash,get_flashed_messages,flash,jsonify
from flask_login import current_user,login_user,logout_user,login_required
from app.models import User,thread,post
from app.forms import LoginForm,RegisterForm
from werkzeug.urls import url_parse
from wtforms.validators import ValidationError
from datetime import datetime

@app.route('/')
@app.route('/index')
def index():
    return render_template('celis.html',title='Home',data_footer_aos="fade-left",data_aos_footer_delay=100,data_aos_header="fade-left",data_header_aos_delay=100)

@app.route('/courses')
@login_required
def course():
    return render_template('courses.html',title='Courses')

@app.route('/profile/<username>')
def profile(username):
    user=User.query.filter_by(username=username).first()
    if user.user_role=="Instructor":
        posts=post.query.filter_by(user_id=user.id).all()
        no_posts=len(posts)
        return render_template('profile_instructor.html',title=user.username[:3],user=user,no_posts=no_posts,posts=posts)
    elif user.user_role=="Student" :
        posts=post.query.filter_by(user_id=user.id).all()
        no_posts=len(posts)
        return render_template('profile_student.html',title=user.username[:3],user=user,no_posts=no_posts,posts=posts)



@app.route('/logout')
def logout():
    current_user.last_seen=datetime.utcnow()
    db.session.commit()
    logout_user()
    return redirect(url_for('index'))

@app.route('/edit_profile',methods=['POST','GET'])
def edit_profile():
    if current_user.is_authenticated:
        if request.method=='POST':
            twitter_link=request.form['twitter_link']
            facebook_link=request.form['linkedin_link']
            instagram_link=request.form['github_link']
            birthdate=request.form['birthdate']
            about=request.form['interests']
            user=User.query.filter_by(id=current_user.id).first()
            user.twitter=twitter_link
            user.facebook=facebook_link
            user.instagram=instagram_link
            user.birthdate=birthdate
            user.Interests=about
            db.session.commit()
        return render_template('edit_profile.html',)
    else:
        return redirect(url_for('index'))



@app.route('/login',methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form=LoginForm()
    if form.validate_on_submit():
        user=User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid Email or Password',category="danger")
            return redirect(url_for('login'))
        login_user(user,remember=form.remember_me.data)
        next_page=request.args.get('next')
        if not next_page or url_parse(next_page).netloc!='':
            next_page=url_for('index')
        return redirect(next_page)
    return render_template('signinpage.html',title='SignIn',form=form)



@app.route('/basetemplate')
def base():
    return render_template('template.html',title='template')


@app.route('/register',methods=['POST','GET'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form=forms.RegisterForm()
    if form.validate_on_submit():
        user=User(username=form.username.data,email=form.email.data,user_role=form.user_role.data,Region=form.Region.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Successfully Registered',category="success")
        print(form.password.data)
        print(form.user_role.data)
        print(form.Region.data)
        return redirect(url_for('login'))
    return render_template('signuppage.html',form=form,title='Register')

@app.route('/forum')
@login_required
def forum():
    threads=thread.query.all()
    return render_template('forumhome.html',title='Forum',threads=threads)

@app.route('/thread/<int:thread_id>',methods=['POST','GET'])
@login_required
def forum_(thread_id):
        posts=post.query.filter_by(thread_id=thread_id).order_by(post.time.asc())
        thread_name=thread.query.filter_by(id=thread_id).first().subject
        return render_template('forum.html',title='Forum',posts=posts,room=thread_name)


@app.route('/contact')
@login_required
def contactus():
    return render_template('contactus.html',title='Contact Us')

#socket events

@socketio.on('join')
def join_room_(data):
    join_room(data['room'])
    socketio.emit('status',data,room=data['room'],dif_user=0)

@socketio.on('leave')
def leave_room_(data):
    leave_room(data['room'])
    print('User gonna leave')
    socketio.emit('left_room_announcement',data,room=data['room'],dif_user=0)

@socketio.on('send_message')
def send_message(data):
    user_=User.query.filter_by(username=data['username']).first()
    thread_=thread.query.filter_by(subject=data['room']).first()
    p=post(message=data['message'],user_id=user_.id,thread_id=thread_.id)
    db.session.add(p)
    db.session.commit()
    p=post.query.filter_by(message=data['message'],user_id=user_.id,thread_id=thread_.id).first()
    socketio.emit('received_message',{'room':data['room'],'user_id':p.user_id,'username':user_.username,'msg':p.message,'post_id':p.id,'thread_id':thread_.id},room=data['room'],dif_user=p.user_id)

@socketio.on('remove')
def remove_post(data):
    id=int(data['post_id'].split('f')[1])
    post_=post.query.filter_by(id=id).first()
    db.session.delete(post_)
    db.session.commit()
    socketio.emit('confirm_remove',{"id":data['post_id']},room=data['room'])
