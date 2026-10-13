import os
import json
import re
from pathlib import Path

import pandas as pd
import psycopg2
from jsonschema import validate
from dotenv import load_dotenv


# ============================================================
# 1. PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

RAW_DIR = BASE_DIR / "data" / "raw"

TOURISM_FILE = RAW_DIR / "india_tourism_dataset.json"
SCHEMA_FILE = RAW_DIR / "dataset_schema.json"
REVIEWS_FILE = RAW_DIR / "google_review_ratings.csv"
NAMES_FILE = RAW_DIR / "destination_names.txt"


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
# 4. CHECK SOURCE FILES
# ============================================================

def check_source_files():

    print("\nChecking source files...")

    files = [
        TOURISM_FILE,
        SCHEMA_FILE,
        REVIEWS_FILE,
        NAMES_FILE
    ]

    missing = []

    for file in files:

        if file.exists():

            print(f"[OK] {file.name}")

        else:

            print(f"[MISSING] {file.name}")

            missing.append(file)

    if missing:

        raise FileNotFoundError(
            "One or more source files are missing."
        )

    print("All source files found.")


# ============================================================
# 5. CONNECT TO POSTGRESQL
# ============================================================

def get_connection():

    if not DB_CONFIG["password"]:

        raise ValueError(
            "POSTGRES_PASSWORD is not set in .env"
        )

    return psycopg2.connect(**DB_CONFIG)


# ============================================================
# 6. VALIDATE TOURISM JSON
# ============================================================

