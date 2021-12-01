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
	s = s.replace("月", "-")
	s = s.replace("日", "")
	s = f"{year}-{s}:00"
	return s

def last_month(now):
	lmonth = now.month
	lyear = now.year
	if now.month == 1:
		lmonth = 12
		lyear -= 1
	else:
		lmonth -= 1
	return lyear, lmonth
		
	
# ----------sidebar-----------
lyear = last_month(datetime.now())[0]
lmonth = last_month(datetime.now())[1]

st.sidebar.write("## 目标时间")
year = st.sidebar.number_input("year", 2021, 2030, value=lyear)
month = st.sidebar.number_input("month", 1, 12, value=lmonth)

st.sidebar.write("## 端内原文件")
files_in = st.sidebar.file_uploader("端内", accept_multiple_files=True)

st.sidebar.write("## 端外原文件")
files_out = st.sidebar.file_uploader("端外", accept_multiple_files=True)

# ----------------------------

# ----------content-----------

start = datetime(year, month, 1)
if month == 12:
	end = datetime(year+1, 1, 1)
else:
	end = datetime(year, month+1, 1)

columns = ["反馈时间", "用户UID", "用户昵称", "问题类型", "具体问题", "问题详情", "图片", "客户端", "手机系统版本", "手机型号", "设备ID", "联系方式", "问题是否解决/第一次登陆", "最后一次登陆"]
#cls = ["登录问题", "功能建议", "广告类", "金币咨询", "客户端功能", "每日领红包", "每日赢大奖", "内容问题", "评论问题", "视频问题", "图片问题", "推荐问题", "无效问题", "疫情情况", "疫情数据", "余额", "账号相关咨询", "PUSH类"]
data_list_in = []

st.markdown("## 时间范围")
z1, z2 = st.columns(2)
z1.write("开始时间: " + str(start))
z2.write("结束时间: " + str(end))


# ---------------------端内---------------------------

if len(files_in) > 0:
	for file_in in files_in:
		if file_in is not None:
			data_in = pd.read_excel(file_in, usecols=range(14))
			data_in.columns = columns
			data_in = data_in.dropna(axis=1, how='all')
			data_in["反馈时间"] = data_in['反馈时间'].astype("datetime64[ns]")
			data_in = data_in[(data_in["反馈时间"] > start) & (data_in["反馈时间"] < end)]
			data_list_in.append(data_in)
	data_in = pd.concat(data_list_in, ignore_index=True)
	data_in = data_in.sort_values(by=["反馈时间"]).reset_index(drop=True)
	
	# 剔除重复did&问题都重复的数据
	d1, d2 = st.columns(2)
	if d1.checkbox("剔除重复数据", value=True):
		dup = len(data_in) - len(data_in.drop_duplicates(subset=["设备ID", "问题类型", "具体问题"]))
		data_in = data_in.drop_duplicates(subset=["设备ID", "问题类型", "具体问题"])
		d2.write("删除重复数据：" + str(dup))
	
	
	# 剔除活动数据
	a1, a2 = st.columns(2)
	cls = data_in["问题类型"].unique()
	unselected_cls = cls
	if a1.checkbox("剔除活动数据", value=True):
		selected_cls = st.multiselect("请选择活动分类", options=cls)
		unselected_cls = data_in[~data_in["问题类型"].isin(selected_cls)]["问题类型"].unique()
		activity = len(data_in) - len(data_in[~data_in["问题类型"].isin(selected_cls)])
		data_in = data_in[~data_in["问题类型"].isin(selected_cls)]
		a2.write("删除活动数据：" + str(activity))
		
	# 修改分类

	
	number_of_cls = st.slider("修改分类数", 0, 10, 1)
	for i in range(number_of_cls):
		exec(f"c{i}1, c{i}2 = st.columns(2)")
		exec(f"old{i} = c{i}1.multiselect('要修改/合并的分类_{i+1}', unselected_cls)")
		exec(f"new{i} = c{i}2.text_input('新分类_{i+1}')")
		exec(f"""for item in old{i}:
			data_in["问题类型"].replace(item, new{i}, inplace=True)
		""")

	data_in.reset_index(inplace=True, drop=True)
	
	# 检查无效分类
	st.markdown("## 检查无效分类")
	with st.expander("请选择分类"):
		n = 0
		for i in range(len(data_in)):
			if data_in.loc[i, "问题类型"] == "无效问题" and is_chinese(str(data_in.loc[i, "问题详情"])):
				n += 1
				st.markdown(f"> {n}. " + str(data_in.loc[i, '问题详情']))
				data_in.loc[i, "问题类型"] = st.selectbox("问题类型_" + str(n), data_in["问题类型"].unique(), list(data_in["问题类型"].unique()).index("无效问题"))
				data_in.loc[i, "具体问题"] = st.selectbox("具体问题_" + str(n), data_in[data_in["问题类型"]==data_in.loc[i, "问题类型"]]["具体问题"].unique())
		
	
	
	data_in = data_in.astype(str)
	st.markdown("## 端内结果")
	st.dataframe(data_in)
	
	# 画图
