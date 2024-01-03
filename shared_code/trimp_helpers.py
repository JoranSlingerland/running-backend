"""Helper functions for TRIMP calculations"""

import math
from typing import Optional


def calculate_hr_reserve(
    avg_workout_hr: float,
    resting_hr: float,
    max_hr: float,
) -> float:
    """
    Calculate HR reserve

    Parameters
    ----------
    avg_workout_hr : float
        The average heart rate of the activity.
    resting_hr : float
        The resting heart rate of the individual.
    max_hr : float
        The maximum heart rate of the individual.

    Returns
    -------
    float
        The calculated HR reserve.

    References
    ----------
        - https://fellrnr.com/wiki/Heart_Rate_Reserve

    """
    return (avg_workout_hr - resting_hr) / (max_hr - resting_hr)


def calculate_pace_reserve(
    avg_workout_pace: float,
    threshold_pace: float,
) -> float:
    """Calculate Pace reserve"""
    return avg_workout_pace / threshold_pace


def calculate_hr_max_percentage(avg_workout_hr: float, max_hr: float) -> float:
    """Calculate HR max percentage"""
    return avg_workout_hr / max_hr


def calculate_vo2max_percentage(hr_max_percentage: float) -> Optional[float]:
    """
    Convert HR max percentage to VO2 max percentage.

    Parameters
    ----------
    hr_max_percentage : float
        The average heart rate of the activity as a percentage of the maximum heart rate.

    Returns
    -------
    Optional[float]
        The calculated VO2 max percentage.

    References
    ----------
        - https://journals.lww.com/acsm-msse/Fulltext/2007/02000/Relationship_between__HRmax,__HR_Reserve,.18.aspx
        - https://www.ncsf.org/pdf/ceu/relationship_between_percent_hr_max_and_percent_vo2_max.pdf
        - https://fellrnr.com/wiki/Heart_Rate_Reserve
    """
    vo2max_percentage = (hr_max_percentage - 0.26) / 0.706

    if 0 <= vo2max_percentage <= 1:
        return vo2max_percentage
    else:
        return None


def gender_constant() -> dict:
    """Gender constant"""
    return {
        "male": 1.92,
        "female": 1.67,
    }


def calculate_hr_trimp(
    duration: float,
    hr_reserve: float,
    gender: str,
    duration_in_seconds: bool = False,
) -> float:
    """
    Calculate HR TRIMP.

    Parameters
    ----------
    duration : float
        The duration of the activity. This can be in minutes or seconds, depending on the value of duration_in_seconds.
    hr_reserve : float
        The reserve heart rate of the activity as a percentage.
    gender : str
        The gender of the individual. This should be either "male" or "female".
    duration_in_seconds : bool, optional
        A boolean value indicating whether the duration is in seconds. If False, the duration is assumed to be in minutes (default is False).

    Returns
    -------
    float
        The calculated HR TRIMP.

    References
    ----------
        - https://fellrnr.com/wiki/TRIMP
    """
    if duration_in_seconds:
        duration = duration / 60

    return (
        duration * hr_reserve * 0.64 * math.exp(gender_constant()[gender] * hr_reserve)
    )


def calculate_pace_trimp(
    duration: float,
    pace_reserve: float,
    gender: str,
    duration_in_seconds: bool = False,
) -> float:
    """
    Calculate Pace TRIMP.

    Parameters
    ----------
    duration : float
        The duration of the activity. This can be in minutes or seconds, depending on the value of duration_in_seconds.
    pace_reserve : float
        The reserve pace of the activity as a percentage of the threshold pace.
    gender : str
        The gender of the individual. This should be either "male" or "female".
    duration_in_seconds : bool, optional
        A boolean value indicating whether the duration is in seconds. If False, the duration is assumed to be in minutes (default is False).

    Returns
    -------
    float
        The calculated Pace TRIMP.

    References
    ----------
        - https://fellrnr.com/wiki/TRIMP
    """
    if duration_in_seconds:
        duration = duration / 60

    return (
        duration
        * pace_reserve
        * 0.64
        * math.exp(gender_constant()[gender] * pace_reserve)
    )


def calculate_vo2max_estimate(
    distance: float,
    duration: float,
    hr_max_percentage: float,
    duration_in_seconds: bool = False,
) -> dict[str, float]:
    """
    Calculate VO2 Max.

    Calculations are still in progress and this is only a rough estimate.

    Parameters
    ----------
    distance : float
        The distance of the activity in meters.
    duration : float
        The duration of the activity. This can be in minutes or seconds, depending on the value of duration_in_seconds.
    hr_max_percentage : float
        The average heart rate of the activity as a percentage of the maximum heart rate.
    duration_in_seconds : bool, optional
        A boolean value indicating whether the duration is in seconds. If False, the duration is assumed to be in minutes (default is False).

    Returns
    -------
    dict[str, float]
        A dictionary containing the workout VO2 Max, the VO2 Max percentage, and the estimated VO2 Max.

    References
    ----------
        - https://www.omnicalculator.com/sports/vo2-max-runners
    """
    if duration_in_seconds:
        duration = duration / 60

    meters_per_minute = distance / duration

    unadjusted_vo2max_for_workout = (
        -4.60 + 0.182258 * meters_per_minute + 0.000104 * meters_per_minute**2
    )
    vo2max_percentage_for_workout = (
        0.8
        + 0.1894393 * (2.71828 ** (-0.012778 * duration))
        + 0.2989558 * (2.71828 ** (-0.1932605 * duration))
    )
    workout_vo2_max = unadjusted_vo2max_for_workout / vo2max_percentage_for_workout

    vo2_max_percentage = calculate_vo2max_percentage(hr_max_percentage)
    if vo2_max_percentage is None:
        estimated_vo2_max = None
    else:
        estimated_vo2_max = workout_vo2_max / vo2_max_percentage

    return {
        "workout_vo2_max": workout_vo2_max,
        "vo2_max_percentage": vo2_max_percentage,
        "estimated_vo2_max": estimated_vo2_max,
    }
