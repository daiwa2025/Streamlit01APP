# import streamlit as st
# import pandas as pd
# import sqlite3
# import os
# from datetime import datetime, timezone, timedelta
# import re
# import jpholiday

# def get_last_business_day(year, month):
#     last_day = pd.Timestamp(year=year, month=month, day=1) + pd.offsets.MonthEnd(0)
#     while last_day.weekday() >= 5 or jpholiday.is_holiday(last_day.date()):
#         last_day -= pd.Timedelta(days=1)
#     return last_day.date()

# today = datetime.now()
# if today.month == 1:
#     last_year = today.year - 1
#     last_month = 12
# else:
#     last_year = today.year
#     last_month = today.month - 1

# default_base_date = get_last_business_day(last_year, last_month).strftime('%Y%m%d')
# SAVE_DIRECTORY_WORK = r"C:\Users\Seigo\Documents\作業用"
# os.makedirs(SAVE_DIRECTORY_WORK, exist_ok=True)

# def convert_name_cut_date(filename):
#     base = filename.rsplit('.', 1)[0]
#     # 全角スラッシュに統一
#     base = base.replace('/', '／')
#     match = re.match(r'^(.*?)[_\-\s]?(\d{8})(.*)$', base)
#     if match:
#         before_date = match.group(1).rstrip('_- ')
#         return before_date
#     else:
#         return base


# conn = sqlite3.connect('filemap.db', check_same_thread=False)
# c = conn.cursor()

# # テーブル設計統一

# c.execute('''
#     CREATE TABLE IF NOT EXISTS monthly_report_map (
#         original_name TEXT,
#         converted_name TEXT,
#         code TEXT
#     )
# ''')
# c.execute('''
#     CREATE TABLE IF NOT EXISTS risk_asset_map (
#         original_name TEXT,
#         converted_name TEXT,
#         code TEXT
#     )
# ''')
# conn.commit()

# jst = timezone(timedelta(hours=9))
# if 'df' not in st.session_state:
#     st.session_state.df = pd.DataFrame(columns=[
#         '元のファイル名', '新ファイル名', '銘柄コード','ファンド名', '更新日', '作業者', '基準日', '【月次報告書】', '【リスクアセット表】'
#     ])

# # ========== DBアップロード・手動追加ページ ==========
# def mapping_table_page(conn, c, table_name, table_jp_name, file_type):
#     st.markdown(f"### {table_jp_name}のアップロード（CSV）と手動追加")
#     file_label = f"{table_jp_name}（CSV: 元のファイル名, 銘柄コード）"
#     db_file = st.file_uploader(file_label, type=['csv'], key=f'db_uploader_{table_name}')
#     db = None
#     if db_file is not None:
#         try:
#             db = pd.read_csv(db_file, encoding='utf-8', sep='\t', dtype={'銘柄コード': str})
#             db.columns = db.columns.str.strip()
#             db['converted_name'] = db['元のファイル名'].apply(convert_name_cut_date)
#         except UnicodeDecodeError:
#             db = pd.read_csv(db_file, encoding='cp932')
#         except pd.errors.EmptyDataError:
#             st.error("CSVファイルに列名（ヘッダー）がありません。1行目を「元のファイル名,銘柄コード」にしてください。")
#             db = None

#     if db is not None:
#         st.dataframe(db[['元のファイル名', 'converted_name', '銘柄コード']])
#         st.write(f"CSV列名: {db.columns.tolist()}")
#     elif db_file is not None:
#         st.write("CSVファイルの読み込みに失敗しました。ファイル形式・ヘッダー行を確認してください。")

#     if db is not None:
#         # ★ ここで拡張子チェックを追加！
#         if table_name == "monthly_report_map":
#             # .pdfのみ
#             invalid_ext = ~db['元のファイル名'].str.lower().str.endswith('.pdf')
#             if invalid_ext.any():
#                 st.error("マンスリーレポートDBには.pdfファイルのみ登録可能です。以下の行のファイル名に誤りがあります。")
#                 st.dataframe(db[invalid_ext])
#                 db = db[~invalid_ext]
#         elif table_name == "risk_asset_map":
#             # .xlsxのみ
#             invalid_ext = ~db['元のファイル名'].str.lower().str.endswith('.xlsx')
#             if invalid_ext.any():
#                 st.error("リスクアセット表DBには.xlsxファイルのみ登録可能です。以下の行のファイル名に誤りがあります。")
#                 st.dataframe(db[invalid_ext])
#                 db = db[~invalid_ext]

