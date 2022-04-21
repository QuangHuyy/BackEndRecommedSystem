import os
os.environ["KMP_DUPLICATE_LIB_OK"]="TRUE"
import torch
import numpy
import re
import underthesea # Thư viện tách từ


from transformers import AutoModel, AutoTokenizer # Thư viện BERT

import pandas as pd
import csv

# Hàm load model BERT
def load_bert():
    v_phobert = AutoModel.from_pretrained("vinai/phobert-base")
    v_tokenizer = AutoTokenizer.from_pretrained("vinai/phobert-base", use_fast=False)
    return v_phobert, v_tokenizer

# Hàm chuẩn hoá câu
def standardize_data(row):
    # Xóa dấu chấm, phẩy, hỏi ở cuối câu
    row = re.sub(r"[\.,\?]+$-", "", row)
    # Xóa tất cả dấu chấm, phẩy, chấm phẩy, chấm thang, ... trong câu
    row = row.replace(",", " ").replace(".", " ") \
        .replace(";", " ").replace("“", " ") \
        .replace(":", " ").replace("”", " ") \
        .replace('"', " ").replace("'", " ") \
        .replace("!", " ").replace("?", " ") \
        .replace("-", " ").replace("?", " ")
    row = row.strip().lower()
    return row

# Hàm load danh sách các từ vô nghĩa: lắm, ạ, à, bị, vì..
def load_stopwords():
    sw = []
    with open("../vietnamese-stopwords.txt", encoding='utf-16') as f:
        lines = f.readlines()
    for line in lines:
        sw.append(line.replace("\n",""))
    return sw


# Hàm load dữ liệu từ file data_1.csv để train model
def load_data():
    v_text=[]
    ds = pd.read_csv(
    "../laptop_all.csv")
    for sensten in ds["full_name"].tolist():
        v_text.append(str(sensten))

    return v_text


# Hàm tạo ra bert features
def make_bert_features(v_text):
    global phobert, sw
    v_tokenized = []
    max_len = 100 # Mỗi câu dài tối đa 100 từ
    for i_text in v_text:
        print("Đang xử lý line = ", i_text)
        # Phân thành từng từ
        line = underthesea.word_tokenize(i_text)
        # Lọc các từ vô nghĩa
        filtered_sentence = [w for w in line if not w in sw]
        # Ghép lại thành câu như cũ sau khi lọc
        line = " ".join(filtered_sentence)
        line = underthesea.word_tokenize(line, format="text")
        # print("Word segment  = ", line)
        # Tokenize bởi BERT
        line = tokenizer.encode(line)
        v_tokenized.append(line)

    # Chèn thêm số 1 vào cuối câu nếu như không đủ 100 từ
    padded = numpy.array([i + [1] * (max_len - len(i)) for i in v_tokenized])
    print('padded:', padded[0])
    print('len padded:', padded.shape)

    # Đánh dấu các từ thêm vào = 0 để không tính vào quá trình lấy features
    attention_mask = numpy.where(padded == 1, 0, 1)
    print('attention mask:', attention_mask[0])

    # Chuyển thành tensor
    padded = torch.tensor(padded).to(torch.long)
    print("Padd = ",padded.size())
    attention_mask = torch.tensor(attention_mask)

    # Lấy features dầu ra từ BERT
    with torch.no_grad():
        last_hidden_states = phobert(input_ids= padded, attention_mask=attention_mask)

    v_features = last_hidden_states[0][:, 0, :].numpy()
    print(v_features.shape)
    return v_features

ds = pd.read_csv(
    "../laptop_all.csv")
print("Chuẩn bị nạp danh sách các từ vô nghĩa (stopwords)...")
sw = load_stopwords()
print("Đã nạp xong danh sách các từ vô nghĩa")

print("Chuẩn bị nạp model BERT....")
phobert, tokenizer = load_bert()
print("Đã nạp xong model BERT.")

print("Chuẩn bị load dữ liệu....")
text = load_data()
print("Đã load dữ liệu xong")

print("Chuẩn bị tạo features từ BERT.....")
features = make_bert_features(text)
print("Đã tạo xong features từ BERT")

ds['vector'] = features
ds.to_csv("")

# import numpy as np
# from scipy import sparse
# from sklearn.metrics.pairwise import cosine_similarity
# from sklearn.metrics.pairwise import linear_kernel
# cosine_similarities = linear_kernel(features, features)
#
# results = {}
#
# for idx, row in ds.iterrows():
#     similar_indices = cosine_similarities[idx].argsort()[:-100:-1]
#     similar_items = [(cosine_similarities[idx][i], ds['code'][i]) for i in similar_indices]
#     results[row['code']] = similar_items[1:]
#
# def getRelevantItems(itemCode):
#     print(ds[ds["code"] == itemCode].iloc[0]["full_name"])
#
#     recs = results[itemCode][:8]
#     for rec in recs:
#         # print("Recommended: " + str(int(rec[1])) + " (score:" + str(rec[0]) + ")")
#         print(ds[ds["code"] == rec[1]].iloc[0]["full_name"])
#         print("rec = ", rec[1])
#
# getRelevantItems(220042001424)