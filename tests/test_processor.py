from bugfix_automator.models import JiraIssue
from bugfix_automator.processor import count_oo_occurrences, process_issues, select_time_in_minutes


def build_issue(**kwargs):
    base = {
        "key": "ABC-1",
        "summary": "Fix OO in parser",
        "status": "For Review",
        "assignee": "Jane",
        "description": "Investigate OO branch and OO fallback",
        "timespent_seconds": 600,
        "timeoriginalestimate_seconds": 1200,
    }
    base.update(kwargs)
    return JiraIssue(**base)


def test_select_time_in_minutes_prefers_timespent():
    issue = build_issue(timespent_seconds=600, timeoriginalestimate_seconds=1800)
    assert select_time_in_minutes(issue) == 10


def test_select_time_in_minutes_fallback_to_estimate():
    issue = build_issue(timespent_seconds=None, timeoriginalestimate_seconds=900)
    assert select_time_in_minutes(issue) == 15


def test_count_oo_occurrences_literal():
    assert count_oo_occurrences("OO xx OOOO") == 3


def test_process_issues_totals():
    issues = [
        build_issue(key="ABC-1", summary="OO", description=""),
        build_issue(key="ABC-2", summary="No tag", description="OO OO", timespent_seconds=120),
    ]

    report = process_issues(issues)

    assert len(report.issues) == 2
    assert report.total_tiempo_minutos == 12
    assert report.total_oo == 3