def validate_tourism_json():

    print("\nValidating tourism JSON...")

    # Read actual dataset
    with open(
        TOURISM_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        tourism_data = json.load(file)

    # Read schema
    with open(
        SCHEMA_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        schema = json.load(file)

    try:

        validate(
            instance=tourism_data,
            schema=schema
        )

        print("Tourism JSON validation successful.")

    except Exception as error:

        print("\nWARNING:")
        print("The tourism dataset does not completely")
        print("match the supplied JSON schema.")

        if hasattr(error, "message"):

            print(f"Validation message: {error.message}")

        else:

            print(error)

        print("\nContinuing ETL using the actual dataset...")

    return tourism_data


# ============================================================
# 7. CHECK IMPORTANT FIELDS
# ============================================================

def check_required_fields(tourism_data):

    print("\nChecking important destination fields...")

    required_fields = [
        "id",
        "destination_name",
        "state",
        "district",
        "region"
    ]

    problems = []

    for index, destination in enumerate(tourism_data):

        for field in required_fields:

            if field not in destination:

                problems.append(
                    f"Record {index}: missing '{field}'"
                )

    if problems:

        print("\nWARNING: Missing important fields:")

        for problem in problems:

            print(problem)

    else:

        print("Important destination fields are present.")

    print(
        f"Total destinations: {len(tourism_data)}"
    )


# ============================================================
# 8. CREATE POSTGRESQL TABLES
# ============================================================

def create_tables(conn):

    cursor = conn.cursor()

    print("\nCreating PostgreSQL tables...")

    # --------------------------------------------------------
    # SCHEMA
    # --------------------------------------------------------

    cursor.execute("""
        CREATE SCHEMA IF NOT EXISTS travel;
    """)

    # --------------------------------------------------------
    # DESTINATIONS
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS travel.destinations (

            destination_id INTEGER PRIMARY KEY,

            destination_name TEXT NOT NULL,

            state TEXT,

            district TEXT,

            region TEXT,

            latitude DOUBLE PRECISION,

            longitude DOUBLE PRECISION,

            altitude_m INTEGER,

            popularity_score DOUBLE PRECISION,

            accessibility TEXT,

            road_connectivity TEXT,

            minimum_days INTEGER,

            ideal_days INTEGER,

            maximum_days INTEGER,

            safety_rating DOUBLE PRECISION,

            permits_required BOOLEAN,

            nearest_airport_name TEXT,

            nearest_airport_distance_km DOUBLE PRECISION,

            nearest_railway_name TEXT,

            nearest_railway_distance_km DOUBLE PRECISION,

            nearest_major_city TEXT,

            nearest_major_city_distance_km DOUBLE PRECISION,

            language_spoken TEXT,

            mobile_network TEXT,

            internet_connectivity TEXT,

            atm_availability TEXT,

            last_updated DATE,

            extra_data JSONB
        );
    """)

    # --------------------------------------------------------
    # ATTRACTIONS
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS travel.attractions (

            attraction_id SERIAL PRIMARY KEY,

            destination_id INTEGER
                REFERENCES travel.destinations(destination_id)
                ON DELETE CASCADE,

            attraction_name TEXT NOT NULL,

            attraction_type TEXT
        );
    """)

    # --------------------------------------------------------
    # ACTIVITIES
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS travel.activities (

            activity_id SERIAL PRIMARY KEY,

            destination_id INTEGER
                REFERENCES travel.destinations(destination_id)
                ON DELETE CASCADE,

            activity_name TEXT NOT NULL
        );
    """)

    # --------------------------------------------------------
    # ACCOMMODATIONS
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS travel.accommodations (

            accommodation_id SERIAL PRIMARY KEY,

            destination_id INTEGER
                REFERENCES travel.destinations(destination_id)
                ON DELETE CASCADE,

            accommodation_type TEXT NOT NULL
        );
    """)

    # --------------------------------------------------------
    # BUDGETS
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS travel.budgets (

            budget_id SERIAL PRIMARY KEY,

            destination_id INTEGER
                REFERENCES travel.destinations(destination_id)
                ON DELETE CASCADE,

            budget_type TEXT NOT NULL,

            accommodation_min NUMERIC,

            accommodation_max NUMERIC,

            food_min NUMERIC,

            food_max NUMERIC,

            activities_min NUMERIC,

            activities_max NUMERIC,

            transport_min NUMERIC,

            transport_max NUMERIC,

            total_daily_min NUMERIC,

            total_daily_max NUMERIC
        );
    """)

    # --------------------------------------------------------
    # SEASONS
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS travel.seasons (

            season_id SERIAL PRIMARY KEY,

            destination_id INTEGER
                REFERENCES travel.destinations(destination_id)
                ON DELETE CASCADE,

            season_type TEXT NOT NULL,

            season_name TEXT
        );
    """)

    # --------------------------------------------------------
    # USERS
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS travel.users (

            user_id INTEGER PRIMARY KEY,

            user_name TEXT NOT NULL
        );
    """)

    # --------------------------------------------------------
    # USER RATINGS
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS travel.user_ratings (

            user_id INTEGER
                REFERENCES travel.users(user_id)
                ON DELETE CASCADE,

            category_id INTEGER NOT NULL,

            category_name TEXT NOT NULL,

            rating DOUBLE PRECISION,

            PRIMARY KEY (user_id, category_id)
        );
    """)

    # --------------------------------------------------------
    # DESTINATION NAMES
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS travel.destination_names (

            source_number INTEGER PRIMARY KEY,

            destination_name TEXT NOT NULL
        );
    """)

    # --------------------------------------------------------
    # INDEXES
    # --------------------------------------------------------

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_destinations_state
        ON travel.destinations(state);
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_destinations_region
        ON travel.destinations(region);
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_attractions_destination
        ON travel.attractions(destination_id);
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_activities_destination
        ON travel.activities(destination_id);
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_ratings_user
        ON travel.user_ratings(user_id);
    """)

    conn.commit()

    cursor.close()

    print("PostgreSQL tables created successfully.")


# ============================================================
# 9. LOAD DESTINATIONS
# ============================================================

