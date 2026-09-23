# Executive Summary

**Care Operations Analytics — Evidence-Based Findings**

*All data is synthetic and fictional. No real personal, healthcare, client, employee, or company data is used.*

---

### Context

A fictional Canadian care-services provider delivers in-home services funded by 6 funders across 25 cities. The dataset covers 300 clients, 110 workers, 7,500+ service visits, and 7,257 claims over 12 months (2024). This summary presents three prioritized findings derived from actual computed data.

---

### Finding 1: Funding Utilization Risk — High Priority

**Evidence**: Analysis of client-funder allocations reveals that some allocations approach or exceed 90% utilization. With $7,544.73 average allocation and approved claim spend tracked, multiple client-funder pairs are nearing their funding limits. The `funding_at_risk_count` KPI identifies allocations at or above the 90% threshold.

**Implication**: Budget overruns could lead to service disruption or unapproved spend, requiring immediate leadership attention.

**Recommendation**: Prioritize proactive funding review for allocations at ≥90% utilization. Reallocate resources or negotiate additional funding before limits are breached.

**Priority**: High

---

### Finding 2: Documentation Delays Driving Claim Rejections — High Priority

**Evidence**: Of 7,503 service visits, documentation delays are present in a significant subset. Claims linked to delayed documentation show higher rejection rates. The most common rejection reasons include "Late submission beyond SLA" (137 claims), "Missing documentation" (134 claims), and "Inconsistent hours" (130 claims).

**Implication**: Documentation process inefficiencies directly impact revenue cycle performance. Late submissions beyond funder SLA periods result in claim rejections and financial loss.

**Recommendation**: Implement documentation SLA monitoring with automated alerts. Target a 20% reduction in late submissions within the next quarter.

**Priority**: High

---

### Finding 3: Reconciliation Exceptions Requiring Analyst Triage — Medium Priority

**Evidence**: 300 reconciliation exceptions were generated, with approximately 35% remaining unresolved. High-priority exceptions represent significant financial exposure. The `open_exception_exposure` metric quantifies the total dollar value of open exceptions.

**Implication**: Unresolved exceptions create ongoing financial uncertainty and audit risk.

**Recommendation**: Establish a triage process to resolve high-priority exceptions first. Target resolution within 30 days for medium and 60 days for high priority items.

**Priority**: Medium

---

### Three Clear Recommendations

1. **Immediate**: Review all allocations at ≥90% utilization and develop reallocation plans.
2. **Short-term**: Deploy documentation SLA monitoring to reduce late submissions by 20%.
3. **Ongoing**: Implement a structured exception triage process based on priority and dollar exposure.

---

### How I Would Validate This With a Real Client

1. **Confirm data integrity**: Validate all synthetic mappings against real client systems.
2. **Interview stakeholders**: Confirm that the identified patterns match operational reality.
3. **A/B test interventions**: Pilot documentation SLA monitoring in one region before scaling.
4. **Review funding limits**: Verify allocation thresholds against actual funder contracts.
5. **Reconcile exception aging**: Cross-reference with actual reconciliation timelines.

---

### Assumptions and Limitations

- All data is synthetic and fictional; findings are illustrative only.
- Data spans a single year (2024); multi-year trends cannot be assessed.
- Worker capacity calculations assume consistent weekly capacity across seasons.
- Risk model uses logistic regression for interpretability, not maximum accuracy.
- Documentation delay calculations use generated delay days rather than actual SLA arithmetic.
- The risk model target definition combines rejection and reconciliation exception flags.

---

### Synthetic Data Disclaimer

**All data in this project is entirely synthetic and fictional.** No real personal, healthcare, client, employee, or company data is used. This project is intended for portfolio demonstration and analytics education purposes only.
