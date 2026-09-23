import os
import logging
from datetime import date, timedelta
from typing import List, Tuple

import pandas as pd
from faker import Faker

from src.config import config

logger = logging.getLogger(__name__)

fake = Faker("en_CA")
fake.seed_instance(config.random_seed)

CITIES = [
    "Toronto", "Mississauga", "Brampton", "Hamilton", "Ottawa",
    "London", "Winnipeg", "Vancouver", "Kitchener", "Windsor",
    "Oshawa", "Quebec City", "Surrey", "Edmonton", "Calgary",
    "Markham", "Burnaby", "Saskatoon", "Regina", "Moncton",
    "Barrie", "Kingston", "Thunder Bay", "Saint John", "Halifax",
]

SERVICE_TYPES = [
    "Personal Care", "Nursing Care", "Physiotherapy",
    "Occupational Therapy", "Speech Therapy", "Social Work",
    "Respite Care", "Meal Preparation", "Companion Services",
    "Palliative Care", "Rehabilitation", "Cognitive Support",
]

SERVICE_PROGRAMS = [
    "Home Care", "Long-Term Care Support", "Community Care Access",
    "Aging in Place", "Mental Health Support", "Post-Acute Recovery",
    "Pediatric Home Care", "Palliative Home Care",
]

WORKER_TYPES = ["Registered Nurse", "Personal Support Worker", "Physiotherapist",
                "Occupational Therapist", "Social Worker", "Speech-Language Pathologist",
                "Nurse Practitioner"]

WORKER_NAMES = [
    "Ahmed", "Priya", "Chen", "Omar", "Sophie", "Raj", "Maria", "James",
    "Elena", "Wei", "Fatima", "David", "Anita", "Carlos", "Yuki",
    "Michael", "Nadia", "Kenji", "Lisa", "Roberto",
]

SERVICE_PROGRAM_BY_CLIENT = {
    "Personal Care": 0.25, "Nursing Care": 0.20, "Physiotherapy": 0.15,
    "Occupational Therapy": 0.12, "Speech Therapy": 0.08,
    "Social Work": 0.06, "Respite Care": 0.07, "Meal Preparation": 0.03,
    "Companion Services": 0.02, "Palliative Care": 0.01,
    "Rehabilitation": 0.005, "Cognitive Support": 0.005,
}


def _weighted_choice(weights: dict) -> str:
    import random
    total = sum(weights.values())
    r = random.random() * total
    cumulative = 0
    for k, v in weights.items():
        cumulative += v
        if r <= cumulative:
            return k
    return list(weights.keys())[0]


def generate_clients() -> pd.DataFrame:
    rng = pd.Series(range(config.num_clients), name="index")
    data = {
        "client_id": [f"CL{i:05d}" for i in range(1, config.num_clients + 1)],
        "client_name": [fake.unique.first_name() + " " + fake.unique.last_name() for _ in range(config.num_clients)],
        "city": [fake.random_element(CITIES) for _ in range(config.num_clients)],
        "service_program": [_weighted_choice(SERVICE_PROGRAM_BY_CLIENT) for _ in range(config.num_clients)],
        "intake_date": [fake.date_between(start_date="-5y", end_date="today") for _ in range(config.num_clients)],
        "active_flag": [bool(fake.random_int(0, 1)) for _ in range(config.num_clients)],
    }
    df = pd.DataFrame(data)
    logger.info(f"Generated {len(df)} client records")
    return df


def generate_workers() -> pd.DataFrame:
    data = {
        "worker_id": [f"WK{i:04d}" for i in range(1, config.num_workers + 1)],
        "worker_name": [fake.random_element(WORKER_NAMES) + " " + fake.unique.last_name() for _ in range(config.num_workers)],
        "worker_type": [fake.random_element(WORKER_TYPES) for _ in range(config.num_workers)],
        "home_city": [fake.random_element(CITIES) for _ in range(config.num_workers)],
        "weekly_capacity_hours": [round(fake.random.uniform(20, 60), 1) for _ in range(config.num_workers)],
        "hire_date": [fake.date_between(start_date="-10y", end_date="today") for _ in range(config.num_workers)],
        "active_flag": [bool(fake.random_int(0, 1)) for _ in range(config.num_workers)],
    }
    df = pd.DataFrame(data)
    logger.info(f"Generated {len(df)} worker records")
    return df


