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
    path("api/education/", get_education_json, name="get_education_json"),
    path("hobbies/", show_hobbies, name="show_hobbies"),
]
