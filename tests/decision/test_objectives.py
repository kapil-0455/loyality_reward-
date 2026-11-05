import math

import pytest

from backend.app.decision.objectives import calculate_reward_score


def test_calculate_reward_score():
    score = calculate_reward_score(90, 80, 100, 20)
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
    assert calculate_reward_score(0, 0, 0, 0) == 0


def test_maximum_positive_inputs():
    assert calculate_reward_score(100, 100, 100, 0) == 85


def test_negative_input_rejected():
    with pytest.raises(ValueError):
        calculate_reward_score(-10, 80, 90, 20)


def test_input_above_100_rejected():
    with pytest.raises(ValueError):
        calculate_reward_score(110, 80, 90, 20)


@pytest.mark.parametrize("invalid_value", [math.nan, math.inf, -math.inf])
def test_non_finite_objective_value_rejected(invalid_value):
    with pytest.raises(ValueError):
        calculate_reward_score(invalid_value, 80, 90, 20)
