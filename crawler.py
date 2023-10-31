import time
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"


def timed(function):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        value = function(*args, **kwargs)
        end_time = time.time()
        func_name = function.__name__
        print(f'{func_name} 花費 {(end_time - start_time) } s!')
        return value
    return wrapper


class Chrome_webdriver(webdriver.Chrome):
    def __init__(self):
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('log-level=3')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-extensions')
        options.add_argument('--headless')
        options.add_argument("--disable-3d-apis")
        options.add_argument(
            f"user-agent={USER_AGENT}")
        super(Chrome_webdriver, self).__init__(
            options=options)

    def search_player_id(self, player: str) -> tuple[str, str, str]:
        """
        return (player_id, player_name player_team)
        """
        url = 'https://www.nba.com/players'
        self.get(url)
        time.sleep(1)
        search_field = self.find_element(
            By.CSS_SELECTOR, 'div[class="Block_blockAd__1Q_77"] div input')
        search_field.clear()
        search_field.send_keys(player)
        time.sleep(1)
        player_result = self.find_elements(
            By.CSS_SELECTOR, 'a[class="Anchor_anchor__cSc3P RosterRow_playerLink__qw1vG"]')
        if len(player_result) != 1:
            return '', '', ''
        team_result = self.find_elements(
            By.CSS_SELECTOR, 'a[class="Anchor_anchor__cSc3P RosterRow_team__AunTP"]')
        player_url = player_result[0].get_attribute('href')
        player_id = player_url.split('/')[-3]
        player_name = player_url.split('/')[-2]
        player_name = ' '.join(player_name.split('-')).title()
        team = team_result[0].get_attribute('innerHTML')
        return player_id, player_name, team

    def search_game_id(self, team: str, date: str) -> tuple[str, str, int]:
        """
        return (game_id, game_rival, game_status_code)
        game_status_code (0: no game, 1: not begin, 2: ongoing, 3: finished)
        """
        if not date:
            date = datetime.datetime.now().strftime('%Y-%m-%d')
        team = team.lower()
        url = f'https://www.nba.com/games?date={date}'
        self.get(url)
        time.sleep(2)
        games = self.find_elements(
            By.CSS_SELECTOR, 'a[class="GameCard_gcm__SKtfh GameCardMatchup_gameCardMatchup__H0uPe"]')
        for game in games:
            href = game.get_attribute('href')
            if team not in href:
                continue
            for word in href.split('/')[-1].split('-'):
                if word in ('vs', team):
                    continue
                if len(word) == 3:
                    game_rival = word
                else:
                    game_id = word
            # game_id = re.search("\d+", href)
            game_status = game.find_elements(
                By.CSS_SELECTOR, 'div[class="GameCardMatchupStatusText_gcs__2yfjE"]')
            game_status_code = game_status[0].get_attribute(
                'data-game-status')

            return (game_id, game_rival, int(game_status_code)) if game_id else ('', '', 0)
        return ('', '', 0)

    def determine_season(self, date: str) -> str:
        year, month, day = date.split('-')
        year_int = int(year)
        if int(month) >= 10:
            return f'{year}-{str(year_int+1)[2:]}'
        else:
            return f'{str(year_int-1)}-{year[2:]}'

    def player_highlight(self, player_id: str, game_id: str, date: str) -> list[str]:
        stats = {'FGM': 3, 'AST': 1, 'STL': 1, 'BLK': 1}
        season = self.determine_season(date)
        target_list = []
        for key, val in stats.items():
            url = f'https://www.nba.com/stats/events/?ContextMeasure={key}&GameID={game_id}&PlayerID={player_id}&Season={season}&flag={val}&sct=plot&section=game'
            self.get(url)
            print(url)
            time.sleep(2)
            data = self.find_elements(
                By.CSS_SELECTOR, 'tr[class="EventsTable_row__Gs8B9"]')
            print(f'{key} {len(data)}')
            if not data:
                continue
            for i in range(len(data)):
                self.execute_script("arguments[0].click();", data[i])
                time.sleep(0.5)
                video_element = self.find_element(
                    By.ID, "vjs_video_3_html5_api")
                video_url = video_element.get_attribute('src')
                if 'missing' in video_url:
                    continue
                target_list.append(video_url)
        return target_list
