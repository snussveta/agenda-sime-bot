"""Async API client for agenda.sime.md."""

from __future__ import annotations

import asyncio
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Optional
import aiohttp

from .auth import BASE_URL, SimeAuthManager
from .exceptions import SimeAuthError, SimeConnectionError
from .models import (
    SimeAccountRole,
    SimeLesson,
    SimeStudentData,
    SimeSubjectGrades,
)
from .parser import (
    parse_calendar_events,
    parse_homework,
    parse_recent_grades,
    parse_semester_absences,
    parse_semester_grades_table,
    parse_student_dashboard,
)

_LOGGER = logging.getLogger(__name__)


class SimeClient:
    """Client for querying agenda.sime.md student data."""

    def __init__(
        self,
        username: str,
        password: str,
        role: SimeAccountRole = SimeAccountRole.STUDENT,
    ) -> None:
        self.username = username
        self.password = password
        self.role = role
        self.auth = SimeAuthManager(role=role)
        self._session: Optional[aiohttp.ClientSession] = None

    async def get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                cookie_jar=aiohttp.CookieJar(unsafe=True),
                timeout=aiohttp.ClientTimeout(total=30),
            )
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def authenticate(self) -> str:
        session = await self.get_session()
        return await self.auth.login(session, self.username, self.password)

    async def fetch_data(self) -> SimeStudentData:
        """Fetch all student data: profile, grades, homework, absences, timetable."""
        session = await self.get_session()

        if not self.auth.is_authenticated:
            await self.authenticate()

        target_url = self.auth.portal_url
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Referer": BASE_URL,
        }

        try:
            async with session.get(target_url, headers=headers) as resp:
                if resp.status != 200:
                    raise SimeConnectionError(f"HTTP {resp.status} loading dashboard {target_url}")
                html = await resp.text()
        except aiohttp.ClientError as err:
            raise SimeConnectionError(f"Network error loading student dashboard: {err}") from err

        if "P101_USERNAME" in html and "P101_PASSWORD" in html:
            self.auth.invalidate()
            raise SimeAuthError("Session expired, redirected to login page")

        dashboard = parse_student_dashboard(html)
        student = dashboard.student
        recent_grades = parse_recent_grades(dashboard.recent_eval_raw)
        homework = parse_homework(dashboard.homework_raw)
        absence_summary = dashboard.absence_summary

        subjects: dict[str, SimeSubjectGrades] = {}
        session_id = self.auth.session_id

        eleve_id = dashboard.eleve_id
        eleve_ck = dashboard.eleve_ck
        salt = dashboard.salt
        protected = dashboard.protected

        # Fetch semester grades reports
        if session_id and eleve_id and eleve_ck:
            ajax_url = f"{BASE_URL}/ords/wwv_flow.ajax?p_context=main/main-page/{session_id}"
            ajax_headers = {
                **headers,
                "Referer": target_url,
                "Origin": BASE_URL,
                "X-Requested-With": "XMLHttpRequest",
                "Accept": "text/html, */*; q=0.01",
            }

            for sem_name, (ajax_id, _region_id) in dashboard.sem_ajax_configs.items():
                r_obj = {
                    "salt": salt,
                    "pageItems": {
                        "itemsToSubmit": [{"n": "P1_ELEVE_ID", "v": eleve_id, "ck": eleve_ck}],
                        "protected": protected,
                        "rowVersion": "",
                        "formRegionChecksums": [],
                    },
                }

                payload = {
                    "p_flow_id": "104",
                    "p_flow_step_id": "1",
                    "p_instance": session_id,
                    "p_request": f"PLUGIN={ajax_id}",
                    "p_json": json.dumps(r_obj),
                }

                try:
                    async with session.post(ajax_url, data=payload, headers=ajax_headers) as rep_resp:
                        if rep_resp.status == 200:
                            rep_html = await rep_resp.text()
                            sem_subjects = parse_semester_grades_table(rep_html)
                            for subj_name, subj_data in sem_subjects.items():
                                if subj_name not in subjects:
                                    subjects[subj_name] = subj_data
                                else:
                                    subjects[subj_name].grades.extend(subj_data.grades)
                                    if subj_data.semester_grade is not None:
                                        subjects[subj_name].semester_grade = subj_data.semester_grade
                                    subjects[subj_name].average = subjects[subj_name].calculate_average()

                            # Parse semester absences from report table if dashboard items were 0
                            sem_m, sem_nm = parse_semester_absences(rep_html)
                            if sem_name == "sem1":
                                if sem_m > 0 and absence_summary.sem1_motivated == 0:
                                    absence_summary.sem1_motivated = sem_m
                                if sem_nm > 0 and absence_summary.sem1_unmotivated == 0:
                                    absence_summary.sem1_unmotivated = sem_nm
                            elif sem_name == "sem2":
                                if sem_m > 0 and absence_summary.sem2_motivated == 0:
                                    absence_summary.sem2_motivated = sem_m
                                if sem_nm > 0 and absence_summary.sem2_unmotivated == 0:
                                    absence_summary.sem2_unmotivated = sem_nm
                except Exception as err:
                    _LOGGER.warning("Failed to fetch %s grades report: %s", sem_name, err)

        # Calculate general average
        averages = [s.average for s in subjects.values() if s.average is not None]
        general_avg = round(sum(averages) / len(averages), 2) if averages else None

        # Fetch timetable (FullCalendar)
        timetable: list[SimeLesson] = []
        fc_match = re.search(
            r"apex\.widget\.fullCalendar\(\{.*?\"ajaxIdentifier\":\"([^\"]+)\"",
            html,
            re.DOTALL,
        )
        if fc_match and session_id and eleve_id:
            fc_ajax_id = fc_match.group(1).encode().decode("unicode_escape")
            now_dt = datetime.now()
            start_str = (now_dt - timedelta(days=7)).strftime("%Y%m%d000000")
            end_str = (now_dt + timedelta(days=21)).strftime("%Y%m%d235959")

            fc_obj = {
                "salt": salt,
                "pageItems": {
                    "itemsToSubmit": [{"n": "P1_ELEVE_ID", "v": eleve_id, "ck": eleve_ck}] if eleve_ck else [],
                    "protected": protected,
                    "rowVersion": "",
                    "formRegionChecksums": [],
                },
            }

            fc_payload = {
                "p_flow_id": "104",
                "p_flow_step_id": "1",
                "p_instance": session_id,
                "p_request": f"PLUGIN={fc_ajax_id}",
                "x01": "GET",
                "x02": start_str,
                "x03": end_str,
                "p_json": json.dumps(fc_obj),
            }

            ajax_url = f"{BASE_URL}/ords/wwv_flow.ajax?p_context=main/main-page/{session_id}"
            ajax_headers = {
                **headers,
                "Referer": target_url,
                "Origin": BASE_URL,
                "X-Requested-With": "XMLHttpRequest",
                "Accept": "application/json, text/javascript, */*; q=0.01",
            }

            try:
                async with session.post(ajax_url, data=fc_payload, headers=ajax_headers) as fc_resp:
                    if fc_resp.status == 200:
                        fc_data = await fc_resp.json(content_type=None)
                        if isinstance(fc_data, list):
                            timetable = parse_calendar_events(fc_data)
            except Exception as err:
                _LOGGER.warning("Failed to fetch timetable calendar events: %s", err)

        return SimeStudentData(
            student=student,
            recent_grades=recent_grades,
            subjects=subjects,
            general_average=general_avg,
            absence_summary=absence_summary,
            homework=homework,
            timetable=timetable,
        )