def generate_funders() -> pd.DataFrame:
    funders_data = {
        "funder_id": [f"FN{i:03d}" for i in range(1, config.num_funders + 1)],
        "funder_name": [
            "Ontario Health Services Fund", "Canada Care Alliance",
            "Regional Accessibility Fund", "Provincial Home Care Program",
            "Community Health Partners", "Municipal Support Services",
        ][:config.num_funders],
        "funding_type": [
            "Provincial", "Federal", "Provincial", "Municipal",
            "Private Insurance", "Municipal",
        ][:config.num_funders],
        "claim_limit": [round(fake.random.uniform(500000, 5000000), 2) for _ in range(config.num_funders)],
        "documentation_sla_days": [fake.random_int(7, 30) for _ in range(config.num_funders)],
    }
    df = pd.DataFrame(funders_data)
    logger.info(f"Generated {len(df)} funder records")
    return df


def generate_funding_allocations(clients_df: pd.DataFrame, funders_df: pd.DataFrame) -> pd.DataFrame:
    import random
    rng = random.Random(config.random_seed)
    allocations = []
    for i in range(1, config.num_clients + 1):
        num_allocations = rng.randint(1, 3)
        for _ in range(num_allocations):
            allocations.append({
                "allocation_id": f"AL{i:05d}_{rng.randint(1, 99):02d}",
                "client_id": f"CL{i:05d}",
                "funder_id": f"FN{rng.randint(1, config.num_funders):03d}",
                "allocation_start_date": fake.date_between(start_date="-2y", end_date="today"),
                "allocation_end_date": fake.date_between(start_date="today", end_date="+2y"),
                "allocated_amount": round(rng.uniform(5000, 100000), 2),
                "approved_hours": round(rng.uniform(50, 1000), 1),
            })
    df = pd.DataFrame(allocations)
    df = df.drop_duplicates(subset=["allocation_id"])
    logger.info(f"Generated {len(df)} funding allocation records")
    return df


def generate_service_visits(clients_df: pd.DataFrame, workers_df: pd.DataFrame) -> pd.DataFrame:
    import random
    rng = random.Random(config.random_seed + 1)
    active_clients = clients_df[clients_df["active_flag"] == True]["client_id"].tolist()
    active_workers = workers_df[workers_df["active_flag"] == True]["worker_id"].tolist()
    start_date = date(2024, 1, 1)
    end_date = date(2024, 12, 31)
    num_visits = config.num_visits

    visits = []
    for i in range(1, num_visits + 1):
        visit_status = rng.choices(
            ["Completed", "Completed", "Completed", "Completed", "Cancelled", "Missed"],
            weights=[0.72, 0.12, 0.08, 0.05, 0.02, 0.01],
            k=1,
        )[0]
        scheduled_hours = round(rng.uniform(0.5, 6.0), 1)
        if visit_status == "Completed":
            completed_hours = round(rng.uniform(scheduled_hours * 0.8, scheduled_hours * 1.15), 1)
            doc_delay = rng.randint(-1, 14)
            doc_submitted = start_date + timedelta(days=rng.randint(0, 365))
        elif visit_status == "Cancelled":
            completed_hours = 0.0
            doc_delay = -1
            doc_submitted = pd.NaT
        else:
            completed_hours = 0.0
            doc_delay = -1
            doc_submitted = pd.NaT

        visits.append({
            "visit_id": f"VS{i:07d}",
            "client_id": rng.choice(active_clients) if active_clients else f"CL{rng.randint(1, config.num_clients):05d}",
            "worker_id": rng.choice(active_workers) if active_workers else f"WK{rng.randint(1, config.num_workers):04d}",
            "service_date": start_date + timedelta(days=rng.randint(0, 364)),
            "service_type": fake.random_element(SERVICE_TYPES),
            "scheduled_hours": scheduled_hours,
            "completed_hours": completed_hours,
            "hourly_rate": round(rng.uniform(25, 95), 2),
            "visit_status": visit_status,
            "documentation_submitted_date": doc_submitted if doc_submitted != pd.NaT else None,
            "documentation_delay_days": doc_delay if visit_status == "Completed" else None,
        })

    # Inject some invalid records intentionally
    for _ in range(rng.randint(3, 8)):
        visits.append({
            "visit_id": f"VS{num_visits + _ + 1:07d}",
            "client_id": None,
            "worker_id": None,
            "service_date": None,
            "service_type": None,
            "scheduled_hours": -1,
            "completed_hours": -1,
            "hourly_rate": None,
            "visit_status": "Completed",
            "documentation_submitted_date": None,
            "documentation_delay_days": None,
        })

    df = pd.DataFrame(visits)
    logger.info(f"Generated {len(df)} service visit records")
    return df


