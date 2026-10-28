# RSNA Knee：银牌方案的排名融合复现

面向膝关节 MRI **12 类异常预测**，整理五分支集成方案的后处理实现、融合配置和方法来源。本仓库提供可运行的 **V38 排名融合实现**与合成数据演示，便于检查数值细节和说明比赛思路。

配套的 [Kaggle 公共 notebook](https://www.kaggle.com/code/luisszoboszlai/rsna-knee-v38-silver-rank-fusion)关联原比赛，展示相同融合代码与合成数据演示；[notebook 源文件](notebooks/v38_rank_fusion_demo.ipynb)也保存在本仓库。

**本仓库从五份分支预测开始，不包含 MRI 读取、模型训练或五分支影像推理。** 原方案使用公开模型与代码资产，相关推理需要分别取得上游授权并配置其运行环境。

## 经历与结果口径

- 参赛成绩：**Kaggle RSNA Knee Abnormality Detection，Solo 银牌，311 / 6,300（前 4.94%）**，按参赛者成绩记录展示。
- 本地保存的历史官方记录显示：截至 **2026-10-21**，提交 **57412742（V38）**已完成，公榜显示 **0.958**，当时被接口列为当前最佳提交。
- V38 是与所描述的五分支、65/35 配方一致的存档版本。现有证据没有证明它是最终选中版本，也没有核实最终私榜分数；上述两类结果分别记录。

## 方案结构

| 分支 | 原方案中的模型与作用 |
|---|---|
| Raptor384 | 384 像素输入的 CoAtNet |
| Raptor224 | 224 像素裁剪的 CoAtNet，与 384 分支互补 |
| R6 | 四折 ConvNeXt，原图与镜像 TTA |
| S6 | 全数据训练的 ConvNeXt，提供补充预测 |
| Reader | 三折 2.5D ConvNeXt 多实例学习，以小权重加入 |

先分别按 **65% / 35%**融合 Raptor384 / Raptor224 和 R6 / S6，再按病种分配两组份额。基础预测重新排名后，以 **0.3%–3.5%**的逐病种份额加入 Reader，最后再次排名。

`rank` 指同一病种在当前完整病例集合中的百分位排名，并列值取平均名次。本实现兼容 V38 的 **float32 → CSV 序列化 → 读回**步骤，避免用直接浮点转换替代历史计算路径。

## 运行

在仓库根目录安装：

```bash
python -m pip install -e .
```

使用合成数据演示，不需要患者数据或模型权重：

```bash
python -m rsna_knee_ensemble demo --output-dir artifacts/demo
```

融合已合法取得的五份分支预测：

```bash
python -m rsna_knee_ensemble blend --config configs/v38.json --raptor384 /path/to/raptor384.csv --raptor224 /path/to/raptor224.csv --r6 /path/to/r6.csv --s6 /path/to/s6.csv --reader /path/to/reader.csv --output artifacts/submission.csv
```

每份 CSV 包含 `StudyInstanceUID` 和相同的 12 个病种列，病例须一一对应。输出仅为后处理结果，不表示已通过 Kaggle 评分。请将真实预测保留在本机，不提交到仓库。

原 S6 的 `B_probs.csv` 还包含额外的 `z|...` 列，接入前仅保留病例 ID 和 12 个概率列；不能把这些额外列作为概率输入。镜像 TTA 的平均与解剖标签回映，应在生成分支预测时完成。

运行测试：

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
```

已通过 17 项测试，并在本地与存档可见运行的融合输出逐元素核对一致；验证范围见 [复现核对](docs/VALIDATION.md)。

## 面试时可以讨论的内容

- 为什么使用排名融合，以及它与概率校准的区别。
- 为什么按病种分配权重，并将 Reader 控制在小份额。
- 镜像 TTA 中内外侧标签回映为什么应在分支推理阶段完成。
- 并列排名、病例集合、CSV 精度和列对齐如何影响可复现性。
- 为什么反复用于调参的 58 例探索样本不能作为独立验证集。

详细公式与逐病种权重见 [方案说明](docs/SOLUTION.md)；上游引用、贡献边界与证据口径见 [来源说明](docs/PROVENANCE.md)。新编写的代码采用 [MIT 许可](LICENSE)，该许可不覆盖上游代码、数据或权重。
