import requests
import os
import shutil
from concurrent.futures import ThreadPoolExecutor

from moviepy.editor import VideoFileClip, concatenate_videoclips

from crawler import timed, Chrome_webdriver


def single_scrape(url: str, temp_folder: str, filename: str = '', chunk_size: int = 1024) -> None:
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
        executor.map(single_scrape, target_list,
                     [temp_folder] * len(target_list))
    mergeCrawl(output_name, temp_folder)
    try:
        shutil.rmtree(temp_folder)
    except PermissionError:
        pass


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
    name = input("Please enter the NBA player's name: ")
    # name = 'Chet Holmgren'
    dr = Chrome_webdriver()
    player_url, player_team = dr.search_player_url(name)
    player_id, player_name = dr.separate_player_url(player_url)
    header_arr, value_arr, target_list = dr.player_lastest_highlight(
        player_id)

    if target_list:
        output_name = dr.output_name_creator(player_url, header_arr, value_arr)
        print(output_name, len(target_list))
        startCrawl(output_name, target_list)

    # name = input("Please enter the NBA player's name: ")
    # date = input("Please enter the date (YYYY-MM-DD): ")
    # # name = 'Chet Holmgren'
    # # date = "2023-11-02"

    # dr = Chrome_webdriver()
    # player_url, player_team = dr.search_player_url(name)
    # player_id, player_name = dr.separate_player_url(player_url)

    # game_url, game_status_code = dr.search_game_url(player_team, date)
    # game_id, game_opponent = dr.separate_game_url(game_url, player_team)

    # code_explain = {
    #     0: 'do not exist', 1: "haven't begin yet", 2: 'is ongoing', 3: 'finished'}
    # if game_status_code < 3:
    #     print(
    #         f'cannot produce highlight now because the game {code_explain[game_status_code]}')
    # target_list = dr.player_highlight(player_id, game_id, date)
    # output_name = f"{player_name} {date} vs {game_opponent.upper()} Highlights .mp4"
    # if target_list:
    #     startCrawl(output_name, target_list)
