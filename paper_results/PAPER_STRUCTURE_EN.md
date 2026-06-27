# Paper Structure Outline: Homelessness Resource Accessibility and Social Need on Long Island

Suggested title:

**Beyond Resource Presence: Mapping Homelessness Resource Accessibility and Social Need on Long Island**

Core argument:

> **Resource presence is not enough. Social responsibility should be evaluated by whether resources are accessible and spatially aligned with need.**

---

## Abstract

Homelessness and housing instability on Long Island are often overshadowed by the more visible crisis in New York City, yet Nassau and Suffolk counties also contain substantial social need. This study evaluates whether homelessness-related and basic-needs resources on Long Island are spatially aligned with poverty, rent burden, renter share, and a composite tract-level need score. The analysis integrates 2022 ACS five-year census tract indicators, Nassau and Suffolk resource locations, and NYSED McKinney-Vento K-12 student homelessness data. Methodologically, the study uses the Enhanced Two-Step Floating Catchment Area (E2SFCA) method to calculate 15-minute drive and walk access, then constructs a mismatch index to identify high-need / low-access areas. Results show that the bivariate Moran's I between need and access is +0.097 under the drive model (p = 0.001), indicating a statistically significant but weak relationship; under the walk model, the relationship is not significant. Pearson correlations between access index and major need factors are also weak. These findings suggest that Long Island does have visible resources, but resource presence alone does not demonstrate social responsibility. If resources are not consistently aligned with social need, the resource system should be evaluated through accessibility, equity, and local mismatch.

---

## Keywords

homelessness; resource accessibility; Long Island; social responsibility; spatial mismatch; E2SFCA; suburban poverty; McKinney-Vento; GIS

---

## 1. Introduction

### Paragraph 1: Problem Context

Explain that homelessness is often imagined as a New York City or central-city issue, while suburban counties such as Long Island also experience housing instability, student homelessness, and basic-needs insecurity.

### Paragraph 2: Research Problem

State that the paper does not simply ask whether Long Island has homelessness-related or basic-needs resources. Instead, it asks whether these resources are spatially aligned with high-need areas, whether they are accessible, and whether their distribution supports a meaningful claim of social responsibility.

### Paragraph 3: Research Gap

Explain that many resource maps show facility locations but do not evaluate the spatial relationship between resource access and social need. This creates a gap between resource presence and resource effectiveness.

### Paragraph 4: Research Questions

List three research questions:

1. How is housing-instability need distributed at the census tract level on Long Island?
2. Are homelessness-related and basic-needs resources spatially aligned with high-need tracts?
3. Do drive access and walk access produce different mismatch patterns?

### Paragraph 5: Core Argument

State the central claim: Long Island has visible resources, but resource access is only weakly aligned with measured social need. Therefore, social responsibility should not be evaluated only by whether resources exist, but by whether they are accessible, equitable, and responsive to local mismatch.

### Paragraph 6: Contributions

Identify three contributions: first, a Long Island-wide tract-level resource mismatch analysis; second, a method combining E2SFCA, Moran's I, LISA, and K-12 homelessness data; third, the use of "resource presence is not enough" as a framework for evaluating suburban homelessness response.

---

## 2. Literature Review

### Paragraph 1: Spatial Mismatch Theory

Explain that spatial mismatch theory was first used to describe the separation between disadvantaged residential communities and employment opportunities. This paper extends that logic to ask whether social need and homelessness-related resources are spatially misaligned.

Suggested citations:

Kain, J. F. (1968). Housing segregation, Negro employment, and metropolitan decentralization. *The Quarterly Journal of Economics, 82*(2), 175-197. https://doi.org/10.2307/1885893

Kain, J. F. (1992). The spatial mismatch hypothesis: Three decades later. *Housing Policy Debate, 3*(2), 371-460.

Ihlanfeldt, K. R., & Sjoquist, D. L. (1998). The spatial mismatch hypothesis: A review of recent studies and their implications for welfare reform. *Housing Policy Debate, 9*(4), 849-892.

### Paragraph 2: Accessibility and E2SFCA

Explain that accessibility is not only distance, but a relationship among supply, demand, and travel-time catchments. E2SFCA provides a GIS-based method for measuring resource accessibility, and this study adapts it from health care accessibility to homelessness-related and basic-needs resources.

Suggested citations:

