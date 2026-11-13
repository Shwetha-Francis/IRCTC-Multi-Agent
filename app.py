import sys 
import json
import re 
import io

from pathlib import Path
from contextlib import redirect_stdout 
from datetime import datetime
from typing import TypedDict

from dotenv import load_dotenv

from langchain_groq import ChatGroq 
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage 

from langgraph.graph import StateGraph, START, END 
                                                   

PROJECT_DIR = Path(__file__).resolve().parent 
sys.path.insert(0, str(PROJECT_DIR))

load_dotenv()

# agents imports

from agents.profile_agent import (
    register_user, 
    login_user, 
    save_booking, 
    get_booking_history, 
    save_food_order 
)

from agents.train_search_agent import (
    find_station, 
    train_search_agent 
)

from agents.ticket_booking_agent import ticket_booking_agent
from agents.food_booking_agent import food_booking_agent
from agents.live_tracking_agent import live_tracking_agent
from agents.railway_faq_agent import railway_faq_agent


llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0 
)


# langGraph state
class ChatState(TypedDict, total=False):
    messages: list #Stores the conversation messages.
    user_id: int
    passenger_name: str #Stores the passenger's name.
    pending_train_search: dict #Remembers station options when the destination is ambiguous.
    intent: str #Identifies what the current user wants.
    pending_intent: str #Remembers an unfinished booking or tracking request.
    pending_text: str #Stores earlier details so the user can provide missing information later.

#categories your router recognizes. The category determines which agent receives the user's request.
INTENTS = [
    "train_search",
    "ticket_booking",
    "food_booking",
    "live_tracking",
    "booking_history",
    "railway_faq",
    "general",
]


def extract_details(question, fields):

    prompt = f"""
    Today's date is {datetime.now().strftime('%Y-%m-%d')}.
    Extract the following details from the user's message:
    {fields}

    User message: {question}

    Return only a valid JSON object.
    Use null for missing information.
    For journey_date, use YYYY-MM-DD format.
    Convert relative dates like "tomorrow" or "next Friday" using today's date.
    """

    response = llm.invoke(prompt)

    try:
        content = response.content
        start = content.find("{")
        end = content.rfind("}") + 1

        if start == -1 or end == 0:
            return {}

        return json.loads(content[start:end])

    except (json.JSONDecodeError, TypeError):
        return {}


def normalize_station_name(name):

    name = name.lower().replace("junction", "jn")
    name = re.sub(r"[^a-z0-9 ]", "", name)

    return " ".join(name.split())


def resolve_station(query):

    result = find_station(query)

    if result["status"] == "success":
        return result["station"], None

    if result["status"] == "not_found":
        return None, "Station not found. Please check the station name."

    if result["status"] == "multiple":

        stations = result["stations"]

        exact_match = next(
            (
                station for station in stations
                if query.upper() == station["code"].upper()
                or normalize_station_name(query)
                == normalize_station_name(station["name"])
            ),
            None
        )

        if exact_match:
            return exact_match, None

        options = "\n".join(
            f"{station['name']} ({station['code']})"
            for station in stations
        )

        return None, "Multiple stations found. Please specify:\n" + options

    return None, "Unable to identify the station."


def format_duration(minutes):

    hours = minutes // 60
    remaining_minutes = minutes % 60

    return f"{hours} hr {remaining_minutes} min"


