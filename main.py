#!/usr/bin/env python3

import streamlit as st
import pandas as pd
from datetime import datetime
import io
import openpyxl

def output_file(data):
	output = io.BytesIO()
	writer = pd.ExcelWriter(output, engine='xlsxwriter')
	data.to_excel(writer)
	writer.save()
	return output

def is_chinese(string):
	"""
	检查整个字符串是否包含中文
	:param string: 需要检查的字符串
	:return: bool
	"""
	for ch in string:
		if u'\u4e00' <= ch <= u'\u9fa5':
			return True
		
	return False

def time_convert(s):
	year = datetime.now().year
	s = s.replace("月", "-")
	s = s.replace("日", "")
	s = f"{year}-{s}:00"
	return s

def last_month(now):
	out_month = now.month
	out_year = now.year
	if now.month == 1:
		out_month = 12
		out_year -= 1
	else:
		out_month -= 1
	return out_year, out_month

def plot_fig(cls, data):
	fig_df = pd.DataFrame(columns=["问题数量"])
	for item in cls:
		fig_df.loc[item] = len(data[data["问题类型"]==item])
	st.bar_chart(fig_df)
	
def time_start_end(year, month):
	start = datetime(year, month, 1)
	if month == 12:
		end = datetime(year+1, 1, 1)
	else:
		end = datetime(year, month+1, 1)
	return start, end

class InClient(object):
	columns = ["反馈时间", "用户UID", "用户昵称", "问题类型", "具体问题", "问题详情", "图片", "客户端", "手机系统版本", "手机型号", "设备ID", "联系方式", "问题是否解决/第一次登陆", "最后一次登陆"]
	def __init__(self, in_client_files, year, month):
		data_ls = []
		for file in in_client_files:
			data = pd.read_excel(file, usecols=range(14))
			# 重命名表头
			data.columns = self.columns
			# 剔除空数据
			data.dropna(axis=1, how='all', inplace=True)
			# 剔除其他月份
			data["反馈时间"] = data['反馈时间'].astype("datetime64[ns]")
			data = data[(data["反馈时间"] > time_start_end(year, month)[0]) & (data["反馈时间"] < time_start_end(year, month)[1])]
			time_start = time_start_end(year, month)[0]
			time_end = time_start_end(year, month)[1]
			#data = data.query("反馈时间 > time_start and 反馈时间 < time_end")
			data_ls.append(data)
		data_in = pd.concat(data_ls, ignore_index=True)
		data_in = data_in.sort_values(by=["反馈时间"]).reset_index(drop=True)
		self.data_in = data_in.astype('str')
		
	def drop_duplicate(self):
		dup = len(self.data_in) - len(self.data_in.drop_duplicates(subset=["设备ID", "问题类型", "具体问题"]).drop_duplicates(subset=["用户UID", "问题类型", "具体问题"]))
		self.data_in = self.data_in.drop_duplicates(subset=["设备ID", "问题类型", "具体问题"]).drop_duplicates(subset=["用户UID", "问题类型", "具体问题"])
		self.data_in.reset_index(inplace=True, drop=True)
		return dup
	
	def drop_activity(self, selected_cls):
		activity = len(self.data_in) - len(self.data_in[~self.data_in["问题类型"].isin(selected_cls)])
		self.data_in = self.data_in[~self.data_in["问题类型"].isin(selected_cls)]
		self.data_in.reset_index(inplace=True, drop=True)
		return activity
	
	def rename_cls(self, rename_str, is_first_cls):
		rename_groups = rename_str.split('\n')
		for rename_group in rename_groups:
			before = rename_group.split('->')[0]
			after = rename_group.split('->')[1]
			if is_first_cls:
				self.data_in["问题类型"].replace(before, after, inplace=True)
			else:
				self.data_in["具体问题"].replace(before, after, inplace=True)
				
	def transfer_cls(self, transfer_str):
		transfer_groups = transfer_str.split('\n')
		for transfer_group in transfer_groups:
			first = transfer_group.split('->')[0]
			second = transfer_group.split('->')[1]
			# self.data_in.query("问题类型 == '%s'" % first, inplace=True).assign(问题类型=second, 具体问题=first)
			self.data_in.loc[self.data_in["问题类型"]==first, ['问题类型', '具体问题']] = [second, first]
			
	def check_null(self):
		n = 0
		for i in range(len(self.data_in)):
			if self.data_in.loc[i, "问题类型"] == "无效问题" and is_chinese(str(self.data_in.loc[i, "问题详情"])):
				n += 1
				st.markdown(f"> {n}. " + str(self.data_in.loc[i, '问题详情']))
				self.data_in.loc[i, "问题类型"] = st.selectbox("问题类型_" + str(n), self.data_in["问题类型"].unique(), list(self.data_in["问题类型"].unique()).index("无效问题"))
				self.data_in.loc[i, "具体问题"] = st.selectbox("具体问题_" + str(n), self.data_in[self.data_in["问题类型"]==self.data_in.loc[i, "问题类型"]]["具体问题"].unique())
			
