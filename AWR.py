
# coding: utf-8

# # AWRの順位データ取得

# 第1引数にAWRのプロジェクト名、第2引数に取得対象日を指定して実行。
# 
# 【例】  
# python AWR.py 02_%E3%82%AB%E3%82%A4%E3%82%B7%E3%83%A3%E3%81%AE%E8%A9%95%E5%88%A4_Daily 2018-02-09

# ## ライブラリのインストール

# In[1]:


import tarfile, json,os,urllib,requests,zipfile,sys,subprocess
import pandas as pd
from dotenv import load_dotenv, find_dotenv
from urllib.parse import urlparse


# ## 環境変数の指定

# In[2]:


#  ディレクトリから.envファイルを探す
dotenv_path = find_dotenv()

# 環境変数をロード
load_dotenv(dotenv_path)

# API_KEYに環境変数を代入
token = os.environ.get("AWR_token")


# ## 引数の取得

# In[3]:


args = sys.argv
API_project = args[1]
date = args[2]


# ## APIコール用のURLを生成

# In[4]:


url = 'https://api.awrcloud.com/v2/get.php?action=get&project={}&date={}&compression=zip&token={}'
API_call = url.format(API_project,date,token)


# ## 格納先ディレクトリの作成とファイル名の指定

# In[5]:


# ディレクトリの作成
directory = 'output/' + date + '/'
try:
    os.makedirs(directory)
except FileExistsError:
    pass

# ファイル名の指定
filename = date + '.zip'
# 階層も含めたディレクトリ名の指定
output =  directory + filename


# ## Zipファイルをダウンロード・解凍し、jsonのリストを取得

# In[6]:


# Zipファイルのダウンロード
r = requests.get(API_call, stream=True)
with open(output, 'wb') as f:
    for chunk in r.iter_content(chunk_size=1024):
        if chunk:
            f.write(chunk)
            f.flush()

# Zipファイルの格納
zfile = zipfile.ZipFile(output)
zfile.extractall(directory)

# jsonリストの取得
import glob
file_list = glob.glob(directory + "*.json")


# ## jsonをデータフレームに整形する関数

# In[7]:


def json_to_df(target_file):
    # jsonから辞書型へ変更
    with open(target_file) as f:
       data = json.load(f)

    # 辞書からデータフレームへの変換
    rankdata = pd.DataFrame.from_dict(data['rankdata'])

    # 検索エンジン、キーワード、日付のデータを追加
    rankdata['searchengine'] = data['searchengine']
    rankdata['keyword'] = data['keyword']
    rankdata['date'] = date

    # urlからドメインを抜き出して['domain']に格納
    for index, row in rankdata.iterrows():
        rankdata.loc[index,'domain'] = urlparse(row['url']).netloc
        
    return rankdata


# ## データフレームを結合し、csvにアウトプット

# In[8]:


# 空のデータフレームを作成
ranking = pd.DataFrame()

# jsonのリストをデータフレームに変換し、空のデータフレームに追加
for target_file in file_list:
    ranking = ranking.append(json_to_df(target_file))

# 1KWにつき1ドメインになるよう重複削除
ranking.drop_duplicates(['date', 'keyword','domain'])

# csvに格納
ranking.to_csv("result.csv", index=False, mode='a', header=False)


# In[9]:


# pyファイルに変換して保存
subprocess.run(['jupyter', 'nbconvert', '--to', 'python', 'AWR.ipynb'])

