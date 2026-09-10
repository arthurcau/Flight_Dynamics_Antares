def _transfer_rocket_components(rocket, stoch_rocket):
    from rocketpy.rocket.aero_surface import NoseCone, TrapezoidalFins, EllipticalFins, Tail
    for surface_tuple in rocket.aerodynamic_surfaces:
        surface = surface_tuple.component
        pos = surface_tuple.position[2]
        if isinstance(surface, NoseCone):
            stoch_rocket.add_nose(surface, position=pos)
        elif isinstance(surface, TrapezoidalFins):
            stoch_rocket.add_trapezoidal_fins(surface, position=pos)
        elif isinstance(surface, EllipticalFins):
            stoch_rocket.add_elliptical_fins(surface, position=pos)
        elif isinstance(surface, Tail):
            stoch_rocket.add_tail(surface, position=pos)
    
    for rb_tuple in rocket.rail_buttons:
        stoch_rocket.set_rail_buttons(rb_tuple.component, lower_button_position=rb_tuple.position[2])
        
    for parachute in rocket.parachutes:
        stoch_rocket.add_parachute(parachute)
