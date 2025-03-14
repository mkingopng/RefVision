# refvision/apl_rules.py
"""
Rules for failing lifts.
"""

from typing import Dict, Any, List


class LiftEvaluationResult:
    """
    Encapsulates the result of evaluating a lift attempt.
    """

    def __init__(self) -> None:
        self.is_successful: bool = True
        self.reasons: List[str] = []

    def add_failure(self, reason: str) -> None:
        """
        Records a reason for failure and marks the lift as unsuccessful.

        :param reason: The reason for the lift's failure.
        :return: None
        """
        self.is_successful = False
        self.reasons.append(reason)

    def __str__(self) -> str:
        """
        Returns a string representation of the evaluation result.

        :return: A success or failure message with reasons.
        """
        return (
            "Lift Successful"
            if self.is_successful
            else f"Lift Failed: {', '.join(self.reasons)}"
        )


class Squat:
    """
    Evaluates a squat lift attempt based on defined rules.
    """

    def evaluate(self, lifter_state: Dict[str, Any]) -> LiftEvaluationResult:
        """
        Evaluates a lifter's squat performance against the rules.

        :param lifter_state: The state of the lifter during the squat attempt.
        :returns: The result of the squat evaluation.
        """
        result: LiftEvaluationResult = LiftEvaluationResult()
        self.rule_bar_position(lifter_state, result)
        self.rule_knees_locked_at_start(lifter_state, result)
        self.rule_descent_below_parallel(lifter_state, result)
        self.rule_no_double_bounce(lifter_state, result)
        self.rule_no_downward_movement_during_ascent(lifter_state, result)
        self.rule_knees_locked_at_completion(lifter_state, result)
        self.rule_wait_for_commands(lifter_state, result)
        self.rule_no_spotter_contact(lifter_state, result)
        self.rule_no_elbow_leg_contact(lifter_state, result)
        return result

    def rule_bar_position(
        self, state: Dict[str, Any], result: LiftEvaluationResult
    ) -> None:
        """
        Validates the bar position.

        :param state: The lifter's state.
        :param result: The evaluation result to update.
        :return: None
        """
        if state.get("bar_position", 4) > 3:
            result.add_failure("Bar held more than 3cm below posterior deltoids.")

    def rule_knees_locked_at_start(
        self, state: Dict[str, Any], result: LiftEvaluationResult
    ) -> None:
        """
        Validates that the knees are locked at the start.

        :param state: The lifter's state.
        :param result: The evaluation result to update.
        :return: None
        """
        if not state.get("knees_locked", False):
            result.add_failure("Knees not locked at the start.")

    def rule_descent_below_parallel(
        self, state: Dict[str, Any], result: LiftEvaluationResult
    ) -> None:
        """
        Validates the depth of the squat.

        :param state: The lifter's state.
        :param result: The evaluation result to update.
        :return: None
        """
        if not state.get("descent_below_parallel", False):
            result.add_failure("Top of legs at hip joint not below top of knees.")

    def rule_no_double_bounce(
        self, state: Dict[str, Any], result: LiftEvaluationResult
    ) -> None:
        """
        Ensures no double bouncing during the lift.

        :param state: The lifter's state.
        :param result: The evaluation result to update.
        :return: None
        """
        if state.get("double_bounce", False):
            result.add_failure("Double bounce during ascent.")

    def rule_no_downward_movement_during_ascent(
        self, state: Dict[str, Any], result: LiftEvaluationResult
    ) -> None:
        """
        Validates that there is no downward movement during the ascent.

        :param state: The lifter's state.
        :param result: The evaluation result to update.
        :return: None
        """
        if state.get("downward_movement_during_ascent", False):
            result.add_failure("Downward movement of the bar during ascent.")

    def rule_knees_locked_at_completion(
        self, state: Dict[str, Any], result: LiftEvaluationResult
    ) -> None:
        """
        Validates that the knees are locked at the end.

        :param state: The lifter's state.
        :param result: The evaluation result to update.
        :return: None
        """
        if not state.get("knees_locked_at_finish", False):
            result.add_failure("Knees not locked at completion.")

    def rule_wait_for_commands(
        self, state: Dict[str, Any], result: LiftEvaluationResult
    ) -> None:
        """
        Ensures the lifter waits for the referee's commands.

        :param state: The lifter's state.
        :param result: The evaluation result to update.
        :return: None
        """
        if not state.get("waited_for_rack_command", False):
            result.add_failure("Did not wait for 'RACK' command.")

    def rule_no_spotter_contact(
        self, state: Dict[str, Any], result: LiftEvaluationResult
    ) -> None:
        """
        Ensures no contact with spotters.

        :param state: The lifter's state.
        :param result: The evaluation result to update.
        :return: None
        """
        if state.get("spotter_contact", False):
            result.add_failure("Spotter made contact with the bar.")

    def rule_no_elbow_leg_contact(
        self, state: Dict[str, Any], result: LiftEvaluationResult
    ) -> None:
        """
        Ensures elbows or upper arms do not contact the legs.

        :param state: The lifter's state.
        :param result: The evaluation result to update.
        :return: None
        """
        if state.get("elbows_touch_legs", False):
            result.add_failure("Elbows or upper arms contacted the legs.")