def load_destinations(conn, tourism_data):

    cursor = conn.cursor()

    print("\nLoading destinations...")

    count = 0

    for destination in tourism_data:

        destination_id = destination.get("id")

        destination_name = destination.get(
            "destination_name"
        )

        if destination_id is None:
            continue

        if not destination_name:
            continue

        coordinates = destination.get(
            "coordinates",
            {}
        )

        airport = destination.get(
            "nearest_airport",
            {}
        )

        railway = destination.get(
            "nearest_railway_station",
            {}
        )

        major_city = destination.get(
            "nearest_major_city",
            {}
        )

        cursor.execute("""
            INSERT INTO travel.destinations (

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
                last_updated,
                extra_data

            )

            VALUES (

                %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s

            )

            ON CONFLICT (destination_id)

            DO UPDATE SET

                destination_name =
                    EXCLUDED.destination_name,

                state =
                    EXCLUDED.state,

                district =
                    EXCLUDED.district,

                region =
                    EXCLUDED.region,

                latitude =
                    EXCLUDED.latitude,

                longitude =
                    EXCLUDED.longitude,

                altitude_m =
                    EXCLUDED.altitude_m,

                popularity_score =
                    EXCLUDED.popularity_score,

                accessibility =
                    EXCLUDED.accessibility,

                road_connectivity =
                    EXCLUDED.road_connectivity,

                minimum_days =
                    EXCLUDED.minimum_days,

                ideal_days =
                    EXCLUDED.ideal_days,

                maximum_days =
                    EXCLUDED.maximum_days,

                safety_rating =
                    EXCLUDED.safety_rating,

                permits_required =
                    EXCLUDED.permits_required,

                nearest_airport_name =
                    EXCLUDED.nearest_airport_name,

                nearest_airport_distance_km =
                    EXCLUDED.nearest_airport_distance_km,

                nearest_railway_name =
                    EXCLUDED.nearest_railway_name,

                nearest_railway_distance_km =
                    EXCLUDED.nearest_railway_distance_km,

                nearest_major_city =
                    EXCLUDED.nearest_major_city,

                nearest_major_city_distance_km =
                    EXCLUDED.nearest_major_city_distance_km,

                language_spoken =
                    EXCLUDED.language_spoken,

                mobile_network =
                    EXCLUDED.mobile_network,

                internet_connectivity =
                    EXCLUDED.internet_connectivity,

                atm_availability =
                    EXCLUDED.atm_availability,

                last_updated =
                    EXCLUDED.last_updated,

                extra_data =
                    EXCLUDED.extra_data;
        """, (

            destination_id,

            destination_name,

            destination.get("state"),

            destination.get("district"),

            destination.get("region"),

            coordinates.get("latitude"),

            coordinates.get("longitude"),

            destination.get("altitude_m"),

            destination.get("popularity_score"),

            destination.get("accessibility"),

            destination.get("road_connectivity"),

            destination.get("minimum_days"),

            destination.get("ideal_days"),

            destination.get("maximum_days"),

            destination.get("safety_rating"),

            destination.get("permits_required"),

            airport.get("name"),

            airport.get("distance_km"),

            railway.get("name"),

            railway.get("distance_km"),

            major_city.get("name"),

            major_city.get("distance_km"),

            destination.get("language_spoken"),

            destination.get("mobile_network"),

            destination.get("internet_connectivity"),

            destination.get("atm_availability"),

            destination.get("last_updated"),

            json.dumps(
                destination,
                ensure_ascii=False
            )
        ))

        count += 1

    conn.commit()

    cursor.close()

    print(f"Loaded {count} destinations.")


# ============================================================
# 10. LOAD ATTRACTIONS
# ============================================================

def load_attractions(conn, tourism_data):

    cursor = conn.cursor()

    print("\nLoading attractions...")

    count = 0

    for destination in tourism_data:

        destination_id = destination.get("id")

        primary_attractions = destination.get(
            "primary_attractions",
            []
        )

        hidden_gems = destination.get(
            "hidden_gems",
            []
        )

        for attraction in primary_attractions:

            cursor.execute("""
                INSERT INTO travel.attractions (

                    destination_id,
                    attraction_name,
                    attraction_type

                )

                VALUES (%s, %s, %s);
            """, (

                destination_id,
                str(attraction),
                "primary"

            ))

            count += 1

        for attraction in hidden_gems:

            cursor.execute("""
                INSERT INTO travel.attractions (

                    destination_id,
                    attraction_name,
                    attraction_type

                )

                VALUES (%s, %s, %s);
            """, (

                destination_id,
                str(attraction),
                "hidden_gem"

            ))

            count += 1

    conn.commit()

    cursor.close()

    print(f"Loaded {count} attractions.")


