from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model

from .models import (
    Contest,
    ContestProblem,
    ContestRegistration,
    ContestParticipant,
    ContestSubmission,
)
from problem.models import Problem, Difficulty, AnswerStatus

User = get_user_model()


class ContestModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@test.com", password="password"
        )

    def test_default_weekly_contest_title(self):
        # When no title is provided, it should auto-generate "Weekly run 1"
        c1 = Contest.objects.create(
            start_time=timezone.now() + timedelta(days=2),
            duration_minutes=90,
        )
        self.assertEqual(c1.title, "Weekly run 1")
        self.assertTrue(c1.is_weekly)

        # Second one without title should be "Weekly run 2"
        c2 = Contest.objects.create(
            start_time=timezone.now() + timedelta(days=9),
            duration_minutes=90,
        )
        self.assertEqual(c2.title, "Weekly run 2")
        self.assertTrue(c2.is_weekly)

    def test_custom_contest_title(self):
        # When custom title is provided, it is not counted as a weekly run
        c = Contest.objects.create(
            title="Biweekly Flash Round",
            start_time=timezone.now() + timedelta(days=1),
            duration_minutes=60,
        )
        self.assertEqual(c.title, "Biweekly Flash Round")
        self.assertFalse(c.is_weekly)


class ContestAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="contestant1", email="c1@test.com", password="password"
        )
        self.user2 = User.objects.create_user(
            username="contestant2", email="c2@test.com", password="password"
        )
        self.client.force_authenticate(user=self.user)

        self.problem1 = Problem.objects.create(
            name="Two Sum", difficulty=Difficulty.EASY
        )
        self.problem2 = Problem.objects.create(
            name="Add Two Numbers", difficulty=Difficulty.MEDIUM
        )

        self.contest = Contest.objects.create(
            title="Weekly run 10",
            start_time=timezone.now() - timedelta(minutes=10),
            duration_minutes=90,
        )
        self.cp1 = ContestProblem.objects.create(
            contest=self.contest, problem=self.problem1, order=1, points=3
        )
        self.cp2 = ContestProblem.objects.create(
            contest=self.contest, problem=self.problem2, order=2, points=5
        )

    def test_list_contests(self):
        url = "/api/contests/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_register_and_leaderboard(self):
        # Register for contest
        reg_url = f"/api/contests/{self.contest.id}/register/"
        response = self.client.post(reg_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            ContestRegistration.objects.filter(
                contest=self.contest, user=self.user
            ).exists()
        )

        # Check leaderboard
        lb_url = f"/api/contests/{self.contest.id}/leaderboard/"
        response = self.client.get(lb_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("leaderboard", response.data)

    def test_contest_problem_detail(self):
        url = f"/api/contests/{self.contest.id}/problems/{self.problem1.id}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Two Sum")
        self.assertEqual(response.data["points"], 3)
        self.assertEqual(response.data["order"], 1)
        self.assertEqual(response.data["next_problem_id"], self.problem2.id)
