# 独立审计报告

审计日期：2026-09-13。对象：项目当前磁盘快照及 `AUDIT.md` 中的主张。
模式：full-compute 廉价独立复核，包括 40 文件 SHA256/字节数、结构与表格重算、完整轨迹分析、ChEMBL/Open Targets/PubMed 在线核验。未重跑完整筛选、MD 生产、模型训练或 CNN 推理。

**结论：FAIL，当前研究报告不能作为已验证的先导物发现结果交付。** 原始计算产物确实存在，若干数值可以复现；但参考活性的靶点归属、结合态 MD 单位/分析、实际金属参数和生物学方向表述存在实质错误。此结论不等于认定人为造假，也不证明 SMPD1 假说或全部候选分子无效。

## 主要发现（按影响排序）

### 1. [P1] 参考物活性归属错误，ASM 活性锚定失效

`final-report.md:84`、`:88` 和 `target-dossier.md` 把三个参考物的约 1–2 µM 活性作为人 SMPD1/CHEMBL2760 的已知活性。在线查询确认：

| 分子 | 实际可查记录 | 对报告的影响 |
|---|---|---|
| CHEMBL310981 | 对人 CHEMBL2760 的 IC50 = 49,000 nM，activity_id 375434；1,000 / 3,300 nM 对应 CHEMBL4712 | 将 49 µM 错写为约 1 µM |
| CHEMBL418376 | 1,000 nM 对应人 CHEMBL4712（activity_id 372577）及大鼠 CHEMBL3528；此次查不到 CHEMBL2760 记录 | 不是已核实的人 ASM 1 µM 对照 |
| CHEMBL5284579 | 1,800 nM 对应人 CHEMBL4712，activity_id 24982941；此次查不到 CHEMBL2760 记录 | 同上 |

CHEMBL4712 的记录名称为 “Sphingomyelin phosphodiesterase 2”，并非此次人 ASM 靶点 CHEMBL2760。原始缓存 `data/chembl_finalists_extra.json:7` 已有 49,000 nM，故不能仅解释为在线数据库变化。其 `SMPD1_human_B` 标签不足以证明靶点身份。

应撤回 D5 和 CNN 的“已知 ASM 微摩尔活性带”解释，按 target ID、物种、assay ID、测量类型、关系符和原始论文重建参考集。证据：`live_results.json`、`followup_results.json`。

### 2. [P1] 结合态 MD 的距离单位、时长和主链选择错误

`scripts/bound_md.py:48` 取出的坐标单位是 nm，`:49` 的 RMSD 未乘 10，打印时却写 A。因此日志中的 0.69 对应 6.9 Å，而非报告的 0.69 Å；该指标是相对最小化坐标的未拟合位移，也并非注释所称的 pocket frame RMSD。

积分步长为 2 fs，每轮 1,000,000 步实际为 2 ns。`md/bound_log.csv` 有 1,220 条，末行 3,050,000 步、6,100 ps，包含 100 ps 初始阶段和 6 ns 后续运行，并非 3 ns。

`:26` 的主链选择仅排除 LIG/ZN，包含 21,684 个水氧。`md/bound_run.log` 的 backbone=23,796 因而不是蛋白主链原子数；“12.5 Å 主链漂移由建模环区导致”的解释没有被这个指标支持，且同样混淆 nm/Å。

独立复算全部 1,220 帧：先周期整分子 imaging，再只以蛋白 backbone 拟合，以首个保存帧为参考，配体重原子 RMSD 平均 4.128 Å、最大 5.141 Å；配体自身拟合的内部 RMSD 平均 1.847 Å、最大 2.370 Å；蛋白主链 RMSD 平均 2.175 Å、最大 2.679 Å。这些定义与原始最小化参考不同，不能逐数直接替换原指标；但“≤0.69 Å 稳定结合”和“巨大蛋白环区漂移”的现有证据链均不成立。最小化 x0 未单独保存，此次未重做最小化来伪装成相同参考。

### 3. [P1] 实际 Zn 参数不是报告声称加载的参数

