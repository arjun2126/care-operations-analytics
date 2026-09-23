# Executive Summary

**Care Operations Analytics**

*All data is synthetic and fictional. No real personal, healthcare, client, employee, or company data is used.*

---

### Results at a Glance

Computed from the processed datasets:

- **Total visits**: 7,500
- **Total claim dollars**: C$1,383,161.09
- **Approval rate**: 60.0%
- **Open exceptions**: 223 with C$1,653,941.11 exposure
- **Risk model**: Precision 0.632, Recall 0.299, F1 0.406, ROC-AUC 0.675

The model is a prioritization aid, not an automated decision system.

---

### Context

A fictional Canadian care-services provider delivers in-home services funded by 6 funders across 25 cities. The dataset covers 300 clients, 110 workers, 7,500+ service visits, and 7,257 claims over 12 months (2024). This summary presents three prioritized findings derived from actual computed data.

---

### Finding 1: Funding Utilization Risk — High Priority

Several client–funder allocations sit at or above 90% utilization. The `funding_at_risk_count` KPI on the dashboard flags them automatically. With an average allocation around $7,544.73, a full overrun on one allocation is a meaningful dollar amount.

If utilization keeps climbing, the likely outcome is service disruption or spend that no one approved. I'd review every allocation at ≥90% first, then reallocate or negotiate additional funding before the limit is actually reached.

---

### Finding 2: Documentation Delays Driving Claim Rejections — High Priority

Out of 7,503 service visits, a notable share of claims came with documentation delays, and those claims are rejected more often. The most common rejection reasons are "Late submission beyond SLA" (137 claims), "Missing documentation" (134 claims), and "Inconsistent hours" (130 claims).

Late submissions past a funder's SLA turn into rejected claims and lost revenue. I'd add monitoring on documentation SLAs with a target of cutting late submissions by roughly 20% in the next quarter.

---

### Finding 3: Reconciliation Exceptions Requiring Analyst Triage — Medium Priority

Of 300 reconciliation exceptions, about 35% were still unresolved. The `open_exception_exposure` metric puts the total dollar value of open exceptions into one number, so the impact is easy to see.

Unresolved exceptions mean financial uncertainty and audit risk. I'd set up a triage queue that works through high-priority exceptions first, with a goal of resolving medium-priority items within 30 days and high-priority items within 60.

---

### Three Clear Recommendations

1. **Immediate**: Review all allocations at ≥90% utilization and develop reallocation plans.
2. **Short-term**: Deploy documentation SLA monitoring to reduce late submissions by 20%.
3. **Ongoing**: Implement a structured exception triage process based on priority and dollar exposure.

---

### What I'd Verify With a Real Client

1. **Confirm data integrity**: Check the synthetic client maps against a real client's systems.
2. **Interview stakeholders**: Make sure the patterns here match their operational reality.
3. **A/B test interventions**: Pilot documentation SLA monitoring in one region before rolling it out.
4. **Review funding limits**: Verify the 90% threshold against actual funder contracts.
5. **Reconcile exception aging**: Cross-reference aging with their actual reconciliation timelines.

---

### Assumptions and Limitations

- All data is synthetic and fictional; findings are illustrative only.
- Data spans a single year (2024); multi-year trends cannot be assessed.
- Worker capacity calculations assume consistent weekly capacity across seasons.
- Risk model uses logistic regression for interpretability, not maximum accuracy.
- Documentation delay calculations use generated delay days rather than actual SLA arithmetic.
- The risk model target definition combines rejection and reconciliation exception flags.
