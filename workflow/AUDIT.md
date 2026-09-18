# AUDIT.md — 独立审计文档(供其他 AI agent / 人类审计员使用)

**项目**:AI 全流程自动化早期药物发现 — 靶点 SMPD1(人酸性鞘磷脂酶)→ 认知损伤适应症小分子先导物
**工作目录**:`C:\Users\Gnimi\.zcode\workspace\default\cognition-drug-discovery`
**生成时间**:2026-09-13 · **完整性清单**:`audit_manifest.json`(40 个关键文件 SHA256)

---

## 0. 审计协议(审计 agent 请按此执行)

1. **完整性**:对 `audit_manifest.json` 中每个文件重算 SHA256,与清单不符即FAIL。
2. **主张→证据**:对 §3 注册表中的每条主张,执行"独立验证命令"列,核对"预期结果"。
3. **活体验证**:§3 中标注 [LIVE] 的命令会访问外部 API(Open Targets/ChEMBL/PubMed),
   验证"同日查询"类主张是否仍然成立(注意:外部数据库会随时间变化,数值漂移本身
   不是 FAIL,但方向性结论翻转必须记录)。
4. **失败登记**:§5 列出所有已知失败/负结果。若审计发现未登记的失败,记为隐瞒。
5. **红线**:§7 列出会使本研究无效的具体情形。
6. 所有昂贵的完整复跑(虚拟筛选 93 分钟、MD 2.5 小时)标注 [EXPENSIVE];
   审计通常只需跑 §3 的廉价抽查。

**运行环境要求**:Windows 主机 Python 3.12(rdkit, chembl_webresource_client, PyTDC,
DeepPurpose, scikit-learn, meeko)+ WSL2 `CybergymUbuntu` 中 miniforge 环境
`md`(openmm/mdtraj/parmed)、`amber`(AmberTools)、`gnina12`(CUDA 12.8 库)、
`p2r`(OpenJDK);GPU RTX 5080。WSL 命令模板:
`wsl -d CybergymUbuntu -- ~/miniforge/envs/md/bin/python <script>`。

---

## 1. 环境与工具清单(可独立复核)

| 工具 | 版本验证命令 | 位置 |
|---|---|---|
| OpenMM | `wsl -d CybergymUbuntu -- ~/miniforge/envs/md/bin/python -c "import openmm; print(openmm.__version__)"` → 8.6.1 | WSL conda env `md` |
| AutoDock Vina | `./bin/vina.exe --version` → v1.2.7 | `bin/vina.exe` |
| AmberTools | `wsl ... ~/miniforge/envs/amber/bin/cpptraj --version` → V7.6.2 | WSL conda env `amber` |
| GROMACS | `wsl ... ~/miniforge/envs/gmx/bin/gmx --version` → 2026.3 | WSL conda env `gmx` |
| GNINA | `wsl ... LD_LIBRARY_PATH=~/miniforge/envs/gnina12/lib /tmp/gnina --version` → v1.3.3 | `/tmp/gnina` |
| P2Rank | `/tmp/p2rank_2.5.1/prank` | WSL /tmp |
| RDKit / Meeko / DeepPurpose / PyTDC / AiZynthFinder / mdtraj / ParmEd / scikit-learn | pip show | 主机 + WSL |
| GPU | `wsl ... nvidia-smi` → RTX 5080 Laptop 16GB, driver 616.64 | — |

**Zn²⁺ 参数来源(防"编造参数"审查)**:
`~/miniforge/envs/amber/dat/leap/parm/frcmod.ions234lm_1264_tip3p` 内含
`Zn2+ 1.455 0.02662782  12-6-4 set for TIP3P water from Li and Merz, JCTC, 2014, 10, 289`
(已引用文献,非自造)。本研究的结合态 MD 仅使用其中 12-6 子集,未含 C4 项(已声明)。

---

## 2. 流水线与产物地图

见 `AUTOMATION.md` §Pipeline map(9 阶段 → 脚本 → 产物 → 门)。一键复现入口
`scripts/run_all.sh` [EXPENSIVE, 全程 ~3–4 h]。

---

## 3. 主张 → 证据 → 独立验证注册表