Luo, W., & Wang, F. (2003). Measures of spatial accessibility to health care in a GIS environment: Synthesis and a case study in the Chicago region. *Environment and Planning B: Planning and Design, 30*(6), 865-884. https://doi.org/10.1068/b29120

Luo, W., & Qi, Y. (2009). An enhanced two-step floating catchment area (E2SFCA) method for measuring spatial accessibility to primary care physicians. *Health & Place, 15*(4), 1100-1107. https://doi.org/10.1016/j.healthplace.2009.06.002

### Paragraph 3: Homelessness and Student Homelessness

Explain that homelessness is not limited to street homelessness or shelter counts. McKinney-Vento student homelessness data can reveal doubled-up families, temporarily housed students, and suburban housing instability.

Suggested citations:

National Center for Homeless Education. (2025). *Student homelessness in America: School years 2020-21 to 2022-23*. U.S. Department of Education.

New York State Education Department. (n.d.). *McKinney-Vento homeless education*. https://www.nysed.gov/essa/mckinney-vento-homeless-education

SchoolHouse Connection. (2026). *Fact sheet: Educating children and youth experiencing homelessness*. https://schoolhouseconnection.org/article/fact-sheet-educating-children-and-youth-experiencing-homelessness

### Paragraph 4: Resource Presence Versus Resource Effectiveness

Explain that homelessness response cannot be evaluated only by the number of resources. Resource effectiveness also depends on whether resources are located near high-need areas, whether they are reachable, and whether they meet the needs of target populations. This paragraph should bring the review back to the paper's core argument: resource presence is not enough.

Suggested citations:

U.S. Department of Housing and Urban Development. (2023). *The 2023 Annual Homelessness Assessment Report (AHAR) to Congress: Part 1: Point-in-time estimates of homelessness in the U.S.* https://www.huduser.gov/portal/datasets/ahar/2023-ahar-part-1-pit-estimates-of-homelessness-in-the-us.html

United States Interagency Council on Homelessness. (n.d.). *Homelessness data & trends*. https://usich.gov/guidance-reports-data/data-trends

### Paragraph 5: Literature Review Synthesis

Explain that existing scholarship addresses spatial mismatch, accessibility measurement, and homelessness data separately, but less often places them together in suburban homelessness resource systems. This paper uses Long Island as a case to evaluate whether resource presence actually becomes spatially aligned resource access.

---

## 3. Data and Methodologies

### 3.1 Study Area

This study focuses on Long Island, defined as Nassau County and Suffolk County, New York. Kings County and Queens County are excluded because they are part of New York City's distinct shelter system, transit environment, density structure, and governance context. The unit of tract-level analysis is the 2022 Census tract. Water-only tracts were excluded from the analytical tract layer so that the map and spatial statistics reflect land-based communities rather than offshore or water-dominated geographies.

The suburban geography of Long Island is central to the research design. Unlike New York City, where public transit and dense service networks shape resource access, Long Island resource accessibility is strongly affected by automobile dependence, dispersed settlement patterns, and county-level service provision. For this reason, the analysis calculates access under two travel assumptions: a 15-minute drive and a 15-minute walk.

### 3.2 Data Sources

The study integrates four main data sources. First, tract-level socioeconomic indicators are drawn from the 2022 ACS five-year estimates. These indicators include poverty rate, rent burden rate, renter share, renter households, demographic counts, and median household income. Second, homelessness-related and basic-needs resource locations are compiled from Nassau and Suffolk resource datasets. The final resource layer includes food pantries, food banks, shelters, shelter intake points, outreach services, legal aid, housing-support services, behavioral-health services, public-benefits services, clinics, and other support resources.

Third, NYSED McKinney-Vento student homelessness data are used to construct a school-district layer of K-12 homelessness. These data report students identified as experiencing homelessness across school districts over the 2018-19, 2019-20, and 2020-21 school years. The layer is not used as a tract-level input to the mismatch index, because school districts and census tracts are different geographies. Instead, it is used as contextual evidence that housing instability and homelessness are empirically visible in suburban Long Island.

Fourth, TIGER/Line spatial boundary files are used for census tracts, county boundaries, and school district boundaries. The school district layer is clipped to land using TIGER AREAWATER files, so district polygons do not extend into bays, the Long Island Sound, or the Atlantic Ocean in the final map.

### 3.3 Resource Classification

