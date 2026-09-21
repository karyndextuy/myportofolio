from django.contrib import messages
from django.core import serializers
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from main.forms import ExperienceForm, EducationForm
from main.models import Experience, Education, Hobby


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
    json_response = get_experience_json(request)
    experiences = serializers.deserialize(
        "json",
        json_response.content.decode("utf-8"),
    )
    experiences = [experience.object for experience in experiences]
    title_query = request.GET.get("title", "").strip()

    context = {
        "name": "Karyn Isabelle Dexter",
        "experience_list": experiences,
        "title_query": title_query,
    }
    return render(request, "experience.html", context)


def show_education(request):
    json_response = get_education_json(request)
    education_list = serializers.deserialize(
        "json",
        json_response.content.decode("utf-8"),
    )
    education_list = [education.object for education in education_list]
    institution_query = request.GET.get("institution", "").strip()

    context = {
        "name": "Karyn Isabelle Dexter",
        "education_list": education_list,
        "institution_query": institution_query,
    }
    return render(request, "education.html", context)


def show_hobbies(request):
    context = {
        "name": "Karyn Isabelle Dexter",
        "hobby_list": Hobby.objects.all(),
    }
    return render(request, "hobbies.html", context)


def create_experience(request):
    form = ExperienceForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Pengalaman baru berhasil ditambahkan!")
        return redirect("main:show_experience")

    context = {
        "name": "Karyn Isabelle Dexter",
        "form": form,
    }
    return render(request, "experience_form.html", context)


def get_experience_json(request):
    title_query = request.GET.get("title", "").strip()
    experiences = Experience.objects.all()

    if title_query:
        experiences = experiences.filter(title__icontains=title_query)

    experiences_json = serializers.serialize("json", experiences)
    return HttpResponse(experiences_json, content_type="application/json")


def delete_experience(request, experience_id):
    experience = get_object_or_404(Experience, pk=experience_id)

    if request.method == "POST":
        experience.delete()
        messages.success(request, "Pengalaman berhasil dihapus!")
        return redirect("main:show_experience")

    return redirect("main:show_experience")


def create_education(request):
    form = EducationForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Riwayat pendidikan baru berhasil ditambahkan!")
        return redirect("main:show_education")

    context = {
        "name": "Karyn Isabelle Dexter",
        "form": form,
        "page_title": "Add Education",
    }
    return render(request, "education_form.html", context)


def update_education(request, education_id):
    education = get_object_or_404(Education, pk=education_id)
    form = EducationForm(request.POST or None, instance=education)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Riwayat pendidikan berhasil diperbarui!")
        return redirect("main:show_education")

    context = {
        "name": "Karyn Isabelle Dexter",
        "form": form,
        "page_title": "Edit Education",
        "education": education,
    }
    return render(request, "education_form.html", context)


def get_education_json(request):
    institution_query = request.GET.get("institution", "").strip()
    education = Education.objects.all()

    if institution_query:
        education = education.filter(institution__icontains=institution_query)

    education_json = serializers.serialize("json", education)
    return HttpResponse(education_json, content_type="application/json")


def delete_education(request, education_id):
    education = get_object_or_404(Education, pk=education_id)

    if request.method == "POST":
        education.delete()
        messages.success(request, "Riwayat pendidikan berhasil dihapus!")
        return redirect("main:show_education")

    return redirect("main:show_education")
