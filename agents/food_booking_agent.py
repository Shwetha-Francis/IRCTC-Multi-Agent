
def food_booking_agent(passenger_name, train_number, journey_date, station, food_item, quantity):
    # Store the food order details in a dictionary.
    order = {
        "passenger": passenger_name,
        "train_number": train_number,
        "journey_date": journey_date,
        "delivery_station": station,
        "food_item": food_item,
        "quantity": quantity,

        "status": "Food order details collected"
    }

    # Return the order so other agents can use these details.
    return order

if __name__ == "__main__":
    # Provide sample details to test the food booking agent.
    result = food_booking_agent(
        "Test Passenger",
        "12952",
        "2026-11-02",
        "Surat",
        "Veg Biryani",
        2
    )

    # Display the collected order details in the terminal.
    print(result)