The resource layer contains 184 Nassau and Suffolk resource points. These resources are divided into two analytical categories. The first category, access-score resources, includes food pantries, food banks, shelters, shelter intake points, and outreach services. These 161 resources enter the E2SFCA access model because they represent direct basic-needs or homelessness-response resources that can plausibly affect immediate access.

The second category, context-only resources, includes legal aid, housing support, behavioral health, public benefits, clinics, and other support services. These 23 resources are retained in the map as contextual infrastructure but are not included in the access score. This distinction prevents the access model from treating all support services as equivalent while still making the broader resource landscape visible.

### 3.4 Need Score Construction

The tract-level need score is a composite measure designed to capture housing instability and socioeconomic vulnerability. It combines rent burden rate, poverty rate, renter share, and an eviction filing rate placeholder. Each component is standardized using z-scores, and the components are combined using equal weights. Higher need scores indicate tracts with greater measured vulnerability.

The eviction filing component is currently a placeholder because tract-level Long Island eviction filing data have not yet been integrated. Since current eviction filings are zero across tracts, this component does not contribute variation to the need score and is skipped in spatial diagnostics when constant. This limitation should be addressed before final publication if reliable tract-level eviction filing or shelter utilization data become available.

### 3.5 Access Score and Access Index

Resource accessibility is measured using the Enhanced Two-Step Floating Catchment Area (E2SFCA) method. In this study, renter households are used as the demand base, while access-score resources are treated as supply points. For each travel mode, the model estimates the relationship between tract-level demand and reachable resources within a 15-minute catchment.

The raw E2SFCA result is retained as `access_score`. Because raw E2SFCA values are supply-demand ratios and can appear very small, the public-facing map also reports `access_index`, a 0-100 percentile rank of raw access within Long Island. Higher access index values indicate greater relative access compared with other Long Island tracts. The raw `access_score` is used for diagnostics and mismatch calculation, while `access_index` is used for interpretation and visualization.

### 3.6 Mismatch Index

The mismatch index measures the gap between tract-level need and resource accessibility. It is defined as:

```text
mismatch_index = z(need_score) - z(access_score)
```

Higher values indicate tracts where measured need is high relative to modeled access. Lower or negative values indicate tracts where access is relatively high compared with need. This index should not be interpreted as a direct measure of homelessness or service failure. Rather, it is a spatial diagnostic that identifies areas where the resource system may not be proportionate to measured social need.

### 3.7 Spatial Diagnostics

The analysis uses several spatial statistics to evaluate whether need, access, and mismatch are spatially clustered. Global Moran's I is calculated for need score, access score, mismatch index, poverty rate, and rent burden rate. Bivariate Moran's I between need and access is used as a validation gate for the central resource-alignment claim. If need and access are strongly positively related, the mismatch argument must be framed carefully; if they are weakly related or unrelated, the mismatch framing becomes more plausible.

Local Indicators of Spatial Association (LISA) are calculated for the mismatch index. In the map interpretation, HH clusters are treated as high need / low access areas, while LL clusters are treated as low need / high access areas. These local clusters are more actionable than countywide averages because they identify spatially coherent areas where resource placement, outreach, or transportation interventions may be considered.

Robustness checks are conducted across multiple spatial weight structures, including queen contiguity, K-nearest neighbors, and distance-band weights. These checks help determine whether clustering patterns depend heavily on one spatial weights assumption.

### 3.8 Correlation Analysis

The right-side application panel and results memo include Pearson correlations between `access_index` and several factors: need score, poverty rate, rent burden rate, renter share, and mismatch index. These correlations are descriptive, not causal. The correlation between access index and mismatch index is expected to be strongly negative because access is part of the mismatch formula. Therefore, that relationship is used only as a sanity check. The more substantively important correlations are between access index and external need factors such as poverty, rent burden, renter share, and the need composite.

### 3.9 Methodological Limitations

Several limitations should be noted. First, travel time currently uses haversine fallback unless OSRM routing endpoints are configured. Final publication should rerun the analysis with network-based drive and walk travel times. Second, resource points do not fully capture capacity, service hours, eligibility restrictions, language access, or hidden shelter infrastructure such as protected addresses and motel voucher systems. Third, the K-12 student homelessness layer is district-level and should not be interpreted as tract-level homelessness. Fourth, all correlations and spatial statistics are descriptive; they do not establish causality between resource placement and homelessness outcomes.

---

## 4. Results

### Paragraph 1: Data Scale and Resource Composition

