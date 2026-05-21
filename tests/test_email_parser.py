from __future__ import annotations

from job_alert_automation.email_parser import parse_email_content, parse_job_alert_body
from job_alert_automation.models import EmailMessageContent, EmailMessageMetadata


def test_parse_linkedin_labeled_fixture() -> None:
    body = """
    Title: Werkstudent AI Automation
    Company: Example Labs
    Location: Berlin
    URL: https://www.linkedin.com/jobs/view/123?utm_source=email
    Description: Build internal automation tools.
    """

    jobs = parse_job_alert_body("linkedin", body)

    assert len(jobs) == 1
    assert jobs[0].source == "linkedin"
    assert jobs[0].title == "Werkstudent AI Automation"
    assert jobs[0].company == "Example Labs"
    assert jobs[0].location == "Berlin"
    assert jobs[0].url == "https://www.linkedin.com/jobs/view/123?utm_source=email"
    assert jobs[0].short_description == "Build internal automation tools."


def test_parse_stepstone_position_block_fixture() -> None:
    body = """
    Werkstudent Softwareentwicklung
    Demo GmbH
    Potsdam
    https://www.stepstone.de/stellenangebote/123

    Senior Backend Engineer
    Other GmbH
    Berlin
    https://www.stepstone.de/stellenangebote/456
    """

    jobs = parse_job_alert_body("stepstone", body)

    assert [job.title for job in jobs] == ["Werkstudent Softwareentwicklung", "Senior Backend Engineer"]
    assert jobs[0].company == "Demo GmbH"
    assert jobs[0].location == "Potsdam"


def test_parser_ignores_common_linkedin_footer_noise() -> None:
    body = """
    Ähnliche Jobs wie Working Student Data Analysis

    Data Analysis Werkstudent:in (w/m/d)
    Enpal
    Berlin
    https://www.linkedin.com/jobs/view/123

    Alle Jobs anzeigen
    Weitere ähnliche Jobs
    Jobs für Working Student Data Analysis
    Jobs bei Enpal
    Jobs in Berlin
    Diese E-Mail ist an Minjian Li gerichtet.
    """

    jobs = parse_job_alert_body("linkedin", body)

    assert len(jobs) == 1
    assert jobs[0].title == "Data Analysis Werkstudent:in (w/m/d)"


def test_parse_indeed_labeled_fixture() -> None:
    body = """
    Job title: Junior Project Manager
    Employer: Example AG
    Job location: Hybrid Berlin
    Link: https://de.indeed.com/viewjob?jk=abc123&utm_campaign=email
    Summary: Coordinate digital transformation workstreams.
    """

    jobs = parse_job_alert_body("indeed", body)

    assert len(jobs) == 1
    assert jobs[0].title == "Junior Project Manager"
    assert jobs[0].company == "Example AG"
    assert jobs[0].location == "Hybrid Berlin"


def test_parser_ignores_common_indeed_header_noise() -> None:
    body = """
    Indeed Job-E-Mail - 30 IT Jobs in Berlin
    Jobs 1-17 von 30 neuen Jobs
    30 IT Jobs in Berlin - Jobs 1-15 von 30 neuen Jobs - Passende Ergebnisse auf Indeed anzeigen:

    Job title: Werkstudent AI
    Employer: Example GmbH
    Job location: Berlin
    Link: https://de.indeed.com/viewjob?jk=abc123
    """

    jobs = parse_job_alert_body("indeed", body)

    assert len(jobs) == 1
    assert jobs[0].title == "Werkstudent AI"


def test_parse_unknown_source_returns_empty_list() -> None:
    assert parse_job_alert_body("unknown", "Title: Something") == []


def test_parse_email_content_adds_message_metadata() -> None:
    content = EmailMessageContent(
        metadata=EmailMessageMetadata(
            user_id="minjian",
            gmail_message_id="msg-1",
            gmail_thread_id="thread-1",
            source="linkedin",
        ),
        text_body="""
        Title: Werkstudent Data
        Company: Data GmbH
        Location: Remote
        URL: https://www.linkedin.com/jobs/view/789
        """,
        body_hash="hash-1",
    )

    jobs = parse_email_content(content)

    assert len(jobs) == 1
    assert jobs[0].metadata["gmail_message_id"] == "msg-1"
    assert jobs[0].metadata["gmail_thread_id"] == "thread-1"
    assert jobs[0].metadata["body_hash"] == "hash-1"