class BenchPress:
    """
    Evaluates a bench press attempt based on defined rules.
    """

    def evaluate(self, lifter_state: Dict[str, Any]) -> LiftEvaluationResult:
        """
        Evaluates a lifter's bench press performance.

        :param lifter_state: The state of the lifter during the bench press attempt.
        :returns: The result of the bench press evaluation.
        """
        result: LiftEvaluationResult = LiftEvaluationResult()
        self.rule_position_on_bench(lifter_state, result)
        self.rule_grip_validity(lifter_state, result)
        self.rule_no_belt_contact(lifter_state, result)
        self.rule_no_downward_movement(lifter_state, result)
        self.rule_wait_for_start_command(lifter_state, result)
        self.rule_no_rack_contact(lifter_state, result)
        self.rule_complete_lockout(lifter_state, result)
        return result

    def rule_position_on_bench(
        self, state: Dict[str, Any], result: LiftEvaluationResult
    ) -> None:
        """
        Validates that the lifter is properly positioned on the bench.

        :param state: The lifter's state.
        :param result: The evaluation result to update.
        :return: None
        """
        if not state.get("shoulders_on_bench", True) or not state.get(
            "buttocks_on_bench", True
        ):
            result.add_failure("Shoulders or buttocks not in contact with the bench.")

    def rule_grip_validity(
        self, state: Dict[str, Any], result: LiftEvaluationResult
    ) -> None:
        """
        Validates the lifter's grip during the bench press.

        :param state: The lifter's state.
        :param result: The evaluation result to update.
        :return: None
        """
        if state.get("grip_width", 82) > 81:
            result.add_failure("Grip width exceeds 81cm.")
        if state.get("thumbs_not_wrapped", False):
            result.add_failure("Thumbless grip is not permitted.")

    def rule_no_belt_contact(
        self, state: Dict[str, Any], result: LiftEvaluationResult
    ) -> None:
        """
        Validates that the bar does not contact the lifter's belt.

        :param state: The lifter's state.
        :param result: The evaluation result to update.
        :return: None
        """
        if state.get("bar_touches_belt", False):
            result.add_failure("Bar touched the lifter's belt.")

    def rule_no_downward_movement(
        self, state: Dict[str, Any], result: LiftEvaluationResult
    ) -> None:
        """
        Validates that there is no downward movement during the bench press.

        :param state: The lifter's state.
        :param result: The evaluation result to update.
        :return: None
        """
        if state.get("downward_movement_during_press", False):
            result.add_failure("Downward movement during the press.")

    def rule_wait_for_start_command(
        self, state: Dict[str, Any], result: LiftEvaluationResult
    ) -> None:
        """
        Ensures the lifter waits for the 'START' command.

        :param state: The lifter's state.
        :param result: The evaluation result to update.
        :return: None
        """
        if state.get("did_not_wait_for_start_command", False):
            result.add_failure("Did not wait for 'START' command.")

    def rule_no_rack_contact(
        self, state: Dict[str, Any], result: LiftEvaluationResult
    ) -> None:
        """
        Validates that the bar does not contact the rack.

        :param state: The lifter's state.
        :param result: The evaluation result to update.
        :return: None
        """
        if state.get("bar_contact_rack", False):
            result.add_failure("Bar contacted the rack during the lift.")

    def rule_complete_lockout(
        self, state: Dict[str, Any], result: LiftEvaluationResult
    ) -> None:
        """
        Validates that the lift achieves a complete lockout.

        :param state: The lifter's state.
        :param result: The evaluation result to update.
        :return: None
        """
        if not state.get("lockout_complete", True):
            result.add_failure("Failed to achieve a complete lockout.")


