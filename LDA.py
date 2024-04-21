import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import re

# 加载数据
file_path = 'papers.csv'
papers_df = pd.read_csv(file_path, encoding='ISO-8859-1')

# 数据清洗，移除<inf...</inf>
papers_df['Title'] = papers_df['Title'].apply(lambda x: re.sub(r"<inf[^>]*>.*?</inf>", "", x, flags=re.DOTALL) if isinstance(x, str) else x)
papers_df['Abstract'] = papers_df['Abstract'].apply(lambda x: re.sub(r"<inf[^>]*>.*?</inf>", "", x, flags=re.DOTALL) if isinstance(x, str) else x)
papers_df['Abstract'] = papers_df['Abstract'].apply(lambda x: re.sub(r"[\n\r]+", " ", x) if isinstance(x, str) else x)

# 填充缺失值
papers_df['text'] = papers_df['Title'].fillna('') + " " + papers_df['Abstract'].fillna('')

# 初始化TF-IDF Vectorizer
tfidf_vectorizer = TfidfVectorizer(max_features=100, stop_words='english', ngram_range=(1, 2))

# 应用TF-IDF处理
tfidf_matrix = tfidf_vectorizer.fit_transform(papers_df['text'])
print(tfidf_matrix)
# 获取关键词名称
feature_names = tfidf_vectorizer.get_feature_names_out()
print(feature_names)
# 初始化LDA模型
n_topics = 2
lda = LatentDirichletAllocation(n_components=n_topics, random_state=0, learning_method='online')

# 应用LDA模型
lda.fit(tfidf_matrix)

# 获取每个主题的关键词
def display_topics(model, feature_names, no_top_words):
    topic_dict = {}
    for topic_idx, topic in enumerate(model.components_):
        topic_dict["Topic %d" % (topic_idx)] = [feature_names[i]
                        for i in topic.argsort()[:-no_top_words - 1:-1]]
    return topic_dict

top_words_per_topic = display_topics(lda, feature_names, 10)
print(top_words_per_topic)
# 生成词云图的函数
def generate_word_clouds(topic_words):
    fig, axes = plt.subplots(1, len(topic_words), figsize=(20, 10))
    for ax, (title, words) in zip(axes.flatten(), topic_words.items()):
        word_freq = {word: value for word, value in zip(words, range(len(words), 0, -1))}
        wordcloud = WordCloud(width=1800, height=1800, background_color="rgba(255,255,255,0)").generate_from_frequencies(word_freq)
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.set_title(title)
        ax.axis('off')
    plt.subplots_adjust(top=1-0.197, bottom=0.197)
    plt.tight_layout()
    plt.savefig("WordClouds.png", format='png')

# 生成并显示词云
generate_word_clouds(top_words_per_topic)

