import json

from django.contrib.auth.models import Group, User
from django.test import Client, TestCase
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

    def test_education_page_renders_skeleton_for_ajax(self):
        response = self.client.get(reverse("main:show_education"))

        # Data tidak lagi dirender server; halaman hanya berisi kerangka
        self.assertNotContains(response, self.education.description)
        self.assertContains(response, 'id="education-timeline"')
        self.assertContains(response, 'id="education-loading"')
        self.assertContains(response, 'id="education-error"')
        self.assertContains(response, reverse("main:get_education_json"))

    def test_education_json_shows_data(self):
        response = self.client.get(reverse("main:get_education_json"))

        self.assertEqual(response["Content-Type"], "application/json")
        fields = response.json()[0]["fields"]
        self.assertEqual(fields["institution"], self.education.institution)
        self.assertEqual(fields["description"], self.education.description)
        self.assertEqual(fields["started_at"], "2025-01-01")
        self.assertTrue(fields["is_ongoing"])

    def test_empty_education_page(self):
        Education.objects.all().delete()
        response = self.client.get(reverse("main:show_education"))

        self.assertContains(response, "Belum ada riwayat pendidikan yang ditambahkan.")

    def test_completed_education(self):
        self.education.ended_at = timezone.now()
        self.education.save()
        self.education.refresh_from_db()
        fields = self.client.get(reverse("main:get_education_json")).json()[0]["fields"]

        self.assertFalse(self.education.is_ongoing)
        self.assertFalse(fields["is_ongoing"])
        self.assertEqual(fields["ended_at"], self.education.ended_at.isoformat())

    def test_education_json_search(self):
        url = reverse("main:get_education_json")

        self.assertEqual(len(self.client.get(url, {"institution": "indonesia"}).json()), 1)
        self.assertEqual(self.client.get(url, {"institution": "zzz"}).json(), [])


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
        self.assertContains(response, "const CAN_UPDATE = false;")
        self.assertContains(response, "const CAN_DELETE = false;")
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
        self.assertContains(response, "const CAN_UPDATE = false;")
        self.assertContains(response, "const CAN_DELETE = false;")
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

        self.assertContains(response, "const CAN_UPDATE = true;")
        self.assertContains(response, "const CAN_DELETE = false;")
        self.assertContains(response, '<span class="nav-role">Editor</span>')
        self.assertNotContains(response, "Tambah Pendidikan")
        self.assertNotContains(response, "Ya, Hapus")

    def test_owner_can_create_update_and_delete(self):
        self.login_as(self.owner)
        response = self.client.get(reverse("main:show_education"))
        self.assertContains(response, "Tambah Pendidikan")
        self.assertContains(response, "const CAN_UPDATE = true;")
        self.assertContains(response, "const CAN_DELETE = true;")
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

        fields = self.client.get(reverse("main:get_education_json")).json()[0]["fields"]
        self.assertEqual(fields["star_count"], 1)
        self.assertTrue(fields["is_starred"])

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
        self.assertEqual(fields["star_count"], 2)
        self.assertFalse(fields["is_starred"])  # pengunjung belum login
        self.assertCountEqual(fields["starred_by_names"].split(", "), ["sasha", "rian"])
        body = response.content.decode()
        self.assertNotIn("password", body)
        self.assertNotIn("pbkdf2", body)
        self.assertNotIn(f'"id": {self.regular.id}', body)

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


