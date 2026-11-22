"""Data models for agenda.sime.md integration."""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

class SimeAccountRole(str, Enum):
    """Account role on agenda.sime.md."""
    PARENT = "1"
    STUDENT = "2"

@dataclass
class SimeStudent:
    """Represents an enrolled student."""
    id: str
    name: str
    birthdate: Optional[str] = None
    permanent_code: Optional[str] = None
    school_name: Optional[str] = None
    classroom: Optional[str] = None
    class_master: Optional[str] = None
    address: Optional[str] = None
    study_year: Optional[str] = None
    current_semester: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class SimeRecentGrade:
    """A recent grade/evaluation entry."""
    date_str: str
    subject: str
    grade: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class SimeSubjectGrades:
    """Grades and average for a single school discipline."""
    subject: str
    grades: List[float] = field(default_factory=list)
    average: Optional[float] = None
    semester_grade: Optional[float] = None

    def calculate_average(self) -> Optional[float]:
        if not self.grades:
            return None
        return round(sum(self.grades) / len(self.grades), 2)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class SimeAbsenceSummary:
    """Cumulative and semester absences."""
    presence_percent: int = 100
    sem1_motivated: int = 0
    sem1_unmotivated: int = 0
    sem2_motivated: int = 0
    sem2_unmotivated: int = 0

    @property
    def total_motivated(self) -> int:
        return self.sem1_motivated + self.sem2_motivated

    @property
    def total_unmotivated(self) -> int:
        return self.sem1_unmotivated + self.sem2_unmotivated

    @property
    def total(self) -> int:
        return self.total_motivated + self.total_unmotivated

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["total_motivated"] = self.total_motivated
        d["total_unmotivated"] = self.total_unmotivated
        d["total"] = self.total
        return d

@dataclass
class SimeHomework:
    """A homework task."""
    due_date_str: str
    subject: str
    description: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class SimeLesson:
    """A scheduled class lesson in the school timetable."""
    id: str
    subject: str
    start_time: str
    end_time: str
    classroom: Optional[str] = None
    teacher: Optional[str] = None
    topic: Optional[str] = None
    order: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class SimeStudentData:
    """Aggregated snapshot for a student."""
    student: SimeStudent
    recent_grades: List[SimeRecentGrade] = field(default_factory=list)
    subjects: Dict[str, SimeSubjectGrades] = field(default_factory=dict)
    general_average: Optional[float] = None
    absence_summary: SimeAbsenceSummary = field(default_factory=SimeAbsenceSummary)
    homework: List[SimeHomework] = field(default_factory=list)
    timetable: List[SimeLesson] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "student": self.student.to_dict(),
            "recent_grades": [g.to_dict() for g in self.recent_grades],
            "subjects": {k: v.to_dict() for k, v in self.subjects.items()},
            "general_average": self.general_average,
            "absence_summary": self.absence_summary.to_dict(),
            "homework": [h.to_dict() for h in self.homework],
            "timetable": [t.to_dict() for t in self.timetable],
        }

@dataclass
class SimeStudentDashboardData:
    """Parsed items from student dashboard page."""
    p1_id: str
    has_tree_nav: bool
    student_urls: List[tuple[str, str]] = field(default_factory=list)
    student: SimeStudent = field(default_factory=lambda: SimeStudent(id="", name=""))
    recent_eval_raw: str = ""
    homework_raw: str = ""
    absence_summary: SimeAbsenceSummary = field(default_factory=SimeAbsenceSummary)
    eleve_id: str = ""
    eleve_ck: Optional[str] = None
    salt: str = ""
    protected: str = ""
    sem_ajax_configs: Dict[str, tuple[str, str]] = field(default_factory=dict)
