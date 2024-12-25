from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import plotly.graph_objs as go
from plotly.utils import PlotlyJSONEncoder
import json
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Flask приложение
app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Конфигурация базы данных
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///messages.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Логирование для Telegram-бота
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Telegram-бот токен
TELEGRAM_TOKEN = "7648569681:AAGD1vpOYv-sHV7tCPGRie8l6kgro6nEQJk"

# Модель для пользователей
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # Роли: "manager", "admin"

# Модель для статистики сообщений
class MessageStat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), nullable=False)
    count = db.Column(db.Integer, default=0)

# Telegram-бот команды
async def start(update, context: CallbackContext):
    """Приветственное сообщение."""
    await update.message.reply_text("Привет! Я бот. Напиши что-нибудь, и я отвечу!")

async def handle_message(update, context: CallbackContext):
    """Обработчик текстовых сообщений от пользователей."""
    user_id = str(update.message.from_user.id)
    text = update.message.text

    # Обновляем статистику сообщений
    stat = MessageStat.query.filter_by(user_id=user_id).first()
    if stat:
        stat.count += 1
    else:
        stat = MessageStat(user_id=user_id, count=1)
        db.session.add(stat)
    db.session.commit()

    await update.message.reply_text(f"Вы сказали: {text}")

# Инициализация Telegram-бота
application = Application.builder().token(TELEGRAM_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Flask авторизация
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Маршруты Flask
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        role = request.form['role']
        user = User(username=username, password=password, role=role)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            return "Неверный логин или пароль"
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    if current_user.role == 'admin':
        return render_template('admin_dashboard.html')
    elif current_user.role == 'manager':
        return render_template('manager_dashboard.html')
    return "Доступ запрещен"

@app.route('/edit_responses', methods=['GET', 'POST'])
@login_required
def edit_responses():
    if current_user.role not in ['admin', 'manager']:
        return "Доступ запрещен"
    if request.method == 'POST':
        # Логика редактирования ответов бота
        return "Ответы бота обновлены!"
    return render_template('edit_responses.html')

@app.route('/stats', methods=['GET'])
@login_required
def stats():
    if current_user.role != 'admin':
        return "Доступ запрещен"
    stats = MessageStat.query.all()
    return render_template('stats.html', stats=stats)

@app.route('/stats_chart', methods=['GET'])
@login_required
def stats_chart():
    if current_user.role != 'admin':
        return "Доступ запрещен"
    stats = MessageStat.query.all()
    users = [stat.user_id for stat in stats]
    counts = [stat.count for stat in stats]

    bar_chart = go.Bar(x=users, y=counts, name='Сообщения')
    layout = go.Layout(title='Сообщения по пользователям', xaxis=dict(title='Пользователи'), yaxis=dict(title='Количество сообщений'))
    fig = go.Figure(data=[bar_chart], layout=layout)

    graphJSON = json.dumps(fig, cls=PlotlyJSONEncoder)
    return render_template('stats_chart.html', graphJSON=graphJSON)

@app.route('/start_bot', methods=['POST'])
def start_bot():
    """Запуск Telegram-бота."""
    try:
        application.run_polling()
        return "Бот запущен!"
    except Exception as e:
        logging.error(f"Ошибка запуска бота: {e}")
        return f"Ошибка запуска бота: {e}"

# Инициализация базы данных
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Создание таблиц в базе данных
    app.run(debug=True, use_reloader=False)