#         # ↓拡張子チェック後にDataFrame表示など
#         st.dataframe(db[['元のファイル名', 'converted_name', '銘柄コード']])
#         st.write(f"CSV列名: {db.columns.tolist()}")
#     elif db_file is not None:
#         st.write("CSVファイルの読み込みに失敗しました。ファイル形式・ヘッダー行を確認してください。")


#     if st.button("対照表をDBに保存", key=f'save_{table_name}'):
#         if db_file is None or db is None:
#             st.error("ファイルを選択してください。")
#         else:
#             duplicated = False
#             for idx, row in db.iterrows():
#                 c.execute(f'SELECT COUNT(*) FROM {table_name} WHERE original_name = ?', (row['元のファイル名'],))
#                 if c.fetchone()[0] > 0:
#                     st.error(f"「{row['元のファイル名']}」はすでにDBに登録されています。スキップします。")
#                     duplicated = True
#                     continue
#                 c.execute(
#                     f'INSERT INTO {table_name} (original_name, converted_name, code) VALUES (?, ?, ?)',
#                     (row['元のファイル名'], row['converted_name'], row['銘柄コード'])
#                 )
#             conn.commit()
#             if not duplicated:
#                 st.success("対照表をDBに保存しました")

#     if f'confirm_delete_{table_name}' not in st.session_state:
#         st.session_state[f'confirm_delete_{table_name}'] = False

#     with st.expander("⚠️ DBの内容を全削除したい場合はこちら（危険操作）", expanded=False):
#         st.warning("この操作はDBの内容をすべて削除します。元に戻せません。")

#         if not st.session_state[f'confirm_delete_{table_name}']:
#             if st.button("DBの内容を全削除", key=f'reset_{table_name}', type="primary"):
#                 st.session_state[f'confirm_delete_{table_name}'] = True
#         else:
#             st.error("本当に削除しますか？この操作は取り消せません。")
#             col1, col2 = st.columns(2)
#             with col1:
#                 if st.button("はい、削除します", key=f'final_delete_{table_name}'):
#                     c.execute(f"DELETE FROM {table_name}")
#                     conn.commit()
#                     st.success("DBの内容を全て削除しました。")
#                     st.session_state[f'confirm_delete_{table_name}'] = False
#             with col2:
#                 if st.button("キャンセル", key=f'cancel_delete_{table_name}'):
#                     st.session_state[f'confirm_delete_{table_name}'] = False

#     if table_name == "risk_asset_map":
#         ori_hint = "例：2486_仏国債2年バイホールド2306(H無／適_20230630.xlsx"
#         new_hint = "例：0005"
#     else:
#         ori_hint = "例：M2486-20230731.pdf"
#         new_hint = "例：0005"
#     with st.form(f"manual_input_form_{table_name}"):
#         manual_original = st.text_input("元のファイル名", placeholder=ori_hint, key=f'manual_original_{table_name}')
#         manual_code = st.text_input("銘柄コード", placeholder=new_hint, key=f'manual_code_{table_name}')
#         submitted = st.form_submit_button("対照表に手動追加")
#     if submitted:
#         if manual_original and manual_code:
#             # 拡張子チェック
#             if (table_name == "monthly_report_map" and not manual_original.lower().endswith('.pdf')):
#                 st.error("マンスリーレポートDBには.pdfファイルのみ登録可能です。ファイル名を確認してください。")
#             elif (table_name == "risk_asset_map" and not manual_original.lower().endswith('.xlsx')):
#                 st.error("リスクアセット表DBには.xlsxファイルのみ登録可能です。ファイル名を確認してください。")
#             else:
#                 c.execute(f'SELECT COUNT(*) FROM {table_name} WHERE original_name = ?', (manual_original,))
#                 if c.fetchone()[0] > 0:
#                     st.error(f"「{manual_original}」はすでにDBに登録されています。")
#                 else:
#                     c.execute(
#                         f'INSERT INTO {table_name} (original_name, converted_name, code) VALUES (?, ?, ?)',
#                         (manual_original, convert_name_cut_date(manual_original), manual_code)
#                     )
#                     conn.commit()
#                     st.success(f"追加: {manual_original} → {manual_code}")
#         else:
#             st.error("「元のファイル名」と「銘柄コード」は必須です。")