从 `md/complex.prmtop` 用 ParmEd 读取两个 Zn：电荷 +2，Rmin/2 = 1.271 Å，epsilon = 0.00330286 kcal/mol。与 Amber 的 `frcmod.ions234lm_126_tip3p` 中 Li et al., JCTC 2013, 9, 2733 的 CM 参数一致。

报告宣称的是 `frcmod.ions234lm_1264_tip3p` 中 1.455 Å / 0.02662782 的 2014 参数之 12-6 子集。`md/tleap_bound.in` 只 source `leaprc.water.tip3p`，其实际加载前述 126 文件，没有覆盖为报告所称 1264 参数。证明某个参数文件存在不等于证明模拟使用它。

这不是“自造参数”，而是方法/引用与实际执行不符。应更正所用模型和局限，或在重新验证配置后另行复跑；现有轨迹不能改名当成另一套参数的结果。

### 4. [P1] 被列为支持证据的论文含方向性反例

PMID 27598773 摘要说明：ASM 过表达模型未出现所测记忆缺陷；amitriptyline 损害雌性野生型小鼠部分物体记忆表现；ASM 过表达对该药的不利记忆影响有保护作用。这不支持“抑制方向一致有益”。

PMID 38337058 和 37605262 的确提供治疗假说与细胞/小鼠支持，但不能抹去第三篇中的相反结果。G1/G2 应重审适用模型、性别、药物多靶点作用与暴露条件，而不是仅核对论文标题后宣告方向确认。证据：`live_results.json` 中三个完整摘要。

### 5. [P1] hERG 大模型的数据规模与可追溯性不符

`final-report.md:128` 声称 n≈12k、AUC 0.904±0.004；当前 `data/herg_central.tab` 有 **306,893** 条，实际执行 `Tox(name='hERG_Central', label_name='hERG_inhib').get_data()` 同样返回 306,893 条。`scripts/herg_karim.py` 未抽样，会对全部记录做 Morgan 指纹、五折 RF 训练。

没有找到对应 12k 抽样规则、划分索引和此大模型的训练日志；此次未重训，因此不能判定 0.904 本身真或假，但无法用当前描述复现。两种模型均使用随机分层 CV，不能据此直接宣称新骨架安全性已“de-risk”。应保存实际训练集身份、去重/划分、运行日志和外部验证，并检查候选与训练集重合。

### 6. [P2] 完整性检查为 39/40，通过不了项目自定规则

`research-log.md` 期望 36,576 bytes，实际 37,661 bytes；期望 SHA256 为 `e96428bd201759c6254744c92c819c3a15799c4dac8c70b39ceabec24bc70009`，实际为 `a31a1595a07fa2e1ca46b9bb5c512c1f8339cda2756745490477ed04735cc056`。其余 39 文件哈希及字节数吻合。

末尾新增的 D12 审计说明可能解释差异，但没有旧副本就不能重建修改内容。哈希失配不等于证明数据造假。原始 `data/` 关键输入、部分分析脚本及 AUDIT.md 本身未被这份 40 文件清单覆盖，清单通过也不证明全项目完整性。

### 7. [P2] “Zn 接触全程 1.9–2.1 Å”不成立

使用 MDTraj 的周期最小镜像距离，逐帧计算两个 Zn 与 36 个配体重原子全部配对的最小值，结果为 **1.810–3.529 Å，均值 1.978 Å**；只有 **77.87%** 保存帧位于 1.9–2.1 Å。与原审计的抽样均值差异可由抽样方式解释，但“贯穿”不能据此成立。

全体原子对的最小距离不追踪固定供体和固定 Zn，不等于维持同一个配位键，也不单独证明稳定结合或酶抑制。此次没有用非周期欧氏距离宣告模拟错误。

### 8. [P2] 筛选表首行不是最佳 Vina 能量，漏斗核查命令不正确

3,642 行、3,642 个唯一名称、1,158 个分数 ≤ -7.0 均确认。表按 composite 排序，首行 CHEMBL28172 为 -8.84；实际最低 Vina 分为 **CHEMBL54786，-8.92**。

