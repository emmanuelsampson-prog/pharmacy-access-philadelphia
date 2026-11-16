"""Transparent tailpipe-CO2 scenarios, never observed emissions estimates."""
import numpy as np

METERS_PER_MILE = 1609.344

def incremental_co2_kg(delta_one_way_m, trips=1, car_share=1.,
                       detour_factor=1.3, additional_trip_share=1.,
                       grams_per_vehicle_mile=400.):
    """Extra CO2 for dedicated round trips, one traveler per vehicle.

    delta_one_way_m: modeled change in straight-line distance. detour_factor
    converts it into an assumed route increment, not a measured route.
    additional_trip_share accounts for trip chaining / delivery / foregone trips.
    A 400 g/vehicle-mile factor describes a typical gasoline vehicle (EPA), not
    the Philadelphia fleet and not lifecycle CO2e. No transit estimate is made.
    """
    distance = np.asarray(delta_one_way_m, dtype=float)
    if not np.isfinite(distance).all() or (distance < -1e-6).any():
        raise ValueError("Distance increments must be finite and nonnegative")
    if trips < 0 or detour_factor < 1 or grams_per_vehicle_mile < 0:
        raise ValueError("Invalid scenario parameter")
    if not 0 <= car_share <= 1 or not 0 <= additional_trip_share <= 1:
        raise ValueError("Shares must lie in [0,1]")
    return (np.maximum(distance,0) * 2 * detour_factor / METERS_PER_MILE
            * trips * car_share * additional_trip_share * grams_per_vehicle_mile / 1000)