class EducationAjaxTest(TestCase):
    """Tugas 5: endpoint JSON, tambah data lewat AJAX, star tanpa reload,
    dan pembersihan input untuk mencegah XSS."""

    password = "S3cure-pass-123"
    xss_payload = '<img src="x" onerror="alert(\'XSS!\')">'

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

        self.create_url = reverse("main:create_education_ajax")
        self.json_url = reverse("main:get_education_json")
        self.star_url = reverse("main:toggle_star_education", args=[self.education.id])

    def login_as(self, user):
        self.client.login(username=user.username, password=self.password)

    def education_data(self, **overrides):
        data = {
            "institution": "SMA Negeri 8",
            "description": "IPA",
            "started_at": "2021-07-01",
            "ended_at": "",
            "certificate_url": "",
        }
        data.update(overrides)
        return data

    def error_messages(self, response, field):
        return [error["message"] for error in response.json()["errors"][field]]

    def test_create_ajax_only_accepts_post(self):
        self.login_as(self.owner)
        self.assertEqual(self.client.get(self.create_url).status_code, 405)

    def test_create_ajax_rejects_every_role_except_owner_with_json_403(self):
        for user in [None, self.regular, self.editor]:
            self.client.logout()
            if user:
                self.login_as(user)
            response = self.client.post(self.create_url, self.education_data())
            self.assertEqual(response.status_code, 403)
            self.assertIn("pemilik portofolio", response.json()["message"])

        self.assertFalse(Education.objects.filter(institution="SMA Negeri 8").exists())

    def test_owner_creates_education_and_gets_201(self):
        self.login_as(self.owner)
        response = self.client.post(self.create_url, self.education_data())

        self.assertEqual(response.status_code, 201)
        created = Education.objects.get(pk=response.json()["pk"])
        self.assertEqual(created.institution, "SMA Negeri 8")
        self.assertEqual(len(self.client.get(self.json_url).json()), 2)

    def test_invalid_data_returns_400_with_field_errors(self):
        self.login_as(self.owner)
        response = self.client.post(
            self.create_url, self.education_data(institution="   ", started_at="")
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.error_messages(response, "institution"), ["This field is required."])
        self.assertEqual(self.error_messages(response, "started_at"), ["This field is required."])

    def test_end_date_before_start_date_is_rejected(self):
        self.login_as(self.owner)
        response = self.client.post(
            self.create_url, self.education_data(ended_at="2020-01-01")
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            self.error_messages(response, "ended_at"),
            ["Tanggal selesai tidak boleh sebelum tanggal mulai."],
        )

    def test_xss_payload_and_javascript_url_are_rejected(self):
        self.login_as(self.owner)

        response = self.client.post(self.create_url, self.education_data(institution=self.xss_payload))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            self.error_messages(response, "institution"),
            ["Nama institusi tidak boleh hanya berisi tag HTML."],
        )

        response = self.client.post(
            self.create_url, self.education_data(certificate_url="javascript:alert(1)")
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("certificate_url", response.json()["errors"])
        self.assertEqual(Education.objects.count(), 1)

    def test_html_tags_are_stripped_before_saving(self):
        self.login_as(self.owner)
        response = self.client.post(
            self.create_url,
            self.education_data(institution="SMA <b>Negeri</b> 8", description="IPA <script>x</script>unggulan"),
        )

        created = Education.objects.get(pk=response.json()["pk"])
        self.assertEqual(created.institution, "SMA Negeri 8")
        self.assertNotIn("<", created.description)

    def test_create_ajax_requires_csrf_token(self):
        client = Client(enforce_csrf_checks=True)
        client.login(username="karyn", password=self.password)

        self.assertEqual(client.post(self.create_url, self.education_data()).status_code, 403)

        client.get(reverse("main:show_education"))
        token = client.cookies["csrftoken"].value
        response = client.post(self.create_url, self.education_data(), HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 201)

    def test_add_modal_is_rendered_only_for_owner(self):
        for user, has_modal in [(None, False), (self.regular, False), (self.editor, False), (self.owner, True)]:
            self.client.logout()
            if user:
                self.login_as(user)
            response = self.client.get(reverse("main:show_education"))
            if has_modal:
                self.assertContains(response, 'id="add-education-modal"')
                self.assertContains(response, 'name="institution"')
            else:
                self.assertNotContains(response, 'id="add-education-modal"')

    def test_json_reports_star_status_for_current_user(self):
        self.education.starred_by.add(self.regular)

        anonymous = self.client.get(self.json_url).json()[0]["fields"]
        self.login_as(self.regular)
        regular = self.client.get(self.json_url).json()[0]["fields"]
        self.client.logout()
        self.login_as(self.editor)
        editor = self.client.get(self.json_url).json()[0]["fields"]

        self.assertEqual((anonymous["star_count"], anonymous["is_starred"]), (1, False))
        self.assertEqual((regular["star_count"], regular["is_starred"]), (1, True))
        self.assertEqual((editor["star_count"], editor["is_starred"]), (1, False))

    def test_json_query_count_does_not_grow_with_rows(self):
        for index in range(5):
            Education.objects.create(institution=f"Sekolah {index}", started_at="2010-01-01")
        self.login_as(self.regular)

        # sesi + user + data + prefetch starred_by, berapa pun jumlah barisnya
        with self.assertNumQueries(4):
            self.client.get(self.json_url)

    def test_ajax_star_returns_json_and_form_fallback_redirects(self):
        self.login_as(self.regular)

        response = self.client.post(self.star_url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        fields = response.json()["fields"]
        self.assertEqual((fields["star_count"], fields["is_starred"]), (1, True))
        self.assertEqual(fields["starred_by_names"], "sasha")

        response = self.client.post(self.star_url)
        self.assertRedirects(response, reverse("main:show_education"))
        self.assertEqual(self.education.starred_by.count(), 0)
