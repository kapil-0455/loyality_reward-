
import pytest

from backend.app.decision.objectives import calculate_reward_score


def test_calculate_reward_score():
    score = calculate_reward_score(
        relevance=90,
        reward_value=80,
        inventory_suitability=100,
        cost_penalty=20
    )

    assert score == 72.5


def test_high_relevance_increases_score():
    score1 = calculate_reward_score(50, 80, 90, 20)
    score2 = calculate_reward_score(90, 80, 90, 20)

    assert score2 > score1


def test_high_cost_penalty_decreases_score():
    score1 = calculate_reward_score(80, 80, 90, 10)
    score2 = calculate_reward_score(80, 80, 90, 90)

    assert score1 > score2


def test_all_zero_values():
    score = calculate_reward_score(0, 0, 0, 0)

    assert score == 0


def test_maximum_positive_inputs():
    score = calculate_reward_score(100, 100, 100, 0)

    assert score == 85


def test_negative_input_rejected():
    with pytest.raises(ValueError):
        calculate_reward_score(-10, 80, 90, 20)


def test_input_above_100_rejected():
    with pytest.raises(ValueError):
        calculate_reward_score(110, 80, 90, 20)
