# 论文结构提纲：Long Island 无家可归资源可达性与社会责任

建议英文题目：

**Beyond Resource Presence: Mapping Homelessness Resource Accessibility and Social Need on Long Island**

核心主线：

> **Resource presence is not enough. Social responsibility should be evaluated by whether resources are accessible and spatially aligned with need.**

中文主线：

> **有资源不等于资源有效。社会责任不能只看资源是否存在，还要看资源是否可达，是否与高需求地区空间对齐。**

---

## Abstract（约 200 字）

Long Island 的 homelessness 与 housing instability 经常被 New York City 的可见危机遮蔽，但 Nassau 与 Suffolk counties 同样存在显著的社会需求。本研究以 census tract 为尺度，整合 ACS 2022 five-year indicators、Nassau 与 Suffolk homelessness/basic-needs resources，以及 NYSED McKinney-Vento K-12 student homelessness data，评估资源是否与 poverty、rent burden、renter share 和综合 need score 空间对齐。方法上，研究使用 Enhanced Two-Step Floating Catchment Area (E2SFCA) 计算 15-minute drive 与 walk access，并构建 mismatch index 衡量 high need / low access areas。结果显示，drive mode 下 need 与 access 的 bivariate Moran’s I 为 +0.097 (p = 0.001)，显著但较弱；walk mode 下关系不显著。Access index 与主要 need factors 的 Pearson correlations 也较弱。研究说明，Long Island 并非没有资源，但资源存在不等于社会责任完成。若资源没有稳定对齐社会需求，那么资源系统仍需要从 accessibility、equity 和 local mismatch 的角度被重新评估。

---

## Keywords

homelessness; resource accessibility; Long Island; social responsibility; spatial mismatch; E2SFCA; suburban poverty; McKinney-Vento; GIS

---

## 1. Introduction

### 第 1 段：问题背景

写 homelessness 通常被想象为 New York City 或大城市中心区问题，但 Long Island 这类 suburban counties 也存在 housing instability、student homelessness 和 basic-needs insecurity。

### 第 2 段：研究问题

写本文不是问 Long Island “有没有资源”，而是问这些 homelessness/basic-needs resources 是否真正对齐高需求地区，是否可达，是否能够体现 social responsibility。

### 第 3 段：研究缺口

写现有资源地图往往只展示 facility locations，但较少评估 resource access 与社会需求之间的空间关系；因此 resource presence 与 resource effectiveness 之间存在研究缺口。

### 第 4 段：研究问题列表

写三个 research questions：

1. Long Island 的 housing-instability need 在 census tract 层面如何分布？
2. Homelessness/basic-needs resources 是否与高需求 tracts 空间对齐？
3. Drive access 与 walk access 是否产生不同的 mismatch pattern？

### 第 5 段：核心论点

写论文主张：Long Island 有可见资源，但资源 access 与 measured social need 之间只有弱对齐，因此 social responsibility 不能只通过资源是否存在来判断，而应通过 accessibility、equity 和 local mismatch 来评估。

### 第 6 段：论文贡献

写三点贡献：第一，提供 Long Island-wide tract-level resource mismatch analysis；第二，将 E2SFCA、Moran’s I、LISA 与 K-12 homelessness data 结合；第三，把 “resource presence is not enough” 作为评价 suburban homelessness response 的核心框架。

---

## 2. Literature Review

### 第 1 段：Spatial mismatch 理论

写 spatial mismatch 最初用于解释弱势群体居住地与就业机会之间的空间错位。本文借用这一逻辑，讨论 social need 与 homelessness-related resources 之间是否也存在空间错位。

建议引用：

Kain, J. F. (1968). Housing segregation, Negro employment, and metropolitan decentralization. *The Quarterly Journal of Economics, 82*(2), 175–197. https://doi.org/10.2307/1885893

Kain, J. F. (1992). The spatial mismatch hypothesis: Three decades later. *Housing Policy Debate, 3*(2), 371–460.

Ihlanfeldt, K. R., & Sjoquist, D. L. (1998). The spatial mismatch hypothesis: A review of recent studies and their implications for welfare reform. *Housing Policy Debate, 9*(4), 849–892.

### 第 2 段：Accessibility 与 E2SFCA

