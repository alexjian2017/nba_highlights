import requests
import os
import shutil
from concurrent.futures import ThreadPoolExecutor

from moviepy.editor import VideoFileClip, concatenate_videoclips

from crawler import timed, Chrome_webdriver


def single_scrape(url: str, temp_folder: str = 'crawl_temp', filename: str = '', chunk_size: int = 1024) -> None:
    """
    You already have url link with video in it
    """
    if not filename:
        filename = url.split('/')[-2]
        filename = f'{int(filename):04.0f}.mp4'
    r = requests.get(url, stream=True)

    with open(os.path.join(temp_folder, filename), 'wb') as f:
        for chunk in r.iter_content(chunk_size=chunk_size):
            f.write(chunk)


@timed
def startCrawl(output_name: str, target_list: list[str], temp_folder: str = 'crawl_temp') -> None:
    if os.path.exists(temp_folder):
        shutil.rmtree(temp_folder)
    os.mkdir(temp_folder)
    with ThreadPoolExecutor(max_workers=16) as executor:
        executor.map(single_scrape, target_list)
    mergeCrawl(output_name, temp_folder)
    shutil.rmtree(temp_folder)


def mergeCrawl(output_name, temp_folder: str, target_folder: str = 'result') -> None:
    if not os.path.exists(target_folder):
        os.mkdir(target_folder)
    arr = []
    for filename in os.listdir(temp_folder):
        if filename.endswith(".mp4"):
            filepath = os.path.join(temp_folder, filename)
            arr.append(VideoFileClip(filepath))
    output = concatenate_videoclips(arr)
    output.write_videofile(os.path.join(target_folder, output_name), temp_audiofile="temp-audio.m4a",
                           remove_temp=True, codec="libx264", audio_codec="aac")


if __name__ == '__main__':

    name = 'Derrick White'
    date = '2023-10-30'
    dr = Chrome_webdriver()

    player_id, player_name, team = dr.search_player_id(name)
    print(player_id, player_name, team)
    game_id, game_rival, game_status_code = dr.search_game_id(team, date)
    print(game_id, game_rival, game_status_code)
    code_explain = {
        0: 'do not exist', 1: "haven't begin yet", 2: 'is ongoing', 3: 'finished'}
    if game_status_code < 3:
        print(
            f'cannot produce highlight now because the game {code_explain[game_status_code]}')
        exit()
    target_list = dr.player_highlight(player_id, game_id, date)
    print(len(target_list))
    output_name = f"{player_name} vs {game_rival.upper()} Highlights {date}.mp4"
    if target_list:
        startCrawl(output_name, target_list)
