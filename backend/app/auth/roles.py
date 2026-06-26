

from enum import Enum


class Roles(str, Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    PRINCIPAL = "principal"
    DEPARTMENT_HEAD = "department_head"
    ADMIN = "admin"
    PROGRAMME = "programme"
    REGIONAL = "regional"
    ICT = "ict"

# class Roles:
#     STUDENT = "student"
#     TEACHER = "teacher"
#     SCHOOL_ADMIN = "school_admin"
#     VICE_PRINCIPAL = "vice_principal"
#     PRINCIPAL = "principal"
#     DEPARTMENT_HEAD = "department_head"
#     ICT = "ict_coordinator"
#     PROGRAMME = "programme_officer"
#     REGIONAL = "regional_monitor"
#     AI_SPECIALIST = "ai_specialist"