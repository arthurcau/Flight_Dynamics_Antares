"""Local RocketPy adapters; never change dependency classes globally."""

import copy
import numpy as np
from rocketpy import StochasticEnvironment, MonteCarlo, Flight
from rocketpy.rocket.aero_surface import NoseCone, TrapezoidalFins, EllipticalFins, Tail
from rocketpy.stochastic import (
    StochasticTrapezoidalFins,
    StochasticNoseCone,
    StochasticEllipticalFins,
    StochasticTail,
)

from antares_fd.config.exceptions import ConfigurationError


class ProfileStochasticEnvironment(StochasticEnvironment):
    """Sample a whole profile with a seeded generator; avoid mutating inputs."""
    def __init__(self, environment, profiles=None, **kwargs):
        super().__init__(environment, **kwargs)
        self._profiles = profiles or [environment]
        self._selected_profile = None

    def _set_stochastic(self, seed=None):
        super()._set_stochastic(seed)
        self._profile_rng = np.random.default_rng(seed)

    def set_profile(self, profile):
        self._selected_profile = profile

    def create_object(self):
        index = int(self._profile_rng.integers(len(self._profiles)))
        profile = self._selected_profile if self._selected_profile is not None else self._profiles[index]
        self.obj = copy.deepcopy(profile)
        self._wind_velocity_x = self.obj.wind_velocity_x
        self._wind_velocity_y = self.obj.wind_velocity_y
        result = super().create_object()
        self.last_rnd_dict["atmospheric_profile_index"] = index if self._selected_profile is None else "presampled"
        return result


class ConfiguredMonteCarlo(MonteCarlo):
    """Preserve all nominal solver settings when RocketPy builds each case."""
    def _MonteCarlo__run_single_simulation(self):
        nominal = self.flight.obj
        parameters = next(self.flight.dict_generator())
        parameters.update({key: getattr(nominal, key) for key in
                           ("rtol", "atol", "max_time", "max_time_step", "min_time_step")})
        parameters["time_overshoot"] = self.flight.time_overshoot
        parameters["terminate_on_apogee"] = self.flight.terminate_on_apogee
        return Flight(rocket=self.rocket.create_object(), environment=self.environment.create_object(), **parameters)


class LengthDefinedStochasticFins(StochasticTrapezoidalFins):
    """Use sweep length as the independent geometric parameter.

    RocketPy 1.13 emits both sweep angle and length when recreating fins; the
    deterministic constructor requires only one. Nominal length is preserved.
    """
    def create_object(self):
        values = dict(next(self.dict_generator()))
        values.pop("sweep_angle", None)
        return TrapezoidalFins(**values)


def _transfer_rocket_components(rocket, stoch_rocket):
    for item in rocket.aerodynamic_surfaces:
        surface, position = item.component, item.position[2]
        if isinstance(surface, NoseCone):
            stoch_rocket.add_nose(StochasticNoseCone(surface), position=[position])
        elif isinstance(surface, TrapezoidalFins):
            stoch_rocket.add_trapezoidal_fins(LengthDefinedStochasticFins(surface), position=[position])
        elif isinstance(surface, EllipticalFins):
            stoch_rocket.add_elliptical_fins(StochasticEllipticalFins(surface), position=[position])
        elif isinstance(surface, Tail):
            stoch_rocket.add_tail(StochasticTail(surface), position=[position])
        else:
            raise ConfigurationError(f"Unsupported stochastic surface: {type(surface).__name__}")
    for item in rocket.rail_buttons:
        stoch_rocket.set_rail_buttons(item.component, lower_button_position=[item.position[2]])
    for parachute in rocket.parachutes:
        stoch_rocket.add_parachute(parachute)
