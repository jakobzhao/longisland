# Long Island 的隐藏需求与资源可达性

> 一个关于 suburban social responsibility 的空间分析：Long Island 不只是纽约市旁边的富裕郊区，它也有住房不稳定、食物不安全和学生 homelessness。真正的问题不是地图上有没有资源，而是资源是否被需要的人看见、到达、使用，并且是否有效。

## 1. 为什么这个题有社会价值

人们想到 homelessness 或 basic-needs resources，通常会先想到 New York City：街头无家可归、地铁、shelter、城市救助系统。但 Nassau 和 Suffolk 也有 homelessness，只是它更不显眼。

Long Island 的问题常常藏在郊区系统里：

- doubled-up households：家庭因为经济困难搬去亲戚或朋友家；
- motel vouchers：DSS 通过汽车旅馆安置家庭，而不是建一个可见的 shelter；
- school-mediated homelessness：学生 homelessness 通过学区数据显现；
- car-dependent access：资源可能开车可达，但步行不可达；
- dispersed support：法律援助、housing counseling、benefits、behavioral health 分散在不同机构里。

所以这个项目强调的是 **social responsibility**：社会资源不能只用“有没有”评价，而应该问“是否真的到达了最需要的人”。

## 2. 核心研究问题

这个项目把 Long Island 定义为 Nassau County + Suffolk County，不包括 Brooklyn 和 Queens，因为后两者属于 NYC，有完全不同的 shelter、transit、density 和治理系统。

核心问题是：

1. Long Island 的住房不稳定和 basic-needs 风险集中在哪里？
2. 食物、shelter/intake、outreach 等资源是否跟高需求地区对齐？
3. 如果把 access 从 15 分钟开车改成 15 分钟步行，结论会不会变？
4. 如果 homelessness 主要通过 motel vouchers、protected addresses、school data 等方式出现，传统 facility map 还够不够？

## 3. 数据和方法

当前 Long Island-wide pipeline 包括：

- 665 个 census tracts（已排除纯水域 tract）；
- 184 个 Nassau + Suffolk 资源点；
- 161 个进入 access score 的 food / shelter / intake / outreach 点；
- 23 个 context-only 支持资源，包括 legal aid、housing counseling、behavioral health、public benefits、clinics；
- 113 个 NYSED McKinney-Vento school district polygons。

Need score 使用 ACS 2022 5-year tract 指标：

- poverty rate；
- rent burden rate；
- renter share；
- eviction filing rate placeholder。

Access score 使用 E2SFCA，分别计算：

- 15-minute drive；
- 15-minute walk。

因为 E2SFCA 的原始值是 supply / demand ratio，数值会天然很小，界面不直接用它作为读者判断依据。地图中的 Access index 是把 raw access score 转换成 Long Island 内部 0-100 percentile rank：越接近 100，代表在 Long Island tracts 中相对 access 越高。

Mismatch index：

```text
mismatch_index = z(need_score) - z(access_score)
```

空间诊断包括：

- Global Moran's I；
- Bivariate Moran's I；
- LISA clusters；
- Getis-Ord Gi*；
- queen / KNN-5 / 3-mile band 稳健性检查。

## 4. 目前 Long Island-wide 结果

扩展到 Nassau + Suffolk 后，结果比 Nassau-only 更有研究张力。

Drive 模式：

- Bivariate Moran's I = `+0.097`
- p = `0.001`

这说明资源和 need 之间有显著但较弱的正关系。也就是说，不能简单说 Long Island 的资源完全没有跟着需求走；但这个关系不强，局部 mismatch 仍然重要。

Walk 模式：

- Bivariate Moran's I = `-0.025`
- p = `0.141`

这说明步行可达性下没有清晰空间关系。这个结果非常符合项目的社会价值主线：在 car-dependent suburb，地图上的资源存在不等于没有车的家庭真的能用。

McKinney-Vento 学生 homelessness 图层显示 Long Island 的问题远不只 Nassau 南岸。三年平均全岛约 7,657 名 K-12 学生被识别为 homeless，集中在 Hempstead、William Floyd、Brentwood、Longwood、Riverhead、Central Islip、Amityville、Sachem、Copiague、Farmingdale、Wyandanch 等学区。

## 5. 项目的主张

最强的论点不是“Long Island 没有资源”，而是：

**Resource presence is not social responsibility.**

资源点存在，只说明系统有服务；但社会责任要求更进一步：

- 高需求地区是否真的被覆盖？
- 没有车的人是否能到达？
- shelter 和 homelessness 是否被隐藏在 voucher、motel、school data 和 doubled-up households 里？
- 地图是否把不可见的脆弱群体误读成“不存在”？

这个项目的贡献就是把 social responsibility 变成可分析、可质疑、可优化的空间问题。

## 6. 下一步

最值得继续补强的方向：

- 给 Suffolk 资源做最终 re-geocoding；
- 加入真实 tract-level eviction filings；
- 自建 OSRM 或换成更真实的 routing；
- 增加 county filter 和 resource category filter；
- 对比 Nassau 与 Suffolk 的 resource density、walk access、mismatch clusters；
- 把 paper 和 website 的叙事统一成 Long Island-wide social responsibility story。