class OutClient(object):
	name = ["iOS", "华为", "小米", "OPPO", "VIVO", "魅族", "微博"]
	def __init__(self, out_client_files):
		data_ls = []
		for file in out_client_files:
			if file.name == "微博.xlsx":
				data = pd.read_excel(file)
				data.rename(columns={"反馈日期": "评论时间", "用户昵称": "评论人", "反馈内容": "内容"}, inplace=True)
				data["评论时间"] = data["评论时间"].apply(lambda x: time_convert(x))
				wb = openpyxl.load_workbook(file)
				ws = wb.get_sheet_by_name('Sheet1')
				for i in range(len(data)):
					data.loc[i, "标题"] = ws.cell(row=i+2, column=1).hyperlink.target
			else:
				data = pd.read_excel(file, skiprows=2)
				data.drop(columns="Unnamed: 0", inplace=True)
				if file.name == "iOS.xlsx":
					data.rename(columns={"发表时间": "评论时间", "作者": "评论人", "评级": "星级"}, inplace=True)
			data_ls.append(data)
		data_out = pd.concat(data_ls, ignore_index=True)
		data_out = data_out.sort_values(by=["评论时间"]).reset_index(drop=True)
		self.data_out = data_out.astype('str')
		
	def select_cls(self):
		for i in range(len(self.data_out)):
			if is_chinese(self.data_out.loc[i, "内容"]):
				st.markdown(f"> {i+1}. " + str(self.data_out.loc[i, '内容']))
				self.data_out.loc[i, "问题分类"] = st.selectbox("问题分类_" + str(i+1), ["Push", "标题党", "功能", "广告", "活动", "内容", "其他", "强制下载", "提现", "性能", "账号"], index=6)
			else:
				self.data_out.loc[i, "问题分类"] = "其他"
	
			
# GUI部分
## sidebar
st.sidebar.markdown("# 目标时间")
year = st.sidebar.number_input("年", 2021, 2099, value=last_month(datetime.now())[0])
month = st.sidebar.number_input("月", 1, 12, value=last_month(datetime.now())[1])

st.sidebar.markdown("# 原始文件")
files_in = st.sidebar.file_uploader("端内", accept_multiple_files=True)
files_out = st.sidebar.file_uploader("端外", accept_multiple_files=True)

## Content
st.markdown("# 时间范围")
d1, d2 = st.columns(2)
d1.text("开始时间：" + str(time_start_end(year, month)[0]))
d2.text("结束时间：" + str(time_start_end(year, month)[1]))

### 端内结果
if files_in:
	indata = InClient(files_in, year, month)
	
	# 剔除重复数据
	d3, d4 = st.columns(2)
	drop_btn = d3.checkbox("剔除重复数据")
	if drop_btn:
		dup = indata.drop_duplicate()
		d4.text(f"删除重复数据：{dup}")
	
	# 剔除活动数据
	d5, d6 = st.columns(2)
	activity_btn = d5.checkbox("剔除活动数据")
	if activity_btn:
		selected_cls = st.multiselect("请选择活动分类", options=indata.data_in["问题类型"].unique())
		activity = indata.drop_activity(selected_cls)
		d6.text(f"删除活动数据：{activity}")
		
	# 重命名分类
	d7, d8 = st.columns(2)
	rename_btn = d7.checkbox("重命名分类")
	if rename_btn:
		rename_str1 = st.text_area("请输入要修改的一级分类：（旧）->（新）")
		rename_str2 = st.text_area("请输入要修改的二级分类：（旧）->（新）")
		if rename_str1:
			indata.rename_cls(rename_str1, True)
		if rename_str2:
			indata.rename_cls(rename_str2, False)
	
	# 转移分类
	d9, d10 = st.columns(2)
	transfer_btn = d9.checkbox("转移分类")
	if transfer_btn:
		transfer_str = st.text_area("请输入要转移的分类：一级（旧）->一级（新）")
		if transfer_str:
			indata.transfer_cls(transfer_str)
			
	# 检查无效分类
	d11, d12 = st.columns(2)
	checknull_btn = d11.checkbox("检查无效分类")
	if checknull_btn:
		with st.expander("检查无效分类"):
			with st.form("无效表单"):
				indata.check_null()
				st.form_submit_button("提交")
	
	st.markdown("# 端内结果")
	st.dataframe(indata.data_in)
	plot_fig(indata.data_in["问题类型"], indata.data_in)
	r1, r2 = st.columns(2)
	r1.text(f"总数量：{len(indata.data_in)}")
	r2.download_button("下载端内结果", data=output_file(indata.data_in), file_name=f"{month}月端内结果.xlsx")
	
### 端外结果
if files_out:
	outdata = OutClient(files_out)
	
	# 修改其他分类
	d13, d14 = st.columns(2)
	select_other_btn = d13.checkbox("修改其他分类")
	if select_other_btn:
		with st.expander("修改其他分类"):
			with st.form("其他表单"):
				outdata.select_cls()
				st.form_submit_button("提交")
	
	st.markdown("# 端外结果")
	st.dataframe(outdata.data_out)
	plot_fig(outdata.data_out["问题类型"], outdata.data_out)
	r3, r4 = st.columns(2)
	r3.text(f"总数量：{len(outdata.data_out)}")
	r4.download_button("下载端外结果", data=output_file(outdata.data_out), file_name=f"{month}月端外结果.xlsx")