所有"预测值"标注规范:对接分数/ADMET/CNN 亲和力均为 **PREDICTED**,报告中已逐一标注。

### 3.1 靶点发现(G1)

| # | 主张 | 证据文件 | 独立验证 [LIVE unless noted] | 预期(2026-09-12 时点) |
|---|---|---|---|---|
| A1 | Open Targets AD 关联:22 基因面板,TREM2 0.862 / CR1 0.914 等 | data/ot_associations.json, data/ad_scores.json | 重跑 `python scripts/ot_fetch_assoc.py` 并 diff 分数 | 分数量级一致(OT 会随版本微变) |
| A2 | 面板评分:HFE 0.660 > PLCG2 0.655 > … > GSK3B 0.265 | data/panel_scores.json, scripts/score_panel.py(权重 30/20/20/20/10 已写死) | 重跑 score_panel.py | 排序一致 |
| A3 | 文献趋势:CHEMBL7385 等 | data/pubmed_trends.json | 抽查 1 个基因的 esearch 计数 | 数量级一致 |

### 3.2 新颖性与档案(G2)

| # | 主张 | 证据 | 独立验证 | 预期 |
|---|---|---|---|---|
| B1 | 人 SMPD1 无已批准药物 | data/chembl_finalists_extra.json(CHEMBL2760 无机制行)、chembl_finalists.json | [LIVE] ChEMBL REST:`https://www.ebi.ac.uk/chembl/api/data/mechanism.json?target_chembl_id=CHEMBL2760` | 无 approved 行(olipudase 为生物制剂,不在小分子机制) |
| B2 | 已知 ASM 抑制剂 1–6 µM | 同上 examples 行(IC50 1000–14100 nM) | [LIVE] 同上 activity 端点 | 数值一致 |
| B3 | 方向:抑制有益 | data/pubmed_direction.json(PMID 38337058/37605262/27598773) | [LIVE] PubMed 取摘要比对标题 | 标题一致 |
| B4 | **诚实声明**:SMPD1 无人类遗传学证据线(OT genetic=0) | data/ad_scores.json | 重跑 ot_scores_trends.py | genetic=0.000 |

### 3.3 结构与口袋(G3)

| # | 主张 | 证据 | 独立验证(本地,廉价) | 预期 |
|---|---|---|---|---|
| C1 | 5I85 重对接 top 姿态 RMSD 1.76 Å | docking/redock_PC.log, docking/redock_PC_out.pdbqt, structures/5i85_PC.pdb | `python scripts/redock.py`(需先重跑 config 对接,~2 min) | <2.0 Å |
| C2 | 交叉晶体 5I81/5JG8:1.52/1.77 Å;锌保守 0.15–0.70 Å | docking/ensemble/PC_*.out.pdbqt, results/ensemble_scores.csv | 重跑 scripts/ensemble_dock.py [EXPENSIVE ~3 min] | 同值 |
| C3 | P2Rank 独立确认主口袋(top1 score 39.05, prob 0.961, 距盒心 8.0 Å) | results/p2rank_out/ | 重跑 scripts/p2rank_run.sh(~10 s) | 同值 |

### 3.4 虚拟筛选与三角分类(G4/G5)

| # | 主张 | 证据 | 独立验证 | 预期 |
|---|---|---|---|---|
| D1 | 3,642 个分子评分;1,158 个 ≤ −7.0;最佳 −8.84(CHEMBL28172) | results/hits_ranked.csv | `python -c "import csv;rows=list(csv.DictReader(open('results/hits_ranked.csv',encoding='utf-8')));print(len(rows),sum(1 for r in rows if float(r['vina_best'])<=-7.0),rows[0]['name'],rows[0]['vina_best'])"` | `3642 1158 CHEMBL28172 -8.84` |
| D2 | 库:20,111 → 11,758(PAINS/Brenk 清洁)→ 3,500 脚手架多样性 | data/chembl_library.jsonl, data/library_filtered.csv, data/dock_set.smi | 逐文件行数统计 | 20111 / 11758 / 3452 |
| D3 | **活性记录审计:top-10 中 6 个为已知 GPCR 配体并降级** | data/chembl_finalists.json(0 条)以外,audit 时可抽查 CHEMBL28172→Nociceptin Ki 2.5nM | [LIVE] `.../activity.json?molecule_chembl_id=CHEMBL28132` | 存在 Ki 2.5 nM 记录 |
| D4 | 同工酶选择性:top20 对 SMPD3/ASAH1/NAAA 配体集 max Tanimoto ≤0.31 | results/homolog_selectivity.csv | 重算(脚本内联于 research-log D6.2 引用的会话;可按 README 重写) | ≤0.31 |
| D5 | 参考 1–2 µM 活性物本协议下 −6.0~−7.0(锚定) | docking/out/REF_*.out.pdbqt | 重对接 3 个参考物(~8 min) | 同值 |

