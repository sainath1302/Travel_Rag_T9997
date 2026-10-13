import os
import json
from pathlib import Path

import psycopg2
from dotenv import load_dotenv


# ============================================================
# 1. PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

OUTPUT_DIR = BASE_DIR / "data" / "processed"

OUTPUT_FILE = OUTPUT_DIR / "rag_documents.json"


# ============================================================
# 2. LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv(BASE_DIR / ".env")


# ============================================================
# 3. POSTGRESQL CONFIGURATION
# ============================================================

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "travel_rag",
    "user": "postgres",
    "password": os.getenv("POSTGRES_PASSWORD")
}


# ============================================================
# 4. CONNECT TO POSTGRESQL
# ============================================================

def get_connection():

    if not DB_CONFIG["password"]:

        raise ValueError(
            "POSTGRES_PASSWORD is not set in .env"
        )

    return psycopg2.connect(**DB_CONFIG)


# ============================================================
# 5. GET DESTINATIONS
# ============================================================

def get_destinations(cursor):

    cursor.execute("""
        SELECT
            destination_id,
            destination_name,
            state,
            district,
            region,
            latitude,
            longitude,
            altitude_m,
            popularity_score,
            accessibility,
            road_connectivity,
            minimum_days,
            ideal_days,
            maximum_days,
            safety_rating,
            permits_required,
            nearest_airport_name,
            nearest_airport_distance_km,
            nearest_railway_name,
            nearest_railway_distance_km,
            nearest_major_city,
            nearest_major_city_distance_km,
            language_spoken,
            mobile_network,
            internet_connectivity,
            atm_availability,
            last_updated
        FROM travel.destinations
        ORDER BY destination_id;
    """)

    columns = [
        description[0]
        for description in cursor.description
    ]

    rows = cursor.fetchall()

    return [
        dict(zip(columns, row))
        for row in rows
    ]


# ============================================================
# 6. GET ATTRACTIONS
# ============================================================

def get_attractions(cursor, destination_id):

    cursor.execute("""
        SELECT
            attraction_name,
            attraction_type
        FROM travel.attractions
        WHERE destination_id = %s
        ORDER BY attraction_id;
    """, (destination_id,))

    return cursor.fetchall()


# ============================================================
# 7. GET ACTIVITIES
# ============================================================

def get_activities(cursor, destination_id):

    cursor.execute("""
        SELECT
            activity_name
        FROM travel.activities
        WHERE destination_id = %s
        ORDER BY activity_id;
    """, (destination_id,))

    return [
        row[0]
        for row in cursor.fetchall()
    ]


# ============================================================
# 8. GET ACCOMMODATIONS
# ============================================================

def get_accommodations(cursor, destination_id):

    cursor.execute("""
        SELECT
            accommodation_type
        FROM travel.accommodations
        WHERE destination_id = %s
        ORDER BY accommodation_id;
    """, (destination_id,))

    return [
        row[0]
        for row in cursor.fetchall()
    ]


# ============================================================
# 9. GET BUDGETS
# ============================================================

def get_budgets(cursor, destination_id):

    cursor.execute("""
        SELECT
            budget_type,
            accommodation_min,
            accommodation_max,
            food_min,
            food_max,
            activities_min,
            activities_max,
            transport_min,
            transport_max,
            total_daily_min,
            total_daily_max
        FROM travel.budgets
        WHERE destination_id = %s
        ORDER BY budget_id;
    """, (destination_id,))

    columns = [
        description[0]
        for description in cursor.description
    ]

    rows = cursor.fetchall()

    return [
        dict(zip(columns, row))
        for row in rows
    ]


# ============================================================
# 10. GET SEASONS
# ============================================================

def get_seasons(cursor, destination_id):

    cursor.execute("""
        SELECT
            season_type,
            season_name
        FROM travel.seasons
        WHERE destination_id = %s
        ORDER BY season_id;
    """, (destination_id,))

    return cursor.fetchall()


# ============================================================
# 11. FORMAT VALUE
# ============================================================

def format_value(value):

    if value is None:
        return "Not specified"

    return str(value)


# ============================================================
# 12. CREATE DESTINATION DOCUMENT
# ============================================================

