"""HTML and APEX response parsers for agenda.sime.md."""

from __future__ import annotations

import html as html_lib
import logging
import re
import urllib.parse
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from bs4 import BeautifulSoup

from .exceptions import SimeAuthError
from .models import (
    SimeAbsenceSummary,
    SimeHomework,
    SimeLesson,
    SimeRecentGrade,
    SimeStudent,
    SimeStudentDashboardData,
    SimeSubjectGrades,
)

_LOGGER = logging.getLogger(__name__)
BASE_URL = "https://agenda.sime.md"


def get_input_value(soup: BeautifulSoup, *element_ids: str, default: str = "") -> str:
    for eid in element_ids:
        inp = soup.find("input", id=eid) or soup.find("input", attrs={"name": eid})
        if inp and inp.has_attr("value"):
            return inp["value"]
    return default


def parse_student_profile(soup: BeautifulSoup) -> SimeStudent:
    student_id = get_input_value(soup, "P1_ELEVE_ID")
    name = get_input_value(soup, "P1_ELEVE")
    birthdate = get_input_value(soup, "P1_BIRTH_DATE") or None
    uk = get_input_value(soup, "P1_ELEVE_UK", "P1_UK") or None
    classroom = get_input_value(soup, "P1_CLASS_NAME") or None
    school = get_input_value(soup, "P1_INSTITUTION_NAME") or None
    diriginte = get_input_value(soup, "P1_DIRIGINTE") or None
    address = get_input_value(soup, "P1_ADDRESS") or None
    study_year = get_input_value(soup, "P1_STUDY_YEAR") or None
    sem_str = get_input_value(soup, "P1_SEMESTER_ID", default="1")
    try:
        semester = int(sem_str)
    except ValueError:
        semester = 1

    return SimeStudent(
        id=student_id,
        name=name,
        birthdate=birthdate,
        permanent_code=uk,
        classroom=classroom,
        school_name=school,
        class_master=diriginte,
        address=address,
        study_year=study_year,
        current_semester=semester,
    )


def parse_recent_grades(html_snippet: str) -> List[SimeRecentGrade]:
    grades: List[SimeRecentGrade] = []
    if not html_snippet:
        return grades

    soup = BeautifulSoup(html_snippet, "html.parser")
    for li in soup.find_all("li"):
        date_span = li.find(class_="eval-date")
        disc_span = li.find(class_="eval-discipline")
        grade_span = li.find(class_="grade")

        if date_span and disc_span and grade_span:
            date_str = date_span.get_text(strip=True)
            subject = disc_span.get_text(strip=True).rstrip(":")
            grade_text = grade_span.get_text(strip=True)
            try:
                grade_val = float(grade_text.replace(",", "."))
                grades.append(
                    SimeRecentGrade(
                        date_str=date_str,
                        subject=subject,
                        grade=grade_val,
                    )
                )
            except ValueError:
                continue

    return grades


def parse_semester_grades_table(report_html: str) -> Dict[str, SimeSubjectGrades]:
    subjects: Dict[str, SimeSubjectGrades] = {}
    if not report_html:
        return subjects

    soup = BeautifulSoup(report_html, "html.parser")
    table = soup.find("table", class_=lambda c: c and "t-Report-report" in c)
    if not table:
        return subjects

    for tr in table.find_all("tr"):
        disc_td = tr.find("td", headers=lambda h: h and "DISCIPLINA" in h)
        eval_td = tr.find("td", headers=lambda h: h and "LISTA_EVALUATION" in h)
        med_td = tr.find("td", headers=lambda h: h and "MED_SEM" in h)

        if not disc_td:
            continue

        subject_name = disc_td.get_text(strip=True)
        if not subject_name:
            continue

        raw_grades: List[float] = []
        if eval_td:
            eval_text = eval_td.get_text(strip=True)
            for part in re.split(r"[,;]+", eval_text):
                cleaned = part.strip().replace(",", ".")
                if cleaned:
                    try:
                        raw_grades.append(float(cleaned))
                    except ValueError:
                        pass

        semester_grade: Optional[float] = None
        if med_td:
            med_text = med_td.get_text(strip=True).replace(",", ".")
            if med_text:
                try:
                    semester_grade = float(med_text)
                except ValueError:
                    pass

        entry = SimeSubjectGrades(
            subject=subject_name,
            grades=raw_grades,
            semester_grade=semester_grade,
        )
        entry.average = entry.calculate_average()
        subjects[subject_name] = entry

    return subjects