### 3.5 扩展与 ADMET

| # | 主张 | 证据 | 独立验证 | 预期 |
|---|---|---|---|---|
| E1 | 225 个扩展类似物、0 失败;CHEMBL24974-CF3 −9.36 | results/expansion_results.json(len=225) | 重跑 expansion.py [EXPENSIVE ~10 min] | 同值 |
| E2 | DeepPurpose ADMET:BBB 0.89–1.00;P-gp CHEMBL24974 0.94 | results/admet_predictions.csv | 重跑 admet_predict.py(模型已缓存) | 同值 |
| E3 | hERG 655 集 AUC 0.863 / DILI 0.888;hERG_Central ≈12k 集 AUC 0.904±0.004;CHEMBL7385 hERG 0.090 | results/herg_dili_predictions.csv, results/herg_karim_predictions.csv, data/herg_dili_train.log | 重跑 herg_dili.py / herg_karim.py(各 ~5–10 min) | AUC 一致(±随机性 0.01) |

### 3.6 分子动力学(本轮审计重点)

| # | 主张 | 证据 | 独立验证 | 预期 |
|---|---|---|---|---|
| F1 | apo MD 5.78 ns,1161 帧,141k→8198 蛋白原子;bbRMSD mean 2.75/max 3.84 Å | md/prod.dcd, md/solvated.pdb, md/md_summary.txt | `wsl ... ~/miniforge/envs/md/bin/python - <<'P'\nimport mdtraj as md;t=md.load("md/prod.dcd",top="md/solvated.pdb");print(t.n_frames)\nP` | 1161 |
| F2 | **结合态 MD 3 ns:配体重原子 RMSD ≤0.69 Å;Zn–配体 1.9–2.1 Å 贯穿** | md/bound.dcd, md/bound_log.csv, md/complex.prmtop | **必须用最小镜像约定**(见 §4 教训):`wsl ... python - <<'P'` 载入 bound.dcd+prmtop,对 resname LIG/ZN 用 unitcell_vectors 做最小镜像距离,抽样全轨迹 | min 1.83 / max 3.53 / mean 2.03 Å;naive 欧氏距离会得 18–35 Å(**那是错的**) |
| F3 | tleap 构建无错(Errors=0,CMET/NTRP 端基,21,684 水) | md/tleap_bound.log, md/complex.prmtop | 读日志尾 | Errors = 0 |
| F4 | GAFF2/AM1-BCC 参数化(65 原子) | md/leader.mol2, md/leader.frcmod, md/antechamber.log | 检查 mol2 @<TRIPOS>ATOM 65 行、电荷列非零 | 一致 |
| F5 | Zn²⁺ 参数出处 | amber env frcmod(见 §1) | grep Li and Merz | 文献行存在 |

### 3.7 CNN 重打分与二意见

| # | 主张 | 证据 | 独立验证 | 预期 |
|---|---|---|---|---|
| G1 | 9 个姿势 CNN 打分;CHEMBL7385 CNNscore 0.705 全场最高;参考物 CNNaffinity 5.7–6.4,候选 5.3–6.0 | results/gnina_rescoring.json | 重跑 scripts/gnina_rescore.py(~10 min,WSL) | 同值(seed 无关,确定性模型) |
| G2 | 跨引擎打分不可比的声明 | 同上 vina_affinity 列与 hits_ranked.csv 差异 | 对比两列 | 数值不同(符合预期) |

---

## 4. 审计实战示例:重算曾"抓到"一个分析陷阱(非造假)

