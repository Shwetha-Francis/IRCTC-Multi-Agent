def ticket_booking_agent(
    passenger_name,
    train_number,
    source,
    destination,
    journey_date,
    travel_class
):
    # Prepare the booking details.
    return {
        "passenger": passenger_name,
        "train_number": train_number,
        "source": source,
        "destination": destination,
        "journey_date": journey_date,
        "travel_class": travel_class,
        "status": "Booking details collected"
    }