def parse_homework(html_snippet: str) -> List[SimeHomework]:
    homework_list: List[SimeHomework] = []
    if not html_snippet:
        return homework_list

    soup = BeautifulSoup(html_snippet, "html.parser")
    for li in soup.find_all("li"):
        due_span = li.find(class_="eval-date")
        disc_span = li.find(class_="eval-discipline")
        desc_span = li.find(class_="homework") or li.find(class_="desc")

        due_str = due_span.get_text(strip=True) if due_span else ""
        subject = disc_span.get_text(strip=True).rstrip(":") if disc_span else ""
        desc = desc_span.get_text(strip=True) if desc_span else li.get_text(strip=True)

        if subject or desc:
            homework_list.append(
                SimeHomework(
                    due_date_str=due_str,
                    subject=subject,
                    description=desc,
                )
            )

    return homework_list


def parse_absence_summary(soup: BeautifulSoup) -> SimeAbsenceSummary:
    def safe_int(val: str, default: int = 0) -> int:
        clean = re.sub(r"[^\d]", "", val)
        return int(clean) if clean else default

    pct_str = get_input_value(soup, "P1_RATA_PREZ")
    pct = safe_int(pct_str, 100)

    sem1_m = safe_int(get_input_value(soup, "P1_NR_ABS_SEM_1_M"))
    sem1_nm = safe_int(get_input_value(soup, "P1_NR_ABS_SEM_1_NM"))
    sem2_m = safe_int(get_input_value(soup, "P1_NR_ABS_SEM_2_M"))
    sem2_nm = safe_int(get_input_value(soup, "P1_NR_ABS_SEM_2_NM"))

    return SimeAbsenceSummary(
        presence_percent=pct,
        sem1_motivated=sem1_m,
        sem1_unmotivated=sem1_nm,
        sem2_motivated=sem2_m,
        sem2_unmotivated=sem2_nm,
    )


def parse_calendar_events(events: List[Dict[str, Any]]) -> List[SimeLesson]:
    lessons: List[SimeLesson] = []
    for ev in events:
        lesson_id = str(ev.get("id", ""))
        subject = ev.get("title", "Lecție")
        start_raw = ev.get("start", "")
        end_raw = ev.get("end", "")

        classroom = ev.get("className") or ev.get("room") or None
        teacher = ev.get("teacher") or ev.get("description") or None

        lessons.append(
            SimeLesson(
                id=lesson_id,
                subject=subject,
                start_time=start_raw,
                end_time=end_raw,
                classroom=str(classroom) if classroom else None,
                teacher=str(teacher) if teacher else None,
            )
        )
    return lessons


def parse_login_dialog_url(html: str, user_type: str) -> Optional[str]:
    # 1. Decode HTML entities and unicode escapes
    text = html_lib.unescape(html)
    try:
        text = text.encode("utf-8").decode("unicode_escape")
    except Exception:
        pass

    # Match APEX dialog or openUrl with login_desktop or login
    pattern = rf'(/ords/r/agenda/main/login[^"\'\)]*p101_user_type={user_type}[^"\'\)]*)'
    m = re.search(pattern, text, re.IGNORECASE)
    if m:
        raw_url = m.group(1).split("',")[0].split('",')[0].strip()
        return urllib.parse.urljoin(BASE_URL, raw_url)

    # Fallback to direct link
    soup = BeautifulSoup(html, "html.parser")
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "login" in href and f"p101_user_type={user_type}" in href.lower():
            return urllib.parse.urljoin(BASE_URL, href)

    return None


