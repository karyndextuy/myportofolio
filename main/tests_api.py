import datetime
import uuid

from django.contrib.auth.models import Group, User
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from main.models import Education, Project
from main.roles import EDITOR_GROUP_NAME


class ProjectAPITest(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_superuser(
            username="owner", password="test-password", email="owner@example.com",
        )
        self.visitor = User.objects.create_user(username="visitor", password="test-password")
        self.project = Project.objects.create(
            title="Portfolio", description="My website", tech_stack="Django",
        )
        self.list_url = reverse("api:project-list")
        self.detail_url = reverse("api:project-detail", args=[self.project.id])
        self.star_url = reverse("api:project-star", args=[self.project.id])
        self.payload = {
            "title": "New project", "description": "A useful app", "tech_stack": "Python",
            "project_url": "https://example.com/", "project_image_url": "",
        }

    def test_public_list_and_detail(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["id"], str(self.project.id))
        self.assertFalse(response.data[0]["is_starred"])
        self.assertNotIn("fields", response.data[0])
        self.assertEqual(self.client.get(self.detail_url).status_code, status.HTTP_200_OK)

    def test_search_and_empty_results(self):
        response = self.client.get(self.list_url, {"title": "PORT"})
        self.assertEqual(len(response.data), 1)
        response = self.client.get(self.list_url, {"title": "not-found"})
        self.assertEqual(response.data, [])

    def test_missing_project(self):
        url = reverse("api:project-detail", args=[uuid.uuid4()])
        self.assertEqual(self.client.get(url).status_code, status.HTTP_404_NOT_FOUND)

    def test_guest_and_visitor_cannot_write(self):
        for user in (None, self.visitor):
            self.client.force_authenticate(user=user)
            self.assertEqual(self.client.post(self.list_url, self.payload, format="json").status_code, 403)
            self.assertEqual(self.client.patch(self.detail_url, {"title": "Changed"}, format="json").status_code, 403)
            self.assertEqual(self.client.delete(self.detail_url).status_code, 403)
        self.assertEqual(Project.objects.count(), 1)
        self.project.refresh_from_db()
        self.assertEqual(self.project.title, "Portfolio")

    def test_owner_can_create(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(self.list_url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Project.objects.filter(pk=response.data["id"]).exists())

    def test_validation(self):
        self.client.force_authenticate(user=self.owner)
        for changes, field in [
            ({"title": "   "}, "title"),
            ({"title": '<img src="x" onerror="alert(1)">'}, "title"),
            ({"project_url": "javascript:alert(1)"}, "project_url"),
        ]:
            response = self.client.post(self.list_url, {**self.payload, **changes}, format="json")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn(field, response.data)
        self.assertEqual(Project.objects.count(), 1)

    def test_patch_put_and_delete(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.patch(self.detail_url, {"title": "Changed"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.project.refresh_from_db()
        self.assertEqual(self.project.description, "My website")
        response = self.client.put(self.detail_url, {"title": "Incomplete"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.client.put(self.detail_url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b"")
        self.assertFalse(Project.objects.filter(pk=self.project.id).exists())

    def test_star_requires_login_and_toggles(self):
        self.assertEqual(self.client.post(self.star_url).status_code, status.HTTP_403_FORBIDDEN)
        self.client.force_authenticate(user=self.visitor)
        response = self.client.post(self.star_url)
        self.assertTrue(response.data["is_starred"])
        self.assertEqual(response.data["star_count"], 1)
        response = self.client.post(self.star_url)
        self.assertFalse(response.data["is_starred"])
        self.assertEqual(response.data["star_count"], 0)

    def test_computed_fields_are_read_only(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(self.list_url, {
            **self.payload, "star_count": 99, "is_starred": True,
            "starred_by_names": "forged", "starred_by": [self.visitor.id],
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["star_count"], 0)
        self.assertFalse(response.data["is_starred"])

    def test_staff_and_editor_cannot_manage_tutorial_projects(self):
        self.visitor.is_staff = True
        self.visitor.save()
        self.visitor.groups.add(Group.objects.get_or_create(name="Editor")[0])
        self.client.force_authenticate(user=self.visitor)
        response = self.client.patch(self.detail_url, {"title": "Changed"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_wrong_method(self):
        self.client.force_authenticate(user=self.owner)
        self.assertEqual(self.client.delete(self.list_url).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_session_write_without_csrf_is_rejected(self):
        client = APIClient(enforce_csrf_checks=True)
        self.assertTrue(client.login(username="owner", password="test-password"))
        response = client.post(self.list_url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Project.objects.count(), 1)

    def test_session_write_with_csrf_succeeds(self):
        client = APIClient(enforce_csrf_checks=True)
        client.login(username="owner", password="test-password")
        # The Browsable API form renders a real CSRF token into the response.
        page = client.get(self.list_url, HTTP_ACCEPT="text/html")
        self.assertEqual(page.status_code, status.HTTP_200_OK)
        token = client.cookies["csrftoken"].value
        response = client.post(
            self.list_url, self.payload, format="json", HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class EducationAPITest(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_superuser(
            username="owner", password="test-password", email="owner@example.com",
        )
        self.regular = User.objects.create_user(
            username="regular", password="test-password", email="regular@example.com",
        )
        self.editor = User.objects.create_user(username="editor", password="test-password")
        # Grup Editor sudah dibuat oleh migrasi 0006, jadi jangan create().
        self.editor.groups.add(Group.objects.get_or_create(name=EDITOR_GROUP_NAME)[0])
        self.education = Education.objects.create(
            institution="Universitas Indonesia",
            description="S1 Sistem Informasi",
            started_at=datetime.date(2023, 8, 1),
        )
        self.list_url = reverse("api:education-list")
        self.detail_url = reverse("api:education-detail", args=[self.education.id])
        self.star_url = reverse("api:education-star", args=[self.education.id])
        self.payload = {
            "institution": "SMA Negeri 8",
            "description": "IPA",
            "started_at": "2020-07-01",
            "ended_at": "2023-06-30",
            "certificate_url": "https://example.com/ijazah.pdf",
        }

    def assert_education_unchanged(self):
        self.assertEqual(Education.objects.count(), 1)
        self.education.refresh_from_db()
        self.assertEqual(self.education.institution, "Universitas Indonesia")
        self.assertEqual(self.education.description, "S1 Sistem Informasi")

    def assert_cannot_create_or_delete(self):
        self.assertEqual(self.client.post(self.list_url, self.payload, format="json").status_code, 403)
        self.assertEqual(self.client.delete(self.detail_url).status_code, 403)
        self.assert_education_unchanged()

    def test_public_list_and_detail(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["id"], str(self.education.id))
        self.assertEqual(response.data[0]["started_at"], "2023-08-01")
        self.assertTrue(response.data[0]["is_ongoing"])
        self.assertFalse(response.data[0]["is_starred"])
        self.assertNotIn("fields", response.data[0])
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["institution"], "Universitas Indonesia")

    def test_response_has_no_sensitive_account_data(self):
        self.education.starred_by.add(self.regular)
        response = self.client.get(self.detail_url, HTTP_ACCEPT="application/json")
        self.assertEqual(response.data["starred_by_names"], "regular")
        self.assertNotIn("starred_by", response.data)
        self.assertNotContains(response, "regular@example.com")
        self.assertNotContains(response, self.regular.password)

    def test_search_and_empty_results(self):
        response = self.client.get(self.list_url, {"institution": "INDONESIA"})
        self.assertEqual(len(response.data), 1)
        response = self.client.get(self.list_url, {"institution": "not-found"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_missing_education_returns_404(self):
        missing_id = uuid.uuid4()
        self.client.force_authenticate(user=self.owner)
        for name, method in [("api:education-detail", "get"), ("api:education-star", "post")]:
            url = reverse(name, args=[missing_id])
            self.assertEqual(getattr(self.client, method)(url).status_code, status.HTTP_404_NOT_FOUND)

    def test_visitor_and_regular_user_cannot_write(self):
        for user in (None, self.regular):
            self.client.force_authenticate(user=user)
            self.assertEqual(self.client.put(self.detail_url, self.payload, format="json").status_code, 403)
            self.assertEqual(self.client.patch(self.detail_url, {"institution": "X"}, format="json").status_code, 403)
            self.assert_cannot_create_or_delete()

    def test_editor_can_update_but_not_create_or_delete(self):
        self.client.force_authenticate(user=self.editor)
        self.assert_cannot_create_or_delete()

        response = self.client.patch(self.detail_url, {"institution": "UI"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.education.refresh_from_db()
        self.assertEqual(self.education.institution, "UI")
        self.assertEqual(self.education.description, "S1 Sistem Informasi")

        response = self.client.put(self.detail_url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.education.refresh_from_db()
        self.assertEqual(self.education.institution, "SMA Negeri 8")

    def test_owner_can_create_update_and_delete(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(self.list_url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Education.objects.filter(pk=response.data["id"]).exists())

        response = self.client.patch(self.detail_url, {"description": "Diubah"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.put(self.detail_url, {"institution": "Tidak lengkap"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("started_at", response.data)

        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b"")
        self.assertFalse(Education.objects.filter(pk=self.education.id).exists())

    def test_invalid_input_returns_400_and_saves_nothing(self):
        self.client.force_authenticate(user=self.owner)
        for changes, field in [
            ({"institution": "   "}, "institution"),
            ({"institution": '<img src="x" onerror="alert(1)">'}, "institution"),
            ({"certificate_url": "javascript:alert(1)"}, "certificate_url"),
            ({"started_at": "bukan-tanggal"}, "started_at"),
            ({"ended_at": "2019-01-01"}, "ended_at"),
        ]:
            response = self.client.post(self.list_url, {**self.payload, **changes}, format="json")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn(field, response.data)
        self.assert_education_unchanged()

    def test_patch_end_date_is_compared_with_stored_start_date(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.patch(self.detail_url, {"ended_at": "2020-01-01"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("ended_at", response.data)
        self.education.refresh_from_db()
        self.assertIsNone(self.education.ended_at)

    def test_html_is_stripped_and_blank_url_becomes_null(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(self.list_url, {
            **self.payload,
            "institution": "<b>SMA</b> 8",
            "description": "<script>alert(1)</script>IPA",
            "certificate_url": "",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created = Education.objects.get(pk=response.data["id"])
        self.assertEqual(created.institution, "SMA 8")
        self.assertNotIn("<script>", created.description)
        self.assertIsNone(created.certificate_url)

    def test_star_requires_login_and_toggles(self):
        self.assertEqual(self.client.post(self.star_url).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.education.starred_by.count(), 0)

        self.client.force_authenticate(user=self.regular)
        response = self.client.post(self.star_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_starred"])
        self.assertEqual(response.data["star_count"], 1)
        response = self.client.post(self.star_url)
        self.assertFalse(response.data["is_starred"])
        self.assertEqual(response.data["star_count"], 0)

    def test_star_always_uses_the_logged_in_account(self):
        self.client.force_authenticate(user=self.regular)
        self.client.post(self.star_url, {"user": self.owner.id, "starred_by": [self.owner.id]}, format="json")
        self.assertEqual(list(self.education.starred_by.all()), [self.regular])

    def test_star_status_is_per_user(self):
        self.education.starred_by.add(self.regular)
        self.client.force_authenticate(user=self.regular)
        self.assertTrue(self.client.get(self.detail_url).data["is_starred"])
        self.client.force_authenticate(user=self.editor)
        self.assertFalse(self.client.get(self.detail_url).data["is_starred"])

    def test_star_only_accepts_post(self):
        self.client.force_authenticate(user=self.regular)
        self.assertEqual(self.client.get(self.star_url).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_computed_fields_are_read_only(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(self.list_url, {
            **self.payload, "id": str(self.education.id), "star_count": 99, "is_starred": True,
            "starred_by_names": "forged", "starred_by": [self.regular.id], "is_ongoing": True,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(response.data["id"], str(self.education.id))
        self.assertEqual(response.data["star_count"], 0)
        self.assertFalse(response.data["is_starred"])
        self.assertFalse(response.data["is_ongoing"])

    def test_wrong_method_returns_405(self):
        self.client.force_authenticate(user=self.owner)
        self.assertEqual(self.client.delete(self.list_url).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_list_query_count_does_not_grow_with_rows(self):
        def count_queries():
            with CaptureQueriesContext(connection) as queries:
                self.client.get(self.list_url)
            return len(queries)

        self.education.starred_by.add(self.regular)
        baseline = count_queries()
        for index in range(5):
            extra = Education.objects.create(institution=f"Kampus {index}", started_at=datetime.date(2020, 1, 1))
            extra.starred_by.add(self.regular, self.editor)
        self.assertEqual(count_queries(), baseline)

    def test_session_write_without_csrf_is_rejected(self):
        client = APIClient(enforce_csrf_checks=True)
        self.assertTrue(client.login(username="owner", password="test-password"))
        response = client.post(self.list_url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        response = client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assert_education_unchanged()

    def test_session_star_without_csrf_is_rejected(self):
        client = APIClient(enforce_csrf_checks=True)
        self.assertTrue(client.login(username="regular", password="test-password"))
        self.assertEqual(client.post(self.star_url).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.education.starred_by.count(), 0)

    def test_session_write_with_csrf_succeeds(self):
        client = APIClient(enforce_csrf_checks=True)
        client.login(username="owner", password="test-password")
        client.get(self.list_url, HTTP_ACCEPT="text/html")
        token = client.cookies["csrftoken"].value
        response = client.post(self.list_url, self.payload, format="json", HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_education_page_sets_csrf_cookie_for_regular_user(self):
        client = APIClient(enforce_csrf_checks=True)
        client.login(username="regular", password="test-password")
        response = client.get(reverse("main:show_education"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token = client.cookies["csrftoken"].value
        response = client.post(self.star_url, HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_starred"])
