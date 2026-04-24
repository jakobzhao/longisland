# Nassau County 的无家可归与社会安全网

> 一个富郡里的空间错配研究：食物网络在整体上已经追随需求，但无家可归的真实地理在一个不可点映射的郊区系统里只能通过学生数据间接显现。

---

## 1. 起点：为什么在 Nassau 研究 homelessness

Nassau County 的家庭收入中位数约 14 万美元，全美各 county 里长期排前 20，学区顶尖、税负沉重。但这张"富人郊区"的标签盖住了一条南北分化带：北岸 Great Neck / Sands Point / Old Westbury 是老钱，南岸的 Hempstead / Roosevelt / Freeport / Uniondale / Westbury 一线 2022 ACS 口径下贫困率和租金负担都显著高于县均值。

这个县内落差就是研究的起点 —— 不是"Nassau 穷不穷"，而是"穷在哪儿、服务追没追上"。

---

## 2. 核心学术问题

- **Q1（全局）** Nassau 现有的应急食物 / 庇护服务网络，在空间上是否**追随** need？如果不追随，mismatch 叙事才成立；如果追随，原定的"整县被遗漏"故事得放下。
- **Q2（局部）** 即便全局追随，是否仍存在**系统性的局部失配**？
- **Q3（模态）** 在一个典型的 car-dependent 郊区，有车和没车的家庭看到的是**同一张**可及性地图吗？
- **Q4（分布）** 当 HUD HIC 压制 shelter 地址、938 张 DSS motel voucher 本质上不可点映射时，我们怎么**量化无家可归在县内的地理分布**？

Q4 是整个项目里最方法论导向的问题 —— 它直接质疑"以设施为锚的空间分析"这一套标准做法在郊区的有效性。

---

## 3. 怎么做的

Pipeline 三段 + 一个补丁，全部 pre-computed，最终产物是一个无需后端的静态站点（[docs/](docs/)）。

### 3.1 Need 复合指标（notebook [01](notebooks/01_access_need_mismatch.py)）

基于 ACS 2022 5-year 的三项比率：

| 分量               | ACS 来源              | 含义                 |
| ------------------ | --------------------- | -------------------- |
| `rent_burden_rate` | B25070 007..010 / 001 | 付租金 ≥30% 家庭占比 |
| `poverty_rate`     | B17001 002 / 001      | 贫困率               |
| `renter_share`     | B25003 003 / 001      | 租客占比             |

每项按 Census Appendix-3 公式传播 90% MOE（proportion form，分母为负时 ratio fallback），z-score 后平均。小数量事件（潜在 eviction rate）用 Poisson-Gamma empirical Bayes 收缩至县均值。

### 3.2 Access score（E2SFCA）

Enhanced 2-Step Floating Catchment Area（Luo-Qi 2009），高斯衰减归一化到 f(0)=1、f(t₀)=0：

- 供给：98 个 Nassau facility（Island Harvest 89 + LI Cares 3 + RHY 2 + OSM 4，去重后）
- 需求基数：**租客户数 B25003_003**（不是总人口 —— housing instability 作用在租客而非业主）
- Catchment：**15 min drive**（主）+ **15 min walk**（对照）
- 行程时间：OSRM `/table`，公用节点限速时降级到 haversine + 模态速度假设

### 3.3 Mismatch 与空间诊断（notebook [02](notebooks/02_spatial_diagnostics.py)）

```
mismatch_index = z(need_score) - z(access_score)
```

- Global Moran's I × 3 种空间权重（queen / knn=5 / 3-mile band），跨 W 稳健 = I_std < 0.05 且所有 p < 0.05
- Bivariate Moran's I(need, access) → **validation gate** 判决
- LISA on mismatch_index → HH / LL / HL / LH / ns 标签
- Gi* on mismatch_index

### 3.4 无家可归分布层（notebook [03](notebooks/03_homeless_students.py)，Q4 专攻）

**NYSED McKinney-Vento 3-year SIRS (2018-19 → 2020-21)**，按学区：

- 源：NYSTEACHS 公开 XLSX，60 个 Nassau 县学区 / 特许学校行
- 维度：3 年的 duplicated-by-LEA total + 3-yr 平均
- 边界：TIGER 2023 NY 学区 shapefile（UNSD + ELSD + SCSD 三类，Nassau 共 57 个）
- 名称归一化后 name join，56/60 匹配到边界（剩 4 个 charter school 无几何、计数极小）
- 因 ELSD（小学区 K-6/8）和 SCSD（中学区 7-12）几何重叠，把 11 个 ELSD 按几何聚合进对应的 3 个 SCSD → 最终 **45 个非重叠 K-12 多边形**覆盖全县

