from django.shortcuts import render

from main.models import Experience


def show_main(request):
    context = {
        "name": "Karyn Isabelle Dexter",
        "npm": "2506656860",
        "study_program": "S1 Sistem Informasi",
        "bio": (
            "CS student at Universitas Indonesia for longer than planned, now a "
            "familiar (and slightly dreaded) face among Fasilkom students as a "
            "teaching assistant across several courses."
        ),
    }
    return render(request, "index.html", context)


def show_experience(request):
    context = {
        "name": "Karyn Isabelle Dexter",
        "experience_list": Experience.objects.all(),
    }
    return render(request, "experience.html", context)