#     df_map = pd.read_sql(f'SELECT * FROM {table_name}', conn)
#     st.write(f"DB内の対照表（{table_jp_name}）：")
#     st.dataframe(df_map)




# # ========== ファイル更新ページ ==========
# def update_files_page(conn, c, worker, base_date):
#     st.header("ファイル更新")
#     st.write('複数ファイル（PDFまたはExcel）をアップロードしてください:')
#     uploaded_files = st.file_uploader("ファイルをアップロード", type=["pdf", "xlsx"], accept_multiple_files=True, key='file_uploader')
#     if st.button('アップロード実行', key='upload_button'):
#         if not base_date or not base_date.isdigit() or len(base_date) != 8:
#             st.error('基準日はYYYYMMDD形式で入力してください！')
#         elif not uploaded_files:
#             st.error("ファイルを選択してください。")
#         else:
#             for uploaded_file in uploaded_files:
#                 original_file_name = uploaded_file.name
#                 ext = os.path.splitext(original_file_name)[1].lower()
#                 converted_name = convert_name_cut_date(original_file_name)

#                 # ファイルの種類によってDBを選択する
#                 if ext == ".pdf":
#                     df_map = pd.read_sql('SELECT * FROM monthly_report_map', conn)
#                 elif ext == ".xlsx":
#                     df_map = pd.read_sql('SELECT * FROM risk_asset_map', conn)
#                 else:
#                     st.warning(f"未対応のファイル形式: {ext}")
#                     continue

#                 row = df_map[df_map["converted_name"] == converted_name]
#                 if row.empty:
#                     st.warning(f"対照表に {converted_name} のエントリがありません。スキップします。")
#                     continue
#                 code = row.iloc[0]["code"]
#                 try:
#                     if ext == ".pdf":
#                         new_file_name = f"A-{code}-20-{base_date}.pdf"
#                         save_path = os.path.join(SAVE_DIRECTORY_WORK, new_file_name)
#                         with open(save_path, "wb") as f:
#                             f.write(uploaded_file.getbuffer())
#                         current_time = datetime.now(jst).strftime('%Y-%m-%d %H:%M:%S')
#                         new_row = pd.DataFrame({
#                             '元のファイル名': [original_file_name],
#                             '新ファイル名': [new_file_name],
#                             '銘柄コード': [code],
#                             '更新日': [current_time],
#                             '作業者': [worker],
#                             '基準日': [base_date],
#                             '【月次報告書】': [new_file_name],
#                             '【リスクアセット表】': [None]
#                         })
#                         st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
#                         st.success(f"保存完了: {new_file_name}")
#                         st.info(f"API経由でアクセス可: http://127.0.0.1:8000/api/files/{new_file_name}")
#                     elif ext == ".xlsx":
#                         new_file_name = f"A-{code}-50-{base_date}.xlsx"
#                         save_path = os.path.join(SAVE_DIRECTORY_WORK, new_file_name)
#                         with open(save_path, "wb") as f:
#                             f.write(uploaded_file.getbuffer())
#                         current_time = datetime.now(jst).strftime('%Y-%m-%d %H:%M:%S')
#                         new_row = pd.DataFrame({
#                             '元のファイル名': [original_file_name],
#                             '新ファイル名': [new_file_name],
#                             '銘柄コード': [code],
#                             '更新日': [current_time],
#                             '作業者': [worker],
#                             '基準日': [base_date],
#                             '【月次報告書】': [None],
#                             '【リスクアセット表】': [new_file_name]
#                         })
#                         st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
#                         st.success(f"保存完了: {new_file_name}")
#                         st.info(f"API経由でアクセス可: http://127.0.0.1:8000/api/files/{new_file_name}")
#                 except Exception as e:
#                     st.error(f"ファイル処理エラー: {original_file_name}, 詳細: {e}")



# FUND_LIST_FILE = r"C:\Users\Seigo\Documents\作業用\fund_list.json"

# # セッション状態でDataFrame初期化
# if 'df' not in st.session_state:
#     if os.path.exists(FUND_LIST_FILE):
#         st.session_state.df = pd.read_json(FUND_LIST_FILE)
#     else:
#         st.session_state.df = pd.DataFrame(columns=["銘柄コード", "ファンド名"])

