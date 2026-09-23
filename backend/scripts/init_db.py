from app.database.connection import create_connection
from app.database.seed import seed_database


def main() -> None:
    """
    Initialize and seed the deterministic NexaTel database.
    """

    connection = create_connection()

    try:
        seed_database(
            connection,
            reset=True,
        )

        print("NexaTel database initialized successfully.")

    finally:
        connection.close()


if __name__ == "__main__":
    main()