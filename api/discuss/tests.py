from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from .models import DiscussPost, DiscussComment, DiscussCategory

User = get_user_model()


class DiscussAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="discuss_coder",
            email="coder@example.com",
            password="testpassword123",
        )
        self.other_user = User.objects.create_user(
            username="other_dev",
            email="other@example.com",
            password="testpassword123",
        )
        self.post = DiscussPost.objects.create(
            author=self.user,
            title="Google L5 System Design Experience",
            category=DiscussCategory.INTERVIEW_EXPERIENCE,
            content="Here is a detailed breakdown of my Google L5 onsite rounds...",
            tags=["Google", "System Design", "L5"],
        )

    def test_list_discussions(self):
        response = self.client.get("/api/discuss/posts/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(
            response.data["results"][0]["title"], "Google L5 System Design Experience"
        )

    def test_filter_by_category(self):
        response = self.client.get("/api/discuss/posts/?category=INTERVIEW_EXPERIENCE")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

        response_empty = self.client.get("/api/discuss/posts/?category=FEEDBACK")
        self.assertEqual(response_empty.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_empty.data["results"]), 0)

    def test_create_discussion(self):
        self.client.force_authenticate(user=self.user)
        payload = {
            "title": "Amazon OA Questions 2025",
            "category": "INTERVIEW_QUESTION",
            "content": "Received these 2 questions on Amazon online assessment...",
            "tags": ["Amazon", "OA"],
        }
        response = self.client.post("/api/discuss/posts/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(DiscussPost.objects.count(), 2)

    def test_vote_on_post(self):
        self.client.force_authenticate(user=self.other_user)
        response = self.client.post(
            f"/api/discuss/posts/{self.post.id}/vote/",
            {"vote_type": "up"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["vote_count"], 1)
        self.assertEqual(response.data["user_vote"], 1)

    def test_add_comment(self):
        self.client.force_authenticate(user=self.other_user)
        response = self.client.post(
            f"/api/discuss/posts/{self.post.id}/add_comment/",
            {"content": "Great experience sharing, thanks for the tips!"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.post.comments.count(), 1)