def handle_train_search(question, pending_search=None):

    # Continue an unfinished search when the user selects a station.
    if pending_search:

        selected = question.strip().upper()

        if selected in ["CANCEL", "STOP", "EXIT"]:
            return "Train search cancelled.", None

        destination_station = next(
            (
                station
                for station in pending_search["destination_options"]
                if selected == station["code"].upper()
                or normalize_station_name(question)
                == normalize_station_name(station["name"])
            ),
            None
        )

        if not destination_station:

            options = "\n".join(
                f"{station['name']} ({station['code']})"
                for station in pending_search["destination_options"]
            )

            return (
                "Please select one of these stations:\n"
                + options
                + "\nType 'cancel' to stop."
            ), pending_search

        source_station = pending_search["source_station"]
        journey_date = pending_search["journey_date"]

    else:

        # Extract details for a new train search.
        details = extract_details(
            question,
            ["source", "destination", "journey_date"]
        )

        source = details.get("source")
        destination = details.get("destination")
        journey_date = details.get("journey_date")

        if not source or not destination or not journey_date:
            return (
                "Please provide departure station, destination station "
                "and journey date."
            ), None

        try:
            datetime.strptime(journey_date, "%Y-%m-%d")
        except ValueError:
            return "Please provide the date in YYYY-MM-DD format.", None

        # Identify the departure station.
        source_station, error = resolve_station(source)

        if error:
            return f"Departure station: {error}", None

        # Identify the destination station.
        destination_result = find_station(destination)

        if destination_result["status"] == "success":

            destination_station = destination_result["station"]

        elif destination_result["status"] == "multiple":

            stations = destination_result["stations"]

            exact_match = next(
                (
                    station for station in stations
                    if destination.upper() == station["code"].upper()
                    or normalize_station_name(destination)
                    == normalize_station_name(station["name"])
                ),
                None
            )

            if exact_match:
                destination_station = exact_match

            else:

                # Save the search details until the user selects a station.
                pending_search = {
                    "source_station": source_station,
                    "journey_date": journey_date,
                    "destination_options": stations
                }

                options = "\n".join(
                    f"{station['name']} ({station['code']})"
                    for station in stations
                )

                return (
                    "Multiple destination stations found. "
                    "Please select one:\n" + options
                ), pending_search

        else:
            return "Destination station not found.", None

    # Retrieve trains using the RailRadar API.
    result = train_search_agent(
        source_station["code"],
        destination_station["code"],
        journey_date
    )

    if not result.get("success"):
        return "Train search was unsuccessful. Please try again.", None

    trains = result.get("data", {}).get("trains", [])

    if not trains:
        return "No trains were found for this journey.", None

    # Prepare the journey date and weekday.
    journey_day = datetime.strptime(journey_date, "%Y-%m-%d")
    journey_weekday = journey_day.strftime("%a").lower()
    weekday_name = journey_day.strftime("%A")

    answer = (
        f"TRAIN RESULTS\n"
        f"Route: {source_station['name']} to {destination_station['name']}\n"
        f"Journey Date: {journey_date} ({weekday_name})\n"
        f"====================================\n"
    )

    # Display the information returned by the API.
    for train in trains:

        train_info = train.get("train", {})
        from_info = train.get("from", {})
        to_info = train.get("to", {})

        name = train_info.get("name", "Name unavailable")
        number = train_info.get("number", "Unavailable")

        departure = from_info.get("departure", "Unavailable")
        arrival = to_info.get("arrival", "Unavailable")

        duration = train.get("duration")

        if isinstance(duration, (int, float)):
            duration_text = format_duration(int(duration))
        else:
            duration_text = "Unavailable"

        # Check the train's scheduled running days.
        run_days = train_info.get("runDays", [])

        if run_days:

            running_days = ", ".join(
                day.capitalize() for day in run_days
            )

            runs_on_date = journey_weekday in [
                str(day).lower()[:3] for day in run_days
            ]

            running_status = (
                "Scheduled to run"
                if runs_on_date
                else "Not scheduled to run"
            )

        else:

            running_days = "Unavailable"
            running_status = "Running days not provided"

        # Check whether arrival is on the next day.
        departure_day = from_info.get("day", 1)
        arrival_day = to_info.get("day", 1)

        if (
            isinstance(departure_day, int)
            and isinstance(arrival_day, int)
            and arrival_day > departure_day
        ):
            arrival += " (Next day)"

        answer += (
            f"\nTrain: {name}\n"
            f"Train Number: {number}\n"
            f"Departure: {departure}\n"
            f"Arrival: {arrival}\n"
            f"Duration: {duration_text}\n"
            f"Running Days: {running_days}\n"
            f"Journey Date Status: {running_status}\n"
        )

    return answer, None


