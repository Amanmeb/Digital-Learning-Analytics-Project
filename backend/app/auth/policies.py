from app.auth.roles import Roles

ROLE_PERMISSIONS = {
    Roles.ADMIN: {
        "users.read",
        "users.write",
        "dashboard.read",
        "audit.read",
    },
    Roles.TEACHER: {
        "dashboard.read",
        "students.read",
    },
    Roles.STUDENT: {
        "profile.read",
        "courses.read",
    },
}