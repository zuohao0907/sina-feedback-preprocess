# 用户反馈预处理工具
[项目地址](https://share.streamlit.io/zuohao0907/sina-feedback-preprocess/main/main.py)
## Part 1 端内
### 功能
1. 合并文件，剔除其它月份数据，按时间排序
2. 去除重复（did、问题类型、具体问题均相同或UID、问题类型、具体问题均相同则去除）
3. 去除活动数据
4. 分类名修改/合并
5. 检查无效分类并修改（不建议使用）
6. 移动分类（将一级分类转移为另一个一级分类的子分类）

### 使用流程
1. 直接导入文件，如有报错，进入下一步，否则直接跳到第三步
2. 根据错误的文件名，核对该文件
  * 表头是否为:  ["反馈时间", "用户UID", "用户昵称", "问题类型", "具体问题", "问题详情", "图片", "客户端版本", "手机系统版本", "手机型号", "设备ID", "联系方式", "问题是否解决/第一次登陆", "最后一次登陆"]
  * 反馈时间列有无特殊格式时间（标准格式: yyyy/mm/dd hh:mm:ss）
3. 勾选删除重复数据（可能会误删一个用户多次提交的同一类问题）
4. 勾选剔除活动数据，选择活动的分类
5. 勾选重命名分类，输入想要更名的分类，格式为：旧->新
6. 勾选检查无效分类，查看无效分类中是否有可以分类的项目（项目较多时不建议选择）
7. 勾选转移分类，将一级分类转为另一个一级分类的子分类，格式为：旧一级->新一级
8. 点击下载端内结果

## Part 2 端外

### 功能
1. 合并文件，剔除其它月份数据，按时间排序
2. 检查分类并修改（不建议使用）

### 使用流程
1. 修改文件名为：iOS, 华为, 小米, VIVO, OPPO, 魅族, 微博(注意iOS后两个字母大写)
2. 检查微博文件中反馈日期是否为标准格式：mm月dd日 hh:mm
3. 同时导入所有7个文件
4. 勾选修改其他分类，对项目指定分类
5. 点击下载端外结果

## 其他问题备注
* 开发者：左豪
* 联系方式：zuohao0907@outlook.com
* 图形化界面API文档：[Streamlit](https://docs.streamlit.io)
* 基于纯Python开发，如有修改意见请邮件联系开发者