def handle_ticket_booking(question, user):

    details = extract_details(
        question,
        [
            "train_number",
            "source",
            "destination",
            "journey_date",
            "travel_class"
        ]
    )

    train_number = details.get("train_number")
    source = details.get("source")
    destination = details.get("destination")
    journey_date = details.get("journey_date")
    travel_class = details.get("travel_class")

    if not all([
        train_number,
        source,
        destination,
        journey_date,
        travel_class
    ]):
        return (
            "Please provide train number, departure station, "
            "destination, journey date and travel class."
        )

    try:
        datetime.strptime(journey_date, "%Y-%m-%d")
    except ValueError:
        return "Please provide the date in YYYY-MM-DD format."

    booking = ticket_booking_agent(
        user["passenger_name"],
        str(train_number),
        source,
        destination,
        journey_date,
        travel_class
    )

    # Save the simulated booking in the user's profile.
    result = save_booking(user["user_id"], booking)

    if not result.get("success"):
        return "Booking details were collected, but saving failed."

    return (
        "Your simulated booking details have been saved.\n\n"
        f"Passenger: {booking['passenger']}\n"
        f"Train: {booking['train_number']}\n"
        f"Route: {booking['source']} to {booking['destination']}\n"
        f"Date: {booking['journey_date']}\n"
        f"Class: {booking['travel_class']}\n"
        f"Booking ID: {result['booking_id']}\n"
        f"Status: {booking['status']}\n\n"
        "This is a demo booking, not an actual IRCTC reservation."
    )


def handle_food_booking(question, user):

    # Extract food booking details from the user's message
    details = extract_details(
        question,
        [
            "train_number",
            "journey_date",
            "station",
            "food_item",
            "quantity"
        ]
    )

    train_number = details.get("train_number")
    journey_date = details.get("journey_date")
    station = details.get("station")
    food_item = details.get("food_item")
    quantity = details.get("quantity")

    # Check whether all required details are available
    if not all([
        train_number,
        journey_date,
        station,
        food_item,
        quantity
    ]):
        return (
            "Please provide train number, journey date, "
            "delivery station, food item and quantity."
        )

    # Validate date and quantity
    try:
        datetime.strptime(journey_date, "%Y-%m-%d")
        quantity = int(quantity)

        if quantity <= 0:
            return "Quantity must be greater than zero."

    except (ValueError, TypeError):
        return "Please check the journey date and food quantity."

    # Collect the food order details
    order = food_booking_agent(
        user["passenger_name"],
        str(train_number),
        journey_date,
        station,
        food_item,
        quantity
    )

    # Save the food order in the SQLite database
    result = save_food_order(user["user_id"], order)

    if not result["success"]:
        return (
            "Food order details were collected, "
            "but saving them failed: " + result["message"]
        )

    # Display the order details
    return (
        "Your simulated food order details were saved successfully.\n\n"
        f"Order ID: {result['order_id']}\n"
        f"Passenger: {order['passenger']}\n"
        f"Train: {order['train_number']}\n"
        f"Date: {order['journey_date']}\n"
        f"Station: {order['delivery_station']}\n"
        f"Food: {order['food_item']}\n"
        f"Quantity: {order['quantity']}\n\n"
        "Order confirmed."
    )


def handle_live_tracking(question):

    details = extract_details(
        question,
        ["train_number", "journey_date"]
    )

    train_number = details.get("train_number")
    journey_date = details.get("journey_date")

    # Find the train number directly if the LLM misses it.
    if not train_number:
        match = re.search(r"\b\d{5}\b", question)

        if match:
            train_number = match.group()

    if not train_number:
        return "Please provide the five-digit train number."

    # Capture the tracking agent's printed output.
    output = io.StringIO()

    with redirect_stdout(output):
        live_tracking_agent(str(train_number), journey_date)

    answer = output.getvalue()

    if not answer.strip():
        return "No tracking information was returned."

    return answer


def handle_booking_history(user):

    bookings = get_booking_history(user["user_id"])

    if not bookings:
        return "You don't have any saved bookings yet."

    answer = "YOUR BOOKING HISTORY\n"

    for booking in bookings:

        answer += (
            f"\nBooking ID: {booking['booking_id']}\n"
            f"Train: {booking['train_number']}\n"
            f"Route: {booking['source']} to {booking['destination']}\n"
            f"Date: {booking['journey_date']}\n"
            f"Class: {booking['travel_class']}\n"
            f"Status: {booking['status']}\n"
        )

    return answer