def generate_claims(service_visits_df: pd.DataFrame, funders_df: pd.DataFrame) -> pd.DataFrame:
    import random
    rng = random.Random(config.random_seed + 2)
    completed_visits = service_visits_df[
        (service_visits_df["visit_status"] == "Completed") &
        (service_visits_df["service_date"].notna())
    ].copy()
    active_funders = funders_df["funder_id"].tolist()
    claims = []
    used_claim_ids = set()

    for _, visit in completed_visits.iterrows():
        claim_status = rng.choices(
            ["Approved", "Rejected", "Pending Review"],
            weights=[0.60, 0.10, 0.30],
            k=1,
        )[0]
        claim_amount = round(visit["completed_hours"] * visit["hourly_rate"], 2) if visit["completed_hours"] > 0 else 0
        rejection_reason = None
        if claim_status == "Rejected":
            rejection_reason = rng.choice([
                "Missing documentation", "Duplicate candidate",
                "Exceeds funding limit", "Invalid service type",
                "Late submission beyond SLA", "Inconsistent hours",
            ])
        submitted_late = bool(rng.random() < 0.15)
        duplicate_candidate = bool(rng.random() < 0.05)
        claim_id = f"CM{rng.randint(1, 999999):06d}"
        while claim_id in used_claim_ids:
            claim_id = f"CM{rng.randint(1, 999999):06d}"
        used_claim_ids.add(claim_id)

        claims.append({
            "claim_id": claim_id,
            "visit_id": visit["visit_id"],
            "client_id": visit["client_id"],
            "funder_id": rng.choice(active_funders) if active_funders else "FN001",
            "claim_date": visit["service_date"] + timedelta(days=rng.randint(0, 30)),
            "claim_amount": claim_amount,
            "claim_status": claim_status,
            "rejection_reason": rejection_reason,
            "submitted_late_flag": submitted_late,
            "duplicate_candidate_flag": duplicate_candidate,
        })

    df = pd.DataFrame(claims)
    logger.info(f"Generated {len(df)} claim records")
    return df


def generate_reconciliation_exceptions(claims_df: pd.DataFrame) -> pd.DataFrame:
    import random
    rng = random.Random(config.random_seed + 3)
    exception_types = ["Amount Discrepancy", "Duplicate Claim", "Missing Documentation",
                       "Funding Exceeded", "Late Submission", "Authorization Gap"]
    priorities = ["High", "Medium", "Low"]
    exceptions = []
    num_exceptions = config.exception_count
    selected_claims = rng.sample(claims_df["claim_id"].tolist(), min(num_exceptions, len(claims_df)))

    for i, claim_id in enumerate(selected_claims):
        ex_type = rng.choice(exception_types)
        exceptions.append({
            "exception_id": f"EX{i:05d}",
            "claim_id": claim_id,
            "exception_type": ex_type,
            "detected_date": date(2024, 1, 1) + timedelta(days=rng.randint(0, 364)),
            "resolved_date": None if rng.random() < 0.35 else date(2024, 1, 1) + timedelta(days=rng.randint(0, 364)),
            "exception_status": rng.choice(["Open", "Open", "In Progress", "Resolved"]),
            "exception_amount": round(rng.uniform(100, 15000), 2),
            "priority": rng.choices(priorities, weights=[0.2, 0.5, 0.3], k=1)[0],
        })

    df = pd.DataFrame(exceptions)
    logger.info(f"Generated {len(df)} reconciliation exception records")
    return df


def generate_all_data() -> dict[str, pd.DataFrame]:
    clients = generate_clients()
    workers = generate_workers()
    funders = generate_funders()
    allocations = generate_funding_allocations(clients, funders)
    visits = generate_service_visits(clients, workers)
    claims = generate_claims(visits, funders)
    exceptions = generate_reconciliation_exceptions(claims)

    data = {
        "clients": clients,
        "workers": workers,
        "funders": funders,
        "funding_allocations": allocations,
        "service_visits": visits,
        "claims": claims,
        "reconciliation_exceptions": exceptions,
    }
    logger.info("All synthetic data generated")
    return data


def save_raw_data(data: dict[str, pd.DataFrame], output_dir: str = None) -> None:
    if output_dir is None:
        output_dir = config.raw_dir
    os.makedirs(output_dir, exist_ok=True)
    for name, df in data.items():
        path = os.path.join(output_dir, f"{name}.csv")
        df.to_csv(path, index=False)
        logger.info(f"Saved {len(df)} records to {path}")