Write about the scale of the analysis: 665 tracts, 184 resources, 161 access-score resources, 23 context-only resources, and 113 school districts. Note that the resource inventory is dominated by food resources and that resource types are unevenly distributed. Suggested evidence: Figure 1, Table 1, and Table 4.

### Paragraph 2: Global Need-Access Relationship

Report that the bivariate Moran's I is +0.097 (p = 0.001) under the drive model and -0.025 (p = 0.121) under the walk model. Explain that the drive relationship is statistically significant but weak, while the walk relationship is not significant. Suggested evidence: Table 2 and Figure 3.

### Paragraph 3: Local Mismatch Clusters

Report that the drive model identifies 172 HH tracts and 128 LL tracts, while the walk model identifies 49 HH tracts, 24 LL tracts, and 568 non-significant tracts. Explain that local mismatch is more visible under the drive assumption. Suggested evidence: Figure 2, Figure 6, and Table 3.

### Paragraph 4: Access and Social-Risk Factors

Discuss that access index is only weakly correlated with need score, poverty rate, rent burden, and renter share. Explain that resource access does not strongly track measured social-need factors. Suggested evidence: Figure 4 and Table 5.

### Paragraph 5: County-Level Context

Compare Nassau and Suffolk at the county level. Note that Nassau has a higher mean access index, while Suffolk has slightly higher mean need and poverty. Clarify that county-level results provide background, but the main analysis is tract-level mismatch. Suggested evidence: Table 10.

### Paragraph 6: K-12 Student Homelessness

Report that Long Island school districts include approximately 7,657 K-12 students experiencing homelessness. Mention high-value districts such as Hempstead, William Floyd, Brentwood, Longwood, and Riverhead. Suggested evidence: Figure 5 and Table 8.

### Paragraph 7: Mismatch Distribution

Compare the drive and walk mismatch distributions. Explain that resource adequacy cannot be evaluated only through driving access or resource presence. Suggested evidence: Figure 7.

---

## 5. Discussion

### Paragraph 1: Interpretation of Main Result

Explain that Long Island has visible resources, but those resources are only weakly aligned with measured social need. Therefore, resource presence cannot be treated as equivalent to social responsibility.

### Paragraph 2: Meaning of Weak Correlation

Explain that weak correlations suggest resource distribution may be shaped by historical locations, organizational capacity, land cost, nonprofit networks, transportation conditions, and other factors rather than need-based planning alone.

### Paragraph 3: Drive Versus Walk

Discuss how drive access shows a weak relationship, while walk access is not significant. Explain that car dependency changes the meaning of resource accessibility in suburban contexts.

### Paragraph 4: K-12 Homelessness

Discuss how student homelessness shows that Long Island homelessness may be less visible than street homelessness, but still exists within family and school systems.

### Paragraph 5: Policy Implications

Explain that the results can help identify high-need / low-access tracts and support outreach, mobile services, funding priorities, transportation support, and resource planning.

### Paragraph 6: Limitations

Discuss limitations: haversine travel time, eviction placeholder, missing resource capacity/hours/eligibility data, district-level K-12 data, and descriptive rather than causal statistics.

---

## 6. Conclusion

### Paragraph 1: Summary of Findings

State that Long Island has resources, but access and need factors are only weakly aligned. The drive relationship is significant but weak, while the walk relationship is not significant.

### Paragraph 2: Contribution

Explain that the paper shifts the evaluation from resource presence to resource effectiveness, using GIS accessibility and mismatch analysis to evaluate suburban homelessness response.

### Paragraph 3: Practical Significance

Explain that public agencies, nonprofits, schools, and community organizations can use the results to identify local mismatch and guide resource supplementation.

### Paragraph 4: Future Research

State that future work should add real routing, eviction filings, resource capacity, service hours, eligibility restrictions, language access, and finer-grained outcome data.

---

## Recommended Figures and Tables for the Paper

Recommended figures:

1. `figures/fig03_access_need_scatter.png`
2. `figures/fig02_lisa_counts.png`
3. `figures/fig06_drive_lisa_map.png`
4. `figures/fig05_top_k12_homeless_districts.png`

Recommended tables:

1. `tables/table02_validation_gate.csv`
2. `tables/table03_lisa_counts.csv`
3. `tables/table05_access_correlations.csv`
4. `tables/table08_top_k12_homeless_districts.csv`

