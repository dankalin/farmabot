import os
from pathlib import Path
import pickle
import numpy as np
import pandas as pd

np.random.seed(42)
DATA_DIR = 'output'
MODEL_DIR = 'model'

def str_to_pandas(*args):
    columns = ['Sex', 'BMI', 'Smg', 'DM', 'AH', 'Age', 'Ht', 'Wt']
    data = [list(args)]
    df = pd.DataFrame(data, columns=columns)
    print(df)
    print(df.dtypes)
    return df


def predict(filename, sex, bmi, smg, dm, ah, age, ht, wt):
    with open('model.pkl', 'rb') as file:
        model = pickle.load(file)
    df = str_to_pandas(sex, bmi, smg, dm, ah, age, ht, wt)
    result = model.predict_proba(df)[:, 1]
    if result > 0.50:
        result += 0.2
    return round(result[0], 3)*100


def save_excel(data):
    filename = str(Path(DATA_DIR) / 'output.xlsx')
    if not os.path.exists(filename):
        # Создать новый файл Excel с заголовками столбцов
        df = pd.DataFrame(
            columns=['Patient Number', 'Sex', 'BMI', 'Smg', 'DM', 'AH', 'Age', 'Ht', 'Wt', 'Prob'])
        df.to_excel(filename, index=False)

    df = pd.read_excel(filename)

    row = {
        'Patient Number': data['Patient Number'],
        'Sex': data['Sex'],
        'BMI': data['BMI'],
        'Smg': data['Smg'],
        'DM': data['DM'],
        'AH': data['AH'],
        'Age': data['Age'],
        'Ht': data['Ht'],
        'Wt': data['Wt'],
        'Prob': data['Prob']
    }
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_excel(filename, index=False)


def predict_excel(tg_filename,res_filename,filename_model):
    old_excel = 'output/output.xlsx'
    df = pd.read_excel(tg_filename)
    df_old = pd.read_excel(old_excel)
    df_new = df[['Sex', 'BMI', 'Smg', 'DM', 'AH', 'Age', 'Ht', 'Wt']].astype(float)
    with open('model.pkl', 'rb') as file:
        model = pickle.load(file)
    result = model.predict_proba(df_new)[:, 1]
    df['Prob'] = result * 100
    df.loc[df['Prob'] > 58, 'Prob'] += 10
    df.loc[df['Prob'] < 42, 'Prob'] -= 10
    df.to_excel(res_filename)
    df_old = pd.concat([df, df_old], ignore_index=True)
    df_old.to_excel(old_excel, index=False)
