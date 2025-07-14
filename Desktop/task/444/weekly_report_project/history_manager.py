# history_manager.py
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 注意: 此变量的值将在 backend.py 中被一个绝对路径所覆盖，
# 这使得此模块的行为在任何运行环境下都保持一致。
HISTORY_FILE = 'processing_history.csv'

def _get_week_range(reference_date):
    start_of_week = reference_date - timedelta(days=reference_date.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    return datetime.combine(start_of_week, datetime.min.time()), datetime.combine(end_of_week, datetime.max.time())

def _aggregate_weekly_data(df):
    if df is None or df.empty:
        return pd.DataFrame()
    
    summary = df.groupby('区域').agg(
        区域内经理数=('区域内经理数', 'max'),
        总订单数=('总订单数', 'sum'),
        总交货数=('总交货数', 'sum')
    ).reset_index()

    summary['覆盖率'] = (summary['总交货数'] / summary['总订单数']).replace(np.inf, 0).fillna(0)
    summary['覆盖率'] = summary['覆盖率'].map('{:.2%}'.format)
    
    return summary[['区域', '区域内经理数', '总订单数', '总交货数', '覆盖率']]

def get_weekly_summary(week_type='this_week'):
    if not os.path.exists(HISTORY_FILE):
        return pd.DataFrame()

    try:
        df_history = pd.read_csv(HISTORY_FILE, parse_dates=['处理时间'])
        if df_history.empty:
            return pd.DataFrame()

        today = datetime.now()
        if week_type == 'this_week':
            start_date, end_date = _get_week_range(today)
        elif week_type == 'last_week':
            last_week_ref_date = today - timedelta(weeks=1)
            start_date, end_date = _get_week_range(last_week_ref_date)
        else:
            return pd.DataFrame()

        df_week = df_history[(df_history['处理时间'] >= start_date) & (df_history['处理时间'] <= end_date)]
        return _aggregate_weekly_data(df_week)

    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame()

def save_result(df):
    try:
        if df is None or df.empty:
            return

        df_to_save = df.copy()
        df_to_save['处理时间'] = datetime.now()
        
        # 兼容 numpy 2.0.0 的 to_pydaetime() 弃用
        if hasattr(pd.Series, 'to_pydatetime'):
            df_to_save['处理时间'] = df_to_save['处理时间'].dt.to_pydatetime()

        header = not os.path.exists(HISTORY_FILE)
        cols_order = ['区域', '区域内经理数', '总订单数', '总交货数', '覆盖率', '处理时间']
        df_to_save = df_to_save.reindex(columns=cols_order)

        df_to_save.to_csv(HISTORY_FILE, mode='a', header=header, index=False, encoding='utf-8-sig')
    
    except Exception as e:
        raise IOError(f"保存历史记录到 {HISTORY_FILE} 时失败: {e}") from e

def get_available_months():
    if not os.path.exists(HISTORY_FILE): return []
    try:
        df = pd.read_csv(HISTORY_FILE, usecols=['处理时间'], parse_dates=['处理时间'])
        if df.empty: return []
        months = df['处理时间'].dt.strftime('%Y-%m').unique().tolist()
        months.sort(reverse=True)
        return months
    except (FileNotFoundError, pd.errors.EmptyDataError): return []

def load_history_by_month(month_str):
    if not os.path.exists(HISTORY_FILE) or not month_str: return pd.DataFrame()
    try:
        df = pd.read_csv(HISTORY_FILE, parse_dates=['处理时间'])
        df_month = df[df['处理时间'].dt.strftime('%Y-%m') == month_str]
        df_month['处理时间'] = df_month['处理时间'].dt.strftime('%Y-%m-%d %H:%M:%S')
        return df_month
    except (FileNotFoundError, pd.errors.EmptyDataError): return pd.DataFrame()