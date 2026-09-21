from django.forms import ModelForm, TextInput, Textarea, URLInput, Select, DateTimeInput, DateInput

from main.models import Experience, Education


class ExperienceForm(ModelForm):
    class Meta:
        model = Experience
        fields = [
            "title",
            "description",
            "category",
            "thumbnail",
            "ended_at",
        ]

        labels = {
            "title": "Judul Pengalaman",
            "description": "Deskripsi",
            "category": "Kategori",
            "thumbnail": "URL Gambar/Thumbnail",
            "ended_at": "Tanggal Selesai",
        }

        widgets = {
            "title": TextInput(
                attrs={
                    "placeholder": "Software Engineer Intern",
                    "maxlength": 255,
                }
            ),
            "description": Textarea(
                attrs={
                    "placeholder": "Ceritakan pengalamanmu",
                    "rows": 3,
                }
            ),
            "category": Select(),
            "thumbnail": URLInput(
                attrs={
                    "placeholder": "https://drive.google.com/thumbnail?id=...&sz=w1000",
                }
            ),
            "ended_at": DateTimeInput(
                attrs={
                    "type": "datetime-local",
                },
            ),
        }


class EducationForm(ModelForm):
    class Meta:
        model = Education
        fields = [
            "institution",
            "description",
            "started_at",
            "ended_at",
            "certificate_url",
        ]

        labels = {
            "institution": "Institusi",
            "description": "Deskripsi",
            "started_at": "Tanggal Mulai",
            "ended_at": "Tanggal Selesai",
            "certificate_url": "URL Sertifikat/Ijazah",
        }

        widgets = {
            "institution": TextInput(
                attrs={
                    "placeholder": "Universitas Indonesia",
                    "maxlength": 255,
                }
            ),
            "description": TextInput(
                attrs={
                    "placeholder": "S1 Sistem Informasi, Fakultas Ilmu Komputer",
                    "maxlength": 255,
                }
            ),
            "started_at": DateInput(
                attrs={
                    "type": "date",
                },
            ),
            "ended_at": DateInput(
                attrs={
                    "type": "date",
                },
            ),
            "certificate_url": URLInput(
                attrs={
                    "placeholder": "https://drive.google.com/thumbnail?id=...&sz=w1000",
                }
            ),
        }