写 accessibility 不只是距离，而是 supply、demand 和 travel-time catchment 的组合。E2SFCA 提供了衡量资源可达性的 GIS 方法，本文将其从 health care accessibility 扩展到 homelessness/basic-needs resources。

建议引用：

Luo, W., & Wang, F. (2003). Measures of spatial accessibility to health care in a GIS environment: Synthesis and a case study in the Chicago region. *Environment and Planning B: Planning and Design, 30*(6), 865–884. https://doi.org/10.1068/b29120

Luo, W., & Qi, Y. (2009). An enhanced two-step floating catchment area (E2SFCA) method for measuring spatial accessibility to primary care physicians. *Health & Place, 15*(4), 1100–1107. https://doi.org/10.1016/j.healthplace.2009.06.002

### 第 3 段：Homelessness 与学生无家可归

写 homelessness 不只表现为 street homelessness 或 shelter count。McKinney-Vento student homelessness data 可以揭示 doubled-up families、temporarily housed students 和 suburban housing instability。

建议引用：

National Center for Homeless Education. (2025). *Student homelessness in America: School years 2020–21 to 2022–23*. U.S. Department of Education.

New York State Education Department. (n.d.). *McKinney-Vento homeless education*. https://www.nysed.gov/essa/mckinney-vento-homeless-education

SchoolHouse Connection. (2026). *Fact sheet: Educating children and youth experiencing homelessness*. https://schoolhouseconnection.org/article/fact-sheet-educating-children-and-youth-experiencing-homelessness

### 第 4 段：Resource presence vs. resource effectiveness

写 homelessness response 不能只用资源数量衡量。资源是否有效，还取决于是否位于高需求地区、是否可达、是否符合服务对象需求。这里要把 literature review 收回到本文主线：resource presence is not enough。

建议引用：

U.S. Department of Housing and Urban Development. (2023). *The 2023 Annual Homelessness Assessment Report (AHAR) to Congress: Part 1: Point-in-time estimates of homelessness in the U.S.* https://www.huduser.gov/portal/datasets/ahar/2023-ahar-part-1-pit-estimates-of-homelessness-in-the-us.html

United States Interagency Council on Homelessness. (n.d.). *Homelessness data & trends*. https://usich.gov/guidance-reports-data/data-trends

### 第 5 段：Literature review 收束

写已有文献分别讨论 spatial mismatch、accessibility measurement 和 homelessness data，但较少把这些放在 suburban homelessness resource systems 中一起分析。本文用 Long Island 作为案例，评估资源存在是否真正转化为空间上对齐需求的 resource access。

---

## 3. Data and Methodologies

### 3.1 Study area

This study focuses on Long Island, defined as Nassau County and Suffolk County, New York. Kings County and Queens County are excluded because they are part of New York City’s distinct shelter system, transit environment, density structure, and governance context. The unit of tract-level analysis is the 2022 Census tract. Water-only tracts were excluded from the analytical tract layer so that the map and spatial statistics reflect land-based communities rather than offshore or water-dominated geographies.

The suburban geography of Long Island is central to the research design. Unlike New York City, where public transit and dense service networks shape resource access, Long Island resource accessibility is strongly affected by automobile dependence, dispersed settlement patterns, and county-level service provision. For this reason, the analysis calculates access under two travel assumptions: a 15-minute drive and a 15-minute walk.

### 3.2 Data sources

The study integrates four main data sources. First, tract-level socioeconomic indicators are drawn from the 2022 ACS 5-year estimates. These indicators include poverty rate, rent burden rate, renter share, renter households, demographic counts, and median household income. Second, homelessness-related and basic-needs resource locations are compiled from Nassau and Suffolk resource datasets. The final resource layer includes food pantries, food banks, shelters, shelter intake points, outreach services, legal aid, housing-support services, behavioral-health services, public-benefits services, clinics, and other support resources.

Third, NYSED McKinney-Vento student homelessness data are used to construct a school-district layer of K-12 homelessness. These data report students identified as experiencing homelessness across school districts over the 2018-19, 2019-20, and 2020-21 school years. The layer is not used as a tract-level input to the mismatch index, because school districts and census tracts are different geographies. Instead, it is used as contextual evidence that housing instability and homelessness are empirically visible in suburban Long Island.

Fourth, TIGER/Line spatial boundary files are used for census tracts, county boundaries, and school district boundaries. The school district layer is clipped to land using TIGER AREAWATER files, so district polygons do not extend into bays, the Long Island Sound, or the Atlantic Ocean in the final map.

