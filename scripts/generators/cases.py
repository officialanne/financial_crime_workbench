# a module to generate cases, investigation summaries and case activities

from faker_setup import fake

PRIORITIES = [
    "LOW",
    "MEDIUM",
    "HIGH",
    "CRITICAL",
]

CASE_STATUSES = [
    "OPEN",
    "OPEN",
    "IN_PROGRESS",
    "CLOSED",
]

ACTIVITY_TYPES = [
    "CASE_OPENED",
    "REVIEW",
    "NOTE_ADDED",
    "DOCUMENT_REQUEST",
    "ESCALATION",
    "CASE_CLOSED",
]

MODELS = [
    "TestModel-1",
    "TestModel-2",
    "TestModel-3",
]

PROMPTS = [
    "v1",
    "v2",
    "v3",
]


def generate_cases(
    connection,
    count,
    alert_ids,
    analyst_ids,
    starting_id=6001,
):
    case_ids = []
    case_records = []

    for index in range(count):
        case_id = starting_id + index
        alert_id = fake.random_element(alert_ids)
        analyst_id = fake.random_element(analyst_ids)
        priority = fake.random_element(PRIORITIES)
        status = fake.random_element(CASE_STATUSES)
        created_at = fake.date_between(start_date="-1y", end_date="today")
        closed_at = (
            fake.date_between(start_date=created_at, end_date="today")
            if status == "CLOSED"
            else None
        )

        case_records.append(
            (
                case_id,
                priority,
                status,
                analyst_id,
                created_at,
                closed_at,
                fake.sentence(nb_words=12),
                alert_id,
            )
        )
        case_ids.append(case_id)

    connection.executemany(
        """
        INSERT INTO Cases (
            CaseID, Priority, Status, AssignedAnalystID, CreatedAt, ClosedAt, Notes, AlertID
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        case_records,
    )

    return case_ids


def generate_investigation_summaries(connection, case_ids, starting_id=7001):
    records = []
    for index, case_id in enumerate(case_ids):
        summary_id = starting_id + index
        records.append(
            (
                summary_id,
                case_id,
                fake.paragraph(nb_sentences=3),
                fake.date_between(start_date="-1y", end_date="today"),
                fake.random_element(MODELS),
                fake.random_element(PROMPTS),
            )
        )

    connection.executemany(
        """
        INSERT INTO InvestigationSummary (
            SummaryID, CaseID, SummaryText, GeneratedAt, ModelName, PromptVersion
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        records,
    )

    return list(range(starting_id, starting_id + len(case_ids)))


def generate_case_activities(
    connection, count, case_ids, analyst_ids, starting_id=8001
):
    records = []
    for index in range(count):
        activity_id = starting_id + index
        records.append(
            (
                activity_id,
                fake.random_element(case_ids),
                fake.random_element(analyst_ids),
                fake.random_element(ACTIVITY_TYPES),
                None,
                fake.date_between(start_date="-1y", end_date="today"),
            )
        )

    connection.executemany(
        """
        INSERT INTO CaseActivity (
            ActivityID, CaseID, AnalystID, ActivityType, Description, CreatedAt
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        records,
    )

    return list(range(starting_id, starting_id + count))