# def register_new_fund_page():
#     register_new_fund_page(worker, base_date)
#     st.header('新規ファンドの登録')
#     new_code = st.text_input('銘柄コード', key='new_code_input')
#     new_name = st.text_input('ファンド名', key='new_name_input')
#     if st.button('追加', key='add_button'):
#         if new_code and new_name:
#             if not new_code.isdigit():
#                 st.error('銘柄コードは数字で入力してください！')
#             elif (st.session_state.df['銘柄コード'] == new_code).any():
#                 st.error('同じ銘柄コードが既に登録されています！')
#             else:
#                 new_row = pd.DataFrame({
#                     '銘柄コード': [new_code],
#                     'ファンド名': [new_name]
#                 })
#                 st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
#                 # 保存時にカラム名をcode, nameに変換
#                 out_df = st.session_state.df.rename(columns={'銘柄コード': 'code', 'ファンド名': 'name'})
#                 out_df.to_json(FUND_LIST_FILE, orient="records", force_ascii=False)
#                 st.success('新しいファンドが追加されました！')
#         else:
#             st.error('銘柄コード・ファンド名を入力してください！')

#     st.dataframe(st.session_state.df)



# def delete_page(conn, c):
#     st.header("削除機能")
#     st.write("登録データ（ファンドリスト）・DB内対照表のどちらを削除しますか？")
#     delete_mode = st.radio("削除対象を選択", ["ファンドリスト", "DB内対照表"], horizontal=True)
#     if delete_mode == "ファンドリスト":
#         if not st.session_state.df.empty:
#             row_to_delete = st.selectbox(
#                 '削除する行を選択してください（銘柄コード）',
#                 list(st.session_state.df['銘柄コード']),
#                 key='delete_selectbox'
#             )
#             confirm_delete = st.checkbox("削除することを確認しました", key='delete_checkbox')
#             if st.button('削除', key='delete_confirm_button'):
#                 if confirm_delete:
#                     st.session_state.df = st.session_state.df[st.session_state.df['銘柄コード'] != row_to_delete]
#                     st.success(f'銘柄コード {row_to_delete} の行が削除されました！')
#                 else:
#                     st.error("削除前に確認チェックを入れてください。")
#         else:
#             st.warning("現在、削除可能なデータがありません。")
#     elif delete_mode == "DB内対照表":
#         df_map = pd.read_sql('SELECT * FROM monthly_report_map', conn)
#         st.write("DB内対照表一覧：")
#         st.dataframe(df_map)
#         if not df_map.empty:
#             to_delete = st.selectbox(
#                 "削除するエントリを選択してください（元のファイル名）",
#                 df_map['original_name'].tolist(),
#                 key='db_delete_selectbox'
#             )
#             confirm_db_delete = st.checkbox("DB対照表から削除することを確認しました", key='db_delete_checkbox')
#             if st.button("DB対照表から削除", key='db_delete_button'):
#                 if confirm_db_delete:
#                     c.execute("DELETE FROM monthly_report_map WHERE original_name = ?", (to_delete,))
#                     conn.commit()
#                     st.success(f"対照表から「{to_delete}」を削除しました。")
#                     df_map = pd.read_sql('SELECT * FROM monthly_report_map', conn)
#                     st.dataframe(df_map)
#                 else:
#                     st.error("削除前に確認チェックを入れてください。")
#         else:
#             st.info("DB内対照表に削除対象がありません。")

# # ========== サイドバー・メインページ ==========

# default_base_date = get_last_business_day(last_year, last_month).strftime('%Y%m%d')

# st.title('私募投信登録専用サイト')

# worker = st.sidebar.selectbox('作業者を選択してください', ['谷 秀顕', '佐藤 真也', '猪野 幸一','澤辺 良司'])
# base_date = st.sidebar.text_input('基準日を入力してください（YYYYMMDD形式）', value=default_base_date)
# st.sidebar.write(f'選択された作業者: {worker}')
# st.sidebar.write(f'入力された基準日: {base_date}')

# workselect = st.sidebar.selectbox(
#     '作業内容を選んでください',
#     [
#         '銘柄対照表 マンスリーレポートDB',
#         '銘柄対照表 リスクアセット表DB',
#         'ファイル更新',
#         '新規ファンドの登録',
#         '削除',
#     ]
# )