### 3.3 Resource classification

The resource layer contains 184 Nassau and Suffolk resource points. These resources are divided into two analytical categories. The first category, access-score resources, includes food pantries, food banks, shelters, shelter intake points, and outreach services. These 161 resources enter the E2SFCA access model because they represent direct basic-needs or homelessness-response resources that can plausibly affect immediate access.

The second category, context-only resources, includes legal aid, housing support, behavioral health, public benefits, clinics, and other support services. These 23 resources are retained in the map as contextual infrastructure but are not included in the access score. This distinction prevents the access model from treating all support services as equivalent while still making the broader resource landscape visible.

### 3.4 Need score construction

The tract-level need score is a composite measure designed to capture housing instability and socioeconomic vulnerability. It combines rent burden rate, poverty rate, renter share, and an eviction filing rate placeholder. Each component is standardized using z-scores, and the components are combined using equal weights. Higher need scores indicate tracts with greater measured vulnerability.

The eviction filing component is currently a placeholder because tract-level Long Island eviction filing data have not yet been integrated. Since current eviction filings are zero across tracts, this component does not contribute variation to the need score and is skipped in spatial diagnostics when constant. This limitation should be addressed before final publication if reliable tract-level eviction filing or shelter utilization data become available.

### 3.5 Access score and access index

Resource accessibility is measured using the Enhanced Two-Step Floating Catchment Area (E2SFCA) method. In this study, renter households are used as the demand base, while access-score resources are treated as supply points. For each travel mode, the model estimates the relationship between tract-level demand and reachable resources within a 15-minute catchment.

The raw E2SFCA result is retained as `access_score`. Because raw E2SFCA values are supply-demand ratios and can appear very small, the public-facing map also reports `access_index`, a 0-100 percentile rank of raw access within Long Island. Higher access index values indicate greater relative access compared with other Long Island tracts. The raw `access_score` is used for diagnostics and mismatch calculation, while `access_index` is used for interpretation and visualization.

### 3.6 Mismatch index

The mismatch index measures the gap between tract-level need and resource accessibility. It is defined as:

```text
mismatch_index = z(need_score) - z(access_score)
```

Higher values indicate tracts where measured need is high relative to modeled access. Lower or negative values indicate tracts where access is relatively high compared with need. This index should not be interpreted as a direct measure of homelessness or service failure. Rather, it is a spatial diagnostic that identifies areas where the resource system may not be proportionate to measured social need.

### 3.7 Spatial diagnostics

The analysis uses several spatial statistics to evaluate whether need, access, and mismatch are spatially clustered. Global Moran’s I is calculated for need score, access score, mismatch index, poverty rate, and rent burden rate. Bivariate Moran’s I between need and access is used as a validation gate for the central resource-alignment claim. If need and access are strongly positively related, the mismatch argument must be framed carefully; if they are weakly related or unrelated, the mismatch framing becomes more plausible.

Local Indicators of Spatial Association (LISA) are calculated for the mismatch index. In the map interpretation, HH clusters are treated as high need / low access areas, while LL clusters are treated as low need / high access areas. These local clusters are more actionable than countywide averages because they identify spatially coherent areas where resource placement, outreach, or transportation interventions may be considered.

Robustness checks are conducted across multiple spatial weight structures, including queen contiguity, K-nearest neighbors, and distance-band weights. These checks help determine whether clustering patterns depend heavily on one spatial weights assumption.

### 3.8 Correlation analysis

The right-side application panel and results memo include Pearson correlations between `access_index` and several factors: need score, poverty rate, rent burden rate, renter share, and mismatch index. These correlations are descriptive, not causal. The correlation between access index and mismatch index is expected to be strongly negative because access is part of the mismatch formula. Therefore, that relationship is used only as a sanity check. The more substantively important correlations are between access index and external need factors such as poverty, rent burden, renter share, and the need composite.

### 3.9 Methodological limitations

Several limitations should be noted. First, travel time currently uses haversine fallback unless OSRM routing endpoints are configured. Final publication should rerun the analysis with network-based drive and walk travel times. Second, resource points do not fully capture capacity, service hours, eligibility restrictions, language access, or hidden shelter infrastructure such as protected addresses and motel voucher systems. Third, the K-12 student homelessness layer is district-level and should not be interpreted as tract-level homelessness. Fourth, all correlations and spatial statistics are descriptive; they do not establish causality between resource placement and homelessness outcomes.

