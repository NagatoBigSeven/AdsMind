
### TODO
任务：整理research\paper_plots\figure3\figure3_panels_updated.ipynb的数据来源：

说明：
现在notebook的数据并不是直接读取results中的文件，而是读取results_sherry这个文件夹（这是Sherry自己用python脚本处理过results中的原始数据获得的结果，但是没有把python代码给我）。
1. 需要理解notebook中图表的数据及其意义。
2. 使用results中的原始数据作为绘制图片的输入。如果原始数据不能直接用，就写python代码先处理results中的数据

要求：
1. 处理数据的python代码放到scripts文件夹，一起放到paper_plots文件夹中，原始数据和处理后的数据都从results文件夹中读取。
2. 中间处理过的原始数据放到results文件夹中，命名和内容可以参考results_sherry中的数据和都有什么，以及notebook需要什么样的数据。
3. 原则上要能重现Sherry的结果，作为cross-check。如果发现不一致，必须咨询我的意见。