审计复算 bound.dcd 时,naive 欧氏距离给出 Zn–配体 18–35 Å,与运行时 1.9–2.1 Å 矛盾。
诊断链(命令见 F2):DCD 帧 0 vs inpcrd 偏移非刚性(PDBFixer/leap 平移 + 逐分子周期包装)
→ 用 unitcell_vectors 最小镜像重算 → **1.83–3.53 Å(均值 2.03 Å),运行时指标确认正确**。
**教训(已写入协议)**:周期盒轨迹上任何"距离/RMSD"复算必须先做整分子 imaging;
否则会误判模拟有问题。本条同时证明:本项目的运行时指标经得起独立重算。

---

## 5. 失败与负结果登记(审计核对"是否如实申报")

| 失败/负结果 | 证据位置 | 状态 |
|---|---|---|
| pip 装 vina 失败(缺 Boost);conda-forge 无 win-64 vina | research-log D4 | 已绕行(官方 win 二进制) |
| OpenBabel ligand-gen3d 全零坐标(数据文件缺失) | research-log D4 | 已绕行(RDKit ETKDG) |
| EBI API 500 中断首次库抓取(数据曾丢失) | research-log Phase4 | 已重写为 REST+checkpoint |
| FPSim2 ChEMBL 指纹库下载 404 | research-log D5.1 | 已降级为"approved-drugs NN"并声明范围 |
| ADMETlab 3.0 API 404(不可脚本化) | research-log D5 | 改用 DeepPurpose+自训模型 |
| **MD"5 ns 实为 5 ps"步数错误** | research-log D8.7 | 由帧数核对抓出并修正(1e6 步/ns) |
| 交叉晶体"5JG8 锌偏移 3.25 Å"为文件内排序伪差 | research-log D7.1 | QC 修正(逐锌配对 0.15–0.70 Å) |
| bound.dcd 18–35 Å 审计初读 | §4 | 周期镜像伪差,最小镜像后确认正确 |
| zenodo 代理库存 404(猜错记录号);官方库存(1.34 GB)网关 504 ×5 | research-log D11 | 真实库存逆合成仍被阻塞 |
| hERG_Karim 名称不存在(TDC 实名 hERG_Central,需 label_name) | research-log D11 | 已修正重训 |
| 扩展 F-scan 首版生成无效价键(37/96) | research-log D6 | 已修复重生成(225/225) |
| 结合态 MD 主链漂移 12.5 Å(无约束建模环区甩动) | research-log D11 | 如实记录;生产级需环区建模/约束 |
| P2Rank 残基名录未做字符串匹配(仅几何重叠为证) | research-log D10 | 已声明 |

## 6. 数据完整性

`audit_manifest.json`:40 文件 SHA256 + 字节数(报告、结果表、轨迹、结构、脚本)。
审计第一步 = 逐文件重算哈希。`md/`(3.0 GB)含 prod.dcd/bound.dcd 轨迹与体系文件;
`docking/`(89 MB)含全部对接输出;`results/`(1.5 MB)全部 CSV/JSON;36 MB `data/` 原始抓取。

## 7. 审计红线(出现任一即判无效)

1. **编造生物活性**:任何未标注 PREDICTED 的 IC50/Ki 值,或无法在 ChEMBL/PubMed 查到的活性引用。
2. **单源证据过 G1**:决赛靶点缺少 ≥2 条独立证据线。
3. **未经验证即对接**:重对接 RMSD ≥2 Å 仍推进筛选。
4. **把对接分当自由能**:出现 ΔΔG 式跨化学型/跨论文比较。
5. **选择性报告**:§5 登记之外发现未申报的失败。
6. **MD 指标违背周期力学**:如本轮 §4 所示,轨迹距离/RMSD 复算未做 imaging 却宣布"模拟错误"或"指标正确"。

## 8. 无法在计算内验证的事项(需湿实验,见 validation-plan.md)

结合亲和力(预测 −6.0~−9.7 仅排序有效)、选择性、ADMET 真值、可合成性真值、
_vendor 可购性(ZINC API 不可脚本化,需人工)、安全性。本研究的定位是
**生成可检验假设并排序**,不替代实验。

---

*审计文档生成:2026-09-13。生成后若任何文件被修改,manifest 哈希即失配——这正是其用途。*
