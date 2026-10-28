# 来源、贡献与结果证据

## 本仓库的定位

本仓库是对比赛方案的**后处理复现与方法存档**：提供新编写的纯融合实现、V38 配置、合成演示与说明文档。它不重新分发上游完整 notebook、嵌入推理代码、模型权重、DICOM、患者文件、真实标签或预测 CSV。

原比赛流程基于公开模型与代码，包含方案集成、融合权重迭代和运行核验。Solo 参赛不表示五个模型都由参赛者独立发明或训练。本仓库也不把上游作者的 Reader 训练、数据构造或模型创新表述为本人的独立原创。

原始 notebook 中第一人称的 “What is ours” 等文字属于其原作者，不能直接用于说明本仓库作者的贡献。因此本仓库重新撰写说明，只保留必要的事实、方法与引用。

## 主要上游

| 来源 | 在原流程中的角色 |
|---|---|
| [goodpjw2008：CoAtNet + R6 + 2.5D MIL](https://www.kaggle.com/code/goodpjw2008/rsna-knee-coatnet-r6-2-5d-mil-lb-0-958) | 原公开集成主线及方法说明 |
| [goodpjw2008：2.5D ConvNeXt Reader](https://www.kaggle.com/datasets/goodpjw2008/rsna-knee-2-5d-convnext-reader) | Reader 结构、推理及公开折次 checkpoint |
| [nartaa：384 CoAtNet / anatomical mirror](https://www.kaggle.com/code/nartaa/rsna-knee-0949-anatomical-mirror) | Raptor384 分支 |
| [nartaa：224 efficient crop](https://www.kaggle.com/code/nartaa/rsna-knee-0945-efficient-224crop) | Raptor224 分支 |
| [nartaa：S6 all-data weights](https://www.kaggle.com/datasets/nartaa/rsna-knee-s6fall-weights) | S6 分支资产 |
| [heliosli：R6 flip-TTA 主线](https://www.kaggle.com/code/heliosli/this-is-new-version-0-9576-in-one-click) | R6 推理、镜像 TTA 与 compact 方案 |
| [heliosli：per-finding blend](https://www.kaggle.com/code/heliosli/blend-mine-in-private-lb-luck-to-all-upvoters) | 逐病种融合思路与权重来源之一 |
| [varshithakolupuri：224 checkpoint 融合](https://www.kaggle.com/code/varshithakolupuri/rsna-knee-one-unused-checkpoint-lifts-the-0-956) | 224 分支加入 Raptor 组的公开方案 |
| [rostigor：R6 versioned copy](https://www.kaggle.com/datasets/rostigor/rsna-knee-r6-fe055406) | 原流程使用的 R6 版本化资产副本 |
| [Dread Development：Raptor](https://www.kaggle.com/datasets/dreaddevelopment/raptor-knee-widedense) | Raptor recipe 与 backbone 来源 |

原主线另致谢 sujanmajhisuzan 的融合及 Reader 改动，以及标签表、`timm` 等相关贡献者。上表为主要依赖链说明，不代表取得了这些代码或模型的再分发权。

上游说明中指出，Part A1 模型使用了 Osteoarthritis Initiative（OAI）数据，并要求保留其致谢。相关来源为 [NIMH Data Archive Study 3407](https://nda.nih.gov/study.html?id=3407)、[DOI: 10.15154/0hcg-f676](https://doi.org/10.15154/0hcg-f676)。本仓库不复制该数据或相应权重；实际使用时应阅读并遵守原资产的完整条件与致谢要求。

## 成绩与版本的区分

| 事项 | 证据口径 |
|---|---|
| Solo 银牌、311 / 6,300、前 4.94% | 按参赛者提供的成绩记录展示；本仓库后处理演示不重新验证该成绩 |
| V38 提交 57412742、公榜显示 0.958 | 依据截至 2026-10-21 保存的官方提交与状态记录；当时接口列为当前最佳 |
| V38 与本文配方一致 | 存档源码和配方审计记录支持：两组内部65/35、逐病种组间权重、Reader 0.3%–3.5% |
| 最终私榜分数、最终选中版本 | 现有存档未证明，不作推断 |

三例可见推理的运行与融合核对通过，不能等同于完整隐藏测试集的可见验证。历史公榜只显示三位小数；不把显示 0.958 写成更高精度分数。探索样本反复用于调权，也不作为独立验证结论。

为保护数据与账户信息，本仓库不附原始账户响应、私有运行标识、患者标识明细或比赛预测文件；上述提交编号只用于说明历史证据的关联。

## 许可与公开方式

新编写实现与文档的许可范围，以仓库明确提供的许可证和文件声明为准。它不覆盖或替代 Kaggle 竞赛数据、上游代码、模型权重及第三方资产的各自许可。Kaggle 上可访问的内容也不能仅凭“公开可见”被重新许可或整份搬运。

本次整理不重新发布许可尚未逐段确认的原始推理 notebook。需要完整五分支推理时，应通过上表原始入口取得授权资产，并核对对应版本、依赖与运行环境。

公开方式遵守该比赛的[具体规则](https://www.kaggle.com/competitions/rsna-knee-abnormality-detection/rules)，其中 General Rules 的 Submission Code Requirements 区分公开代码与受限数据，并要求将公开代码提供至比赛关联的 Kaggle 讨论或 notebook。本次整理不包含数据再分发授权；Kaggle 镜像状态另行记录。