# if workselect == '銘柄対照表 マンスリーレポートDB':
#     mapping_table_page(conn, c, 'monthly_report_map', '銘柄対照表 マンスリーレポートDB', 'csv')
# elif workselect == '銘柄対照表 リスクアセット表DB':
#     mapping_table_page(conn, c, 'risk_asset_map', '銘柄対照表 リスクアセット表DB', 'xlsx')
# elif workselect == 'ファイル更新':
#     update_files_page(conn, c, worker, base_date)
# elif workselect == '新規ファンドの登録':
#     register_new_fund_page(worker, base_date)
# elif workselect == '削除':
#     delete_page(conn, c)

# st.markdown("---")
# st.write("現在のファンドリスト：")
# st.dataframe(st.session_state.df)

import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime, timezone, timedelta
import re
import jpholiday

def get_last_business_day(year, month):
    last_day = pd.Timestamp(year=year, month=month, day=1) + pd.offsets.MonthEnd(0)
    while last_day.weekday() >= 5 or jpholiday.is_holiday(last_day.date()):
        last_day -= pd.Timedelta(days=1)
    return last_day.date()

today = datetime.now()
if today.month == 1:
    last_year = today.year - 1
    last_month = 12
else:
    last_year = today.year
    last_month = today.month - 1

default_base_date = get_last_business_day(last_year, last_month).strftime('%Y%m%d')
SAVE_DIRECTORY_WORK = r"C:\Users\Seigo\Documents\作業用"
os.makedirs(SAVE_DIRECTORY_WORK, exist_ok=True)

def convert_name_cut_date(filename):
    base = filename.rsplit('.', 1)[0]
    base = base.replace('/', '／')
    match = re.match(r'^(.*?)[_\-\s]?(\d{8})(.*)$', base)
    if match:
        before_date = match.group(1).rstrip('_- ')
        return before_date
    else:
        return base

conn = sqlite3.connect('filemap.db', check_same_thread=False)
c = conn.cursor()

c.execute('''
    CREATE TABLE IF NOT EXISTS monthly_report_map (
        original_name TEXT,
        converted_name TEXT,
        code TEXT
    )
''')
c.execute('''
    CREATE TABLE IF NOT EXISTS risk_asset_map (
        original_name TEXT,
        converted_name TEXT,
        code TEXT
    )
''')
conn.commit()

jst = timezone(timedelta(hours=9))

FUND_LIST_FILE = r"C:\Users\Seigo\Documents\作業用\fund_list.json"

# セッション状態でDataFrame初期化（ファンドリスト用）
if 'df_fundlist' not in st.session_state:
    if os.path.exists(FUND_LIST_FILE):
        st.session_state.df_fundlist = pd.read_json(FUND_LIST_FILE)
    else:
        st.session_state.df_fundlist = pd.DataFrame(columns=["銘柄コード", "ファンド名"])

# ========== 新規ファンド登録ページ ==========
def register_new_fund_page(worker, base_date):
    st.header('新規ファンドの登録')
    new_code = st.text_input('銘柄コード', key='new_code_input')
    new_name = st.text_input('ファンド名', key='new_name_input')
    if st.button('追加', key='add_button'):
        if new_code and new_name:
            if not new_code.isdigit():
                st.error('銘柄コードは数字で入力してください！')
            elif (st.session_state.df_fundlist['銘柄コード'] == new_code).any():
                st.error('同じ銘柄コードが既に登録されています！')
            else:
                new_row = pd.DataFrame({
                    '銘柄コード': [new_code],
                    'ファンド名': [new_name]
                })
                st.session_state.df_fundlist = pd.concat([st.session_state.df_fundlist, new_row], ignore_index=True)
                # 保存時にカラム名をcode, nameに変換
                out_df = st.session_state.df_fundlist.rename(columns={'銘柄コード': 'code', 'ファンド名': 'name'})
                out_df.to_json(FUND_LIST_FILE, orient="records", force_ascii=False)
                st.success('新しいファンドが追加されました！')
        else:
            st.error('銘柄コード・ファンド名を入力してください！')
    st.dataframe(st.session_state.df_fundlist)