def parse_login_form_tokens(dialog_html: str) -> Dict[str, Any]:
    soup = BeautifulSoup(dialog_html, "html.parser")
    form = soup.find("form", id="wwvFlowForm") or soup.find("form")
    if not form:
        raise SimeAuthError("Could not find login form in dialog")

    action = form.get("action", "wwv_flow.accept")

    p_flow_id = get_input_value(soup, "p_flow_id", "pFlowId", default="104")
    p_flow_step_id = get_input_value(soup, "p_flow_step_id", "pFlowStepId", default="101")
    p_instance = get_input_value(soup, "p_instance", "pInstance")
    p_page_submission_id = get_input_value(soup, "p_page_submission_id", "pPageSubmissionId")
    p_reload_on_submit = get_input_value(soup, "p_reload_on_submit", "pReloadOnSubmit", default="S")

    salt = get_input_value(soup, "pSalt", "p_salt")
    protected = get_input_value(soup, "pPageItemsProtected", "p_protected")

    checksums: Dict[str, str] = {}
    for inp in soup.find_all("input"):
        if inp.has_attr("data-for") and inp.has_attr("value"):
            checksums[inp["data-for"]] = inp["value"]
        if inp.has_attr("id") and inp["id"].endswith("_CHECKSUM"):
            checksums[inp["id"].replace("_CHECKSUM", "")] = inp.get("value", "")

    # Regex fallback for checksums in JSON
    item_ck_pattern = re.compile(r'"name":"(P101_[^"]+)","value":"[^"]*","checksum":"([^"]+)"')
    for m in item_ck_pattern.finditer(dialog_html):
        checksums[m.group(1)] = m.group(2)

    return {
        "action": action,
        "p_flow_id": p_flow_id,
        "p_flow_step_id": p_flow_step_id,
        "p_instance": p_instance,
        "p_page_submission_id": p_page_submission_id,
        "p_reload_on_submit": p_reload_on_submit,
        "salt": salt,
        "protected": protected,
        "checksums": checksums,
    }


def parse_student_dashboard(html: str) -> SimeStudentDashboardData:
    soup = BeautifulSoup(html, "html.parser")
    p1_id = get_input_value(soup, "P1_ELEVE_ID")
    student = parse_student_profile(soup)

    recent_eval_raw = get_input_value(soup, "P1_LAST_3_EVAL_LIST")
    homework_raw = get_input_value(soup, "P1_HOMEWORK")
    absence_summary = parse_absence_summary(soup)

    eleve_ck = None
    ck_inp = soup.find("input", id="P1_ELEVE_ID_CHECKSUM") or soup.find("input", attrs={"data-for": "P1_ELEVE_ID"})
    if ck_inp:
        eleve_ck = ck_inp.get("value")

    salt = get_input_value(soup, "pSalt", "p_salt")
    protected = get_input_value(soup, "pPageItemsProtected", "p_protected")

    sem_configs = [
        (
            "sem1",
            r'apex\.widget\.report\.init\("sem1","([^"]+)",\{"pageItems":"#P1_ELEVE_ID","lazyLoading":true,"internalRegionId":"([^"]+)"\}',
        ),
        (
            "sem2",
            r'apex\.widget\.report\.init\("sem2","([^"]+)",\{"pageItems":"#P1_ELEVE_ID","lazyLoading":true,"internalRegionId":"([^"]+)"\}',
        ),
    ]
    sem_ajax_configs: Dict[str, Tuple[str, str]] = {}
    for sem_name, pattern in sem_configs:
        match = re.search(pattern, html)
        if match:
            ajax_id = match.group(1).encode().decode("unicode_escape")
            region_id = match.group(2)
            sem_ajax_configs[sem_name] = (ajax_id, region_id)

    return SimeStudentDashboardData(
        p1_id=p1_id,
        has_tree_nav=False,
        student=student,
        recent_eval_raw=recent_eval_raw,
        homework_raw=homework_raw,
        absence_summary=absence_summary,
        eleve_id=p1_id,
        eleve_ck=eleve_ck,
        salt=salt,
        protected=protected,
        sem_ajax_configs=sem_ajax_configs,
    )
