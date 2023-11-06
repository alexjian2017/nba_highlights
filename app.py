from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from crawler import timed, Chrome_webdriver
from celery import Celery

from nba import startCrawl


DB_NAME = 'test1.db'


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'

db.init_app(app)


class Player(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_name: Mapped[int] = mapped_column(String(50), nullable=False)
    player_id: Mapped[int] = mapped_column(String(10), nullable=False)
    group: Mapped[int] = mapped_column(String(50), nullable=False)

    def __repr__(self):
        return f'{self.player_name}({self.group}): {self.player_id}'


with app.app_context():
    db.create_all()

# 配置 Celery
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)


@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        player_name = request.form['player_name']
        group = request.form['player_group']
        add_player(player_name, group)
        return redirect('/')
    players = Player.query.order_by(Player.group).all()
    groups = Player.query.with_entities(
        Player.group).distinct().all()
    return render_template('home.html', players=players, groups=groups)


@celery.task
def add_player(player_name: str, group: str):
    dr = Chrome_webdriver()
    player_url, player_team = dr.search_player_url(player_name)
    player_id, player_name = dr.separate_player_url(player_url)
    new_player = Player(player_name=player_name,
                        player_id=player_id, group=group)
    try:
        db.session.add(new_player)
        db.session.commit()
    except:
        return 'There was an issue when adding player'
    else:
        dr.quit()


@app.route('/delete/<int:id>')
def delete(id):
    player_to_delete = db.get_or_404(Player, id)
    try:
        db.session.delete(player_to_delete)
        db.session.commit()
        return redirect('/')
    except:
        return 'There was a problem when deleting'


@app.route('/download', methods=['POST'])
def download_select_group():
    select_group = request.form.getlist("player_group")
    download(select_group)
    return redirect('/')


@celery.task
def download(select_group: list[str]):
    dr = Chrome_webdriver()
    for group in select_group:
        group_players = Player.query.filter_by(group=group).all()
        for player in group_players:
            header_arr, value_arr, target_list = dr.player_lastest_highlight(
                player.player_id)
            if target_list:
                output_name = dr.output_name_creator(
                    player.player_name, header_arr, value_arr)
                print(output_name, len(target_list))
                startCrawl(output_name, target_list)
    dr.quit()
    return "Completed"


@app.route('/static/css/')
def css():
    return render_template('styles.css')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