class Deadlift:
    """
    Evaluates a deadlift attempt based on defined rules.
    """

    def evaluate(self, lifter_state: Dict[str, Any]) -> LiftEvaluationResult:
        """
        Evaluates a lifter's deadlift performance.

        :param lifter_state: The state of the lifter during the deadlift attempt.
        :returns: The result of the deadlift evaluation.
        """
        result: LiftEvaluationResult = LiftEvaluationResult()
        self.rule_no_downward_movement(lifter_state, result)
        self.rule_knees_and_shoulders_locked(lifter_state, result)
        self.rule_no_thigh_support(lifter_state, result)
        self.rule_wait_for_down_command(lifter_state, result)
        self.rule_controlled_lowering(lifter_state, result)
        return result

    def rule_no_downward_movement(
        self, state: Dict[str, Any], result: LiftEvaluationResult
    ) -> None:
        """
        Validates that there is no premature downward movement in the deadlift.

        :param state: The lifter's state.
        :param result: The evaluation result to update.
        :return: None
        """
        if state.get("downward_movement", False):
            result.add_failure("Downward movement of the bar before completion.")

    def rule_knees_and_shoulders_locked(
        self, state: Dict[str, Any], result: LiftEvaluationResult
    ) -> None:
        """
        Validates that the knees and shoulders are locked in proper position.

        :param state: The lifter's state.
        :param result: The evaluation result to update.
        :return: None
        """
        if not state.get("knees_locked", True):
            result.add_failure("Knees not locked.")
        if not state.get("shoulders_back", True):
            result.add_failure("Shoulders not in final position.")

    def rule_no_thigh_support(
        self, state: Dict[str, Any], result: LiftEvaluationResult
    ) -> None:
        """
        Ensures the bar is not supported on the thighs.

        :param state: The lifter's state.
        :param result: The evaluation result to update.
        :return: None
        """
        if state.get("bar_support_on_thighs", False):
            result.add_failure("Bar supported on thighs.")

    def rule_wait_for_down_command(
        self, state: Dict[str, Any], result: LiftEvaluationResult
    ) -> None:
        """
        Validates that the lifter waits for the 'DOWN' command.

        :param state: The lifter's state.
        :param result: The evaluation result to update.
        :return: None
        """
        if not state.get("waited_for_down_command", True):
            result.add_failure("Did not wait for 'DOWN' command.")

    def rule_controlled_lowering(
        self, state: Dict[str, Any], result: LiftEvaluationResult
    ) -> None:
        """
        Ensures the lowering phase is controlled.

        :param state: The lifter's state.
        :param result: The evaluation result to update.
        :return: None
        """
        if state.get("released_bar", False):
            result.add_failure("Bar released before full lowering.")


if __name__ == "__main__":
    # Example lifter state for testing.
    example_squat_state: Dict[str, Any] = {
        "bar_position": 2,
        "knees_locked": True,
        "descent_below_parallel": True,
        "double_bounce": False,
        "downward_movement_during_ascent": False,
        "knees_locked_at_finish": True,
        "waited_for_rack_command": True,
        "spotter_contact": False,
        "elbows_touch_legs": False,
    }

    # Instantiate evaluators.
    squat_evaluator = Squat()
    bench_evaluator = BenchPress()
    deadlift_evaluator = Deadlift()

    # Evaluate example data.
    squat_result = squat_evaluator.evaluate(example_squat_state)
    print(squat_result)