**为什么选 McKinney-Vento 而不是 2020 Census DHC P5？**
P5 把 group quarters 人口计在 shelter 的物理位置。Nassau 只有 ~14 个 shelter、~1000 张床，P5 只会反映"shelter 建在哪"而非"无家可归的人在哪"；加上 Census differential privacy 对个位数计数加噪严重。McKinney-Vento 按学生实际入学地计，包含 doubled-up（因经济困难搬进亲戚家），正是郊区家庭型无家可归的主流形态。

**已知 caveat**：
1. 公开数据**不分列 unaccompanied youth**（CSPR 有此拆分但只州级），估算占全美 10-12%
2. "Duplicated by LEA" 口径 —— 学年中转学的学生会在两个 LEA 各计一次
3. 跨学区识别松紧不一（富学区倾向积极识别以争取 funding，移民密集学区则因 stigma 低识别）
4. NYSED 对 1-4 人的计数会用 "s" 压制，但 Nassau 60 行全部是明值

---

## 4. 核心发现

### 4.1 整县食物网络在有车前提下已经追随 need —— "整县 mismatch 叙事"被 validation gate 否决

| 模式         | Bivariate Moran's I(need, access) | p-sim | 判定                                      |
| ------------ | --------------------------------: | ----: | ----------------------------------------- |
| 15 min drive |                        **+0.274** | 0.001 | `mismatch-story-weak` —— 服务跟着 need 走 |
| 15 min walk  |                            +0.033 | 0.163 | `inconclusive` —— 无显著关系              |

这一度看起来像"坏消息"，但其实是**对的坏消息** —— 成熟的 emergency-food infrastructure（Island Harvest、Long Island Cares）本来就主动把合作网点布在高需求 municipality。"全县食物网络漏了穷人"这种廉价叙事站不住，得换问题。

### 4.2 局部仍锁定 70 个 HH tract —— 失配不是全局的，是**点状**的

LISA 在 mismatch_index 上识别出 **70 个 HH cluster tract**（自身高失配 + 邻居也高），穿越跨权重稳健检验。这 70 个 tract 集中落在南岸 Hempstead / Roosevelt / Uniondale / Freeport / Westbury 一线，构成可操作的"局部失配清单"。

全局信号虽弱，局部仍然能产出政策意义上的落点。

### 4.3 模态很重要 —— 有车家庭和没车家庭看到的是两张地图

drive 和 walk 诊断的差别不是**信号强度**问题，是**存在与否**的问题：drive 模式下 global Moran's I 显著，服务地形整体跟着 need；walk 模式下基本无信号。

在一个 car-dependent 郊区，access 是"有车"这个前提下的函数。没有车的家庭（ACS B25044 可识别）看到的食物网络，和我们主图展示的不是同一张。

### 4.4 "郊区无家可归系统本质不可点映射" —— 一个方法论发现

- Nassau HUD HIC 2024 的 ~14 个 shelter 程序，**地址全部压制**（HUD 政策 + DV 保护）
- **938 张 DSS motel voucher** 床位 = 分散采购，不是设施，从定义上就无法点映射
- 地图上最后只有 2 个 shelter dot（都是 youth agency RHY）

这不是数据收集的失败，是郊区无家可归系统**形态本身**的结果 —— 与 NYC 的集中式 shelter 模型相反，Nassau 是"中心化 DSS + 分散 motel"模型。推论：**facility-based spatial analysis 在郊区会系统性低估服务供给**。这本身是可发表的方法论论点。

### 4.5 McKinney-Vento 证据：无家可归地理分布**极度集中**

3 年平均 (2018-2021)，全县约 **2976 名 K-12 无家可归学生**。前 5 学区：

| 学区               | 3-yr 平均 |    份额 |
| ------------------ | --------: | ------: |
| **Hempstead UFSD** |  **1305** | **44%** |
| Farmingdale UFSD   |       191 |      6% |
| Roosevelt UFSD     |       177 |      6% |
| Uniondale UFSD     |       171 |      6% |
| Freeport UFSD      |       170 |      6% |
| **Top 5 合计**     |  **2014** | **68%** |