`library_filtered.csv` 总计 20,111 条，应用脚本中的 error/alerts/charge 条件后才是 11,758；`dock_set.smi` 实为 3,500 行，不是协议预期的 3,452。筛选表有 152 个名称不在当前 dock_set，需登记批次合并来源；这本身不证明异常分子被伪造。

`prep_failures.json` 登记了 10 个 embed-failed，且 research-log.md:312 已提及，因此不是完全未披露；但 AUDIT.md §5 失败登记不完整。应区分“对接失败为零”与前处理失败，避免从行数猜漏斗阶段。

### 9. [P2] 活性记录的缺失与编号错误

D3 的 CHEMBL28172 确有 Nociceptin Ki 2.5 nM；验证命令却用 CHEMBL28132，实际检索到 renin/cathepsin D 记录。

`final-report.md:28` 所谓 CHEMBL7385 “no prior activity records”不准确：此次查到 1 条 HIV reverse transcriptase inhibition=0% 的阴性记录；CHEMBL24974 “no prior records”也不准确，有 5 条，包括大鼠血压降低和 LogD 记录。阴性结果不能写成有活性，但“无强阳性靶点记录”和“无任何记录”也不能混用。

### 10. [P2] 重对接 RMSD 采用过度宽松的元素匹配

`scripts/redock.py` 允许任意同元素原子交换，不保持分子连接关系，重算得到的 1.75697 Å 只是这种匹配的结果。按原子名为 2.52418 Å；保持桥接 O2 和链骨架不变，允许三个末端磷酸氧及三个 N-甲基分别置换，得到 1.91377 Å。

后者把末端磷酸氧视作等价，仍是宽松的共振/质子化约定，不能取代正式的键级/质子化感知图同构验证。因此此次不直接判定 G3 门失败，也不把 1.76 Å 作为严格验证值。建议明确质子化状态和对称性算法后重新核准全部晶体。

### 11. [P2] CNN 和选择性的结论超出表格证据

CNN 9 行及 CHEMBL7385 最高 CNNscore=0.705 可确认；但 `final-report.md:94` 称全部四个候选均在参考活性带内，其自身表格中 CHEMBL24974=5.269、CHEMBL48767=4.875 已低于参考最低 5.733。更根本的是参考活性靶点归属错误。

同工酶表的最大 Tanimoto=0.308 可确认，但低化学相似性不能证实功能选择性；当前没有完整可执行重算脚本和固定参考库，D4 只通过文件数值检查。

## 注册表逐项状态

PASS 仅表示该项注明的检查通过，不代表其上游方法或生物学推论通过。PARTIAL 表示部分验证；NOT RUN 表示未执行该计算。

