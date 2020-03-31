# 从imdb爬取ml-100k的电影封面
ml-100k:数据集，只用到了./ml-100k/u.item
result: 电影封面
电影id.jpg,可以用u.item找到id->电影名称对应关系
## 所用到的库
```python
import pandas as pd    # 读取ml-100k中的文件
from pyquery import PyQuery as pq    # 爬虫库
import requests    # 爬虫库
import logging    # 记录日志
import os    # 判断文件是否存在
import multiprocessing    # 多进程，加速爬取
import shutil  # 最后爬取不到的封面，复制no_found封面
```
## 第一步 读取所有电影名称
(ml-100k下载)[http://files.grouplens.org/datasets/movielens/ml-100k.zip]，下载不了也没关系，后面GitHub有
```python
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
```
## 第二步 获取电影对应的封面链接
先定义一个爬虫接口
```python
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
```
先用https://www.imdb.com/find?q=搜索电影名称，然后进入详细电影介绍，找到封面url
```python
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
```
## 第三步 保存封面url到本地文件中
```python
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
```
## 第四步 使用进程池加速爬取，添加异常处理
爬取失败的封面，多爬几次，或手动添加即可。(少许封面因为网速问题会出现失败)
```python
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


if __name__ == '__main__':
    movies_data = get_movie_names()  # 获取所有电影名称
    print(movies_data)
    pool = multiprocessing.Pool()   # 创建进程池
    pool.map(main, movies_data)     # 进程映射
    pool.close()    # 关闭进程加入进程池
    pool.join()     # 等待子进程结束
    print('end')
```
## 第五步 填充没有爬取到封面的电影
```python
def fill(movie_data, fill_jpg='./no_found.jpg', save_base_path='./result/'):
    """讲没找到封面的电影用no_found.jpg代替"""
    for i in range(1, len(movies_data)+1):
        poster_jpg = f'{save_base_path}{i}.jpg'
        if not os.path.exists(poster_jpg):
            shutil.copyfile(fill_jpg, poster_jpg)
```
全部代码如下
```python
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

```