---

## 4. Results

### 第 1 段：数据规模与资源组成

写 665 tracts、184 resources、161 access-score resources、23 context-only resources、113 school districts。说明资源以 food resources 为主，资源类型并不均衡。  
建议放 Figure 1、Table 1、Table 4。

### 第 2 段：Need-access 全局关系

写 drive mode 下 bivariate Moran’s I = +0.097, p = 0.001；walk mode 下 I = -0.025, p = 0.121。说明 drive 下显著但弱，walk 下不显著。  
建议放 Table 2、Figure 3。

### 第 3 段：Local mismatch clusters

写 drive 下 HH = 172、LL = 128；walk 下 HH = 49、LL = 24、ns = 568。说明 local mismatch 在 drive assumption 下更明显。  
建议放 Figure 2、Figure 6、Table 3。

### 第 4 段：Access 与社会风险因素相关性

写 Access index 与 need score、poverty rate、rent burden、renter share 的相关性都较弱。说明资源 access 没有强烈跟随社会需求因素。  
建议放 Figure 4、Table 5。

### 第 5 段：County-level 背景

写 Nassau 平均 access index 高于 Suffolk，Suffolk mean_need 和 poverty 略高。说明 county-level 只是背景，重点仍是 tract-level mismatch。  
建议放 Table 10。

### 第 6 段：K-12 student homelessness

写 Long Island school districts 中约 7,657 名 K-12 students experiencing homelessness。列举 Hempstead、William Floyd、Brentwood、Longwood、Riverhead 等高值 districts。  
建议放 Figure 5、Table 8。

### 第 7 段：Mismatch distribution

写 drive 与 walk 的 mismatch distribution 不同，说明 resource adequacy 不能只靠 driving access 或 resource presence 判断。  
建议放 Figure 7。

---

## 5. Discussion

### 第 1 段：解释主结果

写 Long Island 资源存在，但与 measured social need 的空间对齐较弱，因此 resource presence 不能直接等同于 social responsibility。

### 第 2 段：解释 weak correlation

写弱相关说明资源分布可能受到历史位置、机构能力、土地成本、非营利网络、交通条件等因素影响，而不完全由 need-based planning 决定。

### 第 3 段：讨论 drive vs walk

写 drive access 下看似有一点对齐，但 walk access 下不显著，说明 car dependency 会改变资源可达性的意义。

### 第 4 段：讨论 K-12 homelessness

写 student homelessness 证明 Long Island 的 homelessness 不一定高度可见，但确实存在于家庭和学校系统中。

### 第 5 段：讨论政策含义

写结果可用于识别 high-need / low-access tracts，支持 outreach、mobile services、funding priorities、transportation support 和 resource planning。

### 第 6 段：讨论局限

写 haversine travel time、eviction placeholder、resource capacity/hours/eligibility 缺失、district-level K-12 data、descriptive not causal。

---

## 6. Conclusion

### 第 1 段：总结研究发现

写 Long Island 有资源，但 access 与 need factors 只有弱对齐。Drive relationship 显著但弱，walk relationship 不显著。

### 第 2 段：总结论文贡献

写本文贡献在于从 resource presence 转向 resource effectiveness，用 GIS accessibility 和 mismatch analysis 评价 suburban homelessness response。

### 第 3 段：实践意义

写政府、nonprofits、schools 和 community organizations 可以用结果识别 local mismatch 并优化资源补充。

### 第 4 段：未来研究

写未来应加入 real routing、eviction filings、resource capacity、service hours、eligibility、language access 和更细的 outcome data。

---

## 推荐放入正文的 Figures 和 Tables

最推荐 figures：

1. `figures/fig03_access_need_scatter.png`
2. `figures/fig02_lisa_counts.png`
3. `figures/fig06_drive_lisa_map.png`
4. `figures/fig05_top_k12_homeless_districts.png`

最推荐 tables：

1. `tables/table02_validation_gate.csv`
2. `tables/table03_lisa_counts.csv`
3. `tables/table05_access_correlations.csv`
4. `tables/table08_top_k12_homeless_districts.csv`