def create_document(
    destination,
    attractions,
    activities,
    accommodations,
    budgets,
    seasons
):

    destination_id = destination["destination_id"]

    destination_name = destination["destination_name"]

    # --------------------------------------------------------
    # ATTRACTIONS
    # --------------------------------------------------------

    primary_attractions = [
        name
        for name, attraction_type in attractions
        if attraction_type == "primary"
    ]

    hidden_gems = [
        name
        for name, attraction_type in attractions
        if attraction_type == "hidden_gem"
    ]

    # --------------------------------------------------------
    # SEASONS
    # --------------------------------------------------------

    best_seasons = [
        season_name
        for season_type, season_name in seasons
        if season_type == "best"
    ]

    avoid_seasons = [
        season_name
        for season_type, season_name in seasons
        if season_type == "avoid"
    ]

    # --------------------------------------------------------
    # BUDGET TEXT
    # --------------------------------------------------------

    budget_text = []

    for budget in budgets:

        budget_text.append(
            f"""
Budget category: {format_value(budget['budget_type'])}

Accommodation:
{format_value(budget['accommodation_min'])}
to
{format_value(budget['accommodation_max'])}

Food:
{format_value(budget['food_min'])}
to
{format_value(budget['food_max'])}

Activities:
{format_value(budget['activities_min'])}
to
{format_value(budget['activities_max'])}

Local transport:
{format_value(budget['transport_min'])}
to
{format_value(budget['transport_max'])}

Total daily budget:
{format_value(budget['total_daily_min'])}
to
{format_value(budget['total_daily_max'])}
"""
        )

    # --------------------------------------------------------
    # DOCUMENT
    # --------------------------------------------------------

    text = f"""
Travel Destination: {format_value(destination_name)}

Destination ID:
{format_value(destination_id)}

Location:
State: {format_value(destination['state'])}
District: {format_value(destination['district'])}
Region: {format_value(destination['region'])}

Geographical Information:
Latitude: {format_value(destination['latitude'])}
Longitude: {format_value(destination['longitude'])}
Altitude: {format_value(destination['altitude_m'])} meters

Popularity:
{format_value(destination['popularity_score'])}

Accessibility:
{format_value(destination['accessibility'])}

Road Connectivity:
{format_value(destination['road_connectivity'])}

Recommended Duration:
Minimum: {format_value(destination['minimum_days'])} days
Ideal: {format_value(destination['ideal_days'])} days
Maximum: {format_value(destination['maximum_days'])} days

Safety Rating:
{format_value(destination['safety_rating'])}

Permits Required:
{format_value(destination['permits_required'])}

Nearest Airport:
{format_value(destination['nearest_airport_name'])}
Distance:
{format_value(destination['nearest_airport_distance_km'])} km

Nearest Railway Station:
{format_value(destination['nearest_railway_name'])}
Distance:
{format_value(destination['nearest_railway_distance_km'])} km

Nearest Major City:
{format_value(destination['nearest_major_city'])}
Distance:
{format_value(destination['nearest_major_city_distance_km'])} km

Language:
{format_value(destination['language_spoken'])}

Mobile Network:
{format_value(destination['mobile_network'])}

Internet Connectivity:
{format_value(destination['internet_connectivity'])}

ATM Availability:
{format_value(destination['atm_availability'])}

Primary Attractions:
{', '.join(primary_attractions)
 if primary_attractions else 'Not specified'}

Hidden Gems:
{', '.join(hidden_gems)
 if hidden_gems else 'Not specified'}

Available Activities:
{', '.join(activities)
 if activities else 'Not specified'}

Accommodation Types:
{', '.join(accommodations)
 if accommodations else 'Not specified'}

Best Seasons:
{', '.join(best_seasons)
 if best_seasons else 'Not specified'}

Seasons to Avoid:
{', '.join(avoid_seasons)
 if avoid_seasons else 'Not specified'}

Budget Information:
{''.join(budget_text)
 if budget_text else 'Not specified'}
"""

    return {
        "id": str(destination_id),
        "destination_id": destination_id,
        "destination_name": destination_name,
        "state": destination["state"],
        "region": destination["region"],
        "text": text.strip(),
        "metadata": {
            "destination_id": destination_id,
            "destination_name": destination_name,
            "state": destination["state"],
            "district": destination["district"],
            "region": destination["region"],
            "latitude": destination["latitude"],
            "longitude": destination["longitude"],
            "popularity_score": destination["popularity_score"],
            "safety_rating": destination["safety_rating"],
            "ideal_days": destination["ideal_days"]
        }
    }


# ============================================================
# 13. CREATE ALL RAG DOCUMENTS
# ============================================================

def create_documents():

    print("=" * 60)
    print("TRAVEL RAG - DOCUMENT CREATION")
    print("=" * 60)

    # Create output directory
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # Connect
    print("\nConnecting to PostgreSQL...")

    conn = get_connection()

    print("PostgreSQL connection successful.")

    cursor = conn.cursor()

    try:

        # ----------------------------------------------------
        # GET DESTINATIONS
        # ----------------------------------------------------

        destinations = get_destinations(
            cursor
        )

        print(
            f"\nFound {len(destinations)} destinations."
        )

        documents = []

        # ----------------------------------------------------
        # CREATE ONE DOCUMENT PER DESTINATION
        # ----------------------------------------------------

        for index, destination in enumerate(
            destinations,
            start=1
        ):

            destination_id = destination[
                "destination_id"
            ]

            attractions = get_attractions(
                cursor,
                destination_id
            )

            activities = get_activities(
                cursor,
                destination_id
            )

            accommodations = get_accommodations(
                cursor,
                destination_id
            )

            budgets = get_budgets(
                cursor,
                destination_id
            )

            seasons = get_seasons(
                cursor,
                destination_id
            )

            document = create_document(

                destination,

                attractions,

                activities,

                accommodations,

                budgets,

                seasons

            )

            documents.append(
                document
            )

            print(
                f"[{index}/{len(destinations)}] "
                f"{destination['destination_name']}"
            )

        # ----------------------------------------------------
        # SAVE JSON
        # ----------------------------------------------------

        with open(
            OUTPUT_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                documents,
                file,
                ensure_ascii=False,
                indent=2,
                default=str
            )

        print("\n" + "=" * 60)

        print(
            f"Created {len(documents)} RAG documents."
        )

        print(
            f"Saved to:\n{OUTPUT_FILE}"
        )

        print("=" * 60)

    except Exception as error:

        print("\nDOCUMENT CREATION FAILED")

        print(error)

        raise

    finally:

        cursor.close()

        conn.close()

        print("\nPostgreSQL connection closed.")


# ============================================================
# 14. MAIN
# ============================================================

if __name__ == "__main__":

    create_documents()