# ========== DBアップロード・手動追加ページ ==========
def mapping_table_page(conn, c, table_name, table_jp_name, file_type):
    st.markdown(f"### {table_jp_name}のアップロード（CSV）と手動追加")
    file_label = f"{table_jp_name}（CSV: 元のファイル名, 銘柄コード）"
    db_file = st.file_uploader(file_label, type=['csv'], key=f'db_uploader_{table_name}')

    db = None
    error_msg = None

    if db_file is not None:
        # まずUTF-8・カンマ区切りで読み込む
        try:
             db = pd.read_csv(db_file, encoding='utf-8', dtype={'銘柄コード': str})

        except Exception:
            try:
                # 失敗したらUTF-8・タブ区切りで再試行
                db = pd.read_csv(db_file, encoding='utf-8', sep='\t',dtype={'銘柄コード': str})
            except Exception:
                try:
                    # さらにCP932・カンマ区切りで再試行
                    db = pd.read_csv(db_file, encoding='cp932',dtype={'銘柄コード': str})
                except Exception:
                    try:
                        # CP932・タブ区切りでもダメならエラー
                        db = pd.read_csv(db_file, encoding='cp932', sep='\t',dtype={'銘柄コード': str})
                    except Exception:
                        error_msg = "CSVファイルの読み込みに失敗しました。ファイル形式・エンコーディング・区切り文字を確認してください。"

    # 列名を前後の空白を除去して標準化
    if db is not None:
        db.columns = db.columns.str.strip()
        # 必要な列がなければエラー
        if not set(['元のファイル名', '銘柄コード']).issubset(db.columns):
            error_msg = "CSVファイルに必要な列名（元のファイル名, 銘柄コード）がありません。"
            db = None

    if error_msg:
        st.error(error_msg)

    if db is not None:
        # 日付部分を除去した変換名を追加
        db['converted_name'] = db['元のファイル名'].apply(convert_name_cut_date)
        # 拡張子のチェック
        if table_name == "monthly_report_map":
            # PDFのみ許可
            invalid_ext = ~db['元のファイル名'].str.lower().str.endswith('.pdf')
            if invalid_ext.any():
                st.error("マンスリーレポートDBには.pdfファイルのみ登録可能です。以下の行のファイル名に誤りがあります。")
                st.dataframe(db[invalid_ext])
                db = db[~invalid_ext]
        elif table_name == "risk_asset_map":
            # Excelのみ許可
            invalid_ext = ~db['元のファイル名'].str.lower().str.endswith('.xlsx')
            if invalid_ext.any():
                st.error("リスクアセット表DBには.xlsxファイルのみ登録可能です。以下の行のファイル名に誤りがあります。")
                st.dataframe(db[invalid_ext])
                db = db[~invalid_ext]
        # 最終的なデータフレームを表示
        st.dataframe(db[['元のファイル名', 'converted_name', '銘柄コード']])




    if st.button("対照表をDBに保存", key=f'save_{table_name}'):
        if db_file is None or db is None:
            st.error("ファイルを選択してください。")
        else:
            duplicated = False
            for idx, row in db.iterrows():
                c.execute(f'SELECT COUNT(*) FROM {table_name} WHERE original_name = ?', (row['元のファイル名'],))
                if c.fetchone()[0] > 0:
                    st.error(f"「{row['元のファイル名']}」はすでにDBに登録されています。スキップします。")
                    duplicated = True
                    continue
                c.execute(
                    f'INSERT INTO {table_name} (original_name, converted_name, code) VALUES (?, ?, ?)',
                    (row['元のファイル名'], row['converted_name'], row['銘柄コード'])
                )
            conn.commit()
            if not duplicated:
                st.success("対照表をDBに保存しました")

    if f'confirm_delete_{table_name}' not in st.session_state:
        st.session_state[f'confirm_delete_{table_name}'] = False

    with st.expander("⚠️ DBの内容を全削除したい場合はこちら（危険操作）", expanded=False):
        st.warning("この操作はDBの内容をすべて削除します。元に戻せません。")

        if not st.session_state[f'confirm_delete_{table_name}']:
            if st.button("DBの内容を全削除", key=f'reset_{table_name}', type="primary"):
                st.session_state[f'confirm_delete_{table_name}'] = True
        else:
            st.error("本当に削除しますか？この操作は取り消せません。")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("はい、削除します", key=f'final_delete_{table_name}'):
                    c.execute(f"DELETE FROM {table_name}")
                    conn.commit()
                    st.success("DBの内容を全て削除しました。")
                    st.session_state[f'confirm_delete_{table_name}'] = False
            with col2:
                if st.button("キャンセル", key=f'cancel_delete_{table_name}'):
                    st.session_state[f'confirm_delete_{table_name}'] = False

    if table_name == "risk_asset_map":
        ori_hint = "例：2486_仏国債2年バイホールド2306(H無／適_20230630.xlsx"
        new_hint = "例：0005"
    else:
        ori_hint = "例：M2486-20230731.pdf"
        new_hint = "例：0005"
    with st.form(f"manual_input_form_{table_name}"):
        manual_original = st.text_input("元のファイル名", placeholder=ori_hint, key=f'manual_original_{table_name}')
        manual_code = st.text_input("銘柄コード", placeholder=new_hint, key=f'manual_code_{table_name}')
        submitted = st.form_submit_button("対照表に手動追加")
    if submitted:
        if manual_original and manual_code:
            # 拡張子チェック
            if (table_name == "monthly_report_map" and not manual_original.lower().endswith('.pdf')):
                st.error("マンスリーレポートDBには.pdfファイルのみ登録可能です。ファイル名を確認してください。")
            elif (table_name == "risk_asset_map" and not manual_original.lower().endswith('.xlsx')):
                st.error("リスクアセット表DBには.xlsxファイルのみ登録可能です。ファイル名を確認してください。")
            else:
                c.execute(f'SELECT COUNT(*) FROM {table_name} WHERE original_name = ?', (manual_original,))
                if c.fetchone()[0] > 0:
                    st.error(f"「{manual_original}」はすでにDBに登録されています。")
                else:
                    c.execute(
                        f'INSERT INTO {table_name} (original_name, converted_name, code) VALUES (?, ?, ?)',
                        (manual_original, convert_name_cut_date(manual_original), manual_code)
                    )
                    conn.commit()
                    st.success(f"追加: {manual_original} → {manual_code}")
        else:
            st.error("「元のファイル名」と「銘柄コード」は必須です。")

    df_map = pd.read_sql(f'SELECT * FROM {table_name}', conn)
    st.write(f"DB内の対照表（{table_jp_name}）：")
    st.dataframe(df_map)