# ============================================================
# 11. LOAD ACTIVITIES
# ============================================================

def load_activities(conn, tourism_data):

    cursor = conn.cursor()

    print("\nLoading activities...")

    count = 0

    for destination in tourism_data:

        destination_id = destination.get("id")

        activities = destination.get(
            "activities_available",
            []
        )

        for activity in activities:

            cursor.execute("""
                INSERT INTO travel.activities (

                    destination_id,
                    activity_name

                )

                VALUES (%s, %s);
            """, (

                destination_id,
                str(activity)

            ))

            count += 1

    conn.commit()

    cursor.close()

    print(f"Loaded {count} activities.")


# ============================================================
# 12. LOAD ACCOMMODATIONS
# ============================================================

def load_accommodations(conn, tourism_data):

    cursor = conn.cursor()

    print("\nLoading accommodations...")

    count = 0

    for destination in tourism_data:

        destination_id = destination.get("id")

        accommodations = destination.get(
            "accommodation_types",
            []
        )

        for accommodation in accommodations:

            cursor.execute("""
                INSERT INTO travel.accommodations (

                    destination_id,
                    accommodation_type

                )

                VALUES (%s, %s);
            """, (

                destination_id,
                str(accommodation)

            ))

            count += 1

    conn.commit()

    cursor.close()

    print(f"Loaded {count} accommodation types.")


# ============================================================
# 13. SAFE RANGE HELPER
# ============================================================

def get_range(data, key):

    value = data.get(key)

    if isinstance(value, list):

        if len(value) >= 2:

            return value[0], value[1]

    return None, None


# ============================================================
# 14. LOAD BUDGETS
# ============================================================

def load_budgets(conn, tourism_data):

    cursor = conn.cursor()

    print("\nLoading budgets...")

    count = 0

    budget_types = [
        "budget_category",
        "mid_range_category",
        "luxury_category"
    ]

    for destination in tourism_data:

        destination_id = destination.get("id")

        for budget_type in budget_types:

            budget = destination.get(
                budget_type
            )

            if not isinstance(
                budget,
                dict
            ):
                continue

            accommodation_min, accommodation_max = \
                get_range(
                    budget,
                    "accommodation_range"
                )

            food_min, food_max = \
                get_range(
                    budget,
                    "food_range"
                )

            activities_min, activities_max = \
                get_range(
                    budget,
                    "activities_range"
                )

            transport_min, transport_max = \
                get_range(
                    budget,
                    "local_transport_range"
                )

            total_min, total_max = \
                get_range(
                    budget,
                    "total_daily_range"
                )

            cursor.execute("""
                INSERT INTO travel.budgets (

                    destination_id,
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

                )

                VALUES (

                    %s, %s,

                    %s, %s,

                    %s, %s,

                    %s, %s,

                    %s, %s,

                    %s, %s
                );
            """, (

                destination_id,

                budget_type,

                accommodation_min,
                accommodation_max,

                food_min,
                food_max,

                activities_min,
                activities_max,

                transport_min,
                transport_max,

                total_min,
                total_max
            ))

            count += 1

    conn.commit()

    cursor.close()

    print(f"Loaded {count} budget records.")


# ============================================================
# 15. LOAD SEASONS
# ============================================================

def load_seasons(conn, tourism_data):

    cursor = conn.cursor()

    print("\nLoading seasons...")

    count = 0

    for destination in tourism_data:

        destination_id = destination.get("id")

        best_seasons = destination.get(
            "best_seasons",
            []
        )

        avoid_seasons = destination.get(
            "avoid_seasons",
            []
        )

        for season in best_seasons:

            cursor.execute("""
                INSERT INTO travel.seasons (

                    destination_id,
                    season_type,
                    season_name

                )

                VALUES (%s, %s, %s);
            """, (

                destination_id,
                "best",
                str(season)

            ))

            count += 1

        for season in avoid_seasons:

            cursor.execute("""
                INSERT INTO travel.seasons (

                    destination_id,
                    season_type,
                    season_name

                )

                VALUES (%s, %s, %s);
            """, (

                destination_id,
                "avoid",
                str(season)

            ))

            count += 1

    conn.commit()

    cursor.close()

    print(f"Loaded {count} season records.")