# ---------- router ----------

def classify_intent(question):

    prompt = f"""
    Classify the user's message into exactly one label.

    Labels:
    - train_search: find trains between two stations
    - ticket_booking: book or reserve a ticket
    - food_booking: order food for a train journey
    - live_tracking: running status or live location of a train
    - booking_history: view the user's saved bookings
    - railway_faq: railway rules, refunds, cancellation, tatkal, baggage, RAC, waiting list
    - general: anything else

    Examples:
    "trains from Kochi to Chennai tomorrow" -> train_search
    "book a ticket on 12625 in 3A" -> ticket_booking
    "order 2 biryani at Coimbatore" -> food_booking
    "where is train 12625 now" -> live_tracking
    "show my bookings" -> booking_history
    "what is the refund rule for tatkal" -> railway_faq
    "hello" -> general

    Message: {question}

    Return only the label.
    """

    label = llm.invoke(prompt).content.strip().lower()

    if label in INTENTS:
        return label

    return next((i for i in INTENTS if i in label), "general")


def router_node(state: ChatState):

    question = state["messages"][-1].content
    pending = state.get("pending_train_search")

    # Continue station selection only if the reply looks like an answer to it.
    if pending:

        selected = question.strip().upper()

        is_answer = selected in ["CANCEL", "STOP", "EXIT"] or any(
            selected == s["code"].upper()
            or normalize_station_name(question) == normalize_station_name(s["name"])
            for s in pending["destination_options"]
        )

        if is_answer:
            return {"intent": "train_search"}

        # Unrelated message: drop the pending search instead of trapping the user.
        return {
            "intent": classify_intent(question),
            "pending_train_search": None
        }

    # Continue an incomplete booking/tracking request.
    pending_intent = state.get("pending_intent")

    if pending_intent:

        if question.strip().lower() in ["cancel", "stop", "exit"]:
            return {
                "intent": "general",
                "pending_intent": None,
                "pending_text": None
            }

        new_intent = classify_intent(question)

        if new_intent in ["general", pending_intent]:
            return {"intent": pending_intent}

        return {
            "intent": new_intent,
            "pending_intent": None,
            "pending_text": None
        }

    return {"intent": classify_intent(question)}


def route_by_intent(state: ChatState):  # conditional routing function for the graph edges
    return state["intent"]


# ---------- nodes ----------

def reply(state, answer, **extra):
    return {
        "messages": state["messages"] + [AIMessage(content=str(answer))],
        **extra
    }


def get_user(state):
    return {
        "user_id": state["user_id"],
        "passenger_name": state["passenger_name"]
    }


def safe_node(func):
    """Wrap a node so one failure doesn't crash the chat."""

    def wrapper(state: ChatState):
        try:
            return func(state)
        except Exception as error:
            return reply(
                state,
                f"Sorry, I couldn't complete that request. Error: {error}",
                pending_intent=None,
                pending_text=None
            )

    return wrapper


def run_with_pending(state, intent, handler):
    question = state["messages"][-1].content
    earlier = state.get("pending_text")
    full = f"{earlier} {question}" if earlier else question

    answer = handler(full)

    if str(answer).startswith("Please provide"):
        return reply(state, answer, pending_intent=intent, pending_text=full)

    return reply(state, answer, pending_intent=None, pending_text=None)


@safe_node
def train_search_node(state: ChatState): #Calls handle_train_search() and saves pending station selections.
    question = state["messages"][-1].content
    answer, pending = handle_train_search(
        question, state.get("pending_train_search")
    )
    return reply(state, answer, pending_train_search=pending)


@safe_node
def ticket_booking_node(state: ChatState): #Calls handle_ticket_booking() through run_with_pending()
    user = get_user(state)
    return run_with_pending(
        state, "ticket_booking",
        lambda q: handle_ticket_booking(q, user)
    )


@safe_node
def food_booking_node(state: ChatState): #Calls handle_food_booking() through run_with_pending()
    user = get_user(state)
    return run_with_pending(
        state, "food_booking",
        lambda q: handle_food_booking(q, user)
    )