# ========== ファイル更新ページ ==========
def update_files_page(conn, c, worker, base_date):
    st.header("ファイル更新")
    st.write('複数ファイル（PDFまたはExcel）をアップロードしてください:')
    uploaded_files = st.file_uploader("ファイルをアップロード", type=["pdf", "xlsx"], accept_multiple_files=True, key='file_uploader')
    if st.button('アップロード実行', key='upload_button'):
        if not base_date or not base_date.isdigit() or len(base_date) != 8:
            st.error('基準日はYYYYMMDD形式で入力してください！')
        elif not uploaded_files:
            st.error("ファイルを選択してください。")
        else:
            for uploaded_file in uploaded_files:
                original_file_name = uploaded_file.name
                ext = os.path.splitext(original_file_name)[1].lower()
                converted_name = convert_name_cut_date(original_file_name)

                # ファイルの種類によってDBを選択する
                if ext == ".pdf":
                    df_map = pd.read_sql('SELECT * FROM monthly_report_map', conn)
                elif ext == ".xlsx":
                    df_map = pd.read_sql('SELECT * FROM risk_asset_map', conn)
                else:
                    st.warning(f"未対応のファイル形式: {ext}")
                    continue

                row = df_map[df_map["converted_name"] == converted_name]
                if row.empty:
                    st.warning(f"対照表に {converted_name} のエントリがありません。スキップします。")
                    continue
                code = row.iloc[0]["code"]
                try:
                    if ext == ".pdf":
                        new_file_name = f"A-{code}-20-{base_date}.pdf"
                        save_path = os.path.join(SAVE_DIRECTORY_WORK, new_file_name)
                        with open(save_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        current_time = datetime.now(jst).strftime('%Y-%m-%d %H:%M:%S')
                        # 必要に応じてst.session_state.dfなどに履歴追加
                        st.success(f"保存完了: {new_file_name}")
                        st.info(f"API経由でアクセス可: http://127.0.0.1:8000/api/files/{new_file_name}")
                    elif ext == ".xlsx":
                        new_file_name = f"A-{code}-50-{base_date}.xlsx"
                        save_path = os.path.join(SAVE_DIRECTORY_WORK, new_file_name)
                        with open(save_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        current_time = datetime.now(jst).strftime('%Y-%m-%d %H:%M:%S')
                        # 必要に応じてst.session_state.dfなどに履歴追加
                        st.success(f"保存完了: {new_file_name}")
                        st.info(f"API経由でアクセス可: http://127.0.0.1:8000/api/files/{new_file_name}")
                except Exception as e:
                    st.error(f"ファイル処理エラー: {original_file_name}, 詳細: {e}")

# ========== 削除ページ ==========
def delete_page(conn, c):
    st.header("削除機能")
    st.write("登録データ（ファンドリスト）・DB内対照表のどちらを削除しますか？")
    delete_mode = st.radio("削除対象を選択", ["ファンドリスト", "DB内対照表"], horizontal=True)
    if delete_mode == "ファンドリスト":
        if not st.session_state.df_fundlist.empty:
            row_to_delete = st.selectbox(
                '削除する行を選択してください（銘柄コード）',
                list(st.session_state.df_fundlist['銘柄コード']),
                key='delete_selectbox'
            )
            confirm_delete = st.checkbox("削除することを確認しました", key='delete_checkbox')
            if st.button('削除', key='delete_confirm_button'):
                if confirm_delete:
                    st.session_state.df_fundlist = st.session_state.df_fundlist[st.session_state.df_fundlist['銘柄コード'] != row_to_delete]
                    # 保存も忘れずに
                    out_df = st.session_state.df_fundlist.rename(columns={'銘柄コード': 'code', 'ファンド名': 'name'})
                    out_df.to_json(FUND_LIST_FILE, orient="records", force_ascii=False)
                    st.success(f'銘柄コード {row_to_delete} の行が削除されました！')
                else:
                    st.error("削除前に確認チェックを入れてください。")
        else:
            st.warning("現在、削除可能なデータがありません。")
    elif delete_mode == "DB内対照表":
        df_map = pd.read_sql('SELECT * FROM monthly_report_map', conn)
        st.write("DB内対照表一覧：")
        st.dataframe(df_map)
        if not df_map.empty:
            to_delete = st.selectbox(
                "削除するエントリを選択してください（元のファイル名）",
                df_map['original_name'].tolist(),
                key='db_delete_selectbox'
            )
            confirm_db_delete = st.checkbox("DB対照表から削除することを確認しました", key='db_delete_checkbox')
            if st.button("DB対照表から削除", key='db_delete_button'):
                if confirm_db_delete:
                    c.execute("DELETE FROM monthly_report_map WHERE original_name = ?", (to_delete,))
                    conn.commit()
                    st.success(f"対照表から「{to_delete}」を削除しました。")
                    df_map = pd.read_sql('SELECT * FROM monthly_report_map', conn)
                    st.dataframe(df_map)
                else:
                    st.error("削除前に確認チェックを入れてください。")
        else:
            st.info("DB内対照表に削除対象がありません。")

# ========== サイドバー・メインページ ==========
default_base_date = get_last_business_day(last_year, last_month).strftime('%Y%m%d')

st.title('私募投信登録専用アプリ')

worker = st.sidebar.selectbox('作業者を選択してください', ['谷 秀顕', '佐藤 真也', '猪野 幸一','澤辺 良司'])
base_date = st.sidebar.text_input('基準日を入力してください（YYYYMMDD形式）', value=default_base_date)
st.sidebar.write(f'選択された作業者: {worker}')
st.sidebar.write(f'入力された基準日: {base_date}')

workselect = st.sidebar.selectbox(
    '作業内容を選んでください',
    [
        '銘柄対照表 マンスリーレポートDB',
        '銘柄対照表 リスクアセット表DB',
        'ファイル更新',
        '新規ファンドの登録',
        '削除',
    ]
)

if workselect == '銘柄対照表 マンスリーレポートDB':
    mapping_table_page(conn, c, 'monthly_report_map', '銘柄対照表 マンスリーレポートDB', 'csv')
elif workselect == '銘柄対照表 リスクアセット表DB':
    mapping_table_page(conn, c, 'risk_asset_map', '銘柄対照表 リスクアセット表DB', 'xlsx')
elif workselect == 'ファイル更新':
    update_files_page(conn, c, worker, base_date)
elif workselect == '新規ファンドの登録':
    register_new_fund_page(worker, base_date)
elif workselect == '削除':
    delete_page(conn, c)

st.markdown("---")
st.write("現在のファンドリスト：")
st.dataframe(st.session_state.df_fundlist)