# ============================================================
# 16. LOAD GOOGLE REVIEW USERS AND RATINGS
# ============================================================

def load_reviews(conn):

    print("\nLoading Google review ratings...")

    df = pd.read_csv(
        REVIEWS_FILE
    )

    # --------------------------------------------------------
    # REMOVE COMPLETELY EMPTY COLUMNS
    # --------------------------------------------------------

    df = df.dropna(
        axis=1,
        how="all"
    )

    # --------------------------------------------------------
    # CHECK USER COLUMN
    # --------------------------------------------------------

    if "User" not in df.columns:

        raise ValueError(
            "'User' column not found in "
            "google_review_ratings.csv"
        )

    # --------------------------------------------------------
    # EXTRACT USER ID
    # --------------------------------------------------------

    df["user_id"] = (
        df["User"]
        .astype(str)
        .str.extract(r"(\d+)", expand=False)
    )

    # Remove rows where user ID could not be extracted
    df = df.dropna(
        subset=["user_id"]
    )

    df["user_id"] = df["user_id"].astype(int)

    # --------------------------------------------------------
    # FIND RATING COLUMNS
    # --------------------------------------------------------

    category_columns = [

        column

        for column in df.columns

        if column.startswith("Category")

    ]

    print(
        f"Found {len(category_columns)} rating categories."
    )

    cursor = conn.cursor()

    # --------------------------------------------------------
    # INSERT USERS
    # --------------------------------------------------------

    for _, row in df.iterrows():

        cursor.execute("""
            INSERT INTO travel.users (

                user_id,
                user_name

            )

            VALUES (%s, %s)

            ON CONFLICT (user_id)

            DO UPDATE SET

                user_name =
                EXCLUDED.user_name;
        """, (

            int(row["user_id"]),

            str(row["User"])

        ))

    # --------------------------------------------------------
    # INSERT RATINGS
    # --------------------------------------------------------

    inserted_ratings = 0
    skipped_ratings = 0

    for _, row in df.iterrows():

        user_id = int(
            row["user_id"]
        )

        for category_id, category_name in enumerate(
            category_columns,
            start=1
        ):

            rating = row[category_name]

            # ----------------------------------------------
            # SKIP NULL VALUES
            # ----------------------------------------------

            if pd.isna(rating):

                continue

            # ----------------------------------------------
            # CLEAN RATING
            # ----------------------------------------------

            rating_text = str(rating).strip()

            # Replace tabs/newlines/multiple spaces
            rating_text = re.sub(
                r"[\t\r\n]+",
                " ",
                rating_text
            )

            rating_text = re.sub(
                r"\s+",
                " ",
                rating_text
            ).strip()

            # ----------------------------------------------
            # EXTRACT FIRST NUMERIC VALUE
            #
            # Examples:
            #
            # "4.5"       -> 4.5
            # "3"         -> 3.0
            # "2\t2."      -> 2.0
            # "4 4."      -> 4.0
            # ----------------------------------------------

            match = re.search(
                r"\d+(?:\.\d+)?",
                rating_text
            )

            if not match:

                skipped_ratings += 1

                continue

            try:

                rating_value = float(
                    match.group()
                )

            except ValueError:

                skipped_ratings += 1

                continue

            # ----------------------------------------------
            # VALIDATE RATING RANGE
            # ----------------------------------------------

            if rating_value < 0 or rating_value > 5:

                skipped_ratings += 1

                continue

            # ----------------------------------------------
            # INSERT RATING
            # ----------------------------------------------

            cursor.execute("""
                INSERT INTO travel.user_ratings (

                    user_id,
                    category_id,
                    category_name,
                    rating

                )

                VALUES (%s, %s, %s, %s)

                ON CONFLICT (
                    user_id,
                    category_id
                )

                DO UPDATE SET

                    rating =
                    EXCLUDED.rating;
            """, (

                user_id,

                category_id,

                category_name,

                rating_value

            ))

            inserted_ratings += 1

    conn.commit()

    cursor.close()

    print(
        f"Loaded {len(df)} users."
    )

    print(
        f"Processed "
        f"{len(category_columns)} rating categories."
    )

    print(
        f"Inserted/updated ratings: "
        f"{inserted_ratings}"
    )

    print(
        f"Skipped invalid ratings: "
        f"{skipped_ratings}"
    )


