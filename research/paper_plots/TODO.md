


## TODO
None


### Done
整理两张SI中的数据处理，文件为research\paper_plots\figure_SI_1\si_figure_S1_panels.ipynb，research\paper_plots\figure_SI_2\si_figure_S2_panels.ipynb

说明：
现在notebook的数据并不是直接读取results中的文件，而是读取results_sherry这个文件夹（这是Sherry自己用python脚本处理过results中的原始数据获得的结果，但是没有把python代码给我）。
1. 需要理解notebook中图表的数据及其意义。
2. 使用results中的原始数据作为绘制图片的输入。如果原始数据不能直接用，就写python代码先处理results中的数据

要求：
1. 处理数据的python代码放到scripts文件夹，一起放到paper_plots文件夹中，原始数据和处理后的数据都从results文件夹中读取。
2. 中间处理过的原始数据放到results文件夹中，命名和内容可以参考results_sherry中的数据和都有什么，以及notebook需要什么样的数据。
3. 原则上要能重现Sherry的结果，作为cross-check。如果发现不一致，必须咨询我的意见。



### Done
整理两张SI图片中的panels，文件为research\paper_plots\figure_SI_1\si_figure_S1_panels.ipynb，research\paper_plots\figure_SI_2\si_figure_S2_panels.ipynb

SI 1 说明：
panel a：4个不同策略得出的CMU20的cases的best energy，柱状图。
panel b：根据论文内容和论点，我们并不关心 SI Figure 1 的 panel b 中展示的 token 消耗，可以去掉。
panel c 和 panel d ：都是说明两个不同MLFF的波动性，需要把panel d作为一个小图放在panel c坐标系的左下角（要求可调节位置和大小）。

SI 2 说明：
目前仍缺少gpt和claude的数据，之后会更新，但请在notebook中保留placeholder。
panel a是不同llm backend的slip与否。
panel b是planned site和actual site的分布对比。
panel c是多个seed的可重复性实验。

要求：
1. 对SI 1的图片，去掉panel b，合并panel c & d到一个panel中。
2. SI 1的panel c+d合并后的panel和SI 2的三个panel全是波动性检验，应该放到一张图中，把SI 1的panel a独立为一张图





### Done
任务：整理research\paper_plots\figure3\figure3_panels_updated.ipynb的数据来源：

说明：
现在notebook的数据并不是直接读取results中的文件，而是读取results_sherry这个文件夹（这是Sherry自己用python脚本处理过results中的原始数据获得的结果，但是没有把python代码给我）。
1. 需要理解notebook中图表的数据及其意义。
2. 使用results中的原始数据作为绘制图片的输入。如果原始数据不能直接用，就写python代码先处理results中的数据

要求：
1. 处理数据的python代码放到scripts文件夹，一起放到paper_plots文件夹中，原始数据和处理后的数据都从results文件夹中读取。
2. 中间处理过的原始数据放到results文件夹中，命名和内容可以参考results_sherry中的数据和都有什么，以及notebook需要什么样的数据。
3. 原则上要能重现Sherry的结果，作为cross-check。如果发现不一致，必须咨询我的意见。