**Hempstead 一个学区吸走全县近一半。** 而这 5 个学区在地理上与 §4.2 的 LISA HH tract 高度重合 —— 两套**完全独立**的数据（上游 ACS 风险代理 + 下游 NYSED 学校系统确诊）在空间上互相验证了同一条"风险管道"。这种 cross-source 一致性是任何单源分析都给不了的。

---

## 5. 故事合成

把四条发现合起来，这张图真正在讲的事说白了是这样：

**开车去领食物这件事，整个县已经做得挺到位了。** 食物分发点、食物银行大多就开在穷人集中的地方 —— 不用我们来指出"哪里被遗漏"，机构自己早就跟着需求走了。

**但如果你没车，这张图就不成立了。** Nassau 是典型的郊区，15 分钟步行能到的服务点少得多。需求和服务在"有车"这个前提下对得上，一旦拿掉这个前提就对不上了。

**至于无家可归的人，这个县几乎没有真正意义上的"庇护所"给你看。** Nassau 不像纽约市那样建楼、挂牌，而是把整个系统外包给汽车旅馆 —— 县政府用 voucher 直接付钱，把家庭安置到散落在各处的 motel 房间里。将近 1000 张床，但不在任何设施名录里，地图上也找不到他们。

**那这些家庭到底住在哪？两条完全独立的数据指向同一个答案：**

- 一条来自经济指标：把租金负担、贫困率、租客占比叠在一起看，南岸有一条密集的"高风险带"（就是 §4.2 的 70 个 tract）
- 另一条来自学校：全县无家可归的 K-12 学生，光 Hempstead 一个学区就占近一半，加上 Roosevelt、Uniondale、Freeport、Farmingdale，前 5 个学区占全县 2/3

两条线用的是完全不同的数据源，但画出来是同一条带 —— 南岸那一条。这种来自不同系统的相互印证，是任何单一数据都给不出的说服力。

**所以如果要做点什么，重点不是"再加几个食物点"。** 那些已经开在对的地方了。真正缺的是两件事：

1. **让没车的家庭也能到** —— 公交接驳、送餐到户、流动分发车
2. **让散落在 motel 里的家庭在空间上可见** —— 现在连他们住哪都不知道，服务怎么可能覆盖

这两件事恰好都是"在地图上标设施"那套标准做法看不到的，但在 Nassau 这种富郊区里才是真正卡脖子的地方。

Nassau County looks like a wealthy suburb on paper, but it hides a sharp north-south gradient of housing stress. Our spatial analysis finds that the county's emergency-food network, when measured by a 15-minute drive, already tracks where need is concentrated — the "underserved county" story does not hold up globally. What does hold up is local: seventy census tracts along the south shore cluster as high-mismatch hotspots, and the same geography is independently confirmed by K-12 homeless-student counts, where Hempstead alone accounts for nearly half the county's identified cases and the top five districts for two-thirds. Meanwhile, the shelter system itself is structurally invisible on any facility map: Nassau houses the homeless primarily through ~1,000 dispersed DSS motel-voucher beds rather than purpose-built shelters. The binding constraint in a suburb like Nassau is therefore not service siting but two things standard facility-based analysis cannot see — transport access for car-less households, and the spatial visibility of a voucher-dispersed shelter system.

---

## 6. 未解 / 下一步

| 方向                        | 说明                                                                     |
| --------------------------- | ------------------------------------------------------------------------ |
| Eviction filings 按 tract   | 结构化公开源不存在；Eviction Lab 在 Nassau 只到县级。下一步：FOIL NY OCA |
| HUD HIC 14 shelter 真实地址 | FOIL Nassau DSS                                                          |
| OSRM 行程时间               | 公用节点限速，主 run 降级到 haversine → 自建 OSRM 实例                   |
| 系统脆弱性（Q5）            | Leave-one-facility-out 敏感度尚未实施                                    |
| NYSED 数据滚动              | 目前公开只到 2020-21，等 NYSTEACHS 发布 2021-24                          |
| Unaccompanied youth 拆分    | CSPR 只发州级，district 级需要 FOIL NYSED                                |

---

**数据与代码**
- Pipeline：[notebooks/](notebooks/) 三个 notebook + [run_pipeline.py](run_pipeline.py)
- 处理后数据：[data/processed/](data/processed/)
- 前端静态站点：[docs/](docs/)（GitHub Pages 即可部署，无需 Node）
- 方法论细节：[README.md](README.md)
