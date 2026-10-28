# V38 五分支排名融合

## 范围

本实现复现 **分支预测之后的后处理**。输入是 Raptor384、Raptor224、R6、S6、Reader 五份预测，不是 MRI 文件。完整影像流程中的预处理、模型结构、checkpoint 加载、折次聚合和镜像 TTA，由各分支的授权上游实现负责。

五个分支分别为 384 CoAtNet、224 裁剪 CoAtNet、四折 ConvNeXt R6、全数据训练 ConvNeXt S6，以及三折 2.5D ConvNeXt-MIL Reader。这些模型不是本仓库作者全部独立设计或训练的。

## 输入约定

每份 CSV 的标识列为 `StudyInstanceUID`，预测列为：

```text
ACL, MCL, Medial Meniscus, Lateral Meniscus,
Medial OA, Lateral OA, PF OA, Effusion,
Synovitis, Baker's, Contusion, Fracture
```

病例标识应唯一、五份文件的病例集合一致，预测应为有限数值。融合时按照病例标识和约定病种顺序对齐，不能依赖五份文件恰巧具有相同的行顺序。标识只承担对齐作用，不作为模型特征。

R6 输入应已完成原图与镜像预测的合并；对涉及内外侧的输出，需要先映射回原解剖位置。该操作属于影像分支推理，本后处理模块不会从 CSV 自动恢复或推断镜像对应关系。

## 排名定义

对每个病种，在本次输入的完整病例集合上执行：

```python
pandas.DataFrame(values).rank(method="average", pct=True)
```

每列独立排名，并列预测取平均名次，再除以病例数。这里得到的是相对排序，不是经过校准的患病概率。单病例输入或拆分不同批次，会改变排名含义；应将待融合病例作为一个完整集合处理。

## 计算顺序

记 `R(X)` 为上述逐列百分位排名，`c` 为病种，`w_c` 为该病种的 Raptor 组份额，`λ_c` 为 Reader 最终份额。

第一步，构造两个模型组：

```text
raptor  = 0.65 × R(raptor384) + 0.35 × R(raptor224)
compact = 0.65 × R(r6)        + 0.35 × R(s6)
```

第二步，逐病种融合：

```text
base_c = w_c × raptor_c + (1 − w_c) × compact_c
```

第三步，复现历史数值路径，再加入 Reader：

```text
base_csv = read_csv(to_csv(float32(base)))
final_c  = R((1 − λ_c) × R(base_csv)_c + λ_c × R(reader)_c)
```

`base_csv` 表示先转换为 float32，再按 CSV 十进制文本序列化并读回。它不等同于仅执行 `astype(float32).astype(float64)`；边界数值和并列关系可能受到序列化影响，因此将这一步作为兼容性要求保留。

最终 CSV 保留病例标识及 12 个病种的排名分数。本实现不自动向 Kaggle 提交结果。

## V38 逐病种权重

两组内部都固定为 65/35。下表中的 Raptor 份额用于组间融合，compact 份额为其补数；Reader 份额用于最后一层。

| 病种 | Raptor 组份额 | Reader 最终份额 |
|---|---:|---:|
| ACL | 35% | 2.5% |
| MCL | 37.5% | 2.0% |
| Medial Meniscus | 50% | 2.0% |
| Lateral Meniscus | 40% | 0.8% |
| Medial OA | 42.5% | 2.5% |
| Lateral OA | 12.5% | 0.8% |
| PF OA | 42.5% | 0.8% |
| Effusion | 52.5% | 0.4% |
| Synovitis | 60% | 0.3% |
| Baker's | 28.75% | 3.5% |
| Contusion | 35% | 3.0% |
| Fracture | 55% | 0.8% |

这些是存档配置，不是针对新数据重新拟合的最优权重。

## 版本差异与证据

| 版本 | 相对上一主要版本的变化 | Compact 内 R6/S6 |
|---|---|---|
| V38 | 相对 V34，各病种 Raptor 组份额统一降低 5 个百分点 | 65/35 |
| V39 | 相对 V38，Raptor 组份额再降低 5 个百分点 | 65/35 |
| V41 | 组间权重保持 V39，仅调整 compact 内份额 | 75/25 |

截至 2026-10-21 保存的官方状态中，三者均显示公榜 0.958，当时当前最佳为 V38、提交 57412742。显示精度为三位小数，不能据此判定精确同分或精确差值，也不能由这些记录推断最终私榜或最终选中版本。

反复用于探索和调权的 58 例样本不构成独立验证；可见 3 例的运行与算术复核，只能说明该可见输入上的执行与融合一致性。合成演示和软件测试用于检查实现，也不验证银牌成绩或模型的泛化能力。

## 复现与进一步使用

`demo` 使用合成分支分数展示流程；`blend` 处理本机提供的五份 CSV。取得真实分支预测时，需要分别遵循竞赛、上游代码和模型资产的获取与使用条件。来源和贡献边界见 [PROVENANCE.md](PROVENANCE.md)。
