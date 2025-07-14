# backend.py
import os
import uuid
import threading
import traceback
from flask import Flask, request, jsonify, abort, send_from_directory
from werkzeug.utils import secure_filename
import pandas as pd
import numpy as np

import history_manager

# --- 配置和数据处理逻辑 (不变) ---
CONFIG = {
    'sales_order': {'file_prefix': 'SZJ-销售订单', 'sheet_name': 'SZJ-销售订单', 'columns': ['采购订单编号', '订单数量_总和', '实际交货数量_总和']},
    'multi_price': {'file_prefix': '多形态价格', 'sheet_name': '数据源', 'columns': ['采购订单编号', '客户名称']},
    'manager_map': {'file_prefix': '区域经理覆盖情况跟进表', 'sheet_name': '区域经理对照表', 'columns': ['客户名称', '新任大区经理', '区域']}
}

def process_data_logic(file_paths):
    try:
        read_engine = 'calamine'
        df_sales = pd.read_excel(file_paths['sales_order'], sheet_name=CONFIG['sales_order']['sheet_name'], usecols=CONFIG['sales_order']['columns'], engine=read_engine)
        df_price = pd.read_excel(file_paths['multi_price'], sheet_name=CONFIG['multi_price']['sheet_name'], usecols=CONFIG['multi_price']['columns'], engine=read_engine)
        df_manager = pd.read_excel(file_paths['manager_map'], sheet_name=CONFIG['manager_map']['sheet_name'], usecols=CONFIG['manager_map']['columns'], engine=read_engine)
        df_merged1 = pd.merge(df_sales, df_price.drop_duplicates(subset=['采购订单编号']), on='采购订单编号', how='left')
        df_final_raw = pd.merge(df_merged1, df_manager.drop_duplicates(subset=['客户名称']), on='客户名称', how='left')
        fill_values = {'新任大区经理': '未分配', '区域': '未分配'}
        df_final_raw.fillna(value=fill_values, inplace=True)
        df_agg_by_manager = df_final_raw.groupby(['区域', '新任大区经理']).agg({'订单数量_总和': 'sum', '实际交货数量_总和': 'sum'}).reset_index()
        df_final = df_agg_by_manager.groupby('区域').agg(区域内经理数=('新任大区经理', 'nunique'), 订单数量_总和=('订单数量_总和', 'sum'), 实际交货数量_总和=('实际交货数量_总和', 'sum')).reset_index()
        df_final['覆盖率'] = (df_final['实际交货数量_总和'] / df_final['订单数量_总和']).replace(np.inf, 0).fillna(0)
        df_final['覆盖率'] = df_final['覆盖率'].map('{:.2%}'.format)
        df_final.rename(columns={'订单数量_总和': '总订单数', '实际交货数量_总和': '总交货数'}, inplace=True)
        df_final = df_final[['区域', '区域内经理数', '总订单数', '总交货数', '覆盖率']]
        return df_final
    except Exception as e:
        error_info = traceback.format_exc()
        print(f"ERROR during data processing: {error_info}")
        raise RuntimeError(f"处理数据时发生错误: {e}") from e

# --- Flask App 设置 (健壮的路径配置) ---
basedir = os.path.abspath(os.path.dirname(__file__))

UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
# 动态修改 history_manager 模块的全局变量，使其也使用绝对路径
history_manager.HISTORY_FILE = os.path.join(basedir, 'processing_history.csv')

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

JOBS = {}
app = Flask(__name__, static_folder=os.path.join(basedir, 'static'))


# --- 异步任务 (不变) ---
def run_processing_task(job_id, file_paths):
    try:
        df_result = process_data_logic(file_paths)
        JOBS[job_id]['status'] = 'completed'
        JOBS[job_id]['result'] = df_result.to_json(orient='split')
    except Exception as e:
        JOBS[job_id]['status'] = 'failed'
        JOBS[job_id]['error'] = str(e)
    finally:
        for path in file_paths.values():
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError as e:
                    print(f"Error removing file {path}: {e}")


# --- API Endpoints ---
@app.route('/api/process', methods=['POST'])
def start_processing_endpoint():
    if not all(k in request.files for k in ['sales_order', 'multi_price', 'manager_map']):
        return jsonify({"error": "缺少必需的文件"}), 400

    job_id = str(uuid.uuid4())
    file_paths = {}
    try:
        for key in ['sales_order', 'multi_price', 'manager_map']:
            file = request.files[key]
            filename = secure_filename(f"{job_id}_{file.filename}")
            path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(path)
            file_paths[key] = path

        JOBS[job_id] = {'status': 'processing', 'result': None, 'error': None}
        thread = threading.Thread(target=run_processing_task, args=(job_id, file_paths))
        thread.start()
        return jsonify({"message": "处理任务已启动", "job_id": job_id})
    except Exception as e:
        # 清理已创建的文件
        for path in file_paths.values():
            if os.path.exists(path): os.remove(path)
        return jsonify({"error": f"启动任务失败: {e}"}), 500


@app.route('/api/status/<job_id>', methods=['GET'])
def get_status_endpoint(job_id):
    job = JOBS.get(job_id)
    if not job: abort(404, description="Job not found")
    return jsonify(job)


@app.route('/api/save', methods=['POST'])
def save_result_endpoint():
    data = request.json
    if not data or 'data' not in data or 'columns' not in data:
        return jsonify({"error": "没有提供有效的数据"}), 400
    try:
        df_to_save = pd.DataFrame(data['data'], columns=data['columns'])
        history_manager.save_result(df_to_save)
        return jsonify({"message": "结果保存成功"})
    except Exception as e:
        print(f"Save error: {traceback.format_exc()}")
        return jsonify({"error": f"保存失败: {e}"}), 500


@app.route('/api/summary', methods=['GET'])
def get_summary_endpoint():
    week_type = request.args.get('week', 'this_week')
    df = history_manager.get_weekly_summary(week_type)
    return jsonify(df.to_json(orient='split') if not df.empty else {'data': [], 'columns': [], 'index': []})


@app.route('/api/history/months', methods=['GET'])
def get_history_months_endpoint():
    months = history_manager.get_available_months()
    return jsonify(months)


@app.route('/api/history/data', methods=['GET'])
def get_history_data_endpoint():
    month = request.args.get('month')
    if not month: return jsonify({"error": "需要提供月份参数"}), 400
    df = history_manager.load_history_by_month(month)
    return jsonify(df.to_json(orient='split') if not df.empty else {'data': [], 'columns': [], 'index': []})


# --- 服务前端页面 (不变) ---
@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')


# 此部分仅用于本地开发测试 (例如配合 Ngrok)，Gunicorn 会忽略它
if __name__ == '__main__':
    # 可以在本地测试时开启 debug，但在提交代码到生产服务器前最好设为 False
    app.run(host='127.0.0.1', port=5000, debug=True)