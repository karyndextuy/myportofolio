import json

from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from main.models import Experience, Education, Hobby
from main.roles import EDITOR_GROUP_NAME


class MainTest(TestCase):
    def setUp(self):
        self.experience = Experience.objects.create(
            title="Asisten Dosen PBP",
            description="Membantu mahasiswa memahami pengembangan web.",
            category="part-time",
        )

    def test_main_url_is_accessible(self):
        response = self.client.get(reverse("main:show_main"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "index.html")
        self.assertNotContains(response, self.experience.title)
        self.assertContains(response, f'href="{reverse("main:show_experience")}"')

    def test_nonexistent_page_returns_404(self):
        response = self.client.get("/halaman-yang-tidak-ada/")

        self.assertEqual(response.status_code, 404)

    def test_experience_model(self):
        self.assertEqual(str(self.experience), "Asisten Dosen PBP")
        self.assertEqual(self.experience.category, "part-time")
        self.assertTrue(self.experience.is_ongoing)

    def test_experience_page(self):
        response = self.client.get(reverse("main:show_experience"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "experience.html")
        self.assertContains(response, self.experience.title)
        self.assertContains(response, self.experience.description)
        self.assertContains(response, "Part-Time")
        self.assertContains(response, "Sedang berlangsung")
        self.assertContains(response, f'href="{reverse("main:show_main")}"')

    def test_empty_experience_page(self):
        Experience.objects.all().delete()
        response = self.client.get(reverse("main:show_experience"))

        self.assertContains(response, "Belum ada pengalaman yang ditambahkan.")

    def test_completed_experience(self):
        self.experience.ended_at = timezone.now()
        self.experience.save()
        response = self.client.get(reverse("main:show_experience"))

        self.assertFalse(self.experience.is_ongoing)
        self.assertContains(response, "Selesai")
        self.assertNotContains(response, "Sedang berlangsung")


class EducationTest(TestCase):
    def setUp(self):
        self.education = Education.objects.create(
            institution="Universitas Indonesia",
            description="S1 Sistem Informasi, Fakultas Ilmu Komputer.",
            started_at="2025-01-01",
        )

    def test_education_url_is_accessible(self):
        response = self.client.get(reverse("main:show_education"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "education.html")

    def test_education_page_shows_data(self):
        response = self.client.get(reverse("main:show_education"))

        self.assertContains(response, self.education.institution)
        self.assertContains(response, self.education.description)
        self.assertContains(response, "Sekarang")

    def test_empty_education_page(self):
        Education.objects.all().delete()
        response = self.client.get(reverse("main:show_education"))

        self.assertContains(response, "Belum ada riwayat pendidikan yang ditambahkan.")

    def test_completed_education(self):
        self.education.ended_at = timezone.now()
        self.education.save()
        response = self.client.get(reverse("main:show_education"))

        self.assertFalse(self.education.is_ongoing)
        self.assertNotContains(response, "Sekarang")


class HobbyTest(TestCase):
    def setUp(self):
        self.hobby = Hobby.objects.create(
            name="Cycling",
            icon="\U0001F6B4",
            description="Menikmati akhir pekan dengan bersepeda santai keliling kota.",
        )

    def test_hobbies_url_is_accessible(self):
        response = self.client.get(reverse("main:show_hobbies"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "hobbies.html")

    def test_hobbies_page_shows_data(self):
        response = self.client.get(reverse("main:show_hobbies"))

        self.assertContains(response, self.hobby.name)
        self.assertContains(response, self.hobby.description)

    def test_empty_hobbies_page(self):
        Hobby.objects.all().delete()
        response = self.client.get(reverse("main:show_hobbies"))

        self.assertContains(response, "Belum ada hobi yang ditambahkan.")


class EducationAuthorizationTest(TestCase):
    """Hak akses empat peran pada Education: pengunjung, pengguna biasa,
    Editor, dan pemilik portofolio (superuser)."""

    password = "S3cure-pass-123"

    def setUp(self):
        self.education = Education.objects.create(
            institution="Universitas Indonesia",
            description="S1 Sistem Informasi",
            started_at="2025-01-01",
        )
        self.regular = User.objects.create_user("sasha", password=self.password)
        self.editor = User.objects.create_user("rian", password=self.password)
        self.editor.groups.add(Group.objects.get(name=EDITOR_GROUP_NAME))
        self.owner = User.objects.create_superuser("karyn", password=self.password)

        self.create_url = reverse("main:create_education")
        self.update_url = reverse("main:update_education", args=[self.education.id])
        self.delete_url = reverse("main:delete_education", args=[self.education.id])
        self.star_url = reverse("main:toggle_star_education", args=[self.education.id])

    def login_as(self, user):
        self.client.login(username=user.username, password=self.password)

    def valid_education_data(self, institution):
        return {"institution": institution, "description": "", "started_at": "2020-01-01"}

    def test_editor_group_exists_after_migration(self):
        self.assertTrue(Group.objects.filter(name=EDITOR_GROUP_NAME).exists())

    def test_anonymous_can_read_but_is_redirected_to_login_for_actions(self):
        response = self.client.get(reverse("main:show_education"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Tambah Pendidikan")
        self.assertNotContains(response, ">Edit<")
        self.assertNotContains(response, "Ya, Hapus")

        for url in [self.create_url, self.update_url]:
            self.assertRedirects(self.client.get(url), f"/login/?next={url}")
        for url in [self.delete_url, self.star_url]:
            self.assertRedirects(self.client.post(url), f"/login/?next={url}")

        self.assertTrue(Education.objects.filter(pk=self.education.pk).exists())
        self.assertEqual(self.education.starred_by.count(), 0)

    def test_regular_user_gets_403_on_create_update_delete(self):
        self.login_as(self.regular)

        self.assertEqual(self.client.get(self.create_url).status_code, 403)
        self.assertEqual(self.client.get(self.update_url).status_code, 403)
        self.assertEqual(
            self.client.post(self.create_url, self.valid_education_data("Baru")).status_code, 403
        )
        self.assertEqual(
            self.client.post(self.update_url, self.valid_education_data("Diubah")).status_code, 403
        )
        self.assertEqual(self.client.post(self.delete_url).status_code, 403)

        self.education.refresh_from_db()
        self.assertEqual(self.education.institution, "Universitas Indonesia")
        self.assertEqual(Education.objects.count(), 1)

    def test_regular_user_sees_only_star_button(self):
        self.login_as(self.regular)
        response = self.client.get(reverse("main:show_education"))

        self.assertContains(response, "button-star")
        self.assertNotContains(response, "Tambah Pendidikan")
        self.assertNotContains(response, ">Edit<")
        self.assertNotContains(response, "Ya, Hapus")

    def test_editor_can_update_but_not_create_or_delete(self):
        self.login_as(self.editor)

        self.assertEqual(self.client.get(self.update_url).status_code, 200)
        response = self.client.post(self.update_url, self.valid_education_data("UI (diubah)"))
        self.assertRedirects(response, reverse("main:show_education"))
        self.education.refresh_from_db()
        self.assertEqual(self.education.institution, "UI (diubah)")

        self.assertEqual(self.client.get(self.create_url).status_code, 403)
        self.assertEqual(self.client.post(self.delete_url).status_code, 403)
        self.assertTrue(Education.objects.filter(pk=self.education.pk).exists())

    def test_editor_sees_edit_button_and_role_badge(self):
        self.login_as(self.editor)
        response = self.client.get(reverse("main:show_education"))

        self.assertContains(response, ">Edit<")
        self.assertContains(response, '<span class="nav-role">Editor</span>')
        self.assertNotContains(response, "Tambah Pendidikan")
        self.assertNotContains(response, "Ya, Hapus")

    def test_owner_can_create_update_and_delete(self):
        self.login_as(self.owner)
        response = self.client.get(reverse("main:show_education"))
        self.assertContains(response, "Tambah Pendidikan")
        self.assertContains(response, ">Edit<")
        self.assertContains(response, "Ya, Hapus")

        self.client.post(self.create_url, self.valid_education_data("SMA Negeri 8"))
        self.assertTrue(Education.objects.filter(institution="SMA Negeri 8").exists())

        self.client.post(self.update_url, self.valid_education_data("UI"))
        self.education.refresh_from_db()
        self.assertEqual(self.education.institution, "UI")

        self.client.post(self.delete_url)
        self.assertFalse(Education.objects.filter(pk=self.education.pk).exists())

    def test_star_toggles_once_per_user(self):
        self.login_as(self.regular)

        self.client.post(self.star_url)
        self.client.post(self.star_url)
        self.assertEqual(self.education.starred_by.count(), 0)

        self.client.post(self.star_url)
        self.education.starred_by.add(self.regular)  # add ulang tidak menggandakan star
        self.assertEqual(self.education.starred_by.count(), 1)

        response = self.client.get(reverse("main:show_education"))
        self.assertContains(response, "is-starred")
        self.assertContains(response, "Unstar")
        self.assertContains(response, '<span class="star-count">1</span>')

    def test_star_counts_every_role_and_ignores_get(self):
        for user in [self.regular, self.editor, self.owner]:
            self.login_as(user)
            self.client.post(self.star_url)
            self.client.logout()

        self.assertEqual(self.education.starred_by.count(), 3)
        self.login_as(self.regular)
        self.client.get(self.star_url)
        self.assertEqual(self.education.starred_by.count(), 3)

    def test_education_json_uses_usernames_without_sensitive_data(self):
        self.education.starred_by.add(self.regular, self.editor)
        response = self.client.get(reverse("main:get_education_json"))

        self.assertEqual(response.status_code, 200)
        fields = json.loads(response.content)[0]["fields"]
        self.assertCountEqual(fields["starred_by"], [["sasha"], ["rian"]])
        body = response.content.decode()
        self.assertNotIn("password", body)
        self.assertNotIn("pbkdf2", body)

    def test_login_redirects_back_to_next_only_within_site(self):
        credentials = {"username": "rian", "password": self.password}

        response = self.client.post(reverse("main:login"), {**credentials, "next": self.update_url})
        self.assertRedirects(response, self.update_url)
        self.client.logout()

        response = self.client.post(
            reverse("main:login"), {**credentials, "next": "https://example.com/"}
        )
        self.assertRedirects(response, reverse("main:show_main"))


class ExperienceAuthorizationTest(TestCase):
    password = "S3cure-pass-123"

    def setUp(self):
        self.experience = Experience.objects.create(title="Asdos", description="PBP")
        self.delete_url = reverse("main:delete_experience", args=[self.experience.id])
        User.objects.create_user("sasha", password=self.password)
        User.objects.create_superuser("karyn", password=self.password)

    def test_only_owner_can_create_or_delete_experience(self):
        create_url = reverse("main:create_experience")
        self.assertRedirects(self.client.get(create_url), f"/login/?next={create_url}")

        self.client.login(username="sasha", password=self.password)
        self.assertEqual(self.client.get(create_url).status_code, 403)
        self.assertEqual(self.client.post(self.delete_url).status_code, 403)
        self.client.logout()

        self.client.login(username="karyn", password=self.password)
        self.assertEqual(self.client.get(create_url).status_code, 200)
        self.client.post(self.delete_url)
        self.assertFalse(Experience.objects.filter(pk=self.experience.pk).exists())
