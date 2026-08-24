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

    for case_id in range(
        starting_id,
        starting_id + count,
    ):
        alert_id = fake.random_element(alert_ids)
        analyst_id = fake.random_element(analyst_ids)

        priority = fake.random_element(PRIORITIES)
        status = fake.random_element(CASE_STATUSES)

        created_at = fake.date_between(
            start_date="-1y",
            end_date="today",
        )

        if status == "CLOSED":
            closed_at = fake.date_between(
                start_date=created_at,
                end_date="today",
            )
        else:
            closed_at = None

        notes = fake.sentence(nb_words=12)

        connection.execute(
            """
            INSERT INTO Cases
                (
                    CaseID,
                    Priority,
                    Status,
                    AssignedAnalystID,
                    CreatedAt,
                    ClosedAt,
                    Notes,
                    AlertID
                )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                case_id,
                priority,
                status,
                analyst_id,
                created_at,
                closed_at,
                notes,
                alert_id,
            ),
        )

        case_ids.append(case_id)

    return case_ids


def generate_investigation_summaries(
    connection,
    case_ids,
    starting_id=7001,
):
    summary_ids = []

    for summary_id, case_id in zip(
        range(
            starting_id,
            starting_id + len(case_ids),
        ),
        case_ids,
    ):
        summary_text = fake.paragraph(nb_sentences=3)

        generated_at = fake.date_between(
            start_date="-1y",
            end_date="today",
        )

        model_name = fake.random_element(MODELS)
        prompt_version = fake.random_element(PROMPTS)

        connection.execute(
            """
            INSERT INTO InvestigationSummary
                (
                    SummaryID,
                    CaseID,
                    SummaryText,
                    GeneratedAt,
                    ModelName,
                    PromptVersion
                )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                summary_id,
                case_id,
                summary_text,
                generated_at,
                model_name,
                prompt_version,
            ),
        )

        summary_ids.append(summary_id)

    return summary_ids


def generate_case_activities(
    connection,
    count,
    case_ids,
    analyst_ids,
    starting_id=8001,
):
    activity_ids = []

    for activity_id in range(
        starting_id,
        starting_id + count,
    ):
        case_id = fake.random_element(case_ids)
        analyst_id = fake.random_element(analyst_ids)

        activity_type = fake.random_element(ACTIVITY_TYPES)

        description = fake.sentence(nb_words=10)

        created_at = fake.date_between(
            start_date="-1y",
            end_date="today",
        )

        connection.execute(
            """
            INSERT INTO CaseActivity
                (
                    ActivityID,
                    CaseID,
                    AnalystID,
                    ActivityType,
                    Description,
                    CreatedAt
                )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                activity_id,
                case_id,
                analyst_id,
                activity_type,
                description,
                created_at,
            ),
        )

        activity_ids.append(activity_id)

    return activity_ids