@safe_node
def live_tracking_node(state: ChatState): #Calls handle_live_tracking() through run_with_pending()
    return run_with_pending(
        state, "live_tracking",
        handle_live_tracking
    )


@safe_node
def booking_history_node(state: ChatState):  #Retrieves and displays the user's booking history.
    return reply(state, handle_booking_history(get_user(state)))


@safe_node
def railway_faq_node(state: ChatState): #Sends the question to the railway FAQ agent.
    question = state["messages"][-1].content
    return reply(state, railway_faq_agent(question))


@safe_node
def general_node(state: ChatState): #Uses the LLM to answer general questions.
    # Keep the system prompt + last 10 messages to avoid unbounded context.
    messages = state["messages"]
    trimmed = messages[:1] + messages[1:][-10:]
    response = llm.invoke(trimmed)
    return reply(state, response.content)


# ---------- graph ----------

builder = StateGraph(ChatState)

builder.add_node("router", router_node)
builder.add_node("train_search", train_search_node)
builder.add_node("ticket_booking", ticket_booking_node)
builder.add_node("food_booking", food_booking_node)
builder.add_node("live_tracking", live_tracking_node)
builder.add_node("booking_history", booking_history_node)
builder.add_node("railway_faq", railway_faq_node)
builder.add_node("general", general_node)

builder.add_edge(START, "router")

builder.add_conditional_edges(
    "router",
    route_by_intent,
    {intent: intent for intent in INTENTS}
)

for intent in INTENTS:
    builder.add_edge(intent, END)

chatbot_graph = builder.compile()


def start_chatbot(user):

    messages = [
        SystemMessage(
            content=(
                "You are a friendly personal IRCTC railway assistant. "
                f"The logged-in passenger is {user['passenger_name']}. "
                "Help with railway-related questions. "
                "Never invent train information. "
                "Never claim a booking or food order is confirmed "
                "unless an actual confirmation is received. "
                "Ticket and food bookings in this project are simulated."
            )
        )
    ]

    pending_train_search = None
    pending_intent = None
    pending_text = None

    print(f"\nWelcome, {user['passenger_name']}!")
    print("You are now chatting with your IRCTC assistant.")
    print("Type 'logout' to log out.\n")

    while True:

        question = input("You: ").strip()

        if not question:
            continue

        if question.lower() == "logout":
            print("\nLogged out successfully.\n")
            break

        messages.append(HumanMessage(content=question))

        # Send the conversation and user information to LangGraph.
        result = chatbot_graph.invoke({
            "messages": messages,
            "user_id": user["user_id"],
            "passenger_name": user["passenger_name"],
            "pending_train_search": pending_train_search,
            "pending_intent": pending_intent,
            "pending_text": pending_text
        })

        messages = result["messages"]
        pending_train_search = result.get("pending_train_search")
        pending_intent = result.get("pending_intent")
        pending_text = result.get("pending_text")

        print("\nAssistant:", messages[-1].content, "\n")


def main():

    while True:

        print("\n========== IRCTC PERSONAL ASSISTANT ==========")
        print("1. Login")
        print("2. Register")
        print("3. Exit")

        choice = input("\nChoose an option: ").strip()

        if choice == "1":

            username = input("Username: ").strip()
            password = input("Password: ").strip()

            user = login_user(username, password)

            if user.get("success"):

                print("\nLogin Successful")
                start_chatbot(user)

            else:

                print("\nLogin Failed:", user.get("message"))

        elif choice == "2":

            username = input("Create username: ").strip()
            password = input("Create password: ").strip()
            passenger_name = input("Passenger name: ").strip()

            if not username or not password or not passenger_name:
                print("\nPlease fill in all the details.")
                continue

            result = register_user(
                username,
                password,
                passenger_name
            )

            print("\n", result.get("messages", result.get("message")))

        elif choice == "3":

            print("\nThank you for using the IRCTC assistant.")
            break

        else:

            print("\nInvalid option. Please choose 1, 2 or 3.")


if __name__ == "__main__":
    main()