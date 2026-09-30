from django.urls import path

from main.views import (
    show_main,
    show_experience,
    show_education,
    show_hobbies,
    create_experience,
    get_experience_json,
    delete_experience,
    create_education,
    update_education,
    get_education_json,
    delete_education,
    toggle_star_education,
    show_projects,
    create_project,
    create_project_ajax,
    get_projects_json,
    delete_project,
    toggle_star,
    register,
    login_user,
    logout_user,
)

app_name = "main"

urlpatterns = [
    path("", show_main, name="show_main"),
    path("experience/", show_experience, name="show_experience"),
    path("experience/add/", create_experience, name="create_experience"),
    path("experience/<uuid:experience_id>/delete/", delete_experience, name="delete_experience"),
    path("api/experience/", get_experience_json, name="get_experience_json"),
    path("education/", show_education, name="show_education"),
    path("education/add/", create_education, name="create_education"),
    path("education/<uuid:education_id>/edit/", update_education, name="update_education"),
    path("education/<uuid:education_id>/delete/", delete_education, name="delete_education"),
    path(
        "education/<uuid:education_id>/star/",
        toggle_star_education,
        name="toggle_star_education",
    ),
    path("api/education/", get_education_json, name="get_education_json"),
    path("hobbies/", show_hobbies, name="show_hobbies"),
    path("projects/", show_projects, name="show_projects"),
    path("projects/add/", create_project, name="create_project"),
    path("projects/add-ajax/", create_project_ajax, name="create_project_ajax"),
    path("projects/<uuid:project_id>/delete/", delete_project, name="delete_project"),
    path(
        "projects/<uuid:project_id>/star/",
        toggle_star,
        name="toggle_star",
    ),
    path("api/projects/", get_projects_json, name="get_projects_json"),
    path("register/", register, name="register"),
    path("login/", login_user, name="login"),
    path("logout/", logout_user, name="logout"),
]
