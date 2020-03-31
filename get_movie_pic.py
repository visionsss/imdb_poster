import pandas as pd
from pyquery import PyQuery as pq
import requests
import logging
import os
import multiprocessing
import shutil


def scrape_api(url):
    """爬取网页接口"""
    logging.info(f'scraping {url}')
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response
        logging.error(f'scraping {url} status code error')
    except requests.RequestException:
        logging.error(f'scraping {url} error')
        return None


def get_movie_names(item_path='./ml-100k/u.item'):
    """获取电影名称./ml-100k/u.item
    Args:
        item_path: ml-100k电影名称数据集
    Return:
        movies_data: ml-100k中[(电影id,名称), ()]
    """
    movies_data = []
    data = pd.read_table(item_path, sep='|', encoding='ISO-8859-1', header=None)
    for idx, row in data.iterrows():
        movies_data.append((row[0], row[1]))
    print(f'get {len(movies_data)} movie name success')
    return movies_data


def get_movie_png(movie_name):
    """获取每部电影的封面图片的url"""
    # imdb搜索
    search_url = f'https://www.imdb.com/find?q={movie_name}'
    response = scrape_api(search_url)
    if response is None:
        return None
    doc = pq(response.text)
    href = doc('.findList tr td a').attr('href')    # class='.findList' <tr> <td> <a>标签下的href属性
    if href is None:
        return None
    # imdb封面url链接获取
    detail_url = f'https://www.imdb.com/{href}'
    response = scrape_api(detail_url)
    if response is None:
        return None
    detail_doc = pq(response.text)
    jpg_url = detail_doc('.poster a img').attr('src')  # class='.poster' <a> <img>标签下的src属性
    return jpg_url


def save_pictures(url, movie_index, save_base_path='./result/'):
    """根据url保存图片"""
    # 判断路径是否存在
    if not os.path.exists(save_base_path):
        os.mkdir(save_base_path)
    r = scrape_api(url)
    try:
        jpg = r.content
        open(f'{save_base_path}{movie_index}.jpg', 'wb').write(jpg)
        logging.info(f'成功保存{movie_index}.jpg')
    except IOError:
        logging.error(f'{movie_index}.jpg保存失败')


def main(movie_data, save_base_path='./result/'):
    # 设置日志格式
    logging.basicConfig(level=logging.INFO)
    movie_index = movie_data[0]
    movie_name = movie_data[1]
    # 已经爬取过的图片就无需重复爬取
    if os.path.exists(f'{save_base_path}{movie_index}.jpg'):
        return
    jpg_url = get_movie_png(movie_name)  # 获取电影图片链接
    if jpg_url is None:     # 获取电影图片链接失败
        jpg_url = get_movie_png(movie_name.split('(')[0])  # 把电影名的年份去掉再搜索
        if jpg_url is None:  # 获取电影图片链接失败
            logging.error(f'error to get {movie_name} pic_url')
    else:
        save_pictures(jpg_url, movie_index, save_base_path)  # 保存图片


def fill(movie_data, fill_jpg='./no_found.jpg', save_base_path='./result/'):
    """讲没找到封面的电影用no_found.jpg代替"""
    for i in range(1, len(movies_data)+1):
        poster_jpg = f'{save_base_path}{i}.jpg'
        if not os.path.exists(poster_jpg):
            shutil.copyfile(fill_jpg, poster_jpg)


if __name__ == '__main__':
    movies_data = get_movie_names()  # 获取所有电影名称
    print(movies_data)
    pool = multiprocessing.Pool()   # 创建进程池
    pool.map(main, movies_data)     # 进程映射
    pool.close()    # 关闭进程加入进程池
    pool.join()     # 等待子进程结束
    print('end')
    # 我能爬取1551/1682张封面
    fill(movies_data)  # 将爬取不到的封面用一张图(no_found.jpg)代替