# ============================================================
# 17. LOAD DESTINATION NAMES
# ============================================================

def load_destination_names(conn):

    print("\nLoading destination names...")

    cursor = conn.cursor()

    count = 0

    with open(
        NAMES_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        for line in file:

            line = line.strip()

            if not line:

                continue

            match = re.match(
                r"^(\d+)\.\s*(.*)$",
                line
            )

            if not match:

                continue

            source_number = int(
                match.group(1)
            )

            destination_name = (
                match.group(2).strip()
            )

            cursor.execute("""
                INSERT INTO travel.destination_names (

                    source_number,
                    destination_name

                )

                VALUES (%s, %s)

                ON CONFLICT (source_number)

                DO UPDATE SET

                    destination_name =
                    EXCLUDED.destination_name;
            """, (

                source_number,

                destination_name

            ))

            count += 1

    conn.commit()

    cursor.close()

    print(
        f"Loaded {count} destination names."
    )


# ============================================================
# 18. VERIFY DATABASE
# ============================================================

def verify_database(conn):

    print("\nVerifying PostgreSQL data...")

    cursor = conn.cursor()

    tables = [
        "destinations",
        "attractions",
        "activities",
        "accommodations",
        "budgets",
        "seasons",
        "users",
        "user_ratings",
        "destination_names"
    ]

    for table in tables:

        cursor.execute(
            f"""
            SELECT COUNT(*)
            FROM travel.{table};
            """
        )

        count = cursor.fetchone()[0]

        print(
            f"travel.{table}: {count} rows"
        )

    cursor.close()


# ============================================================
# 19. MAIN ETL PIPELINE
# ============================================================

def main():

    print("=" * 60)
    print("TRAVEL RAG - ETL PIPELINE")
    print("=" * 60)

    # --------------------------------------------------------
    # CHECK FILES
    # --------------------------------------------------------

    check_source_files()

    # --------------------------------------------------------
    # READ + VALIDATE JSON
    # --------------------------------------------------------

    tourism_data = validate_tourism_json()

    # --------------------------------------------------------
    # CHECK IMPORTANT FIELDS
    # --------------------------------------------------------

    check_required_fields(
        tourism_data
    )

    # --------------------------------------------------------
    # CONNECT TO POSTGRESQL
    # --------------------------------------------------------

    print("\nConnecting to PostgreSQL...")

    conn = get_connection()

    print("PostgreSQL connection successful.")

    try:

        # ----------------------------------------------------
        # CREATE TABLES
        # ----------------------------------------------------

        create_tables(conn)

        # ----------------------------------------------------
        # LOAD TOURISM DATA
        # ----------------------------------------------------

        load_destinations(
            conn,
            tourism_data
        )

        load_attractions(
            conn,
            tourism_data
        )

        load_activities(
            conn,
            tourism_data
        )

        load_accommodations(
            conn,
            tourism_data
        )

        load_budgets(
            conn,
            tourism_data
        )

        load_seasons(
            conn,
            tourism_data
        )

        # ----------------------------------------------------
        # LOAD GOOGLE RATINGS
        # ----------------------------------------------------

        load_reviews(conn)

        # ----------------------------------------------------
        # LOAD DESTINATION LIST
        # ----------------------------------------------------

        load_destination_names(conn)

        # ----------------------------------------------------
        # VERIFY
        # ----------------------------------------------------

        verify_database(conn)

        print("\n" + "=" * 60)
        print("ETL COMPLETED SUCCESSFULLY")
        print("=" * 60)

    except Exception as error:

        conn.rollback()

        print("\n" + "=" * 60)
        print("ETL FAILED")
        print("=" * 60)

        print(error)

        raise

    finally:

        conn.close()

        print("\nPostgreSQL connection closed.")


# ============================================================
# 20. PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()