| 主张 | 状态与此次验证 |
|---|---|
| A1 | PASS/PARTIAL：在线抽查 TREM2 genetic=0.862174、CR1 genetic=0.913571，符合缓存；不是二者 overall 分数；未逐一核对所有 22 基因在线分数 |
| A2 | PASS：在内存执行现有评分逻辑，22 个 total 与缓存全一致，没有覆盖原文件 |
| A3 | PASS/PARTIAL：PubMed SMPD1 AND inhibitor，2015–2025，50 条，与缓存一致；协议把 CHEMBL ID 写作基因示例不适用 |
| B1 | PARTIAL：在线 CHEMBL2760 mechanisms=0；只能证明此查询无机制记录，不能穷尽批准药、专利或全部功能性抑制作用 |
| B2 | FAIL：参考活性归属错误，见发现 1 |
| B3 | FAIL（方向）；PASS（引文存在）：三篇标题/摘要可查，27598773 含不支持统一抑制方向的结果 |
| B4 | PASS（数据库范围）：在线及缓存 SMPD1 均无 genetic_association 行；不能扩张为全人类文献中不存在遗传证据 |
| C1 | PARTIAL：现存姿态复算 1.757 Å 为元素匹配；连接约束的宽松匹配 1.914 Å，未重新对接 |
| C2 | NOT RUN：现存 ensemble 表存在；未重跑交叉晶体对接/完整结构匹配 |
| C3 | PARTIAL：P2Rank 原始 CSV 第一项 score=39.05、prob=0.961，中心存在；未重跑模型 |
| D1 | PARTIAL/FAIL：行数和阈值通过，“最佳 -8.84”错误 |
| D2 | PARTIAL/FAIL：20,111→11,758→3,500 的筛选条件可复核；协议逐文件行数预期错误 |
| D3 | PARTIAL/FAIL：28172 活性查证，命令编号错误；未逐一复核 top10 全部六个 GPCR 归属 |
| D4 | PARTIAL：现存表最大 0.308；未重建同工酶参考库，不认定功能选择性 |
| D5 | FAIL（参考身份）；NOT RUN（重对接） |
| E1 | PARTIAL：225 条结果存在；未重生成、重对接，不能单凭结果行数证明 0 失败 |
| E2 | PARTIAL：ADMET 文件在完整性清单中吻合；未重跑 DeepPurpose |
| E3 | PARTIAL/FAIL：小数据训练日志确有 AUC 0.863/0.888；大模型 n≈12k 描述不符，未重训验证 0.904 |
| F1 | PASS（帧数/RMSD）：1,161 帧，蛋白 8,198 原子，bbRMSD 均值 2.750、最大 3.839 Å；最后轨迹帧对应约 5.805 ns，日志末端 5.8075 ns，非精确 5.78 ns |
| F2 | FAIL：全轨迹复算、单位、时长与原主链选择均见发现 2、7 |
| F3 | PASS（日志）：Errors=0，水 21,684；同时 Warnings=138，不能将零错误等同于物理建模有效 |
| F4 | PARTIAL：mol2 65 原子、电荷和约 -0.001，参数化脚本/日志存在；未重跑 AM1-BCC |
| F5 | FAIL（实际使用）；PASS（文件存在）：实际拓扑参数与引用参数文件不同 |
| G1 | PARTIAL：9 行和最高 CNNscore 可确认；未重跑 CNN，参考活性解释失效 |
| G2 | PASS（表格检查）：GNINA vina_affinity 与筛选表不同，报告有跨引擎不可直接比较的声明 |

## 复现、边界与修复顺序

Windows 项目根目录执行：`python independent-audit/check_local.py`、`python independent-audit/check_structure.py`、`python independent-audit/check_live.py`、`python independent-audit/check_followup.py`。

WSL 轨迹分析：`wsl -d CybergymUbuntu -- /root/miniforge/envs/md/bin/python /mnt/c/Users/Gnimi/.zcode/workspace/default/cognition-drug-discovery/independent-audit/check_md.py`。

`local_results.json` 保存逐文件哈希及表格复算；`md_results.json` 保存全轨迹统计；`structure_results.json` 保存结构复算；两份 live/followup JSON 保存 API 原始响应和查询信息。MDTraj 对此 DCD 返回的 `time` 是帧索引式值，不能当作真实 ps；物理时间用 reporter 间隔、dt 和 StateDataReporter 日志交叉确定。apo 复算遵循原项目未发生蛋白包装断裂的首帧参考定义；结合态先做整分子 imaging。

审计自己的首次 Open Targets 查询因不支持 efoIds 参数返回 400，已保留并改用项目中可用的 disease associatedTargets 查询，后续成功。结构检查脚本的首次语法错误已修正；磷酸氧置换范围经检查原子名后扩展为三个末端氧，报告使用最终重算值。轨迹读取的 PDB 编号警告未当成模拟失败。

建议先修正靶点/活性身份和生物学方向，撤回 MD 稳定性及安全性已去风险的措辞；随后修复单位、原子选择、步数和参数声明，保存明确的参考构象与数据划分，再决定需要重跑的计算。最后统一漏斗批次与失败登记，并在报告冻结后重建完整性清单。当前无需因审计失败立刻重跑全部昂贵任务。

此次仅新增 independent-audit 目录，未修改原始研究报告、轨迹、脚本或原清单。用户尚未要求修复原研究，故交付的是可复核的独立审计结果。