#	fig_dic = {}
#	for item in unselected_cls:
#		fig_dic[item] = len(data_in[data_in["问题类型"]==item])
#	st.bar_chart(fig_dic)
	
	dn1, dn2 = st.columns(2)
	dn1.write("总数量：" + str(len(data_in)-len(data_in[data_in["问题类型"]=="无效问题"])) + "；" + "无效问题数量：" + str(len(data_in[data_in["问题类型"]=="无效问题"])))
	#data_in = data_in[data_in["问题类型"]!="无效问题"]
	data_in.reset_index(inplace=True, drop=True)
	
	dn2.download_button("下载端内结果", data=output_file(data_in), file_name=f"{month}月端内结果.xlsx")

	
# ------------------------端外----------------------------


name = ["iOS", "华为", "小米", "OPPO", "VIVO", "魅族", "微博"]
data_list_out = []

if len(files_out) > 0:
	for file_out in files_out:
		if file_out is not None:
			if file_out.name == "微博.xlsx":
				data_out = pd.read_excel(file_out)
			else:
				data_out = pd.read_excel(file_out, skiprows=2)
				data_out.drop(columns="Unnamed: 0", inplace=True)
			data_out["品牌"] = file_out.name.rstrip(".xlsx")
			
			
			# 修改iOS表头
			if file_out.name == "iOS.xlsx":
				data_out.rename(columns={"发表时间": "评论时间", "作者": "评论人", "评级": "星级"}, inplace=True)
				
			# 修改微博表头、时间
			if file_out.name == "微博.xlsx":
				data_out.rename(columns={"反馈日期": "评论时间", "用户昵称": "评论人", "反馈内容": "内容"}, inplace=True)
				data_out["评论时间"] = data_out["评论时间"].apply(lambda x: time_convert(x))
				wb = openpyxl.load_workbook(file_out)
				ws = wb.get_sheet_by_name('Sheet1')
				for i in range(len(data_out)):
					data_out.loc[i, "标题"] = ws.cell(row=i+2, column=1).hyperlink.target
				
				
			data_list_out.append(data_out)
			
	data_out = pd.concat(data_list_out)
	data_out.sort_values(by="评论时间", inplace=True)
	data_out.reset_index(drop = True, inplace=True)
	#order = ['评论时间', '评论人', '星级', '点赞数', '标题', '内容', '品牌', '机型', '版本', '配图', '备注']
	#data = data[order]

	data_out = data_out.astype(str)
	st.markdown("## 端外结果")

	with st.expander("请选择分类"):
		for i in range(len(data_out)):
			if is_chinese(data_out.loc[i, "内容"]):
				st.markdown(f"> {i+1}. " + str(data_out.loc[i, '内容']))
				data_out.loc[i, "问题分类"] = st.selectbox("问题分类_" + str(i+1), ["Push", "标题党", "功能", "广告", "活动", "内容", "其他", "强制下载", "提现", "性能", "账号"], index=6)
			else:
				data_out.loc[i, "问题分类"] = "其他"

	
	st.dataframe(data_out)
	
	dw1, dw2 = st.columns(2)
	dw1.write("总数量：" + str(len(data_out)))
	
	dw2.download_button("下载端外结果", data=output_file(data_out), file_name=f"{month}月端外结果.xlsx")
	
	
